**English** | [简体中文](README.zh-CN.md)

# engine/tools

Command-line tools for a results deck: plotting, page references, speaker-note sync, moving pages, themes, icons, and layout checks. They need Python 3.10+ and use the standard library only; `plot.py` runs the deck's own plotting code (matplotlib), `theme_icons.py` and `svg_raster.py` need headless Chrome, and `layout_check.py` needs Poppler. Every tool prints its full usage with `--help`. The contract behind them is [../SPEC.md](../SPEC.md); the builder itself, `js/build.js`, is described in [../SPEC.md](../SPEC.md) §8.1.

The first argument is the deck directory, which holds `deck.config.js`. The tools do not run Node: they read the literal string fields `name`, `outDir`, `figDir`, `theme`, `lang`, and `iconDir` (move.py also reads `sections`) from deck.config.js with regular expressions, so keep those fields plain string literals. The examples below run from the engine directory on the template deck, `template/`.

| Tool | Reads | Writes |
|---|---|---|
| [plot.py](#plotpy) | `plotting/`, theme | `figures/<name>.png`, `figures/run_meta/<name>.json` |
| [pages.py](#pagespy) | pages.json, README / TODO / outline docs | generated blocks in those docs (`--table --write`) |
| [pull_notes.py](#pull_notespy) | a speaker-edited PPTX, pages.json | `notes/<key>.md`, `notes/_unmatched.json` (`--write`) |
| [move.py](#movepy) | `slides/*.js`, `notes/<key>.md` | one page file's `section` / `order` (`--respace`: several) |
| [theme_from_pptx.py](#theme_from_pptxpy) | a template PPTX | a theme directory (theme.json + pictures) |
| [theme_icons.py](#theme_iconspy) | page files, theme colors, icon library | `<theme>/icons/png/` |
| [svg_raster.py](#svg_rasterpy) | one SVG | one PNG |
| [layout_check.py](#layout_checkpy) | built PPTX + PDF + pages.json | nothing (report only) |

Before writing, `pages.py --table --write` and `pull_notes.py --write` copy every existing file they are about to change to `<deck>/.backups/<YYYYMMDD_HHMMSS>/<relative path>`.

## plot.py

```
python3 tools/plot.py <deck> [--only NAME [NAME ...]] [--out-dir OUT_DIR] [--list]
```

```bash
python3 tools/plot.py template --list                         # registered figure names and their modules
python3 tools/plot.py template --only results_km              # one figure (always --only in parallel work)
python3 tools/plot.py template --only results_km --out-dir /tmp/figs   # regression run, figures/ untouched
python3 tools/plot.py template                                # every figure (integrator, after a theme change)
```

- Sets `DECK_THEME` from `theme` in deck.config.js (relative to the deck; `engine/themes/neutral` with a WARNING when that directory does not exist, and without one when the field or the file is missing) and `DECK_FIG_DIR` from `figDir` (default `<deck>/figures`; `--out-dir` when given). Then it imports every module of `<deck>/plotting/` except `style`, `common`, and `_*`, and merges their `FIGURES = {name: callable}` and `INPUTS = [...]`.
- Calls `style.apply_style()` when defined, then each selected callable, which must return `(figure, stats)`. The PNG is saved by `style.save(fig, name)` when defined, else at the theme dpi on white without a tight bbox.
- Writes `<fig dir>/<name>.png` and `<fig dir>/run_meta/<name>.json` with `{figure, png, module, stats, inputs, versions, created, theme}`; `inputs` is the module's `INPUTS` plus `common.INPUTS`, `theme` the theme directory used. `--only` touches only the files of the figures it draws.
- Exit codes: 0 done; 1 a figure failed or did not return `(figure, stats)` (later figures are not drawn); 2 usage or registry error (no deck directory, a name registered by two modules, an unknown `--only` name).

## pages.py

```
python3 tools/pages.py [deck] [--check | --show FILE | --keys | --table] [--write] [--pages JSON] [--ignore-file TXT]
```

```bash
python3 tools/pages.py template --check                       # default mode, read-only
python3 tools/pages.py template --show outline/01_results.md  # the file with every {{key}} expanded
python3 tools/pages.py template --keys                        # page, key, section, title of every slide
python3 tools/pages.py template --table                       # diff of the generated blocks (dry run)
python3 tools/pages.py template --table --write               # rewrite them (integrator)
```

Living documents name a slide by its key, never by a handwritten page number or title:

| Syntax | Expands to | Use |
|---|---|---|
| `{{sKm}}` | `P2「Hormone Therapy — Recurrence-free Survival」` | page number and title |
| `{{sKm}}–{{sForest}}` | `P2「…」–P3「…」` | a range; each end expands on its own |
| `{{sKm.title}}` | `Hormone Therapy — Recurrence-free Survival` | title only |
| `{{sKm.page}}` | `P2` | page number only |

- Reads `<deck>/<outDir>/<name>_wip.pages.json` by default. A deck built with `build.js --out` (such as the example decks in `examples/slides/`) has no wip: pass `--pages <out stem>.pages.json`.
- Scans `README.md`, `TODO.md`, and `outline/*.md` of the deck; with `lang: "zh"` the `.zh-CN.md` counterparts are preferred. `outline/archive/` is never read. Tokens in inline code and fenced code blocks are literal: neither expanded nor checked.
- `--check` reports [k] a `{{key}}` with no slide or a malformed `{{…}}`, [r] a handwritten page reference `P<digits>` outside code and generated blocks, [b] a key-like name `sXxx` in inline code that is neither a key nor a page file, and [g] a stale generated block. A hit that is not a page reference (e.g. P53) is silenced with a `file:regex` line in `<deck>/pages_ignore.txt` (`--ignore-file` overrides it) or a `<!--pages:ignore-->` marker on the line.
- `--table` regenerates the blocks between `<!-- pages:counts:start/end -->` and `<!-- pages:table:start/end -->`. The handwritten Subsection and Note columns are kept by key; new rows get `—` and the Note placeholder. With `lang: "en"` the blocks read `N slides (section key and slide count): …` and `| Page | Section | Subsection | Slide title | key | Note |` with placeholder `(Note to be added)`; with `lang: "zh"` they are Chinese. A table with a header in either language is read; switching `lang` and running `--table --write` switches the blocks.
- Exit codes: 0 clean; 1 `--check` found errors, or `--show` met an unknown key; 2 FATAL (pages.json missing or unreadable, a repeated key or page number, `name` not readable from deck.config.js, broken block markers).

## pull_notes.py

```
python3 tools/pull_notes.py [--dry-run | --write] [--pages JSON] deck [pptx]
```

```bash
python3 tools/pull_notes.py template template/output/example_deck_wip.pptx   # dry run: report only
python3 tools/pull_notes.py template <speaker-edited.pptx> --write            # integrator
python3 tools/pull_notes.py template --write                                  # pptx = highest output/example_deck_v<N>.pptx
```

- `pptx` defaults to the highest-numbered release `<outDir>/<name>_v<N>.pptx` (FATAL when there is none); `--pages` defaults to `<outDir>/<name>_wip.pages.json`. Without `--write` nothing is written.
- Matches each PPTX slide to a key by title: the first slide to the first pages.json row (when that row's title is `Title` or equal); then `notes/_aliases.json`; then a title that occurs exactly once in pages.json and once in the PPTX. A repeated title is matched only through aliases, `"<title>"` for the first occurrence and `"<title>#2"`, `"<title>#3"` … for later ones:

  ```json
  {
    "Clinical Factors — Univariate Cox": "sForest",
    "Clinical Factors — Univariate Cox#2": "sForestEmphasis"
  }
  ```

- Writes only the `notes/<key>.md` files whose text changed (line endings and trailing whitespace do not count). Empty notes in the PPTX are written as an empty file, which makes the build clear that slide's notes. It never deletes a file; notes files whose key is not in pages.json are listed for manual cleanup.
- Slides it cannot match (no match, a repeated title without an alias, a key not in pages.json or already taken) are not written; they are listed in the report and in `notes/_unmatched.json` (rewritten by every `--write`, `[]` when all matched). Paragraphs and line breaks are kept; bold and font sizes are not.
- `--write` backs up the files it changes to `<deck>/.backups/<timestamp>/notes/` first.
- Exit codes: 0 done (also with unmatched slides); 2 FATAL (deck, PPTX, pages.json, or `_aliases.json` missing or unreadable).

## move.py

```
python3 tools/move.py (--after KEY | --before KEY | --to SECTION | --respace SECTION) [--first | --last] [--dry-run] deck [key]
```

```bash
python3 tools/move.py template sForest --before sKm --dry-run          # order 20 -> 0, first in "results"
python3 tools/move.py template sSummary --to results --last            # into another section, at its end
python3 tools/move.py template --respace results                       # integrator only: 10, 20, 30 ...
```

- Replaces only the `section` and `order` values of `slides/<key>.js`; every other byte stays. `--after` / `--before` also move the page into that page's section; `--to` puts it last unless `--first`.
- The new order is the midpoint of the new neighbors, rounded to the fewest decimals (an integer when possible, at most 3) that still fall strictly between them. At the start of a section it is the largest multiple of 10 below the first page (0 or negative is fine), at the end the smallest multiple of 10 above the last page, and 10 in an empty section.
- When there is no such value, nothing is written and the tool exits with 2, printing the `--respace` command for the integrator. `--respace` edits several page files and must run serially.
- Prints order-dependent wording ("next slide", "as shown before", 「下一页」 …) found in the moved page and its old and new neighbors, in the page files and in `notes/<key>.md`, as WARNINGs. It never builds; it prints the `build.js --list` and `--only <key> --out … --png` commands to run next.
- Exit codes: 0 done (or nothing to do); 2 usage or deck error, including no free order.

## theme_from_pptx.py

```
python3 tools/theme_from_pptx.py <template.pptx> --out OUT [--base BASE] [--force]
```

```bash
python3 tools/theme_from_pptx.py <brand>.pptx --out template/theme_brand
```

- Reads slide size, theme colors (`lt1`, `dk2` or `dk1`, `accent1`), major / minor fonts, the title and body placeholder boxes, and the pictures of the slide master and layouts. The logo is the top-right-most master picture (or the picture shared by most layouts); the title logo comes from the title-slide layout. `accentTints` are mixed from the accent with 25 %, 50 %, and 75 % white. The full field mapping is in [../SPEC.md](../SPEC.md) §5.2.
- Writes `<OUT>/theme.json` and copies every master / layout picture into `<OUT>`; `templatePictures` in theme.json lists them all (`file`, `svg`, `box`, `background`, `from`). An SVG-only logo gets a PNG copy rendered with `svg_raster.py`, and the asset points to the PNG (the SVG is kept). Fields the template lacks come from `--base` (default `engine/themes/neutral/theme.json`); `provenance` marks every field `"template"` or `"default"`.
- Prints a two-column report (from the template / kept default), a NOTE that `color.accent` is the template's `accent1` and is often not the brand color (check it by hand), and WARNINGs for missing fonts or a slide size different from the base.
- Never overwrites an existing `<OUT>/theme.json` without `--force`.
- Exit codes: 0 written; 2 usage error (unreadable PPTX, theme.json exists without `--force`, unreadable base).

## theme_icons.py

```
python3 tools/theme_icons.py [--all] [--size SIZE] [--dry-run] [--workers WORKERS] deck
```

```bash
python3 tools/theme_icons.py template --dry-run          # icons named in slides/*.js and slides/_lib/*.js
python3 tools/theme_icons.py template                    # render them in template/theme's colors
python3 tools/theme_icons.py template --all              # every icon of the library's manifest.csv
```

- Theme directory: `theme` in deck.config.js (default `<deck>/theme`), which must hold a theme.json; colors: `color.text` (`grey` variant) and `color.accent` (`accent` variant). Icon library: `iconDir` (`null` = `research-skills/examples/icons`).
- Renders every icon named by a string literal in `icon(<slide>, "<source>/<name>", …)` calls in `slides/*.js` and `slides/_lib/*.js`; non-literal names are printed as NOTEs. `--all` takes the whole `manifest.csv` instead.
- Writes `<theme>/icons/png/<source>/<name>.png` and `<name>_accent.png` for single-color icons; a multi-color icon gets one copy of `<iconDir>/png/<source>/<name>.png` (rendered in its own colors when missing) and no accent variant. Every listed PNG is rewritten on each run. `icon()` in primitives.js reads these files first and falls back to `<iconDir>/png/`. When the deck's `theme` is a shared directory (such as the engine's neutral theme), the icons are written there.
- `--size` is the PNG side in pixels (default 512); `--workers` the number of parallel Chrome processes (default 4).
- Exit codes: 0 done; 1 some icon failed to render; 2 usage error (no deck.config.js or theme.json, unreadable colors, no headless Chrome).

## svg_raster.py

```
python3 tools/svg_raster.py [--height HEIGHT] [--width WIDTH] [--size SIZE] [--color COLOR] svg png
```

```bash
python3 tools/svg_raster.py logo.svg logo.png --height 210          # width follows the viewBox
python3 tools/svg_raster.py icon.svg icon.png --size 512 --color A51C30
```

- Renders one SVG to a transparent PNG with headless Chrome. Give at least one of `--height`, `--width`, `--size` (square). `--color RRGGBB` recolors a single-color SVG (one that uses `currentColor` or at most one explicit color and embeds no image); multi-color SVGs keep their colors. The SVG on disk is never modified.
- Browser: `$DECK_CHROME` when set (and nothing else), else the first of `google-chrome`, `chromium-browser`, `chromium` on `PATH`.
- Used by `theme_icons.py` and `theme_from_pptx.py`.
- Exit codes: 0 written; 2 error (bad arguments, no Chrome, unreadable SVG, rendering failed).

## layout_check.py

```
python3 tools/layout_check.py [--pptx PPTX] [--pdf PDF] [--pages-json PAGES_JSON] [--pages [PAGES ...]] [--png-dir PNG_DIR] [--tol TOL] [deck]
```

```bash
python3 tools/layout_check.py template                              # the wip pptx / pdf / pages.json
python3 tools/layout_check.py template --pages 2 3 --png-dir /tmp/lc   # two pages, flagged ones rendered
python3 tools/layout_check.py --pptx /tmp/x.pptx --pdf /tmp/x.pdf  # any pair, no deck needed
```

- Combines `pdftotext -bbox-layout` (rendered text lines) with the PPTX XML (picture and text boxes, z-order) and reports HIDDEN-TITLE, TITLE-OVER-PIC, TITLE-WRAP, HIDDEN-TEXT, TEXT-OVER-PIC, and TEXT-OVER-TEXT per page. Title lines are recognized by the theme's `size.title`.
- Defaults to `<deck>/<outDir>/<name>_wip.{pptx,pdf,pages.json}`. `--png-dir` renders the flagged pages as `page_<NN>.png` (`pdftoppm -r 60`); `--tol` is the overlap threshold in points (default 3). Read-only otherwise. Expect a few false positives; the rendered page is the final word.
- Exit codes: 0 clean (or only TITLE-WRAP with a gap of at least 4 pt); 1 problems found; 2 usage error (pdftotext missing, input files missing or unreadable).

## Language policy

`lang: "zh"` in deck.config.js only changes the blocks `pages.py` writes into outline documents. Deck content and generated deliverables stay English. This file and [README.zh-CN.md](README.zh-CN.md) are the bilingual documentation pair.

**English** | [简体中文](SPEC.zh-CN.md)

# Engine interface contract (v2)

The results-deck engine is the reusable layer for building research decks. It provides theme-aware layout primitives (JS), a PPTX builder (JS), themes, a plotting entry point, and tools for page references, speaker notes, moving pages, themes, and layout checks (Python, standard library only; the plotting entry point also needs matplotlib, and theme icons and SVG logo rasterization need headless Chrome), plus a copyable deck template, `template/`. The parts interact only through the file formats, command lines, and function signatures below.

The design has three goals:

1. **Multiple agents in parallel.** Adding, editing, or moving a page, drawing a figure, or editing a page's notes writes only that page's or figure's own files, never a shared page-order file (§9).
2. **A new template means a new style.** Colors, fonts, geometry, and logos live in `theme/`, generated from a template PPTX; page files and plotting code hard-code none of them (§5).
3. **Outline, plotting, and slide construction stay separate.** The outline is one file per chapter (§7), plotting is a package with one module per section (§6), and the builder consumes page files only (§3, §8).

## v1 to v2 changes

- `deck.config.js` lists section keys only. Each `slides/<key>.js` file declares its own `section` and `order`, and the build sorts the pages (§3). Moving a page means changing those two fields in that one file.
- The page key is the filename (without `.js`), not a builder function name. Keys are unique by the filesystem, so the `sXxx#2` rule is gone.
- Page modules export `build(pres, n, P, ctx)`. The builder supplies primitives through `P`, so page files never `require` an engine path.
- Speaker notes moved from one `notes.json` to one UTF-8 file per page at `notes/<key>.md`. Title aliases live in `notes/_aliases.json`; unmatched slides are recorded in `notes/_unmatched.json` (§8.3).
- Themes live in `theme/theme.json` (§5) and `configure()` takes a `theme`. Primitives contain no hard-coded colors, fonts, or coordinates.
- New `--only <key,…>` and `--png`. Partial builds (`--only` / `--sections`) print the **full-deck page numbers** in the footer and are lenient about page files outside the selection (§8.1).
- New full-build lock `<outDir>/.build.lock` (§8.1), plotting entry point `tools/plot.py` (§6), `tools/move.py` (§3.1), `tools/theme_from_pptx.py` (§5.2), `tools/theme_icons.py` and `tools/svg_raster.py` (§5.4), and `tools/layout_check.py` (§8.5).
- Each `pages.json` row has an `order` field; `builder` is kept and holds the key (§8.2).
- `deck.config.js` has a `lang` field that selects English or Chinese for the blocks `pages.py` generates (§8.4).

## 1. Directory layout

```
engine/
  SPEC.md / SPEC.zh-CN.md    this contract (English / Chinese)
  README.md                  how to use it (copy template/, draw, build, self-check, switch the theme)
  js/primitives.js           layout primitives: newSlide, figure, table, conclusion, source, cite, abbr, icon, arrow … (all theme-driven)
  js/build.js                builder: collects and orders page files; wip / release / partial builds, pages.json, notes, hidden supplementary, PDF, PNG
  themes/neutral/            default theme (theme.json); template/theme/ is a copy of it
  tools/README.md            command line, files read and written, and exit codes of every tool
  tools/plot.py              plotting entry point: loads the deck's plotting/ package; --only, --out-dir, --list; one run_meta per figure (§6)
  tools/pages.py             {{key}} page references: --check / --show / --keys / --table [--write] (§8.4)
  tools/pull_notes.py        syncs speaker notes from a speaker-edited PPTX back into notes/<key>.md (§8.3)
  tools/move.py              moves a page by editing only its section / order; --respace renumbers a section (integrator) (§3.1)
  tools/theme_from_pptx.py   generates a theme directory from a template PPTX (§5.2)
  tools/theme_icons.py       renders the icons a deck uses in its theme colors (§5.4)
  tools/svg_raster.py        rasterizes an SVG (optionally recolored) to a transparent PNG with headless Chrome (§5.4)
  tools/layout_check.py      PDF + PPTX collision check (title covered by a figure, text over figure, text over text) (§8.5)
  tools/tests/               regression tests and test decks for the tools
  template/                  skeleton for a new deck (copy the whole directory)
```

## 2. Deck directory (the layout of template/ and of every deck)

```
<deck>/
  deck.config.js             metadata and section order (§2.1); sections only, no pages
  theme/                     theme.json + assets (logo …); a new style = a new directory (§5)
  theme/icons/png/           icons rendered in the theme colors (written by tools/theme_icons.py; optional; §5.4)
  slides/<key>.js            one file per page (§3)
  slides/_lib/*.js           the deck's shared layout helpers (integrator-owned, append-only); not collected as pages
  notes/<key>.md             speaker notes, one per page, optional (§8.3)
  notes/_aliases.json        {PPTX slide title: key} for pull_notes, optional
  notes/_unmatched.json      unmatched PPTX slides, written by pull_notes --write (§8.3)
  outline/README.md          outline index with generated blocks (§7, §8.4)
  outline/NN_<chapter>.md    one file per chapter
  outline/CHANGELOG.md       history of moves, renames, merges, and deletions
  outline/archive/           frozen old versions; tools never read them
  plotting/                  plotting package (§6): style.py, common.py, <section>.py
  figures/<name>.png         figures drawn at on-slide size (dpi from the theme)
  figures/run_meta/<name>.json
  pages_ignore.txt           pages.py ignore rules, one `file:regex` per line, optional (§8.4)
  .backups/<timestamp>/      copies made by pages.py --table --write and pull_notes --write before they change a file
  output/                    build products (location set by outDir, which may be outside the deck; §2.1)
```

Files and directories beginning with `_` (`slides/_lib/`, `notes/_aliases.json`, `notes/_unmatched.json`, `plotting/_*.py`) are shared helpers and are not collected as pages, notes, or figures.

`template/.gitignore` ignores `output/*.pptx`, `output/*.pdf`, `output/*_png/`, `output/.*` (the build lock and temporary files of an interrupted build), `.backups/`, and `notes/_unmatched.json`. `output/*.pages.json` and `figures/` are tracked: `pages.py --check` then works on a fresh checkout without Node, and the pages.json diff records page moves. After copying `template/` to start a deck, delete the copied `output/*.pptx`, `output/*.pdf`, and `output/*_png/`.

### 2.1 deck.config.js

```js
module.exports = {
  name: "my_deck",                 // output file prefix
  title: "My Deck",                // PPTX metadata title
  outDir: "output",                // this and the paths below are relative to the deck directory and may point outside it
  figDir: "figures",
  iconDir: null,                   // null = research-skills/examples/icons
  theme: "theme",                  // theme directory, may be a relative path to a shared theme; without a theme.json there, engine/themes/neutral is used (one WARNING)
  lang: "en",                      // "en" | "zh": language of the blocks pages.py generates (count line, page-table header, Note placeholder)
  refs: {},                        // reference registry {key: [author, journal, rest, isOrg?]} for cite()
  sections: ["title", "background", "methods", "results", "summary", "supplementary"],  // section order; unique keys
  supplementary: "supplementary",  // pages of this section are hidden in the PPTX
};
```

- Paths are relative to the deck directory and may point outside it. The example deck `examples/slides/results/` uses `outDir: "../output"` (both example decks share `examples/slides/output/`), `figDir: "../../figures"`, and `theme: "../../../skills/results-deck/engine/themes/neutral"` (the engine's default theme, no copy).
- build.js loads deck.config.js with Node. The Python tools do not run Node; they read **literal string** fields with regular expressions (`name`, `outDir`, `figDir`, `theme`, `lang`, `iconDir`; move.py also reads the `sections` list). Write these fields as string literals, not as concatenations or variables.
- When `theme` is missing, build.js and theme_icons.py use `<deck>/theme`, while plot.py and layout_check.py use `engine/themes/neutral`. Always write `theme` explicitly.
- A missing `name`, or `sections` that is not a non-empty list of section keys (for example the v1 form `[key, [builders]]`), stops the build with exit code 2. A v1 `notes` field is ignored with a WARNING.

Adding, removing, or reordering sections is rare and done by the integrator. A page's section and position are declared in the page file.

## 3. Page modules `slides/<key>.js`

Each `slides/<key>.js` exports one page:

```js
"use strict";

module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Recurrence-free Survival", n);
    P.figure(s, "survival_km_tamoxifen.png");
    P.conclusion(s, "Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89]; n = 686).");
    P.source(s, "Source: GBSG2 trial; univariate Cox");
    return s;
  },
};
```

- The key is the filename without `.js` and must match `^[A-Za-z][A-Za-z0-9_]*$` (e.g. `sKmTamoxifen`). The outline, notes, figure annotations, and tools all refer to pages by key.
- `section` must appear in `deck.config.js` `sections`.
- `order` is numeric and sorts pages within a section. Use gaps such as 10, 20, and 30 so a page can be inserted later (25). When gaps run out, the integrator runs `move.py --respace <section>` to renumber the section in multiples of 10; it edits several page files at once and must run serially. Two pages with the same `order` in one section stop the build (exit code 2) with both files listed.
- `build(pres, n, P, ctx)` receives the pptxgenjs instance, the footer page number (a title page may ignore it), the primitives object, and `ctx = {key, section, config, theme, deckDir}`. Page files `require` only the deck's own `slides/_lib/*`, never an engine path, so moving the engine does not break a deck. A `slides/_lib/*.js` file that needs primitives writes `require("results-deck")`: build.js maps that module id to the engine's primitives.js, the same object as `P` (`require("pptxgenjs")` and `require("jszip")` likewise map to the copies build.js found).
- Every page must be created with `P.newSlide(pres, title, n, opts)` (title pages use `{chrome: false}`) so its title enters the page table. One file makes exactly one slide: a `build()` that makes more or fewer stops the build (exit code 2) and nothing is written.
- **Two pages sharing a layout**: put the layout in a `slides/_lib/` function and call it from both page files. There is no "one builder, two pages".
- Page modules **hard-code no colors or font names**; they read them from `P.T` (theme colors and fonts). **Shared layout zones** (title, logo, main figure box, conclusion box, source line, page number, margins) are drawn by the primitives from `P.G`, so page modules do not repeat their coordinates. A theme change therefore needs no page edits for colors, fonts or these zones.
  Placement that belongs to one page only (positions and sizes of cards or diagram elements) may be written as numbers, preferably as offsets from `P.G` (e.g. `G.margin`, `G.contentW`); after switching to a theme with different geometry, review those pages one by one. The gallery pages of the example decks are written this way. build.js prints a WARNING (not an error) for a 6-digit hex color literal or a font name in a page file (coordinates are not checked).
- Notes come from `notes/<key>.md`; without that file, the page's `slide.addNotes()` text is used.

### 3.1 Moving pages: `tools/move.py`

```
python3 engine/tools/move.py <deck> <key> (--after <key> | --before <key> | --to <section> [--first | --last]) [--dry-run]
python3 engine/tools/move.py <deck> --respace <section> [--dry-run]      # integrator only, serial
```

- Replaces only the `section` and `order` values in that one page file; every other byte stays. Page files are read with regular expressions (Node is not run). `--after` / `--before` also move the page into that page's section; `--to` defaults to the end of the section (`--last`).
- **New order**: the midpoint of the two new neighbors, rounded to the fewest decimals that still fall strictly between them (an integer when possible, at most 3 decimals). At the start of a section it is the largest multiple of 10 below the first page (may be 0 or negative), at the end the smallest multiple of 10 above the last page, and 10 in an empty section.
- When no such value exists, nothing is written, the exit code is 2, and the tool prints the `move.py <deck> --respace <section>` command for the integrator. `--respace` renumbers a section to 10, 20, 30 … and edits several files.
- Order-dependent wording ("next slide", "as shown before", 「下一页」, …) in the moved page and its old and new neighbors, in both the page file **and `notes/<key>.md`**, is printed as a WARNING for the owner to fix.
- It never builds; it prints the next commands (`build.js <deck> --list` and `--only <key> --out <scratchpad>/<key>.pptx --png`).
- Exit codes: 0 done (or nothing to do), 2 usage or deck error (including no free order).

## 4. primitives.js exports (build.js and page files depend on them)

- `configure({figDir, iconDir, refs, theme})` is called by build.js once before any page module runs. `theme` is the parsed theme.json object with `_dir` (the theme directory that asset paths resolve against). Keys left out keep their value; `figDir` / `iconDir` set to `null` restore the defaults (`research-skills/examples/figures`, `.../icons`), and `theme: null` restores neutral.
- `T`: the theme without `geometry` (`T.color.accent`, `T.font.body`, `T.size.title`, `T.dpi` …). `G`: `geometry` (`G.margin`, `G.full`, `G.conclusion.yFigure` …) plus `G.slideW` / `G.slideH` (= `slide.w` / `slide.h`) and `G.contentW` (= slideW − 2 × margin). Both are live read-only views: after `configure()` changes the theme they return the new values. Before any `configure()`, they hold the `themes/neutral` values.
- The v1 flat constants (`C`, `FONT`, `SERIF`, `SW`, `SH`, `MX`, `CW`, `FIG_Y`, `CONC_Y`, `CONC_H`, `CONC_TEXT_Y`, `CONC_PT`, `CONC_INDENT`, `CONC_AFTER`, `FIG_DPI`, and the directories `FIG`, `ICONS`) are still exported as live views derived from the theme, for old code; new code uses `T` / `G`. `themes/neutral` matches the v1 constants value for value, so the default theme reproduces v1 output pixel for pixel.
- `newDeck(title)` returns a pptxgenjs instance with the theme's `slide` size.
- `newSlide(pres, title, n, opts)` returns a slide with the theme's background, title, logo, and page number, and logs `{page: n, title}` in the internal page table. `opts.logo = false` drops the logo; `opts.chrome = false` draws none of the three (the title is still logged).
- `takePageLog()` returns and clears the page table (in call order).
- `icon(slide, name, x, y, size, variant)`: `name` is `<source>/<icon>` (e.g. `healthicons/microscope`), `variant` is `"grey"` (text color) or `"accent"`. It uses `<theme dir>/icons/png/<name>[_accent].png` (written by `tools/theme_icons.py`) when that file exists, otherwise the same file under `<iconDir>/png/`.
- All other layout helpers (`figure`, `fitImage`, `table`, `conclusion`, `source`, `cite`, `abbr`, `draft`, `arrow` / `thinArrow` / `thickArrow`, `stepArrow`, `mark`, `titleFrame`, `emphasis` …) take their style from `T` / `G`. Rules unchanged: result figures are placed 1:1 without scaling (`figure()` sizes them as pixels / theme dpi), and the main figure goes to the bottom of the slide's z-order.
- primitives.js is a shared, append-only file changed by the integrator. A new layout element starts in the deck's `slides/_lib/` and moves into primitives after its second use.

## 5. Themes: a new template means a new style

### 5.1 theme.json

**The complete field list is [themes/neutral/theme.json](themes/neutral/theme.json)**; its current content:

```json
{
  "name": "neutral",
  "source": null,
  "slide": {"w": 13.333, "h": 7.5},
  "dpi": 200,
  "color": {
    "background": "FFFFFF", "text": "595959", "ink": "222222", "black": "000000",
    "muted": "7F7F7F", "rule": "D9D9D9", "tint": "F3F3F3",
    "accent": "A51C30", "accentTints": ["C45566", "DD99A3", "F1D3D8"],
    "blue": "2A78D6",
    "emphasisTransparency": 88
  },
  "plot": {"ink": "222222", "muted": "6B6B6B", "grid": "E6E6E6", "low": "C0392B", "high": "2A78D6", "mid": "8A8A8A"},
  "font": {"display": "Arial", "body": "Arial", "serif": "Times New Roman", "plot": ["Arial", "DejaVu Sans"]},
  "size": {"title": 28, "body": 16, "conclusion": 18, "table": 12, "source": 9, "abbr": 9.5, "page": 12,
           "plotBase": 12, "plotMin": 11,
           "logo": 11, "draft": 12, "pattern": 12},
  "geometry": {
    "margin": 0.6,
    "title": [0.59, 0.36, 9.6, 0.6],
    "logo": [10.983, 0.2, 2.0, 0.35],
    "figureTop": 1.1, "full": [12.1, 4.6], "half": [5.9, 4.6], "gap": 0.2,
    "conclusion": {"yFigure": 5.75, "yText": 5.95, "h": 1.05, "indent": 22, "after": 10},
    "source": [0.6, 6.82, 11.683, 0.6],
    "page": [12.363, 7.0, 0.6, 0.3],
    "titleSlide": {"logo": [0.6, 0.3, 2.4, 0.35], "accentBar": [0.6, 2.3, 0.1, 1.86], "accentRule": [0, 6.83, 13.333, 0.05]},
    "abbr": [0.6, 6.85, 6.0, 0.55],
    "draft": [10.683, 0.66, 2.35, 0.32],
    "pattern": [9.583, 0.62, 3.4, 0.3],
    "bullet": {"indent": 16, "after": 8, "afterLarge": 10, "largeFrom": 18},
    "tableCellMargin": [0.04, 0.1, 0.04, 0.1],
    "mark": 0.36,
    "stepArrow": [0.2, 0.24],
    "stroke": {"line": 0.75, "rule": 1, "arrowThin": 1, "arrowThick": 3.5, "mark": 1.5, "markGlyph": 2,
               "emphasis": 1, "tableOuter": 1.5, "tableInner": 0.75}
  },
  "asset": {"logo": null, "titleLogo": null},
  "provenance": {}
}
```

- `configure({theme})` deep-merges the given theme onto neutral (objects merge key by key, arrays and scalars replace), so a partial theme still works.
- Coordinates are inches, boxes are `[x, y, w, h]` with the origin at the top left. `geometry.abbr` / `draft` / `pattern` are absolute boxes that do not follow `margin`. `color.emphasisTransparency` is a number (the emphasis box transparency), not a color, and `theme_from_pptx` leaves it alone; `color.blue` is used only where figures use blue; `geometry.stroke` holds line widths (pt).
- **accentTints rule**: `color.accent` mixed with white at 25 %, 50 %, and 75 % white, per channel c′ = c + (255 − c) × f, rounded half up (`000000` → `404040`, `808080`, `BFBFBF`). `theme_from_pptx` writes tints by this rule; recompute them the same way when editing `accent` by hand. The neutral theme keeps v1's hand-picked `accentTints`, which are not derived by this rule.
- Asset paths are relative to the theme directory. With `asset.logo: null`, a gray `YOUR LOGO` placeholder is drawn in `geometry.logo`; with an image, the image is drawn stretched to the box (so measure the box at the image's aspect ratio). `asset.titleLogo` works the same in `geometry.titleSlide.logo`. For an SVG-only logo, `theme_from_pptx` renders a PNG copy, points the asset at the PNG, and keeps the SVG in the theme directory (§5.2).
- `templatePictures` (absent from neutral, written by `theme_from_pptx`): every picture on the template's slide master and layouts, one entry per (file, box): `{file, svg, box, background, from}`. `file` is the file copied into the theme directory (the raster when there is one); `svg` is the SVG of the same picture when both a raster and an SVG exist, else `null`; `box` is `[x, y, w, h]` in inches; `background: true` means it covers more than half of the slide, counts as a background, and is never chosen as a logo; `from` lists where it appears (`"master"`, `"layout '<name>'"` …). Primitives do not read this field: it records what the template holds, so a picture can be wired into `asset` by hand.
- **Icons follow the theme.** `icon(…, "accent")` uses PNGs rendered in the accent color. After `color.text` or `color.accent` changes, regenerate the theme icons with `tools/theme_icons.py` (§5.4); `icon()` looks in `<theme dir>/icons/png/` first, then in `iconDir`.
- `plot` holds the plotting colors (`low` / `high` / `mid` are the position-based curve colors: lower curve red, upper blue, middle gray), read by `plotting/style.py`; `size.plotBase` / `plotMin` are the figure font sizes.
- `provenance` maps every field (dotted key) to `"template"` (read from the template) or `"default"` (not in the template, kept from the base theme). It is written by `theme_from_pptx.py`.
- Theme values control style, not content: speaker names, references, and section names stay out of the theme.

### 5.2 From a template: `tools/theme_from_pptx.py`

```
python3 engine/tools/theme_from_pptx.py <template.pptx> --out <theme dir> [--base <theme.json>] [--force]
```

The tool reads the PPTX XML with the standard library and takes whatever the template provides:

| Theme field | Read from the template |
|---|---|
| `name` / `source` | template file stem / file name |
| `slide` | `sldSz` in `ppt/presentation.xml` (EMU ÷ 914400, 3 decimals) |
| `color.background` / `text` / `accent` | `clrScheme` in `ppt/theme/theme1.xml`: `lt1`, `dk2` (`dk1` when there is no `dk2`), `accent1`; an `srgbClr`, or the `lastClr` of a `sysClr` |
| `color.accentTints` | derived from `accent` by the §5.1 rule (25 %, 50 %, 75 % white) |
| `font.display` / `body` | `majorFont` / `minorFont` (`latin`) of the `fontScheme` |
| `geometry.title` | the `xfrm` of the slide master's `type="title"` placeholder; when the master has none, the first layout that has one (title-only / title-and-body layouts first) |
| `geometry.margin` | left x of the slide master's body placeholder (with the same layout fallback) |
| `asset.logo` + `geometry.logo` | the top-right-most picture on the slide master; when the master has no picture, the picture shared by most layouts (ties: top-right-most); title-slide layouts do not take part |
| `asset.titleLogo` + `geometry.titleSlide.logo` | a picture on the title-slide layout (`type="title"`, or a name containing "Title Slide"); the top-most one when there are several |
| `templatePictures` | every picture on the master and the layouts (§5.1) |

- `--out` is the theme directory to write (theme.json + pictures). Each picture's media file is copied there under its own file name (extension kept). When a picture has both a raster image and an SVG, the raster is the asset and the SVG is listed in `svg`. A picture covering more than half of the slide is a background: listed in `templatePictures`, never chosen as a logo.
- When the chosen logo or title logo is **SVG only**, the tool renders a PNG next to the SVG with `tools/svg_raster.py` (headless Chrome; height = box height × 600 px per inch, aspect ratio kept; named `<stem>_from_svg.png` if `<stem>.png` is taken), points the asset at the PNG, and keeps the SVG. Without Chrome (`DECK_CHROME` overrides the lookup) or when rendering fails, the SVG stays the asset and a WARNING is printed.
- Fields the template lacks (figure boxes, conclusion, source line, font sizes, plot colors) come from `--base` (default `engine/themes/neutral/theme.json`, or a built-in copy of the §5.1 defaults when that file does not exist) and are marked `"default"` in `provenance`. The tool ends with a two-column report: fields taken from the template and fields kept from the default; the second column needs a human look.
- It always prints a NOTE that `color.accent` is the template's `accent1`, which is **often not the brand color** (the brand color may live only in the logo): check it by hand and set `color.accent` and `color.accentTints` if needed.
- Other messages: a NOTE when the theme has no `dk2`, when the title box comes from a layout, or when a layout moves the title box; a WARNING when the slide size differs from the base (the default boxes need checking); a WARNING when the template fonts are not installed (e.g. Aptos; checked with `fc-list`), because a LibreOffice preview substitutes a wider font and lines wrap differently than in PowerPoint. Font files do not go into the repository.
- An existing `<out>/theme.json` is never overwritten without `--force`. Exit codes: 0 written, 2 usage error (unreadable PPTX, existing theme.json without `--force`, unreadable base).
- Out of scope: the template's slide master itself is not copied (pptxgenjs cannot load an existing master), only its style. Complex background patterns and decorations therefore do not carry over; save them as images in `asset` and draw them in `newSlide` if needed.

### 5.3 Switching the style (integrator, serial)

1. `theme_from_pptx.py <new template>.pptx --out <deck>/theme_<name>`; read the report and the NOTEs (especially the accent color) and edit theme.json by hand if needed.
2. Point `theme` in `deck.config.js` at the new directory (keep the old one).
3. Regenerate the icons in the new theme colors with `tools/theme_icons.py <deck>` (it writes into the directory `theme` names).
4. When `geometry.full` / `half`, `dpi`, `font.plot`, `size.plotBase` / `plotMin`, or the `plot` colors changed, redraw every figure with `tools/plot.py <deck>`; otherwise no redraw is needed.
5. Run a full build and `layout_check.py`, and look at every page PNG.

Page files, the outline, and the notes do not change.

### 5.4 Theme icons and SVG rasterization: `tools/theme_icons.py`, `tools/svg_raster.py`

```
python3 engine/tools/theme_icons.py <deck> [--all] [--size 512] [--dry-run] [--workers 4]
python3 engine/tools/svg_raster.py <in.svg> <out.png> [--height PX] [--width PX] [--size PX] [--color RRGGBB]
```

**theme_icons.py** renders the icons a deck uses in its theme colors:

- The theme directory is `theme` in deck.config.js (default `<deck>/theme`) and must hold a theme.json; single-color icons use `color.text` (`grey` variant) and `color.accent` (`accent` variant). The icon library is `iconDir` (`null` = `research-skills/examples/icons`) with `<source>/<name>.svg` files and a `manifest.csv`.
- Which icons: every string literal in `icon(<slide>, "<source>/<name>", …)` calls in `slides/*.js` and `slides/_lib/*.js`; calls whose name is not a string literal are printed as NOTEs and skipped. `--all` renders every icon of `manifest.csv` instead.
- Output: `<theme dir>/icons/png/<source>/<name>.png` (single-color icon in the text color) and `<name>_accent.png` (single-color icon in the accent color). A multi-color icon gets one `<name>.png`, copied from `<iconDir>/png/` (rendered in its own colors when that file is missing), and no accent variant. Every listed PNG is rewritten on each run, since it depends on the theme colors; `--dry-run` prints the plan only. `--size` is the PNG side in pixels; `--workers` is the number of parallel Chrome processes.
- It writes into the directory `theme` names: when the deck uses a shared theme (such as the engine's neutral theme), the icons go into that shared directory.
- Exit codes: 0 done, 1 some icon failed to render, 2 usage error (no deck.config.js or theme.json, unreadable colors, or icons to render but no headless Chrome).

**svg_raster.py** rasterizes one SVG to a transparent PNG with headless Chrome; theme_icons.py and theme_from_pptx.py both use it:

- With only `--height` or only `--width`, the other side follows the SVG's viewBox aspect ratio; both may be given; `--size` makes a square. At least one is required.
- `--color` recolors a single-color SVG only: an SVG is single-color when it uses `currentColor` or at most one explicit color and embeds no `<image>`; recoloring replaces `currentColor` or that one color, or sets `fill` on the root element when there is no explicit color. Multi-color SVGs keep their own colors. The rule is the same as in `examples/icons/render_pngs.py`. The SVG on disk is never modified.
- Browser: `$DECK_CHROME` when it is set (and nothing else then), otherwise the first of `google-chrome`, `chromium-browser`, `chromium` on `PATH`.
- Exit codes: 0 written, 2 error (bad arguments, no Chrome, unreadable SVG, rendering failed).

## 6. Plotting: the `plotting/` package

Instead of one large script (`make_figures.py`) for all figures, a deck has a package with one module per section, so several agents can each own a module:

```
plotting/
  __init__.py
  style.py        reads the theme: FULL / HALF / DPI, colors, fonts, apply_style(), save(); shared by all modules. Theme directory from
                  env DECK_THEME (set by plot.py from deck.config.js theme), else ../theme; figure directory from DECK_FIG_DIR, else ../figures
  common.py       data loading and small helpers shared by modules; registers no figures; may export INPUTS
  <section>.py    figure modules such as survival.py, methods.py; one owner (agent or person) at a time
```

- A figure module ends with `FIGURES = {name: callable}` and `INPUTS = [result table path, …]`, for example:

  ```python
  FIGURES = {"survival_km_tamoxifen": fig_km}
  INPUTS = ["results/current_results.csv"]
  ```

  Each callable returns `(figure, stats)`. The stats must be JSON-serializable and must contain every number shown on the slide.
- The registered name is the PNG name and starts with the section name (`survival_km_tamoxifen`), so modules cannot collide.
- Figure modules do not import each other; they depend only on `style`, `common`, and third-party libraries. Slow or side-effecting imports (scanpy and the like) go inside functions.
- Figures are always drawn at on-slide size (`style.FULL`, `HALF`, or custom) and `save()` uses no tight bbox, so font sizes are on-screen sizes; the rules are in [figures.md](../../../shared/figures.md).

**Entry point** `python3 engine/tools/plot.py <deck> [--only a b …] [--out-dir <dir>] [--list]`:

- It sets `DECK_THEME` (the deck.config.js `theme`, relative to the deck; `engine/themes/neutral` with a WARNING when that directory does not exist, and `engine/themes/neutral` without one when there is no deck.config.js or no `theme` field) and `DECK_FIG_DIR` (`figDir`, default `<deck>/figures`; `--out-dir` when given), then puts `<deck>` on `sys.path` and imports `plotting`. deck.config.js is read with regular expressions for the `theme:` and `figDir:` strings only; Node is not run.
- It knows no figure by name: it imports every module of `plotting/` except `style`, `common`, and `_*`, and merges their `FIGURES` / `INPUTS`. A name registered by two modules exits with code 2 and names both modules.
- It calls `style.apply_style()` when defined. Each figure is saved by `style.save(fig, name)` when defined, else by `fig.savefig(<fig dir>/<name>.png, dpi=<style.DPI, or the theme dpi, default 200>, facecolor="white")` without a tight bbox; the figure is then closed.
- It writes `figures/<name>.png` and `figures/run_meta/<name>.json`: `{figure, png, module, stats, inputs, versions, created, theme}` (`theme` = the theme directory used, i.e. `DECK_THEME`), where `inputs` is the module's `INPUTS` plus `common.INPUTS`. `--only` writes only its own figures' files, so parallel runs never overwrite each other.
- `--out-dir` writes the PNGs and run_meta elsewhere (regression runs) and leaves `figures/` untouched. `--list` prints registered names and their modules and draws nothing.
- Exit codes: 0 done; 1 a figure failed or did not return `(figure, stats)` (traceback printed, later figures not drawn); 2 usage or registry error (no deck directory, duplicate name, unregistered name in `--only`).
- **Always pass `--only` in parallel work.** A full redraw is done only by the integrator, after a theme change.

## 7. Outline: `outline/`

The format is documented in [reference/outline-format.md](../reference/outline-format.md). Key points:

- `outline/README.md` is the index: conventions, a table of contents (each chapter file names the pages it covers as `{{keyA}}–{{keyB}}`), and two generated blocks, `pages:counts` and `pages:table` (§8.4). Only the integrator rewrites the generated blocks, with `pages.py --table --write`.
- One file per chapter, `NN_<chapter>.md`, with one block per page whose heading carries `{{key}}`. A block records the Message (the exact on-screen sentence), the Figure (registered name in `plotting/<module>.py`), every displayed number and its source (table row/column or run_meta key), possible over-reading, and the status (✅ / ⚠️ / ✏️).
- Living documents use `{{key}}`, `{{key.title}}`, and `{{key.page}}` instead of handwritten page numbers or titles; anything in backticks is neither expanded nor checked.
- History goes into `CHANGELOG.md`; chapter files describe the current state only.

## 8. Build and data files

### 8.1 build.js command line

```
node engine/js/build.js <deck> [--list] [--list-sections]
                               [--only k1,k2 | --sections a,b] [--out <file.pptx>] [--png]
                               [--release] [--pdf | --no-pdf]
```

- **Collecting pages**: reads `slides/*.js` (not recursive, skipping `_*`) and validates key, `section`, `order`, and `build`; all problems are listed at once, exit code 2. Sort order: section order from `sections`, then `order`.
- **Strict and lenient**: full builds (default, `--release`, `--out` alone) and `--list` / `--list-sections` require every page file to be valid. Partial builds (`--only` / `--sections`) stop only for problems that concern a selected page (or selected section) or no page in particular (e.g. no `slides/`), or for an unknown `--only` key or `--sections` name. Problems in page files outside the selection are a WARNING ("other page files have problems (not built here; page numbers may be off)") and the build goes on, so another agent's half-edited page cannot block a self-check. Invalid pages are left out of the page order, so footer page numbers may then be off.
- **Default (no options)**: full build to `<outDir>/<name>_wip.pptx`, `.pages.json`, and `.pdf`, replacing the previous wip. It writes a temporary file and renames it at the end, so a failed build leaves the previous wip untouched.
- **`--release`**: writes `<outDir>/<name>_v<N>.pptx` (N = highest existing version + 1) with `.pages.json` and `.pdf`; existing versions are never overwritten (nor an existing PDF of that name). Cannot be combined with `--out`, `--only`, or `--sections`.
- **`--out <file.pptx>` alone**: builds the whole deck into that file (relative to the current directory, replaced if it exists), without the lock and without a PDF by default. `--out` must end in `.pptx` and must not be the wip or a release name. The example decks are built this way (`examples/slides/render.sh`).
- **Full-build lock**: the default and `--release` builds first create `<outDir>/.build.lock` exclusively (content: pid and start time) and remove it at the end, also on failure or a signal. If the lock exists and its pid is alive, the build exits with code 3 ("another full build is running"); if the pid is gone, a WARNING is printed and the lock is taken over. A lock with no readable pid (another build may have just created it) counts as live for 10 s after its last change and is taken over after that.
- **Partial builds** `--only k1,k2` or `--sections a,b` require `--out` (in the agent's scratchpad), never write the wip or a release, and do not take the lock. Pages come out in deck order and **footers carry the full-deck page numbers**, computed from the section and order of all page files without building the other pages. No PDF by default. `--only` and `--sections` cannot be combined.
- **`--png`** implies the PDF (partial builds too) and renders each page with pdftoppm at 60 dpi to `<out stem>_png/<page:02d>-<key>.png`; the directory is replaced on every build. `--png` with `--no-pdf` is an argument error (exit code 2). `--pdf` / `--no-pdf` force or skip the PDF.
- **`--list`** prints the full page order (page, section, order, key; hidden pages marked `(hidden)`) and builds nothing; **`--list-sections`** prints each section key with its page count and keys.
- Supplementary pages are hidden (`show="0"`). The PDF is converted from a temporary copy with `show="0"` removed (LibreOffice < 7.4 skips hidden slides), so PDF pages match pages.json rows one to one. soffice runs with its own temporary `-env:UserInstallation` profile, so conversions can run in parallel; it is looked up in `$DECK_SOFFICE`, `PATH`, `/usr/bin/soffice`, and `/opt/libreoffice*/program/soffice`. Missing soffice or a failed conversion only prints a WARNING: the PPTX is written, the old PDF is left as it was, exit code 0. Missing pdftoppm is likewise a WARNING.
- Notes are applied as in §8.3; color and font literals in page files are WARNINGs (§3); a `notes/*.md` without a page file and a leftover v1 `notes.json` each produce a WARNING.
- pptxgenjs is resolved from `NODE_PATH`, `<deck>/node_modules`, then `<research-skills>/node_modules`; when it is missing the build exits with code 1 and suggests `npm install pptxgenjs`.
- **Exit codes**: 0 ok; 1 build failure (a page's `build()` threw, pptxgenjs missing, a write failed), previous output kept; 2 invalid deck or arguments (deck.config.js, page files, order clashes, a page that did not make exactly one slide, in which case nothing is written); 3 another full build holds the lock.
- The last stdout line is the PPTX path.

### 8.2 pages.json (written next to the PPTX on every build as `<output stem>.pages.json`)

```json
[{"page": 1, "title": "Title", "section": "title", "order": 10, "builder": "sTitle"},
 {"page": 2, "title": "Recurrence-free Survival", "section": "results", "order": 20, "builder": "sKmTamoxifen"}]
```

- One row per line. `page` is the page's position in the full deck (from 1, including the title and supplementary pages); partial builds write the same number. `builder` is the key.
- Page titles may repeat (progressive emphasis: one title on two pages). build.js and pages.py only print a WARNING, and `{{key.title}}` still resolves.
- A slide without a title (`newSlide(pres, null, n)`, e.g. a section divider) has `title: null`; pages.py shows it as an empty title.
- A repeated key or page number is FATAL in pages.py (exit code 2).

### 8.3 Speaker notes: `notes/<key>.md`

- One plain-text UTF-8 file per page, one paragraph per line. The build replaces the page's notes with it and splits it into one `<a:p>` per line. **An empty file clears the page's notes** (the `addNotes()` text too). Pages without a file keep their `addNotes()` text.

```
python3 engine/tools/pull_notes.py <deck> [pptx] [--dry-run | --write] [--pages <pages.json>]
```

- `pptx` is optional and defaults to the highest-numbered release `<outDir>/<name>_v<N>.pptx` (an error when there is no release: pass the speaker's PPTX). pages.json defaults to `<outDir>/<name>_wip.pages.json`. Without `--write` nothing is written (`--dry-run` only makes that explicit).
- Slides are matched to keys by title, trying in order: (a) the first slide is the first pages.json row when that row's title is `Title` or equals the slide's title; (b) aliases in `notes/_aliases.json`, `{"<PPTX slide title>": "<key>"}`, with a title that occurs several times in the PPTX addressed as `"<title>"`, `"<title>#2"` …; (c) the title equals exactly one pages.json title and occurs once in the PPTX. A repeated title is never matched automatically and needs aliases.
- **Writes only changed** `notes/<key>.md` files (both sides are normalized first, so trailing whitespace, CRLF, or a missing final newline is not a change). Empty notes in the PPTX are written as an **empty notes file** (the build then clears that slide's notes) when the page has no notes file yet or its file holds other text.
- **Never deletes a file.** Notes files whose key is not in pages.json are listed (kept; delete them by hand if the page is gone).
- A slide whose title matches nothing, repeats without an alias for that occurrence, or maps to a key that is not in pages.json or already taken is not written: it is listed in the report and in `notes/_unmatched.json` (`{slide, title, occurrence, reason, notes}` per entry), which `--write` rewrites every time (`[]` when every slide matched). Add an alias and run again.
- `--write` first copies every existing file it is about to change to `<deck>/.backups/<timestamp>/notes/` (timestamp `YYYYMMDD_HHMMSS`), then writes.
- Notes text comes from the body placeholder of the notes page: paragraphs and soft line breaks become line breaks; formatting (bold, font sizes) is not kept. Text typed after the number in the slide-number placeholder is kept as an extra paragraph.
- Exit codes: 0 done (also when some slides are unmatched); 2 FATAL problem with the deck, the PPTX, pages.json, or `_aliases.json`.
- Once the speaker edits notes in PowerPoint, the speaker's PPTX is the source of truth; the integrator runs `--write`.

### 8.4 Outline generated blocks (maintained by tools/pages.py)

```
python3 engine/tools/pages.py [<deck>] [--check | --show <file> | --keys | --table [--write]] [--pages <pages.json>] [--ignore-file <txt>]
```

The language of the generated blocks is `lang` in deck.config.js. `lang: "en"` (the default):

```markdown
<!-- pages:counts:start -->
N slides (section key and slide count): `title` 1 · `results` 2 · …
<!-- pages:counts:end -->

<!-- pages:table:start -->
| Page | Section | Subsection | Slide title | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | … |
<!-- pages:table:end -->
```

`lang: "zh"`:

```markdown
<!-- pages:counts:start -->
共 N 页（节 key 和页数）：`title` 1 · `results` 2 · …
<!-- pages:counts:end -->

<!-- pages:table:start -->
| 页 | 节 | 小节 | 页标题 | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | … |
<!-- pages:table:end -->
```

- The Subsection and Note columns are handwritten and kept per key by `--table --write`; the other columns come from pages.json. New rows get the placeholders `—` and `(Note to be added)` (`zh`: `（待补 Note）`); keys that are no longer pages are printed and their Note is dropped.
- Table rows are read by position, so a header in either language (or v1's `key（builder）`) is understood, and a Note that is still either language's placeholder is rewritten in the deck's language. After changing `lang`, `--table --write` switches the blocks; until then `--check` reports them as stale.
- Files scanned: `README.md`, `TODO.md`, and `outline/*.md` (with `lang: "zh"`, the `.zh-CN.md` counterparts are preferred); the other language is skipped and `outline/archive/` is never read.
- `--check` (default, read-only) reports: [k] a `{{key}}` with no page or a malformed `{{…}}`; [r] a handwritten page reference `P<digits>` outside code and generated blocks (handwritten Note cells included); [b] a key-like name `sXxx` in inline code that is neither a pages.json key nor a page file; [g] a stale generated block. Exit code 1 on any error. `--show <file>` prints the file with every token resolved (exit code 1 for an unknown key), `--keys` prints page, key, section, and title of every page, and `--table` without `--write` prints the diff only; `--write` first copies each changed file to `<deck>/.backups/<timestamp>/<relative path>`.
- The default pages.json is `<deck>/<outDir>/<name>_wip.pages.json`. A deck built with `--out` (such as the example decks in `examples/slides/`) has no wip: pass `--pages <out stem>.pages.json`.
- Hits that are not page numbers (e.g. the protein P53): add a `file:regex` line to `<deck>/pages_ignore.txt` (`--ignore-file` overrides the file); a line containing `<!--pages:ignore-->` is skipped by the [r] check.
- A missing or unreadable pages.json, a repeated key or page number, or an unreadable `name` in deck.config.js is FATAL, exit code 2.

### 8.5 Layout check: `tools/layout_check.py`

```
python3 engine/tools/layout_check.py [<deck>] [--pptx <f>] [--pdf <f>] [--pages-json <f>] [--pages N …] [--png-dir <dir>] [--tol <pt>]
```

- Read-only. Defaults to `<deck>/<outDir>/<name>_wip.{pptx,pdf,pages.json}`; without a deck, pass `--pptx` and `--pdf`. The title size comes from the deck theme's `size.title` (fallback: neutral, then 28 pt). Needs poppler's `pdftotext`.
- Reports per page: HIDDEN-TITLE (a title covered by a picture higher in the z-order), TITLE-OVER-PIC, TITLE-WRAP (title wraps; the gap to the element below is reported), HIDDEN-TEXT, TEXT-OVER-PIC, TEXT-OVER-TEXT. `--pages` limits the check to those pages; `--png-dir` renders the flagged pages there with `pdftoppm -r 60` as `page_<NN>.png`; `--tol` is the overlap threshold in points (default 3). Expect a few false positives; the rendered page is the final word.
- Exit codes: 0 clean (or only TITLE-WRAP with a gap of 4 pt or more), 1 problems found, 2 usage error (no pdftotext, input files missing or unreadable).

## 9. Parallel editing

| Operation | Writes only these files | Who |
|---|---|---|
| Add a page | `slides/<key>.js`, optionally `notes/<key>.md`, its chapter's outline block, and new figures in a figure module | the page owner |
| Edit a page | same as above | the page owner |
| Move a page | the page file's `section` / `order` (`move.py <key> --after <key>`, one file only) | the page owner |
| Delete a page | delete `slides/<key>.js` and `notes/<key>.md`, mark the outline block as deleted | the page owner; the integrator refreshes the generated blocks |
| Draw a figure | `plotting/<module>.py`, `figures/<name>.png`, `figures/run_meta/<name>.json` | the module owner |
| Edit notes | `notes/<key>.md` | the page owner; the integrator runs `pull_notes --write` |
| Primitives, theme, sections, shared code | `primitives.js`, `theme/` (including files written by `theme_from_pptx` and `theme_icons`), `deck.config.js`, `slides/_lib/`, `plotting/style.py`, `plotting/common.py` | the integrator, append-only |
| Full build, release, `--respace`, `pages.py --table --write`, `pull_notes --write`, full `plot.py`, commit | wip / release outputs, generated blocks, `notes/`, `figures/`, git | the integrator, serially |

- **Self-check**: each agent builds only its own pages with `build.js <deck> --only <own keys> --out <scratchpad>/x.pptx --png`, inspects the PNGs, and draws its figures with `plot.py <deck> --only <own figures>`, without waiting for a full build. Partial builds are lenient about pages outside the selection (§8.1), so another agent's half-edited page does not block a self-check.
- **Remaining conflicts surface at build time**: two pages with the same `order` in a section (build.js error, fixed by one of the page owners) and two modules registering the same figure name (plot.py error). When two agents edit the same chapter file, they use Edit for each change, never Write for the whole file (Edit fails when the file changed and requires a re-read).
- **Wording dependencies** ("next slide", "as shown on the previous slide") cannot be managed at the file level. `move.py` prints such wording found in the moved page and its old and new neighbors (page files and notes) for the owner to fix.
- **git**: parallel agents each use their own worktree and the integrator merges. In a shared working tree, the integrator commits explicit paths and **never uses `git add -A`**, so another agent's half-edited files are not committed.
- Parallel safety is not content consistency: the integrator reviews how the same number is stated across pages, and the wording of conclusions, against the outline.

## 10. Practices kept from a deck in use

These practices were proven in a 90-page project deck and are kept as is: wip is written to a temporary file and renamed; releases increment `v<N>` and never overwrite; PDF and PPTX are produced together, with a separate soffice profile; supplementary pages are hidden in the PPTX and shown in the PDF; `pages.json` with `{{key}}` page references; notes stored as data and synced back from the speaker-edited PPTX; the main figure at the bottom of the z-order; `layout_check` for collisions; plotting split into modules by section with one run_meta per figure; the outline split by chapter, with history in CHANGELOG and old versions in archive.

What differs from that deck serves parallel work and theme changes: there, one `slides_<section>.js` held a run of pages and the page order lived in one `SLIDES` list (every move or addition edited it), the notes were one `notes.json` rewritten as a whole, and design constants lived in `style.js`.

## 11. Language policy

All generated deliverables are English: slide text, figure text, tables, source lines, speaker notes, PPTX, PDF, and preview images. `lang: "zh"` only changes the blocks pages.py writes into outline documents. User-facing repository documentation is maintained as paired `X.md` (English, the GitHub default) and `X.zh-CN.md` files, with a language switcher on the first line of both.

**English** | [简体中文](README.zh-CN.md)

# Deck template

A complete five-slide deck in the engine's v2 layout (title, two result slides, summary, a hidden supplementary table) on the public GBSG2 trial data. It builds as is, so copy it, check that it builds, then replace the content. The interface is defined in [../SPEC.md](../SPEC.md); the tools are described in [../tools/README.md](../tools/README.md).

```
deck.config.js        name, title, paths, theme, lang, refs, section order
theme/theme.json      colors, fonts, sizes, geometry, logo (a copy of engine/themes/neutral)
slides/<key>.js       one page each: {section, order, build(pres, n, P, ctx)}; shared layouts in slides/_lib/layouts.js
notes/<key>.md        speaker notes, one per page; notes/_aliases.json (empty) for pull_notes.py
outline/              README.md (index + generated page table) and one file per chapter, each with a .zh-CN.md mirror
plotting/             style.py (theme), common.py (data), results.py (figures of the results section)
figures/              PNGs drawn at on-slide size + run_meta/<name>.json with every number shown
output/               build products; only *.pages.json is tracked (see .gitignore)
.gitignore            ignores output/*.pptx, *.pdf, *_png/, the build lock, .backups/, notes/_unmatched.json
```

Below, `E` is `<research-skills>/skills/results-deck/engine` and commands run in the deck directory.

## Start a deck

```bash
cp -r $E/template <project>/presentation/my_deck && cd <project>/presentation/my_deck
rm -rf output/*.pptx output/*.pdf output/*_png               # copied build products (git-ignored)
NODE_PATH=<node_modules> node $E/js/build.js . --png      # smoke test: 5 pages, no WARNING lines
```

After copying, delete `output/*.pptx`, `output/*.pdf`, and `output/*_png/`: they are git-ignored build products of the template and are rebuilt by the smoke test. Keep `output/*.pages.json` (tracked; `pages.py --check` resolves `{{key}}` against it). Then set `name`, `title`, `refs`, and `sections` in `deck.config.js`, and replace the pages, notes, outline, and figures. Keep `theme` written explicitly (`"theme"`): the plotting and layout tools fall back to the engine's neutral theme when the field is missing.

## Edit pages, notes, and the outline

- A page is `slides/<key>.js`; the file name is the key used everywhere (`{{sKm}}` in the outline, `notes/sKm.md`, `--only sKm`). `section` must be in `sections`; `order` sorts pages within a section (10, 20, 30 …, insert with 25).
- Page files take colors, fonts, and geometry from `P.T` / `P.G` and never hard-code them (the build warns). A layout used by two pages goes into `slides/_lib/`, as `titleSlide`, `numberedTakeaways`, and `centeredTable` in `slides/_lib/layouts.js`.
- Speaker notes go in `notes/<key>.md` (one paragraph per line); they replace any `addNotes()` text of the page, and an empty file clears the page's notes. After the speaker edits the pptx, `python3 $E/tools/pull_notes.py . <pptx>` reports the changes and `--write` brings them back (without `<pptx>` it reads the newest release `output/<name>_v<N>.pptx`).
- The outline keeps the exact on-screen sentences, figure names, numbers with their run_meta keys, and status. Write `{{key}}` instead of page numbers. Move a page with `python3 $E/tools/move.py . <key> --after <key>` (or `--before <key>`, `--to <section>`); it edits only that page file.

## Draw figures

```bash
python3 $E/tools/plot.py . --only results_km    # one figure: figures/results_km.png + figures/run_meta/results_km.json
python3 $E/tools/plot.py . --list               # registered names: results_km, results_forest
python3 $E/tools/plot.py .                      # all figures (after a theme change)
```

One module per section in `plotting/`, ending with `FIGURES = {name: callable}` and `INPUTS = [...]`; names start with the section (`results_km`). Each callable returns `(figure, stats)`, and `stats` must hold every number the slide shows. Needs matplotlib, numpy, pandas, and lifelines.

## Build

```bash
NODE_PATH=<node_modules> node $E/js/build.js .                     # output/<name>_wip.pptx + .pages.json + .pdf
NODE_PATH=<node_modules> node $E/js/build.js . --only sKm --out /tmp/x.pptx --png   # one page, look at /tmp/x_png/
NODE_PATH=<node_modules> node $E/js/build.js . --release           # output/<name>_v<N>.pptx, never overwritten
NODE_PATH=<node_modules> node $E/js/build.js . --list              # page order, nothing built
```

The PDF needs LibreOffice and `--png` needs Poppler; without them the build only warns. The supplementary section is hidden in the pptx and included in the PDF. In a partial build (`--only`), footers carry the full-deck page numbers, and problems in other page files are only warnings.

## Switch the theme

Generate a theme from a template pptx, point `theme` in `deck.config.js` at it, and recolor the icons:

```bash
python3 $E/tools/theme_from_pptx.py <template>.pptx --out theme_<name>   # then set theme: "theme_<name>"
python3 $E/tools/theme_icons.py .
```

`theme_from_pptx.py` reads colors, fonts, the title box, and the logo from the template and lists the fields it kept from the neutral theme; check `color.accent` by hand, since the template's accent1 is often not the brand color. Page files, notes, and the outline do not change; redraw the figures with `plot.py .` when the figure sizes, dpi, plot fonts, or plot colors changed, then rebuild.

## Check

```bash
python3 $E/tools/pages.py . --check               # {{key}} references, hand-written page numbers, stale generated blocks
python3 $E/tools/pages.py . --table --write       # refresh the generated blocks in outline/README.md after a build
python3 $E/tools/layout_check.py .                # titles or text covered by figures, text over text
```

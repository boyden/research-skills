**English** | [简体中文](README.zh-CN.md)

# results-deck engine

The engine turns a deck directory into a 16:9 PPTX, along with a PDF, a page table (`pages.json`), and PNG previews. A deck directory holds one page file per slide, figures drawn at on-slide size, speaker notes, an outline, and a theme. Each page lives in its own file and each figure module has one owner, so several agents can work on one deck in parallel; the style lives in a theme directory, so a new template only means a new theme.

The contract (deck layout, page modules, theme fields, file formats, CLI flags, exit codes, who owns which file) is [SPEC.md](SPEC.md). The command line of every tool is in [tools/README.md](tools/README.md).

## Quick start

`E` is `<research-skills>/skills/results-deck/engine`; the commands run in the deck directory.

```bash
# 1. Copy the template, then delete its build products (git-ignored, rebuilt at any time)
cp -r $E/template <project>/presentation/my_deck && cd <project>/presentation/my_deck
rm -rf output/*.pptx output/*.pdf output/*_png

# 2. Draw figures from the plotting/ package: figures/<name>.png + figures/run_meta/<name>.json
python3 $E/tools/plot.py . --only results_km          # one figure; without --only: every figure

# 3. Build the full deck: output/<name>_wip.pptx + .pages.json + .pdf
NODE_PATH=<node_modules> node $E/js/build.js .

# 4. Self-check your own pages without a full build, then look at /tmp/x_png/*.png
NODE_PATH=<node_modules> node $E/js/build.js . --only sKm,sForest --out /tmp/x.pptx --png

# 5. Check page references and layout
python3 $E/tools/pages.py . --check
python3 $E/tools/layout_check.py .

# 6. Switch the theme: generate one from a template PPTX, point `theme` in deck.config.js at it, recolor the icons
python3 $E/tools/theme_from_pptx.py <template>.pptx --out theme_<name>
python3 $E/tools/theme_icons.py .
```

After step 1, set `name`, `title`, `refs`, and `sections` in `deck.config.js` and replace the pages, notes, outline, and figures; [template/README.md](template/README.md) walks through this. After step 6, read the report the theme tool prints (check the accent color by hand), redraw the figures when the figure sizes, dpi, plot fonts, or plot colors changed, and rebuild ([SPEC.md](SPEC.md) §5.3).

Requirements: Node.js with `pptxgenjs` (found via `NODE_PATH`, `<deck>/node_modules`, or `<research-skills>/node_modules`) and Python 3.10+. Optional: LibreOffice for the PDF; Poppler (`pdftoppm`, `pdftotext`) for PNG previews and `layout_check.py`; matplotlib for `plot.py` (the template's figures also need numpy, pandas, and lifelines); headless Chrome for `theme_icons.py` and SVG-only logos. Without LibreOffice or Poppler the build only warns and still writes the PPTX.

## Components

| File | Purpose |
|---|---|
| [js/build.js](js/build.js) | Collects and orders `slides/<key>.js`; builds wip, release, `--out`, and partial (`--only` / `--sections`) PPTX files with `pages.json`, notes, hidden supplementary pages, PDF, and PNGs; holds the full-build lock |
| [js/primitives.js](js/primitives.js) | Theme-driven layout primitives (`newSlide`, `figure`, `table`, `conclusion`, `source`, `cite`, `abbr`, `icon`, arrows …) and the live theme views `T` / `G` |
| [themes/neutral/theme.json](themes/neutral/theme.json) | The default theme and the complete list of theme fields |
| [tools/plot.py](tools/plot.py) | Draws the figures registered in a deck's `plotting/` package; one run_meta per figure |
| [tools/pages.py](tools/pages.py) | Checks and expands `{{key}}` page references; regenerates the outline's page-count and page-table blocks |
| [tools/pull_notes.py](tools/pull_notes.py) | Syncs speaker notes from a speaker-edited PPTX back into `notes/<key>.md` |
| [tools/move.py](tools/move.py) | Moves a page by editing only its `section` / `order`; `--respace` renumbers a section |
| [tools/theme_from_pptx.py](tools/theme_from_pptx.py) | Generates a theme directory (theme.json + pictures) from a template PPTX |
| [tools/theme_icons.py](tools/theme_icons.py) | Renders the icons a deck uses in its theme colors |
| [tools/svg_raster.py](tools/svg_raster.py) | Rasterizes an SVG (optionally recolored) to a transparent PNG with headless Chrome |
| [tools/layout_check.py](tools/layout_check.py) | Finds titles and text covered by pictures or colliding with other text in the built PDF |
| [template/](template/README.md) | A complete five-slide deck to copy as the start of a new deck |

## Language policy

All generated deliverables are English: slide text, figure labels, tables, source lines, speaker notes, PPTX, PDF, and preview images. Repository documentation is maintained as paired `X.md` and `X.zh-CN.md` files, with English as the GitHub default.

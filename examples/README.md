**English** | [简体中文](README.zh-CN.md)

# examples

Examples referenced in `shared/` and in the skill docs: figures, example decks, icons. All data and icons are public and redistributable.

| Directory | Contents |
|---|---|
| `figures/` | Example figures (PNG) and one `run_meta/<figure name>.json` per figure, drawn by the [plotting/](plotting/__init__.py) package through the engine's [plot.py](../skills/results-deck/engine/tools/plot.py) |
| [slides/](slides/) | Example decks of classic slide types: results (`results_examples`) and narrative (`narrative_examples`), with pptx, PDF and per-slide previews |
| [icons/](icons/README.md) | Open-license icons (AI / LLM / VLM / Agent, computational pathology, spatial omics, general research), with SVG, 512 px PNG and the overview sheet `icon_sheet.png` |

## Example figures

Every figure is drawn at its actual size on a 16:9 slide. Results figures are drawn full width (12.1 × 4.6 in) or half width (5.9 × 4.6 in); `layout_*` (8.0 × 4.5, i.e. 0.6 × the slide) and `three_line_table_example` (8.0 × 3.2) are small illustrative figures:

```bash
cd research-skills
python skills/results-deck/engine/tools/plot.py examples                    # all; needs matplotlib, numpy, pandas, lifelines, scikit-learn
python skills/results-deck/engine/tools/plot.py examples --only km_example  # only some
python skills/results-deck/engine/tools/plot.py examples --list             # registered names and their modules
```

`examples/` has no `deck.config.js`, so the neutral theme is used and the figures go to `figures/`. The package follows the engine layout ([SPEC.md](../skills/results-deck/engine/SPEC.md) §6): `style.py` (sizes, colors and fonts from the theme), `common.py` (data loading and statistics), and one figure module per group: `layouts.py` (`layout_*`), `survival.py` (`km_example`, `forest_example`), `discrimination.py` (`roc_example`, `auc_bars_example`), `tables.py` (`three_line_table_example`).

| Registered name | Contents |
|---|---|
| `layout_figure_conclusion` | Layout zones of the most common slide, figure + conclusion (title, figure frame, conclusion sentence, source line); the boxes state that the figure is drawn at its on-slide size and placed 1:1 |
| `layout_*` | Layout zones of the other 16 slide types, drawn to scale, with the coordinates of the neutral theme ([theme.json](../skills/results-deck/engine/themes/neutral/theme.json)) and of the page files of the two example decks; embedded under each slide type in [slide-types.md](../skills/results-deck/reference/slide-types.md) |
| `km_example` | Two square KM panels: censoring marks, at-risk table, HR / Cox p / C-index / log-rank p |
| `roc_example` | Two square ROC panels: AUC [95% bootstrap CI], n, number of positives |
| `auc_bars_example` | AUC bar chart, drawn from 0.5 (chance) |
| `forest_example` | Univariable Cox forest plot, with a three-line-table number column on the right |
| `three_line_table_example` | A three-line table drawn into a figure (cohort baseline characteristics) |

- Data: the GBSG2 breast cancer trial, 686 node-positive patients, endpoint recurrence-free survival, shipped with lifelines (`lifelines.datasets.load_gbsg2`).
  - The data come from the R package TH.data (GPL-2) and are redistributed by lifelines (MIT). This repo does not include the data file: the script reads it from lifelines at run time, and only the figures drawn from it are committed.
  - Original study: Schumacher M, et al. *J Clin Oncol* 12.10 (1994): 2086–2093.
  - Common citation for the dataset: Sauerbrei W, Royston P. *J R Stat Soc A* 162.1 (1999): 71–94.
- The bootstrap uses 2000 resamples and `random_state = 0`, recorded in each figure's run_meta.
- The numbers here only demonstrate how to draw the figures. They do not support any clinical conclusion.

## Icons

For the full index (source, license, author and original URL of every icon), see [icons/README.md](icons/README.md); the per-icon list is in `icons/manifest.csv`.
CC BY icons that require attribution are listed separately in the index. When you use one, write the attribution in that slide's source line or on the deck's credits slide.
For other open-license icon libraries and their attribution requirements, see [shared/figures.md](../shared/figures.md), "Icons and external images".

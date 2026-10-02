**English** | [简体中文](figures.zh-CN.md)

# Figures

Shared by decks and papers. The example figures are drawn from public data by the [examples/plotting/](../examples/plotting/__init__.py) package (`python skills/results-deck/engine/tools/plot.py examples`).

## 1. Draw at final size

**Fix the slot first, then draw.** `figsize` is the size the figure occupies on the final page, and the font size in the code is the font size the reader sees.
Place figures 1:1: no scaling, cropping or stretching.

| Target | Slot (width × height, inches) | Font size |
|---|---|---|
| 16:9 slide (13.333 × 7.5), full width between title and conclusion sentence | 12.1 × 4.6, top edge y = 1.1 | Body 12 pt, minimum 11 pt |
| Same, two side by side | 5.9 × 4.6 | Same |
| Same, two-row KM grid (two endpoints, one above the other) | 12.1 × 4.9, top edge y = 0.95 | Same |
| Paper single / double column | Per target journal (commonly about 3.5 / 7.2) | Per journal requirements, commonly 7–9 pt |

- Drop to 10 pt only for long lists that cannot fit at 11 pt (forest plots with 20+ rows, dozens of category names).
- Result figures are always placed 1:1. Only thumbnails and external images are shown scaled; their font size is counted at the displayed size.
- Why: if you draw large and then shrink, font sizes differ from page to page, and figures from different sources on one page do not line up.

![Slide layout zones](../examples/figures/layout_figure_conclusion.png)

## 2. Text and fonts

- All text in figures is English: titles, axis labels, legends, annotations, category names.
- Labels meant for figures are written in English in the data table itself, not translated at plotting time. Fixes to display names (spelling, capitalization) live in one function.
- Font `["Arial", "DejaVu Sans"]`, `pdf.fonttype = 42` (text stays editable in the PDF), `axes.unicode_minus = False`.
- Chinese fonts easily turn into boxes on other people's machines; this is one reason figures contain no Chinese.

## 3. Shape and color

- Draw ROC, KM and scatter plots whose two axes share a scale as squares (`ax.set_box_aspect(1)`).
- If a figure has any square panel, all its square panels are square and the same size. If they do not fit, put them in one row instead of shrinking them to tiny squares.
- Use only one accent color and gray for everything else; tints of the accent color count as the same color. The accent color marks only what is "worth looking at" (e.g. rows with q < 0.05); it is not used to tell categories apart.
- With many categories, use one fixed categorical palette; a category keeps the same color across the whole output.

## 4. Survival plots (when applicable)

- **KM colors follow curve position, not group**: the lower curve (worse prognosis) is red, the upper one blue, and the middle one gray when there are three groups.
  Lower and upper are decided by RMST over the shared follow-up period, so crossing curves are not misjudged.
- **Each KM panel states four quantities**:
  - HR [95% CI] (per SD for continuous variables, yes vs no for binary ones);
  - Cox p;
  - C-index of the univariate model;
  - log-rank p of the plotted grouping.
- Write each group's n in the legend.
- When a continuous variable is split at the median for the KM plot, the HR is still the per-SD HR of the continuous variable, and the log-rank p is for the plotted grouping.
- **Draw censoring marks on every KM curve**: short vertical ticks "|", in the curve's color.
- **Put a number-at-risk table under every KM panel**:
  - columns aligned with the x-axis ticks (e.g. 0, 2, 4, 6 years), one row per group, a short group name at the start of each row;
  - group names and numbers in that group's curve color;
  - compute the counts yourself (number with follow-up ≥ t) and place each one as text. lifelines' `add_at_risk_counts` resizes the axes and breaks the fixed slot.
- The at-risk table makes the square smaller, so put the four quantities to the right of the panel, not over the curves.

![KM example](../examples/figures/km_example.png)

- **Forest plots**:
  - log x-axis, reference line at 1;
  - the number columns on the right are laid out as a three-line table (see [tables.md](tables.md)), aligned on column centers;
  - rows with q < 0.05 in the accent color, the rest gray.

![Forest plot example](../examples/figures/forest_example.png)

## 4b. ROC and AUC (when applicable)

- **Draw ROC panels as squares**; several ROC panels in one figure are the same size; both axes range over 0–1.
- Draw a dashed diagonal for chance level (AUC = 0.5).
- Each panel states `AUC 0.xxx [lo–hi]`, plus n and the number of positives (`n = 686, positive = 497`).
- **CI by bootstrap** (commonly 2000 resamples, percentile method); record the random seed and the number of resamples in run_meta / the statistics table.
- When one unit of analysis has several samples (e.g. several slides or ROIs per patient), aggregate to the unit of analysis first (e.g. one score per patient) before computing AUC,
  and resample by that unit in the bootstrap too; otherwise n is inflated and the CI is too narrow.

![ROC example](../examples/figures/roc_example.png)

- **AUC bar charts**:
  - bars start at 0.5 (chance level), not at 0; the axis may extend slightly below 0.5 so that CIs crossing 0.5 show in full;
  - error bars show the 95% bootstrap CI; label each bar with its AUC (3 decimals);
  - bars whose CI excludes 0.5 in the accent color, the rest gray;
  - state the direction: for variables where low values go with the positive class, either flip the direction and say so in the label (e.g. `Tumour size, smaller`), or do not flip and plot them as they are, below 0.5; either is fine, but say which one you used;
  - when the smaller class has fewer than 5 cases, draw no bar and write "not evaluable" in that row;
  - if there is an internal test-set AUC, you may add a dashed reference line marking it.

![AUC bar chart example](../examples/figures/auc_bars_example.png)

## 5. Schematics and framework diagrams

- Arrows come in two layers:
  - between steps inside a processing band, thin gray arrows;
  - outside the band, for the flow of inputs and outputs, thick accent-color arrows.
- When several rows share the same input or output, draw only one arrow, pointing at the middle, not one per row.
- Small images and icons are each a separate image object, and text uses native text boxes; do not merge them into one picture. That way each can be edited on its own in PowerPoint / Illustrator later.
- Use only openly licensed icons and paper figures, and register their source and license (see below).

## 6. Icons and external images

| Source | License | Notes |
|---|---|---|
| [Health Icons](https://healthicons.org) ([GitHub](https://github.com/resolvetosavelives/healthicons)) | CC0 | Free to use, no attribution needed; examples in [examples/icons/](../examples/icons/) |
| [Lucide](https://lucide.dev) | ISC | No attribution needed on screen; keep the LICENSE when redistributing the source files |
| [Tabler Icons](https://tabler.io/icons) | MIT | No attribution needed on screen; keep the LICENSE when redistributing the source files |
| [Servier Medical Art](https://smart.servier.com) | Depends on where the file came from: files on the Servier site are CC BY 4.0; Servier files redistributed via Bioicons are CC BY 3.0 | Attribution required; follow that file's own license |
| [Bioicons](https://bioicons.com) ([GitHub](https://github.com/duerrsimon/bioicons)) | Varies per icon (CC0, CC BY, CC BY-SA, MIT, BSD) | Check the icon's license before use; CC BY-SA requires derivative works under the same license |
| [NIH BioArt](https://bioart.niaid.nih.gov) | Free to use, attribution required, a few items licensed differently | Attribution format: `Illustration from NIAID NIH BioArt Source (bioart.niaid.nih.gov/bioart/###)` |
| Figures from papers | Only CC BY / BY-NC / BY-NC-ND | ND does not allow adaptation; whether cropping counts as adaptation is disputed, so the safe choice is to use the figure as is; register source and license in the outline |

- Keep SVG as the master (for paper figures, and for editing in Illustrator / Inkscape). Slides use 512 px PNG: LibreOffice < 7.4 cannot render SVG embedded by pptxgenjs, so the preview would be wrong.
  matplotlib cannot read SVG; when you need one there, likewise convert it to a high-resolution PNG first.
- Register every external image used in the project: source URL, license, whether it was modified.

## 7. Engineering conventions

- Plotting scripts only read result tables; they do no analysis. If a figure is wrong, fix it in the plotting script, not in the deck or the layout software.
- Each figure has a registered name (`FIGURES = {"km_example": fig_km, ...}`); the entry point supports `--only <name>` to draw just a few,
  and each figure writes its own `run_meta/<figure name>.json`, so plotting in parallel does not overwrite anything.
- Normally use `--only` to redraw just the figures you changed; do not redraw the whole set every time.

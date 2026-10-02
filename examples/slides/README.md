**English** | [简体中文](README.zh-CN.md)

# Classic slide-type examples

Two example decks; each slide demonstrates one classic slide type. Small gray text in the top-right corner of each slide gives the slide-type name, and the speaker notes say when to use it and which rules it demonstrates.
The rules themselves are in [shared/](../../shared/) and [skills/results-deck/reference/slide-types.md](../../skills/results-deck/reference/slide-types.md).

- **Results** ([results/](results/), `results_examples`): every number comes from the public GBSG2 data. Some are taken from [../figures/run_meta/](../figures/run_meta/); the rest are computed by [results/results_stats.py](results/results_stats.py) and written to `results/results_stats.json`.
- **Narrative** ([narrative/](narrative/), `narrative_examples`): uses a fictional "AI for computational pathology and spatial omics" study to demonstrate structural slides. All results are `XX` placeholders; no numbers are made up.

Both are v2 engine decks (one file per page; the contract is in [skills/results-deck/engine/SPEC.md](../../skills/results-deck/engine/SPEC.md)):

```
<deck>/
  deck.config.js        name, sections (incl. a hidden `supplementary` section), theme, figDir, refs
  slides/<key>.js       one page per file: {section, order, build(pres, n, P)}
  slides/_lib/*.js      shared constants and layouts of this deck (source lines, abbreviation lists, ...)
  notes/<key>.md        the speaker notes of that page, one paragraph per line
```

Both decks use the engine's neutral theme in place (`theme: "../../../skills/results-deck/engine/themes/neutral"`), so they keep no theme copy; figures come from `../../figures` (examples/figures) and icons from examples/icons (`iconDir: null`).

## Build

```bash
cd research-skills
NODE_PATH=<node_modules containing pptxgenjs> bash examples/slides/render.sh            # both decks
NODE_PATH=<…> bash examples/slides/render.sh results                                 # one deck only
```

For each deck, `render.sh` runs the engine build and then moves the page PNGs into `preview/`:

```bash
node skills/results-deck/engine/js/build.js examples/slides/results \
  --out examples/slides/output/results_examples.pptx --png
```

1. `build.js` writes `output/<deck>_examples.pptx` (the supplementary page is hidden), `output/<deck>_examples.pages.json` and `output/<deck>_examples.pdf` (LibreOffice; hidden pages included);
2. `--png` renders one PNG per page at 60 dpi, which `render.sh` renames to `preview/<deck>-NN.png`.

Needs node + pptxgenjs, LibreOffice and pdftoppm. When the example figures change, redraw them first with `python skills/results-deck/engine/tools/plot.py examples --only <name …>` (from the repo root).
To list a deck's pages, run `node skills/results-deck/engine/js/build.js examples/slides/results --list`, or after a build
`python3 skills/results-deck/engine/tools/pages.py examples/slides/results --keys --pages examples/slides/output/results_examples.pages.json`
(`--pages` is needed because these decks are built with `--out`, not as a `_wip` working copy).

| File | Purpose |
|---|---|
| [results/deck.config.js](results/deck.config.js), [narrative/deck.config.js](narrative/deck.config.js) | Deck metadata, section order, theme and figure directory |
| `results/slides/`, `narrative/slides/` | One page file per slide (keys in the tables below) |
| [results/slides/_lib/results.js](results/slides/_lib/results.js) | Source lines, abbreviation lists, the progressive-emphasis layout shared by two pages |
| [narrative/slides/_lib/narrative.js](narrative/slides/_lib/narrative.js) | Section names shared by the agenda and the section divider |
| `results/notes/`, `narrative/notes/` | Speaker notes, one `<key>.md` per page |
| [results/results_stats.py](results/results_stats.py) | Numbers in the results deck that are not in run_meta (baseline table, model C-index, multivariable Cox) |
| [render.sh](render.sh) | Build both decks with the engine (pptx, PDF) and render previews |

## Results slide types

| Slide | Key | Slide type | When to use | Preview |
|---|---|---|---|---|
| 1 | `sKmSurvival` | Assertion–evidence | One finding per slide: topic title, one full-width figure, one conclusion sentence at the bottom | [results-01](preview/results-01.png) |
| 2 | `sRocTwoPanels` | Two panels, one conclusion | Two angles on the same question (here, two ROCs) | [results-02](preview/results-02.png) |
| 3 | `sForestPlot` | Forest plot | Comparing effect sizes of several variables together | [results-03](preview/results-03.png) |
| 4 | `sCohortTable` | Native three-line table | Tables that must be editable in PowerPoint, such as cohort baseline characteristics | [results-04](preview/results-04.png) |
| 5 | `sKeyNumbers` | Key numbers | 2–3 large numbers to fix the scale at the opening or in a summary | [results-05](preview/results-05.png) |
| 6 | `sAucTakeaways` | Figure + key points | Half-width figure plus 3 key points, for when the figure itself needs explaining | [results-06](preview/results-06.png) |
| 7 | `sKmCallout` | Callout | Teaches the audience how to read a figure: a highlight box with a thin line to the explanation | [results-07](preview/results-07.png) |
| 8–9 | `sForestEmphasis1`, `sForestEmphasis2` | Progressive emphasis | The same figure on two consecutive slides; the second highlights the row to look at, with no animation | [results-08](preview/results-08.png), [results-09](preview/results-09.png) |
| 10 | `sFeatureDefinitions` | Feature definition table | First explains what each feature is, what high and low values mean, and what HR > 1 means | [results-10](preview/results-10.png) |
| 11 | `sModelComparison` | Model comparison | C-index table; states whether it is apparent or CV | [results-11](preview/results-11.png) |
| 12 | `sDraftAdjustedHr` | DRAFT slide | A slide whose numbers are not confirmed yet: a label in the top-right corner, and the notes say what is still to be confirmed | [results-12](preview/results-12.png) |
| 13 | `sSuppMultivariable` | Supplementary slide (hidden) | Skipped during the show; brought up for Q&A | [results-13](preview/results-13.png) |

Sections: `results` (slides 1–12), `supplementary` (13).

## Narrative slide types

| Slide | Key | Slide type | When to use | Preview |
|---|---|---|---|---|
| 1 | `sTitle` | Title slide | Title, subtitle, speaker and affiliation (placeholders) | [narrative-01](preview/narrative-01.png) |
| 2 | `sAgenda` | Agenda | Lists the sections at the start; the current section is in the accent color | [narrative-02](preview/narrative-02.png) |
| 3 | `sSectionDivider` | Section title slide | Section breaks in a long deck | [narrative-03](preview/narrative-03.png) |
| 4 | `sBigStatement` | Big statement | Background slide: one claim, plus 2–3 supporting points and references | [narrative-04](preview/narrative-04.png) |
| 5 | `sProblemApproachImpact` | Problem → approach → impact | Three columns that explain why, how and what it is good for | [narrative-05](preview/narrative-05.png) |
| 6 | `sDataModalities` | Data modality grid | Introduces several kinds of data side by side, each with an icon, a one-line description and n | [narrative-06](preview/narrative-06.png) |
| 7 | `sMethodsFlow` | Method workflow | Numbered step cards with arrows, definitions below, and one conclusion sentence at the end | [narrative-07](preview/narrative-07.png) |
| 8 | `sFramework` | Framework diagram | Input → processing band → output; thin gray arrows inside the band, thick accent-color arrows outside it | [narrative-08](preview/narrative-08.png) |
| 9 | `sAgentLoop` | Agent loop | Closed loop of plan → call tool → observe → produce, with the callable tools listed alongside | [narrative-09](preview/narrative-09.png) |
| 10 | `sTimeline` | Timeline | Study design or lines of therapy, with labels alternating above and below | [narrative-10](preview/narrative-10.png) |
| 11 | `sComparison` | Two-column comparison | Existing methods vs this work, with ✓ / ✗ / – marks drawn as shapes | [narrative-11](preview/narrative-11.png) |
| 12 | `sLimitations` | Limitations | 3–4 items, each stating which conclusion it affects | [narrative-12](preview/narrative-12.png) |
| 13 | `sSummary` | Key takeaways | 3 numbered points | [narrative-13](preview/narrative-13.png) |
| 14 | `sNextSteps` | Next steps | 3 cards, each with a time frame | [narrative-14](preview/narrative-14.png) |
| 15 | `sThankYou` | Acknowledgments / questions | Closing slide, with contact details as placeholders | [narrative-15](preview/narrative-15.png) |
| 16 | `sSuppModelSettings` | Supplementary slide (hidden) | Details such as model settings | [narrative-16](preview/narrative-16.png) |
| 17 | `sCredits` | Credits | Icon libraries, licenses and data sources used | [narrative-17](preview/narrative-17.png) |

Sections: `opening` (1–3), `background` (4–5), `methods` (6–10), `discussion` (11–12), `closing` (13–15), `supplementary` (16), `credits` (17).

## Notes

- Narrative slide 6 uses CC BY icons; the attribution is in that slide's source line and on slide 17. Do this whenever you use CC BY icons.
- The footer page number is the slide's position in the whole deck (engine rule), so preview file numbers match footer numbers in both decks. The title and closing slides of the narrative deck show no page number.
- All layout elements are in [skills/results-deck/engine/js/primitives.js](../../skills/results-deck/engine/js/primitives.js) (`abbr`, `arrow` / `thinArrow` / `thickArrow`, `cite`, `mark`, etc.); the engine passes them to every page as `P`.
  Page files take colors from `P.C` and geometry from `P.G`, never hex colors or font names (`build.js` warns about those).
- The highlight-box positions on the callout and progressive-emphasis slides were measured by hand on the current PNGs. After redrawing the example figures, measure again if the layout changed.

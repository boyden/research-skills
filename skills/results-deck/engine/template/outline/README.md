**English** | [简体中文](README.zh-CN.md)

# Deck outline: <title>

> The two generated blocks below (slides per section, page table) are rewritten by `python3 <engine>/tools/pages.py <deck dir> --table --write` from the `pages.json` of the latest build; inside them, edit only the Subsection and Note columns.

## Conventions

- **Message** is the exact English sentence on screen, copied as is by the page file. Figures, numbers and sources are written in each chapter's per-slide blocks.
- Status: ✅ figure and numbers ready · ⚠️ needs confirmation or more analysis (still built, with `P.draft(s)` showing `DRAFT – to be confirmed` at the top right) · ✏️ text or native-table slide (methods, definitions, summary).
- Slide references: never write page numbers or slide titles by hand; write the slide's key (the page file name `slides/<key>.js`). Read a file with the references expanded by `pages.py <deck dir> --show <file>`.

  | Syntax | Expands to | Use |
  |---|---|---|
  | `{{sKm}}` | `P2「Hormone Therapy — Recurrence-free Survival」` | One slide: page number and title |
  | `{{sKm}}–{{sForest}}` | `P2「…」–P3「…」` | Range: each end expands on its own |
  | `{{sKm.title}}` | `Hormone Therapy — Recurrence-free Survival` | Title only |
  | `{{sKm.page}}` | `P2` | Page number only |

  Anything inside backticks is literal: not expanded and not checked (as in the table above). `pages.py <deck dir> --check` stops hand-written page numbers, unknown keys and out-of-date generated blocks.
- Facts checked by hand are written as "Confirmed (date, how checked)", without person names.

## Contents

- [01_results.md](01_results.md): all five slides, {{sTitle}}–{{sSuppTable}} (title, results, summary, Supplementary); split into one `NN_<chapter>.md` per chapter as the deck grows.
- `CHANGELOG.md`: history of moved, renamed, merged and deleted slides; create it at the first change of the slide order. Chapter files describe only the current state.
- `archive/`: frozen old outlines, with their old page numbers; the tools do not read it.

## Page table (wip)

<!-- pages:counts:start -->

5 slides (section key and slide count): `title` 1 · `results` 2 · `summary` 1 · `supplementary` 1

<!-- pages:counts:end -->

Page, section, slide title and key are rewritten from `pages.json` every time. Subsection is this outline's content number and Note a one-line summary with a pointer (figure, function); both are hand-written and kept per key.
A new slide gets Subsection "—" and Note "(Note to be added)" to fill in by hand; when a key is deleted, `--table --write` backs up this file first and then drops that row.
Slides of the `supplementary` section are hidden in the pptx and exported to the PDF as usual.

<!-- pages:table:start -->

| Page | Section | Subsection | Slide title | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | Title slide: talk title, presenter and role, date; no numbers. |
| P2 | results | 1.1 | Hormone Therapy — Recurrence-free Survival | `sKm` | KM of tamoxifen vs no tamoxifen, HR 0.69 [0.54–0.89] (n = 686, 299 events); figure `results_km`. |
| P3 | results | 1.2 | Clinical Factors — Univariate Cox | `sForest` | Univariate Cox forest of eight clinical factors, positive nodes strongest; figure `results_forest`. |
| P4 | summary | 2.1 | Summary | `sSummary` | Three takeaways, numbers copied from {{sKm}}, {{sForest}} and {{sSuppTable}}. |
| P5 | supplementary | S.1 | Supplementary — Cohort Characteristics | `sSuppTable` | Native three-line table of cohort characteristics by hormone therapy. |

<!-- pages:table:end -->

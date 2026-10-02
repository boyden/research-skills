**English** | [简体中文](outline-format.zh-CN.md)

# Outline format

The outline is the single source of the deck's content: everything except the slide order (titles, exact on-screen sentences, figures, numbers and sources, status, speaker-notes points) is written here first,
and each page file `slides/<key>.js` copies it; the engine does not read the outline. The slide order is set by each page file's `section` and `order` (sections in the order of `sections` in `deck.config.js`); the outline never contains hand-written page numbers.

## 1. Directory structure

```
outline/
  README.md          index
  00_title_background.md
  01_<chapter>.md    one file per chapter; within a chapter, ordered by content number (1.1, 1.2 …)
  …
  CHANGELOG.md       history of moved, renamed, merged and deleted slides
  archive/           frozen old versions (the whole outline before it was split, speaker notes before a rewrite); tools don't touch it
```

- **One file per chapter**: to change one slide, read only the index and that chapter, not the whole outline; several people / agents editing different chapters in parallel don't conflict.
- Content numbers (`4.1`, `4.0a`) are only numbering inside the outline, not the slide order; page numbers change with each build and are looked up in `pages.json`.
- History goes into `CHANGELOG.md`; chapter files describe only the current state. Old versions are frozen into `archive/`, keep their old page numbers, and are not edited again.
- A new deck copied from `engine/template/` already has an `outline/` with this layout (README with both generated blocks, one chapter file).

### README.md (index) contains

1. A paragraph of conventions: `Message` is the exact English sentence on screen, all other notes are in the project's documentation language; what the status icons mean; how to write slide references (see §3).
2. Contents: one line per chapter file, saying which slides it covers (using `{{keyA}}–{{keyB}}`).
3. **The generated slide-count block and page-number table**, placed between marker comments and rewritten by `pages.py <deck> --table --write` (integrator), never edited by hand:

```markdown
<!-- pages:counts:start -->

24 slides (section key and slide count): `title` 1 · `background` 3 · `results` 14 · `summary` 2 · `supplementary` 4

<!-- pages:counts:end -->

<!-- pages:table:start -->

| Page | Section | Subsection | Slide title | key | Note |
|---|---|---|---|---|---|
| P5 | results | 2.1 | Hormone Therapy — Recurrence-free Survival | `sKmTamoxifen` | KM of tamoxifen vs no tamoxifen; figure km_example |

<!-- pages:table:end -->
```

- Page, section, slide title, key and slide counts are rewritten from `pages.json` every time; the "Subsection" and "Note" columns are hand-written and kept per key.
- For a new slide, Subsection is written as "—" and Note as "(Note to be added)", as a reminder to fill them in by hand; when a key is deleted, its row and Note are dropped (`--write` backs up the file to `.backups/` first).
- The language of the counts line, the table header and the Note placeholder follows `lang` in `deck.config.js`: `"en"` (the default) writes the strings above; `"zh"` writes `共 N 页（节 key 和页数）：…`, `| 页 | 节 | 小节 | 页标题 | key | Note |` and `（待补 Note）`.
  With `lang: "zh"`, pages.py reads the `.zh-CN.md` outline files where they exist; tables in either language are read by position, so switching `lang` and running `--table --write` rewrites them.

## 2. Per-slide block

One block per slide, from this template (replace the `<>` parts):

```markdown
### <content number> <topic title> <status> · {{<key>}}
- **Message**: <the exact English sentence on screen, word for word>
- **Figure**: `figures/<figure name>.png` (`fig_<name>` in `plotting/<module>.py`, registered name `<figure name>`): <what the figure shows, how the panels are arranged>
- **Numbers**: <every on-screen number, with n, number of events, interval; source table + column / run_meta key>
- **Source**: <the Source line, verbatim>
- **What could be over-read (speaker notes only, not on screen)**: <one or two sentences>
- **Speaker notes**: <speaker-notes points, or "see notes/<key>.md">
- To confirm: <for ⚠️ slides, state what needs confirming, whom to ask, and which number it is stuck on>
```

- The **title** states the topic, not the conclusion (see [writing-style.md](../../../shared/writing-style.md)).
- **Message** is the sentence on screen, copied as is into the page file; if too long, split it into a few numbered bullets, each also an exact on-screen sentence. Wording the user has changed is written as the user wrote it; qualifiers go into the speaker notes.
- **Figure** names the plotting function and the registered name, so you know where to fix a broken figure (`plot.py <deck> --only <figure name>` redraws it); figures not drawn at on-screen size (external figures linked as is) are marked as such.
- Each of the **Numbers** points to a table row and column or a run_meta key (see [numbers-and-sources.md](../../../shared/numbers-and-sources.md));
  every on-screen number must appear here, but not everything here has to go on screen.
- **What could be over-read** is a separate item, and goes only into the speaker notes or a limitations slide, never piled into Message.
- Facts that were checked by hand are written as "confirmed (date, how checked)", without person names.

### Status icons

| Icon | Meaning | At build time |
|---|---|---|
| ✅ | Figure and numbers are ready | Slide is built normally |
| ⚠️ | Needs confirmation or more analysis first | Slide is still built, with `DRAFT – to be confirmed` at the top right (`P.draft(s)`); the "To confirm" item is copied into the speaker notes |
| ✏️ | Text slide or native-table slide (methods, definitions, summary) | Numbers are copied from the source named in the block; the speaker notes say where they come from |

Once confirmed, change ⚠️ to ✅, note "confirmed (date, how checked)" in the block, and remove the DRAFT label.

## 3. Slide references: `{{key}}`

Living documents contain **no hand-written page numbers and no hand-written slide titles**. Page numbers change when slides are added, deleted or moved, titles get renamed, and hand-written references silently go stale.

- key = the slide's page file name without `.js` (`slides/<key>.js`, written as the `builder` field in `pages.json`), e.g. `sKmTamoxifen`. One page file makes exactly one slide, so keys are unique.
- Slide titles may repeat (e.g. progressive emphasis: one title on two slides); build.js and pages.py only print a WARNING and every token still resolves by key.
  Speaker-notes sync matches slides by title, so a repeated title needs aliases (`"<title>"`, `"<title>#2"`) in `notes/_aliases.json`.

| Syntax | Expands to | Use |
|---|---|---|
| `{{sKmTamoxifen}}` | `P5「Hormone Therapy — Recurrence-free Survival」` | One slide: page number plus title |
| `{{sMethods}}–{{sForest}}` | `P3「…」–P7「…」` | Range: one token at each end, each expanded separately |
| `{{sKmTamoxifen.title}}` | `Hormone Therapy — Recurrence-free Survival` | Naming a slide in running text, without the page number |
| `{{sKmTamoxifen.page}}` | `P5` | Page number only |

- Anything inside backticks (inline code, code blocks) is literal text: not expanded, not checked. Put examples in documentation inside backticks.
- Page numbers and titles are looked up in the `pages.json` of the latest full build (`<outDir>/<name>_wip.pages.json`), so moving slides or changing titles needs no edits to the md. Only renaming a page file (its key) requires replacing the key everywhere, including the name of `notes/<key>.md`.

`engine/tools/pages.py <deck>` has these modes:

| Mode | Read / write | What it does |
|---|---|---|
| `--check` | Read-only, exit code 1 on errors | Unknown or malformed keys; hand-written `P<number>` (Note cells included); key-like names `sXxx` in backticks that are neither a key in `pages.json` nor a page file `slides/<name>.js`; stale generated blocks |
| `--show <file>` | Read-only | Expands every token in the file to page number plus title and prints it |
| `--keys` | Read-only | Lists every slide's page number, key, section and title |
| `--table [--write]` | Dry run by default | Rewrites the page-number table and slide-count block between the marker comments, keeping hand-written columns per key |

Strings like `P21` that are not page numbers (e.g. protein names) are registered in `<deck>/pages_ignore.txt` (`file:regex` lines), or the line gets `<!--pages:ignore-->`.

## 4. Complete example block (public dataset GBSG2)

```markdown
### 2.1 Hormone Therapy — Recurrence-free Survival ✅ · {{sKmTamoxifen}}
- **Message**: Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).
- **Figure**: `figures/km_example.png` (`fig_km` in `examples/plotting/survival.py`, registered name `km_example`, 12.1 × 4.6 in):
  two equal-sized square KM plots, tamoxifen vs no tamoxifen on the left, positive lymph nodes split at the median on the right; each panel shows HR [95% CI],
  Cox p, C-index and log-rank p on its right, with number at risk below. The lower curve (worse prognosis) is red, the upper one blue.
- **Numbers** (run_meta `km_example.json`, `hormone_therapy`): HR 0.695 [0.544–0.888] (yes vs no), Cox p 0.0036,
  C-index 0.543, log-rank p 0.0034; n = 686, 299 recurrence or death events. On screen, HR has two decimals and p three.
  The right panel's numbers are only in the figure; the conclusion sentence doesn't mention them.
- **Source**: GBSG2 trial (lifelines `load_gbsg2`); univariate Cox, recurrence-free survival
- **What could be over-read (speaker notes only, not on screen)**: univariate Cox, not adjusted for tumor size, grade, lymph nodes or hormone receptors,
  so it says *associated with*, not *improves*; a C-index of 0.543 means this variable alone discriminates poorly.
- **Speaker notes**: Both panels use the same endpoint. Note: the HR is yes vs no; the right panel's HR is per SD of log(1 + nodes), drawn as a median split.
```

The slide built from this (`slides/sKmTamoxifen.js`): title `Hormone Therapy — Recurrence-free Survival`, the figure placed 1:1 at y = 1.1 in (`geometry.figureTop` of the theme), the Message sentence at the bottom,
the Source line at the bottom right, and the speaker notes are the Speaker notes paragraph, stored in `notes/sKmTamoxifen.md`.

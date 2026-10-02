---
name: results-deck
description: Build or revise presentation decks from existing analysis results. Use for results reports, lab meetings, defenses, progress updates, slide edits, figure or methods slides, speaker-note synchronization, and explicit deck releases. Do not use for doing the analysis from scratch, manuscript layout, or text-only reports.
---

**English** | [简体中文](SKILL.zh-CN.md)

# results-deck: presentation decks from analysis results

Build a traceable 16:9 presentation deck from existing analysis results. The normal deliverable is a `.pptx`; the engine also attempts to produce a matching PDF and preview PNGs when the required local tools are available.

## When to use

Use this skill when the user wants to:

- turn result tables or existing figures into a presentation deck;
- add, remove, move, or revise slides;
- add a KM, ROC, forest, methods, framework, table, or summary slide;
- synchronize speaker notes edited in PowerPoint; or
- create an explicit released version of a deck.

Do not use it to perform the underlying statistical analysis, lay out a manuscript, or write a text-only report. Prepare or verify result tables first.

## Prerequisites and installation boundary

Before building, check which dependencies are available:

- Node.js and `pptxgenjs` (through `NODE_PATH` or a local `node_modules`);
- LibreOffice (`soffice`) and Poppler (`pdftoppm`, and `pdftotext` for layout checks);
- Python with `matplotlib` and `pandas`; add `lifelines` or `scikit-learn` only when the requested figures need them;
- the fonts used by the selected theme; and
- optionally, a PowerPoint structural validator such as `validate.py`.

If a dependency is missing, report the command the user can run and ask before installing anything. Do not install or upgrade packages, fonts, or other system resources on your own.

## Read the shared rules

Before changing content or figures, read these shared rules. They govern provenance, wording, figure construction, tables, and writing style:

- [numbers-and-sources.md](../../shared/numbers-and-sources.md): number provenance, effect-size formats, intervals, and candidate-versus-significant wording;
- [figures.md](../../shared/figures.md): final-size drawing, KM / ROC / forest conventions, diagrams, icons, figure registration, and `--only`;
- [tables.md](../../shared/tables.md): three-line tables and native `pptxgenjs` table borders; and
- [writing-style.md](../../shared/writing-style.md): titles, conclusion sentences, abbreviations, names, wording supplied by the user, and version naming.

For the executable v2 interface, use [engine/SPEC.md](engine/SPEC.md) as the authority. Use [reference/outline-format.md](reference/outline-format.md), [reference/slide-types.md](reference/slide-types.md), and [reference/checks.md](reference/checks.md) for content planning, layout conventions, and verification.

## Language and documentation policy

- All generated deliverables are English: slide titles and messages, figure labels, tables, source lines, speaker notes, PPTX, PDF, and preview images.
- Repository documentation is bilingual. Maintain an English `X.md` and a Chinese `X.zh-CN.md` for every user-facing skill, engine, reference, and template document; put a language switcher on the first line of both, or immediately after YAML front matter when a document has it.
- Keep code identifiers, filenames, figure text, and on-slide text in English. Chinese belongs in the paired documentation files or in explicitly localized tool output, not in the deliverables.

## Project layout

The engine v2 uses one file per slide. A deck normally has this shape:

```text
presentation/<deck>/
  deck.config.js             metadata, theme, lang, references, and section order
  theme/theme.json           colors, fonts, geometry, and assets
  slides/<key>.js            exactly one page module per slide
  slides/_lib/               deck-local reusable layout helpers, not pages
  notes/<key>.md             one speaker-notes file per slide, optional
  notes/_aliases.json        title aliases used when importing notes from PPTX
  outline/                   content, provenance, status, and generated page tables
  plotting/                  figure modules that read results but do not analyze
  figures/                   PNGs drawn at their on-screen size
    run_meta/<figure>.json   inputs and statistics for each registered figure
  output/                    working and released deck artifacts
```

Start a new deck by copying [engine/template/](engine/template/README.md); `lang` (`"en"` or `"zh"`) sets the language of the blocks that `pages.py` generates in the outline.

The project outline is the content and provenance review source. The slide modules are the executable layout source: the engine does not infer slide content from Markdown. Keep each slide's `Message`, numbers, figures, and source line synchronized between the outline and its page module.

## Page-module contract

Every file in `slides/` whose name does not start with `_` must export:

```js
module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Topic title", n);
    P.figure(s, "figure_name.png");
    P.conclusion(s, "One evidence-backed conclusion sentence.");
    P.source(s, "Source: result table or dataset; method");
    return s;
  },
};
```

Keep these invariants:

- `deck.config.js.sections` contains only section keys, in deck order.
- `section` must be one of those keys; `order` controls the order within a section.
- The slide key is the filename without `.js`; use a stable, unique key matching `^[A-Za-z][A-Za-z0-9_]*$`.
- Each page module creates exactly one slide through `P.newSlide()`.
- Put shared layouts in `slides/_lib/`; do not turn helper files into pages.
- Read colors, fonts, sizes, and geometry from `P.T` and `P.G`, or use primitives that already do so. Do not hard-code theme colors, font names, or page geometry in a page module.
- Use `P.figure()` for result figures so the image is placed at native on-screen size and sent behind the title. Use fitting or scaling only for thumbnails and other explicitly non-result images.

## Workflow

1. **Inspect inputs and scope.** Identify the result tables, source figures, existing deck, requested audience, and changed sections. Do not invent missing numbers or silently reinterpret an analysis.
2. **Update the outline.** Record the topic title, exact on-screen `Message`, figure key, every displayed number and its source, source line, status, and speaker-note cautions. Unconfirmed wording or numbers stay marked as draft.
3. **Prepare figures.** Plot only from result tables or other named inputs. Register each figure, return its display statistics, write `run_meta`, and use `engine/tools/plot.py <deck> --only <figure>`. Draw at the final on-screen size.
4. **Build the changed pages.** Use `node engine/js/build.js <deck> --only <key,...> --out <scratch>/x.pptx --png` or `--sections <section,...> --out <scratch>/x.pptx --png` for a partial build; its footers carry the page numbers of the full deck. A full build (`node engine/js/build.js <deck>`, which replaces the `_wip` artifacts) is for integration and release checks and is run by the integrator.
5. **Render and inspect.** Convert to PDF and PNG, or use the engine's `--png` option. Inspect every changed slide for overflow, overlap, missing footer or DRAFT state, incorrect figure sizing, non-English labels, and mismatched numbers. Use `engine/tools/layout_check.py` as a screening aid; the rendered PNG is the final visual judge.
6. **Synchronize speaker notes.** After the speaker edits a PPTX, run `engine/tools/pull_notes.py` in dry-run mode first, resolve unmatched or repeated-title slides with `notes/_aliases.json`, then run `--write`, which writes `notes/<key>.md` only for matched slides whose notes changed. Recheck relative wording such as “next slide” after moving pages.
7. **Move pages and refresh page references.** Move a page with `engine/tools/move.py <deck> <key> --after <key>` (or `--before <key>`, `--to <section>`); it edits only that page file's `section` and `order`. After adding, deleting, moving, or renaming pages, run a full build, then `engine/tools/pages.py <deck> --table --write` and `--check`. Use `{{key}}`, `{{key.title}}`, and `{{key.page}}` in live outline prose instead of handwritten page numbers.
8. **Release only with confirmation.** Normal work overwrites the `_wip` artifacts. Use `--release` only for an explicit release request or milestone confirmation; never modify an existing `_v<N>` artifact.

When several agents edit one deck in parallel, each one writes only its own page files, notes, and figure module and checks its pages with partial builds. The full build, `--release`, `move.py --respace`, `pages.py --table --write`, `pull_notes.py --write`, and commits are integrator steps, run serially; see [reference/checks.md](reference/checks.md#8-wip-release-and-parallel-slide-editing).

## Per-slide rules

| Element | Rule |
|---|---|
| Title | State the topic, not the conclusion; use a stable title and consistent section prefix. |
| Conclusion | Use one evidence-backed conclusion sentence, normally the outline's exact `Message`; split into bullets when necessary instead of shrinking the font. |
| Source line | Put the result table, dataset, and method in the source line so every displayed number has a traceable origin. |
| Draft state | A slide with unresolved content remains buildable but carries `DRAFT – to be confirmed`; put the unresolved issue in its notes. |
| Figures | Draw at final size; do not crop, stretch, or cover a wrong figure in the deck. Fix the plotting code and redraw it. |
| Tables | Use the shared three-line `table()` helper rather than direct `addTable()` calls. |
| References | Register on-screen citations once and use the shared reference helper. |
| Abbreviations | Keep one consistent abbreviation line per slide when abbreviations appear. |
| Notes | Put layout-displaced details and likely over-interpretations in speaker notes, clearly labeled when useful. |

## Stop and ask

Stop and ask the user when:

- a displayed number cannot be found or does not match the result table, figure metadata, or named source;
- the user's wording conflicts with the source or changes an estimand, time range, comparison, or statistical interpretation;
- a figure is wrong in its values, labels, colors, or intended size;
- a requested edit would change the signature or behavior of a shared engine file such as `primitives.js` or `build.js`; or
- a missing dependency or missing input prevents a reliable build.

Do not choose among conflicting numbers, patch a wrong figure by overlaying objects, or present an unconfirmed result as final.

## Do not

- Do not perform the underlying analysis or edit analysis-result files as part of deck layout.
- Do not install or upgrade packages, fonts, or system tools without user approval.
- Do not overwrite released `_v<N>` artifacts.
- Do not upload the deck to cloud storage or commit changes unless the user explicitly asks.
- Do not use page numbers as stable identifiers; use slide keys and generated `pages.json`.

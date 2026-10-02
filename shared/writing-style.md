**English** | [简体中文](writing-style.zh-CN.md)

# Writing conventions

Applies to text on slides, paper text, and code comments, docs and commit messages.

## Wording

- **Titles state the topic; conclusion sentences state the finding.**
  - Title example: `Hormone Therapy — Recurrence-free Survival`, not a conclusion.
  - Conclusion sentence example: `Tamoxifen is associated with longer recurrence-free survival (HR 0.69 …)`.
- **When the user has decided how to say something, use it as is.** Do not add qualifiers, subgroup details or explanations to on-slide text yourself; definitions, time ranges and details go in the notes or the outline.
  Only when the simple wording contradicts the source (e.g. a 20-year cumulative count written as "within 10 years") do you not adopt it as is, and you tell the user directly where the difference lies.
- **Keep causation and association apart**: for observational data write *associated with*, not *improves* or *causes*.
- **Parallel things get parallel names.** When naming parallel feature families, analyses or modules, do not use words that imply order or rank, such as `extra_*`, `base` or "second batch".
- **Abbreviations**: on each slide (or in each figure legend), write them uniformly as `ABBR: expansion; ABBR: expansion.`.
  - List them in the given order, separated by semicolons, ending with a period, with no "Abbreviations:" prefix.
  - When expanding, expand every letter of the abbreviation.
  - Write plus/minus signs as suffixes: `HR+: hormone receptor-positive`.
  - Anything extra goes in parentheses.

## Person names

- No person names in code comments, docs or commit messages, and do not attribute judgments or decisions to a named person.
  Verified facts are written as "Confirmed (date, how it was checked)" (in Chinese docs: 「已确认（日期，核对方式）」).
- Exceptions:
  - authors in literature citations, in the format of the institution's template, e.g. `Surname, Given, et al. Journal vol.issue (year): pages`;
  - the speaker on the title slide;
  - the author byline of a paper;
  - attribution required by a license (e.g. CC BY icons, authors of images).
- Person names that are already part of a directory or file name are paths; keep them unchanged.

## Versions and files

- An output carries either a version number or a date, not both. Decks use version numbers (`_v1`, `_v2` …).
- The working version (`*_wip`) is overwritten every time; a new version number is released only at a milestone or when the user confirms. All released versions are kept: never deleted, never overwritten.
- When reporting generated files (figures, PDFs, CSVs, logs) to the user, give full absolute paths, one per line, in a code block; source files in the repository get relative links.

## Language

- All generated deliverables are in English: slide and figure text, tables, source lines, speaker notes, PPTX, PDF, and preview images. Papers remain in the language of submission.
- Repository documentation is maintained in two versions: English `X.md` (the GitHub default) and Chinese `X.zh-CN.md`. Both start with a language switcher line, or place it immediately after YAML front matter, and changes to one are made to the other in the same change.
- Code identifiers, filenames, comments, slide text, and figure text stay in English unless a tool is explicitly producing localized documentation output.
  English docs use American spelling (color, gray, license, center); code identifiers, file names and labels already drawn in figures keep their spelling until the code or figure changes.

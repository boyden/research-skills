**English** | [简体中文](README.zh-CN.md)

# research-skills

A collection of Claude Code skills for research outputs: turning analysis results into a presentation deck, with paper writing and more to come.

## Structure

```
shared/                      Rules shared across skills; each skill references them instead of copying
  numbers-and-sources.md     Number provenance, how to write effect sizes, wording for multiple testing
  figures.md                 Drawing at final size, fonts, colors, KM / ROC / forest plots, diagrams, open-license icons
  tables.md                  Three-line tables (implementations in matplotlib / pptxgenjs / LaTeX / Word)
  writing-style.md           Titles and conclusion sentences, using the user's wording as given, person names, abbreviations, version naming
skills/
  results-deck/              Build a pptx deck from analysis results
    SKILL.md                 Entry point: workflow, per-slide rules, when to stop and ask
    reference/               Outline format, slide-type catalog, checklist
    engine/                  Reusable v2 builder, themes, plotting and verification tools
      SPEC.md                Engine interface contract
      template/              Copyable deck skeleton
examples/                    Example figures drawn from public data (GBSG2), open-license icons (CC0 / ISC / MIT / CC BY, each registered in examples/icons/manifest.csv), and the script that generates the example figures
```

Planned:
- `skills/paper-writing/`: a skill for writing papers;
- `.claude-plugin/`: a plugin manifest, for installing everything in one step on another machine.

## Using it in Claude Code

The plugin manifest is not written yet. For now, symlink the skill into the user-level skill directory so every project can use it:

```bash
ln -s /path/to/research-skills/skills/results-deck ~/.claude/skills/results-deck
```

SKILL.md references the shared rules by the relative path `../../shared/`. A symlink resolves only to the real directory, so link the whole skill directory;
do not copy SKILL.md out on its own.

## Conventions

- Docs come in two versions: English `X.md` (the GitHub default) and Chinese `X.zh-CN.md`. When you change one, update the other in the same change.
- All generated deliverables are English: slide and figure text, tables, source lines, speaker notes, PPTX, PDF, and preview images.
- Figures, on-slide text, speaker notes, code identifiers, filenames, and code comments are in English.
- User-facing engine, template, reference, and skill documents follow the same `X.md` / `X.zh-CN.md` pairing rule.
- Only generic material goes here. Institutional template pptx files, logos, license-restricted fonts and project-specific statistical definitions stay in their own projects.
- Use only openly licensed external icons and images, and register their source and license in `examples/README.md` or in the project that uses them.

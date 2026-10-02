**English** | [简体中文](checks.zh-CN.md)

# Verification steps and known pitfalls

After every slide change do at least §1–§3 (the self-check: a partial build of your own pages, the PNGs, the collision check); after moving, adding or deleting slides or changing titles, also do "Slide references" in §7; after the speaker has edited the speaker notes, do "Speaker notes are data" in §7.
By default, verify only the pages you changed; building the full deck and checking every slide is done by the integrator (§8).
`<engine>` below is `skills/results-deck/engine`, `<deck>` the deck directory and `$SCRATCH` your own scratch directory.

## 1. Syntax and structure

```bash
node --check <deck>/slides/<key>.js                         # syntax of each changed page file
node <engine>/js/build.js <deck> --only <key>[,<key>] --out "$SCRATCH/x.pptx" --png
python <pptx skill directory>/scripts/office/validate.py "$SCRATCH/x.pptx"   # must report All validations PASSED
python3 <engine>/tools/layout_check.py <deck> --pptx "$SCRATCH/x.pptx" --pdf "$SCRATCH/x.pdf" \
        --pages-json "$SCRATCH/x.pages.json" --png-dir "$SCRATCH/flagged"
```

- The build first checks every page file (key, `section`, `order`, `build`; two pages of one section with the same `order`) and lists all problems at once (exit code 2). `--sections <section>[,<section>]` builds whole sections instead of `--only`.
- A partial build (`--only` / `--sections`) needs `--out`, never writes the wip or a release and takes no lock; its footers carry the page numbers of the full deck. `--png` adds `x.pdf` and `x_png/<page>-<key>.png`; `x.pages.json` is always written next to `x.pptx`.
- Structural checks use `validate.py` from the Anthropic pptx skill (only available if it is installed; if not, skip it and say in the report that it was not done).
  LibreOffice being able to open a file does not mean PowerPoint can, so passing the render does not replace this step.
- The build writes to a temporary file first and renames it only on success; if it fails midway (e.g. a missing figure), the previous output is left as it was.

## 2. Rendering

`--png` converts the pptx to PDF with its own LibreOffice profile and renders every page with `pdftoppm -r 60` to `<out stem>_png/<page>-<key>.png`. To render a pptx by hand (e.g. one the speaker edited), use:

```bash
soffice -env:UserInstallation=file://$SCRATCH/lo_profile_$$ --headless \
        --convert-to pdf --outdir "$SCRATCH" "$SCRATCH/x.pptx"
pdftoppm -r 60 -png "$SCRATCH/x.pdf" "$SCRATCH/preview/page"
```

- **Use a separate LibreOffice profile for every conversion** (`-env:UserInstallation=file://<unique directory>`): when several conversions run at once and share the default profile, they lock each other,
  and the conversion silently fails or hangs. build.js already does this; `$DECK_SOFFICE` overrides where it looks for `soffice`.
- Write previews to your own temporary directory, not `output/`. 60 dpi (the same as `--png` and examples/slides/render.sh) is enough to check layout; for small text or thin lines, render single slides at 100–150 dpi.
- If conversion fails, only warn; don't fail the build: the pptx is kept as usual and the old PDF is left untouched.

## 3. Look at each PNG

Look only at the changed slides, and go through each one:

- [ ] Text overflowing or cut off (conclusion box over 3 lines, last table row outside the frame, bullets falling off the slide)
- [ ] Overlapping elements (wrapped title running into the figure, conclusion box running into the source line, icons off their own row)
- [ ] Figure stretched, squashed or scaled (compare the figure's pixel size / dpi with its placed size)
- [ ] Missing footer (source line, page number); ⚠️ slides have the DRAFT label, ✅ slides don't
- [ ] Any non-English text (in figures, on the slide, in tables)
- [ ] Numbers match the outline's Message and the source table

When you find a problem, fix it, rebuild and look again; problems in the figure itself are fixed in the plotting code and redrawn with `plot.py <deck> --only <figure>` (see SKILL.md "[Stop and ask](../SKILL.md#stop-and-ask)").

## 4. Fonts and z-order: where the preview differs from PowerPoint

- **Install the template fonts on the system**; otherwise LibreOffice uses a wider substitute font, long titles wrap to two lines, conclusion sentences gain a line, and the preview no longer matches PowerPoint.
  No root needed: put the font files in the user font directory `~/.local/share/fonts/<font name>/`, then run `fc-cache -f ~/.local/share/fonts`.
  Check whether the theme's fonts are present (`fc-list | grep <font name>`): `theme_from_pptx.py` warns about template fonts that are not installed, but build.js only warns when Arial (or Liberation Sans) is missing.
- **Don't commit or redistribute commercial font files**: most "may be installed on your own devices" licenses don't allow putting them in a repository. Document where to download them and where to install them.
- If the fonts can't be installed: whatever fits in the preview will fit in PowerPoint (the substitute font is wider), but line breaks are only approximate.
- **Send the main figure to the bottom of the z-order**: a figure added after the title sits above the title in the z-order, so when the title wraps, its second line is hidden by the figure and invisible in the PNG.
  `P.figure()` sends the figure to the back right after adding it (several figures on one slide keep their order relative to each other); icons and small images that are meant to sit on top of shapes are left alone.

## 5. Automatic collision check (`layout_check.py`)

Checking dozens of slides by eye one by one misses things; `<engine>/tools/layout_check.py` screens them first (default input: the wip pptx, PDF and pages.json; `--pptx` / `--pdf` / `--pages-json` for a partial build, `--pages` for some pages only):

- Text boxes: `pdftotext -bbox-layout <pdf>` gives the rendered box (pt) of every line.
- Image boxes and z-order: read each `p:pic`'s position (EMU → pt) and its order within `spTree` from the pptx slide XML;
  match each text line in the PDF back to its pptx text box by content to get its z-order.
- Report per slide: title line hidden under a figure higher in the z-order (hidden title); title and figure intersecting with the text on top; title wrapping to 2 or more lines and its distance to the next element;
  other text lines intersecting a figure by more than 3 pt (`--tol`); two text-line boxes overlapping. `--png-dir` renders the flagged slides as low-resolution PNGs for a visual check.
- **False positives are expected**: white or transparent margins in PNGs, scale bars and labels deliberately placed over figures, and icons in table columns are all reported as intersections;
  PDF line boxes are taller than the glyphs. **The PNG is the final judge**; the script only decides which slides to look at first.

## 6. Supplementary slides hidden, still in the PDF

- Slides of the section named by `supplementary` in `deck.config.js` are set to hidden in the pptx (`show="0"` in the slide XML) and are skipped during the slideshow.
- LibreOffice before 7.4 **skips hidden slides** when converting to PDF and has no option to export them. build.js therefore converts a temporary copy of the pptx with `show="0"` removed.
  The pptx stays hidden, the PDF has one page per slide, and the page count matches `pages.json`.
- Check: PDF page count = number of entries in `pages.json`.

## 7. Slide references and speaker notes

**Slide references** (after moving, adding or deleting slides or changing titles):

1. Change the page files: `move.py <deck> <key> --after <key>` (or `--before <key>`, `--to <section>`) edits only that page's `section` / `order`; a title is changed in its page file; a page is added or deleted as `slides/<key>.js` (with `notes/<key>.md`).
2. The integrator runs a full build (pptx + PDF + `pages.json`), then `pages.py <deck> --table --write` to rewrite the generated blocks in the outline (slide counts, page table).
3. `pages.py <deck> --check`: unknown keys, hand-written `P<number>`, and stale generated blocks must all be zero.
4. Record the move, rename, merge or deletion in `outline/CHANGELOG.md`; the chapter files describe only the current state.

**Speaker notes are data**:

- Speaker notes are stored one file per slide in `notes/<key>.md` (plain UTF-8 text, one paragraph per line); at build time the file replaces that slide's notes as a whole; slides without a file keep the `slide.addNotes()` text of their page file.
- Once the speaker has edited the notes in PowerPoint, **the speaker's pptx is the source of truth**. `pull_notes.py <deck> [pptx]` reads the notes of every slide in the pptx and matches keys by slide title:
  the first slide is the title slide; then the alias table `notes/_aliases.json` is checked (a repeated title is addressed as `"<title>"`, `"<title>#2"` …); then the title is matched uniquely in `pages.json`. Slides that don't match, have repeated titles without an alias, or whose key is already taken are **not written**;
  they are listed in `notes/_unmatched.json`, and you add aliases and rerun. First run `--dry-run` to see which keys are new, changed or unchanged; the integrator then runs `--write`, which backs up the files it changes to `.backups/` and never deletes a file.
- Only plain text is read back: bold and font size are not kept; paragraphs and soft line breaks both become line breaks.
- pptxgenjs writes the whole speaker-notes text as one paragraph; build.js splits it into several `a:p` at line breaks so the paragraphs in PowerPoint match the lines of `notes/<key>.md`.
- **After moving slides, check relative references in the notes**: "the next slide", "the previous slide", "the supplementary slide '…'", "Next, I'll show …" silently become wrong when slides move.
  `move.py` prints such wording found in the moved page and its old and new neighbors (page file and notes) as WARNINGs; read each one yourself against the titles of the current neighboring slides (or the slide named); keyword overlap is only triage, and generic words will make wrong ones look right.
  The tool only reports and never edits the wording: the speaker notes belong to the speaker; any change is made in the pptx, then synced.
- Details moved off the slide into the speaker notes for layout are written as `Note: …`, so the speaker can see at a glance which statements are not on the slide.

## 8. wip, release and parallel slide editing

- **Full builds write wip** (`<outDir>/<name>_wip.pptx`, along with the PDF and `pages.json`), overwritten every time; they hold `<outDir>/.build.lock` (exit code 3 while another full build runs); only the integrator runs them.
- **Release**: `--release` writes `<outDir>/<name>_v<N>.pptx` (+ PDF + `pages.json`), N = current highest version + 1; file names carry only the version number, no date; released files are never overwritten or deleted.
- **Parallel slide editing**: each person / agent owns their own page files `slides/<key>.js`, their `notes/<key>.md`, their outline blocks and their plotting module, and builds only those pages to a temporary path:
  `node <engine>/js/build.js <deck> --only <key>[,<key>] --out $SCRATCH/x.pptx --png`. Such a build refuses to write wip, takes no lock, numbers the footers with the full-deck page numbers, and produces no PDF unless `--png` or `--pdf` is given.
- **Integrator-only steps**, run serially: the full build, `--release`, `move.py --respace <section>` (renumbers a whole section, so it edits several page files), `pages.py --table --write`, `pull_notes.py --write`, `plot.py <deck>` without `--only` (after a theme change), and commits. A commit lists its paths explicitly; **never `git add -A`**, which would also commit files another agent has half edited.
- Shared files (`primitives.js`, `build.js`, `theme/`, `deck.config.js`, `slides/_lib/`, `plotting/style.py`, `plotting/common.py`, the outline index) get append-only changes, merged by the integrator; existing functions' signatures and behavior are not changed.
- Each figure has its own run_meta and plotting always uses `--only`, so parallel plotting runs never overwrite each other. The PDF is only as new as the latest full build.

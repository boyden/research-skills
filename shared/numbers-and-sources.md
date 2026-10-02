**English** | [简体中文](numbers-and-sources.zh-CN.md)

# Numbers and sources

Applies to every output that presents analysis results to other people: decks, papers, reports, responses to reviewers.

## Rules

1. **Every number can be traced to a source.** The source is a result table (file + row / column) or the literature. In a deck it goes in the Source line on the slide;
   in a paper, in the figure legend or the methods; finer details of definitions go in the outline or the speaker notes.
2. **If you cannot find it, or it does not match, stop and ask**; do not pick one that looks right yourself. Old decks and old drafts only supply structure:
   copy none of their numbers; take every number again from the current results.
3. **Read numbers from tables; do not copy them by hand.** Plotting scripts read result tables and write the statistics used in each figure into one run_meta per figure
   (`run_meta/<figure name>.json`: input (file path or dataset name), statistics, script, time). Numbers in the text are copied from run_meta or the result table.
   If a quantity recomputed at plotting time (e.g. log-rank p) disagrees with the table, exit with an error, so that the plot is guaranteed to show the grouping in the table.
4. **Effect sizes come with context.** Give the interval, n and number of events, and state the unit (per SD / per unit / yes vs no).
   Fix each convention once per output (e.g. "HR always per SD") and do not mix conventions afterward.
5. **Wording under multiple testing.**
   - Nominal p < 0.05 but not passing FDR: call it *candidate* or *nominal*, not *significant*.
   - When nothing passes FDR, make no statement of anything "passing FDR".
   - Something selected and evaluated on the same samples is not called *validation*; small samples or post-hoc selection are labeled *exploratory*.
6. **Consistent formats.**
   - p values to three decimals; below 0.001 write `<0.001`.
   - HR to two or three decimals, the same throughout one output.
   - Intervals with an en dash (`0.54–0.89`), thousands separated by commas (`3,334,358`).
7. **Manually verified facts** are written as "Confirmed (date, how it was checked)" (in Chinese docs: 「已确认（日期，核对方式）」), without saying who confirmed them.
8. **Places that could be over-interpreted** get a sentence of their own, in the notes or the limitations section, not piled onto the sentence on the slide.

## Example (public data GBSG2, see [examples/](../examples/))

Conclusion sentence on the slide:

> Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).

Source line:

> Source: GBSG2 trial (lifelines `load_gbsg2`); univariate Cox, recurrence-free survival

The matching run_meta snippet (the `stats` field of `examples/figures/run_meta/km_example.json`; the file holds unrounded values, shortened here for layout):

```json
{"hormone_therapy": {"hr": 0.695, "lo": 0.544, "hi": 0.888, "p": 0.0036, "c": 0.543,
                     "n": 686, "events": 299, "logrank_p": 0.0034}}
```

Counterexamples:

- "Tamoxifen significantly improves survival": no interval, n or source, and *improves* also implies causation.
- Giving only the Cox p while the plot shows a median split: when both p values are near 0.05 they will not agree, so give both (see [figures.md](figures.md) "Survival plots").

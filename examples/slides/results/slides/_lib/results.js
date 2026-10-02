/*
 * Shared by the results example pages (engine/SPEC.md §3: slides/_lib/ is not collected as pages): source
 * lines, abbreviation lists and the progressive-emphasis layout used by two pages.
 *
 * Numbers (GBSG2, n = 686, 299 recurrence-or-death events) come from the km_example / forest_example /
 * roc_example / auc_bars_example run_meta (examples/figures/run_meta/) or from ../results_stats.json
 * (cohort table, nested-model C-index, multivariable Cox; written by ../results_stats.py) and are copied
 * into the page files by hand: a number on a slide must match one of those files.
 */
"use strict";

const SRC_COX = "Source: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival";
const SRC_KM = "Source: GBSG2 trial (lifelines load_gbsg2); Kaplan–Meier, univariate Cox and log-rank, recurrence-free survival";

const ABBR_KM = [["HR", "hazard ratio"], ["SD", "standard deviation"], ["C-index", "concordance index"]];
const ABBR_COX = [["HR", "hazard ratio"], ["CI", "confidence interval"], ["SD", "standard deviation"],
  ["PR", "progesterone receptor"], ["ER", "estrogen receptor"], ["q", "Benjamini–Hochberg adjusted p"]];

// Rows 2–6 and 8 of the forest figure have q < 0.05 (row pitch 0.405 in, row 1 center at y 0.74 in).
const FOREST_ROW = (i) => 0.74 + (i - 1) * 0.405;

/*
 * Progressive emphasis (a build without animation): the forest figure at the same position on two
 * consecutive pages; step 2 adds a highlight over the q < 0.05 rows and a new conclusion.
 */
function forestEmphasis(pres, n, P, step) {
  const s = P.newSlide(pres, "Clinical Factors — Univariate Cox", n);
  P.pattern(s, `Pattern: progressive emphasis ${step}/2`);
  const f = P.figure(s, "forest_example.png");
  if (step === 1) {
    P.conclusion(s, "Hazard ratios range from 0.66 per SD (PR receptor) to 1.65 per SD (positive nodes) " +
      "across eight clinical factors (n = 686, 299 events).");
  } else {
    const x0 = f.x + 0.85, x1 = f.x + 11.97, half = 0.2;
    P.emphasis(s, x0, f.y + FOREST_ROW(2) - half, x1 - x0, FOREST_ROW(6) - FOREST_ROW(2) + 2 * half);
    P.emphasis(s, x0, f.y + FOREST_ROW(8) - half, x1 - x0, 2 * half);
    P.conclusion(s, "Six of eight factors have q < 0.05 (all q ≤ 0.005): larger tumors, more nodes and grade III " +
      "with shorter, higher receptor levels and tamoxifen with longer recurrence-free survival.");
  }
  P.abbr(s, ABBR_COX);
  P.source(s, SRC_COX);
  return s;
}

module.exports = { SRC_COX, SRC_KM, ABBR_KM, ABBR_COX, FOREST_ROW, forestEmphasis };

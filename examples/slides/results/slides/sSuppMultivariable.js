"use strict";
// Supplementary slide, hidden in the pptx (section supplementary): univariate vs multivariable Cox
// (forest_example run_meta and ../results_stats.json, multi). Notes in notes/sSuppMultivariable.md.
const { ABBR_COX } = require("./_lib/results");

module.exports = {
  section: "supplementary",
  order: 10,
  build(pres, n, P) {
    const { G } = P;
    const s = P.newSlide(pres, "Supplementary — Univariate vs Multivariable", n);
    P.pattern(s, "Pattern: supplementary (hidden)");
    const rows = [
      ["Variable", "Univariate HR [95% CI]", "p", "q", "Multivariable HR [95% CI]", "p"],
      ["Age (per SD)", "0.96 [0.85–1.07]", "0.446", "0.510", "0.92 [0.77–1.10]", "0.341"],
      ["Tumor size (per SD)", "1.24 [1.12–1.36]", "<0.001", "<0.001", "1.05 [0.94–1.18]", "0.348"],
      ["Positive nodes, log (per SD)", "1.65 [1.48–1.84]", "<0.001", "<0.001", "1.58 [1.41–1.78]", "<0.001"],
      ["PR receptor, log (per SD)", "0.66 [0.59–0.74]", "<0.001", "<0.001", "0.67 [0.58–0.78]", "<0.001"],
      ["ER receptor, log (per SD)", "0.78 [0.69–0.87]", "<0.001", "<0.001", "1.06 [0.91–1.24]", "0.456"],
      ["Grade III vs I–II", "1.48 [1.14–1.91]", "0.003", "0.005", "1.09 [0.83–1.44]", "0.524"],
      ["Postmenopausal", "1.06 [0.84–1.34]", "0.596", "0.596", "1.22 [0.86–1.75]", "0.266"],
      ["Tamoxifen", "0.69 [0.54–0.89]", "0.004", "0.005", "0.68 [0.53–0.88]", "0.003"],
    ];
    const colW = [3.4, 2.4, 1.1, 1.1, 2.7, 1.1];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.2, colW, 0.44, rows, { fontSize: 13 });
    P.conclusion(s, "Nodes, PR receptor and tamoxifen stay associated in the multivariable model (HR 1.58, 0.67, 0.68; " +
      "all p ≤ 0.003); tumor size, grade III and ER do not (n = 686, 299 events).");
    P.abbr(s, ABBR_COX);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); univariate (forest_example) and 8-variable Cox");
    return s;
  },
};

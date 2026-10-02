"use strict";
// Draft slide: DRAFT tag on a page whose numbers are not final (../results_stats.json, multi).
// Notes in notes/sDraftAdjustedHr.md.

module.exports = {
  section: "results",
  order: 120,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Tamoxifen — Adjusted Hazard Ratio", n);
    P.draft(s);
    P.pattern(s, "Pattern: draft", 1.02);   // under the DRAFT tag
    const rows = [
      ["Cox model for tamoxifen", "HR [95% CI]", "p", "n (events)"],
      ["Univariate", "0.69 [0.54–0.89]", "0.004", "686 (299)"],
      ["Adjusted for 7 clinical variables", "0.68 [0.53–0.88]", "0.003", "686 (299)"],
    ];
    const colW = [4.6, 2.8, 1.6, 2.2];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.9, colW, 0.6, rows, { fontSize: 16 });
    P.text(s, (G.slideW - w) / 2, 3.95, w, 0.9, [
      "Adjusted for positive nodes, tumor size, grade III, age, postmenopausal status, PR and ER (continuous per SD).",
    ], { fontSize: 14, color: C.text });
    P.conclusion(s, "After adjustment for seven clinical variables the tamoxifen HR barely changes " +
      "(0.68 [0.53–0.88] vs 0.69 unadjusted, p = 0.003; n = 686, 299 events).");
    P.abbr(s, [["HR", "hazard ratio"], ["CI", "confidence interval"], ["PR", "progesterone receptor"],
      ["ER", "estrogen receptor"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); multivariable Cox, recurrence-free survival");
    return s;
  },
};

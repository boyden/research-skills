"use strict";
// Model comparison: C-index table of nested Cox models (../results_stats.json, models). Notes in notes/sModelComparison.md.

module.exports = {
  section: "results",
  order: 110,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Model Comparison — C-index", n);
    P.pattern(s, "Pattern: model comparison");
    const rows = [
      ["Cox model", "Variables", "Apparent C-index", "5-fold CV C-index"],
      ["Positive nodes", "1", "0.645", "0.646"],
      ["Nodes + size + grade", "3", "0.655", "0.650"],
      ["All clinical", "8", "0.698", "0.688"],
    ];
    const colW = [4.0, 2.0, 2.8, 2.8];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.7, colW, 0.6, rows, { fontSize: 16 });
    P.text(s, (G.slideW - w) / 2, 4.35, w, 0.9, [
      "All clinical = nodes, tumor size, grade III, age, postmenopausal, PR, ER and tamoxifen. Apparent C-index: " +
      "fitted and evaluated on the same 686 patients.",
    ], { fontSize: 14, color: C.text });
    P.conclusion(s, "Adding all eight clinical variables raises the apparent C-index from 0.645 (nodes only) to 0.698 " +
      "on the same patients (n = 686, 299 events); 5-fold CV gives 0.688.");
    P.abbr(s, [["C-index", "concordance index"], ["CV", "cross-validation"], ["PR", "progesterone receptor"],
      ["ER", "estrogen receptor"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); multivariable Cox, Harrell's C; KFold(5, shuffle, random_state 0)");
    return s;
  },
};

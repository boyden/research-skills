"use strict";
// Figure + conclusion: figures/results_forest.png (plotting/results.py, results_forest); notes in notes/sForest.md.

module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Clinical Factors — Univariate Cox", n);
    P.figure(s, "results_forest.png");
    P.conclusion(s, "More positive lymph nodes are most strongly associated with shorter recurrence-free survival " +
      "(HR 1.65 [1.48–1.84] per SD, q < 0.001; n = 686, 299 events).");
    P.abbr(s, [["HR", "hazard ratio"], ["CI", "confidence interval"], ["SD", "standard deviation"],
      ["PR", "progesterone receptor"], ["ER", "estrogen receptor"], ["q", "Benjamini–Hochberg adjusted p"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival");
    return s;
  },
};

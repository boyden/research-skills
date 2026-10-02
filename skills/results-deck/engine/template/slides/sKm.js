"use strict";
// Figure + conclusion: figures/results_km.png (plotting/results.py, results_km); notes in notes/sKm.md.

module.exports = {
  section: "results",
  order: 10,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Hormone Therapy — Recurrence-free Survival", n);
    P.figure(s, "results_km.png");
    P.conclusion(s, "Tamoxifen is associated with longer recurrence-free survival " +
      "(HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).");
    P.abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["C-index", "concordance index"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival");
    return s;
  },
};

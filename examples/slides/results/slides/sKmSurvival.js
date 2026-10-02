"use strict";
// Assertion–evidence: one full-width figure (km_example), one conclusion. Notes in notes/sKmSurvival.md.
const { SRC_KM, ABBR_KM } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 10,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Recurrence-free Survival", n);
    P.pattern(s, "Pattern: assertion–evidence");
    P.figure(s, "km_example.png");
    P.conclusion(s, "Tamoxifen is associated with longer, and more positive nodes with shorter, recurrence-free " +
      "survival (HR 0.69 [0.54–0.89], p = 0.004; HR 1.65 [1.48–1.84] per SD, p < 0.001; n = 686, 299 events).");
    P.abbr(s, ABBR_KM);
    P.source(s, SRC_KM);
    return s;
  },
};

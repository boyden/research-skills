"use strict";
// Forest plot, full width (forest_example). Notes in notes/sForestPlot.md.
const { SRC_COX, ABBR_COX } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 30,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Clinical Factors — Univariate Cox", n);
    P.pattern(s, "Pattern: forest plot");
    P.figure(s, "forest_example.png");
    P.conclusion(s, "More positive lymph nodes are most strongly associated with shorter recurrence-free survival " +
      "(HR 1.65 [1.48–1.84] per SD, q < 0.001; n = 686, 299 events).");
    P.abbr(s, ABBR_COX);
    P.source(s, SRC_COX);
    return s;
  },
};

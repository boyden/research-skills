"use strict";
// Two panels, one shared conclusion: the two-panel ROC figure (roc_example). Notes in notes/sRocTwoPanels.md.

module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Discrimination — ROC", n);
    P.pattern(s, "Pattern: two panels, one conclusion");
    P.figure(s, "roc_example.png");
    P.conclusion(s, "PR level separates ER status well (AUC 0.877 [0.849–0.904]; 497 of 686 ER-positive), whereas " +
      "nodes predict 5-year recurrence only moderately (AUC 0.671 [0.619–0.724]; 285 of 406 recurred).");
    P.abbr(s, [["ROC", "receiver operating characteristic"], ["AUC", "area under the curve"],
      ["PR", "progesterone receptor"], ["ER", "estrogen receptor"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); ROC with 2,000-sample bootstrap 95% CI, random_state 0");
    return s;
  },
};

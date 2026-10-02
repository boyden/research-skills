"use strict";
// Figure + takeaways: half-width figure (auc_bars_example) with three bullets. Notes in notes/sAucTakeaways.md.

module.exports = {
  section: "results",
  order: 60,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Single Predictors of ER Status", n);
    P.pattern(s, "Pattern: figure + takeaways");
    const f = P.figure(s, "auc_bars_example.png", G.figureTop, G.margin);
    const x = f.x + f.w + 0.4;
    P.text(s, x, 1.55, G.slideW - G.margin - x, 0.4, "Takeaways", { fontSize: 18, bold: true, color: C.text });
    P.bullets(s, x, 2.1, G.slideW - G.margin - x, 3.3, [
      "PR level is by far the strongest (AUC 0.877)",
      "Grade and age add little (AUC 0.656, 0.568)",
      "Nodes and tumor size: CIs include 0.5",
    ], 18);
    P.conclusion(s, "Of five clinical variables, only PR level discriminates ER status well " +
      "(AUC 0.877 [0.849–0.904]; 497 of 686 ER-positive).");
    P.abbr(s, [["AUC", "area under the curve"], ["CI", "confidence interval"], ["ER", "estrogen receptor"],
      ["PR", "progesterone receptor"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); AUC with 2,000-sample bootstrap 95% CI, random_state 0");
    return s;
  },
};

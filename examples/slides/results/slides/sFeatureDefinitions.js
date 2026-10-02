"use strict";
// Feature-definition table (ranges and SDs: ../results_stats.json). Notes in notes/sFeatureDefinitions.md.

module.exports = {
  section: "results",
  order: 100,
  build(pres, n, P) {
    const { G } = P;
    const s = P.newSlide(pres, "Feature Definitions", n);
    P.pattern(s, "Pattern: feature-definition table");
    const rows = [
      ["Feature", "Low → high", "What is computed (unit)", "Higher value", "Lower value", "HR > 1 means"],
      ["Age", "21 → 80 years", ["Age at entry (years)", "per SD = 10.1 years"], "Older", "Younger",
        "Older recur sooner"],
      ["Tumor size", "3 → 120 mm", ["Largest diameter (mm)", "per SD = 14.3 mm"], "Larger", "Smaller",
        "Larger recur sooner"],
      ["Positive nodes", "1 → 51 nodes", ["log(1 + nodes)", "per SD = 0.72"], "More nodes", "Fewer nodes",
        "More nodes recur sooner"],
      ["PR receptor", "0 → 2,380 fmol/mg", ["log(1 + PR, fmol/mg)", "per SD = 1.93"], "More PR", "Less PR",
        "More PR recur sooner"],
      ["Grade III", "I–II → III", ["Grade III vs I–II", "yes vs no"], "Grade III", "Grade I–II",
        "Grade III recur sooner"],
    ];
    const colW = [1.6, 2.0, 3.0, 1.5, 1.5, 2.5];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.3, colW, [0.5, 0.72, 0.72, 0.72, 0.72, 0.72], rows, { fontSize: 13, labelCol: true });
    P.conclusion(s, "Continuous features are scaled per SD in this cohort (n = 686), so HR > 1 means a one-SD " +
      "higher value goes with shorter recurrence-free survival.");
    P.abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["PR", "progesterone receptor"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); ranges and SDs over all 686 patients");
    return s;
  },
};

"use strict";
// Native three-line table: cohort characteristics (../results_stats.json, cohort). Notes in notes/sCohortTable.md.

module.exports = {
  section: "results",
  order: 40,
  build(pres, n, P) {
    const { G } = P;
    const s = P.newSlide(pres, "Cohort Characteristics", n);
    P.pattern(s, "Pattern: native three-line table");
    const rows = [
      ["Characteristic", ["All", "n = 686"], ["Tamoxifen", "n = 246"], ["No tamoxifen", "n = 440"]],
      ["Age, years, median (IQR)", "53 (46–61)", "58 (50–63)", "50 (45–59)"],
      ["Postmenopausal, n (%)", "396 (58%)", "187 (76%)", "209 (48%)"],
      ["Tumor size, mm, median (IQR)", "25 (20–35)", "25 (20–35)", "25 (20–35)"],
      ["Grade III, n (%)", "161 (23%)", "50 (20%)", "111 (25%)"],
      ["Positive nodes, median (IQR)", "3 (1–7)", "3 (1–7)", "3 (1–7)"],
      ["Recurrence or death, n (%)", "299 (44%)", "94 (38%)", "205 (47%)"],
    ];
    const colW = [4.3, 2.5, 2.5, 2.5];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.3, colW, [0.8, ...Array(rows.length - 1).fill(0.5)], rows, { fontSize: 16 });
    P.conclusion(s, "Women given tamoxifen were older (median 58 vs 50 years) and more often postmenopausal " +
      "(76% vs 48%); tumor size, grade and nodes were similar (n = 686).");
    P.abbr(s, [["IQR", "interquartile range"]]);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); descriptive statistics by hormone therapy");
    return s;
  },
};

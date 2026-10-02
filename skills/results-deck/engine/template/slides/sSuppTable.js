"use strict";
// Native three-line table, hidden in the pptx (supplementary section). Numbers: figures/run_meta/results_km.json
// (stats.cohort); notes in notes/sSuppTable.md.
const { centeredTable } = require("./_lib/layouts");

module.exports = {
  section: "supplementary",
  order: 10,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Supplementary — Cohort Characteristics", n);
    centeredTable(s, [
      ["Characteristic", ["All", "n = 686"], ["Tamoxifen", "n = 246"], ["No tamoxifen", "n = 440"]],
      ["Age, years, median (IQR)", "53 (46–61)", "58 (50–63)", "50 (45–59)"],
      ["Postmenopausal, n (%)", "396 (58%)", "187 (76%)", "209 (48%)"],
      ["Tumor size, mm, median (IQR)", "25 (20–35)", "25 (20–35)", "25 (20–35)"],
      ["Grade III, n (%)", "161 (23%)", "50 (20%)", "111 (25%)"],
      ["Positive nodes, median (IQR)", "3 (1–7)", "3 (1–7)", "3 (1–7)"],
      ["Recurrence or death, n (%)", "299 (44%)", "94 (38%)", "205 (47%)"],
    ], [43, 25, 25, 25]);                         // relative column widths
    P.conclusion(s, "Women given tamoxifen were older (median 58 vs 50 years) and more often postmenopausal " +
      "(76% vs 48%); tumor size, grade and nodes were similar (n = 686).");
    P.abbr(s, [["IQR", "interquartile range"]], P.G.abbr[2] / 2);  // half width: the citation is on the right
    P.cite(s, [["Source: GBSG2 trial (lifelines load_gbsg2), descriptive statistics; ", "schumacher1994"]]);
    return s;
  },
};

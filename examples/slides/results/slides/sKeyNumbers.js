"use strict";
// Key numbers: three large numerals with label and context. Notes in notes/sKeyNumbers.md.
const { SRC_COX } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 50,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Study at a Glance", n);
    P.pattern(s, "Pattern: key numbers");
    const items = [
      ["686", "patients", "Node-positive breast cancer"],
      ["299", "recurrence-or-death events", "44% of patients"],
      ["0.69", "HR, tamoxifen vs none", "95% CI 0.54–0.89; p = 0.004"],
    ];
    const colW = G.contentW / 3;
    items.forEach(([num, label, sub], i) => {
      const x = G.margin + i * colW;
      const y0 = 1.9;
      P.text(s, x, y0, colW, 1.3, { runs: [num], align: "center" }, { fontSize: 72, bold: true, color: C.accent, valign: "middle" });
      P.text(s, x, y0 + 1.35, colW, 0.45, { runs: [label], align: "center" }, { fontSize: 20, bold: true, color: C.text });
      P.text(s, x + 0.3, y0 + 1.85, colW - 0.6, 0.7, { runs: [sub], align: "center" }, { fontSize: 14, color: C.muted });
    });
    P.conclusion(s, "Tamoxifen is associated with longer recurrence-free survival " +
      "(HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).");
    P.abbr(s, [["HR", "hazard ratio"], ["CI", "confidence interval"]]);
    P.source(s, SRC_COX);
    return s;
  },
};

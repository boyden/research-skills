"use strict";
// Data modalities grid: one card per modality with an illustration and a count. Notes in notes/sDataModalities.md.

module.exports = {
  section: "methods",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Data Modalities", n);
    P.pattern(s, "Pattern: data modalities grid");
    const cards = [
      ["bioicons/glass-slide", "H&E whole-slide images", "Scanned at 40×, one per resection", "n = XX slides"],
      ["bioicons/confocal-microscope", "Multiplex imaging", "40-plex protein panel on a subset", "n = XX regions"],
      ["bioicons/single-cell-umap", "Single-cell phenotypes", "Cell types called from the panel", "n = XX cells"],
      ["bioicons/patient", "Clinical and outcome", "Stage, therapy, recurrence-free survival", "n = XX patients"],
    ];
    const gap = 0.3, w = (G.contentW - 3 * gap) / 4, y0 = 1.35, h = 4.1, isz = 1.5;
    cards.forEach(([ic, head, body, num], i) => {
      const x = G.margin + i * (w + gap);
      P.rect(s, x, y0, w, h, { fill: C.tint });
      P.rect(s, x, y0, w, 0.06, { fill: C.accent });
      P.icon(s, ic, x + (w - isz) / 2, y0 + 0.35, isz);
      P.text(s, x + 0.2, y0 + 2.05, w - 0.4, 0.7, { runs: [head], align: "center" },
        { fontSize: 18, bold: true, color: C.text, valign: "middle" });
      P.text(s, x + 0.2, y0 + 2.8, w - 0.4, 0.65, { runs: [body], align: "center" }, { fontSize: 14, color: C.ink });
      P.text(s, x + 0.2, y0 + 3.5, w - 0.4, 0.4, { runs: [num], align: "center" },
        { fontSize: 16, bold: true, color: C.accent });
    });
    P.conclusion(s, "Four modalities from the same patients, linked by patient ID; multiplex data exist for a " +
      "subset only.", G.conclusion.yText);
    P.source(s, "Icons: Bioicons — glass slide by Servier Medical Art (CC BY 3.0); confocal microscope by DBCLS " +
      "TogoTV (CC BY 4.0)");
    return s;
  },
};

"use strict";
// Two-column comparison: prior approaches vs this work, marks drawn as shapes. Notes in notes/sComparison.md.

module.exports = {
  section: "discussion",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Prior Approaches vs This Work", n);
    P.pattern(s, "Pattern: two-column comparison");
    const rows = [
      ["Labels needed", ["no", "Pixel-level annotation"], ["yes", "Slide-level outcome only"]],
      ["Spatial context", ["no", "Tile features averaged"], ["yes", "Cell graph keeps neighbors"]],
      ["Modalities", ["no", "H&E only"], ["yes", "H&E, multiplex and clinical"]],
      ["Validation", ["yes", "Often external cohorts"], ["part", "Internal 5-fold CV so far"]],
      ["Report", ["no", "Written by hand"], ["yes", "Agent drafts, human signs off"]],
    ];
    const SW = G.slideW, MX = G.margin;
    const xL = MX, wL = 2.6, xA = 3.6, wA = 4.0, xB = 8.3, wB = SW - MX - 8.3, y0 = 1.35, hh = 0.55, rh = 0.72;
    P.rect(s, xB - 0.15, y0, wB + 0.15, hh + rows.length * rh, { fill: C.tint });
    P.text(s, xA, y0, wA, hh, "Prior approaches", { fontSize: 18, bold: true, color: C.muted, valign: "middle" });
    P.text(s, xB + 0.1, y0, wB, hh, "This work", { fontSize: 18, bold: true, color: C.accent, valign: "middle" });
    P.hline(s, xL, SW - MX, y0 + hh, C.text, 1);
    rows.forEach(([crit, [ka, ta], [kb, tb]], i) => {
      const y = y0 + hh + i * rh;
      P.text(s, xL, y, wL, rh, crit, { fontSize: 16, bold: true, color: C.text, valign: "middle" });
      P.mark(s, xA, y + (rh - 0.36) / 2, ka);
      P.text(s, xA + 0.55, y, wA - 0.55, rh, ta, { fontSize: 16, color: C.ink, valign: "middle" });
      P.mark(s, xB + 0.1, y + (rh - 0.36) / 2, kb);
      P.text(s, xB + 0.65, y, wB - 0.7, rh, tb, { fontSize: 16, color: C.ink, valign: "middle" });
      if (i < rows.length - 1) P.hline(s, xL, SW - MX, y + rh);
    });
    P.hline(s, xL, SW - MX, y0 + hh + rows.length * rh, C.text, 1);
    P.conclusion(s, "This work trades external validation for richer inputs; the gap is listed under limitations.",
      G.conclusion.yText);
    P.abbr(s, [["CV", "cross-validation"]]);
    return s;
  },
};

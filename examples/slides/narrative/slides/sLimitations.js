"use strict";
// Limitations: numbered rows, each with what it affects. Notes in notes/sLimitations.md.

module.exports = {
  section: "discussion",
  order: 20,
  build(pres, n, P) {
    const { C, G } = P;
    const SW = G.slideW, MX = G.margin;
    const s = P.newSlide(pres, "Limitations", n);
    P.pattern(s, "Pattern: limitations");
    const items = [
      ["Single-center cohort", "Other scanners, stains and sites are untested"],
      ["No external validation yet", "Performance is cross-validated on one cohort"],
      ["Multiplex data on a subset (n = XX)", "Fusion model trained on fewer patients"],
      ["Agent reports not yet graded", "Draft accuracy unknown; drafts only"],
    ];
    const y0 = 1.3, rh = 1.0;
    P.text(s, MX + 1.0, y0, 5.0, 0.35, "LIMITATION", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
    P.text(s, 6.9, y0, 5.8, 0.35, "WHAT IT AFFECTS", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
    items.forEach(([lim, aff], i) => {
      const y = y0 + 0.45 + i * rh;
      P.hline(s, MX, SW - MX, y);
      P.text(s, MX, y, 0.8, rh, String(i + 1), { fontSize: 28, bold: true, color: C.muted, valign: "middle" });
      P.text(s, MX + 1.0, y, 5.6, rh, lim, { fontSize: 18, bold: true, color: C.text, valign: "middle" });
      P.text(s, 6.9, y, SW - MX - 6.9, rh, aff, { fontSize: 16, color: C.text, valign: "middle" });
    });
    P.hline(s, MX, SW - MX, y0 + 0.45 + items.length * rh);
    P.conclusion(s, "These results are exploratory; an external cohort is needed before any clinical claim.", G.conclusion.yText);
    return s;
  },
};

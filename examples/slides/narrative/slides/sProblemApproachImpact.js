"use strict";
// Problem → approach → impact: three icon columns joined by arrows. Notes in notes/sProblemApproachImpact.md.

module.exports = {
  section: "background",
  order: 20,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Problem, Approach and Impact", n);
    P.pattern(s, "Pattern: problem → approach → impact");
    const cols = [
      ["Problem", "lucide/scan-eye", "Spatial context is lost",
        "Tile models average away where cells sit"],
      ["Approach", "lucide/brain-circuit", "Learn from the tissue",
        "Foundation-model tiles plus cell graphs, trained on outcome"],
      ["Impact", "lucide/users", "Stratify patients by risk",
        "A reproducible score and a draft report for review"],
    ];
    const gap = 0.7, w = (G.contentW - 2 * gap) / 3, y0 = 1.75, isz = 0.9;
    cols.forEach(([tag, ic, head, body], i) => {
      const x = G.margin + i * (w + gap);
      P.icon(s, ic, x + (w - isz) / 2, y0, isz, "accent");
      P.text(s, x, y0 + 1.1, w, 0.35, { runs: [tag.toUpperCase()], align: "center" },
        { fontSize: 14, bold: true, color: C.accent, charSpacing: 2 });
      P.text(s, x, y0 + 1.5, w, 0.5, { runs: [head], align: "center" }, { fontSize: 22, bold: true, color: C.text });
      P.text(s, x + 0.2, y0 + 2.1, w - 0.4, 0.85, { runs: [body], align: "center" }, { fontSize: 16, color: C.text });
      if (i < cols.length - 1) P.arrow(s, x + w + 0.12, y0 + isz / 2, x + w + gap - 0.12, y0 + isz / 2,
        { color: C.muted, width: 1.5 });
    });
    P.conclusion(s, "Goal: a risk score from routine slides and spatial data that a pathologist can check.", G.conclusion.yText);
    return s;
  },
};

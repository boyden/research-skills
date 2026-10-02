"use strict";
// Next steps / roadmap: three time-boxed cards under a time arrow. Notes in notes/sNextSteps.md.

module.exports = {
  section: "closing",
  order: 20,
  build(pres, n, P) {
    const { C, G } = P;
    const SW = G.slideW, MX = G.margin, CW = G.contentW;
    const s = P.newSlide(pres, "Next Steps", n);
    P.pattern(s, "Pattern: next steps / roadmap");
    const cards = [
      ["Next 3 months", "lucide/users", "External validation",
        ["Second cohort, other scanner", "Frozen model, no retraining"]],
      ["3–6 months", "lucide/list-checks", "Grade agent reports",
        ["Blinded scoring of n = XX", "Errors logged per tool"]],
      ["6–12 months", "lucide/code", "Release",
        ["Code and model card", "Preprint, no placeholders"]],
    ];
    const gap = 0.45, w = (CW - 2 * gap) / 3, y0 = 1.7, h = 3.5, hh = 0.5, isz = 0.7;
    // Thin time arrow above the cards.
    P.arrow(s, MX, 1.35, SW - MX, 1.35, { color: C.muted, width: 1.5 });
    cards.forEach(([when, ic, head, lines], i) => {
      const x = MX + i * (w + gap);
      P.rect(s, x, y0, w, hh, { fill: i === 0 ? C.accent : C.text });
      P.text(s, x + 0.2, y0, w - 0.4, hh, when, { fontSize: 16, bold: true, color: C.white, valign: "middle" });
      P.rect(s, x, y0 + hh, w, h - hh, { fill: C.tint });
      P.icon(s, ic, x + 0.25, y0 + hh + 0.3, isz, i === 0 ? "accent" : "grey");
      P.text(s, x + 0.25, y0 + hh + 1.15, w - 0.5, 0.45, head, { fontSize: 20, bold: true, color: C.text, valign: "middle" });
      P.bullets(s, x + 0.25, y0 + hh + 1.8, w - 0.5, h - hh - 1.9, lines, 16);
    });
    P.conclusion(s, "External validation comes first; its result decides whether the later steps go ahead.", G.conclusion.yText);
    return s;
  },
};

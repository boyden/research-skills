"use strict";
// Big statement: one claim, two or three supporting bullets and a citation. Notes in notes/sBigStatement.md.

module.exports = {
  section: "background",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Background", n);
    P.pattern(s, "Pattern: big statement");
    P.rect(s, G.margin, 1.75, 0.08, 1.35, { fill: C.accent });
    P.text(s, G.margin + 0.35, 1.7, G.contentW - 0.6, 1.45,
      "Whole-slide images can be learned from slide-level labels alone, without drawing a single region.",
      { fontSize: 30, bold: true, color: C.black, valign: "middle" });
    P.bullets(s, G.margin + 0.35, 3.75, G.contentW - 0.6, 2.3, [
      [P.b("Weak supervision: "), "attention-based multiple-instance learning finds the regions that drive a slide label"],
      [P.b("Scale: "), "one label per slide makes routine archives usable, not only annotated sets"],
      [P.b("Open question: "), "the same idea for outcome (survival), and for spatial omics next to H&E"],
    ], 18);
    P.cite(s, "lu2021");
    return s;
  },
};

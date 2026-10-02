"use strict";
// Title slide: no topic-title chrome, no page number. Notes in notes/sTitle.md.

module.exports = {
  section: "opening",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Title", n, { chrome: false });
    P.titleFrame(s, 2.3);
    P.pattern(s, "Pattern: title slide");
    P.text(s, 0.95, 2.3, 11.2, 1.3, ["AI for Computational Pathology", "and Spatial Omics"],
      { fontSize: 40, bold: true, color: C.text, valign: "top" });
    P.text(s, 0.95, 3.72, 11.2, 0.45, "From whole-slide images and cell graphs to a survival model and a draft report",
      { fontSize: 20, color: C.muted });
    P.text(s, 6.4, 4.75, G.slideW - G.margin - 6.4, 1.3, [
      { runs: [P.b("Presenter Name, Role")], align: "right", after: 4 },
      { runs: ["Department, Institution"], align: "right", after: 4 },
      { runs: ["Meeting name · Month DD, YYYY"], align: "right" },
    ], { fontSize: 16, color: C.text });
    return s;
  },
};

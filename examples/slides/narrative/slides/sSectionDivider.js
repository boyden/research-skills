"use strict";
// Section divider: no topic title, the section number and name only. Notes in notes/sSectionDivider.md.
const { SECTIONS } = require("./_lib/narrative");

module.exports = {
  section: "opening",
  order: 30,
  build(pres, n, P) {
    const { C } = P;
    const s = P.newSlide(pres, null, n);
    P.pattern(s, "Pattern: section divider");
    P.text(s, 1.2, 2.0, 3.2, 2.2, "02", { fontSize: 120, bold: true, color: C.accent, valign: "middle" });
    P.rect(s, 4.45, 2.35, 0.04, 1.5, { fill: C.rule });
    P.text(s, 4.85, 2.35, 7.5, 0.8, SECTIONS[1][0], { fontSize: 40, bold: true, color: C.text, valign: "middle" });
    P.text(s, 4.85, 3.2, 7.5, 0.6, SECTIONS[1][1], { fontSize: 20, color: C.muted, valign: "middle" });
    return s;
  },
};

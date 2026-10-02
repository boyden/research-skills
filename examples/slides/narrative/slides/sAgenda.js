"use strict";
// Agenda / roadmap: numbered sections, the current one highlighted. Notes in notes/sAgenda.md.
const { SECTIONS } = require("./_lib/narrative");

module.exports = {
  section: "opening",
  order: 20,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Agenda", n);
    P.pattern(s, "Pattern: agenda / roadmap");
    const current = 0, y0 = 1.45, pitch = 0.88, x0 = 1.0, w = G.slideW - 2 * x0;
    SECTIONS.forEach(([name, sub], i) => {
      const y = y0 + i * pitch, on = i === current;
      if (on) {
        P.rect(s, x0, y, w, pitch - 0.1, { fill: C.tint });
        P.rect(s, x0, y, 0.08, pitch - 0.1, { fill: C.accent });
      }
      P.text(s, x0 + 0.35, y, 1.0, pitch - 0.1, String(i + 1).padStart(2, "0"),
        { fontSize: 28, bold: true, color: on ? C.accent : C.rule, valign: "middle" });
      P.text(s, x0 + 1.4, y + 0.06, 4.6, pitch - 0.22, name,
        { fontSize: 22, bold: true, color: on ? C.black : C.muted, valign: "middle" });
      P.text(s, x0 + 6.0, y + 0.06, w - 6.2, pitch - 0.22, sub,
        { fontSize: 16, color: on ? C.text : C.muted, valign: "middle" });
      if (!on && i < SECTIONS.length - 1 && i + 1 !== current) P.hline(s, x0 + 0.35, x0 + w, y + pitch - 0.05);
    });
    return s;
  },
};

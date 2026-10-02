"use strict";
// Callout / annotated figure: km_example with a highlight box and a native callout. Notes in notes/sKmCallout.md.
const { SRC_KM, ABBR_KM } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 70,
  build(pres, n, P) {
    const { C } = P;
    const s = P.newSlide(pres, "Reading the Kaplan–Meier Panel", n);
    P.pattern(s, "Pattern: callout");
    const f = P.figure(s, "km_example.png");
    // Number-at-risk table of the left panel (measured on the 12.1 x 4.6 in figure: x 0.09–3.99, y 3.90–4.55 in).
    const box = { x: f.x + 0.06, y: f.y + 3.87, w: 3.97, h: 0.71 };
    P.rect(s, box.x, box.y, box.w, box.h, { line: C.accent, lineW: 1.5 });
    // Callout in the white space right of the left panel's statistics.
    const cx = f.x + 4.55, cy = f.y + 1.35, cw = 2.2, ch = 1.45;
    P.rect(s, cx, cy, cw, ch, { fill: C.white, line: C.accent, lineW: 0.75 });
    P.text(s, cx + 0.08, cy + 0.06, cw - 0.16, ch - 0.12, [
      { runs: [P.b("Number at risk")], after: 4 },
      "Patients still event-free and followed at 0, 2, 4 and 6 years. Only 18 per arm remain at 6 years.",
    ], { fontSize: 12, color: C.ink });
    P.line(s, cx + 0.05, cy + ch, box.x + box.w - 0.05, box.y);
    P.conclusion(s, "By 6 years only 18 women per arm remain at risk, so the curves beyond 6 years rest on " +
      "few patients (n = 686, 299 events).");
    P.abbr(s, ABBR_KM);
    P.source(s, SRC_KM);
    return s;
  },
};

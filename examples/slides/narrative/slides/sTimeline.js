"use strict";
// Timeline / study design: milestones on one axis, labels alternating above and below. Notes in notes/sTimeline.md.

module.exports = {
  section: "methods",
  order: 50,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Study Design — Patient Timeline", n);
    P.pattern(s, "Pattern: timeline");
    const ay = 3.3, x0 = 1.0, x1 = G.slideW - 0.9;
    P.arrow(s, x0, ay, x1, ay, { color: C.text, width: 2 });
    P.text(s, x1 - 2.6, ay + 0.12, 2.6, 0.3, { runs: ["Time from diagnosis"], align: "right" },
      { fontSize: 12, italic: true, color: C.muted });
    const ms = [
      ["healthicons/biopsy", "Diagnosis", "t = 0; biopsy confirms cancer", true],
      ["healthicons/tissue", "Surgery", "Tissue scanned and imaged", false],
      ["healthicons/hospital", "Adjuvant therapy", "Chemotherapy or hormone therapy", false],
      ["healthicons/regular-patient", "Follow-up", "Visits until event or last contact", false],
      ["healthicons/chart-line", "Event or censoring", "Recurrence or death", true],
    ];
    // First and last milestone sit 1.4 in inside the margins, so their 2.8 in labels stay within them.
    const xa = G.margin + 1.4, xb = G.slideW - G.margin - 1.4, step = (xb - xa) / (ms.length - 1), isz = 0.6, lw = 2.8;
    ms.forEach(([ic, head, body, key], i) => {
      const x = xa + i * step, up = i % 2 === 0;
      const d = 0.26;
      s.addShape("ellipse", { x: x - d / 2, y: ay - d / 2, w: d, h: d,
        fill: { color: key ? C.accent : C.white }, line: { color: key ? C.accent : C.text, width: 1.5 } });
      if (up) {
        P.line(s, x, ay - 0.75, x, ay - d / 2, C.rule, 1);
        P.icon(s, ic, x - isz / 2, ay - 1.4, isz, key ? "accent" : "grey");
        P.text(s, x - lw / 2, ay - 2.2, lw, 0.75, [{ runs: [P.b(head)], align: "center", after: 2 },
          { runs: [body], align: "center" }], { fontSize: 13, color: C.text, valign: "bottom" });
      } else {
        P.line(s, x, ay + d / 2, x, ay + 0.75, C.rule, 1);
        P.icon(s, ic, x - isz / 2, ay + 0.8, isz, key ? "accent" : "grey");
        P.text(s, x - lw / 2, ay + 1.47, lw, 0.75, [{ runs: [P.b(head)], align: "center", after: 2 },
          { runs: [body], align: "center" }], { fontSize: 13, color: C.text });
      }
    });
    P.conclusion(s, "Recurrence-free survival runs from diagnosis to recurrence or death; in GBSG2, 299 of 686 " +
      "patients had an event and the rest were censored at last follow-up.", G.conclusion.yText);
    P.source(s, "Source: GBSG2 trial (lifelines load_gbsg2); event counts");
    return s;
  },
};

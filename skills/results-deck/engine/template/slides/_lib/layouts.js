/*
 * Layouts shared by this deck's page files (engine/SPEC.md §3: slides/_lib/ is not collected as pages).
 * Positions are offsets from the theme geometry (P.G) and colors / sizes come from the theme (P.T), so the
 * page files carry only their content and a theme change needs no page edits.
 * Integrator-owned and append-only: add a function, do not change what existing pages rely on.
 */
"use strict";

// build.js maps "results-deck" to the engine primitives: the same object as the P handed to build().
const P = require("results-deck");

/*
 * Title slide content on a {chrome: false} slide: the accent frame, a two-line talk title, a subtitle and a
 * right-aligned block of presenter lines (the first one bold).
 */
function titleSlide(s, { title, subtitle, presenter }) {
  const { G, T, C } = P;
  const [barX, barY, , barH] = G.titleSlide.accentBar;
  const x = barX + 0.35;                          // text starts just right of the accent bar
  const w = G.slideW - x - 2 * G.margin;
  P.titleFrame(s);
  P.text(s, x, barY, w, barH * 0.7, title, { fontSize: T.size.title + 12, bold: true, color: C.text, valign: "top" });
  P.text(s, x, barY + barH * 0.76, w, 0.45, subtitle, { fontSize: T.size.conclusion + 2, color: C.muted });
  const bw = G.contentW * 0.52;
  P.text(s, G.slideW - G.margin - bw, barY + barH + 0.59, bw, 1.3, presenter.map((line, i) => ({
    runs: [i === 0 ? P.b(line) : line], align: "right", ...(i < presenter.length - 1 ? { after: 4 } : {}),
  })), { fontSize: T.size.body, color: C.text });
}

/*
 * Numbered takeaways: one row per [claim, evidence], a large accent numeral on the left, the claim in bold
 * and one line of evidence under it, thin rules between the rows.
 */
function numberedTakeaways(s, items) {
  const { G, T, C } = P;
  const y0 = G.figureTop + 0.35;
  const rowH = (G.conclusion.yFigure + G.conclusion.h - y0) / items.length;
  const claimPt = T.size.conclusion + 4;
  const textX = G.margin + 1.1;
  items.forEach(([claim, evidence], i) => {
    const y = y0 + i * rowH;
    if (i) P.hline(s, G.margin, G.slideW - G.margin, y - 0.1);
    P.text(s, G.margin, y, 1.0, 1.2, String(i + 1), { fontSize: 2 * claimPt, bold: true, color: C.accent, valign: "top" });
    P.text(s, textX, y + 0.08, G.contentW - 1.1, 0.5, claim, { fontSize: claimPt, bold: true, color: C.black });
    P.text(s, textX, y + 0.62, G.contentW - 1.1, 0.55, evidence, { fontSize: T.size.body, color: C.text });
  });
}

/*
 * A native three-line table centered under the title. ``weights`` are relative column widths, scaled to
 * ``fill`` of the content width; the header row is two lines tall, body rows one line (at ``fontSize``).
 */
function centeredTable(s, rows, weights, { fontSize = P.T.size.body, fill = 0.97 } = {}) {
  const { G } = P;
  const total = weights.reduce((a, c) => a + c, 0);
  const colW = weights.map((c) => (c / total) * G.contentW * fill);
  const line = fontSize / 72;                     // one text line, in inches
  const rowH = [3.6 * line, ...Array(rows.length - 1).fill(2.25 * line)];
  const w = colW.reduce((a, c) => a + c, 0);
  P.table(s, (G.slideW - w) / 2, G.figureTop + 0.2, colW, rowH, rows, { fontSize });
}

module.exports = { titleSlide, numberedTakeaways, centeredTable };

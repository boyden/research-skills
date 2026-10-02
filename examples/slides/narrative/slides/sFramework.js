"use strict";
// Framework diagram: inputs → processing band → outputs. Notes in notes/sFramework.md.

module.exports = {
  section: "methods",
  order: 30,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Framework Overview", n);
    P.pattern(s, "Pattern: framework diagram");
    const rowY = [1.95, 3.35, 4.75];           // center line of each input row
    const isz = 0.7;
    // Inputs
    [["lucide/microscope", "H&E slides"], ["tabler/stack-2", "Multiplex imaging"],
      ["lucide/clipboard-list", "Clinical data"]].forEach(([ic, lab], i) => {
      P.icon(s, ic, G.margin, rowY[i] - isz / 2, isz, "accent");
      P.text(s, G.margin + 0.82, rowY[i] - 0.3, 1.3, 0.6, lab, { fontSize: 14, bold: true, color: C.text, valign: "middle" });
    });
    // Processing band
    const bx = 3.25, bw = 6.3, by = 1.2, bh = 4.3;
    P.rect(s, bx, by, bw, bh, { fill: C.tint });
    P.text(s, bx + 0.2, by + 0.08, 3, 0.3, "PROCESSING", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
    const box = (x, y, w, h, label) => {
      P.rect(s, x, y, w, h, { fill: C.white, line: C.rule, lineW: 1 });
      P.text(s, x + 0.08, y, w - 0.16, h, { runs: [label], align: "center" }, { fontSize: 13, color: C.ink, valign: "middle" });
    };
    const c1 = bx + 0.3, c2 = bx + 2.35, bwid = 1.7, bht = 0.7;
    const fx = bx + 4.45, fw = 1.6, fy = rowY[0] - 0.25, fh = rowY[2] - rowY[0] + 0.5;
    box(c1, rowY[0] - bht / 2, bwid, bht, "Tile + embed");
    box(c2, rowY[0] - bht / 2, bwid, bht, "Attention MIL");
    box(c1, rowY[1] - bht / 2, bwid, bht, "Segment cells");
    box(c2, rowY[1] - bht / 2, bwid, bht, "Cell graph GNN");
    box(c1, rowY[2] - bht / 2, bwid, bht, "Encode covariates");
    P.rect(s, fx, fy, fw, fh, { fill: C.white, line: C.accent, lineW: 1.25 });
    P.text(s, fx + 0.1, fy, fw - 0.2, fh, [{ runs: [P.b("Fusion")], align: "center", after: 4 },
      { runs: ["+ Cox head"], align: "center" }], { fontSize: 14, color: C.ink, valign: "middle" });
    [0, 1].forEach((i) => P.thinArrow(s, c1 + bwid + 0.04, rowY[i], c2 - 0.04, rowY[i]));
    [0, 1].forEach((i) => P.thinArrow(s, c2 + bwid + 0.04, rowY[i], fx - 0.04, rowY[i]));
    P.thinArrow(s, c1 + bwid + 0.04, rowY[2], fx - 0.04, rowY[2]);
    // Input and output arrows: one thick accent arrow each, outside the band.
    rowY.forEach((y) => P.thickArrow(s, 2.7, y, bx - 0.05, y));
    const outY = [2.65, 4.05];
    outY.forEach((y) => P.thickArrow(s, bx + bw + 0.05, y, bx + bw + 0.55, y));
    [["tabler/chart-histogram", "Risk score", "per patient"], ["tabler/photo-scan", "Attention maps", "per slide"]]
      .forEach(([ic, lab, sub], i) => {
        const ox = bx + bw + 0.7;
        P.icon(s, ic, ox, outY[i] - isz / 2, isz, "accent");
        P.text(s, ox + 0.85, outY[i] - 0.35, G.slideW - G.margin - ox - 0.85, 0.7,
          [{ runs: [P.b(lab)] }, { runs: [sub] }], { fontSize: 14, color: C.text, valign: "middle" });
      });
    P.conclusion(s, "Image, cell-graph and clinical features are fused into one patient-level risk score.");
    P.abbr(s, [["MIL", "multiple-instance learning"], ["GNN", "graph neural network"]]);
    return s;
  },
};

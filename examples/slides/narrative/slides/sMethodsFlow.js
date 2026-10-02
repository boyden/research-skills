"use strict";
// Methods flow: numbered step cards with arrows, definitions below. Notes in notes/sMethodsFlow.md.

module.exports = {
  section: "methods",
  order: 20,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Methods — Slide to Survival", n);
    P.pattern(s, "Pattern: methods flow");
    const steps = [
      ["Tile", "tabler/grid-scan", "Tissue tiles at 20×; background masked out"],
      ["Embed", "tabler/cube-spark", "Frozen pathology foundation model; one vector per tile"],
      ["Aggregate", "lucide/network", "Attention MIL or cell graph pools tiles per slide"],
      ["Score", "tabler/chart-histogram", "Linear Cox head: one risk score per patient"],
      ["Survival", "lucide/trending-down", "Cox model and KM by median score; 5-fold CV"],
    ];
    const gap = 0.32, w = (G.contentW - 4 * gap) / 5, y0 = 1.3, h = 2.3, hh = 0.42, isz = 0.6;
    steps.forEach(([name, ic, body], i) => {
      const x = G.margin + i * (w + gap);
      P.rect(s, x, y0, w, hh, { fill: C.accent });
      P.text(s, x + 0.12, y0, w - 0.24, hh, `${i + 1} · ${name}`, { fontSize: 14, bold: true, color: C.white, valign: "middle" });
      P.rect(s, x, y0 + hh, w, h - hh, { fill: C.tint });
      P.icon(s, ic, x + 0.15, y0 + hh + 0.18, isz, "accent");
      P.text(s, x + 0.15, y0 + hh + 0.92, w - 0.3, h - hh - 1.0, body, { fontSize: 13, color: C.ink });
      if (i < steps.length - 1) P.stepArrow(s, x + w + (gap - 0.2) / 2, y0 + h / 2);
    });
    P.bullets(s, G.margin, 3.85, G.contentW, 1.9, [
      [P.b("MIL "), "(multiple-instance learning): the slide label is known, the tile labels are not"],
      [P.b("Foundation model: "), "pretrained on unlabeled tiles; its weights stay frozen, only later layers train"],
      [P.b("Folds split by patient, "), "so tiles of one patient are never in both training and test"],
    ], 16);
    P.conclusion(s, "Tiling and embeddings are fixed before outcomes are seen; only the aggregator and the Cox head " +
      "are trained on survival.", G.conclusion.yText);
    P.abbr(s, [["MIL", "multiple-instance learning"], ["KM", "Kaplan–Meier"], ["CV", "cross-validation"]]);
    return s;
  },
};

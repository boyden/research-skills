"use strict";
// Supplementary slide, hidden in the pptx (section supplementary): model settings. Notes in notes/sSuppModelSettings.md.

module.exports = {
  section: "supplementary",
  order: 10,
  build(pres, n, P) {
    const { G } = P;
    const s = P.newSlide(pres, "Supplementary — Model Settings", n);
    P.pattern(s, "Pattern: supplementary (hidden)");
    const rows = [
      ["Component", "Setting", "Value", "Fixed before outcomes?"],
      ["Tiling", "Tile size; magnification", "256 × 256 px; 20×", "Yes"],
      ["Tissue mask", "Threshold on saturation", "Otsu", "Yes"],
      ["Foundation model", "Encoder; embedding dimension", "Frozen ViT; XX", "Yes"],
      ["Attention MIL", "Hidden units; dropout", "XX; XX", "Yes"],
      ["Cell graph", "Edges; neighbors per cell", "k-nearest neighbors; k = XX", "Yes"],
      ["Cox head", "Penalty; learning rate; epochs", "L2 XX; XX; XX", "Tuned in inner folds"],
      ["Cross-validation", "Folds; split unit; random_state", "5; patient; 0", "Yes"],
      ["Agent", "Model; temperature; max tool calls", "XX; 0; XX", "Yes"],
    ];
    const colW = [2.4, 3.7, 3.3, 2.7];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.2, colW, 0.46, rows, { fontSize: 13, labelCol: true });
    P.conclusion(s, "All settings except the Cox penalty were fixed before outcome data were used; random_state is " +
      "recorded in run_meta.json.");
    P.abbr(s, [["MIL", "multiple-instance learning"], ["ViT", "vision transformer"], ["L2", "ridge penalty"]]);
    return s;
  },
};

"use strict";
// Key takeaways: three numbered messages, each with one line of evidence. Notes in notes/sSummary.md.

module.exports = {
  section: "closing",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const SW = G.slideW, MX = G.margin, CW = G.contentW;
    const s = P.newSlide(pres, "Summary", n);
    P.pattern(s, "Pattern: key takeaways");
    const items = [
      ["Routine slides and spatial data feed one risk score",
        "Tiling and embeddings fixed; only the aggregator and Cox head see outcomes (methods flow)"],
      ["Cell graphs add the spatial context that tile averages lose",
        "C-index XX vs XX, 5-fold CV (n = XX patients); placeholders for this example"],
      ["An agent drafts the report; a pathologist signs it off",
        "Every statement links back to a tool output (agent loop)"],
    ];
    const y0 = 1.45, rh = 1.65;
    items.forEach(([claim, ev], i) => {
      const y = y0 + i * rh;
      if (i) P.hline(s, MX, SW - MX, y - 0.1);
      P.text(s, MX, y, 1.0, 1.2, String(i + 1), { fontSize: 44, bold: true, color: C.accent, valign: "top" });
      P.text(s, MX + 1.1, y + 0.08, CW - 1.1, 0.5, claim, { fontSize: 22, bold: true, color: C.black });
      P.text(s, MX + 1.1, y + 0.62, CW - 1.1, 0.55, ev, { fontSize: 16, color: C.text });
    });
    P.abbr(s, [["C-index", "concordance index"], ["CV", "cross-validation"]]);
    return s;
  },
};

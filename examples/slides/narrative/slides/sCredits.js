"use strict";
// Credits: every icon source, license and data source used in the deck. Notes in notes/sCredits.md.

module.exports = {
  section: "credits",
  order: 10,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Credits", n);
    P.pattern(s, "Pattern: credits");
    const rows = [
      ["Source", "Icons used in this deck", "License"],
      ["Health Icons (healthicons.org)", "biopsy, tissue, hospital, regular-patient, chart-line", "CC0 1.0"],
      ["Lucide (lucide.dev)", ["scan-eye, brain-circuit, users, network, trending-down, microscope, clipboard-list,",
        "list-checks, toolbox, message-square-text, bot, book-open-text, code"], "ISC (code: MIT, Feather)"],
      ["Tabler Icons (tabler.io/icons)", "grid-scan, cube-spark, chart-histogram, stack-2, photo-scan, api", "MIT"],
      ["Bioicons (bioicons.com)", "glass-slide — Servier Medical Art (smart.servier.com)", "CC BY 3.0"],
      ["", "confocal-microscope — DBCLS TogoTV", "CC BY 4.0"],
      ["", "single-cell-umap — James Lloyd; patient — Marcel Tisch", "CC0 1.0"],
    ];
    const colW = [3.3, 6.4, 2.4];
    const w = colW.reduce((a, c) => a + c, 0);
    P.table(s, (G.slideW - w) / 2, 1.25, colW, [0.45, 0.45, 0.72, 0.45, 0.45, 0.45, 0.45], rows, { fontSize: 12 });
    P.text(s, (G.slideW - w) / 2, 4.95, w, 1.4, [
      { runs: [P.b("Data: "), "GBSG2 trial counts (686 patients, 299 recurrence-or-death events) via lifelines load_gbsg2."],
        after: 6 },
      { runs: [P.b("Reference: "), "Lu, Ming Y., et al. ", P.it("Nature Biomedical Engineering"), " 5.6 (2021): 555–570."],
        after: 6 },
      { runs: ["All other content is an illustrative example; values marked XX are placeholders."] },
    ], { fontSize: 13, color: C.text });
    return s;
  },
};

"use strict";
// Three numbered takeaways; every number repeats one shown on an earlier slide. Notes in notes/sSummary.md.
const { numberedTakeaways } = require("./_lib/layouts");

module.exports = {
  section: "summary",
  order: 10,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Summary", n);
    numberedTakeaways(s, [
      ["Tamoxifen is associated with longer recurrence-free survival",
        "HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events (univariate Cox)"],
      ["Positive lymph nodes carry the strongest univariate association",
        "HR 1.65 [1.48–1.84] per SD, q < 0.001; largest effect of eight clinical factors"],
      ["The tamoxifen group differs at baseline",
        "Older (median 58 vs 50 years) and more often postmenopausal (76% vs 48%); see Supplementary"],
    ]);
    P.abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["q", "Benjamini–Hochberg adjusted p"]]);
    return s;
  },
};

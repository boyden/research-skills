// Test fixture for engine/tools/pull_notes.py: a deck whose wip pages.json was derived by hand from
// examples/slides/output/results_examples.pptx (13 slides; "Clinical Factors — Univariate Cox" on 3 of them).
// notes/ holds an outdated notes file (sRoc), one of a page that is gone (sRemoved) and _aliases.json.
module.exports = {
  name: "results_examples",
  title: "Result slide patterns",
  outDir: "output",
  lang: "en",
  sections: ["results", "supplementary"],
  supplementary: "supplementary",
};

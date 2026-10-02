/*
 * Deck configuration read by engine/js/build.js (format: engine/SPEC.md §2.1). Paths are relative to this
 * directory. Only the sections and their order live here; each slides/<key>.js declares its own section
 * and order.
 */
"use strict";

module.exports = {
  name: "example_deck",            // output file prefix: output/example_deck_wip.pptx, _v1, _v2 ...
  title: "Example Results Deck",   // pptx metadata title
  outDir: "output",
  figDir: "figures",               // drawn by plotting/ (python <engine>/tools/plot.py .)
  iconDir: null,                   // null = research-skills/examples/icons
  theme: "theme",                  // replace this directory (or point here to another one) to change the style
  lang: "en",                      // language of the blocks pages.py writes into outline/README.md
  refs: {
    schumacher1994: ["Schumacher, M.", "Journal of Clinical Oncology", "12.10 (1994): 2086–2093"],
  },
  sections: ["title", "results", "summary", "supplementary"],
  supplementary: "supplementary",  // pages of this section are hidden in the pptx and kept in the PDF
};

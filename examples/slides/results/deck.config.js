/*
 * Results example deck (engine/SPEC.md §2.1): classic result-slide types on the public GBSG2 example figures.
 * Paths are relative to this directory. Build with examples/slides/render.sh, or directly:
 *
 *   node skills/results-deck/engine/js/build.js examples/slides/results \
 *     --out examples/slides/output/results_examples.pptx --png
 */
"use strict";

module.exports = {
  name: "results_examples",
  title: "Result slide patterns",
  outDir: "../output",
  figDir: "../../figures",                               // examples/figures, drawn by examples/plotting/
  iconDir: null,                                         // null = research-skills/examples/icons
  theme: "../../../skills/results-deck/engine/themes/neutral",  // the engine's default theme, no copy here
  lang: "en",
  refs: {},
  sections: ["results", "supplementary"],
  supplementary: "supplementary",
};

/*
 * Narrative example deck (engine/SPEC.md §2.1): classic structure slides told as one ILLUSTRATIVE study,
 * "AI for computational pathology and spatial omics". Paths are relative to this directory. Build with
 * examples/slides/render.sh, or directly:
 *
 *   node skills/results-deck/engine/js/build.js examples/slides/narrative \
 *     --out examples/slides/output/narrative_examples.pptx --png
 */
"use strict";

module.exports = {
  name: "narrative_examples",
  title: "Narrative slide patterns",
  outDir: "../output",
  figDir: "../../figures",                               // examples/figures (no figure is used by this deck)
  iconDir: null,                                         // null = research-skills/examples/icons
  theme: "../../../skills/results-deck/engine/themes/neutral",  // the engine's default theme, no copy here
  lang: "en",
  // Reference registry for cite(): key -> [author, journal, rest, isOrg?].
  refs: {
    lu2021: ["Lu, Ming Y.", "Nature Biomedical Engineering", "5.6 (2021): 555–570"],
  },
  // The credits page comes last, after the hidden supplementary page.
  sections: ["opening", "background", "methods", "discussion", "closing", "supplementary", "credits"],
  supplementary: "supplementary",
};

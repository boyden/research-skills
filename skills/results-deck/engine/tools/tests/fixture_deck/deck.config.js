// Test fixture for engine/tools (pages.py reads only `name:`, `outDir:` and `lang:` from this file).
// lang is "zh" because outline/README.md is a copy of the template outline, which is in Chinese.
module.exports = {
  name: "fixture_deck",
  title: "Fixture Deck",
  outDir: "output",
  figDir: "figures",
  iconDir: null,
  theme: "theme",
  lang: "zh",
  refs: {},
  sections: ["title", "results", "summary", "supplementary"],
  supplementary: "supplementary",
};

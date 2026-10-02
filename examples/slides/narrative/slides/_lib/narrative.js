/*
 * Shared by the narrative example pages (engine/SPEC.md §3: slides/_lib/ is not collected as pages).
 *
 * The study is a design example, not a real study: no result numbers are invented. Counts that would come
 * from a real cohort are written as placeholders ("n = XX"); the only real numbers are the public GBSG2
 * counts (686 patients, 299 recurrence-or-death events; lifelines load_gbsg2). Icons come from
 * examples/icons/ (open licenses; every icon used is listed on the credits page, sCredits). Every page's
 * speaker notes (notes/<key>.md) end with the same "Illustrative example" paragraph.
 */
"use strict";

// Section names and subtitles, shared by the agenda (sAgenda) and the section divider (sSectionDivider).
const SECTIONS = [
  ["Background", "Why tissue architecture matters"],
  ["Data and methods", "Slides, spatial omics and the survival model"],
  ["Results", "Risk score and model comparison"],
  ["Report-drafting agent", "LLM / VLM agent that writes a draft report"],
  ["Limitations and next steps", "What the results can and cannot support"],
];

module.exports = { SECTIONS };

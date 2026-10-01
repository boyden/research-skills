/*
 * Gallery of classic narrative / structure slide patterns (title, agenda, divider, statement, methods
 * flow, framework, agent loop, timeline, comparison, limitations, summary, next steps, closing, supplementary,
 * credits), told as one ILLUSTRATIVE study: "AI for computational pathology and spatial omics".
 *
 *   NODE_PATH=<dir with pptxgenjs> node examples/slides/build_narrative.js
 *   -> examples/slides/output/narrative_examples.pptx
 *
 * The study is a design example, not a real study: no result numbers are invented. Counts that would
 * come from a real cohort are written as placeholders ("n = XX"); the only real numbers are the public
 * GBSG2 counts (686 patients, 299 recurrence-or-death events; lifelines load_gbsg2). Icons come from
 * examples/icons/ (open licences; every icon used is listed on the credits slide).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const {
  C, FONT, SERIF, SW, SH, MX, CW, b, it, toRuns, text, bullets, rect, hline, icon, table,
  newSlide, conclusion, source, newDeck, pattern, line,
} = require("./common");

const OUT = path.join(__dirname, "output");
const ILLUSTRATIVE = "Illustrative example: a design example, not a real study. Placeholders (n = XX) stand " +
  "where a real deck would put numbers from its own result tables.";
const CONC_TEXT_Y = 5.95;   // conclusion box on slides without a main figure

// ---- Local helpers -----------------------------------------------------------------------------
// "ABBR: expansion; ABBR: expansion." bottom left, bottom-aligned so it sits on the source line.
function abbr(slide, entries, w = 6.0) {
  const runs = entries.flatMap(([a, e], i) => [...(i ? [" "] : []), b(`${a}: `), `${e}${i < entries.length - 1 ? ";" : "."}`]);
  slide.addText(toRuns({ runs }, { fontSize: 9.5, color: C.muted }),
    { x: MX, y: 6.85, w, h: 0.55, margin: 0, valign: "bottom", align: "left", fontFace: FONT, wrap: true });
}

// Arrow from (x1, y1) to (x2, y2) with the head at (x2, y2). pptx lines run from their top-left (or, flipped,
// top-right) corner, so the head goes on the line's end when the arrow points down or level, else on its start.
function arrow(slide, x1, y1, x2, y2, { color = C.muted, width = 1, head = "triangle" } = {}) {
  const headAtEnd = y2 >= y1;
  slide.addShape("line", {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: (x2 < x1) !== (y2 < y1),
    line: { color, width, ...(headAtEnd ? { endArrowType: head } : { beginArrowType: head }) },
  });
}
// The two arrow weights of a framework diagram: thin grey inside a processing band, thick accent outside.
const thinArrow = (s, x1, y1, x2, y2) => arrow(s, x1, y1, x2, y2, { color: C.muted, width: 1 });
const thickArrow = (s, x1, y1, x2, y2) => arrow(s, x1, y1, x2, y2, { color: C.accent, width: 3.5 });

// Small filled right-pointing arrow between step cards (methods-flow pattern).
function stepArrow(slide, x, yMid, w = 0.2, h = 0.24) {
  slide.addShape("rightArrow", { x, y: yMid - h / 2, w, h, fill: { color: C.muted }, line: { type: "none" } });
}

// Circle marker with a check (accent), a cross (grey) or a dash (partial, grey), drawn from native lines.
function mark(slide, x, y, kind, d = 0.36) {
  const col = kind === "yes" ? C.accent : C.muted;
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: C.white }, line: { color: col, width: 1.5 } });
  const cx = x + d / 2, cy = y + d / 2, r = d * 0.22;
  if (kind === "yes") {
    line(slide, cx - r, cy, cx - r * 0.25, cy + r * 0.75, col, 2);
    line(slide, cx - r * 0.25, cy + r * 0.75, cx + r * 1.05, cy - r * 0.8, col, 2);
  } else if (kind === "no") {
    line(slide, cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8, col, 2);
    line(slide, cx - r * 0.8, cy + r * 0.8, cx + r * 0.8, cy - r * 0.8, col, 2);
  } else {
    line(slide, cx - r, cy, cx + r, cy, col, 2);
  }
}

// Title-slide frame (also used by the closing slide): logo placeholder top left, accent bar left of the
// title band, full-width accent rule at the bottom.
function titleFrame(slide, barY, barH = 1.86) {
  slide.background = { color: C.white };
  text(slide, MX, 0.3, 2.4, 0.35, "YOUR LOGO", { fontSize: 11, bold: true, color: C.rule });
  rect(slide, MX, barY, 0.1, barH, { fill: C.accent });
  rect(slide, 0, 6.83, SW, 0.05, { fill: C.accent });
}

// Literature citation in the source position (9 pt serif, right/bottom aligned) with an italic journal run.
function cite(slide, runs) {
  slide.addText(toRuns({ runs, align: "right" }, { fontSize: 9, color: C.ink, fontFace: SERIF }),
    { x: 0.6, y: 6.82, w: SW - 0.6 - 1.05, h: 0.6, margin: 0, valign: "bottom", fontFace: SERIF, wrap: true });
}

function notes(slide, lines) { slide.addNotes([...lines, ILLUSTRATIVE].join("\n\n")); }

// ---- Deck --------------------------------------------------------------------------------------
const pres = newDeck("Narrative slide patterns");
let n = 0;
const SECTIONS = [
  ["Background", "Why tissue architecture matters"],
  ["Data and methods", "Slides, spatial omics and the survival model"],
  ["Results", "Risk score and model comparison"],
  ["Report-drafting agent", "LLM / VLM agent that writes a draft report"],
  ["Limitations and next steps", "What the results can and cannot support"],
];

// 1 · Title -------------------------------------------------------------------------------------
{
  const s = pres.addSlide();
  titleFrame(s, 2.3);
  pattern(s, "Pattern: title slide");
  text(s, 0.95, 2.3, 11.2, 1.3, ["AI for Computational Pathology", "and Spatial Omics"],
    { fontSize: 40, bold: true, color: C.text, valign: "top" });
  text(s, 0.95, 3.72, 11.2, 0.45, "From whole-slide images and cell graphs to a survival model and a draft report",
    { fontSize: 20, color: C.muted });
  text(s, 6.4, 4.75, SW - MX - 6.4, 1.3, [
    { runs: [b("Presenter Name, Role")], align: "right", after: 4 },
    { runs: ["Department, Institution"], align: "right", after: 4 },
    { runs: ["Meeting name · Month DD, YYYY"], align: "right" },
  ], { fontSize: 16, color: C.text });
  notes(s, [
    "PATTERN: title slide. The first slide carries the talk title, the presenter, affiliation and date; it has " +
    "no topic-title chrome and no page number.",
    "Design rules shown: logo placeholder top left; title in a horizontal band with a thin accent bar on its " +
    "left (0.1 x 1.86 in) and a full-width accent rule near the bottom (y 6.83); the title wraps onto two lines " +
    "inside one text box; presenter, affiliation and date right-aligned under the title. The presenter's name " +
    "appears only here (and in literature citations), never in notes, code or other slides.",
  ]);
}

// 2 · Agenda ------------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Agenda", ++n);
  pattern(s, "Pattern: agenda / roadmap");
  const current = 0, y0 = 1.45, pitch = 0.88, x0 = 1.0, w = SW - 2 * x0;
  SECTIONS.forEach(([name, sub], i) => {
    const y = y0 + i * pitch, on = i === current;
    if (on) {
      rect(s, x0, y, w, pitch - 0.1, { fill: C.tint });
      rect(s, x0, y, 0.08, pitch - 0.1, { fill: C.accent });
    }
    text(s, x0 + 0.35, y, 1.0, pitch - 0.1, String(i + 1).padStart(2, "0"),
      { fontSize: 28, bold: true, color: on ? C.accent : C.rule, valign: "middle" });
    text(s, x0 + 1.4, y + 0.06, 4.6, pitch - 0.22, name,
      { fontSize: 22, bold: true, color: on ? C.black : C.muted, valign: "middle" });
    text(s, x0 + 6.0, y + 0.06, w - 6.2, pitch - 0.22, sub,
      { fontSize: 16, color: on ? C.text : C.muted, valign: "middle" });
    if (!on && i < SECTIONS.length - 1 && i + 1 !== current) hline(s, x0 + 0.35, x0 + w, y + pitch - 0.05);
  });
  notes(s, [
    "PATTERN: agenda / roadmap. Show it after the title, and again at each section start with that section " +
    "highlighted, so the audience always knows where they are. Four to six sections; more is a table of contents.",
    "Design rules shown: numbered rows; the current section has an accent numeral, black name, tint band and accent " +
    "edge bar; the other sections are muted grey; one short subtitle per section, no bullets. Reuse the same " +
    "geometry on every repeat so only the highlight moves.",
  ]);
}

// 3 · Section divider ---------------------------------------------------------------------------
{
  const s = newSlide(pres, null, ++n);
  pattern(s, "Pattern: section divider");
  text(s, 1.2, 2.0, 3.2, 2.2, "02", { fontSize: 120, bold: true, color: C.accent, valign: "middle" });
  rect(s, 4.45, 2.35, 0.04, 1.5, { fill: C.rule });
  text(s, 4.85, 2.35, 7.5, 0.8, SECTIONS[1][0], { fontSize: 40, bold: true, color: C.text, valign: "middle" });
  text(s, 4.85, 3.2, 7.5, 0.6, SECTIONS[1][1], { fontSize: 20, color: C.muted, valign: "middle" });
  notes(s, [
    "PATTERN: section divider. Use it between major blocks of a long talk (20 minutes or more) as a pause; in a " +
    "short talk the repeated agenda slide does the same job.",
    "Design rules shown: no topic title, nothing to read except the number and the section name (the same words " +
    "as on the agenda); one accent numeral, a thin grey rule, white space. The page number stays.",
  ]);
}

// 4 · Big statement -----------------------------------------------------------------------------
{
  const s = newSlide(pres, "Background", ++n);
  pattern(s, "Pattern: big statement");
  rect(s, MX, 1.75, 0.08, 1.35, { fill: C.accent });
  text(s, MX + 0.35, 1.7, CW - 0.6, 1.45,
    "Whole-slide images can be learned from slide-level labels alone, without drawing a single region.",
    { fontSize: 30, bold: true, color: C.black, valign: "middle" });
  bullets(s, MX + 0.35, 3.75, CW - 0.6, 2.3, [
    [b("Weak supervision: "), "attention-based multiple-instance learning finds the regions that drive a slide label"],
    [b("Scale: "), "one label per slide makes routine archives usable, not only annotated sets"],
    [b("Open question: "), "the same idea for outcome (survival), and for spatial omics next to H&E"],
  ], 18);
  cite(s, ["Lu, Ming Y., et al. ", it("Nature Biomedical Engineering"), " 5.6 (2021): 555–570"]);
  notes(s, [
    "PATTERN: big statement. Use it to open the background with the one sentence the audience should accept " +
    "before the study makes sense; two or three bullets give the support, a citation backs the claim.",
    "Design rules shown: the statement is a complete sentence in 30 pt bold black next to a thin accent bar; " +
    "bullets 18 pt grey with a bold lead phrase; the citation sits in the source position, 9 pt serif, journal " +
    "in italics, format 'Surname, Given, et al. Journal vol.issue (year): pages'. No separate conclusion box: " +
    "the statement is the take-home line.",
    "Reference: CLAM, data-efficient weakly supervised computational pathology on whole-slide images; " +
    "PMID 33649564, doi 10.1038/s41551-020-00682-w (checked against PubMed metadata).",
  ]);
}

// 5 · Problem → Approach → Impact ---------------------------------------------------------------
{
  const s = newSlide(pres, "Problem, Approach and Impact", ++n);
  pattern(s, "Pattern: problem → approach → impact");
  const cols = [
    ["Problem", "lucide/scan-eye", "Spatial context is lost",
      "Tile models average away where cells sit"],
    ["Approach", "lucide/brain-circuit", "Learn from the tissue",
      "Foundation-model tiles plus cell graphs, trained on outcome"],
    ["Impact", "lucide/users", "Stratify patients by risk",
      "A reproducible score and a draft report for review"],
  ];
  const gap = 0.7, w = (CW - 2 * gap) / 3, y0 = 1.75, isz = 0.9;
  cols.forEach(([tag, ic, head, body], i) => {
    const x = MX + i * (w + gap);
    icon(s, ic, x + (w - isz) / 2, y0, isz, "accent");
    text(s, x, y0 + 1.1, w, 0.35, { runs: [tag.toUpperCase()], align: "center" },
      { fontSize: 14, bold: true, color: C.accent, charSpacing: 2 });
    text(s, x, y0 + 1.5, w, 0.5, { runs: [head], align: "center" }, { fontSize: 22, bold: true, color: C.text });
    text(s, x + 0.2, y0 + 2.1, w - 0.4, 0.85, { runs: [body], align: "center" }, { fontSize: 16, color: C.text });
    if (i < cols.length - 1) arrow(s, x + w + 0.12, y0 + isz / 2, x + w + gap - 0.12, y0 + isz / 2,
      { color: C.muted, width: 1.5 });
  });
  conclusion(s, "Goal: a risk score from routine slides and spatial data that a pathologist can check.", CONC_TEXT_Y);
  notes(s, [
    "PATTERN: problem → approach → impact. Use it once, early, to frame the whole talk in three steps the " +
    "audience can repeat. Each column answers one question: what is wrong, what we do, what changes.",
    "Design rules shown: three equal columns on one grid; one icon per column, same size (0.9 in) and same " +
    "colour; a small accent tag, a short header (four or five words) and two lines of body text; thin grey " +
    "arrows between the columns; a single take-home line at the bottom.",
    "Icons: lucide/scan-eye, lucide/brain-circuit, lucide/users (ISC).",
  ]);
}

// 6 · Data modalities ---------------------------------------------------------------------------
{
  const s = newSlide(pres, "Data Modalities", ++n);
  pattern(s, "Pattern: data modalities grid");
  const cards = [
    ["bioicons/glass-slide", "H&E whole-slide images", "Scanned at 40×, one per resection", "n = XX slides"],
    ["bioicons/confocal-microscope", "Multiplex imaging", "40-plex protein panel on a subset", "n = XX regions"],
    ["bioicons/single-cell-umap", "Single-cell phenotypes", "Cell types called from the panel", "n = XX cells"],
    ["bioicons/patient", "Clinical and outcome", "Stage, therapy, recurrence-free survival", "n = XX patients"],
  ];
  const gap = 0.3, w = (CW - 3 * gap) / 4, y0 = 1.35, h = 4.1, isz = 1.5;
  cards.forEach(([ic, head, body, num], i) => {
    const x = MX + i * (w + gap);
    rect(s, x, y0, w, h, { fill: C.tint });
    rect(s, x, y0, w, 0.06, { fill: C.accent });
    icon(s, ic, x + (w - isz) / 2, y0 + 0.35, isz);
    text(s, x + 0.2, y0 + 2.05, w - 0.4, 0.7, { runs: [head], align: "center" },
      { fontSize: 18, bold: true, color: C.text, valign: "middle" });
    text(s, x + 0.2, y0 + 2.8, w - 0.4, 0.65, { runs: [body], align: "center" }, { fontSize: 14, color: C.ink });
    text(s, x + 0.2, y0 + 3.5, w - 0.4, 0.4, { runs: [num], align: "center" },
      { fontSize: 16, bold: true, color: C.accent });
  });
  conclusion(s, "Four modalities from the same patients, linked by patient ID; multiplex data exist for a " +
    "subset only.", CONC_TEXT_Y);
  source(s, "Icons: Bioicons — glass slide by Servier Medical Art (CC BY 3.0); confocal microscope by DBCLS " +
    "TogoTV (CC BY 4.0)");
  notes(s, [
    "PATTERN: data modalities grid. Use it before the methods, so the audience knows what goes in and how much " +
    "of each there is. One card per modality; four in a row, or 2 x 2 when each card needs two lines more.",
    "Design rules shown: equal cards on one grid with a thin accent top edge; one illustration per card at the " +
    "same size (1.5 in square box) from one icon source; a header, one line of detail and the count in accent. " +
    "Counts are placeholders (n = XX) here; in a real deck they come from the cohort table and are the same " +
    "numbers as on the cohort slide.",
    "Icons: Bioicons glass-slide (Servier Medical Art, CC BY 3.0) and confocal-microscope (DBCLS TogoTV, CC BY 4.0) " +
    "need attribution, given on the source line and on the credits slide; single-cell-umap (James Lloyd) and " +
    "patient (Marcel Tisch) are CC0.",
  ]);
}

// 7 · Methods flow ------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Methods — Slide to Survival", ++n);
  pattern(s, "Pattern: methods flow");
  const steps = [
    ["Tile", "tabler/grid-scan", "Tissue tiles at 20×; background masked out"],
    ["Embed", "tabler/cube-spark", "Frozen pathology foundation model; one vector per tile"],
    ["Aggregate", "lucide/network", "Attention MIL or cell graph pools tiles per slide"],
    ["Score", "tabler/chart-histogram", "Linear Cox head: one risk score per patient"],
    ["Survival", "lucide/trending-down", "Cox model and KM by median score; 5-fold CV"],
  ];
  const gap = 0.32, w = (CW - 4 * gap) / 5, y0 = 1.3, h = 2.3, hh = 0.42, isz = 0.6;
  steps.forEach(([name, ic, body], i) => {
    const x = MX + i * (w + gap);
    rect(s, x, y0, w, hh, { fill: C.accent });
    text(s, x + 0.12, y0, w - 0.24, hh, `${i + 1} · ${name}`, { fontSize: 14, bold: true, color: C.white, valign: "middle" });
    rect(s, x, y0 + hh, w, h - hh, { fill: C.tint });
    icon(s, ic, x + 0.15, y0 + hh + 0.18, isz, "accent");
    text(s, x + 0.15, y0 + hh + 0.92, w - 0.3, h - hh - 1.0, body, { fontSize: 13, color: C.ink });
    if (i < steps.length - 1) stepArrow(s, x + w + (gap - 0.2) / 2, y0 + h / 2);
  });
  bullets(s, MX, 3.85, CW, 1.9, [
    [b("MIL "), "(multiple-instance learning): the slide label is known, the tile labels are not"],
    [b("Foundation model: "), "pretrained on unlabelled tiles; its weights stay frozen, only later layers train"],
    [b("Folds split by patient, "), "so tiles of one patient are never in both training and test"],
  ], 16);
  conclusion(s, "Tiling and embeddings are fixed before outcomes are seen; only the aggregator and the Cox head " +
    "are trained on survival.", CONC_TEXT_Y);
  abbr(s, [["MIL", "multiple-instance learning"], ["KM", "Kaplan–Meier"], ["CV", "cross-validation"]]);
  notes(s, [
    "PATTERN: methods flow. Use it for a processing pipeline of three to five steps; each card says what is done " +
    "and the key parameter, never a result.",
    "Design rules shown: one row of equal step cards 0.32 in apart with a small grey arrow between them; accent " +
    "header '1 · Step' in 14 pt white bold; tint body in 13 pt near-black; one accent icon per card, same size " +
    "and position (0.6 in, top left of the body); definitions as 14 pt bullets under the row; one take-home line.",
    "Icons: tabler/grid-scan, tabler/cube-spark, lucide/network, tabler/chart-histogram, lucide/trending-down " +
    "(MIT / ISC). Parameters (20×, 5 folds) are illustrative settings, not results.",
  ]);
}

// 8 · Framework diagram -------------------------------------------------------------------------
{
  const s = newSlide(pres, "Framework Overview", ++n);
  pattern(s, "Pattern: framework diagram");
  const rowY = [1.95, 3.35, 4.75];           // centre line of each input row
  const isz = 0.7;
  // Inputs
  [["lucide/microscope", "H&E slides"], ["tabler/stack-2", "Multiplex imaging"],
    ["lucide/clipboard-list", "Clinical data"]].forEach(([ic, lab], i) => {
    icon(s, ic, MX, rowY[i] - isz / 2, isz, "accent");
    text(s, MX + 0.82, rowY[i] - 0.3, 1.3, 0.6, lab, { fontSize: 14, bold: true, color: C.text, valign: "middle" });
  });
  // Processing band
  const bx = 3.25, bw = 6.3, by = 1.2, bh = 4.3;
  rect(s, bx, by, bw, bh, { fill: C.tint });
  text(s, bx + 0.2, by + 0.08, 3, 0.3, "PROCESSING", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
  const box = (x, y, w, h, label) => {
    rect(s, x, y, w, h, { fill: C.white, line: C.rule, lineW: 1 });
    text(s, x + 0.08, y, w - 0.16, h, { runs: [label], align: "center" }, { fontSize: 13, color: C.ink, valign: "middle" });
  };
  const c1 = bx + 0.3, c2 = bx + 2.35, bwid = 1.7, bht = 0.7;
  const fx = bx + 4.45, fw = 1.6, fy = rowY[0] - 0.25, fh = rowY[2] - rowY[0] + 0.5;
  box(c1, rowY[0] - bht / 2, bwid, bht, "Tile + embed");
  box(c2, rowY[0] - bht / 2, bwid, bht, "Attention MIL");
  box(c1, rowY[1] - bht / 2, bwid, bht, "Segment cells");
  box(c2, rowY[1] - bht / 2, bwid, bht, "Cell graph GNN");
  box(c1, rowY[2] - bht / 2, bwid, bht, "Encode covariates");
  rect(s, fx, fy, fw, fh, { fill: C.white, line: C.accent, lineW: 1.25 });
  text(s, fx + 0.1, fy, fw - 0.2, fh, [{ runs: [b("Fusion")], align: "center", after: 4 },
    { runs: ["+ Cox head"], align: "center" }], { fontSize: 14, color: C.ink, valign: "middle" });
  [0, 1].forEach((i) => thinArrow(s, c1 + bwid + 0.04, rowY[i], c2 - 0.04, rowY[i]));
  [0, 1].forEach((i) => thinArrow(s, c2 + bwid + 0.04, rowY[i], fx - 0.04, rowY[i]));
  thinArrow(s, c1 + bwid + 0.04, rowY[2], fx - 0.04, rowY[2]);
  // Input and output arrows: one thick accent arrow each, outside the band.
  rowY.forEach((y) => thickArrow(s, 2.7, y, bx - 0.05, y));
  const outY = [2.65, 4.05];
  outY.forEach((y) => thickArrow(s, bx + bw + 0.05, y, bx + bw + 0.55, y));
  [["tabler/chart-histogram", "Risk score", "per patient"], ["tabler/photo-scan", "Attention maps", "per slide"]]
    .forEach(([ic, lab, sub], i) => {
      const ox = bx + bw + 0.7;
      icon(s, ic, ox, outY[i] - isz / 2, isz, "accent");
      text(s, ox + 0.85, outY[i] - 0.35, SW - MX - ox - 0.85, 0.7,
        [{ runs: [b(lab)] }, { runs: [sub] }], { fontSize: 14, color: C.text, valign: "middle" });
    });
  conclusion(s, "Image, cell-graph and clinical features are fused into one patient-level risk score.");
  abbr(s, [["MIL", "multiple-instance learning"], ["GNN", "graph neural network"]]);
  notes(s, [
    "PATTERN: framework diagram (inputs → processing band → outputs). Use it once as the map of the whole " +
    "analysis; later slides zoom into one part of it.",
    "Design rules shown: the processing layer is a tint band; steps inside it are white boxes joined by thin grey " +
    "arrows; outside the band only thick accent arrows, exactly one per input and one per output; inputs on the " +
    "left, outputs on the right, rows aligned on the same centre lines. Every icon is its own image and every " +
    "label a native text box, so the diagram can be edited in PowerPoint.",
    "Icons: lucide/microscope, tabler/stack-2, lucide/clipboard-list (inputs); tabler/chart-histogram, " +
    "tabler/photo-scan (outputs).",
  ]);
}

// 9 · Agent loop --------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Report-drafting Agent", ++n);
  pattern(s, "Pattern: agent loop");
  const cx = 3.7, cy = 3.35, rx = 2.2, ry = 1.55, isz = 0.65;
  const nodes = [
    ["lucide/list-checks", "1 · Plan", 0, -ry],
    ["lucide/toolbox", "2 · Use tools", rx, 0],
    ["lucide/scan-eye", "3 · Observe", 0, ry],
    ["lucide/message-square-text", "4 · Draft report", -rx, 0],
  ];
  const pos = nodes.map(([, , dx, dy]) => [cx + dx, cy + dy]);
  // Loop arrows between consecutive nodes (thin grey, along the sides of the diamond), kept clear of the
  // icons (centred 0.15 in above each node point) and of the labels below them.
  const loopArrow = (x1, y1, x2, y2) => arrow(s, x1, y1, x2, y2, { color: C.muted, width: 1.5 });
  loopArrow(cx + 0.75, cy - ry + 0.05, cx + rx - 0.2, cy - 0.6);
  loopArrow(cx + rx - 0.2, cy + 0.68, cx + 0.5, cy + ry - 0.45);
  loopArrow(cx - 0.5, cy + ry - 0.45, cx - rx + 0.2, cy + 0.68);
  loopArrow(cx - rx + 0.2, cy - 0.6, cx - 0.75, cy - ry + 0.05);
  nodes.forEach(([ic, lab], i) => {
    const [x, y] = pos[i];
    icon(s, ic, x - isz / 2, y - isz / 2 - 0.15, isz, "accent");
    text(s, x - 0.9, y + 0.22, 1.8, 0.35, { runs: [lab], align: "center" }, { fontSize: 14, bold: true, color: C.text });
  });
  icon(s, "lucide/bot", cx - 0.35, cy - 0.5, 0.7, "grey");
  text(s, cx - 0.8, cy + 0.22, 1.6, 0.35, { runs: ["LLM agent"], align: "center" }, { fontSize: 12, color: C.muted });
  // Tools panel
  const px = 7.4, pw = SW - MX - px;
  text(s, px, 1.3, pw, 0.4, "Tools the agent can call", { fontSize: 18, bold: true, color: C.text });
  hline(s, px, px + pw, 1.78);
  const tools = [
    ["tabler/photo-scan", "VLM slide reader", "Describes a region the model attended to"],
    ["tabler/api", "Feature store", "Returns the patient's risk score and inputs"],
    ["lucide/book-open-text", "Guideline lookup", "Retrieves the reporting criteria text"],
  ];
  tools.forEach(([ic, head, body], i) => {
    const y = 1.98 + i * 0.95;
    icon(s, ic, px, y, 0.55, "grey");
    text(s, px + 0.8, y - 0.05, pw - 0.8, 0.8, [{ runs: [b(head)], after: 2 }, body], { fontSize: 14, color: C.text });
  });
  rect(s, px, 4.9, pw, 0.6, { fill: C.tint });
  text(s, px + 0.2, 4.9, pw - 0.4, 0.6, [{ runs: [b("Stop: "), "draft goes to a pathologist for sign-off"] }],
    { fontSize: 14, color: C.ink, valign: "middle" });
  conclusion(s, "The agent drafts the report; a pathologist signs it off, and every statement points to a tool output.",
    CONC_TEXT_Y);
  abbr(s, [["LLM", "large language model"], ["VLM", "vision-language model"]]);
  notes(s, [
    "PATTERN: agent loop. Use it to explain an LLM / VLM agent: what it plans, which tools it may call, what it " +
    "observes and when it stops. A loop reads as iteration; a straight line would hide that the agent revises.",
    "Design rules shown: four numbered steps on a diamond, one accent icon each (same size, 0.65 in), joined by " +
    "thin grey arrows; the agent itself in the centre in grey; the tool list on the right as icon + bold name + " +
    "one line; the stop condition (human sign-off) in a tint box. All shapes and arrows are native and editable.",
    "Icons: lucide/list-checks, lucide/toolbox, lucide/scan-eye, lucide/message-square-text, lucide/bot, " +
    "lucide/book-open-text (ISC); tabler/photo-scan, tabler/api (MIT).",
  ]);
}

// 10 · Timeline / study design ------------------------------------------------------------------
{
  const s = newSlide(pres, "Study Design — Patient Timeline", ++n);
  pattern(s, "Pattern: timeline");
  const ay = 3.3, x0 = 1.0, x1 = SW - 0.9;
  arrow(s, x0, ay, x1, ay, { color: C.text, width: 2 });
  text(s, x1 - 2.6, ay + 0.12, 2.6, 0.3, { runs: ["Time from diagnosis"], align: "right" },
    { fontSize: 12, italic: true, color: C.muted });
  const ms = [
    ["healthicons/biopsy", "Diagnosis", "t = 0; biopsy confirms cancer", true],
    ["healthicons/tissue", "Surgery", "Tissue scanned and imaged", false],
    ["healthicons/hospital", "Adjuvant therapy", "Chemotherapy or hormone therapy", false],
    ["healthicons/regular-patient", "Follow-up", "Visits until event or last contact", false],
    ["healthicons/chart-line", "Event or censoring", "Recurrence or death", true],
  ];
  // First and last milestone sit 1.4 in inside the margins, so their 2.8 in labels stay within them.
  const xa = MX + 1.4, xb = SW - MX - 1.4, step = (xb - xa) / (ms.length - 1), isz = 0.6, lw = 2.8;
  ms.forEach(([ic, head, body, key], i) => {
    const x = xa + i * step, up = i % 2 === 0;
    const d = 0.26;
    s.addShape("ellipse", { x: x - d / 2, y: ay - d / 2, w: d, h: d,
      fill: { color: key ? C.accent : C.white }, line: { color: key ? C.accent : C.text, width: 1.5 } });
    if (up) {
      line(s, x, ay - 0.75, x, ay - d / 2, C.rule, 1);
      icon(s, ic, x - isz / 2, ay - 1.4, isz, key ? "accent" : "grey");
      text(s, x - lw / 2, ay - 2.2, lw, 0.75, [{ runs: [b(head)], align: "center", after: 2 },
        { runs: [body], align: "center" }], { fontSize: 13, color: C.text, valign: "bottom" });
    } else {
      line(s, x, ay + d / 2, x, ay + 0.75, C.rule, 1);
      icon(s, ic, x - isz / 2, ay + 0.8, isz, key ? "accent" : "grey");
      text(s, x - lw / 2, ay + 1.47, lw, 0.75, [{ runs: [b(head)], align: "center", after: 2 },
        { runs: [body], align: "center" }], { fontSize: 13, color: C.text });
    }
  });
  conclusion(s, "Recurrence-free survival runs from diagnosis to recurrence or death; in GBSG2, 299 of 686 " +
    "patients had an event and the rest were censored at last follow-up.", CONC_TEXT_Y);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); event counts");
  notes(s, [
    "PATTERN: timeline / study design. Use it to define the time axis of a survival analysis (time zero, " +
    "exposure window, event, censoring) or to show project phases. Three to six milestones.",
    "Design rules shown: one horizontal axis with an arrow head; round markers on the axis, filled accent for " +
    "the two that define the endpoint (time zero and event), white with a grey ring for the rest; labels " +
    "alternate above and below so they never collide; one icon per milestone from one icon source, all the same " +
    "size; a thin grey stem joins each marker to its label.",
    "Numbers: 686 patients and 299 recurrence-or-death events from lifelines load_gbsg2; the timeline itself is " +
    "the illustrative study's design, not GBSG2's.",
    "Icons: Health Icons biopsy, tissue, hospital, regular-patient, chart-line (CC0).",
  ]);
}

// 11 · Two-column comparison --------------------------------------------------------------------
{
  const s = newSlide(pres, "Prior Approaches vs This Work", ++n);
  pattern(s, "Pattern: two-column comparison");
  const rows = [
    ["Labels needed", ["no", "Pixel-level annotation"], ["yes", "Slide-level outcome only"]],
    ["Spatial context", ["no", "Tile features averaged"], ["yes", "Cell graph keeps neighbours"]],
    ["Modalities", ["no", "H&E only"], ["yes", "H&E, multiplex and clinical"]],
    ["Validation", ["yes", "Often external cohorts"], ["part", "Internal 5-fold CV so far"]],
    ["Report", ["no", "Written by hand"], ["yes", "Agent drafts, human signs off"]],
  ];
  const xL = MX, wL = 2.6, xA = 3.6, wA = 4.0, xB = 8.3, wB = SW - MX - 8.3, y0 = 1.35, hh = 0.55, rh = 0.72;
  rect(s, xB - 0.15, y0, wB + 0.15, hh + rows.length * rh, { fill: C.tint });
  text(s, xA, y0, wA, hh, "Prior approaches", { fontSize: 18, bold: true, color: C.muted, valign: "middle" });
  text(s, xB + 0.1, y0, wB, hh, "This work", { fontSize: 18, bold: true, color: C.accent, valign: "middle" });
  hline(s, xL, SW - MX, y0 + hh, C.text, 1);
  rows.forEach(([crit, [ka, ta], [kb, tb]], i) => {
    const y = y0 + hh + i * rh;
    text(s, xL, y, wL, rh, crit, { fontSize: 16, bold: true, color: C.text, valign: "middle" });
    mark(s, xA, y + (rh - 0.36) / 2, ka);
    text(s, xA + 0.55, y, wA - 0.55, rh, ta, { fontSize: 16, color: C.ink, valign: "middle" });
    mark(s, xB + 0.1, y + (rh - 0.36) / 2, kb);
    text(s, xB + 0.65, y, wB - 0.7, rh, tb, { fontSize: 16, color: C.ink, valign: "middle" });
    if (i < rows.length - 1) hline(s, xL, SW - MX, y + rh);
  });
  hline(s, xL, SW - MX, y0 + hh + rows.length * rh, C.text, 1);
  conclusion(s, "This work trades external validation for richer inputs; the gap is listed under limitations.",
    CONC_TEXT_Y);
  abbr(s, [["CV", "cross-validation"]]);
  notes(s, [
    "PATTERN: two-column comparison (prior approaches vs this work, or pros vs cons). Use it when the audience " +
    "needs the difference on a few named criteria, not a literature review.",
    "Design rules shown: one row per criterion with the criterion name on the left, so the two columns are read " +
    "across, not down; markers drawn from native shapes (accent check = has it, grey cross = lacks it, grey dash " +
    "= partly) instead of symbol-font glyphs that may be missing on another machine; 'This work' column on a " +
    "tint band with an accent header; rows separated by thin rules. Be honest: show where prior work is better " +
    "(validation here) and say so in the take-home line.",
  ]);
}

// 12 · Limitations ------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Limitations", ++n);
  pattern(s, "Pattern: limitations");
  const items = [
    ["Single-centre cohort", "Other scanners, stains and sites are untested"],
    ["No external validation yet", "Performance is cross-validated on one cohort"],
    ["Multiplex data on a subset (n = XX)", "Fusion model trained on fewer patients"],
    ["Agent reports not yet graded", "Draft accuracy unknown; drafts only"],
  ];
  const y0 = 1.3, rh = 1.0;
  text(s, MX + 1.0, y0, 5.0, 0.35, "LIMITATION", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
  text(s, 6.9, y0, 5.8, 0.35, "WHAT IT AFFECTS", { fontSize: 12, bold: true, color: C.muted, charSpacing: 2 });
  items.forEach(([lim, aff], i) => {
    const y = y0 + 0.45 + i * rh;
    hline(s, MX, SW - MX, y);
    text(s, MX, y, 0.8, rh, String(i + 1), { fontSize: 28, bold: true, color: C.muted, valign: "middle" });
    text(s, MX + 1.0, y, 5.6, rh, lim, { fontSize: 18, bold: true, color: C.text, valign: "middle" });
    text(s, 6.9, y, SW - MX - 6.9, rh, aff, { fontSize: 16, color: C.text, valign: "middle" });
  });
  hline(s, MX, SW - MX, y0 + 0.45 + items.length * rh);
  conclusion(s, "These results are exploratory; an external cohort is needed before any clinical claim.", CONC_TEXT_Y);
  notes(s, [
    "PATTERN: limitations. Use it before the summary, so the take-home messages are heard with their caveats. " +
    "Three or four limitations, each paired with what it affects; a list without consequences reads as ritual.",
    "Design rules shown: calm grey styling (no accent: limitations are not highlights); numbered rows with the " +
    "limitation in bold and its consequence in the right column; thin rules between rows; the take-home line " +
    "names the status of the results (exploratory) and what is needed next.",
  ]);
}

// 13 · Summary ----------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Summary", ++n);
  pattern(s, "Pattern: key takeaways");
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
    if (i) hline(s, MX, SW - MX, y - 0.1);
    text(s, MX, y, 1.0, 1.2, String(i + 1), { fontSize: 44, bold: true, color: C.accent, valign: "top" });
    text(s, MX + 1.1, y + 0.08, CW - 1.1, 0.5, claim, { fontSize: 22, bold: true, color: C.black });
    text(s, MX + 1.1, y + 0.62, CW - 1.1, 0.55, ev, { fontSize: 16, color: C.text });
  });
  abbr(s, [["C-index", "concordance index"], ["CV", "cross-validation"]]);
  notes(s, [
    "PATTERN: key takeaways. Use it as the last content slide: three numbered messages the audience should " +
    "leave with, each backed by one line of evidence from an earlier slide.",
    "Design rules shown: accent numerals (44 pt) as the only colour; each takeaway a short bold claim in black, " +
    "then one grey evidence line; thin rules between rows; no conclusion box, because the takeaways are the " +
    "conclusion. No number may appear here that was not on an earlier result slide, and the wording keeps the " +
    "earlier qualifiers (candidate, exploratory).",
  ]);
}

// 14 · Next steps -------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Next Steps", ++n);
  pattern(s, "Pattern: next steps / roadmap");
  const cards = [
    ["Next 3 months", "lucide/users", "External validation",
      ["Second cohort, other scanner", "Frozen model, no retraining"]],
    ["3–6 months", "lucide/list-checks", "Grade agent reports",
      ["Blinded scoring of n = XX", "Errors logged per tool"]],
    ["6–12 months", "lucide/code", "Release",
      ["Code and model card", "Preprint, no placeholders"]],
  ];
  const gap = 0.45, w = (CW - 2 * gap) / 3, y0 = 1.7, h = 3.5, hh = 0.5, isz = 0.7;
  // Thin time arrow above the cards.
  arrow(s, MX, 1.35, SW - MX, 1.35, { color: C.muted, width: 1.5 });
  cards.forEach(([when, ic, head, lines], i) => {
    const x = MX + i * (w + gap);
    rect(s, x, y0, w, hh, { fill: i === 0 ? C.accent : C.text });
    text(s, x + 0.2, y0, w - 0.4, hh, when, { fontSize: 16, bold: true, color: C.white, valign: "middle" });
    rect(s, x, y0 + hh, w, h - hh, { fill: C.tint });
    icon(s, ic, x + 0.25, y0 + hh + 0.3, isz, i === 0 ? "accent" : "grey");
    text(s, x + 0.25, y0 + hh + 1.15, w - 0.5, 0.45, head, { fontSize: 20, bold: true, color: C.text, valign: "middle" });
    bullets(s, x + 0.25, y0 + hh + 1.8, w - 0.5, h - hh - 1.9, lines, 16);
  });
  conclusion(s, "External validation comes first; its result decides whether the later steps go ahead.", CONC_TEXT_Y);
  notes(s, [
    "PATTERN: next steps / roadmap. Use it at the end of a progress talk: three time-boxed cards, the first one " +
    "highlighted because it is the decision point.",
    "Design rules shown: equal cards on one grid under a thin grey time arrow; a dark header with the timeframe " +
    "(accent only for the first, the current priority); one icon, a short title and two bullets per card; the " +
    "take-home line says what the plan depends on.",
    "Icons: lucide/users, lucide/list-checks, lucide/code (ISC; code is MIT via Feather).",
  ]);
}

// 15 · Thank you --------------------------------------------------------------------------------
{
  const s = pres.addSlide();
  titleFrame(s, 2.3, 1.5);
  pattern(s, "Pattern: questions / thank you");
  text(s, 0.95, 2.3, 11.2, 0.9, "Thank you", { fontSize: 44, bold: true, color: C.text, valign: "top" });
  text(s, 0.95, 3.2, 11.2, 0.55, "Questions and discussion", { fontSize: 24, color: C.muted });
  const cy = 4.45, cx = 0.95;
  icon(s, "lucide/message-square-text", cx, cy, 0.45, "grey");
  text(s, cx + 0.65, cy - 0.05, 6, 0.55, "contact@institution.org", { fontSize: 16, color: C.text, valign: "middle" });
  icon(s, "lucide/code", cx, cy + 0.65, 0.45, "grey");
  text(s, cx + 0.65, cy + 0.6, 6, 0.55, "github.com/<org>/<repo>", { fontSize: 16, color: C.text, valign: "middle" });
  notes(s, [
    "PATTERN: questions / thank you. Use the same frame as the title slide so the talk visibly closes; leave it " +
    "up during questions, with a way to reach the team and the code.",
    "Design rules shown: same logo, accent bar and bottom rule as the title slide; no page number; contact as " +
    "a generic address (a team or lab address, not a person's name); small grey icons in front of each contact line.",
  ]);
}

// 16 · Supplementary (hidden) -------------------------------------------------------------------
{
  const s = newSlide(pres, "Supplementary — Model Settings", ++n);
  s.hidden = true;
  pattern(s, "Pattern: supplementary (hidden)");
  const rows = [
    ["Component", "Setting", "Value", "Fixed before outcomes?"],
    ["Tiling", "Tile size; magnification", "256 × 256 px; 20×", "Yes"],
    ["Tissue mask", "Threshold on saturation", "Otsu", "Yes"],
    ["Foundation model", "Encoder; embedding dimension", "Frozen ViT; XX", "Yes"],
    ["Attention MIL", "Hidden units; dropout", "XX; XX", "Yes"],
    ["Cell graph", "Edges; neighbours per cell", "k-nearest neighbours; k = XX", "Yes"],
    ["Cox head", "Penalty; learning rate; epochs", "L2 XX; XX; XX", "Tuned in inner folds"],
    ["Cross-validation", "Folds; split unit; random_state", "5; patient; 0", "Yes"],
    ["Agent", "Model; temperature; max tool calls", "XX; 0; XX", "Yes"],
  ];
  const colW = [2.4, 3.7, 3.3, 2.7];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.2, colW, 0.46, rows, { fontSize: 13, labelCol: true });
  conclusion(s, "All settings except the Cox penalty were fixed before outcome data were used; random_state is " +
    "recorded in run_meta.json.");
  abbr(s, [["MIL", "multiple-instance learning"], ["ViT", "vision transformer"], ["L2", "ridge penalty"]]);
  notes(s, [
    "PATTERN: supplementary slide, hidden in the slide show (slide.hidden = true, show=\"0\"). Use it for the dense " +
    "settings table you expect a question about; it stays in the file and the PDF but is skipped when presenting.",
    "Design rules shown: same chrome as a main slide (topic title, conclusion, abbreviations); the three-line " +
    "table may be denser (13 pt, nine rows) because it is read on demand; first column bold and left-aligned, " +
    "the others centred. Values marked XX are placeholders; the settings shown are illustrative choices.",
  ]);
}

// 17 · Credits ----------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Credits", ++n);
  pattern(s, "Pattern: credits");
  const rows = [
    ["Source", "Icons used in this deck", "Licence"],
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
  table(s, (SW - w) / 2, 1.25, colW, [0.45, 0.45, 0.72, 0.45, 0.45, 0.45, 0.45], rows, { fontSize: 12 });
  text(s, (SW - w) / 2, 4.95, w, 1.4, [
    { runs: [b("Data: "), "GBSG2 trial counts (686 patients, 299 recurrence-or-death events) via lifelines load_gbsg2."],
      after: 6 },
    { runs: [b("Reference: "), "Lu, Ming Y., et al. ", it("Nature Biomedical Engineering"), " 5.6 (2021): 555–570."],
      after: 6 },
    { runs: ["All other content is an illustrative example; values marked XX are placeholders."] },
  ], { fontSize: 13, color: C.text });
  notes(s, [
    "PATTERN: credits. Use it as the very last slide (after the supplementary slides) whenever the deck uses third-party " +
    "icons, images or data: list every source actually used with its licence, and the author for attribution " +
    "licences (CC BY). CC BY icons are also credited on the slide where they appear.",
    "Design rules shown: one three-line table (source, items, licence), first column left, others centred; data " +
    "and literature sources in plain text below. Authors of icons and references are the only person names in " +
    "the deck besides the presenter placeholder.",
  ]);
}

fs.mkdirSync(OUT, { recursive: true });
pres.writeFile({ fileName: path.join(OUT, "narrative_examples.pptx") }).then((f) => console.log("wrote", f));

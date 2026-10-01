/*
 * Shared theme, geometry and drawing helpers for the example slide decks in examples/slides/.
 *
 * White background, greys and one placeholder accent colour (replace it with your template's main
 * colour), Arial (metric-compatible with Liberation Sans, so LibreOffice previews wrap like
 * PowerPoint). 16:9, 13.333 x 7.5 in.
 * Figures from examples/figures/ are drawn at their on-slide size at 200 dpi and placed 1:1.
 *
 * pptxgenjs is resolved from NODE_PATH or a local node_modules (npm install pptxgenjs).
 */
"use strict";

const fs = require("fs");
const path = require("path");

// ---- Theme ---------------------------------------------------------------------------------------
const C = {
  white: "FFFFFF",
  black: "000000",
  text: "595959",      // titles and body text
  ink: "222222",       // table body, numbers
  muted: "7F7F7F",
  rule: "D9D9D9",
  tint: "F3F3F3",
  accent: "A51C30",    // the one accent colour (placeholder)
  accent2: "C45566",   // accent2-accent4: tints of the accent, not extra colours
  accent3: "DD99A3",
  accent4: "F1D3D8",
  blue: "2A78D6",      // used only where the figures use it (KM upper curve)
};
const FONT = "Arial";
const SERIF = "Times New Roman";

// ---- Geometry (inches) ---------------------------------------------------------------------------
const SW = 13.333, SH = 7.5;
const MX = 0.6;                 // side margin
const CW = SW - 2 * MX;         // content width
const FIG_Y = 1.1;              // top of the figure box (12.1 x 4.6)
const CONC_Y = 5.75;            // conclusion box 5.75-6.80
const CONC_H = 1.05;
const CONC_PT = 18, CONC_INDENT = 22, CONC_AFTER = 10;
const FIG_DPI = 200;
const ROOT = path.join(__dirname, "..");
const FIG = path.join(ROOT, "figures");
const ICONS = path.join(ROOT, "icons");

// ---- Text ----------------------------------------------------------------------------------------
const b = (s) => [s, { bold: true }];
const it = (s) => [s, { italic: true }];

/*
 * Paragraphs -> pptxgenjs runs. A paragraph is a string or {runs, bullet, after, align}; a run is a
 * string or [text, options]. Line spacing is always single and space before 0.
 */
function toRuns(paras, base = {}) {
  if (!Array.isArray(paras)) paras = [paras];
  const out = [];
  paras.forEach((para, i) => {
    if (typeof para === "string") para = { runs: [para] };
    para.runs.forEach((r, j) => {
      const [t, st] = typeof r === "string" ? [r, {}] : r;
      const o = { fontFace: FONT, ...base, ...st };
      if (para.align) o.align = para.align;
      if (para.bullet) o.bullet = { indent: para.bullet === true ? 16 : para.bullet };
      if (para.after !== undefined) o.paraSpaceAfter = para.after;
      if (j === para.runs.length - 1 && i < paras.length - 1) o.breakLine = true;
      out.push({ text: t, options: o });
    });
  });
  return out;
}

function text(slide, x, y, w, h, paras, { valign = "top", align = "left", ...base } = {}) {
  slide.addText(toRuns(paras, base), { x, y, w, h, margin: 0, valign, align, fontFace: FONT, wrap: true });
}

// Grey bullet list; each item is a list of runs. 8 pt after (10 pt for >= 18 pt text).
function bullets(slide, x, y, w, h, items, fontSize = 16) {
  const after = fontSize >= 18 ? 10 : 8;
  text(slide, x, y, w, h, items.map((runs) => ({ runs: Array.isArray(runs) ? runs : [runs], bullet: true, after })),
    { fontSize, color: C.text });
}

// ---- Shapes and images ---------------------------------------------------------------------------
function rect(slide, x, y, w, h, { fill = null, line = null, lineW = 0.75, shape = "rect" } = {}) {
  slide.addShape(shape, {
    x, y, w, h,
    fill: fill ? { color: fill } : { type: "none" },
    line: line ? { color: line, width: lineW } : { type: "none" },
  });
}

function hline(slide, x1, x2, y, color = C.rule, width = 1) {
  slide.addShape("line", { x: x1, y, w: x2 - x1, h: 0, line: { color, width } });
}

function pngSize(file) {
  const buf = fs.readFileSync(file);
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
}

// Send the most recent object to the back, so a title that wraps is never hidden behind a figure.
function sendToBack(slide) {
  const objs = slide._slideObjects;
  const k = slide._backCount || 0;
  objs.splice(k, 0, objs.pop());
  slide._backCount = k + 1;
}

// A figure from examples/figures/ at native size (200 dpi), centred horizontally unless x is given.
function figure(slide, name, y = FIG_Y, x = null) {
  const file = path.join(FIG, name);
  const [pw, ph] = pngSize(file);
  const w = pw / FIG_DPI, h = ph / FIG_DPI;
  const fx = x === null ? (SW - w) / 2 : x;
  slide.addImage({ path: file, x: fx, y, w, h });
  sendToBack(slide);
  return { x: fx, y, w, h };
}

// A figure scaled to fit a box, keeping its aspect ratio (only for thumbnails, never for result figures).
function fitImage(slide, name, x, y, w, h) {
  const file = path.join(FIG, name);
  const [pw, ph] = pngSize(file);
  const s = Math.min(w / pw, h / ph);
  slide.addImage({ path: file, x: x + (w - pw * s) / 2, y: y + (h - ph * s) / 2, w: pw * s, h: ph * s });
}

/*
 * An icon from examples/icons/png/: ``name`` is "<source>/<icon>" (e.g. "healthicons/microscope"),
 * ``variant`` "grey" (text colour) or "accent". PNGs are rendered from the SVGs at 512 px because
 * LibreOffice < 7.4 does not draw SVG images embedded by pptxgenjs. Square box of side ``size``.
 */
function icon(slide, name, x, y, size, variant = "grey") {
  const file = path.join(ICONS, "png", `${name}${variant === "accent" ? "_accent" : ""}.png`);
  slide.addImage({ path: file, x, y, w: size, h: size });
}

/*
 * Native three-line table: rule above the header, under the header and under the last row; first
 * column left-aligned, all other columns centred (header included). ``rowH`` is a number or a list.
 */
function table(slide, x, y, colW, rowH, rows, { fontSize = 12, labelCol = false } = {}) {
  const none = { type: "none" };
  const outer = { type: "solid", pt: 1.5, color: C.text };
  const mid = { type: "solid", pt: 0.75, color: C.text };
  const last = rows.length - 1;
  const data = rows.map((row, i) => row.map((val, j) => {
    const base = i === 0 ? { fontSize, bold: true, color: C.text } : { fontSize, color: C.ink, bold: labelCol && j === 0 };
    const top = i === 0 ? outer : i === 1 ? mid : none;
    const bottom = i === last ? outer : i === 0 ? mid : none;
    return {
      text: toRuns(val, base),
      options: { align: j === 0 ? "left" : "center", valign: "middle", margin: [0.04, 0.1, 0.04, 0.1],
                 border: [top, none, bottom, none] },
    };
  }));
  const h = Array.isArray(rowH) ? rowH.reduce((a, c) => a + c, 0) : rowH * rows.length;
  slide.addTable(data, { x, y, w: colW.reduce((a, c) => a + c, 0), colW, h, rowH, fontFace: FONT, autoPage: false });
}

// ---- Slide chrome --------------------------------------------------------------------------------
// Topic title top left (28 pt bold grey), a neutral logo placeholder top right, page number bottom right.
function newSlide(pres, title, n, { logo = true } = {}) {
  const s = pres.addSlide();
  s.background = { color: C.white };
  if (logo) text(s, SW - 2.35, 0.2, 2.0, 0.35, "YOUR LOGO", { fontSize: 11, bold: true, color: C.rule, align: "right" });
  if (title) text(s, 0.59, 0.36, 9.6, 0.6, title, { fontSize: 28, bold: true, color: C.text });
  if (n !== null && n !== undefined) text(s, SW - 0.97, 7.0, 0.6, 0.3, String(n), { fontSize: 12, color: C.text, align: "right" });
  return s;
}

// The slide's one finding: 18 pt bold black; a list of items becomes bullets with a 22 pt hanging indent.
function conclusion(slide, s, y = CONC_Y) {
  const paras = Array.isArray(s)
    ? s.map((item) => ({ runs: typeof item === "string" ? [item] : item, bullet: CONC_INDENT, after: CONC_AFTER }))
    : s;
  text(slide, MX + 0.1, y, CW - 0.2, CONC_H, paras, { fontSize: CONC_PT, bold: true, color: C.black });
}

// Data source / citation at bottom right, 9 pt serif.
function source(slide, s) {
  text(slide, 0.6, 6.82, SW - 0.6 - 1.05, 0.6, { runs: [s], align: "right" },
    { valign: "bottom", fontSize: 9, color: C.ink, fontFace: SERIF });
}

// Grey tag for slides whose numbers are not yet confirmed.
function draft(slide) {
  rect(slide, SW - 2.65, 0.66, 2.35, 0.32, { fill: C.tint, line: C.rule });
  text(slide, SW - 2.65, 0.66, 2.35, 0.32, "DRAFT – to be confirmed",
    { valign: "middle", align: "center", fontSize: 12, bold: true, color: C.muted });
}

// "ABBR: expansion; ABBR: expansion." in the order given.
function abbreviations(slide, x, y, w, h, entries, fontSize = 9.5) {
  const runs = entries.flatMap(([a, e], i) => [...(i ? [" "] : []), b(`${a}: `), `${e}${i < entries.length - 1 ? ";" : "."}`]);
  text(slide, x, y, w, h, { runs }, { fontSize, color: C.muted });
}

// ---- Gallery helpers -----------------------------------------------------------------------------
// Small grey italic label naming the slide pattern, top right under the logo placeholder.
function pattern(slide, s) {
  text(slide, SW - 3.75, 0.62, 3.4, 0.3, s, { fontSize: 12, italic: true, color: C.muted, align: "right" });
}

// A straight line between two points (pptxgenjs lines run top-left -> bottom-right unless flipped).
function line(slide, x1, y1, x2, y2, color = C.accent, width = 0.75) {
  slide.addShape("line", {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: (x2 < x1) !== (y2 < y1), line: { color, width },
  });
}

// Semi-transparent accent box for progressive emphasis or a callout highlight.
function emphasis(slide, x, y, w, h) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.accent, transparency: 88 }, line: { color: C.accent, width: 1 } });
}

// A new 16:9 presentation with the theme fonts.
function newDeck(title) {
  const pptxgen = require("pptxgenjs");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = title;
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  return pres;
}

module.exports = {
  C, FONT, SERIF, SW, SH, MX, CW, FIG_Y, CONC_Y, CONC_H, CONC_PT, CONC_INDENT, CONC_AFTER, FIG_DPI, FIG, ICONS,
  b, it, toRuns, text, bullets, rect, hline, pngSize, sendToBack, figure, fitImage, icon, table,
  newSlide, conclusion, source, draft, abbreviations, pattern, line, emphasis, newDeck,
};

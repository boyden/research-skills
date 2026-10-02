/*
 * Slide primitives of the results-deck engine: theme, geometry, text, shapes, figures, icons, tables,
 * slide chrome, citations and diagram helpers. Deck builders and engine/js/build.js import from here.
 *
 * Every color, font, font size and layout box comes from the current theme (theme.json, SPEC §5);
 * nothing is hard-coded in the drawing helpers. Until configure({theme}) is called the theme is
 * engine/themes/neutral: white background, grays and one placeholder accent color, Arial
 * (metric-compatible with Liberation Sans, so LibreOffice previews wrap like PowerPoint), 16:9,
 * 13.333 x 7.5 in. Figures are drawn at their on-slide size at the theme dpi and placed 1:1.
 *
 * configure({figDir, iconDir, refs, theme}) sets where figure() / fitImage() / icon() look, the reference
 * registry cite() uses and the theme; build.js calls it once per deck before any builder runs.
 * T (theme without geometry) and G (geometry + slideW / slideH / contentW) are live read-only views;
 * the v1 flat constants (C, FONT, SW, MX, ...) are live getters derived from the same theme.
 * pptxgenjs is resolved from NODE_PATH or a local node_modules (npm install pptxgenjs).
 */
"use strict";

const fs = require("fs");
const path = require("path");

// ---- Theme ---------------------------------------------------------------------------------------
const NEUTRAL_DIR = path.join(__dirname, "..", "themes", "neutral");
const NEUTRAL = JSON.parse(fs.readFileSync(path.join(NEUTRAL_DIR, "theme.json"), "utf8"));

const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);

// Deep merge: objects merge key by key, arrays and scalars (null included) replace. Returns a fresh copy.
function deepMerge(base, over) {
  const out = JSON.parse(JSON.stringify(base));
  if (!isObj(over)) return out;
  for (const [k, v] of Object.entries(over)) {
    if (v === undefined) continue;
    out[k] = isObj(v) && isObj(out[k]) ? deepMerge(out[k], v) : JSON.parse(JSON.stringify(v));
  }
  return out;
}

function deepFreeze(o) {
  if (o && typeof o === "object") {
    Object.values(o).forEach(deepFreeze);
    Object.freeze(o);
  }
  return o;
}

let TH;        // current merged theme (frozen), without _dir
let GEO;       // geometry + slideW / slideH / contentW (frozen)
let THEME_DIR; // absolute theme directory; asset paths resolve against it

function setTheme(theme, dir) {
  const { _dir, ...rest } = isObj(theme) ? theme : {};
  TH = deepFreeze(deepMerge(NEUTRAL, rest));
  THEME_DIR = _dir ? path.resolve(_dir) : dir;
  const slideW = TH.slide.w, slideH = TH.slide.h;
  GEO = deepFreeze({ ...JSON.parse(JSON.stringify(TH.geometry)), slideW, slideH,
                     contentW: slideW - 2 * TH.geometry.margin });
}
setTheme(NEUTRAL, NEUTRAL_DIR);

// Read-only view of whatever object get() returns right now (so it follows configure()).
function liveView(get) {
  return new Proxy({}, {
    get: (_, k) => get()[k],
    has: (_, k) => k in get(),
    ownKeys: () => Reflect.ownKeys(get()),
    getOwnPropertyDescriptor: (_, k) => (k in get()
      ? { value: get()[k], writable: false, enumerable: true, configurable: true } : undefined),
    set: () => { throw new TypeError("primitives: T / G are read-only; pass a theme to configure()"); },
    defineProperty: () => { throw new TypeError("primitives: T / G are read-only"); },
    deleteProperty: () => { throw new TypeError("primitives: T / G are read-only"); },
  });
}
const T = liveView(() => { const { geometry, ...rest } = TH; return rest; });
const G = liveView(() => GEO);

// Absolute path of a theme asset (theme.asset.*), or null when the theme has none.
function assetPath(key) {
  const rel = TH.asset && TH.asset[key];
  return rel ? path.resolve(THEME_DIR || process.cwd(), rel) : null;
}

// v1 color names, read live from the theme. accent2-accent4 are tints of the accent, not extra colors;
// white is the slide background; blue is used only where the figures use it (KM upper curve).
const C = {};
for (const [name, get] of Object.entries({
  white: () => TH.color.background,
  black: () => TH.color.black,
  text: () => TH.color.text,          // titles and body text
  ink: () => TH.color.ink,            // table body, numbers
  muted: () => TH.color.muted,
  rule: () => TH.color.rule,
  tint: () => TH.color.tint,
  accent: () => TH.color.accent,      // the one accent color
  accent2: () => TH.color.accentTints[0],
  accent3: () => TH.color.accentTints[1],
  accent4: () => TH.color.accentTints[2],
  blue: () => TH.color.blue,
})) Object.defineProperty(C, name, { enumerable: true, get });
Object.freeze(C);

// ---- Configuration -------------------------------------------------------------------------------
// research-skills root, resolved from this file (skills/results-deck/engine/js/).
const RS_ROOT = path.join(__dirname, "..", "..", "..", "..");
const DEFAULTS = {
  figDir: path.join(RS_ROOT, "examples", "figures"),
  iconDir: path.join(RS_ROOT, "examples", "icons"),
};
const cfg = { figDir: DEFAULTS.figDir, iconDir: DEFAULTS.iconDir, refs: {} };

/*
 * Set the figure and icon directories, the reference registry and the theme. Keys left out keep their
 * current value; figDir / iconDir null restore the defaults (research-skills/examples/figures, .../icons).
 * ``refs[key] = [author, journal, rest, isOrg?]``. ``theme`` is a parsed theme.json object (missing keys
 * fall back to themes/neutral, deep merge) with an optional ``_dir`` (absolute theme directory, used to
 * resolve asset paths); null restores the neutral theme.
 */
function configure({ figDir, iconDir, refs, theme } = {}) {
  if (figDir !== undefined) cfg.figDir = figDir === null ? DEFAULTS.figDir : path.resolve(figDir);
  if (iconDir !== undefined) cfg.iconDir = iconDir === null ? DEFAULTS.iconDir : path.resolve(iconDir);
  if (refs !== undefined) cfg.refs = refs || {};
  if (theme !== undefined) {
    if (theme === null) setTheme(NEUTRAL, NEUTRAL_DIR);
    else setTheme(theme, undefined);
  }
}

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
      const o = { fontFace: TH.font.body, ...base, ...st };
      if (para.align) o.align = para.align;
      if (para.bullet) o.bullet = { indent: para.bullet === true ? GEO.bullet.indent : para.bullet };
      if (para.after !== undefined) o.paraSpaceAfter = para.after;
      if (j === para.runs.length - 1 && i < paras.length - 1) o.breakLine = true;
      out.push({ text: t, options: o });
    });
  });
  return out;
}

function text(slide, x, y, w, h, paras, { valign = "top", align = "left", ...base } = {}) {
  slide.addText(toRuns(paras, base), { x, y, w, h, margin: 0, valign, align, fontFace: TH.font.body, wrap: true });
}

// Gray bullet list; each item is a list of runs. Space after from the theme (geometry.bullet: 8 pt,
// 10 pt for text of at least largeFrom = 18 pt in the neutral theme).
function bullets(slide, x, y, w, h, items, fontSize = TH.size.body) {
  const bl = GEO.bullet;
  const after = fontSize >= bl.largeFrom ? bl.afterLarge : bl.after;
  text(slide, x, y, w, h, items.map((runs) => ({ runs: Array.isArray(runs) ? runs : [runs], bullet: true, after })),
    { fontSize, color: C.text });
}

// ---- Shapes and images ---------------------------------------------------------------------------
function rect(slide, x, y, w, h, { fill = null, line = null, lineW = GEO.stroke.line, shape = "rect" } = {}) {
  slide.addShape(shape, {
    x, y, w, h,
    fill: fill ? { color: fill } : { type: "none" },
    line: line ? { color: line, width: lineW } : { type: "none" },
  });
}

function hline(slide, x1, x2, y, color = C.rule, width = GEO.stroke.rule) {
  slide.addShape("line", { x: x1, y, w: x2 - x1, h: 0, line: { color, width } });
}

// A straight line between two points (pptxgenjs lines run top-left -> bottom-right unless flipped).
function line(slide, x1, y1, x2, y2, color = C.accent, width = GEO.stroke.line) {
  slide.addShape("line", {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: (x2 < x1) !== (y2 < y1), line: { color, width },
  });
}

// Arrow from (x1, y1) to (x2, y2) with the head at (x2, y2). pptx lines run from their top-left (or, flipped,
// top-right) corner, so the head goes on the line's end when the arrow points down or level, else on its start.
function arrow(slide, x1, y1, x2, y2, { color = C.muted, width = GEO.stroke.arrowThin, head = "triangle" } = {}) {
  const headAtEnd = y2 >= y1;
  slide.addShape("line", {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: (x2 < x1) !== (y2 < y1),
    line: { color, width, ...(headAtEnd ? { endArrowType: head } : { beginArrowType: head }) },
  });
}
// The two arrow weights of a framework diagram: thin gray inside a processing band, thick accent outside.
const thinArrow = (slide, x1, y1, x2, y2) => arrow(slide, x1, y1, x2, y2, { color: C.muted, width: GEO.stroke.arrowThin });
const thickArrow = (slide, x1, y1, x2, y2) => arrow(slide, x1, y1, x2, y2, { color: C.accent, width: GEO.stroke.arrowThick });

// Small filled right-pointing arrow between step cards (methods-flow pattern), centered on yMid.
function stepArrow(slide, x, yMid, w = GEO.stepArrow[0], h = GEO.stepArrow[1]) {
  slide.addShape("rightArrow", { x, y: yMid - h / 2, w, h, fill: { color: C.muted }, line: { type: "none" } });
}

// Circle marker with a check (accent), a cross (gray) or a dash (partial, gray), drawn from native lines.
function mark(slide, x, y, kind, d = GEO.mark) {
  const col = kind === "yes" ? C.accent : C.muted;
  const glyph = GEO.stroke.markGlyph;
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: C.white }, line: { color: col, width: GEO.stroke.mark } });
  const cx = x + d / 2, cy = y + d / 2, r = d * 0.22;
  if (kind === "yes") {
    line(slide, cx - r, cy, cx - r * 0.25, cy + r * 0.75, col, glyph);
    line(slide, cx - r * 0.25, cy + r * 0.75, cx + r * 1.05, cy - r * 0.8, col, glyph);
  } else if (kind === "no") {
    line(slide, cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8, col, glyph);
    line(slide, cx - r * 0.8, cy + r * 0.8, cx + r * 0.8, cy - r * 0.8, col, glyph);
  } else {
    line(slide, cx - r, cy, cx + r, cy, col, glyph);
  }
}

// Semi-transparent accent box for progressive emphasis or a callout highlight.
function emphasis(slide, x, y, w, h) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.accent, transparency: TH.color.emphasisTransparency },
                           line: { color: C.accent, width: GEO.stroke.emphasis } });
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

// A figure from the figure directory at native size (pixels / theme dpi), centered horizontally unless x is given.
function figure(slide, name, y = GEO.figureTop, x = null) {
  const file = path.join(cfg.figDir, name);
  const [pw, ph] = pngSize(file);
  const w = pw / TH.dpi, h = ph / TH.dpi;
  const fx = x === null ? (GEO.slideW - w) / 2 : x;
  slide.addImage({ path: file, x: fx, y, w, h });
  sendToBack(slide);
  return { x: fx, y, w, h };
}

// A figure scaled to fit a box, keeping its aspect ratio (only for thumbnails, never for result figures).
function fitImage(slide, name, x, y, w, h) {
  const file = path.join(cfg.figDir, name);
  const [pw, ph] = pngSize(file);
  const s = Math.min(w / pw, h / ph);
  slide.addImage({ path: file, x: x + (w - pw * s) / 2, y: y + (h - ph * s) / 2, w: pw * s, h: ph * s });
}

/*
 * An icon from <iconDir>/png/: ``name`` is "<source>/<icon>" (e.g. "healthicons/microscope"),
 * ``variant`` "grey" (text color) or "accent". PNGs are rendered from the SVGs at 512 px because
 * LibreOffice < 7.4 does not draw SVG images embedded by pptxgenjs. Square box of side ``size``.
 * A copy rendered in the theme's colors (<theme dir>/icons/png/<name>[_accent].png, written by
 * tools/theme_icons.py) is used when it exists; otherwise the <iconDir>/png/ file.
 */
function icon(slide, name, x, y, size, variant = "grey") {
  const rel = `${name}${variant === "accent" ? "_accent" : ""}.png`;
  const themed = THEME_DIR ? path.join(THEME_DIR, "icons", "png", rel) : null;
  const file = themed && fs.existsSync(themed) ? themed : path.join(cfg.iconDir, "png", rel);
  slide.addImage({ path: file, x, y, w: size, h: size });
}

/*
 * Native three-line table: rule above the header, under the header and under the last row; first
 * column left-aligned, all other columns centered (header included). ``rowH`` is a number or a list.
 */
function table(slide, x, y, colW, rowH, rows, { fontSize = TH.size.table, labelCol = false } = {}) {
  const none = { type: "none" };
  const outer = { type: "solid", pt: GEO.stroke.tableOuter, color: C.text };
  const mid = { type: "solid", pt: GEO.stroke.tableInner, color: C.text };
  const last = rows.length - 1;
  const cellMargin = GEO.tableCellMargin;
  const data = rows.map((row, i) => row.map((val, j) => {
    const base = i === 0 ? { fontSize, bold: true, color: C.text } : { fontSize, color: C.ink, bold: labelCol && j === 0 };
    const top = i === 0 ? outer : i === 1 ? mid : none;
    const bottom = i === last ? outer : i === 0 ? mid : none;
    return {
      text: toRuns(val, base),
      options: { align: j === 0 ? "left" : "center", valign: "middle", margin: [...cellMargin],
                 border: [top, none, bottom, none] },
    };
  }));
  const h = Array.isArray(rowH) ? rowH.reduce((a, c) => a + c, 0) : rowH * rows.length;
  slide.addTable(data, { x, y, w: colW.reduce((a, c) => a + c, 0), colW, h, rowH, fontFace: TH.font.body, autoPage: false });
}

// ---- Deck and slide chrome -----------------------------------------------------------------------
// A new presentation with the theme's slide size and fonts (LAYOUT_WIDE for 13.333 x 7.5).
function newDeck(title) {
  const pptxgen = require("pptxgenjs");
  const pres = new pptxgen();
  const { w, h } = TH.slide;
  if (w === 13.333 && h === 7.5) {
    pres.layout = "LAYOUT_WIDE";
  } else {
    pres.defineLayout({ name: "THEME", width: w, height: h });
    pres.layout = "THEME";
  }
  pres.title = title;
  pres.theme = { headFontFace: TH.font.display, bodyFontFace: TH.font.body };
  return pres;
}

let pageLog = [];

// Logo in a box: the theme's image asset when it has one, else the gray "YOUR LOGO" placeholder text.
function drawLogo(slide, assetKey, [x, y, w, h], align) {
  const file = assetPath(assetKey);
  if (file) slide.addImage({ path: file, x, y, w, h });
  else text(slide, x, y, w, h, "YOUR LOGO", { fontSize: TH.size.logo, bold: true, color: C.rule, ...(align ? { align } : {}) });
}

/*
 * Topic title top left (theme title size, bold, text color), the logo top right, page number bottom right.
 * ``logo: false`` drops the logo; ``chrome: false`` draws none of the three (title-type slides), but the
 * title is still logged. Every slide is logged as {page: n, title} for build.js (see takePageLog).
 */
function newSlide(pres, title, n, { logo = true, chrome = true } = {}) {
  const s = pres.addSlide();
  s.background = { color: TH.color.background };
  pageLog.push({ page: n, title });
  if (!chrome) return s;
  const g = GEO;
  if (logo) drawLogo(s, "logo", g.logo, "right");
  if (title) text(s, ...g.title, title, { fontSize: TH.size.title, bold: true, color: C.text, fontFace: TH.font.display });
  if (n !== null && n !== undefined) text(s, ...g.page, String(n), { fontSize: TH.size.page, color: C.text, align: "right" });
  return s;
}

// Return the slides logged by newSlide since the last call, in call order, and clear the log.
function takePageLog() {
  const out = pageLog;
  pageLog = [];
  return out;
}

// Title-slide frame (also for the closing slide): logo top left, accent bar left of the title band
// (from barY, height barH; defaults from geometry.titleSlide.accentBar), full-width accent rule at the
// bottom. Use on a {chrome: false} slide.
function titleFrame(slide, barY, barH) {
  const ts = GEO.titleSlide;
  const [bx, by, bw, bh] = ts.accentBar;
  slide.background = { color: TH.color.background };
  drawLogo(slide, "titleLogo", ts.logo, null);
  rect(slide, bx, barY === undefined ? by : barY, bw, barH === undefined ? bh : barH, { fill: C.accent });
  rect(slide, ...ts.accentRule, { fill: C.accent });
}

// The slide's one finding: bold black at the theme conclusion size; a list of items becomes bullets
// with the theme's hanging indent.
function conclusion(slide, s, y = GEO.conclusion.yFigure) {
  const cc = GEO.conclusion;
  const paras = Array.isArray(s)
    ? s.map((item) => ({ runs: typeof item === "string" ? [item] : item, bullet: cc.indent, after: cc.after }))
    : s;
  text(slide, GEO.margin + 0.1, y, GEO.contentW - 0.2, cc.h, paras, { fontSize: TH.size.conclusion, bold: true, color: C.black });
}

// Data source at bottom right, theme source size, serif.
function source(slide, s) {
  text(slide, ...GEO.source, { runs: [s], align: "right" },
    { valign: "bottom", fontSize: TH.size.source, color: C.ink, fontFace: TH.font.serif });
}

// Citation from runs (e.g. with an italic journal run) in the source position: source size, serif, bottom right.
function citeRuns(slide, runs) {
  const [x, y, w, h] = GEO.source;
  slide.addText(toRuns({ runs, align: "right" }, { fontSize: TH.size.source, color: C.ink, fontFace: TH.font.serif }),
    { x, y, w, h, margin: 0, valign: "bottom", fontFace: TH.font.serif, wrap: true });
}

/*
 * Runs for registered references: "Author, et al. *Journal* rest" (organization authors without
 * "et al."). ``refs`` is a key, or a list of keys and [prefix, key] pairs, joined by "; ".
 */
function refRuns(refs) {
  const list = Array.isArray(refs) ? refs : [refs];
  return list.flatMap((item, i) => {
    const [prefix, key] = Array.isArray(item) ? item : ["", item];
    const ref = cfg.refs[key];
    if (!ref) throw new Error(`cite: unknown reference key "${key}" (pass it via configure({refs}))`);
    const [author, journal, rest, isOrg] = ref;
    return [...(i ? ["; "] : []), ...(prefix ? [prefix] : []), `${author}${isOrg ? "" : ", et al."} `,
      it(journal), ...(rest ? [` ${rest}`] : [])];
  });
}

// Literature citation from the reference registry in the source position (see refRuns).
function cite(slide, refs) {
  citeRuns(slide, refRuns(refs));
}

// Gray tag for slides whose numbers are not yet confirmed.
function draft(slide) {
  const box = GEO.draft;
  rect(slide, ...box, { fill: C.tint, line: C.rule });
  text(slide, ...box, "DRAFT – to be confirmed",
    { valign: "middle", align: "center", fontSize: TH.size.draft, bold: true, color: C.muted });
}

/*
 * "ABBR: expansion; ABBR: expansion." in the order given, bottom left and bottom-aligned so it sits on
 * the source line (box geometry.abbr); w / x / y / h / fontSize / valign move it elsewhere.
 */
function abbr(slide, entries, w = GEO.abbr[2],
              { x = GEO.abbr[0], y = GEO.abbr[1], h = GEO.abbr[3], fontSize = TH.size.abbr, valign = "bottom" } = {}) {
  const runs = entries.flatMap(([a, e], i) => [...(i ? [" "] : []), b(`${a}: `), `${e}${i < entries.length - 1 ? ";" : "."}`]);
  slide.addText(toRuns({ runs }, { fontSize, color: C.muted }),
    { x, y, w, h, margin: 0, valign, align: "left", fontFace: TH.font.body, wrap: true });
}

// Older positional form of abbr() with an explicit box (top-aligned).
function abbreviations(slide, x, y, w, h, entries, fontSize = TH.size.abbr) {
  abbr(slide, entries, w, { x, y, h, fontSize, valign: "top" });
}

// ---- Gallery helpers -----------------------------------------------------------------------------
// Small gray italic label naming the slide pattern, top right under the logo (box geometry.pattern).
function pattern(slide, s, y = GEO.pattern[1]) {
  const [x, , w, h] = GEO.pattern;
  text(slide, x, y, w, h, s, { fontSize: TH.size.pattern, italic: true, color: C.muted, align: "right" });
}

module.exports = {
  configure, b, it, toRuns, text, bullets, rect, hline, line, arrow, thinArrow, thickArrow, stepArrow, mark,
  emphasis, pngSize, sendToBack, figure, fitImage, icon, table, newDeck, newSlide, takePageLog, titleFrame,
  conclusion, source, citeRuns, refRuns, cite, draft, abbr, abbreviations, pattern,
};
// Live, read-only values: the configured directories and everything derived from the current theme.
for (const [name, get] of Object.entries({
  FIG: () => cfg.figDir,
  ICONS: () => cfg.iconDir,
  T: () => T,
  G: () => G,
  C: () => C,
  FONT: () => TH.font.body,
  SERIF: () => TH.font.serif,
  SW: () => GEO.slideW,
  SH: () => GEO.slideH,
  MX: () => GEO.margin,
  CW: () => GEO.contentW,
  FIG_Y: () => GEO.figureTop,
  CONC_Y: () => GEO.conclusion.yFigure,
  CONC_H: () => GEO.conclusion.h,
  CONC_TEXT_Y: () => GEO.conclusion.yText,
  CONC_PT: () => TH.size.conclusion,
  CONC_INDENT: () => GEO.conclusion.indent,
  CONC_AFTER: () => GEO.conclusion.after,
  FIG_DPI: () => TH.dpi,
})) Object.defineProperty(module.exports, name, { enumerable: true, get });

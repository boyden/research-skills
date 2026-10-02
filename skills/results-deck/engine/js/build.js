#!/usr/bin/env node
/*
 * Build a results deck (SPEC v2): <deck>/slides/<key>.js -> <outDir>/<name>_wip.pptx (+ .pages.json, .pdf).
 *
 *   node engine/js/build.js <deck dir> [--list] [--list-sections]
 *                                      [--only k1,k2 | --sections a,b] [--out f.pptx] [--png]
 *                                      [--release] [--pdf | --no-pdf]
 *
 * The interface (deck directory, deck.config.js, page files, theme, pages.json, notes/<key>.md) is fixed in
 * engine/SPEC.md. This file collects and orders the page files, builds them and writes the pptx and its
 * side files.
 *
 * Pages: one file per page, slides/<key>.js (not recursive; files starting with "_" and slides/_lib/ are
 * shared helpers, not pages). key = file name without .js, matching ^[A-Za-z][A-Za-z0-9_]*$. A page file
 * exports {section, order, build(pres, n, P, ctx)}: `section` is one of deck.config.js `sections` (a list
 * of section keys), `order` a number, unique within its section. Pages are sorted by section (config order),
 * then by order. All problems are reported at once, exit status 2. Each build() makes exactly one slide
 * with P.newSlide(); P is the engine's primitives.js and ctx = {key, section, config, theme, deckDir}.
 * Page files and slides/_lib/*.js may require("results-deck") (and "pptxgenjs" / "jszip"): this file maps
 * those ids to the engine's primitives.js (the same object as P) and the pptxgenjs it found, so a deck
 * copied anywhere needs no relative path back to the engine.
 *
 * Theme: <deck>/<config.theme || "theme">/theme.json, else engine/themes/neutral/theme.json (WARNING); its
 * directory is set as theme._dir and the object is handed to P.configure({figDir, iconDir, refs, theme}).
 *
 * Outputs (all next to each other in <outDir>, relative to the deck dir):
 * - default: the working copy <name>_wip.pptx, replaced on every build. It is written to a temp file and
 *   renamed at the end, so a failed build keeps the previous working copy.
 * - --release: <name>_v<N>.pptx, N = highest existing version + 1; versions are never overwritten.
 * - the default and the --release build hold <outDir>/.build.lock (created exclusively, "pid\nISO time");
 *   a lock whose pid is alive stops the build with exit status 3, a lock whose pid is gone is taken over
 *   with a WARNING. The lock is removed at the end, also when the build fails.
 * - --only k1,k2 / --sections a,b: only those pages, in deck order, into --out (required; never the wip or a
 *   release name; no lock). The footer and pages.json carry each page's number in the FULL deck, computed
 *   from the section/order of all page files without building the others. No PDF unless --pdf / --png.
 * - every build writes <out stem>.pages.json: [{page, title, section, order, builder}, ...] (builder = key);
 *   repeated titles (e.g. progressive emphasis) are allowed and only warned about.
 * - --png: also the PDF, rendered to <out stem>_png/<page:02d>-<key>.png (pdftoppm, 60 dpi); the directory
 *   is replaced on every build.
 *
 * Speaker notes: <deck>/notes/<key>.md (plain UTF-8 text, one paragraph per line) replaces the notes of
 * that page; pages without one keep their addNotes() text. After writing, the notes are split into one
 * <a:p> per line so PowerPoint (and tools/pull_notes.py) see the speaker's paragraphs.
 *
 * Supplementary: the slides of the section named by `supplementary` are hidden (show="0").
 *
 * PDF: the wip and release builds also write <stem>.pdf with LibreOffice. It is converted from a copy of
 * the pptx without the show="0" flags (LibreOffice < 7.4 skips hidden slides), so the PDF has one page per
 * pages.json entry, using a per-run soffice profile so parallel builds do not collide. soffice is looked
 * up in $DECK_SOFFICE, then PATH, /usr/bin/soffice, /opt/libreoffice*\/program/soffice. A missing soffice or
 * a failed conversion only prints a WARNING: the pptx is kept, the old PDF untouched, exit status 0.
 *
 * Lint: a 6-digit hex color literal or a font name literal in a page file is a WARNING (use P.T / P.G).
 *
 * pptxgenjs is resolved from NODE_PATH, then <deck>/node_modules, then <research-skills>/node_modules.
 * The last stdout line is always the pptx path. Exit status: 0 ok, 1 build failure, 2 invalid deck or
 * arguments, 3 another full build holds the lock.
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const Module = require("module");
const { spawnSync } = require("child_process");

const ENGINE_JS = __dirname;
const PRIMITIVES = path.join(ENGINE_JS, "primitives.js");
const NEUTRAL_THEME = path.join(ENGINE_JS, "..", "themes", "neutral", "theme.json");
const RS_ROOT = path.join(ENGINE_JS, "..", "..", "..", "..");
const KEY_RE = /^[A-Za-z][A-Za-z0-9_]*$/;

const USAGE = `usage: node engine/js/build.js <deck dir> [--list] [--list-sections]
                                   [--only k1,k2 | --sections a,b] [--out f.pptx] [--png]
                                   [--release] [--pdf | --no-pdf]

  (default)        full deck: working copy <outDir>/<name>_wip.pptx + .pages.json + .pdf, replaced on every
                   build; holds <outDir>/.build.lock (exit 3 while another full build runs)
  --release        full deck: kept version <outDir>/<name>_v<N>.pptx (N = highest existing + 1) + .pages.json
                   + .pdf; holds the lock too
  --only k1,k2     only these page keys, in deck order; needs --out; footers carry the full-deck page numbers
  --sections a,b   only these sections, in deck order; needs --out; footers carry the full-deck page numbers
  --out f.pptx     output file (relative to the current directory; replaced if it exists); not the wip or a
                   release name; no lock; no PDF by default
  --png            also the PDF, and one PNG per page in <out stem>_png/<page:02d>-<key>.png (pdftoppm)
  --pdf / --no-pdf force / skip the PDF (LibreOffice soffice; $DECK_SOFFICE overrides the lookup)
  --list           print the deck order (page, section, order, key); build nothing
  --list-sections  print each section key, its page count and keys; build nothing

Pages: slides/<key>.js exporting {section, order, build(pres, n, P, ctx)} (engine/SPEC.md §3).
pptxgenjs: NODE_PATH, <deck>/node_modules or <research-skills>/node_modules (npm install pptxgenjs).
The last stdout line is the pptx path. Exit status: 1 build failure, 2 invalid deck/arguments, 3 locked.`;

function fail(msg, code = 1) {
  console.error(`ERROR: ${msg}`);
  process.exit(code);
}

// ---- Arguments -----------------------------------------------------------------------------------
function parseArgs(argv) {
  const opts = {
    deck: null, list: false, listSections: false, only: null, sections: null, out: null,
    png: false, release: false, pdf: null,
  };
  const keyList = (v) => v.split(",").map((k) => k.trim()).filter(Boolean);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const value = () => {
      const v = argv[++i];
      if (v === undefined || v.startsWith("--")) fail(`${a} needs a value`, 2);
      return v;
    };
    if (a === "-h" || a === "--help") { console.log(USAGE); process.exit(0); }
    else if (a === "--list") opts.list = true;
    else if (a === "--list-sections") opts.listSections = true;
    else if (a === "--only") opts.only = keyList(value());
    else if (a === "--sections") opts.sections = keyList(value());
    else if (a === "--out") opts.out = value();
    else if (a === "--png") opts.png = true;
    else if (a === "--release") opts.release = true;
    else if (a === "--pdf" || a === "--no-pdf") {
      if (opts.pdf !== null && opts.pdf !== (a === "--pdf")) fail("--pdf and --no-pdf cannot be combined", 2);
      opts.pdf = a === "--pdf";
    } else if (a.startsWith("--")) fail(`unknown option ${a}\n\n${USAGE}`, 2);
    else if (opts.deck === null) opts.deck = a;
    else fail(`unexpected argument ${a}\n\n${USAGE}`, 2);
  }
  if (opts.deck === null) fail(`no deck directory given\n\n${USAGE}`, 2);
  if (opts.only && opts.sections) fail("--only and --sections cannot be combined", 2);
  if ((opts.only && !opts.only.length) || (opts.sections && !opts.sections.length)) fail("--only / --sections need at least one key", 2);
  if (opts.release && (opts.out || opts.only || opts.sections)) fail("--release cannot be combined with --out, --only or --sections", 2);
  if ((opts.only || opts.sections) && !opts.out) {
    fail(`${opts.only ? "--only" : "--sections"} needs --out <file.pptx> (in your scratchpad): ` +
      "a partial build never writes the working copy or a release", 2);
  }
  if (opts.png && opts.pdf === false) fail("--png needs the PDF; it cannot be combined with --no-pdf", 2);
  return opts;
}

// ---- Module resolution ---------------------------------------------------------------------------
// Directory of an installed package `name`: NODE_PATH, <deck>/node_modules, <research-skills>/node_modules,
// then Node's normal lookup from this file. null when not found.
function findPackage(name, deckDir) {
  const dirs = [
    ...(process.env.NODE_PATH || "").split(path.delimiter).filter(Boolean),
    path.join(deckDir, "node_modules"),
    path.join(RS_ROOT, "node_modules"),
  ];
  for (const d of dirs) {
    const p = path.resolve(d, name);
    if (fs.existsSync(path.join(p, "package.json"))) return p;
  }
  try { return path.dirname(require.resolve(`${name}/package.json`)); } catch (e) { return null; }
}

/*
 * Map the ids "results-deck" (engine primitives), "pptxgenjs" and "jszip" to fixed files for every
 * require() in this process, so the page files, slides/_lib, primitives.js and this file share one
 * primitives instance (the page log, the theme) and one pptxgenjs, wherever the deck lives.
 */
function installAliases(deckDir) {
  const aliases = { "results-deck": PRIMITIVES };
  const pptx = findPackage("pptxgenjs", deckDir);
  if (pptx) {
    aliases.pptxgenjs = require.resolve(pptx);
    try { aliases.jszip = require.resolve("jszip", { paths: [pptx] }); } catch (e) { /* resolved lazily below */ }
  }
  if (!aliases.jszip) {
    const jz = findPackage("jszip", deckDir);
    if (jz) aliases.jszip = require.resolve(jz);
  }
  const orig = Module._resolveFilename;
  Module._resolveFilename = function (request, ...rest) {
    if (Object.prototype.hasOwnProperty.call(aliases, request)) return aliases[request];
    return orig.call(this, request, ...rest);
  };
  return aliases;
}

function requirePptxgen(aliases) {
  if (!aliases.pptxgenjs || !aliases.jszip) {
    fail("pptxgenjs not found (looked in NODE_PATH, <deck>/node_modules, <research-skills>/node_modules).\n" +
      "Install it next to the deck:  cd <deck dir> && npm install pptxgenjs\n" +
      "or point NODE_PATH at a node_modules that has it:  NODE_PATH=/path/to/node_modules node engine/js/build.js <deck>");
  }
}

// ---- Deck config ---------------------------------------------------------------------------------
function loadConfig(deckDir) {
  const file = path.join(deckDir, "deck.config.js");
  if (!fs.existsSync(file)) fail(`${file} not found (copy engine/template/ to start a deck)`, 2);
  let raw;
  try { raw = require(file); } catch (e) { fail(`deck.config.js cannot be loaded: ${e.stack || e}`, 2); }
  const problems = [];
  if (!raw.name || typeof raw.name !== "string") problems.push("`name` (output file prefix) is missing");
  if (!Array.isArray(raw.sections) || !raw.sections.length) {
    problems.push("`sections` must be a non-empty list of section keys (SPEC §2.1)");
  } else {
    const seen = new Set();
    const show = (v) => JSON.stringify(v, (k, x) => (typeof x === "function" ? `<function ${x.name}>` : x)) || String(v);
    let v1 = false;
    raw.sections.forEach((entry, i) => {
      if (typeof entry !== "string" || !entry) {
        v1 = v1 || Array.isArray(entry);
        problems.push(`sections[${i}] must be a section key string (SPEC §2.1), got ${show(entry)}`);
        return;
      }
      if (seen.has(entry)) problems.push(`section key "${entry}" is listed twice`);
      seen.add(entry);
    });
    if (v1) {
      problems.push("this is the v1 form [key, [builders]]: in v2 `sections` only lists the section keys, e.g. " +
        "[\"title\", \"results\"], and every page file slides/<key>.js declares its own section and order (SPEC §2.1, §3)");
    }
  }
  if (problems.length) fail(`deck.config.js (${file}):\n  - ${problems.join("\n  - ")}`, 2);
  if (raw.notes !== undefined) {
    console.warn("WARNING: deck.config.js `notes` is ignored: v2 reads the speaker notes from notes/<key>.md (SPEC §8.3)");
  }
  const supp = raw.supplementary === undefined ? "supplementary" : raw.supplementary;
  if (supp && !raw.sections.includes(supp)) console.warn(`WARNING: supplementary section "${supp}" is not in sections; no slide is hidden`);
  return {
    raw,
    name: raw.name,
    title: raw.title || raw.name,
    outDir: path.resolve(deckDir, raw.outDir || "output"),
    figDir: path.resolve(deckDir, raw.figDir || "figures"),
    iconDir: raw.iconDir ? path.resolve(deckDir, raw.iconDir) : null,
    themeDir: path.resolve(deckDir, raw.theme || "theme"),
    supplementary: supp || null,
    refs: raw.refs || {},
    sections: raw.sections,
  };
}

// ---- Theme ---------------------------------------------------------------------------------------
// The deck's theme.json, else the engine's neutral one (WARNING), else null (WARNING). Sets theme._dir.
function loadTheme(cfg) {
  const read = (file) => {
    try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch (e) { fail(`${file}: ${e.message}`, 2); }
  };
  const own = path.join(cfg.themeDir, "theme.json");
  let file = null;
  if (fs.existsSync(own)) file = own;
  else if (fs.existsSync(NEUTRAL_THEME)) {
    console.warn(`WARNING: ${own} not found; using the engine's default theme ${path.resolve(NEUTRAL_THEME)}`);
    file = NEUTRAL_THEME;
  } else {
    console.warn(`WARNING: neither ${own} nor ${path.resolve(NEUTRAL_THEME)} exists; primitives keep their built-in style`);
    return null;
  }
  const theme = read(file);
  if (theme === null || typeof theme !== "object" || Array.isArray(theme)) fail(`${file}: not a JSON object`, 2);
  theme._dir = path.dirname(path.resolve(file));
  return theme;
}

// ---- Page files ----------------------------------------------------------------------------------
/*
 * Load slides/*.js. Returns {pages, problems}: pages = [{key, file, section, order, build, index, page}] in
 * deck order with their full-deck page numbers, holding only the pages without problems; problems =
 * [{keys, msg}] (keys = the page keys a problem concerns).
 */
function collectPages(deckDir, cfg) {
  const dir = path.join(deckDir, "slides");
  const problems = [];
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    return { pages: [], problems: [{ keys: [], msg: `${dir} not found (one page file slides/<key>.js per page, SPEC §3)` }] };
  }
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".js") && !f.startsWith("_")).sort();
  const loaded = [];
  for (const f of files) {
    const key = f.slice(0, -3);
    const rel = path.join("slides", f);
    let section = null; // known once the module is loaded; lets a partial build tell its own problems apart
    const bad = (msg) => problems.push({ keys: [key], section, msg: `${rel}: ${msg}` });
    if (!KEY_RE.test(key)) { bad(`key "${key}" must match ${KEY_RE.source} (the key is the file name)`); continue; }
    if (!fs.statSync(path.join(dir, f)).isFile()) continue;
    let mod;
    try { mod = require(path.join(dir, f)); } catch (e) {
      bad(`cannot be loaded: ${String(e && e.stack || e).split("\n").slice(0, 4).join(" | ")}`);
      continue;
    }
    if (mod === null || typeof mod !== "object") { bad("must export {section, order, build}"); continue; }
    if (typeof mod.section === "string") section = mod.section;
    const before = problems.length;
    if (mod.build === undefined && mod.section === undefined && Object.values(mod).some((v) => typeof v === "function")) {
      bad(`exports builder function(s) (${Object.keys(mod).join(", ")}) but no {section, order, build}: v1 page module? ` +
        "v2 is one page per file exporting {section, order, build(pres, n, P, ctx)} (SPEC §3)");
      continue;
    }
    if (typeof mod.section !== "string") bad(`\`section\` must be a string, got ${JSON.stringify(mod.section)}`);
    else if (!cfg.sections.includes(mod.section)) bad(`section "${mod.section}" is not in deck.config.js sections (${cfg.sections.join(", ")})`);
    if (typeof mod.order !== "number" || !Number.isFinite(mod.order)) bad(`\`order\` must be a number, got ${JSON.stringify(mod.order)}`);
    if (typeof mod.build !== "function") bad("`build` must be a function build(pres, n, P, ctx)");
    if (problems.length === before) loaded.push({ key, file: path.join(dir, f), section: mod.section, order: mod.order, build: mod.build });
  }
  // Unique (section, order): report every clash with all its files; clashing pages are dropped.
  const groups = {};
  loaded.forEach((p) => { (groups[`${p.section}\u0000${p.order}`] = groups[`${p.section}\u0000${p.order}`] || []).push(p); });
  const clashing = new Set();
  for (const ps of Object.values(groups).filter((g) => g.length > 1)) {
    problems.push({
      keys: ps.map((p) => p.key),
      section: ps[0].section,
      msg: `section "${ps[0].section}" order ${ps[0].order} is used by ${ps.length} pages: ` +
        `${ps.map((p) => path.join("slides", `${p.key}.js`)).join(", ")} (change one order, e.g. to a free value in between)`,
    });
    ps.forEach((p) => clashing.add(p.key));
  }
  const pages = loaded.filter((p) => !clashing.has(p.key));
  const sIdx = (s) => cfg.sections.indexOf(s);
  pages.sort((a, b) => sIdx(a.section) - sIdx(b.section) || a.order - b.order);
  pages.forEach((p, i) => { p.index = i; p.page = i + 1; });
  return { pages, problems };
}

function reportProblems(problems, header) {
  console.error(`ERROR: ${header} (${problems.length} problem${problems.length === 1 ? "" : "s"}):`);
  problems.forEach((p) => console.error(`  - ${p.msg}`));
}

// WARNING for hard-coded colors and font names in page files (they belong in the theme: P.T / P.G).
const FONT_NAMES = [
  "Arial", "Arial Narrow", "Arial Black", "Helvetica", "Helvetica Neue", "Calibri", "Calibri Light", "Cambria",
  "Aptos", "Aptos Display", "Times New Roman", "Times", "Georgia", "Garamond", "Palatino", "Verdana", "Tahoma",
  "Trebuchet MS", "Segoe UI", "Century Gothic", "Gill Sans", "Futura", "Franklin Gothic", "Courier New", "Consolas",
  "Menlo", "DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono", "Liberation Sans", "Liberation Serif", "Roboto",
  "Open Sans", "Lato", "Inter", "Source Sans Pro", "Noto Sans", "Noto Serif", "Noto Sans CJK SC", "Microsoft YaHei",
  "SimSun", "SimHei", "PingFang SC",
].map((s) => s.toLowerCase());

function lintPages(pages) {
  const lit = /(["'`])([^"'`\n]{1,40})\1/g;
  const warnings = [];
  for (const p of pages) {
    const lines = fs.readFileSync(p.file, "utf8").split(/\r?\n/);
    lines.forEach((line, i) => {
      if (/^\s*(\/\/|\/?\*)/.test(line)) return; // comment lines
      let m;
      lit.lastIndex = 0;
      while ((m = lit.exec(line)) !== null) {
        const v = m[2].trim();
        if (/^#?[0-9A-Fa-f]{6}$/.test(v)) warnings.push(`slides/${p.key}.js:${i + 1}: color literal "${v}" (use P.T.color.*)`);
        else if (FONT_NAMES.includes(v.toLowerCase())) warnings.push(`slides/${p.key}.js:${i + 1}: font name "${v}" (use P.T.font.*)`);
      }
    });
  }
  if (warnings.length) {
    console.warn(`WARNING: hard-coded style in page files (take colors and fonts from the theme, SPEC §3):\n  ${warnings.join("\n  ")}`);
  }
}

function listPages(pages, cfg) {
  console.log("page\tsection\torder\tkey");
  pages.forEach((p) => console.log(`${p.page}\t${p.section}\t${p.order}\t${p.key}${p.section === cfg.supplementary ? "\t(hidden)" : ""}`));
}

function listSections(pages, cfg) {
  for (const key of cfg.sections) {
    const keys = pages.filter((p) => p.section === key).map((p) => p.key);
    console.log(`${key}\t${keys.length}\t${keys.join(", ")}${key === cfg.supplementary ? "\t(hidden)" : ""}`);
  }
  console.log(`total\t${pages.length}`);
}

// ---- Notes ---------------------------------------------------------------------------------------
// notes/<key>.md -> text (BOM and trailing whitespace dropped), or null when there is none.
function readNote(notesDir, key) {
  const file = path.join(notesDir, `${key}.md`);
  if (!fs.existsSync(file)) return null;
  return fs.readFileSync(file, "utf8").replace(/^﻿/, "").replace(/\s+$/, "");
}

function warnStaleNotes(deckDir, notesDir, allKeys) {
  if (fs.existsSync(path.join(deckDir, "notes.json"))) {
    console.warn("WARNING: notes.json is not read: v2 takes the speaker notes from notes/<key>.md, one file per page (SPEC §8.3)");
  }
  if (!fs.existsSync(notesDir)) return;
  const stale = fs.readdirSync(notesDir).filter((f) => f.endsWith(".md") && !f.startsWith("_"))
    .map((f) => f.slice(0, -3)).filter((k) => !allKeys.has(k));
  if (stale.length) console.warn(`WARNING: notes/<key>.md with no page file: ${stale.map((k) => `notes/${k}.md`).join(", ")}`);
}

// pptxgenjs keeps every addNotes() call as a "notes" object and concatenates them when writing, so replacing
// means dropping the existing notes objects first.
function replaceNotes(slide, text) {
  slide._slideObjects = slide._slideObjects.filter((o) => o._type !== "notes");
  if (text) slide.addNotes(text);
}

// pptxgenjs writes the whole notes text as ONE paragraph with the line breaks inside the run. Split it into one
// <a:p> per line (empty lines become empty paragraphs).
async function splitNotesParagraphs(pptx) {
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(pptx));
  const para = /<a:p><a:r><a:rPr lang="en-US" dirty="0"\/><a:t>([\s\S]*?)<\/a:t><\/a:r><a:endParaRPr lang="en-US" dirty="0"\/><\/a:p>/;
  let changed = 0;
  for (const name of Object.keys(zip.files).filter((f) => /^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(f))) {
    const xml = await zip.file(name).async("string");
    const out = xml.replace(para, (all, body) => {
      if (!/[\r\n]/.test(body)) return all;
      return body.split(/\r\n|\r|\n/).map((ln) => (ln
        ? `<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>${ln}</a:t></a:r></a:p>`
        : `<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>`)).join("");
    });
    if (out !== xml) { zip.file(name, out); changed++; }
  }
  if (changed) fs.writeFileSync(pptx, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

// ---- Output names --------------------------------------------------------------------------------
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function nextVersion(cfg) {
  const re = new RegExp(`^${escapeRe(cfg.name)}_v(\\d+)\\.pptx$`);
  const taken = fs.existsSync(cfg.outDir) ? fs.readdirSync(cfg.outDir).map((f) => f.match(re)).filter(Boolean) : [];
  const n = taken.reduce((m, x) => Math.max(m, Number(x[1])), 0) + 1;
  return path.join(cfg.outDir, `${cfg.name}_v${n}.pptx`);
}

// True for <outDir>/<name>_wip.pptx and <outDir>/<name>_v<N>.pptx.
function isReservedName(cfg, file) {
  if (path.dirname(file) !== cfg.outDir) return false;
  const re = new RegExp(`^${escapeRe(cfg.name)}_(wip|v\\d+)\\.pptx$`);
  return re.test(path.basename(file));
}

// ---- Full-build lock -----------------------------------------------------------------------------
let heldLock = null;

function releaseLock() {
  if (!heldLock) return;
  try { fs.rmSync(heldLock, { force: true }); } catch (e) { /* best effort */ }
  heldLock = null;
}

function pidAlive(pid) {
  try { process.kill(pid, 0); return true; } catch (e) { return e.code === "EPERM"; }
}

// Create <outDir>/.build.lock exclusively. A live holder -> exit 3; a dead (or unreadable, older than 10 s)
// holder -> WARNING and take the lock over.
function acquireLock(outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const lock = path.join(outDir, ".build.lock");
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const fd = fs.openSync(lock, "wx");
      fs.writeSync(fd, `${process.pid}\n${new Date().toISOString()}\n`);
      fs.closeSync(fd);
      heldLock = lock;
      return;
    } catch (e) {
      if (e.code !== "EEXIST") fail(`cannot create ${lock}: ${e.message}`);
    }
    let content = "", age = 0;
    try { content = fs.readFileSync(lock, "utf8"); age = Date.now() - fs.statSync(lock).mtimeMs; } catch (e) { continue; } // vanished: retry
    const [pidLine, since] = content.split("\n");
    const pid = /^\d+$/.test((pidLine || "").trim()) ? Number(pidLine.trim()) : null;
    if (pid !== null ? pidAlive(pid) : age < 10000) {
      console.error(`ERROR: another full build is running (pid ${pid === null ? "?" : pid}, since ${since || "?"}; lock ${lock}).\n` +
        "Wait for it to finish, or use a partial build: --only <keys> --out <scratchpad>/x.pptx");
      process.exit(3);
    }
    console.warn(`WARNING: stale build lock ${lock} (pid ${pid === null ? "?" : pid} is not running, since ${since || "?"}); taking it over`);
    try { fs.rmSync(lock, { force: true }); } catch (e) { /* retry below */ }
  }
  console.error(`ERROR: could not take ${lock} (another build keeps creating it)`);
  process.exit(3);
}

// ---- PDF -----------------------------------------------------------------------------------------
function findExe(name, envVar, extra = []) {
  const isExe = (p) => { try { fs.accessSync(p, fs.constants.X_OK); return fs.statSync(p).isFile(); } catch (e) { return false; } };
  if (envVar && process.env[envVar]) return isExe(process.env[envVar]) ? process.env[envVar] : null;
  const cands = (process.env.PATH || "").split(path.delimiter).filter(Boolean).map((d) => path.join(d, name));
  cands.push(...extra);
  return cands.find(isExe) || null;
}

function findSoffice() {
  const extra = ["/usr/bin/soffice"];
  try {
    fs.readdirSync("/opt").filter((d) => d.startsWith("libreoffice")).sort().reverse()
      .forEach((d) => extra.push(path.join("/opt", d, "program", "soffice")));
  } catch (e) { /* no /opt */ }
  return findExe("soffice", "DECK_SOFFICE", extra);
}

// pptx -> <same stem>.pdf next to it. Never throws: returns the PDF path or null (with a WARNING).
async function makePdf(pptx, noOverwrite) {
  const t0 = Date.now();
  const stem = path.basename(pptx, ".pptx");
  const pdf = path.join(path.dirname(pptx), `${stem}.pdf`);
  if (noOverwrite && fs.existsSync(pdf)) {
    console.warn(`WARNING: ${pdf} already exists; not overwriting, no PDF written`);
    return null;
  }
  const soffice = findSoffice();
  if (!soffice) {
    console.warn(`WARNING: soffice not found ($DECK_SOFFICE, PATH, /usr/bin, /opt/libreoffice*); no PDF written, ${pdf} left as it was`);
    return null;
  }
  let work = null, profile = null;
  try {
    work = fs.mkdtempSync(path.join(path.dirname(pptx), `.${stem}.pdfbuild-`));
    profile = fs.mkdtempSync(path.join(os.tmpdir(), "soffice_profile_"));
    const JSZip = require("jszip");
    const zip = await JSZip.loadAsync(fs.readFileSync(pptx));
    for (const name of Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f))) {
      const xml = await zip.file(name).async("string");
      const shown = xml.replace(/(<p:sld\b[^>]*?) show="0"/, "$1");
      if (shown !== xml) zip.file(name, shown);
    }
    const src = path.join(work, `${stem}.src.pptx`);
    fs.writeFileSync(src, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
    // The theme's fonts (or a metric-compatible substitute) keep the PDF line breaks as in PowerPoint.
    const SUBSTITUTES = { "arial": /liberation sans/i, "helvetica": /liberation sans|nimbus sans/i,
      "times new roman": /liberation serif/i, "courier new": /liberation mono/i };
    const font = require(PRIMITIVES).T.font || {};
    for (const face of [...new Set([font.display, font.body, font.serif].filter(Boolean))]) {
      const fc = spawnSync("fc-match", [face], { encoding: "utf8" });
      if (fc.error) break;   // no fontconfig: nothing to check
      const got = String(fc.stdout).trim();
      const ok = got.toLowerCase().includes(`"${face.toLowerCase()}"`) || (SUBSTITUTES[face.toLowerCase()] || /$^/).test(got);
      if (!ok) console.warn(`WARNING: theme font "${face}" is not installed (fc-match: ${got}); PDF line breaks may differ from PowerPoint`);
    }
    const r = spawnSync(soffice, [`-env:UserInstallation=file://${profile}`, "--headless", "--convert-to", "pdf", "--outdir", work, src],
      { stdio: ["ignore", "ignore", "pipe"], timeout: 15 * 60 * 1000 });
    const made = path.join(work, `${stem}.src.pdf`);
    if (r.error || r.status !== 0 || !fs.existsSync(made) || fs.statSync(made).size === 0) {
      const why = r.error ? r.error.message
        : `exit ${r.status}${r.signal ? ` signal ${r.signal}` : ""} ${String(r.stderr || "").trim().split("\n").pop()}`;
      console.warn(`WARNING: PDF conversion failed (${why}); pptx kept, ${pdf} left as it was`);
      return null;
    }
    fs.renameSync(made, pdf);
    console.log(`PDF ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    return pdf;
  } catch (err) {
    console.warn(`WARNING: PDF conversion failed (${err.message}); pptx kept, ${pdf} left as it was`);
    return null;
  } finally {
    if (work) fs.rmSync(work, { recursive: true, force: true });
    if (profile) fs.rmSync(profile, { recursive: true, force: true });
  }
}

// PDF -> <pptx stem>_png/<page:02d>-<key>.png, one per pages.json row (PDF page i = rows[i]). The directory
// is replaced as a whole. Never throws: returns the directory or null (with a WARNING).
function makePngs(pdf, pptx, rows) {
  const dir = path.join(path.dirname(pptx), `${path.basename(pptx, ".pptx")}_png`);
  const pdftoppm = findExe("pdftoppm", null, ["/usr/bin/pdftoppm"]);
  if (!pdftoppm) { console.warn("WARNING: pdftoppm (poppler-utils) not found; no PNGs written"); return null; }
  let work = null;
  try {
    work = fs.mkdtempSync(path.join(path.dirname(pptx), `.${path.basename(pptx, ".pptx")}.pngbuild-`));
    const r = spawnSync(pdftoppm, ["-r", "60", "-png", pdf, path.join(work, "p")], { stdio: ["ignore", "ignore", "pipe"] });
    if (r.error || r.status !== 0) {
      console.warn(`WARNING: pdftoppm failed (${r.error ? r.error.message : String(r.stderr || "").trim()}); no PNGs written`);
      return null;
    }
    const made = fs.readdirSync(work).map((f) => [f, f.match(/^p-(\d+)\.png$/)]).filter(([, m]) => m)
      .sort((a, b) => Number(a[1][1]) - Number(b[1][1])).map(([f]) => f);
    if (made.length !== rows.length) {
      console.warn(`WARNING: the PDF has ${made.length} page(s) but the deck ${rows.length}; PNGs are named by PDF page order`);
    }
    made.forEach((f, i) => {
      const name = i < rows.length ? `${String(rows[i].page).padStart(2, "0")}-${rows[i].builder}.png` : `extra-${i + 1}.png`;
      fs.renameSync(path.join(work, f), path.join(work, name));
    });
    fs.rmSync(dir, { recursive: true, force: true });
    fs.renameSync(work, dir);
    work = null;
    return dir;
  } catch (err) {
    console.warn(`WARNING: PNG rendering failed (${err.message}); ${dir} left as it was`);
    return null;
  } finally {
    if (work) fs.rmSync(work, { recursive: true, force: true });
  }
}

// ---- Main ----------------------------------------------------------------------------------------
async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const deckDir = path.resolve(opts.deck);
  if (!fs.existsSync(deckDir) || !fs.statSync(deckDir).isDirectory()) fail(`${deckDir} is not a directory`, 2);
  const aliases = installAliases(deckDir);
  const P = require("results-deck");
  const cfg = loadConfig(deckDir);
  const { pages: allPages, problems } = collectPages(deckDir, cfg);
  const partial = Boolean(opts.only || opts.sections);

  // Which pages. A full build (and --list) needs a clean deck; a partial build only needs its own pages to be
  // clean, so another page being edited does not block it (its page numbers may then be off).
  let pages = allPages;
  if (opts.only) {
    const known = new Set([...allPages.map((p) => p.key), ...problems.flatMap((p) => p.keys)]);
    const unknown = opts.only.filter((k) => !known.has(k));
    if (unknown.length) {
      problems.push({ keys: unknown, msg: `--only: no page file slides/<key>.js for ${unknown.join(", ")}`, fatal: true });
    }
    pages = allPages.filter((p) => opts.only.includes(p.key)); // deck order, whatever the order given
  } else if (opts.sections) {
    const unknown = opts.sections.filter((k) => !cfg.sections.includes(k));
    if (unknown.length) {
      problems.push({ keys: [], msg: `--sections: unknown section(s) ${unknown.join(", ")}; sections: ${cfg.sections.join(", ")}`, fatal: true });
    }
    pages = allPages.filter((p) => opts.sections.includes(p.section));
  }
  if (problems.length) {
    // A problem blocks a partial build when it concerns one of the selected keys or sections (or no page).
    const own = (p) => p.fatal || !p.keys.length ||
      (opts.only ? p.keys.some((k) => opts.only.includes(k)) : opts.sections.includes(p.section));
    const blocking = partial ? problems.filter(own) : problems;
    if (blocking.length) { reportProblems(problems, `invalid deck ${deckDir}`); process.exit(2); }
    console.warn(`WARNING: other page files have problems (not built here; page numbers may be off):\n  ` +
      problems.map((p) => p.msg).join("\n  "));
  }
  if (!pages.length && !opts.list && !opts.listSections) fail("no pages to build", 2);

  if (opts.list || opts.listSections) {
    if (opts.list) listPages(allPages, cfg);
    if (opts.listSections) listSections(allPages, cfg);
    return;
  }
  lintPages(pages);

  // Where they go.
  const wip = path.join(cfg.outDir, `${cfg.name}_wip.pptx`);
  let out = null;
  if (opts.out) {
    out = path.resolve(opts.out);
    if (path.extname(out).toLowerCase() !== ".pptx") fail(`--out must end in .pptx: ${out}`, 2);
    if (isReservedName(cfg, out)) fail(`--out must not be the working copy or a release name (${path.basename(out)}); choose another file`, 2);
  }
  const wantPdf = opts.png || (opts.pdf !== null ? opts.pdf : !opts.out);
  requirePptxgen(aliases);
  if (partial) console.log(`partial build: ${pages.length} of ${allPages.length} pages; page numbers are the full deck's`);

  const theme = loadTheme(cfg);
  P.configure({ figDir: cfg.figDir, iconDir: cfg.iconDir, refs: cfg.refs, theme });
  const notesDir = path.join(deckDir, "notes");
  warnStaleNotes(deckDir, notesDir, new Set(allPages.map((p) => p.key)));

  if (!opts.out) {
    acquireLock(cfg.outDir); // full builds only; released on exit, also on failure
    out = opts.release ? nextVersion(cfg) : wip;
  }
  const tmp = path.join(path.dirname(out), `.${path.basename(out, ".pptx")}.building-${process.pid}.pptx`);
  try {
    const pres = P.newDeck(cfg.title);
    const rows = [];
    const slideProblems = [];
    let notesApplied = 0;
    P.takePageLog();
    for (const pg of pages) {
      const before = pres.slides.length;
      const ctx = { key: pg.key, section: pg.section, config: cfg.raw, theme, deckDir };
      try {
        pg.build(pres, pg.page, P, ctx);
      } catch (err) {
        err.message = `page ${pg.key} (slides/${pg.key}.js): ${err.message}`;
        throw err;
      }
      const logged = P.takePageLog();
      const added = pres.slides.length - before;
      if (added !== 1 || logged.length !== 1) {
        slideProblems.push({ keys: [pg.key], msg: `slides/${pg.key}.js made ${added} slide(s) with ${logged.length} newSlide() call(s); ` +
          "a page file makes exactly one slide with P.newSlide() (shared layouts go into slides/_lib/, SPEC §3)" });
        continue;
      }
      // `?? null` keeps the title key in pages.json when a page passes no title (JSON drops undefined).
      rows.push({ page: pg.page, title: logged[0].title ?? null, section: pg.section, order: pg.order, builder: pg.key });
      const slide = pres.slides[pres.slides.length - 1];
      const note = readNote(notesDir, pg.key);
      if (note !== null) { replaceNotes(slide, note); notesApplied++; }
      if (cfg.supplementary && pg.section === cfg.supplementary) slide.hidden = true;
    }
    if (slideProblems.length) {
      reportProblems(slideProblems, `invalid deck ${deckDir}; nothing written`);
      process.exit(2);
    }
    console.log(`notes: ${notesApplied} slide(s) from notes/<key>.md, ${rows.length - notesApplied} from addNotes()`);

    const byTitle = {};
    rows.forEach((r) => { (byTitle[r.title] = byTitle[r.title] || []).push(r.builder); });
    const dup = Object.entries(byTitle).filter(([, ks]) => ks.length > 1);
    if (dup.length) {
      console.warn("WARNING: repeated page titles (allowed; pull_notes needs aliases for them): " +
        dup.map(([t, ks]) => `"${t}" (${ks.join(", ")})`).join("; "));
    }

    fs.mkdirSync(path.dirname(out), { recursive: true });
    await pres.writeFile({ fileName: tmp });
    await splitNotesParagraphs(tmp);
    fs.renameSync(tmp, out);
    const pagesJson = path.join(path.dirname(out), `${path.basename(out, ".pptx")}.pages.json`);
    fs.writeFileSync(pagesJson, `[${rows.map((r) => JSON.stringify(r)).join(",\n ")}]\n`); // one page per line
    const hidden = rows.filter((r) => r.section === cfg.supplementary).length;
    console.log(`${rows.length} pages${hidden ? ` (${hidden} hidden, section ${cfg.supplementary})` : ""}; ${pagesJson}`);
    if (wantPdf) {
      const pdf = await makePdf(out, opts.release); // a release PDF is a kept version too
      if (pdf) console.log(`PDF: ${pdf}`);
      if (opts.png) {
        if (pdf) {
          const pngDir = makePngs(pdf, out, rows);
          if (pngDir) console.log(`PNG: ${pngDir}`);
        } else {
          console.warn("WARNING: no PDF, so no PNGs");
        }
      }
    }
    console.log(out); // always the last stdout line
  } catch (err) {
    fs.rmSync(tmp, { force: true });
    console.error(`ERROR: build failed, ${out} not replaced: ${err.stack || err}`);
    process.exit(1);
  } finally {
    releaseLock();
  }
}

process.on("exit", releaseLock);
for (const sig of ["SIGINT", "SIGTERM", "SIGHUP"]) {
  process.on(sig, () => { releaseLock(); process.exit(128 + (os.constants.signals[sig] || 0)); });
}
main().catch((err) => { console.error(`ERROR: ${err.stack || err}`); process.exit(1); });

#!/usr/bin/env python3
"""Slide references in a deck's docs: ``{{key}}`` tokens, check, show, generated blocks.

Convention
----------
A live doc never carries a page number or a slide title by hand.  It names a slide by its
KEY, written ``{{key}}``; the page number and the title are looked up in the pages list that
every build writes next to the pptx (``<outDir>/<name>_wip.pages.json``)::

    [{"page": 1, "title": "Title", "section": "title", "order": 10, "builder": "sTitle"}, ...]

``{{key}}`` is shown as ``P<page>「<title>」``, ``{{key.title}}`` as the title alone and
``{{key.page}}`` as ``P<page>`` alone.  A range is two tokens, ``{{keyA}}–{{keyB}}``; each end
resolves on its own.  Moving or renaming a slide therefore never needs an edit in an md file.

Keys
----
The key of a slide is the name of its page file ``slides/<key>.js`` (without ``.js``); the
build writes it as ``builder`` in pages.json.  A page without a builder gets
``slide-<slug of the title>``.  Keys must be unique (a repeated key, or a repeated page number,
is FATAL: exit code 2).  The ``order`` field of pages.json is read but not shown.  Titles may
repeat (progressive emphasis: one title on two pages); repeated titles only print a WARNING
and every token still resolves by key.

Tokens and page references inside inline code (backticks) and fenced code blocks are literal
text: they are neither resolved nor checked.

Usage
-----
::

    python3 pages.py <deck> [--check]          # default mode
    python3 pages.py <deck> --show outline/01_results.md
    python3 pages.py <deck> --keys
    python3 pages.py <deck> --table [--write]  # dry run unless --write

``<deck>`` is the deck directory (holds ``deck.config.js``; default: the current directory).
The default pages.json is ``<deck>/<outDir>/<name>_wip.pages.json``, with ``name`` and
``outDir`` read from ``deck.config.js`` by a regex (node is not run); ``--pages`` overrides it.
``lang`` is read from deck.config.js the same way.

Modes
-----
--check     read-only.  Errors: [k] a ``{{key}}`` with no slide, or a malformed ``{{...}}``; [r] a hand-written page
            reference ``P<digits>`` outside code and generated blocks (the hand-written Note
            cells of the page table are checked too); [b] a key-like name ``sXxx`` in
            inline code that is neither a key of pages.json nor a page file
            ``<deck>/slides/<name>.js`` (code spans holding a ``{{`` token example are
            skipped; names inside the page files are not looked at); [g] a
            generated block that is out of date (run ``--table --write``).  Also prints a
            note with the number of slide titles still written out as ``「title」`` (not an
            error).  Exit 1 on any error.
--show F    print doc F with every token resolved (exit 1 if a key is unknown).
--keys      print page, key, section and title of every slide.
--table     regenerate the blocks between ``<!-- pages:counts:start -->`` / ``...:end -->``
            (pages per section, from pages.json) and ``<!-- pages:table:start -->`` /
            ``...:end -->`` (page, section, subsection, title, key, Note) in every scanned doc
            that has them.  The hand-written subsection and Note columns are kept per key; new
            rows get the placeholders ``—`` / ``(Note to be added)``; keys that are no longer
            slides are printed (their Note is dropped).  Dry run (prints the diff) unless
            ``--write``; ``--write`` first copies each changed file to
            ``<deck>/.backups/<timestamp>/<relative path>``.

Language of the generated blocks
--------------------------------
``lang: "en"`` (the default) or ``lang: "zh"`` in deck.config.js sets the language of the
counts line, the table header and the Note placeholder::

    en  N slides (section key and slide count): `title` 1 · `results` 2
        | Page | Section | Subsection | Slide title | key | Note |      placeholder (Note to be added)
    zh  共 N 页（节 key 和页数）：`title` 1 · `results` 2
        | 页 | 节 | 小节 | 页标题 | key | Note |                          placeholder （待补 Note）

Table rows are read by position, so a table with a header in either language (or v1's
``key（builder）``) is understood, and a Note that is still the placeholder of either language
is rewritten in the deck's language.  Changing ``lang`` and running ``--table --write``
therefore switches the blocks; until then ``--check`` reports them as out of date.

Files scanned: the language selected by ``deck.config.js`` from ``README.md`` / ``README.zh-CN.md``,
``TODO.md`` / ``TODO.zh-CN.md``, and ``outline/*.md`` / ``outline/*.zh-CN.md``.  With ``lang: "en"``
the unsuffixed files are scanned; with ``lang: "zh"`` the ``.zh-CN.md`` files are preferred when they
exist.  The alternate language is skipped, and ``outline/archive/`` is never read.  Files are read fresh
on every run.

Hits that are not slide pages (e.g. a protein named P53): put a line ``file:regex`` into
``<deck>/pages_ignore.txt`` (``--ignore-file`` overrides); a hit is ignored when the regex
matches a span of that line that covers the hit.  A line containing ``<!--pages:ignore-->``
is skipped by the [r] check.

Python 3.10+, standard library only.
"""

import argparse
import datetime as dt
import difflib
import fnmatch
import json
import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn

INLINE_IGNORE = "<!--pages:ignore-->"
IGNORE_FILE = "pages_ignore.txt"
BACKUP_DIR = ".backups"

TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z_][\w#\-]*)(?:\.(title|page))?\s*\}\}")
ANY_TOKEN_RE = re.compile(r"\{\{[^{}\n]*\}\}")
# P<number> not glued to a letter/digit before, not followed by a digit, a letter, or ".<alnum>".
PAGE_REF_RE = re.compile(r"(?<![A-Za-z0-9_])P(\d{1,3})(?![\d.A-Za-z_]|\.\w)")
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
BLOCK_RE = re.compile(r"<!--\s*pages:(table|counts):(start|end)\s*-->")
BUILDER_RE = re.compile(r"\bs[A-Z][A-Za-z0-9_]+\b(?![\w*])")

# Strings of the generated blocks per deck.config.js ``lang``.  Rows of an existing table are
# read by position, so the header of either language (and v1's "key（builder）") is accepted.
LANGS = {
    "en": {"header": ["Page", "Section", "Subsection", "Slide title", "key", "Note"],
           "note": "(Note to be added)"},
    "zh": {"header": ["页", "节", "小节", "页标题", "key", "Note"],
           "note": "（待补 Note）"},
}
DEFAULT_LANG = "en"
N_COLS = 6
NO_SECTION = "—"
NOTE_PLACEHOLDERS = {s["note"] for s in LANGS.values()}


def die(msg, code=2) -> NoReturn:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------------- deck config
class DeckError(Exception):
    """deck.config.js is missing or a field cannot be read from it."""


def config_field(deck, field, default=None):
    """String value of ``field: "..."`` in ``<deck>/deck.config.js`` (first match at line start).

    The file is not executed: only a literal string value is understood.  Without a match the
    default is returned, or ``DeckError`` raised when there is no default.
    """
    path = Path(deck) / "deck.config.js"
    if not path.is_file():
        if default is not None:
            return default
        raise DeckError(f"{path} not found (is {deck} a deck directory?)")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\s*" + re.escape(field) + r"""\s*:\s*(["'`])([^"'`\n]*)\1""", text, re.M)
    if m:
        return m.group(2)
    if default is not None:
        return default
    raise DeckError(f"{path}: no literal string field '{field}: \"...\"' found (pass --pages)")


def default_pages_path(deck):
    """``<deck>/<outDir>/<name>_wip.pages.json`` from deck.config.js."""
    deck = Path(deck)
    name = config_field(deck, "name")
    out_dir = config_field(deck, "outDir", "output")
    return deck / out_dir / f"{name}_wip.pages.json"


def deck_lang(deck):
    """``lang`` of deck.config.js ("en" when the file or the field is missing)."""
    lang = config_field(deck, "lang", DEFAULT_LANG)
    if lang not in LANGS:
        raise DeckError(f"{Path(deck) / 'deck.config.js'}: lang must be one of "
                        f"{', '.join(repr(k) for k in LANGS)}, not {lang!r}")
    return lang


# --------------------------------------------------------------------------- pages
class PagesError(Exception):
    """pages.json is missing or unusable."""


def slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()


def assign_keys(rows):
    """Add ``key`` to every row (rows sorted by page): the builder, i.e. the page file name."""
    for row in rows:
        row["key"] = row.get("builder") or f"slide-{slug(row['title'])}"
    pages_of = {}
    for row in rows:
        pages_of.setdefault(row["key"], []).append(row["page"])
    dup = {k: ns for k, ns in pages_of.items() if len(ns) > 1}
    if dup:
        raise PagesError("keys must be unique (key = page file name slides/<key>.js); repeated: "
                         + "; ".join(f"{k} on pages {ns}" for k, ns in sorted(dup.items())))
    return rows


def load_pages(path):
    """The pages.json list ``[{"page", "title", "section", "order", "builder", "key"}, ...]`` in page order.

    Raises ``PagesError`` when the file is missing or broken, or when a page number or a key is
    not unique.  Repeated titles are allowed (see ``duplicate_titles``).
    """
    path = Path(path)
    if not path.is_file():
        raise PagesError(f"pages file not found: {path}\n"
                         "Build the deck first (it writes <name>_wip.pages.json), or pass --pages.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PagesError(f"{path} is not valid JSON: {exc}")
    if not isinstance(data, list) or not data:
        raise PagesError(f"{path}: expected a non-empty list of page records")
    rows, seen_page = [], set()
    for rec in data:
        if not isinstance(rec, dict) or "page" not in rec or "title" not in rec:
            raise PagesError(f"{path}: record without page/title: {rec}")
        # A slide made with newSlide(pres, null, n) (e.g. a section divider) has no title: show it as "".
        n, title = int(rec["page"]), "" if rec["title"] is None else str(rec["title"])
        if n in seen_page:
            raise PagesError(f"{path}: page number {n} appears twice")
        seen_page.add(n)
        rows.append({"page": n, "title": title, "section": rec.get("section", "") or "",
                     "order": rec.get("order"), "builder": rec.get("builder", "") or ""})
    rows.sort(key=lambda r: r["page"])
    return assign_keys(rows)


def duplicate_titles(rows):
    """{title: [pages]} of the titles that occur on more than one page (allowed, but worth a warning)."""
    seen = {}
    for r in rows:
        seen.setdefault(r["title"], []).append(r["page"])
    return {t: ns for t, ns in seen.items() if len(ns) > 1}


class Pages:
    """Rows from ``load_pages`` with lookups by key and title (by_title: first page of a title).

    ``lang`` is the language of the generated blocks (a key of ``LANGS``).
    """

    def __init__(self, rows, path=None, lang=DEFAULT_LANG):
        self.recs = rows
        self.path = path
        self.lang = lang
        self.by_key = {r["key"]: r for r in rows}
        self.by_title = {}
        for r in rows:
            self.by_title.setdefault(r["title"], r)
        self.titles_longest_first = sorted(self.by_title, key=len, reverse=True)
        self.dup_titles = duplicate_titles(rows)


def token_text(rec, part=None):
    """``{{key}}`` -> P2「title」; ``{{key.title}}`` -> title; ``{{key.page}}`` -> P2."""
    if part == "title":
        return rec["title"]
    if part == "page":
        return f"P{rec['page']}"
    return f"P{rec['page']}「{rec['title']}」"


# --------------------------------------------------------------------------- docs
def doc_files(deck):
    """Return only the live documentation language selected by ``deck.config.js``.

    A deck may keep English and Chinese outline files side by side.  Scanning both would make one
    language look stale whenever ``lang`` selects the other, so the localized sibling is preferred
    for ``lang: "zh"`` and skipped otherwise.
    """
    lang = deck_lang(deck)

    def choose(path):
        if lang == "zh":
            zh = path.with_name(f"{path.stem}.zh-CN{path.suffix}")
            if zh.is_file():
                return zh
        return path if path.is_file() else None

    files = []
    for name in ("README.md", "TODO.md"):
        selected = choose(deck / name)
        if selected is not None:
            files.append(selected)

    outline = deck / "outline"
    if outline.is_dir():
        for path in sorted(outline.glob("*.md")):
            if path.name.endswith(".zh-CN.md"):
                continue
            selected = choose(path)
            if selected is not None:
                files.append(selected)
    return files


def read_lines(path):
    # newline="" keeps the original line endings; split on "\n" only.
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read().split("\n")


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines))


def mask_lines(lines):
    """Same lines with fenced code blocks and inline code spans blanked out (same length)."""
    out, fence = [], None
    for ln in lines:
        m = FENCE_RE.match(ln)
        if fence is None and m:
            fence = m.group(1)
            out.append(" " * len(ln))
        elif fence is not None:
            if m and m.group(1) == fence:
                fence = None
            out.append(" " * len(ln))
        else:
            out.append(CODE_SPAN_RE.sub(lambda s: " " * len(s.group(0)), ln))
    return out


def load_ignore(path):
    entries = []
    if path is not None and path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            fpat, _, rx = raw.partition(":")
            if not rx:
                die(f"{path}: bad entry (need file:regex): {raw}")
            entries.append((fpat.strip(), re.compile(rx.strip())))
    return entries


def is_ignored(entries, rel, line, pos):
    for fpat, rx in entries:
        if not (fpat == rel or fpat == Path(rel).name or fnmatch.fnmatch(rel, fpat)):
            continue
        for m in rx.finditer(line):
            if m.start() <= pos < m.end():
                return True
    return False


def find_blocks(lines, rel):
    """{name: (start_idx, end_idx)} of the marker lines of the generated blocks."""
    open_, blocks = {}, {}
    for i, ln in enumerate(lines):
        m = BLOCK_RE.fullmatch(ln.strip())
        if not m:
            continue
        name, edge = m.groups()
        if edge == "start":
            if name in open_ or name in blocks:
                die(f"{rel}:{i + 1}: second 'pages:{name}:start' marker")
            open_[name] = i
        else:
            if name not in open_:
                die(f"{rel}:{i + 1}: 'pages:{name}:end' without a start marker")
            blocks[name] = (open_.pop(name), i)
    if open_:
        name = next(iter(open_))
        die(f"{rel}:{open_[name] + 1}: 'pages:{name}:start' without an end marker")
    return blocks


def cell_texts(line):
    """Stripped cell texts of a markdown table row ('|' escaped as '\\|' stays inside a cell)."""
    s = line.rstrip("\r")
    if not s.lstrip().startswith("|"):
        return []
    idx = [i for i, ch in enumerate(s) if ch == "|" and (i == 0 or s[i - 1] != "\\")]
    return [s[a + 1:b].strip() for a, b in zip(idx, idx[1:])]


def is_table_row(cells):
    return len(cells) == N_COLS and re.fullmatch(r"P\d+", cells[0]) is not None


def resolve_text(line, mline, pages, unknown=None):
    """Replace the tokens of a line (found in its masked twin) by their text."""
    out, pos = [], 0
    for m in TOKEN_RE.finditer(mline):
        rec = pages.by_key.get(m.group(1))
        out.append(line[pos:m.start()])
        if rec is None:
            if unknown is not None:
                unknown.append(m.group(1))
            out.append(line[m.start():m.end()])
        else:
            out.append(token_text(rec, m.group(2)))
        pos = m.end()
    out.append(line[pos:])
    return "".join(out)


# --------------------------------------------------------------------------- generated blocks
def section_counts(pages):
    """[(section key, page count)] in order of first appearance in pages.json."""
    counts = {}
    for rec in pages.recs:
        counts[rec["section"]] = counts.get(rec["section"], 0) + 1
    return list(counts.items())


def render_counts(pages):
    counts = section_counts(pages)
    total = sum(n for _, n in counts)
    items = " · ".join(f"`{k}` {n}" for k, n in counts)
    if pages.lang == "zh":
        return ["", f"共 {total} 页（节 key 和页数）：" + items, ""]
    return ["", f"{total} slide{'' if total == 1 else 's'} (section key and slide count): " + items, ""]


def parse_table_block(body):
    """{key: (subsection, Note)} from the rows of a generated page table (header not read).

    An empty cell or a Note that is the placeholder of any language comes back as ``None``,
    so that ``render_table`` writes the placeholder of the deck's language.
    """
    preserved = {}
    for ln in body:
        cells = cell_texts(ln)
        if is_table_row(cells):
            note = cells[5] if cells[5] and cells[5] not in NOTE_PLACEHOLDERS else None
            preserved[cells[4].strip("`")] = (cells[2] or NO_SECTION, note)
    return preserved


def render_table(pages, preserved):
    """Lines of the page table; preserved = {key: (subsection, Note)}.  Also returns the dropped keys."""
    strings = LANGS[pages.lang]
    header = strings["header"]
    lines = ["", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for rec in pages.recs:
        sub, note = preserved.get(rec["key"], (NO_SECTION, None))
        note = note or strings["note"]
        title = rec["title"].replace("|", "\\|")
        lines.append(f"| P{rec['page']} | {rec['section']} | {sub} | {title} | `{rec['key']}` | {note} |")
    lines.append("")
    dropped = [k for k in preserved if k not in pages.by_key]
    return lines, dropped


def refresh_blocks(lines, rel, pages):
    """Regenerate the generated blocks of a doc; returns (new lines, dropped keys of the table)."""
    blocks = find_blocks(lines, rel)
    new, dropped = list(lines), []
    for name, (s, e) in sorted(blocks.items(), key=lambda kv: -kv[1][0]):
        if name == "table":
            gen, drop = render_table(pages, parse_table_block(new[s + 1:e]))
            dropped += drop
        else:
            gen = render_counts(pages)
        new[s + 1:e] = gen
    return new, dropped


# --------------------------------------------------------------------------- check
KIND_NAMES = {
    "k": "{{key}} with no matching slide",
    "r": "hand-written page reference (use {{key}})",
    "b": "slide key in backticks that does not exist",
    "g": "generated block out of date",
}


def page_file_keys(deck):
    """Keys of the page files ``<deck>/slides/<key>.js`` (not recursive; ``_*`` files are helpers)."""
    return {p.stem for p in (deck / "slides").glob("*.js") if not p.name.startswith("_")}


def scan_doc(path, rel, pages, ignore, known_keys):
    """(errors, literal-title count) of one doc.  errors: [(kind, lineno, message)].

    ``known_keys``: keys of pages.json plus the names of the page files slides/<key>.js.
    """
    lines = read_lines(path)
    mlines = mask_lines(lines)
    blocks = find_blocks(lines, rel)
    gen = set()
    for s, e in blocks.values():
        gen.update(range(s, e + 1))
    quoted = re.compile("「(" + "|".join(re.escape(t) for t in pages.titles_longest_first) + ")」")
    errs, literal, fence = [], 0, None
    for i, (line, ml) in enumerate(zip(lines, mlines)):
        lineno = i + 1
        for m in ANY_TOKEN_RE.finditer(ml):
            t = TOKEN_RE.fullmatch(m.group(0))
            if t is None:
                errs.append(("k", lineno, f"{m.group(0)} is not a token: write {{{{key}}}}, {{{{key.title}}}} or {{{{key.page}}}}"))
            elif t.group(1) not in pages.by_key:
                errs.append(("k", lineno, f"{{{{{t.group(1)}}}}} is not a slide key (see --keys)"))
        # key-like names are checked in inline code only (not in fenced blocks)
        fm = FENCE_RE.match(line)
        if fence is None and fm:
            fence = fm.group(1)
            continue
        if fence is not None:
            if fm and fm.group(1) == fence:
                fence = None
            continue
        for span in CODE_SPAN_RE.finditer(line):
            if "{{" in span.group(0):          # a token written as an example: literal
                continue
            for m in BUILDER_RE.finditer(span.group(0)):
                if m.group(0) not in known_keys:
                    errs.append(("b", lineno, f"`{m.group(0)}` is neither in pages.json nor a page file "
                                              f"slides/{m.group(0)}.js"))
        if i in gen:       # generated blocks hold page numbers by design; only the Note cell is checked
            cells = cell_texts(ml)
            if is_table_row(cell_texts(line)) and len(cells) == N_COLS:
                for m in PAGE_REF_RE.finditer(cells[5]):
                    errs.append(("r", lineno, f"hand-written page reference P{m.group(1)} in a Note: write {{{{key}}}}"))
            continue
        literal += len(quoted.findall(ml))
        if INLINE_IGNORE in line:
            continue
        for m in PAGE_REF_RE.finditer(ml):
            if is_ignored(ignore, rel, line, m.start()):
                continue
            snippet = line[max(0, m.start() - 12): m.end() + 14]
            errs.append(("r", lineno, f"hand-written page reference P{m.group(1)}: write {{{{key}}}}  …{snippet}…"))
    if blocks:
        new, _ = refresh_blocks(lines, rel, pages)
        if new != lines:
            first = next(j for j, (a, b) in enumerate(zip(lines + [None], new + [None])) if a != b)
            errs.append(("g", first + 1, "generated block is out of date: run  pages.py <deck> --table --write"))
    return errs, literal


def cmd_check(deck, pages, ignore):
    known_keys = page_file_keys(deck) | {r["key"] for r in pages.recs}
    files = doc_files(deck)
    print(f"pages: {len(pages.recs)} slides from {pages.path}")
    print(f"docs:  {', '.join(p.relative_to(deck).as_posix() for p in files) or '(none)'}")
    allerrs, literal = [], {}
    for p in files:
        rel = p.relative_to(deck).as_posix()
        errs, lit = scan_doc(p, rel, pages, ignore, known_keys)
        allerrs += [(k, rel, ln, msg) for k, ln, msg in errs]
        if lit:
            literal[rel] = lit
    totals = {}
    for kind, label in KIND_NAMES.items():
        items = [e for e in allerrs if e[0] == kind]
        totals[kind] = len(items)
        if items:
            print(f"\n[{kind}] {label}: {len(items)}")
            for _, rel, ln, msg in items:
                print(f"  {rel}:{ln}  {msg}")
    if literal:
        print("\nnote: slide titles still written out as 「title」 (not errors; they do not follow a rename): "
              + ", ".join(f"{rel} {n}" for rel, n in sorted(literal.items())))
    total = sum(totals.values())
    print("\nSummary: " + ", ".join(f"[{k}] {v}" for k, v in totals.items()) + f"  | total {total}")
    return 1 if total else 0


# --------------------------------------------------------------------------- show / keys
def resolve_doc_path(arg, deck):
    for cand in (Path(arg), deck / arg, deck / "outline" / arg):
        if cand.is_file():
            return cand
    die(f"--show: file not found: {arg}")


def cmd_show(deck, pages, arg):
    path = resolve_doc_path(arg, deck)
    lines = read_lines(path)
    unknown = []
    out = [resolve_text(ln, ml, pages, unknown) for ln, ml in zip(lines, mask_lines(lines))]
    sys.stdout.write("\n".join(out))
    if not out[-1:] == [""]:
        sys.stdout.write("\n")
    if unknown:
        print(f"WARNING: unknown keys left unresolved: {', '.join(sorted(set(unknown)))}", file=sys.stderr)
        return 1
    return 0


def cmd_keys(pages):
    wk = max(len("key"), *(len(r["key"]) for r in pages.recs))
    ws = max(len("section"), *(len(r["section"]) for r in pages.recs))
    print(f"{'page':>4}  {'key':<{wk}}  {'section':<{ws}}  title")
    for r in pages.recs:
        print(f"{r['page']:>4}  {r['key']:<{wk}}  {r['section']:<{ws}}  {r['title']}")
    return 0


# --------------------------------------------------------------------------- table
def cmd_table(deck, pages, write):
    backup_dir = deck / BACKUP_DIR / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    marked, changed = 0, 0
    for p in doc_files(deck):
        rel = p.relative_to(deck).as_posix()
        lines = read_lines(p)
        if not find_blocks(lines, rel):
            continue
        marked += 1
        new, dropped = refresh_blocks(lines, rel, pages)
        if dropped:
            print(f"{rel}: keys in the table that are no longer slides (their subsection / Note are dropped): "
                  + ", ".join(dropped))
        if new == lines:
            print(f"{rel}: generated blocks up to date")
            continue
        changed += 1
        diff = [d for d in difflib.unified_diff(lines, new, lineterm="", n=0)
                if d[:1] in "+-" and d[:3] not in ("+++", "---")]
        print(f"{rel}: {len(diff)} changed line(s) in the generated blocks")
        if not write:
            for d in diff:
                print("   " + d)
            continue
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        write_lines(p, new)
        print(f"  written (backup: {dst})")
    if not marked:
        print("no scanned doc has pages:table / pages:counts markers")
    elif changed and not write:
        print("DRY RUN: nothing written (add --write)")
    return 0


# --------------------------------------------------------------------------- main
def open_pages(deck, pages_arg):
    """Pages of the deck (``--pages`` or the wip pages.json); FATAL (exit 2) on any problem."""
    try:
        path = Path(pages_arg) if pages_arg else default_pages_path(deck)
        pages = Pages(load_pages(path), path, deck_lang(deck))
    except (DeckError, PagesError) as exc:
        die(str(exc))
    if pages.dup_titles:
        print("WARNING: titles shared by several pages (allowed; {{key}} still works, pull_notes needs "
              "aliases for them): " + "; ".join(f"{t!r} pages {ns}" for t, ns in pages.dup_titles.items()),
              file=sys.stderr)
    return pages


def main(argv=None):
    ap = argparse.ArgumentParser(description="{{key}} slide references in a deck's docs "
                                             "(see the module docstring).")
    ap.add_argument("deck", nargs="?", default=".", type=Path,
                    help="deck directory holding deck.config.js and outline/ (default: .)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only check (default)")
    mode.add_argument("--show", metavar="FILE", help="print FILE with every {{key}} resolved")
    mode.add_argument("--keys", action="store_true", help="print page, key, section and title of every slide")
    mode.add_argument("--table", action="store_true",
                      help="regenerate the pages:counts / pages:table blocks (dry run unless --write)")
    ap.add_argument("--write", action="store_true", help="--table: really write the docs")
    ap.add_argument("--pages", metavar="JSON",
                    help="pages.json (default: <deck>/<outDir>/<name>_wip.pages.json from deck.config.js)")
    ap.add_argument("--ignore-file", type=Path, metavar="TXT",
                    help=f"file:regex lines of hits that are not pages (default: <deck>/{IGNORE_FILE})")
    args = ap.parse_args(argv)
    if args.write and not args.table:
        ap.error("--write only goes with --table")

    deck = args.deck.resolve()
    if not deck.is_dir():
        die(f"deck directory not found: {deck}")
    pages = open_pages(deck, args.pages)
    if args.show:
        return cmd_show(deck, pages, args.show)
    if args.keys:
        return cmd_keys(pages)
    if args.table:
        return cmd_table(deck, pages, args.write)
    ignore = load_ignore(args.ignore_file or deck / IGNORE_FILE)
    return cmd_check(deck, pages, ignore)


if __name__ == "__main__":
    sys.exit(main())

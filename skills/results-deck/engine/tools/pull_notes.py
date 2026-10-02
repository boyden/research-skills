#!/usr/bin/env python3
"""Pull the speaker notes out of a hand-edited pptx into the deck's ``notes/<key>.md`` files.

The speaker notes are DATA, one file per slide: ``<deck>/notes/<key>.md`` (UTF-8, one
paragraph per line, trailing newline), keyed by the slide key (the page file name
``slides/<key>.js``, see ``pages.py``).  The build replaces the notes of every slide that has a
notes file; slides without one keep the ``slide.addNotes()`` text of their page file.  The
source of truth is the pptx the speaker edits in PowerPoint; this tool reads its notes pages
and writes the notes files of the slides whose text CHANGED.  It never deletes a file.

Usage
-----
::

    python3 pull_notes.py <deck> [pptx] [--dry-run | --write] [--pages PAGES_JSON]

Without ``--write`` nothing is written (``--dry-run`` only makes that explicit).  The report
lists the keys whose file would be / was written (new or changed), the keys whose file is
unchanged and the pptx slides that were not matched.  ``--write`` first copies every existing
file it is about to change to ``<deck>/.backups/<timestamp>/<relative path>``, then writes the
changed ``notes/<key>.md`` files and rewrites ``notes/_unmatched.json`` (a list, ``[]`` when
every slide matched).  A file whose text equals the pptx notes is not touched.

Default pptx: the highest release ``<deck>/<outDir>/<name>_v<N>.pptx``.  Default pages.json:
``<deck>/<outDir>/<name>_wip.pages.json``.  ``name`` and ``outDir`` come from
``deck.config.js`` (like ``pages.py``).  v1's ``<deck>/notes.json`` is not read; when it exists
a one-line hint is printed.

Matching a pptx slide to a key
------------------------------
Slide title: the first text shape (in shape order) whose text equals a pages.json title;
otherwise the title placeholder; otherwise the text shape closest to the top-left corner.
Whitespace and line breaks inside a shape are collapsed to single spaces before comparing.
Keys are tried in this order:

a. the first slide is the first pages.json entry when that entry's title is ``Title`` or
   equals the slide's title (a title slide rarely shows the word "Title");
b. ``<deck>/notes/_aliases.json`` (``{"<pptx slide title>": "<key>"}``); a title that occurs
   several times in the pptx is addressed as ``"<title>"`` (first occurrence), then
   ``"<title>#2"``, ``"<title>#3"`` ...;
c. the title equals exactly one pages.json title and occurs once in the pptx.  A repeated
   title (allowed in pages.json, e.g. progressive emphasis) is never matched automatically:
   it needs the aliases ``"<title>"``, ``"<title>#2"`` ...

A slide that matches nothing, whose title occurs more than once in the pptx without an alias
for that occurrence, or whose key is not in pages.json, is not usable as a file name or is
already taken by an earlier slide is NOT written: it is listed in the report and in
``<deck>/notes/_unmatched.json`` (with its notes text and the reason), so it can be resolved
by adding an alias and running the tool again.

Notes text: the body placeholder of the notes page.  Paragraphs and soft line breaks become
line breaks; line endings are normalized and trailing whitespace of every line and of the
whole text is stripped; run formatting is not kept.  Text typed after the number in the
slide-number placeholder of a notes page (PowerPoint lets the speaker type there by accident)
is appended as an extra paragraph; the number itself is dropped.  A notes file is compared
after the same normalization, so a missing trailing newline or CRLF line endings alone do not
count as a change.  Empty pptx notes are written as an empty file (the build then clears that
slide's notes) when the slide has no notes file yet or its file holds other text.

Python 3.10+, standard library only (zipfile + xml.etree).
"""

import argparse
import datetime as dt
import json
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import NoReturn
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pages as pg  # noqa: E402  # pyright: ignore[reportMissingImports]  (sibling module)

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
RID = "{%s}id" % NS["r"]
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
NOTES_DIR = "notes"
ALIASES_JSON = f"{NOTES_DIR}/_aliases.json"
UNMATCHED_JSON = f"{NOTES_DIR}/_unmatched.json"
V1_NOTES_JSON = "notes.json"
# A key becomes a file name: no path separators, no leading "_" or "." (those are helper files).
KEY_FILE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_#\-]*")


def die(msg) -> NoReturn:
    pg.die(msg)
    raise SystemExit(2)      # not reached; tells type checkers that die() does not return


def norm(text):
    return " ".join(text.split())


def para_text(para):
    """Text of one a:p: runs and fields in order, a:br as a newline."""
    out = []
    for el in para:
        if el.tag in (A + "r", A + "fld"):
            out.append("".join(t.text or "" for t in el.findall("a:t", NS)))
        elif el.tag == A + "br":
            out.append("\n")
    return "".join(out)


def clean(text):
    """Normalise line endings; strip trailing whitespace of every line and of the whole text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0b", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).rstrip()


def body_text(sp):
    tx = sp.find("p:txBody", NS)
    return clean("\n".join(para_text(p) for p in tx.findall("a:p", NS))) if tx is not None else ""


def rels_of(z, part):
    """{rId: (Type, zip path of the target)} of a part."""
    d, name = part.rsplit("/", 1)
    rel_path = f"{d}/_rels/{name}.rels"
    if rel_path not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(rel_path)):
        if r.get("TargetMode") == "External":
            continue
        out[r.get("Id")] = (r.get("Type", ""), resolve(d, r.get("Target", "")))
    return out


def resolve(base_dir, target):
    """Zip path of a relationship target relative to the part's directory."""
    parts = target[1:].split("/") if target.startswith("/") else (base_dir + "/" + target).split("/")
    out = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        elif p and p != ".":
            out.append(p)
    return "/".join(out)


def placeholder_type(sp):
    ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
    return None if ph is None else ph.get("type", "body")


def slide_title(root, titles):
    """Title of a slide (see the module doc); ``titles`` = normalised pages.json titles."""
    shapes = []
    for sp in root.iter(P + "sp"):
        txt = norm(" ".join(para_text(p) for p in sp.iter(A + "p")))
        if not txt:
            continue
        if txt in titles:
            return txt
        off = sp.find("p:spPr/a:xfrm/a:off", NS)
        xy = (int(off.get("x", 0)), int(off.get("y", 0))) if off is not None else None
        shapes.append((placeholder_type(sp), xy, txt))
    for ph, _, txt in shapes:
        if ph in ("title", "ctrTitle"):
            return txt
    placed = [(math.hypot(*xy), xy[1], xy[0], txt) for _, xy, txt in shapes if xy is not None]
    if placed:
        return min(placed)[3]
    return shapes[0][2] if shapes else ""


def notes_text(z, part):
    root = ET.fromstring(z.read(part))
    notes, extra = "", ""
    for sp in root.iter(P + "sp"):
        ph = placeholder_type(sp)
        if ph == "body" and not notes:
            notes = body_text(sp)
        elif ph == "sldNum":
            extra = re.sub(r"^\s*\d+\s*", "", body_text(sp))
    return (notes + "\n" + extra).strip("\n") if extra else notes


def read_pptx(path, titles=()):
    """Slides of a pptx in deck order: [{n, title, notes, hidden}]."""
    titles = {norm(t) for t in titles}
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        prels = rels_of(z, "ppt/presentation.xml")
        lst = pres.find("p:sldIdLst", NS)
        slides = []
        for n, sld in enumerate(lst if lst is not None else [], 1):
            part = prels[sld.get(RID)][1]
            root = ET.fromstring(z.read(part))
            notes = ""
            for typ, target in rels_of(z, part).values():
                if typ.endswith("/notesSlide"):
                    notes = notes_text(z, target)
            slides.append({"n": n, "title": slide_title(root, titles), "notes": notes,
                           "hidden": root.get("show") in ("0", "false")})
    return slides


def match_slides(slides, rows, aliases):
    """(matched, unmatched): matched = [(key, slide)], unmatched = [(slide, occurrence, reason)]."""
    keys = {r["key"] for r in rows}
    by_title = {}
    for r in rows:
        by_title.setdefault(norm(r["title"]), []).append(r["key"])
    aliases = {norm(k.rsplit("#", 1)[0]) + (("#" + k.rsplit("#", 1)[1]) if re.search(r"#\d+$", k) else ""): v
               for k, v in aliases.items()}
    total = {}
    for s in slides:
        total[s["title"]] = total.get(s["title"], 0) + 1
    seen, taken, matched, unmatched = {}, {}, [], []
    for idx, s in enumerate(slides):
        title = s["title"]
        seen[title] = seen.get(title, 0) + 1
        occ = seen[title]
        alias_name = title if occ == 1 else f"{title}#{occ}"
        key, reason = None, None
        if idx == 0 and rows and (rows[0]["title"] == "Title" or norm(rows[0]["title"]) == title):
            key = rows[0]["key"]
        elif alias_name in aliases:
            key = aliases[alias_name]
        elif total[title] > 1:
            reason = (f"title occurs {total[title]} times in the pptx; add aliases "
                      f"'{title}', '{title}#2', ... to {ALIASES_JSON}")
        elif len(by_title.get(title, [])) == 1:
            key = by_title[title][0]
        elif len(by_title.get(title, [])) > 1:
            reason = (f"title is shared by {len(by_title[title])} slides of pages.json "
                      f"({', '.join(by_title[title])}); add an alias to {ALIASES_JSON}")
        else:
            reason = f"title matches no slide of pages.json; add an alias to {ALIASES_JSON}"
        if key is not None and key not in keys:
            reason, key = f"key '{key}' is not in pages.json", None
        if key is not None and not KEY_FILE_RE.fullmatch(key):
            reason, key = f"key '{key}' cannot be a file name {NOTES_DIR}/<key>.md", None
        if key is not None and key in taken:
            reason, key = f"key '{key}' is already taken by slide {taken[key]}", None
        if key is None:
            unmatched.append((s, occ, reason))
        else:
            taken[key] = s["n"]
            matched.append((key, s))
    return matched, unmatched


def read_json(path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"{path} is not valid JSON: {exc}")


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def notes_file_text(text):
    """Content of a notes file: one paragraph per line and a trailing newline (empty notes: empty file)."""
    return text + "\n" if text else ""


def read_notes_file(path):
    """Text of a notes file normalized like the pptx notes (``clean``), or None when there is no file."""
    return clean(path.read_text(encoding="utf-8")) if path.is_file() else None


def default_pptx(deck):
    """The highest release ``<deck>/<outDir>/<name>_v<N>.pptx`` (``DeckError`` when there is none)."""
    name = pg.config_field(deck, "name")
    out = deck / pg.config_field(deck, "outDir", "output")
    rx = re.compile(re.escape(name) + r"_v(\d+)\.pptx")
    found = [(int(m.group(1)), p) for p in out.glob("*.pptx") if (m := rx.fullmatch(p.name))]
    if not found:
        raise pg.DeckError(f"no release {out}/{name}_v<N>.pptx found: pass the speaker's pptx")
    return max(found)[1]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", type=Path, help="deck directory (holds deck.config.js, notes/)")
    ap.add_argument("pptx", type=Path, nargs="?",
                    help="the pptx with the speaker's notes (default: the highest <outDir>/<name>_v<N>.pptx)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="report only, write nothing (the default)")
    mode.add_argument("--write", action="store_true",
                      help=f"write the changed {NOTES_DIR}/<key>.md files and {UNMATCHED_JSON}")
    ap.add_argument("--pages", metavar="JSON",
                    help="pages.json to match against (default: <deck>/<outDir>/<name>_wip.pages.json)")
    args = ap.parse_args(argv)

    deck = args.deck.resolve()
    if not deck.is_dir():
        die(f"deck directory not found: {deck}")
    try:
        pptx = args.pptx or default_pptx(deck)
    except pg.DeckError as exc:
        die(str(exc))
    if not pptx.is_file():
        die(f"pptx not found: {pptx}")
    pages = pg.open_pages(deck, args.pages)
    rows = pages.recs
    if (deck / V1_NOTES_JSON).is_file():
        print(f"NOTE: {V1_NOTES_JSON} is not read: v2 keeps one {NOTES_DIR}/<key>.md per slide "
              f"(aliases in {ALIASES_JSON})")
    notes_dir = deck / NOTES_DIR
    aliases = read_json(deck / ALIASES_JSON, {})
    if not isinstance(aliases, dict):
        die(f"{deck / ALIASES_JSON}: expected an object {{\"<pptx slide title>\": \"<key>\"}}")
    try:
        slides = read_pptx(pptx, [r["title"] for r in rows])
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        die(f"cannot read {pptx} as a pptx: {exc}")
    matched, unmatched = match_slides(slides, rows, aliases)

    print(f"pptx : {pptx} ({len(slides)} slides, {sum(s['hidden'] for s in slides)} hidden)")
    print(f"pages: {pages.path} ({len(rows)} slides)")
    if len(slides) != len(rows):
        print(f"NOTE: the pptx has {len(slides)} slides but pages.json has {len(rows)}; slides are matched "
              "by title, unmatched ones are listed below")
    order = {r["key"]: i for i, r in enumerate(rows)}
    got = {key: s["notes"] for key, s in sorted(matched, key=lambda ks: order[ks[0]])}
    status = {}
    for key, text in got.items():
        old = read_notes_file(notes_dir / f"{key}.md")
        status[key] = "new" if old is None else "unchanged" if old == text else "changed"
    counts = {st: sum(v == st for v in status.values()) for st in ("new", "changed", "unchanged")}
    to_write = [k for k, st in status.items() if st != "unchanged"]
    print(f"matched {len(matched)} slides -> {counts['new']} new, {counts['changed']} changed, "
          f"{counts['unchanged']} unchanged in {NOTES_DIR}/")
    if to_write:
        print(("written" if args.write else "to write") + f" ({len(to_write)}):")
        for key in to_write:
            print(f"  {status[key]:9s} {key}")
    unchanged = [k for k, st in status.items() if st == "unchanged"]
    if unchanged:
        print("unchanged (not written): " + ", ".join(unchanged))
    empty = [k for k in to_write if not got[k]]
    if empty:
        print("empty notes in the pptx (written as empty files: the build clears these slides' notes): "
              + ", ".join(empty))
    missing = [r["key"] for r in rows if r["key"] not in got]
    if missing:
        print("pages.json keys without a matched slide (their notes files are not touched): " + ", ".join(missing))
    orphans = sorted(p.stem for p in notes_dir.glob("*.md") if not p.name.startswith("_") and p.stem not in order)
    if orphans:
        print(f"{NOTES_DIR}/ files of keys that are not in pages.json (kept; delete by hand if the page is gone): "
              + ", ".join(orphans))
    if unmatched:
        print(f"UNMATCHED {len(unmatched)} slide(s) (not written; listed in {UNMATCHED_JSON}):")
        for s, occ, reason in unmatched:
            print(f"  slide {s['n']}: '{s['title']}'" + (f" (occurrence {occ})" if occ > 1 else "") + f" -- {reason}")
    if not args.write:
        print("DRY RUN: nothing written (add --write)")
        return 0

    un = [{"slide": s["n"], "title": s["title"], "occurrence": occ, "reason": reason, "notes": s["notes"]}
          for s, occ, reason in unmatched]
    writes = [(notes_dir / f"{key}.md", notes_file_text(got[key])) for key in to_write]
    unmatched_path = deck / UNMATCHED_JSON
    un_text = json_text(un)
    un_changed = not (unmatched_path.is_file() and unmatched_path.read_text(encoding="utf-8") == un_text)
    if un_changed:
        writes.append((unmatched_path, un_text))
    backup_root = deck / pg.BACKUP_DIR / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backed_up = 0
    for path, _ in writes:                  # back up first, so a failed write leaves a copy of every file
        if path.is_file():
            dst = backup_root / path.relative_to(deck)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
            backed_up += 1
    notes_dir.mkdir(exist_ok=True)
    for path, text in writes:
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(to_write)} notes file(s) to {notes_dir}"
          + (f"; {UNMATCHED_JSON} ({len(un)} entries)" if un_changed else f"; {UNMATCHED_JSON} unchanged")
          + (f"; backup of {backed_up} file(s): {backup_root}" if backed_up else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

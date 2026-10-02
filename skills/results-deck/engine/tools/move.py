#!/usr/bin/env python3
"""Move one slide of a deck: edit only that page file's ``section`` and ``order`` (engine/SPEC.md §3, §9).

Every page is its own file ``slides/<key>.js`` that declares ``section: "<name>"`` and ``order: <number>``;
the build sorts the pages by the section order of ``deck.config.js`` (``sections: [...]``) and then by
``order``.  Moving a page therefore means changing those two fields in that one file, which is safe while
other agents edit other pages.

Usage
-----
::

    python3 move.py <deck> <key> --after <key>          # right after that page (and into its section)
    python3 move.py <deck> <key> --before <key>         # right before that page (and into its section)
    python3 move.py <deck> <key> --to <section> [--first | --last]   # default --last
    python3 move.py <deck> --respace <section>          # integrator only: orders 10, 20, 30 ...
    ... [--dry-run]                                     # print what would change, write nothing

Rules
-----
- The new order is a value between the two new neighbors: their midpoint, rounded to the fewest
  decimals (at most 3) that still fall strictly between them.  At the start of a section it is the
  largest multiple of 10 below the first page, at the end the smallest multiple of 10 above the last
  page, and 10 in an empty section.
- When there is no such value (the neighbors differ by less than 0.001 or so), nothing is written and
  the exit code is 2: the integrator then runs ``--respace <section>`` (it edits several page files and
  must run serially).
- Only the two values are replaced; every other byte of the page file stays as it was.
- Wording that depends on the page order ("next slide", "as shown before", ...) found in the moved page
  and in its old and new neighbors (page file and ``notes/<key>.md``) is printed as a WARNING.
- The tool never builds; it prints the build commands to run next.

The page files are read with regular expressions (node is not run).  Files whose name starts with
``_`` (and ``slides/_lib/``) are not pages.  Exit codes: 0 done (or nothing to do), 2 usage or deck error.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
BUILD_JS = ENGINE / "js" / "build.js"
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
# ``section: "x"`` / ``order: 20`` at the start of a line or right after ``{`` or ``,`` (searched in the
# text with comments blanked out, so offsets are those of the original file).
SECTION_RE = re.compile(r"""(?m)(?:^|[{,])[ \t]*section[ \t]*:[ \t]*(["'])([^"'\n]*)\1""")
ORDER_RE = re.compile(r"""(?m)(?:^|[{,])[ \t]*order[ \t]*:[ \t]*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)""")
SECTIONS_RE = re.compile(r"\bsections\s*:\s*\[(.*?)\]", re.S)
STRING_RE = re.compile(r"""(["'])((?:\\.|(?!\1).)*)\1""")
# Order-dependent wording (case-insensitive).
WORDING_RE = re.compile(
    r"\b(?:next|previous|preceding|following|prior|last)\s+(?:slide|page)s?\b"
    r"|\bsee\s+(?:slide|page)s?\b"
    r"|\bas\s+(?:shown|seen|discussed|mentioned|noted)\s+(?:before|above|earlier|previously|below)\b"
    r"|\bon\s+the\s+(?:next|previous|last)\s+(?:slide|page)\b"
    r"|下一页|上一页|前一页|后一页|前页|下页|上页|前文|上文|如前所示|见第",
    re.I)
MAX_DECIMALS = 3
MIN_GAP = 1e-6


class DeckError(Exception):
    """A problem with the deck or the request; printed as ERROR, exit code 2."""


@dataclass
class Page:
    key: str
    path: Path
    section: str
    order: float
    order_text: str


# --------------------------------------------------------------------------- reading
def blank_comments(src: str) -> str:
    """Return ``src`` with JS comments replaced by spaces (newlines kept), so offsets stay valid."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out[i:j] = " " * (j - i)
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out[i:j] = [ch if ch == "\n" else " " for ch in src[i:j]]
            i = j
        else:
            i += 1
    return "".join(out)


def read_text(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:     # newline="": keep CRLF as is
        return fh.read()


def write_text(path: Path, text: str) -> None:
    """Replace ``path`` atomically (temporary file in the same directory, then rename)."""
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.chmod(tmp, path.stat().st_mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_sections(deck: Path) -> list[str]:
    cfg = deck / "deck.config.js"
    if not cfg.is_file():
        raise DeckError(f"deck.config.js not found in {deck}")
    text = blank_comments(read_text(cfg))
    m = SECTIONS_RE.search(text)
    if not m:
        raise DeckError(f"{cfg}: no `sections: [...]` list found")
    body = m.group(1)
    if "[" in body:
        raise DeckError(f"{cfg}: `sections` holds nested lists (the v1 format); v2 lists section names only")
    names = [s.group(2) for s in STRING_RE.finditer(body)]
    if not names:
        raise DeckError(f"{cfg}: `sections` is empty")
    dup = sorted({s for s in names if names.count(s) > 1})
    if dup:
        raise DeckError(f"{cfg}: section names repeat: {', '.join(dup)}")
    return names


def field_spans(text: str):
    """Return (section match, order match) of the first ``section:`` / ``order:`` fields, or None."""
    blank = blank_comments(text)
    return SECTION_RE.search(blank), ORDER_RE.search(blank)


def read_pages(deck: Path, sections: list[str]) -> list[Page]:
    """Read every page file; on any problem raise DeckError listing all of them.  Sorted in deck order."""
    slides = deck / "slides"
    if not slides.is_dir():
        raise DeckError(f"no slides/ directory in {deck}")
    pages, problems = [], []
    for path in sorted(slides.glob("*.js")):
        key = path.stem
        if key.startswith("_") or not path.is_file():
            continue
        rel = path.relative_to(deck)
        if not KEY_RE.match(key):
            problems.append(f"{rel}: key {key!r} does not match {KEY_RE.pattern}")
            continue
        text = read_text(path)
        sec_m, ord_m = field_spans(text)
        if not sec_m:
            problems.append(f"{rel}: no `section: \"...\"` field")
        if not ord_m:
            problems.append(f"{rel}: no numeric `order: ...` field")
        if not (sec_m and ord_m):
            continue
        section = text[sec_m.start(2):sec_m.end(2)]
        if section not in sections:
            problems.append(f"{rel}: section {section!r} is not in deck.config.js sections")
            continue
        order_text = text[ord_m.start(1):ord_m.end(1)]
        pages.append(Page(key, path, section, float(order_text), order_text))
    if problems:
        raise DeckError("problems in the page files:\n  " + "\n  ".join(problems))
    rank = {s: i for i, s in enumerate(sections)}
    pages.sort(key=lambda p: (rank[p.section], p.order, p.key))
    return pages


def warn_ties(pages: list[Page]) -> None:
    seen: dict[tuple[str, float], str] = {}
    for p in pages:
        other = seen.setdefault((p.section, p.order), p.key)
        if other != p.key:
            print(f"WARNING: {other} and {p.key} share order {fmt(p.order)} in section {p.section!r} "
                  f"(build.js stops on this)")


# --------------------------------------------------------------------------- orders
def fmt(x: float) -> str:
    if float(x).is_integer():
        return str(int(x))
    return f"{x:.{MAX_DECIMALS}f}".rstrip("0").rstrip(".")


def between(prev: float | None, nxt: float | None) -> float | None:
    """A tidy order strictly between two neighbors (None = open end); None when there is no gap."""
    if prev is None and nxt is None:
        return 10.0
    if prev is None:
        return math.ceil(nxt / 10) * 10 - 10.0
    if nxt is None:
        return math.floor(prev / 10) * 10 + 10.0
    if nxt - prev < MIN_GAP:
        return None
    mid = (prev + nxt) / 2
    for decimals in range(MAX_DECIMALS + 1):
        c = round(mid, decimals)
        if prev < c < nxt:
            return float(c)
    return None


def replace_fields(text: str, section: str | None, order: str | None) -> str:
    """Return ``text`` with the section and/or order value replaced; nothing else changes."""
    sec_m, ord_m = field_spans(text)
    edits = []
    if section is not None:
        edits.append((sec_m.start(2), sec_m.end(2), section))
    if order is not None:
        edits.append((ord_m.start(1), ord_m.end(1), order))
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    return text


# --------------------------------------------------------------------------- reporting
def neighbors(pages: list[Page], key: str) -> list[str]:
    i = [p.key for p in pages].index(key)
    return [pages[j].key for j in (i - 1, i + 1) if 0 <= j < len(pages)]


def wording_warnings(deck: Path, keys: list[str]) -> list[str]:
    out = []
    for key in keys:
        for path in (deck / "slides" / f"{key}.js", deck / "notes" / f"{key}.md"):
            if not path.is_file():
                continue
            for lineno, line in enumerate(read_text(path).splitlines(), 1):
                hits = sorted({m.group(0) for m in WORDING_RE.finditer(line)})
                if hits:
                    out.append(f"{path.relative_to(deck)}:{lineno}: {', '.join(repr(h) for h in hits)}: "
                               f"{line.strip()[:120]}")
    return out


def next_steps(deck: Path, key: str | None) -> None:
    print("\nNext (not run by move.py):")
    print(f"  node {BUILD_JS} {deck} --list")
    if key:
        print(f"  node {BUILD_JS} {deck} --only {key} --out <scratchpad>/{key}.pptx --png")


# --------------------------------------------------------------------------- commands
def cmd_move(deck: Path, sections: list[str], pages: list[Page], key: str, args) -> int:
    by_key = {p.key: p for p in pages}
    if key not in by_key:
        raise DeckError(f"no page {key!r} (slides/{key}.js)")
    moved = by_key[key]
    anchor_key = args.after or args.before
    if anchor_key is not None:
        if anchor_key == key:
            raise DeckError("a page cannot be moved relative to itself")
        if anchor_key not in by_key:
            raise DeckError(f"no page {anchor_key!r} (slides/{anchor_key}.js)")
        target = by_key[anchor_key].section
    else:
        target = args.to
        if target not in sections:
            raise DeckError(f"section {target!r} is not in deck.config.js sections: {', '.join(sections)}")

    others = [p for p in pages if p.key != key and p.section == target]       # already in order
    if args.after:
        idx = [p.key for p in others].index(args.after) + 1
    elif args.before:
        idx = [p.key for p in others].index(args.before)
    else:
        idx = 0 if args.first else len(others)
    prev = others[idx - 1].order if idx > 0 else None
    nxt = others[idx].order if idx < len(others) else None

    old_pos = pages.index(moved) + 1
    if (moved.section == target and (prev is None or prev < moved.order)
            and (nxt is None or moved.order < nxt)):
        print(f"{key} is already there: section {target!r}, order {moved.order_text}, deck position {old_pos}. "
              f"Nothing to change.")
        return 0

    new_order = between(prev, nxt)
    if new_order is None:
        print(f"ERROR: no free order between {fmt(prev)} ({others[idx - 1].key}) and {fmt(nxt)} "
              f"({others[idx].key}) in section {target!r}; nothing written.\n"
              f"Ask the integrator to run (serially, it edits several page files):\n"
              f"  python3 {Path(__file__).resolve()} {deck} --respace {target}\n"
              f"then run this move again.", file=sys.stderr)
        return 2

    new_text_order = fmt(new_order)
    after_pages = [p for p in pages if p.key != key]
    after_pages.append(Page(key, moved.path, target, new_order, new_text_order))
    rank = {s: i for i, s in enumerate(sections)}
    after_pages.sort(key=lambda p: (rank[p.section], p.order, p.key))
    new_pos = [p.key for p in after_pages].index(key) + 1

    print(f"{key}  ({moved.path.relative_to(deck)})")
    print(f"  section : {moved.section} -> {target}" if target != moved.section
          else f"  section : {target} (unchanged)")
    print(f"  order   : {moved.order_text} -> {new_text_order}")
    print(f"  position: {old_pos} -> {new_pos} of {len(pages)}")
    old_nb, new_nb = neighbors(pages, key), neighbors(after_pages, key)
    print(f"  neighbors before: {', '.join(old_nb) or '-'};  after: {', '.join(new_nb) or '-'}")

    scan = [key] + [k for k in old_nb + new_nb if k != key]
    scan = list(dict.fromkeys(scan))
    for w in wording_warnings(deck, scan):
        print(f"WARNING wording that depends on the page order: {w}")

    if args.dry_run:
        print("(dry run: nothing written)")
    else:
        text = read_text(moved.path)
        new = replace_fields(text, target if target != moved.section else None, new_text_order)
        write_text(moved.path, new)
        print(f"wrote {moved.path}")
    next_steps(deck, key)
    return 0


def cmd_respace(deck: Path, sections: list[str], pages: list[Page], section: str, dry_run: bool) -> int:
    if section not in sections:
        raise DeckError(f"section {section!r} is not in deck.config.js sections: {', '.join(sections)}")
    sec_pages = [p for p in pages if p.section == section]
    changes = []
    for i, p in enumerate(sec_pages, 1):
        new = 10.0 * i
        if new != p.order:
            changes.append((p, fmt(new)))
    print(f"WARNING: --respace is an integrator-only step that edits {len(changes)} page file(s) at once; "
          f"run it serially, while no other agent moves or edits pages of section {section!r}.")
    if not sec_pages:
        print(f"section {section!r} has no pages")
        return 0
    for i, p in enumerate(sec_pages, 1):
        new = fmt(10.0 * i)
        mark = "" if new == fmt(p.order) else "   (changed)"
        print(f"  {p.key:<24} {p.order_text:>8} -> {new:<6}{mark}")
    if not changes:
        print("orders are already 10, 20, 30 ...; nothing to change")
    elif dry_run:
        print("(dry run: nothing written)")
    else:
        for p, new in changes:
            write_text(p.path, replace_fields(read_text(p.path), None, new))
        print(f"wrote {len(changes)} file(s)")
    next_steps(deck, None)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="move.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", type=Path, help="deck directory (holds deck.config.js and slides/)")
    ap.add_argument("key", nargs="?", help="key of the page to move (= slides/<key>.js)")
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--after", metavar="KEY", help="put the page right after this page (its section)")
    where.add_argument("--before", metavar="KEY", help="put the page right before this page (its section)")
    where.add_argument("--to", metavar="SECTION", help="put the page into this section (last unless --first)")
    where.add_argument("--respace", metavar="SECTION",
                       help="integrator only: renumber this section to 10, 20, 30 ... (edits several files)")
    end = ap.add_mutually_exclusive_group()
    end.add_argument("--first", action="store_true", help="with --to: first page of the section")
    end.add_argument("--last", action="store_true", help="with --to: last page of the section (default)")
    ap.add_argument("--dry-run", action="store_true", help="print the change, write nothing")
    args = ap.parse_args(argv)

    if args.respace is not None and args.key:
        ap.error("--respace takes no page key")
    if args.respace is None and not args.key:
        ap.error("give the key of the page to move")
    if (args.first or args.last) and args.to is None:
        ap.error("--first / --last only go with --to")

    deck = args.deck
    try:
        sections = read_sections(deck)
        pages = read_pages(deck, sections)
        warn_ties(pages)
        if args.respace is not None:
            return cmd_respace(deck, sections, pages, args.respace, args.dry_run)
        return cmd_move(deck, sections, pages, args.key, args)
    except DeckError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

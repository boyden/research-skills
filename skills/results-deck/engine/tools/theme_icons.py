#!/usr/bin/env python3
"""Render the icons a deck uses in its theme's colors (engine/SPEC.md section 5.1, "icons follow the theme").

Usage::

    python3 theme_icons.py <deck> [--all] [--size 512] [--dry-run]

The theme directory is ``theme:`` of <deck>/deck.config.js (default <deck>/theme); its theme.json gives
``color.text`` (grey variant) and ``color.accent`` (accent variant). The icon library is ``iconDir:``
(null: research-skills/examples/icons), with <source>/<name>.svg files and a manifest.csv.

Which icons: every ``icon(<slide>, "<source>/<name>", ...)`` string literal in <deck>/slides/*.js and
<deck>/slides/_lib/*.js; calls whose name is not a plain string literal are reported and left out.
``--all`` takes every icon of the library's manifest.csv instead.

Output, read by icon() in engine/js/primitives.js before it falls back to <iconDir>/png/:

    <theme>/icons/png/<source>/<name>.png          single-color icons in color.text
    <theme>/icons/png/<source>/<name>_accent.png   single-color icons in color.accent
    <theme>/icons/png/<source>/<name>.png          multi-color icons: <iconDir>/png/... copied as is
                                                   (rendered in their own colors when that PNG is missing)

Single-color vs multi-color and the recoloring follow examples/icons/render_pngs.py (see svg_raster.py).
Every listed PNG is (re)written on each run, since it depends on the theme's colors. ``--dry-run`` prints
the plan and writes nothing.
Exit codes: 0 done, 1 some icon failed to render, 2 usage error (no deck.config.js / theme.json, no
headless Chrome).
"""

import argparse
import concurrent.futures as cf
import csv
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svg_raster  # noqa: E402

RS_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ICON_DIR = RS_ROOT / "examples" / "icons"

# icon(<first argument>, <second argument> ...: the second argument is captured as written.
CALL_RE = re.compile(r"(?<![\w$.])(?:[\w$]+\.)?icon\s*\(\s*[^,()]+,\s*([^,()]+)")
LITERAL_RE = re.compile(r"""^(["'`])([\w.-]+/[\w.-]+)\1$""")


def config_value(text, key):
    """Value of ``key:`` in deck.config.js: a string, None for null, or ... when absent."""
    m = re.search(rf"""(?<![\w$]){key}\s*:\s*(null|"([^"]*)"|'([^']*)')""", text)
    if not m:
        return ...
    if m.group(1) == "null":
        return None
    return m.group(2) if m.group(2) is not None else m.group(3)


def deck_dirs(deck):
    """(theme dir, icon dir) of a deck, from deck.config.js."""
    text = (deck / "deck.config.js").read_text(encoding="utf-8")
    theme = config_value(text, "theme")
    icons = config_value(text, "iconDir")
    theme_dir = (deck / (theme or "theme")).resolve()
    icon_dir = (deck / icons).resolve() if icons else DEFAULT_ICON_DIR
    return theme_dir, icon_dir


def scan_pages(deck):
    """({"<source>/<name>": [file:line, ...]}, [unresolved "file:line: call"]) from the page files."""
    found, dynamic = {}, []
    files = sorted((deck / "slides").glob("*.js")) + sorted((deck / "slides" / "_lib").glob("*.js"))
    for f in files:
        text = f.read_text(encoding="utf-8")
        for m in CALL_RE.finditer(text):
            if re.search(r"function\s*$", text[:m.start()]):  # the definition "function icon(slide, name"
                continue
            line = text.count("\n", 0, m.start()) + 1
            where = f"{f.relative_to(deck)}:{line}"
            arg = m.group(1).strip()
            lit = LITERAL_RE.match(arg)
            if lit and "${" not in arg:
                found.setdefault(lit.group(2), []).append(where)
            else:
                dynamic.append(f"{where}: icon(..., {arg}, ...)")
    return found, dynamic


def manifest_icons(icon_dir):
    with open(icon_dir / "manifest.csv", newline="", encoding="utf-8") as fh:
        return [f"{r['source']}/{r['name']}" for r in csv.DictReader(fh)]


def plan(names, icon_dir, out_root, grey, accent):
    """(jobs, skipped): jobs are (label, kind, src, out, color) with kind "render" / "copy"."""
    jobs, skipped = [], []
    for name in names:
        svg = icon_dir / f"{name}.svg"
        if not svg.exists():
            skipped.append(f"{name}: no {svg}")
            continue
        out = out_root / f"{name}.png"
        if svg_raster.is_single_color(svg.read_text(encoding="utf-8")):
            jobs.append((name, "render", svg, out, grey))
            jobs.append((f"{name}_accent", "render", svg, out_root / f"{name}_accent.png", accent))
        else:
            orig = icon_dir / "png" / f"{name}.png"
            if orig.exists():
                jobs.append((name, "copy", orig, out, None))
            else:
                jobs.append((name, "render", svg, out, None))
            skipped.append(f"{name}_accent: multi-color icon, no accent variant")
    return jobs, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", type=Path, help="deck directory (with deck.config.js)")
    ap.add_argument("--all", action="store_true", help="every icon in the icon library's manifest.csv")
    ap.add_argument("--size", type=int, default=512, help="PNG side in px (default 512)")
    ap.add_argument("--dry-run", action="store_true", help="print what would be written; write nothing")
    ap.add_argument("--workers", type=int, default=4, help="parallel Chrome processes (default 4)")
    args = ap.parse_args(argv)

    deck = args.deck.resolve()
    if not (deck / "deck.config.js").exists():
        print(f"ERROR: {deck / 'deck.config.js'} not found", file=sys.stderr)
        return 2
    theme_dir, icon_dir = deck_dirs(deck)
    theme_json = theme_dir / "theme.json"
    engine_themes = (Path(__file__).resolve().parent.parent / "themes").resolve()
    if engine_themes in theme_dir.parents and not args.dry_run:
        # A shared engine theme (the example decks point at themes/neutral): writing there would change the
        # icons of every deck that uses it. Give the deck its own theme dir (copy the theme) first.
        print(f"ERROR: {theme_dir} is an engine theme shared by other decks; copy it into the deck "
              f"(e.g. <deck>/theme) and point deck.config.js theme at the copy", file=sys.stderr)
        return 2
    if not theme_json.exists():
        print(f"ERROR: {theme_json} not found (theme_icons writes into the deck's own theme directory)",
              file=sys.stderr)
        return 2
    color = json.loads(theme_json.read_text(encoding="utf-8")).get("color", {})
    try:
        grey, accent = svg_raster.hex_color(color["text"]), svg_raster.hex_color(color["accent"])
    except (KeyError, ValueError) as e:
        print(f"ERROR: {theme_json}: color.text / color.accent: {e}", file=sys.stderr)
        return 2
    print(f"theme {theme_dir} (text {grey}, accent {accent}); icons from {icon_dir}")

    if args.all:
        names, dynamic = manifest_icons(icon_dir), []
        print(f"{len(names)} icons in {icon_dir / 'manifest.csv'}")
    else:
        used, dynamic = scan_pages(deck)
        names = sorted(used)
        print(f"{len(names)} icon(s) named in the page files")
        for n in names:
            print(f"  {n}  ({', '.join(used[n])})")
    for d in dynamic:
        print(f"NOTE: cannot resolve {d}; pass --all or render it by hand")

    out_root = theme_dir / "icons" / "png"
    jobs, skipped = plan(names, icon_dir, out_root, grey, accent)
    if args.dry_run:
        for label, kind, src, out, col in jobs:
            print(f"would {'copy' if kind == 'copy' else 'render'} {label} -> {out}"
                  + (f" ({col})" if col else ""))
        for s in skipped:
            print(f"skip {s}")
        print(f"dry run: {len(jobs)} PNG(s) planned, nothing written")
        return 0

    chrome = svg_raster.find_chrome()
    if not chrome and any(kind == "render" for _l, kind, *_r in jobs):
        print("ERROR: no headless Chrome found (set DECK_CHROME or install google-chrome / chromium)",
              file=sys.stderr)
        return 2

    def run(job):
        label, kind, src, out, col = job
        out.parent.mkdir(parents=True, exist_ok=True)
        if kind == "copy":
            shutil.copyfile(src, out)
        else:
            svg_raster.rasterize(src, out, width=args.size, height=args.size, color=col, chrome=chrome)
        return f"{'copied' if kind == 'copy' else 'wrote'} {out}" + (f" ({col})" if col else "")

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for fut, job in [(ex.submit(run, j), j) for j in jobs]:
            try:
                print(fut.result())
            except (OSError, ValueError, RuntimeError) as e:
                failed += 1
                print(f"FAILED {job[0]}: {e}", file=sys.stderr)
    for s in skipped:
        print(f"skipped {s}")
    print(f"{len(jobs) - failed} PNG(s) written into {out_root}, {len(skipped)} skipped, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

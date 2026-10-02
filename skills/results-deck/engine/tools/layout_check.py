#!/usr/bin/env python3
"""Find text that is hidden behind a picture or collides with a picture / other text in a deck PDF.

Why: the deck is previewed as a PDF made by LibreOffice, which may lack the template font and substitute a
wider one. Long titles then wrap to a second line, and a figure that is drawn later (higher in the z-order)
covers it. This tool combines two sources, both read-only::

    pdftotext -bbox-layout   rendered text lines and their boxes (points) in the PDF (poppler)
    pptx XML                 picture boxes (EMU -> points), text-shape boxes and the z-order of both

Checks, per page. A title line is a line in the top 2 in whose box is at least 0.85 x the theme's title size
(``size.title`` of the deck theme, default 28 pt) tall:

    HIDDEN-TITLE    a title line intersects a picture that is above the title's text shape in the z-order
    TITLE-OVER-PIC  a title line intersects a picture that is below the title (visible, but a collision)
    TITLE-WRAP      the title wraps to 2+ lines; the gap to the next element below it (picture top or other
                    text line, whichever overlaps in x and is nearest) is reported; gap < 0 is a collision
    HIDDEN-TEXT     any other text line intersects (> tol in x and y) a picture that is above its text shape
    TEXT-OVER-PIC   same, picture below the text (visible text over a picture)
    TEXT-OVER-TEXT  two text lines whose boxes overlap by more than tol in x and 40 % of the smaller line
                    height in y (adjacent lines of one paragraph overlap less than that)

The z-order of a PDF line is recovered by matching the line's text to a pptx text shape (text contained in the
shape's text, line starts inside the shape's x-range); a line that matches no shape counts as possibly hidden.
Pictures drawn by a slide on purpose over other text (icons in a table column, tiles in a card) show up as
TEXT-OVER-PIC when they cover text; look at the picture. Expect a few false positives: the PDF boxes are font
boxes (a line box is taller than its glyphs), the PNG may have a transparent margin, and a wrapped title that
ends above the figure's top margin is reported as TITLE-WRAP only. The rendered page (``--png-dir``) is the
final word.

Usage::

    python3 layout_check.py <deck dir>                       the wip pptx / pdf / pages.json of the deck
    python3 layout_check.py <deck dir> --pages 7 8 --png-dir /tmp/x
    python3 layout_check.py --pptx a.pptx --pdf a.pdf        any pair (no deck directory needed)

Defaults come from ``<deck>/deck.config.js``, read with regular expressions (node is not run): ``name:`` and
``outDir:`` give ``<deck>/<outDir>/<name>_wip.{pptx,pdf,pages.json}``; ``theme:`` gives the theme directory
whose theme.json supplies ``size.title`` (fallback: engine/themes/neutral, then 28 pt).
Options: ``--pages N ...`` (only these pages), ``--pages-json`` (titles and keys), ``--png-dir DIR`` (render the
flagged pages there with ``pdftoppm -r 60``, file ``page_<NN>.png``), ``--tol`` (overlap threshold, points).

Exit codes: 0 clean (or only TITLE-WRAP with a gap of 4 pt or more), 1 problems found, 2 usage error
(pdftotext missing, input files missing or unreadable).
"""

import argparse
import json
import posixpath
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
NEUTRAL = ENGINE / "themes" / "neutral" / "theme.json"

EMU_PER_PT = 12700.0
DEFAULT_TITLE_PT = 28.0
TITLE_FRAC = 0.85  # a line box at least this share of the title size tall is a title line
TITLE_MAX_Y = 144.0  # title lines start in the top 2 in
TEXT_Y_FRAC = 0.4  # text-over-text: y overlap as a fraction of the smaller line height
OK_GAP = 4.0  # a wrapped title with at least this gap (points) to the next element is only informative

NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_H = "{http://www.w3.org/1999/xhtml}"


class UsageError(Exception):
    pass


@dataclass
class Box:
    x0: float
    y0: float
    x1: float
    y1: float
    z: int = -1  # position in the slide's shape tree (higher = drawn later = on top)
    text: str = ""  # text shapes: the flattened text without whitespace
    name: str = ""  # pictures: image file name

    def overlap(self, o):
        """(dx, dy) overlap in points; negative = gap."""
        return min(self.x1, o.x1) - max(self.x0, o.x0), min(self.y1, o.y1) - max(self.y0, o.y0)


@dataclass
class Line:
    box: Box
    text: str
    shape_z: int = -1  # z of the matched pptx text shape, -1 if unmatched
    is_title: bool = False


@dataclass
class Issue:
    page: int
    kind: str
    detail: str
    severe: bool = True


def squash(s):
    return re.sub(r"\s+", "", s)


# ---- deck defaults ---------------------------------------------------------------------------------

def config_field(text, key):
    """A string field of deck.config.js (``key: "value"`` at the start of a line), or None."""
    m = re.search(rf"^\s*{key}\s*:\s*[\"']([^\"']*)[\"']", text, re.M)
    return m.group(1) if m else None


def deck_defaults(deck):
    """(pptx, pdf, pages.json, theme.json or None) for a deck directory."""
    cfg = deck / "deck.config.js"
    if not cfg.exists():
        raise UsageError(f"{cfg} not found; pass --pptx and --pdf")
    text = cfg.read_text(encoding="utf-8")
    name = config_field(text, "name")
    if not name:
        raise UsageError(f"no name: field in {cfg}; pass --pptx and --pdf")
    out = deck / (config_field(text, "outDir") or "output")
    # Same rule as build.js: <deck>/<theme>, default <deck>/theme (neutral is the fallback in title_size()).
    theme_json = deck / (config_field(text, "theme") or "theme") / "theme.json"
    return out / f"{name}_wip.pptx", out / f"{name}_wip.pdf", out / f"{name}_wip.pages.json", theme_json


def title_size(theme_json):
    """(size.title in points, where it came from)."""
    for path in (theme_json, NEUTRAL):
        if path and path.exists():
            try:
                return float(json.loads(path.read_text(encoding="utf-8"))["size"]["title"]), str(path)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
    return DEFAULT_TITLE_PT, "default"


# ---- pptx ------------------------------------------------------------------------------------------

def rels_of(z, part):
    d, base = posixpath.split(part)
    name = posixpath.join(d, "_rels", base + ".rels")
    out = {}
    if name not in z.namelist():
        return out
    for r in ET.fromstring(z.read(name)).iter(f"{NS_PKG_REL}Relationship"):
        target = r.get("Target", "")
        out[r.get("Id")] = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(d, target))
    return out


def xfrm_pt(xfrm):
    if xfrm is None:
        return None
    off, ext = xfrm.find(f"{NS_A}off"), xfrm.find(f"{NS_A}ext")
    if off is None or ext is None:
        return None
    x, y = int(off.get("x")) / EMU_PER_PT, int(off.get("y")) / EMU_PER_PT
    return x, y, x + int(ext.get("cx")) / EMU_PER_PT, y + int(ext.get("cy")) / EMU_PER_PT


def read_pptx(path):
    """(slide width in points, {page: (pictures, text shapes)}) with boxes in points; pages in deck order."""
    out = {}
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find(f"{NS_P}sldSz")
        width = int(sz.get("cx")) / EMU_PER_PT if sz is not None else 960.0
        pres_rels = rels_of(z, "ppt/presentation.xml")
        order = [pres_rels.get(s.get(f"{NS_R}id")) for s in pres.iter(f"{NS_P}sldId")]
        order = [p for p in order if p and p in z.namelist()]
        if not order:  # fall back to the file numbers
            order = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                           key=lambda n: int(re.findall(r"\d+", n)[0]))
        for page, part in enumerate(order, start=1):
            rels = rels_of(z, part)
            tree = ET.fromstring(z.read(part)).find(f"{NS_P}cSld/{NS_P}spTree")
            pics, texts = [], []
            for z_idx, el in enumerate(tree):
                tag = el.tag.replace(NS_P, "")
                if tag == "pic":
                    b = xfrm_pt(el.find(f"{NS_P}spPr/{NS_A}xfrm")) or xfrm_pt(el.find(f".//{NS_A}xfrm"))
                    if b is None:
                        continue
                    blip = el.find(f".//{NS_A}blip")
                    target = rels.get(blip.get(f"{NS_R}embed") if blip is not None else None, "")
                    pics.append(Box(*b, z_idx, name=posixpath.basename(target)))
                elif tag in ("sp", "graphicFrame"):
                    t = squash("".join(a.text or "" for a in el.iter(f"{NS_A}t")))
                    if not t:
                        continue
                    xfrm = el.find(f"{NS_P}spPr/{NS_A}xfrm") if tag == "sp" else el.find(f"{NS_P}xfrm")
                    b = xfrm_pt(xfrm)
                    if b is None:
                        continue
                    texts.append(Box(*b, z_idx, text=t))
            out[page] = (pics, texts)
    return width, out


# ---- pdf -------------------------------------------------------------------------------------------

def read_pdf_lines(path, first=None, last=None):
    """{page: (width, height, [Line])} from ``pdftotext -bbox-layout``."""
    cmd = ["pdftotext", "-bbox-layout"]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    res = subprocess.run(cmd + [str(path), "-"], capture_output=True)
    if res.returncode != 0:
        raise UsageError(f"pdftotext failed on {path}: {res.stderr.decode(errors='replace').strip()}")
    root = ET.fromstring(res.stdout)
    pages = {}
    n0 = first or 1
    for i, page in enumerate(root.iter(f"{NS_H}page")):
        lines = []
        for ln in page.iter(f"{NS_H}line"):
            words = [w.text or "" for w in ln.iter(f"{NS_H}word")]
            b = Box(*(float(ln.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")))
            lines.append(Line(b, " ".join(words)))
        pages[n0 + i] = (float(page.get("width")), float(page.get("height")), lines)
    return pages


# ---- checks ----------------------------------------------------------------------------------------

def match_shape(line, texts):
    """z of the pptx text shape the PDF line belongs to, or -1."""
    t = squash(line.text)
    best, best_d = -1, 1e9
    for s in texts:
        if t and t in s.text and s.x0 - 3 <= line.box.x0 <= s.x1 + 3 and line.box.y0 >= s.y0 - 6:
            d = line.box.y0 - s.y0
            if d < best_d:
                best, best_d = s.z, d
    return best


def check_page(page, w_pt, lines, pics, texts, tol, slide_w_pt, title_min_h):
    scale = w_pt / slide_w_pt  # PDF points per slide point
    for ln in lines:
        ln.box.x0, ln.box.x1, ln.box.y0, ln.box.y1 = (v / scale for v in (ln.box.x0, ln.box.x1, ln.box.y0, ln.box.y1))
        ln.shape_z = match_shape(ln, texts)
        ln.is_title = (ln.box.y1 - ln.box.y0) >= title_min_h and ln.box.y0 < TITLE_MAX_Y
    issues = []
    fmt = lambda b: f"[{b.x0:.0f},{b.y0:.0f},{b.x1:.0f},{b.y1:.0f}]"  # noqa: E731

    # lines versus pictures
    for ln in lines:
        for p in pics:
            dx, dy = ln.box.overlap(p)
            if dx <= tol or dy <= tol:
                continue
            hidden = ln.shape_z < 0 or p.z > ln.shape_z
            if ln.is_title:
                kind = "HIDDEN-TITLE" if hidden else "TITLE-OVER-PIC"
            else:
                kind = "HIDDEN-TEXT" if hidden else "TEXT-OVER-PIC"
            issues.append(Issue(page, kind, f"'{ln.text[:40]}' {fmt(ln.box)} x {p.name} {fmt(p)} overlap {dx:.0f}x{dy:.0f} pt"))

    # wrapped title and the gap to the next element
    title = sorted((ln for ln in lines if ln.is_title), key=lambda ln: ln.box.y0)
    if len(title) >= 2:
        # keep the first paragraph block: lines stacked from the first line (x within 4 pt of it)
        block = [title[0]]
        for ln in title[1:]:
            if abs(ln.box.x0 - block[0].box.x0) <= 4 and ln.box.y0 - block[-1].box.y1 < 8:
                block.append(ln)
        if len(block) >= 2:
            bottom = max(ln.box.y1 for ln in block)
            x0, x1 = min(ln.box.x0 for ln in block), max(ln.box.x1 for ln in block)
            cands = []
            for p in pics:
                if p.x1 > x0 and p.x0 < x1 and p.y1 > block[0].box.y0:
                    cands.append((p.y0 - bottom, f"picture {p.name} top {p.y0:.0f}"))
            for ln in lines:
                if ln not in block and not ln.is_title and ln.box.x1 > x0 and ln.box.x0 < x1 and ln.box.y1 > bottom - 1:
                    cands.append((ln.box.y0 - bottom, f"text '{ln.text[:30]}' top {ln.box.y0:.0f}"))
            gap, what = min(cands) if cands else (float("nan"), "nothing below")
            issues.append(Issue(page, "TITLE-WRAP",
                                f"{len(block)} lines, bottom {bottom:.0f} pt; gap {gap:.0f} pt to {what}",
                                severe=not (gap >= OK_GAP or gap != gap)))

    # text over text
    body = [ln for ln in lines if ln.text.strip()]
    for i, a in enumerate(body):
        for b in body[i + 1:]:
            dx, dy = a.box.overlap(b.box)
            hmin = min(a.box.y1 - a.box.y0, b.box.y1 - b.box.y0)
            if dx > tol and dy > TEXT_Y_FRAC * hmin and dy > tol:
                issues.append(Issue(page, "TEXT-OVER-TEXT",
                                    f"'{a.text[:30]}' {fmt(a.box)} x '{b.text[:30]}' {fmt(b.box)} overlap {dx:.0f}x{dy:.0f} pt"))
    return issues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", nargs="?", type=Path, help="deck directory (with deck.config.js)")
    ap.add_argument("--pptx", type=Path, help="default: <deck>/<outDir>/<name>_wip.pptx")
    ap.add_argument("--pdf", type=Path, help="default: <deck>/<outDir>/<name>_wip.pdf")
    ap.add_argument("--pages-json", type=Path, help="titles and keys; default: the wip pages.json")
    ap.add_argument("--pages", type=int, nargs="*", help="only these pages")
    ap.add_argument("--png-dir", type=Path, help="render the flagged pages here (pdftoppm -r 60)")
    ap.add_argument("--tol", type=float, default=3.0, help="overlap threshold in points (default 3)")
    args = ap.parse_args(argv)

    try:
        if not shutil.which("pdftotext"):
            raise UsageError("pdftotext not found; install poppler (poppler-utils) to run layout_check")
        pptx, pdf, pages_json, theme_json = (None,) * 4
        if args.deck:
            pptx, pdf, pages_json, theme_json = deck_defaults(args.deck)
        elif not (args.pptx and args.pdf):
            raise UsageError("give a deck directory, or both --pptx and --pdf")
        pptx, pdf = args.pptx or pptx, args.pdf or pdf
        pages_json = args.pages_json or pages_json or pptx.with_suffix(".pages.json")
        for f in (pptx, pdf):
            if not f.exists():
                raise UsageError(f"{f} not found")
        title_pt, title_src = title_size(theme_json)
        try:
            slide_w_pt, deck = read_pptx(pptx)
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
            raise UsageError(f"cannot read {pptx}: {e}") from e
        first = min(args.pages) if args.pages else None
        last = max(args.pages) if args.pages else None
        pdf_pages = read_pdf_lines(pdf, first, last)
    except UsageError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    meta = {}
    if pages_json.exists():
        try:
            meta = {p["page"]: p for p in json.loads(pages_json.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            print(f"WARNING: cannot read {pages_json}; titles not shown")

    title_min_h = TITLE_FRAC * title_pt
    issues = []
    for page, (w_pt, _h, lines) in sorted(pdf_pages.items()):
        if args.pages and page not in args.pages:
            continue
        pics, texts = deck.get(page, ([], []))
        issues += check_page(page, w_pt, lines, pics, texts, args.tol, slide_w_pt, title_min_h)
        if "title" not in meta.get(page, {}):  # no pages.json: show the title lines found in the PDF
            meta.setdefault(page, {})["title"] = " ".join(ln.text for ln in lines if ln.is_title) or "?"

    n_checked = len([p for p in pdf_pages if not args.pages or p in args.pages])
    print(f"layout_check: {pptx.name} / {pdf.name}; pages checked: {n_checked}; "
          f"title = lines >= {title_min_h:.1f} pt tall in the top 2 in (size.title {title_pt:g} pt, {title_src})")
    if len(pdf_pages) != len(deck) and not args.pages:
        print(f"WARNING: the PDF has {len(pdf_pages)} pages, the pptx {len(deck)} slides; pages may not line up")
    print(f"{'page':>4}  {'key':<18} {'title':<40} {'issue':<15} detail")
    for it in issues:
        m = meta.get(it.page, {})
        key = str(m.get("builder") or m.get("key") or "?")
        print(f"{it.page:>4}  {key[:18]:<18} {str(m.get('title', '?'))[:40]:<40} {it.kind:<15} {it.detail}")
    flagged = sorted({i.page for i in issues})
    by_kind = {}
    for i in issues:
        by_kind.setdefault(i.kind, set()).add(i.page)
    print("pages per issue: " + ("; ".join(f"{k} {len(v)}" for k, v in sorted(by_kind.items())) or "none"))
    print(f"flagged pages: {flagged}")

    if args.png_dir and flagged:
        if not shutil.which("pdftoppm"):
            print("WARNING: pdftoppm not found; no PNGs rendered")
        else:
            args.png_dir.mkdir(parents=True, exist_ok=True)
            for pg in flagged:
                subprocess.run(["pdftoppm", "-r", "60", "-png", "-f", str(pg), "-l", str(pg), "-singlefile",
                                str(pdf), str(args.png_dir / f"page_{pg:02d}")], check=True)
            print(f"rendered {len(flagged)} pages to {args.png_dir}")
    return 1 if any(i.severe for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())

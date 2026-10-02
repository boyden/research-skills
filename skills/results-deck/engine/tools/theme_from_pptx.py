#!/usr/bin/env python3
"""Generate a deck theme (theme.json + picture assets) from a template pptx (engine/SPEC.md section 5.2).

Usage::

    python3 theme_from_pptx.py <template.pptx> --out <deck>/theme [--base <theme.json>] [--force]

Only the standard library is used (zipfile + xml.etree). What is read from the template:

    slide                      ppt/presentation.xml  p:sldSz (EMU / 914400 -> inches, 3 decimals)
    color.background           theme clrScheme lt1
    color.text                 theme clrScheme dk2 (dk1 when dk2 is missing)
    color.accent               theme clrScheme accent1
    color.accentTints          derived from color.accent: mixed with white at 25 %, 50 % and 75 % white,
                               i.e. channel' = channel + (255 - channel) * f, rounded half up, for
                               f = 0.25, 0.5, 0.75 (000000 -> 404040, 808080, BFBFBF)
    font.display / font.body   theme fontScheme majorFont / minorFont latin typeface
    geometry.title             slide master placeholder type="title" (spPr/xfrm)
    geometry.margin            left x of the slide master body placeholder
    asset.logo, geometry.logo  the top-right-most picture of the slide master; when the master has no
                               picture, the picture shared by most layouts (ties: top-right-most)
    asset.titleLogo,           a picture on the title-slide layout (type "title", or a name containing
    geometry.titleSlide.logo   "Title Slide"); the top-most one when there are several
    templatePictures           every picture found on the master and the layouts: {file, svg, box, background,
                               from} (``background``: covers more than half the slide; ``from``: list of the
                               master / layout parts it appears on)

Colors are srgbClr values or the lastClr of a sysClr. Placeholder boxes missing on the master are taken
from the first layout that has one (title-only / title-and-body layouts first). A picture that covers more
than half of the slide counts as a background and is listed but never chosen as a logo. Each picture's
media file is copied into the output directory under its own file name (extension kept); when a picture
has both a raster image and an SVG, the raster is the asset and the SVG is listed next to it. When the
chosen logo or title logo is SVG only, a PNG rendered from it with headless Chrome (svg_raster.py; 600 px
per inch of its box height, aspect ratio kept) is written next to the SVG and becomes the asset; without
Chrome the SVG stays the asset and a WARNING is printed.

Everything else (figure boxes, conclusion, source line, font sizes, plot colors) comes from the base theme
(default: engine/themes/neutral/theme.json, or the built-in copy of its SPEC values when that file does not
exist). ``provenance`` in the output maps every leaf (dotted key) to "template" or "default", and the tool
prints the same split as a two-column report; the "kept default" column needs a human look. A WARNING is
printed when the display or body font is not installed (checked with ``fc-list : family``), because a
LibreOffice preview then substitutes a wider font and lines wrap differently than in PowerPoint.

An existing <out>/theme.json is never overwritten unless --force is given.
Exit codes: 0 written, 2 usage error (unreadable pptx, existing theme.json without --force, bad base).
"""

import argparse
import copy
import itertools
import json
import posixpath
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svg_raster  # noqa: E402

ENGINE = Path(__file__).resolve().parent.parent
NEUTRAL = ENGINE / "themes" / "neutral" / "theme.json"
LOGO_DPI = 600  # an SVG-only logo is rendered to a PNG this many px per inch of its box height

EMU_PER_IN = 914400.0
TINT_WHITE = (0.25, 0.5, 0.75)  # share of white in each accent tint
BACKGROUND_FRAC = 0.5  # a picture covering more than this share of the slide is a background

NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_SVG = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}"

PRESET_COLORS = {"white": "FFFFFF", "black": "000000"}

# The SPEC section 5.1 defaults, used when engine/themes/neutral/theme.json does not exist.
DEFAULT_THEME = {
    "name": "neutral",
    "source": None,
    "slide": {"w": 13.333, "h": 7.5},
    "dpi": 200,
    "color": {
        "background": "FFFFFF", "text": "595959", "ink": "222222", "black": "000000",
        "muted": "7F7F7F", "rule": "D9D9D9", "tint": "F3F3F3",
        "accent": "A51C30", "accentTints": ["C45566", "DD99A3", "F1D3D8"],
    },
    "plot": {"ink": "222222", "muted": "6B6B6B", "grid": "E6E6E6", "low": "C0392B", "high": "2A78D6", "mid": "8A8A8A"},
    "font": {"display": "Arial", "body": "Arial", "serif": "Times New Roman", "plot": ["Arial", "DejaVu Sans"]},
    "size": {"title": 28, "body": 16, "conclusion": 18, "table": 12, "source": 9, "abbr": 9.5, "page": 12,
             "plotBase": 12, "plotMin": 11},
    "geometry": {
        "margin": 0.6,
        "title": [0.59, 0.36, 9.6, 0.6],
        "logo": [10.983, 0.2, 2.0, 0.35],
        "figureTop": 1.1, "full": [12.1, 4.6], "half": [5.9, 4.6], "gap": 0.2,
        "conclusion": {"yFigure": 5.75, "yText": 5.95, "h": 1.05, "indent": 22, "after": 10},
        "source": [0.6, 6.82, 11.683, 0.6],
        "page": [12.363, 7.0, 0.6, 0.3],
        "titleSlide": {"logo": [0.6, 0.3, 2.4, 0.35], "accentBar": [0.6, 2.3, 0.1, 1.86],
                       "accentRule": [0, 6.83, 13.333, 0.05]},
    },
    "asset": {"logo": None, "titleLogo": None},
    "provenance": {},
}


# ---- package helpers -------------------------------------------------------------------------------

def emu_in(v):
    return round(float(v) / EMU_PER_IN, 3)


def read_xml(z, part):
    try:
        return ET.fromstring(z.read(part))
    except KeyError:
        return None


def rels_of(z, part):
    """{rId: (resolved part name, relationship type)} for a package part."""
    d, base = posixpath.split(part)
    root = read_xml(z, posixpath.join(d, "_rels", base + ".rels"))
    out = {}
    if root is None:
        return out
    for r in root.iter(f"{NS_PKG_REL}Relationship"):
        target = r.get("Target", "")
        if r.get("TargetMode") == "External":
            continue
        resolved = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(d, target))
        out[r.get("Id")] = (resolved, r.get("Type", ""))
    return out


def first_of_type(rels, suffix):
    for target, typ in rels.values():
        if typ.endswith(suffix):
            return target
    return None


# ---- reading ---------------------------------------------------------------------------------------

def color_of(el):
    """Hex color of a clrScheme entry (srgbClr, sysClr lastClr or a few preset colors), or None."""
    if el is None:
        return None
    for c in el:
        tag = c.tag.replace(NS_A, "")
        if tag == "srgbClr" and c.get("val"):
            return c.get("val").upper()
        if tag == "sysClr" and c.get("lastClr"):
            return c.get("lastClr").upper()
        if tag == "prstClr" and c.get("val") in PRESET_COLORS:
            return PRESET_COLORS[c.get("val")]
    return None


def tints(accent):
    """Accent mixed with white: one hex color per share of white in TINT_WHITE."""
    rgb = [int(accent[i:i + 2], 16) for i in (0, 2, 4)]
    return ["".join(f"{int(c + (255 - c) * f + 0.5):02X}" for c in rgb) for f in TINT_WHITE]


def xfrm_box(xfrm):
    """[x, y, w, h] in EMU from an a:xfrm (or p:xfrm), or None."""
    if xfrm is None:
        return None
    off, ext = xfrm.find(f"{NS_A}off"), xfrm.find(f"{NS_A}ext")
    if off is None or ext is None:
        return None
    try:
        return [float(off.get("x")), float(off.get("y")), float(ext.get("cx")), float(ext.get("cy"))]
    except (TypeError, ValueError):
        return None


def to_inches(box):
    return [emu_in(v) for v in box]


def placeholders(tree):
    """{(type, idx): box in EMU or None} for the placeholders of a shape tree (default type is "obj")."""
    out = {}
    for sp in tree.iter(f"{NS_P}sp"):
        ph = sp.find(f"{NS_P}nvSpPr/{NS_P}nvPr/{NS_P}ph")
        if ph is None:
            continue
        key = (ph.get("type", "obj"), ph.get("idx"))
        out.setdefault(key, xfrm_box(sp.find(f"{NS_P}spPr/{NS_A}xfrm")))
    return out


def ph_box(phs, types):
    """First box among the placeholders of the given types (any idx)."""
    for t in types:
        for (pt, _idx), box in phs.items():
            if pt == t and box is not None:
                return box
    return None


def pictures(tree, rels, transform=(1.0, 1.0, 0.0, 0.0)):
    """Pictures of a shape tree (groups resolved): dicts {raster, svg, box (EMU)}."""
    sx, sy, tx, ty = transform
    out = []
    for el in tree:
        tag = el.tag.replace(NS_P, "")
        if tag == "pic":
            box = xfrm_box(el.find(f"{NS_P}spPr/{NS_A}xfrm"))
            blip = el.find(f"{NS_P}blipFill/{NS_A}blip")
            if box is None or blip is None:
                continue
            raster = rels.get(blip.get(f"{NS_R}embed"), (None,))[0]
            svg_el = blip.find(f".//{NS_SVG}svgBlip")
            svg = rels.get(svg_el.get(f"{NS_R}embed"), (None,))[0] if svg_el is not None else None
            if not raster and not svg:
                continue
            x, y, w, h = box
            out.append({"raster": raster, "svg": svg, "box": [x * sx + tx, y * sy + ty, w * sx, h * sy]})
        elif tag == "grpSp":
            g = el.find(f"{NS_P}grpSpPr/{NS_A}xfrm")
            inner = transform
            if g is not None:
                box = xfrm_box(g)
                ch_off, ch_ext = g.find(f"{NS_A}chOff"), g.find(f"{NS_A}chExt")
                if box and ch_off is not None and ch_ext is not None:
                    cw, chh = float(ch_ext.get("cx") or 0), float(ch_ext.get("cy") or 0)
                    gx = box[2] / cw if cw else 1.0
                    gy = box[3] / chh if chh else 1.0
                    ox = box[0] - float(ch_off.get("x") or 0) * gx
                    oy = box[1] - float(ch_off.get("y") or 0) * gy
                    inner = (gx * sx, gy * sy, ox * sx + tx, oy * sy + ty)
            out += pictures(el, rels, inner)
    return out


def shape_tree(root):
    return root.find(f"{NS_P}cSld/{NS_P}spTree") if root is not None else None


def is_title_layout(root):
    name = (root.find(f"{NS_P}cSld").get("name") or "") + " " + (root.get("matchingName") or "")
    return root.get("type") == "title" or "title slide" in name.lower()


def read_template(path):
    """Everything theme_from_pptx reads, as a dict (boxes in inches, media as part names)."""
    with zipfile.ZipFile(path) as z:
        info = {"notes": []}
        pres_part = "ppt/presentation.xml"
        pres = read_xml(z, pres_part)
        if pres is None:
            raise ValueError("no ppt/presentation.xml (not a pptx?)")
        sz = pres.find(f"{NS_P}sldSz")
        slide_w = slide_h = None
        if sz is not None and sz.get("cx") and sz.get("cy"):
            slide_w, slide_h = float(sz.get("cx")), float(sz.get("cy"))
            info["slide"] = {"w": emu_in(slide_w), "h": emu_in(slide_h)}

        # master: the first one listed in presentation.xml
        pres_rels = rels_of(z, pres_part)
        master_part = None
        mid = pres.find(f"{NS_P}sldMasterIdLst/{NS_P}sldMasterId")
        if mid is not None and mid.get(f"{NS_R}id") in pres_rels:
            master_part = pres_rels[mid.get(f"{NS_R}id")][0]
        master_part = master_part or first_of_type(pres_rels, "/slideMaster") or "ppt/slideMasters/slideMaster1.xml"
        master = read_xml(z, master_part)
        master_rels = rels_of(z, master_part)
        info["master"] = master_part

        # theme
        theme_part = first_of_type(master_rels, "/theme") or "ppt/theme/theme1.xml"
        theme = read_xml(z, theme_part)
        info["theme"] = theme_part
        if theme is not None:
            cs = theme.find(f".//{NS_A}clrScheme")
            if cs is not None:
                get = lambda k: color_of(cs.find(f"{NS_A}{k}"))  # noqa: E731
                info["background"] = get("lt1")
                info["text"], info["text_from"] = (get("dk2"), "dk2") if get("dk2") else (get("dk1"), "dk1")
                info["accent"] = get("accent1")
            fs = theme.find(f".//{NS_A}fontScheme")
            if fs is not None:
                for key, tag in (("display", "majorFont"), ("body", "minorFont")):
                    latin = fs.find(f"{NS_A}{tag}/{NS_A}latin")
                    if latin is not None and latin.get("typeface"):
                        info[key] = latin.get("typeface")

        # layouts, in the master's order
        layouts = []
        if master is not None:
            for lid in master.iter(f"{NS_P}sldLayoutId"):
                target = master_rels.get(lid.get(f"{NS_R}id"), (None,))[0]
                if target:
                    layouts.append(target)
        if not layouts:
            layouts = sorted(t for t, typ in master_rels.values() if typ.endswith("/slideLayout"))

        # placeholders: master first, a layout as fallback (title-only / title-and-body layouts first)
        mtree = shape_tree(master)
        master_phs = placeholders(mtree) if mtree is not None else {}
        layout_roots = [(lp, read_xml(z, lp)) for lp in layouts]
        layout_roots = [(lp, r) for lp, r in layout_roots if r is not None and shape_tree(r) is not None]
        pref = {"titleOnly": 0, "tx": 1, "obj": 2}
        fallback = sorted(layout_roots, key=lambda lr: pref.get(lr[1].get("type"), 9))
        for key, types in (("title", ("title",)), ("bodyBox", ("body", "obj"))):
            box = ph_box(master_phs, types)
            src = "slide master"
            if box is None:
                for lp, r in fallback:
                    box = ph_box(placeholders(shape_tree(r)), types)
                    if box is not None:
                        src = f"layout {layout_name(r, lp)}"
                        break
            if box is not None:
                info[key] = to_inches(box)
                info[key + "_from"] = src
        # layouts whose title box differs from the master's (informative)
        if "title" in info:
            for lp, r in layout_roots:
                b = ph_box(placeholders(shape_tree(r)), ("title",))
                if b is not None and to_inches(b) != info["title"]:
                    info["notes"].append(f"layout {layout_name(r, lp)} moves the title to {to_inches(b)}")

        # pictures
        slide_area = (slide_w or 12192000.0) * (slide_h or 6858000.0)
        pics = []
        if mtree is not None:
            for p in pictures(mtree, master_rels):
                p["from"] = "master"
                pics.append(p)
        title_layout = None
        for lp, r in layout_roots:
            lname = layout_name(r, lp)
            if title_layout is None and is_title_layout(r):
                title_layout = lname
            for p in pictures(shape_tree(r), rels_of(z, lp)):
                p["from"] = f"layout {lname}"
                p["title_layout"] = is_title_layout(r)
                pics.append(p)
        for p in pics:
            p["background"] = p["box"][2] * p["box"][3] > BACKGROUND_FRAC * slide_area
        info["pictures"] = pics
        info["title_layout"] = title_layout
        info["n_layouts"] = len(layout_roots)
        info["slide_emu"] = (slide_w or 12192000.0, slide_h or 6858000.0)
        info["media"] = {p[k]: z.read(p[k]) for p in pics for k in ("raster", "svg") if p.get(k) and p[k] in z.namelist()}
    return info


def layout_name(root, part):
    name = root.find(f"{NS_P}cSld").get("name")
    return f"'{name}'" if name else posixpath.basename(part)


def top_right(pics, slide_w):
    """The picture whose top-right corner is nearest the slide's top-right corner."""
    return min(pics, key=lambda p: (slide_w - (p["box"][0] + p["box"][2])) ** 2 + p["box"][1] ** 2)


def picture_key(p):
    return p["raster"], p["svg"], tuple(round(v) for v in p["box"])


def unique_pictures(pics):
    """[(picture, [where it appears])]: one entry per media file and box, in first-seen order."""
    groups = {}
    for p in pics:
        groups.setdefault(picture_key(p), (p, []))[1].append(p["from"])
    return list(groups.values())


def choose_logos(info):
    """(logo picture or None, how it was chosen, title-logo picture or None)."""
    slide_w = info["slide_emu"][0]
    cand = [p for p in info["pictures"] if not p["background"]]
    master = [p for p in cand if p["from"] == "master"]
    logo, how = None, ""
    if master:
        logo, how = top_right(master, slide_w), "top-right-most picture of the slide master"
    else:
        layout_pics = [p for p in cand if p["from"] != "master" and not p.get("title_layout")]
        if layout_pics:
            groups = unique_pictures(layout_pics)
            most = max(len(where) for _p, where in groups)
            logo = top_right([p for p, where in groups if len(where) == most], slide_w)
            how = f"no picture on the slide master; picture shared by {most} of {info['n_layouts']} layouts"
    title_pics = [p for p in cand if p.get("title_layout")]
    title_logo = min(title_pics, key=lambda p: (p["box"][1], p["box"][0])) if title_pics else None
    return logo, how, title_logo


# ---- theme assembly --------------------------------------------------------------------------------

def leaves(d, prefix=""):
    """Dotted keys of the leaves of a nested dict (lists are leaves)."""
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and v:
            yield from leaves(v, key + ".")
        else:
            yield key, v


def set_dotted(d, key, value):
    parts = key.split(".")
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = value


def media_name(part):
    return posixpath.basename(part) if part else None


def build_theme(info, base, template_path):
    """(theme dict, {dotted key: value} read from the template)."""
    got = {}
    got["name"] = template_path.stem
    got["source"] = template_path.name
    if "slide" in info:
        got["slide.w"], got["slide.h"] = info["slide"]["w"], info["slide"]["h"]
    for key, field in (("background", "color.background"), ("text", "color.text"), ("accent", "color.accent")):
        if info.get(key):
            got[field] = info[key]
    if info.get("accent"):
        got["color.accentTints"] = tints(info["accent"])
    for key in ("display", "body"):
        if info.get(key):
            got[f"font.{key}"] = info[key]
    if "title" in info:
        got["geometry.title"] = info["title"]
    if "bodyBox" in info:
        got["geometry.margin"] = info["bodyBox"][0]
    logo, _how, title_logo = choose_logos(info)
    if logo:
        got["asset.logo"] = media_name(logo["raster"] or logo["svg"])
        got["geometry.logo"] = to_inches(logo["box"])
    if title_logo:
        got["asset.titleLogo"] = media_name(title_logo["raster"] or title_logo["svg"])
        got["geometry.titleSlide.logo"] = to_inches(title_logo["box"])
    if info["pictures"]:
        got["templatePictures"] = [
            {"file": media_name(p["raster"] or p["svg"]), "svg": media_name(p["svg"]) if p["raster"] else None,
             "box": to_inches(p["box"]), "background": p["background"], "from": where}
            for p, where in unique_pictures(info["pictures"])]

    theme = copy.deepcopy(base)
    theme.pop("provenance", None)
    for key, value in got.items():
        set_dotted(theme, key, value)
    theme["provenance"] = {k: ("template" if k in got else "default") for k, _v in leaves(theme)}
    return theme, got


def rasterize_svg_logos(theme, info, out_dir):
    """Render SVG-only logo / title logo to PNG next to the SVG and point the theme at the PNG.

    Returns {asset key: (svg name, png name or None, (w, h) or error text)}; png None means the SVG
    stays the asset (no Chrome, or rendering failed)."""
    logo, _how, title_logo = choose_logos(info)
    taken = {media_name(p) for p in info["media"]}
    chrome = svg_raster.find_chrome()
    done, result = {}, {}
    for key, pic in (("logo", logo), ("titleLogo", title_logo)):
        if not pic or pic["raster"] or not pic["svg"]:
            continue
        svg = media_name(pic["svg"])
        if svg not in done:
            png = Path(svg).stem + ".png"
            if png in taken:
                png = Path(svg).stem + "_from_svg.png"
            if not chrome:
                done[svg] = (None, "no headless Chrome found (set DECK_CHROME or install google-chrome / chromium)")
            else:
                try:
                    height = max(1, round(to_inches(pic["box"])[3] * LOGO_DPI))
                    size = svg_raster.rasterize(out_dir / svg, out_dir / png, height=height, chrome=chrome)
                    done[svg] = (png, size)
                except (OSError, ValueError, RuntimeError) as e:
                    done[svg] = (None, str(e))
        png, size = done[svg]
        if png:
            theme["asset"][key] = png
        result[key] = (svg, png, size)
    return result


def fmt(v, width):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= width else s[:width - 3] + "..."


def installed_fonts():
    """Set of installed font family names (lower case), or None when fc-list is not available."""
    exe = shutil.which("fc-list")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, ":", "family"], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return None
    return {f.strip().lower() for line in out.splitlines() for f in line.split(",") if f.strip()}


def report(theme, got, info, base, base_label, logos=None):
    tmpl = [f"{k} = {fmt(v, 44)}" for k, v in leaves(theme) if theme["provenance"].get(k) == "template"
            and k != "templatePictures"]
    # kept defaults, grouped by parent key: "geometry.conclusion: yFigure, yText, h"
    groups = {}
    for k, _v in leaves(theme):
        if theme["provenance"].get(k) == "default":
            parent, _, leaf = k.rpartition(".")
            groups.setdefault(parent, []).append(leaf)
    dflt = []
    for parent, names in groups.items():
        if not parent:
            dflt += names
            continue
        line = f"{parent}: "
        for n in names:
            if len(line) + len(n) > 60 and not line.endswith(": "):
                dflt.append(line.rstrip(", ") + ",")
                line = "    "
            line += n + ", "
        dflt.append(line.rstrip(", "))
    w = max([len("from template")] + [len(s) for s in tmpl]) + 2
    print(f"{'from template':<{w}}kept default ({base_label})")
    print(f"{'-' * (w - 2):<{w}}{'-' * 30}")
    for a, b in itertools.zip_longest(tmpl, dflt, fillvalue=""):
        print(f"{a:<{w}}{b}")
    print()

    if info.get("text_from") == "dk1":
        print("NOTE: the theme has no dk2; color.text is dk1.")
    if "title" in info and info.get("title_from") != "slide master":
        print(f"NOTE: geometry.title from {info['title_from']} (the slide master has no title box).")
    for n in info["notes"]:
        print(f"NOTE: {n} (geometry.title keeps the slide master's box).")
    if got.get("color.accent"):
        print(f"NOTE: color.accent is the theme's accent1 ({got['color.accent']}); if the brand color lives in a "
              "logo rather than in the theme, set color.accent and color.accentTints by hand.")
    pics = info["pictures"]
    logo, how, title_logo = choose_logos(info)
    if pics:
        groups = unique_pictures(pics)
        print(f"pictures on the slide master and layouts ({len(groups)} distinct, {len(pics)} placements):")
        for p, where in groups:
            mark = (" <- logo" if logo and picture_key(p) == picture_key(logo) else "") + \
                (" <- titleLogo" if title_logo and picture_key(p) == picture_key(title_logo) else "")
            names = ", ".join(media_name(p[k]) for k in ("raster", "svg") if p.get(k))
            bg = " (background)" if p["background"] else ""
            shown = ", ".join(where[:3]) + (f" and {len(where) - 3} more" if len(where) > 3 else "")
            print(f"  {names:<28} {to_inches(p['box'])}{bg}{mark}  on {shown}")
    if logo:
        print(f"logo: {how}.")
    for key, (svg, png, size) in (logos or {}).items():
        if png:
            print(f"NOTE: the {key} is SVG only; rendered {png} ({size[0]} x {size[1]} px) from {svg} and "
                  f"pointed asset.{key} at it ({svg} is kept).")
        else:
            print(f"WARNING: the {key} is SVG only and was not rendered to PNG ({size}); if a renderer shows "
                  f"it badly, convert it to PNG and point asset.{key} at the PNG.")
    if not logo:
        print("NOTE: no logo picture found on the slide master or the layouts; asset.logo kept from the base.")
    if not title_logo:
        layout = info.get("title_layout")
        print(f"NOTE: no picture on the title-slide layout ({layout or 'no title-slide layout found'}); "
              "asset.titleLogo kept from the base.")
    if "slide" in info:
        bw, bh = base.get("slide", {}).get("w"), base.get("slide", {}).get("h")
        if bw and bh and (abs(info["slide"]["w"] - bw) > 0.05 or abs(info["slide"]["h"] - bh) > 0.05):
            print(f"WARNING: slide size {info['slide']['w']} x {info['slide']['h']} in differs from the base "
                  f"({bw} x {bh}); the default boxes (figure, conclusion, source, page) need checking.")

    fonts = installed_fonts()
    wanted = sorted({got[k] for k in ("font.display", "font.body") if k in got})
    if fonts is None and wanted:
        print("NOTE: fc-list not found; cannot check whether the template fonts are installed.")
    elif fonts is not None:
        missing = [f for f in wanted if f.lower() not in fonts]
        if missing:
            print(f"WARNING: font(s) not installed: {', '.join(missing)}. A LibreOffice preview substitutes a "
                  "wider font, so lines wrap differently than in PowerPoint (font files do not go into the repo).")


def load_base(path):
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8")), str(path)
    if NEUTRAL.exists():
        return json.loads(NEUTRAL.read_text(encoding="utf-8")), "themes/neutral"
    return copy.deepcopy(DEFAULT_THEME), "built-in SPEC defaults"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("template", type=Path, help="template .pptx")
    ap.add_argument("--out", type=Path, required=True, help="theme directory to write (theme.json + pictures)")
    ap.add_argument("--base", type=Path, help="base theme.json (default: engine/themes/neutral/theme.json)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing <out>/theme.json")
    args = ap.parse_args(argv)

    out_json = args.out / "theme.json"
    if out_json.exists() and not args.force:
        print(f"ERROR: {out_json} exists; pass --force to overwrite it.", file=sys.stderr)
        return 2
    try:
        base, base_label = load_base(args.base)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read base theme {args.base}: {e}", file=sys.stderr)
        return 2
    try:
        info = read_template(args.template)
    except (OSError, zipfile.BadZipFile, ValueError, ET.ParseError) as e:
        print(f"ERROR: cannot read {args.template}: {e}", file=sys.stderr)
        return 2

    theme, got = build_theme(info, base, args.template)
    args.out.mkdir(parents=True, exist_ok=True)
    for part, data in info["media"].items():
        (args.out / media_name(part)).write_bytes(data)
    logos = rasterize_svg_logos(theme, info, args.out)
    out_json.write_text(json.dumps(theme, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"theme_from_pptx: {args.template.name} -> {out_json}")
    report(theme, got, info, base, base_label, logos)
    if info["media"]:
        print(f"copied {len(info['media'])} picture file(s) into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

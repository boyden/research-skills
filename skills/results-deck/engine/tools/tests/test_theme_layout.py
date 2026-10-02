"""Tests of engine/tools/theme_from_pptx.py and engine/tools/layout_check.py (standard library unittest).

Run from anywhere:

    python3 -B skills/results-deck/engine/tools/tests/test_theme_layout.py -v

All fixtures are generated here, in temporary directories: minimal OOXML packages written with zipfile
(a template with a slide master, layouts, a theme and pictures; a deck with slides) and a small PDF written by
hand (Helvetica text at known positions). Nothing is written into the repository. The layout_check tests need
pdftotext (poppler) and are skipped without it, except the test of the missing-pdftotext exit code. Two tests
also read examples/slides/output/*.pptx / .pdf read-only when they exist.
"""

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from shutil import which

TESTS = Path(__file__).resolve().parent
TOOLS = TESTS.parent
ENGINE = TOOLS.parent
REPO = ENGINE.parents[2]
THEME_TOOL = TOOLS / "theme_from_pptx.py"
LAYOUT_TOOL = TOOLS / "layout_check.py"
sys.path.insert(0, str(TOOLS))
from svg_raster import find_chrome  # noqa: E402  (an SVG-only logo gets a PNG copy when Chrome is available)
EXAMPLES = REPO / "examples" / "slides" / "output"

sys.dont_write_bytecode = True          # no __pycache__ next to the tools
sys.path.insert(0, str(TOOLS))
import theme_from_pptx  # noqa: E402  # pyright: ignore[reportMissingImports]

EMU_IN = 914400
EMU_PT = 12700
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
REL_T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
SVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
HAS_PDFTOTEXT = which("pdftotext") is not None


def run(tool, *args, env=None):
    return subprocess.run([sys.executable, "-B", str(tool), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", env=env)


# ---- OOXML fixture writers -------------------------------------------------------------------------

def png_bytes(w=4, h=2):
    """A tiny valid grey PNG."""
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x80" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="2"><rect width="10" height="2"/></svg>'


def xfrm(box, unit):
    x, y, w, h = (round(v * unit) for v in box)
    return f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'


def ph(sid, ph_attrs, box=None):
    """A placeholder shape; box in inches or None (no xfrm)."""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="ph{sid}"/><p:cNvSpPr/><p:nvPr><p:ph {ph_attrs}/></p:nvPr>'
            f'</p:nvSpPr><p:spPr>{xfrm(box, EMU_IN) if box else ""}</p:spPr></p:sp>')


def text_sp(sid, box_pt, text):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="t{sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr>{xfrm(box_pt, EMU_PT)}</p:spPr><p:txBody><a:bodyPr/><a:p><a:r><a:t>{text}</a:t></a:r>'
            f'</a:p></p:txBody></p:sp>')


def pic(sid, box, rid=None, svg_rid=None, unit=EMU_IN):
    ext = (f'<a:extLst><a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}"><asvg:svgBlip xmlns:asvg="{SVG_NS}" '
           f'r:embed="{svg_rid}"/></a:ext></a:extLst>') if svg_rid else ""
    embed = f' r:embed="{rid}"' if rid else ""
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="pic{sid}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip{embed}>{ext}</a:blip></p:blipFill><p:spPr>{xfrm(box, unit)}</p:spPr></p:pic>')


def group(sid, box, ch_box, inner):
    x, y, w, h = (round(v * EMU_IN) for v in box)
    cx, cy, cw, chh = (round(v * EMU_IN) for v in ch_box)
    return (f'<p:grpSp><p:nvGrpSpPr><p:cNvPr id="{sid}" name="g{sid}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            f'<p:grpSpPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/><a:chOff x="{cx}" y="{cy}"/>'
            f'<a:chExt cx="{cw}" cy="{chh}"/></a:xfrm></p:grpSpPr>{inner}</p:grpSp>')


def tree(shapes):
    return ('<p:cSld{name}><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr/>' + "".join(shapes) + '</p:spTree></p:cSld>')


def rels(entries):
    """entries: [(rId, type suffix, target)]."""
    body = "".join(f'<Relationship Id="{i}" Type="{REL_T}{t}" Target="{tg}"/>' for i, t, tg in entries)
    return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="{REL_NS}">{body}</Relationships>'


def theme_xml(colors, major, minor):
    """colors: {name: inner color element xml}."""
    cs = "".join(f"<a:{k}>{v}</a:{k}>" for k, v in colors.items())
    return (f'<?xml version="1.0" encoding="UTF-8"?><a:theme {NS} name="Fixture"><a:themeElements>'
            f'<a:clrScheme name="Fixture">{cs}</a:clrScheme><a:fontScheme name="Fixture">'
            f'<a:majorFont><a:latin typeface="{major}"/></a:majorFont>'
            f'<a:minorFont><a:latin typeface="{minor}"/></a:minorFont></a:fontScheme></a:themeElements></a:theme>')


def write_template(path, slide_in, theme, master_shapes, master_media, layouts):
    """A template package. layouts: [(type, name, shapes, media)]; media: [(rId, file name, bytes)]."""
    files = {}
    cx, cy = (round(v * EMU_IN) for v in slide_in)
    layout_ids = "".join(f'<p:sldLayoutId id="{2147483649 + i}" r:id="rIdL{i + 1}"/>' for i in range(len(layouts)))
    files["ppt/presentation.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><p:presentation {NS}><p:sldMasterIdLst>'
        f'<p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldSz cx="{cx}" cy="{cy}"/>'
        f'</p:presentation>')
    files["ppt/_rels/presentation.xml.rels"] = rels([("rId1", "slideMaster", "slideMasters/slideMaster1.xml")])
    files["ppt/theme/theme1.xml"] = theme
    files["ppt/slideMasters/slideMaster1.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><p:sldMaster {NS}>' + tree(master_shapes).replace("{name}", "")
        + f'<p:sldLayoutIdLst>{layout_ids}</p:sldLayoutIdLst></p:sldMaster>')
    mrels = [("rIdT", "theme", "../theme/theme1.xml")]
    mrels += [(f"rIdL{i + 1}", "slideLayout", f"../slideLayouts/slideLayout{i + 1}.xml") for i in range(len(layouts))]
    mrels += [(rid, "image", f"../media/{fn}") for rid, fn, _b in master_media]
    files["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = rels(mrels)
    media = {fn: data for _r, fn, data in master_media}
    for i, (ltype, lname, shapes, lmedia) in enumerate(layouts, start=1):
        files[f"ppt/slideLayouts/slideLayout{i}.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8"?><p:sldLayout {NS} type="{ltype}">'
            + tree(shapes).replace("{name}", f' name="{lname}"') + '</p:sldLayout>')
        lrels = [("rIdM", "slideMaster", "../slideMasters/slideMaster1.xml")]
        lrels += [(rid, "image", f"../media/{fn}") for rid, fn, _b in lmedia]
        files[f"ppt/slideLayouts/_rels/slideLayout{i}.xml.rels"] = rels(lrels)
        media.update({fn: data for _r, fn, data in lmedia})
    for fn, data in media.items():
        files[f"ppt/media/{fn}"] = data
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)


def write_deck_pptx(path, slides, media):
    """A deck package: slides = [[shape xml]] (pictures use rId "rImg" + n); media = {rId: (file, bytes)}."""
    files = {}
    ids = "".join(f'<p:sldId id="{256 + i}" r:id="rIdS{i + 1}"/>' for i in range(len(slides)))
    files["ppt/presentation.xml"] = (
        f'<?xml version="1.0" encoding="UTF-8"?><p:presentation {NS}><p:sldIdLst>{ids}</p:sldIdLst>'
        f'<p:sldSz cx="{960 * EMU_PT}" cy="{540 * EMU_PT}"/></p:presentation>')
    files["ppt/_rels/presentation.xml.rels"] = rels(
        [(f"rIdS{i + 1}", "slide", f"slides/slide{i + 1}.xml") for i in range(len(slides))])
    for i, shapes in enumerate(slides, start=1):
        files[f"ppt/slides/slide{i}.xml"] = (f'<?xml version="1.0" encoding="UTF-8"?><p:sld {NS}>'
                                             + tree(shapes).replace("{name}", "") + '</p:sld>')
        files[f"ppt/slides/_rels/slide{i}.xml.rels"] = rels(
            [(rid, "image", f"../media/{fn}") for rid, (fn, _d) in media.items()])
    for fn, data in media.values():
        files[f"ppt/media/{fn}"] = data
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)


def write_pdf(path, pages, w=960, h=540):
    """A PDF with Helvetica text: pages = [[(x, baseline from top, size, text)]]. Line box ~ baseline - 0.72 size."""
    bodies = {1: b"<< /Type /Catalog /Pages 2 0 R >>", 3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"}
    n, kids = 4, []
    for texts in pages:
        stream = "".join(f"BT /F1 {s} Tf {x} {h - y} Td ({t}) Tj ET\n" for x, y, s, t in texts).encode()
        bodies[n + 1] = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream"
        bodies[n] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Resources << /Font << /F1 3 0 R >> >> "
                     f"/Contents {n + 1} 0 R >>").encode()
        kids.append(n)
        n += 2
    bodies[2] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>".encode()
    out, offs = bytearray(b"%PDF-1.4\n"), {}
    for i in range(1, n):
        offs[i] = len(out)
        out += f"{i} 0 obj\n".encode() + bodies[i] + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {n}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offs[i]:010d} 00000 n \n".encode() for i in range(1, n))
    out += f"trailer\n<< /Size {n} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(path).write_bytes(bytes(out))


# ---- template fixtures -----------------------------------------------------------------------------

def template_a(path):
    """10 x 7.5 in; master with title/body boxes, a top-right logo, a top-left mark and a background;
    a title-slide layout with its own picture; a title-only layout that moves the title."""
    theme = theme_xml({"dk1": '<a:sysClr val="windowText" lastClr="000000"/>',
                       "lt1": '<a:sysClr val="window" lastClr="FEFEFE"/>',
                       "dk2": '<a:srgbClr val="1f2a44"/>', "lt2": '<a:srgbClr val="EEEEEE"/>',
                       "accent1": '<a:srgbClr val="336699"/>'},
                      "Fixture Display Face", "Fixture Body Face")
    master = [ph(2, 'type="title"', [0.5, 0.4, 9.0, 0.8]), ph(3, 'type="body" idx="1"', [0.7, 1.5, 8.6, 5.0]),
              pic(4, [0, 0, 10, 7.5], "rBg"), pic(5, [0.1, 0.1, 0.5, 0.5], "rMark"),
              pic(6, [8.0, 0.1, 1.8, 0.4], "rLogo")]
    master_media = [("rBg", "bg.png", png_bytes()), ("rMark", "mark.png", png_bytes()),
                    ("rLogo", "logo.png", png_bytes())]
    layouts = [("title", "Title Slide", [ph(2, 'type="ctrTitle"'), pic(3, [0.5, 0.5, 3.0, 1.0], "rT")],
                [("rT", "title_logo.png", png_bytes())]),
               ("titleOnly", "Title Only", [ph(2, 'type="title"', [0.3, 0.2, 9.0, 0.8])], [])]
    write_template(path, (10, 7.5), theme, master, master_media, layouts)


def template_b(path):
    """13.333 x 7.5 in; no dk2; master title without a box, body placeholder without a type, no master
    picture; an SVG-only logo inside a group shared by two layouts; a second picture on one layout."""
    theme = theme_xml({"dk1": '<a:srgbClr val="101010"/>', "lt1": '<a:prstClr val="white"/>',
                       "accent1": '<a:srgbClr val="000000"/>'}, "Fixture Display Face", "Fixture Body Face")
    master = [ph(2, 'type="title"'), ph(3, 'idx="1"', [0.8, 1.5, 11.7, 5.0])]
    logo = group(9, [10.0, 0.2, 2.0, 1.0], [0, 0, 4.0, 2.0], pic(10, [2.0, 0.4, 2.0, 0.8], svg_rid="rS"))
    svg = [("rS", "brand.svg", SVG)]
    layouts = [("title", "Title", [ph(2, 'type="ctrTitle"', [1, 2, 10, 2])], []),
               ("titleOnly", "Title Only", [ph(2, 'type="title"', [0.6, 0.3, 9.0, 0.7]), logo], svg),
               ("blank", "Blank", [logo, pic(11, [0.2, 6.8, 1.0, 0.5], "rO")], svg + [("rO", "other.png", png_bytes())])]
    write_template(path, (13.333, 7.5), theme, master, [], layouts)


class ThemeFromPptxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="theme_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def build(self, maker, *extra, name="fixture_template.pptx"):
        src = self.tmp / name
        maker(src)
        out = self.tmp / "theme"
        res = run(THEME_TOOL, src, "--out", out, *extra)
        return res, out

    def test_tints_rule(self):
        self.assertEqual(theme_from_pptx.tints("000000"), ["404040", "808080", "BFBFBF"])
        self.assertEqual(theme_from_pptx.tints("336699"), ["668CB3", "99B3CC", "CCD9E6"])
        self.assertEqual(theme_from_pptx.tints("FFFFFF"), ["FFFFFF"] * 3)

    def test_template_a(self):
        res, out = self.build(template_a)
        self.assertEqual(res.returncode, 0, res.stderr)
        t = json.loads((out / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual(t["name"], "fixture_template")
        self.assertEqual(t["source"], "fixture_template.pptx")
        self.assertEqual(t["slide"], {"w": 10.0, "h": 7.5})
        self.assertEqual(t["color"]["background"], "FEFEFE")      # sysClr lastClr
        self.assertEqual(t["color"]["text"], "1F2A44")            # dk2, upper-cased
        self.assertEqual(t["color"]["accent"], "336699")
        self.assertEqual(t["color"]["accentTints"], theme_from_pptx.tints("336699"))
        self.assertEqual(t["font"]["display"], "Fixture Display Face")
        self.assertEqual(t["font"]["body"], "Fixture Body Face")
        self.assertEqual(t["geometry"]["title"], [0.5, 0.4, 9.0, 0.8])  # the master's, not the layout's
        self.assertEqual(t["geometry"]["margin"], 0.7)
        self.assertEqual(t["asset"]["logo"], "logo.png")         # top-right, not the mark or the background
        self.assertEqual(t["geometry"]["logo"], [8.0, 0.1, 1.8, 0.4])
        self.assertEqual(t["asset"]["titleLogo"], "title_logo.png")
        self.assertEqual(t["geometry"]["titleSlide"]["logo"], [0.5, 0.5, 3.0, 1.0])
        for fn in ("bg.png", "mark.png", "logo.png", "title_logo.png"):
            self.assertTrue((out / fn).exists(), fn)
        pics = {p["file"]: p for p in t["templatePictures"]}
        self.assertTrue(pics["bg.png"]["background"])
        self.assertEqual(pics["title_logo.png"]["from"], ["layout 'Title Slide'"])
        prov = t["provenance"]
        for k in ("slide.w", "color.text", "color.accentTints", "font.body", "geometry.title", "geometry.margin",
                  "asset.logo", "geometry.titleSlide.logo", "name", "source"):
            self.assertEqual(prov[k], "template", k)
        for k in ("dpi", "size.title", "geometry.full", "geometry.conclusion.yFigure", "plot.low", "font.serif",
                  "geometry.titleSlide.accentBar"):
            self.assertEqual(prov[k], "default", k)
        self.assertNotIn("provenance", prov)
        # every leaf of the theme has a provenance entry
        leaves = {k for k, _v in theme_from_pptx.leaves({k: v for k, v in t.items() if k != "provenance"})}
        self.assertEqual(leaves, set(prov))
        # report
        self.assertIn("from template", res.stdout)
        self.assertIn("kept default", res.stdout)
        self.assertIn("moves the title to [0.3, 0.2, 9.0, 0.8]", res.stdout)
        self.assertIn("slide size 10.0 x 7.5 in differs", res.stdout)
        if which("fc-list"):
            self.assertIn("WARNING: font(s) not installed: Fixture Body Face, Fixture Display Face", res.stdout)

    def test_template_b_fallbacks(self):
        res, out = self.build(template_b)
        self.assertEqual(res.returncode, 0, res.stderr)
        t = json.loads((out / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual(t["color"]["text"], "101010")            # dk1 when dk2 is missing
        self.assertEqual(t["color"]["background"], "FFFFFF")      # prstClr white
        self.assertEqual(t["color"]["accentTints"], ["404040", "808080", "BFBFBF"])
        self.assertEqual(t["geometry"]["title"], [0.6, 0.3, 9.0, 0.7])  # master has no box: title-only layout
        self.assertEqual(t["geometry"]["margin"], 0.8)                  # placeholder without a type = obj
        # shared by two layouts, SVG only: rasterized to brand.png when Chrome is found, else kept as SVG
        self.assertEqual(t["asset"]["logo"], "brand.png" if find_chrome() else "brand.svg")
        self.assertEqual(t["geometry"]["logo"], [11.0, 0.4, 1.0, 0.4])  # group transform applied
        self.assertIsNone(t["asset"]["titleLogo"])
        self.assertEqual(t["provenance"]["asset.titleLogo"], "default")
        self.assertTrue((out / "brand.svg").exists())
        self.assertTrue((out / "other.png").exists())
        self.assertIn("no dk2", res.stdout)
        self.assertIn("geometry.title from layout 'Title Only'", res.stdout)
        self.assertIn("picture shared by 2 of 3 layouts", res.stdout)
        self.assertIn("SVG only", res.stdout)
        self.assertIn("no picture on the title-slide layout ('Title')", res.stdout)

    def test_refuses_overwrite_without_force(self):
        res, out = self.build(template_a)
        self.assertEqual(res.returncode, 0, res.stderr)
        (out / "theme.json").write_text("{}", encoding="utf-8")
        res = run(THEME_TOOL, self.tmp / "fixture_template.pptx", "--out", out)
        self.assertEqual(res.returncode, 2)
        self.assertIn("--force", res.stderr)
        self.assertEqual((out / "theme.json").read_text(encoding="utf-8"), "{}")
        res = run(THEME_TOOL, self.tmp / "fixture_template.pptx", "--out", out, "--force")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads((out / "theme.json").read_text(encoding="utf-8"))["color"]["accent"], "336699")

    def test_base_option(self):
        base = json.loads(json.dumps(theme_from_pptx.DEFAULT_THEME))
        base["size"]["title"] = 40
        base["extra"] = {"keep": True}
        (self.tmp / "base.json").write_text(json.dumps(base), encoding="utf-8")
        res, out = self.build(template_a, "--base", self.tmp / "base.json")
        self.assertEqual(res.returncode, 0, res.stderr)
        t = json.loads((out / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual(t["size"]["title"], 40)
        self.assertEqual(t["extra"], {"keep": True})
        self.assertEqual(t["provenance"]["extra.keep"], "default")
        self.assertEqual(t["color"]["accent"], "336699")

    def test_not_a_pptx(self):
        bad = self.tmp / "bad.pptx"
        bad.write_text("not a zip", encoding="utf-8")
        res = run(THEME_TOOL, bad, "--out", self.tmp / "theme")
        self.assertEqual(res.returncode, 2)
        self.assertFalse((self.tmp / "theme" / "theme.json").exists())

    @unittest.skipUnless((EXAMPLES / "results_examples.pptx").exists(), "examples pptx not built")
    def test_example_deck_as_template(self):
        out = self.tmp / "theme"
        res = run(THEME_TOOL, EXAMPLES / "results_examples.pptx", "--out", out)
        self.assertEqual(res.returncode, 0, res.stderr)
        t = json.loads((out / "theme.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(t["slide"]["w"], 13.333, places=2)
        self.assertEqual(t["source"], "results_examples.pptx")


# ---- layout_check ----------------------------------------------------------------------------------

def layout_fixture(root):
    """deck/ with deck.config.js, output/fx_wip.{pptx,pdf,pages.json}; one problem per page."""
    deck = root / "deck"
    (deck / "output").mkdir(parents=True)
    (deck / "deck.config.js").write_text(
        'module.exports = {\n  name: "fx",\n  title: "Fixture",\n  outDir: "output",\n  theme: "theme",\n};\n',
        encoding="utf-8")
    img = {"rImg": ("fig.png", png_bytes())}
    pt = lambda box: pic(90, box, "rImg", unit=EMU_PT)  # noqa: E731
    # text: (x, baseline, size, text); a 28 pt line box is about [baseline - 20, baseline + 6]
    pages = [
        # 1 clean: title, body, a picture to the right
        ([text_sp(2, [35, 30, 700, 50], "Clean Title"), text_sp(3, [35, 180, 400, 40], "Body text here"),
          pt([500, 150, 400, 300])],
         [(40, 60, 28, "Clean Title"), (40, 200, 16, "Body text here")]),
        # 2 the title is drawn first, a picture over it
        ([text_sp(2, [35, 30, 700, 50], "Hidden Title"), pt([100, 30, 300, 100])],
         [(40, 60, 28, "Hidden Title")]),
        # 3 a picture first, text over it
        ([pt([30, 150, 400, 100]), text_sp(3, [35, 180, 400, 40], "Caption over figure")],
         [(40, 200, 16, "Caption over figure")]),
        # 4 two text lines on top of each other
        ([text_sp(2, [35, 280, 300, 40], "Alpha beta gamma"), text_sp(3, [55, 280, 300, 40], "Delta epsilon zeta")],
         [(40, 300, 16, "Alpha beta gamma"), (60, 300, 16, "Delta epsilon zeta")]),
        # 5 a two-line title, picture well below it (informative only)
        ([text_sp(2, [35, 30, 700, 80], "First title line Second title line"), pt([40, 140, 600, 300])],
         [(40, 60, 28, "First title line"), (40, 92, 28, "Second title line")]),
    ]
    write_deck_pptx(deck / "output" / "fx_wip.pptx", [s for s, _t in pages], img)
    write_pdf(deck / "output" / "fx_wip.pdf", [t for _s, t in pages])
    (deck / "output" / "fx_wip.pages.json").write_text(json.dumps(
        [{"page": i + 1, "title": f"Page {i + 1}", "section": "results", "order": 10 * (i + 1),
          "builder": f"sPage{i + 1}"} for i in range(len(pages))]), encoding="utf-8")
    return deck


@unittest.skipUnless(HAS_PDFTOTEXT, "pdftotext (poppler) not installed")
class LayoutCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="layout_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.deck = layout_fixture(self.tmp)

    def kinds(self, out):
        """{page: set of issue kinds} from the report table."""
        got = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) > 4 and parts[0].isdigit() and parts[1].startswith("sPage"):
                kind = next(p for p in parts if p.isupper() and "-" in p)
                got.setdefault(int(parts[0]), set()).add(kind)
        return got

    def test_all_pages(self):
        res = run(LAYOUT_TOOL, self.deck)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("pages checked: 5", res.stdout)
        self.assertIn("size.title 28 pt", res.stdout)
        k = self.kinds(res.stdout)
        self.assertNotIn(1, k)
        self.assertEqual(k[2], {"HIDDEN-TITLE"})
        self.assertEqual(k[3], {"TEXT-OVER-PIC"})
        self.assertEqual(k[4], {"TEXT-OVER-TEXT"})
        self.assertEqual(k[5], {"TITLE-WRAP"})
        self.assertIn("sPage2", res.stdout)                    # key column from pages.json

    def test_clean_pages_exit_zero(self):
        res = run(LAYOUT_TOOL, self.deck, "--pages", 1, 5)    # a wrap with a wide gap is only informative
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("pages checked: 2", res.stdout)
        self.assertEqual(self.kinds(res.stdout), {5: {"TITLE-WRAP"}})

    def test_theme_title_size(self):
        theme = self.deck / "theme"
        theme.mkdir()
        (theme / "theme.json").write_text(json.dumps({"size": {"title": 40}}), encoding="utf-8")
        res = run(LAYOUT_TOOL, self.deck, "--pages", 2)
        self.assertIn("size.title 40 pt", res.stdout)
        self.assertEqual(self.kinds(res.stdout), {2: {"HIDDEN-TEXT"}})  # 28 pt text is no title any more
        self.assertEqual(res.returncode, 1)

    def test_explicit_files_and_png(self):
        out = self.deck / "output"
        png = self.tmp / "png"
        res = run(LAYOUT_TOOL, "--pptx", out / "fx_wip.pptx", "--pdf", out / "fx_wip.pdf", "--pages", 3,
                  "--png-dir", png)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("TEXT-OVER-PIC", res.stdout)
        if which("pdftoppm"):
            self.assertTrue((png / "page_03.png").exists())

    def test_missing_inputs(self):
        self.assertEqual(run(LAYOUT_TOOL).returncode, 2)                       # neither deck nor files
        res = run(LAYOUT_TOOL, self.tmp / "nowhere")
        self.assertEqual(res.returncode, 2)
        self.assertIn("deck.config.js", res.stderr)
        res = run(LAYOUT_TOOL, self.deck, "--pdf", self.tmp / "missing.pdf")
        self.assertEqual(res.returncode, 2)

    @unittest.skipUnless((EXAMPLES / "results_examples.pdf").exists(), "examples not built")
    def test_example_decks_run(self):
        for name in ("results_examples", "narrative_examples"):
            pptx, pdf = EXAMPLES / f"{name}.pptx", EXAMPLES / f"{name}.pdf"
            if not (pptx.exists() and pdf.exists()):
                continue
            res = run(LAYOUT_TOOL, "--pptx", pptx, "--pdf", pdf)
            self.assertIn(res.returncode, (0, 1), res.stderr)
            self.assertIn("pages checked:", res.stdout)


class LayoutCheckNoPopplerTest(unittest.TestCase):
    def test_missing_pdftotext_exits_2(self):
        with tempfile.TemporaryDirectory() as empty:
            res = run(LAYOUT_TOOL, "--pptx", "a.pptx", "--pdf", "a.pdf", env={"PATH": empty})
        self.assertEqual(res.returncode, 2)
        self.assertIn("pdftotext not found", res.stderr)


if __name__ == "__main__":
    unittest.main()

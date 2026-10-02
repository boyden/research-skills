"""Tests of engine/tools/theme_icons.py, engine/tools/svg_raster.py and the SVG-logo rendering of
engine/tools/theme_from_pptx.py (standard library unittest).

Run from anywhere:

    python3 -B skills/results-deck/engine/tools/tests/test_theme_icons.py -v

Fixtures (a deck with deck.config.js, theme/theme.json and page files; small SVGs; a template pptx from
test_theme_layout.template_b) are written into temporary directories; nothing is written into the
repository. The icon library examples/icons/ is read only. Tests that render need headless Chrome
(svg_raster.find_chrome()) and are skipped without it.
"""

import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from collections import Counter
from pathlib import Path

TESTS = Path(__file__).resolve().parent
TOOLS = TESTS.parent
REPO = TOOLS.parents[3]
ICONS = REPO / "examples" / "icons"
THEME_ICONS = TOOLS / "theme_icons.py"
THEME_TOOL = TOOLS / "theme_from_pptx.py"

sys.dont_write_bytecode = True          # no __pycache__ next to the tools
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TESTS))
import svg_raster  # noqa: E402  # pyright: ignore[reportMissingImports]
import theme_icons  # noqa: E402  # pyright: ignore[reportMissingImports]
from test_theme_layout import template_b  # noqa: E402  # pyright: ignore[reportMissingImports]

HAS_CHROME = svg_raster.find_chrome() is not None
ACCENT = "1F4E79"
TEXT = "333333"
MONO = "lucide/bot"
MULTI = "bioicons/glass-slide"


def run(tool, *args, env=None):
    return subprocess.run([sys.executable, "-B", str(tool), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", env=env)


def read_png(path):
    """(width, height, rows of RGBA tuples) of an 8-bit RGB / RGBA non-interlaced PNG."""
    data = Path(path).read_bytes()
    w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", data[16:29])
    assert depth == 8 and not interlace and ctype in (2, 6), (depth, ctype, interlace)
    bpp = 4 if ctype == 6 else 3
    idat, pos = b"", 8
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        if data[pos + 4:pos + 8] == b"IDAT":
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
            if f == 1:
                line[i] = (line[i] + a) & 0xFF
            elif f == 2:
                line[i] = (line[i] + b) & 0xFF
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        rows.append([tuple(line[x * bpp:(x + 1) * bpp]) + ((255,) if bpp == 3 else ())
                     for x in range(w)])
        prev = line
    return w, h, rows


def dominant(path):
    """Most common RGB among (nearly) opaque pixels, and the number of such pixels."""
    _w, _h, rows = read_png(path)
    cnt = Counter(px[:3] for row in rows for px in row if px[3] > 250)
    (rgb, _n), = cnt.most_common(1)
    return rgb, sum(cnt.values())


def rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))


def make_deck(root, pages, lib=None, accent=ACCENT, text=TEXT):
    deck = root / "deck"
    (deck / "slides" / "_lib").mkdir(parents=True)
    (deck / "theme").mkdir()
    (deck / "deck.config.js").write_text(
        'module.exports = {\n  name: "t",\n  iconDir: null,\n  theme: "theme",\n  sections: ["results"],\n};\n',
        encoding="utf-8")
    (deck / "theme" / "theme.json").write_text(
        json.dumps({"name": "t", "color": {"text": text, "accent": accent}}), encoding="utf-8")
    for name, body in pages.items():
        (deck / "slides" / name).write_text(body, encoding="utf-8")
    for name, body in (lib or {}).items():
        (deck / "slides" / "_lib" / name).write_text(body, encoding="utf-8")
    return deck


PAGE = f""""use strict";
module.exports = {{
  section: "results", order: 10,
  build(pres, n, P) {{
    const s = P.newSlide(pres, "Icons", n);
    P.icon(s, "{MONO}", 1, 2, 1.0, "accent");
    P.icon(s,
           "{MONO}", 3, 2, 1.0);
    P.icon(s, '{MULTI}', 5, 2, 1.0);
    const which = "tabler/robot";
    P.icon(s, which, 7, 2, 1.0);
    P.icon(s, `lucide/${{which}}`, 9, 2, 1.0);
    return s;
  }},
}};
"""
LIB = """"use strict";
function icon(slide, name, x, y) { return null; }   // a definition, not a call
const { icon: draw } = require("x");
module.exports = { badge: (P, s) => P.icon(s, "tabler/robot", 0, 0, 0.5, "accent") };
"""


class TestScan(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_scan_pages(self):
        deck = make_deck(self.tmp, {"sIcons.js": PAGE}, {"common.js": LIB})
        found, dynamic = theme_icons.scan_pages(deck)
        self.assertEqual(sorted(found), [MULTI, MONO, "tabler/robot"])
        self.assertEqual(found[MONO], ["slides/sIcons.js:6", "slides/sIcons.js:7"])
        self.assertEqual(found["tabler/robot"], ["slides/_lib/common.js:4"])
        self.assertEqual(len(dynamic), 2, dynamic)
        self.assertTrue(any("which" in d and "sIcons.js:11" in d for d in dynamic), dynamic)
        self.assertTrue(any("${which}" in d for d in dynamic), dynamic)

    def test_deck_dirs(self):
        deck = make_deck(self.tmp, {})
        theme_dir, icon_dir = theme_icons.deck_dirs(deck)
        self.assertEqual(theme_dir, (deck / "theme").resolve())
        self.assertEqual(icon_dir, ICONS.resolve())
        cfg = deck / "deck.config.js"
        cfg.write_text('module.exports = { iconDir: "../lib", theme: "theme_b" };\n', encoding="utf-8")
        theme_dir, icon_dir = theme_icons.deck_dirs(deck)
        self.assertEqual(theme_dir, (deck / "theme_b").resolve())
        self.assertEqual(icon_dir, (self.tmp / "lib").resolve())

    def test_dry_run_writes_nothing(self):
        deck = make_deck(self.tmp, {"sIcons.js": PAGE})
        before = sorted(p.relative_to(deck) for p in deck.rglob("*"))
        res = run(THEME_ICONS, deck, "--dry-run")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(sorted(p.relative_to(deck) for p in deck.rglob("*")), before)
        self.assertIn(f"would render {MONO}_accent", res.stdout)
        self.assertIn(f"#{ACCENT}", res.stdout)
        self.assertIn(f"would copy {MULTI}", res.stdout)
        self.assertIn("cannot resolve", res.stdout)
        res = run(THEME_ICONS, deck, "--dry-run", "--all")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse((deck / "theme" / "icons").exists())

    def test_missing_theme_json(self):
        deck = make_deck(self.tmp, {})
        (deck / "theme" / "theme.json").unlink()
        res = run(THEME_ICONS, deck, "--dry-run")
        self.assertEqual(res.returncode, 2)
        self.assertIn("theme.json", res.stderr)


@unittest.skipUnless(HAS_CHROME, "headless Chrome not found")
class TestRender(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_theme_icons_render(self):
        deck = make_deck(self.tmp, {"sIcons.js": PAGE})
        res = run(THEME_ICONS, deck, "--size", "128")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        out = deck / "theme" / "icons" / "png"
        accent, grey, multi = out / f"{MONO}_accent.png", out / f"{MONO}.png", out / f"{MULTI}.png"
        for p in (accent, grey, multi):
            self.assertTrue(p.exists(), p)
        self.assertFalse((out / f"{MULTI}_accent.png").exists())
        self.assertEqual(svg_raster.png_size(accent.read_bytes()), (128, 128))
        for path, want in ((accent, rgb(ACCENT)), (grey, rgb(TEXT))):
            got, n = dominant(path)
            self.assertGreater(n, 200, path)
            self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(got, want)), (path, got, want))
        # multi-color icons: the library's PNG, copied as is
        self.assertEqual(multi.read_bytes(), (ICONS / "png" / f"{MULTI}.png").read_bytes())
        self.assertIn("skipped bioicons/glass-slide_accent", res.stdout)

    def test_non_square_svg_keeps_aspect(self):
        svg = self.tmp / "wide.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100">'
                       '<rect width="300" height="100" fill="#ff0000"/></svg>', encoding="utf-8")
        png = self.tmp / "wide.png"
        self.assertEqual(svg_raster.rasterize(svg, png, height=60), (180, 60))
        w, h, rows = read_png(png)
        self.assertEqual((w, h), (180, 60))
        # the rect fills the whole image: corners opaque red, so nothing was clipped at the bottom
        for x, y in ((0, 0), (179, 0), (0, 59), (179, 59)):
            self.assertEqual(rows[y][x], (255, 0, 0, 255), (x, y))
        # recoloring a single-color SVG; a width-only request keeps the aspect too
        self.assertEqual(svg_raster.rasterize(svg, png, width=90, color="1F4E79"), (90, 30))
        self.assertEqual(read_png(png)[2][15][45], (31, 78, 121, 255))

    def test_theme_from_pptx_svg_logo_png(self):
        src = self.tmp / "t.pptx"
        template_b(src)
        out = self.tmp / "theme"
        res = run(THEME_TOOL, src, "--out", out)
        self.assertEqual(res.returncode, 0, res.stderr)
        t = json.loads((out / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual(t["asset"]["logo"], "brand.png")
        self.assertTrue((out / "brand.svg").exists())                 # the SVG is kept
        # box [11.0, 0.4, 1.0, 0.4] in -> 0.4 * 600 = 240 px high; SVG 10 x 2 -> 1200 px wide
        self.assertEqual(svg_raster.png_size((out / "brand.png").read_bytes()), (1200, 240))
        self.assertIn("rendered brand.png", res.stdout)
        # without Chrome: the SVG stays the asset, with a WARNING
        env = dict(os.environ, DECK_CHROME="/nonexistent/chrome")
        out2 = self.tmp / "theme2"
        res = run(THEME_TOOL, src, "--out", out2, env=env)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(json.loads((out2 / "theme.json").read_text(encoding="utf-8"))["asset"]["logo"],
                         "brand.svg")
        self.assertIn("WARNING: the logo is SVG only", res.stdout)
        self.assertFalse((out2 / "brand.png").exists())


if __name__ == "__main__":
    unittest.main()

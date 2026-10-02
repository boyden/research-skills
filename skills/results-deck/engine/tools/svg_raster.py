#!/usr/bin/env python3
"""Rasterize an SVG file (optionally recolored) to a transparent PNG with headless Chrome.

Shared by theme_icons.py (theme-colored icons) and theme_from_pptx.py (SVG-only logos). Only the
standard library is used; the browser is ``$DECK_CHROME`` when that is set (and nothing else then), else
the first of google-chrome, chromium-browser, chromium on PATH.

The recoloring rule is the one of examples/icons/render_pngs.py: an SVG counts as single-color when it
uses ``currentColor`` or at most one explicit color (and embeds no ``<image>``); recoloring replaces
``currentColor``, or the one explicit color, or (no explicit color at all) sets ``fill`` on the root
element. Multi-color SVGs are rendered with their own colors.

The SVG on disk is never modified: a copy whose root element has the target width/height (viewBox kept,
or added from the old width/height) is written to a temporary directory and screenshotted. Headless
Chrome's viewport is about 87 px shorter than ``--window-size``, so the window is opened ``PAD`` px taller
than the image and the screenshot is cropped back to the top rows.

Usage::

    python3 svg_raster.py <in.svg> <out.png> [--height PX | --size PX] [--width PX] [--color RRGGBB]

``--height`` alone keeps the SVG's aspect ratio (width derived from the viewBox); ``--size`` is a square.
"""

import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

PAD = 200  # extra window height, cropped off again (see screenshot())

COLOR_RE = re.compile(
    r"""(?:fill|stroke|stop-color|color)\s*[:=]\s*["']?\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|[a-zA-Z]+)""")
NEUTRAL = {"none", "transparent", "currentcolor", "inherit", "url"}


def find_chrome():
    """Path of the headless browser, or None. ``$DECK_CHROME`` (when set) is the only candidate."""
    env = os.environ.get("DECK_CHROME")
    if env:
        return shutil.which(env)
    for name in ("google-chrome", "chromium-browser", "chromium"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


# ---- Colors (same rule as examples/icons/render_pngs.py) -------------------------------------------

def colors(svg):
    """Distinct explicit colors in the SVG (lower case, excluding none / currentColor)."""
    found = {c.lower() for c in COLOR_RE.findall(svg)}
    found = {c for c in found if c not in NEUTRAL}
    expand = {"#fff": "#ffffff", "white": "#ffffff", "#000": "#000000", "black": "#000000"}
    return {expand.get(c, c) for c in found}


def is_single_color(svg):
    """currentColor SVGs, or SVGs drawn in exactly one explicit color (or none at all)."""
    if "currentColor" in svg:
        return True
    if "<image" in svg:  # embedded raster: cannot be recolored
        return False
    return len(colors(svg)) <= 1


def recolor(svg, color):
    """The SVG text drawn in ``color`` ("#RRGGBB"); the caller checks is_single_color() first."""
    if "currentColor" in svg:
        return svg.replace("currentColor", color)
    cols = colors(svg)
    if len(cols) == 1:
        (old,) = cols
        return re.sub(re.escape(old), color, svg, flags=re.I)
    # no explicit color: the default fill is black, so set fill on the root element
    return re.sub(r"<svg\b", f'<svg fill="{color}"', svg, count=1)


def hex_color(c):
    """"1F4E79" / "#1f4e79" -> "#1F4E79"."""
    c = c.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", c):
        raise ValueError(f"not an RRGGBB color: {c!r}")
    return "#" + c.upper()


# ---- Size ------------------------------------------------------------------------------------------

def _num(v):
    m = re.match(r"\s*([0-9.]+)", v or "")
    return float(m.group(1)) if m else None


def _root(svg):
    m = re.search(r"<svg\b[^>]*>", svg, flags=re.S)
    if m is None:
        raise ValueError("no <svg> element")
    return m


def _attr(tag, name):
    m = re.search(rf'\s{name}\s*=\s*["\']([^"\']*)["\']', tag)
    return m.group(1) if m else None


def aspect(svg):
    """Width / height of the SVG: from the viewBox, else from numeric width / height."""
    tag = _root(svg).group(0)
    vb = _attr(tag, "viewBox")
    if vb:
        parts = [float(p) for p in re.split(r"[\s,]+", vb.strip()) if p]
        if len(parts) == 4 and parts[2] > 0 and parts[3] > 0:
            return parts[2] / parts[3]
    w, h = _num(_attr(tag, "width")), _num(_attr(tag, "height"))
    if w and h:
        return w / h
    raise ValueError("SVG has neither viewBox nor numeric width/height")


def resize(svg, width, height):
    """Root <svg>: width/height in px, viewBox kept (added from the old width/height if missing)."""
    m = _root(svg)
    tag = m.group(0)
    w, h = _attr(tag, "width"), _attr(tag, "height")
    new = re.sub(r'\s(width|height)\s*=\s*["\'][^"\']*["\']', "", tag)
    if not re.search(r"viewBox\s*=", new):
        wv, hv = _num(w), _num(h)
        if not (wv and hv):
            raise ValueError("SVG has neither viewBox nor numeric width/height")
        new = new.replace("<svg", f'<svg viewBox="0 0 {wv:g} {hv:g}"', 1)
    new = new.replace("<svg", f'<svg width="{width}" height="{height}"', 1)
    if "xmlns=" not in new:
        new = new.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg[:m.start()] + new + svg[m.end():]


# ---- PNG -------------------------------------------------------------------------------------------

def _chunks(data):
    pos = 8
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        yield data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n


def _chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def png_size(png_bytes):
    """(width, height) from the IHDR chunk."""
    return struct.unpack(">II", png_bytes[16:24])


def crop_top(png_bytes, height):
    """Keep the top ``height`` rows of an 8-bit, non-interlaced PNG (standard library only).

    PNG row filters only refer to earlier rows, so the first rows of the filtered stream can be
    kept as they are."""
    chunks = list(_chunks(png_bytes))
    ihdr = chunks[0][1]
    w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", ihdr)
    if depth != 8 or interlace or ctype not in (2, 6):
        raise ValueError("unexpected PNG format from Chrome")
    if h == height:
        return png_bytes
    if h < height:
        raise ValueError(f"Chrome screenshot is {h} px high, expected at least {height}")
    bpp = 4 if ctype == 6 else 3
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    raw = raw[:height * (1 + w * bpp)]
    new_ihdr = struct.pack(">IIBBBBB", w, height, depth, ctype, 0, 0, 0)
    return (png_bytes[:8] + _chunk(b"IHDR", new_ihdr) + _chunk(b"IDAT", zlib.compress(raw, 9))
            + _chunk(b"IEND", b""))


def screenshot(svg_text, out_png, width, height, chrome):
    """Write ``svg_text`` (already sized to width x height) as a width x height PNG."""
    with tempfile.TemporaryDirectory(prefix="svg_raster_", ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        src = tmp / "image.svg"
        src.write_text(svg_text, encoding="utf-8")
        shot = tmp / "shot.png"
        profile = tmp / "profile"
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--force-device-scale-factor=1",
               "--default-background-color=00000000", "--hide-scrollbars", f"--user-data-dir={profile}",
               f"--window-size={width},{height + PAD}", f"--screenshot={shot}", src.as_uri()]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120, check=False)
        if not shot.exists() or shot.stat().st_size == 0:
            raise RuntimeError(f"Chrome produced no PNG for {out_png}")
        data = crop_top(shot.read_bytes(), height)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_png.write_bytes(data)


def target_size(svg, width=None, height=None):
    """(width, height) in px; a missing side follows the SVG's aspect ratio."""
    if width and height:
        return int(width), int(height)
    a = aspect(svg)
    if height:
        return max(1, round(height * a)), int(height)
    if width:
        return int(width), max(1, round(width / a))
    raise ValueError("give a width, a height or both")


def rasterize(svg_path, out_png, *, width=None, height=None, color=None, chrome=None):
    """Render ``svg_path`` to ``out_png``; returns (width, height) of the PNG.

    ``width`` / ``height``: both for a fixed box (the SVG is letterboxed by its viewBox), one of them to
    keep the SVG's aspect ratio. ``color`` ("RRGGBB" or "#RRGGBB") recolors a single-color SVG and is
    ignored for a multi-color one. ``chrome`` defaults to find_chrome(); RuntimeError when there is none."""
    chrome = chrome or find_chrome()
    if not chrome:
        raise RuntimeError("no headless Chrome found (set DECK_CHROME or install google-chrome / chromium)")
    text = Path(svg_path).read_text(encoding="utf-8")
    if color and is_single_color(text):
        text = recolor(text, hex_color(color))
    w, h = target_size(text, width, height)
    screenshot(resize(text, w, h), out_png, w, h, chrome)
    return w, h


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("svg", type=Path)
    ap.add_argument("png", type=Path)
    ap.add_argument("--height", type=int, help="PNG height in px (width follows the aspect ratio)")
    ap.add_argument("--width", type=int, help="PNG width in px")
    ap.add_argument("--size", type=int, help="square PNG of this side in px")
    ap.add_argument("--color", help="recolor a single-color SVG (RRGGBB)")
    args = ap.parse_args(argv)
    width, height = (args.size, args.size) if args.size else (args.width, args.height)
    if not (width or height):
        ap.error("give --height, --width or --size")
    try:
        w, h = rasterize(args.svg, args.png, width=width, height=height, color=args.color)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"wrote {args.png} ({w} x {h} px)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

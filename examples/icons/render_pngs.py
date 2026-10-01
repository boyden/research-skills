#!/usr/bin/env python3
"""Render every icon SVG under examples/icons/<source>/ to 512 x 512 transparent PNGs.

Output: examples/icons/png/<source>/<name>.png (grey #595959) and, for single-colour icons,
examples/icons/png/<source>/<name>_accent.png (accent #A51C30). Multi-colour icons (most
Bioicons) are rendered with their own colours and get no ``_accent`` variant.

The SVGs on disk stay unmodified: a recoloured copy with width/height 512 is written to a
temporary directory and screenshotted by headless Chrome (LibreOffice < 7.4 cannot draw SVGs
embedded in pptx, so slides use the PNGs). Existing PNGs are skipped unless --force.

Usage:
    python3 examples/icons/render_pngs.py            # render missing PNGs
    python3 examples/icons/render_pngs.py --force    # re-render everything
    python3 examples/icons/render_pngs.py --only lucide/bot tabler/robot
"""
import argparse
import concurrent.futures as cf
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
GREY = "#595959"
ACCENT = "#A51C30"
SIZE = 512
PAD = 200  # extra window height, cropped off again (see screenshot())
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")

COLOR_RE = re.compile(
    r"""(?:fill|stroke|stop-color|color)\s*[:=]\s*["']?\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|[a-zA-Z]+)""")
NEUTRAL = {"none", "transparent", "currentcolor", "inherit", "url"}


def colours(svg):
    """Distinct explicit colours in the SVG (lower-case, excluding none/currentColor)."""
    found = {c.lower() for c in COLOR_RE.findall(svg)}
    found = {c for c in found if c not in NEUTRAL}
    expand = {"#fff": "#ffffff", "white": "#ffffff", "#000": "#000000", "black": "#000000"}
    return {expand.get(c, c) for c in found}


def is_single_colour(svg):
    """currentColor icons, or icons drawn in exactly one explicit colour (or none at all)."""
    if "currentColor" in svg:
        return True
    if "<image" in svg:  # embedded raster: cannot be recoloured
        return False
    return len(colours(svg)) <= 1


def recolour(svg, colour):
    if "currentColor" in svg:
        return svg.replace("currentColor", colour)
    cols = colours(svg)
    if len(cols) == 1:
        (old,) = cols
        return re.sub(re.escape(old), colour, svg, flags=re.I)
    # no explicit colour: default fill is black, so set fill on the root element
    return re.sub(r"<svg\b", f'<svg fill="{colour}"', svg, count=1)


def _num(v):
    m = re.match(r"\s*([0-9.]+)", v or "")
    return float(m.group(1)) if m else None


def resize(svg):
    """Root <svg>: width/height 512, viewBox kept (added from the old width/height if missing)."""
    m = re.search(r"<svg\b[^>]*>", svg, flags=re.S)
    if m is None:
        raise ValueError("no <svg> element")
    tag = m.group(0)
    w = re.search(r'\swidth\s*=\s*["\']([^"\']*)["\']', tag)
    h = re.search(r'\sheight\s*=\s*["\']([^"\']*)["\']', tag)
    new = re.sub(r'\s(width|height)\s*=\s*["\'][^"\']*["\']', "", tag)
    if not re.search(r"viewBox\s*=", new):
        wv, hv = _num(w.group(1) if w else None), _num(h.group(1) if h else None)
        if not (wv and hv):
            raise ValueError("SVG has neither viewBox nor numeric width/height")
        new = new.replace("<svg", f'<svg viewBox="0 0 {wv:g} {hv:g}"', 1)
    new = new.replace("<svg", f'<svg width="{SIZE}" height="{SIZE}"', 1)
    if "xmlns=" not in new:
        new = new.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg[:m.start()] + new + svg[m.end():]


def _chunks(data):
    pos = 8
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        yield data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n


def _chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


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
    bpp = 4 if ctype == 6 else 3
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    raw = raw[:height * (1 + w * bpp)]
    new_ihdr = struct.pack(">IIBBBBB", w, height, depth, ctype, 0, 0, 0)
    return (png_bytes[:8] + _chunk(b"IHDR", new_ihdr) + _chunk(b"IDAT", zlib.compress(raw, 9))
            + _chunk(b"IEND", b""))


def screenshot(svg_text, out_png, tmp):
    tmp.mkdir(parents=True, exist_ok=True)
    src = tmp / (out_png.stem + ".svg")
    src.write_text(svg_text, encoding="utf-8")
    shot = tmp / (out_png.stem + "_shot.png")
    profile = tempfile.mkdtemp(prefix="chrome_", dir=tmp)
    # Headless Chrome's viewport is ~87 px shorter than --window-size, so the window is made
    # taller than the icon and the screenshot is cropped back to SIZE x SIZE.
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--force-device-scale-factor=1",
           "--default-background-color=00000000", "--hide-scrollbars", f"--user-data-dir={profile}",
           f"--window-size={SIZE},{SIZE + PAD}", f"--screenshot={shot}", src.as_uri()]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False)
    shutil.rmtree(profile, ignore_errors=True)
    if not shot.exists() or shot.stat().st_size == 0:
        raise RuntimeError(f"Chrome produced no PNG for {out_png}")
    out_png.write_bytes(crop_top(shot.read_bytes(), SIZE))


def jobs_for(svg_path, root, force):
    source, name = svg_path.parent.name, svg_path.stem
    text = svg_path.read_text(encoding="utf-8")
    out_dir = root / "png" / source
    mono = is_single_colour(text)
    variants = [("", GREY), ("_accent", ACCENT)] if mono else [("", None)]
    for suffix, colour in variants:
        out = out_dir / f"{name}{suffix}.png"
        if out.exists() and not force:
            continue
        body = recolour(text, colour) if colour else text
        yield f"{source}/{name}{suffix}", resize(body), out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-render PNGs that already exist")
    ap.add_argument("--only", nargs="*", default=None, help="limit to <source>/<name> entries")
    ap.add_argument("--root", type=Path, default=HERE, help="icons root (default: this directory)")
    ap.add_argument("--workers", type=int, default=4, help="parallel Chrome processes")
    args = ap.parse_args()
    if not CHROME:
        sys.exit("google-chrome / chromium not found on PATH")

    root = args.root.resolve()
    svgs = sorted(p for p in root.glob("*/*.svg") if p.parent.name != "png")
    if args.only:
        wanted = set(args.only)
        svgs = [p for p in svgs if f"{p.parent.name}/{p.stem}" in wanted]
    todo = [j for p in svgs for j in jobs_for(p, root, args.force)]
    print(f"{len(svgs)} SVGs, {len(todo)} PNGs to render")
    with tempfile.TemporaryDirectory(prefix="icons_render_") as tmpdir:
        def run(job):
            label, text, out = job
            out.parent.mkdir(parents=True, exist_ok=True)
            screenshot(text, out, Path(tmpdir) / label.replace("/", "__"))
            return label
        failed = 0
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            for fut, job in [(ex.submit(run, j), j) for j in todo]:
                try:
                    print("rendered", fut.result())
                except Exception as exc:  # report and continue
                    failed += 1
                    print("FAILED", job[0], exc, file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

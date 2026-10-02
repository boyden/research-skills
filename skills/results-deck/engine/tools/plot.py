#!/usr/bin/env python3
"""Draw a deck's figures from its ``plotting/`` package (engine/SPEC.md §6).

Usage
-----
::

    python plot.py <deck>                         # every figure (integrator only, e.g. after a theme change)
    python plot.py <deck> --only name_a name_b    # just these figures: the form to use in parallel work
    python plot.py <deck> --only name_a --out-dir /tmp/figs   # regression run, figures/ untouched
    python plot.py <deck> --list                  # registered figure names and their modules, draws nothing

What it does
------------
1. Reads ``theme:`` and ``figDir:`` from ``<deck>/deck.config.js`` with regular expressions (node is not
   run; no deck.config.js means defaults) and sets two environment variables for ``plotting/style.py``:

   - ``DECK_THEME``: ``<deck>/<theme>`` (``theme`` defaults to ``"theme"``, as in build.js) when that directory
     exists, otherwise ``<engine>/themes/neutral`` (a WARNING when a named directory is missing).  If neither exists the
     variable is left unset and style.py uses its own default.
   - ``DECK_FIG_DIR``: ``--out-dir`` if given, else ``<deck>/<figDir>``, default ``<deck>/figures``.

2. Puts ``<deck>`` on ``sys.path``, imports the package ``plotting`` and then every module in it except
   ``style``, ``common`` and names starting with ``_``.  It knows no figure by name: it merges the modules'
   ``FIGURES = {name: callable}`` and ``INPUTS = [path, ...]``.  A figure name registered by two modules is
   an error (exit code 2, both modules named).

3. Calls ``style.apply_style()`` when ``plotting/style.py`` defines it, then draws each selected figure:
   the callable returns ``(figure, stats)``.  The PNG is written by ``style.save(fig, name)`` when style.py
   defines ``save``, else by ``fig.savefig(<fig dir>/<name>.png, dpi=<theme dpi, default 200>,
   facecolor="white")`` (no tight bbox: figures are drawn at their on-slide size).  The figure is closed.

4. Writes ``<fig dir>/run_meta/<name>.json`` per figure: ``{figure, png, module, stats, inputs, versions,
   created, theme}``; ``inputs`` is the module's ``INPUTS`` plus ``common.INPUTS``.  ``--only`` therefore
   touches only the files of the figures it draws, and parallel runs never overwrite each other.

Exit codes: 0 done, 1 a figure failed to draw, 2 usage or registry error.  matplotlib is imported only by
the deck's plotting modules, never by this file.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import pkgutil
import platform
import re
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
NEUTRAL_THEME = ENGINE / "themes" / "neutral"
NOT_FIGURE_MODULES = {"style", "common"}
DEFAULT_DPI = 200


class PlotError(Exception):
    """Usage or registry problem: printed as ERROR, exit code 2."""


# --------------------------------------------------------------------------- deck.config.js
def blank_comments(src: str) -> str:
    """Return ``src`` with JS comments replaced by spaces (string literals are left alone)."""
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


def config_string(text: str, field: str) -> str | None:
    """Value of ``field: "..."`` in deck.config.js (literal strings only), or None."""
    m = re.search(rf"""\b{field}\s*:\s*(["'`])((?:\\.|(?!\1).)*)\1""", text)
    return m.group(2) if m else None


def resolve_dirs(deck: Path, out_dir: Path | None) -> tuple[Path | None, Path]:
    """Return (theme dir or None, figure dir) for this deck."""
    cfg = deck / "deck.config.js"
    text = blank_comments(cfg.read_text(encoding="utf-8")) if cfg.is_file() else ""
    theme_name, fig_name = config_string(text, "theme"), config_string(text, "figDir")

    # Same rule as build.js: <deck>/<theme>, default <deck>/theme; neutral when that directory is missing.
    theme = None
    cand = (deck / (theme_name or "theme")).resolve()
    if cand.is_dir():
        theme = cand
    elif theme_name:
        print(f"WARNING: theme directory {cand} (deck.config.js theme) does not exist; "
              f"using {NEUTRAL_THEME}")
    if theme is None and NEUTRAL_THEME.is_dir():
        theme = NEUTRAL_THEME
    if theme is None:
        print(f"WARNING: {NEUTRAL_THEME} does not exist; DECK_THEME is left unset "
              f"(plotting/style.py uses its own default)")

    if out_dir is not None:
        fig_dir = out_dir.resolve()
    else:
        fig_dir = (deck / (fig_name or "figures")).resolve()
    return theme, fig_dir


def theme_dpi(theme: Path | None) -> int | float:
    try:
        dpi = json.loads((theme / "theme.json").read_text(encoding="utf-8")).get("dpi")
        return dpi if isinstance(dpi, (int, float)) and dpi > 0 else DEFAULT_DPI
    except (OSError, TypeError, ValueError, AttributeError):
        return DEFAULT_DPI


# --------------------------------------------------------------------------- registry
def load_registry(deck: Path):
    """Import ``plotting`` and its figure modules.  Return (style, common, figures, owner, inputs)."""
    if not (deck / "plotting" / "__init__.py").is_file():
        raise PlotError(f"no plotting package in {deck} (plotting/__init__.py)")
    sys.path.insert(0, str(deck))
    plotting = importlib.import_module("plotting")
    loaded = Path(plotting.__file__).resolve().parent
    if loaded != (deck / "plotting").resolve():
        raise PlotError(f"`import plotting` found {loaded}, not the deck's plotting/ package")

    names = sorted(i.name for i in pkgutil.iter_modules(plotting.__path__))
    style = importlib.import_module("plotting.style") if "style" in names else None
    common = importlib.import_module("plotting.common") if "common" in names else None

    figures: dict = {}
    owner: dict[str, str] = {}
    inputs: dict[str, list[str]] = {}
    clashes = []
    for name in names:
        if name in NOT_FIGURE_MODULES or name.startswith("_"):
            continue
        mod = importlib.import_module(f"plotting.{name}")
        inputs[name] = [str(p) for p in getattr(mod, "INPUTS", [])]
        for fig_name, draw in getattr(mod, "FIGURES", {}).items():
            if fig_name in figures:
                clashes.append(f"figure {fig_name!r} is registered by both plotting/{owner[fig_name]}.py "
                               f"and plotting/{name}.py")
                continue
            if not callable(draw):
                raise PlotError(f"plotting/{name}.py: FIGURES[{fig_name!r}] is not callable")
            figures[fig_name] = draw
            owner[fig_name] = name
    if clashes:
        raise PlotError("\n  ".join(["duplicate figure names (rename one, names start with the section):"]
                                    + clashes))
    return style, common, figures, owner, inputs


# --------------------------------------------------------------------------- run_meta
def jsonable(x):
    """Plain JSON value: numpy scalars / arrays, paths, tuples and sets converted; NaN / inf -> None."""
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in x]
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if hasattr(x, "tolist"):                       # numpy array or scalar
        return jsonable(x.tolist())
    if hasattr(x, "item"):
        return jsonable(x.item())
    return str(x)


def versions() -> dict:
    out = {"python": platform.python_version()}
    for lib in ("matplotlib", "numpy"):
        mod = sys.modules.get(lib)
        if mod is None:
            try:
                mod = importlib.import_module(lib)
            except ImportError:
                continue
        out[lib] = getattr(mod, "__version__", None)
    return out


def write_json(path: Path, data: dict) -> None:
    """Write atomically, so a reader never sees half a file."""
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(jsonable(data), fh, ensure_ascii=False, indent=1, allow_nan=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --------------------------------------------------------------------------- drawing
def close(fig) -> None:
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is not None:
        plt.close(fig)


def draw_one(name, draw, style, fig_dir: Path, dpi) -> tuple[str, dict]:
    result = draw()
    if not (isinstance(result, tuple) and len(result) == 2):
        raise TypeError(f"FIGURES[{name!r}] must return (figure, stats), got {type(result).__name__}")
    fig, stats = result
    if stats is None:
        stats = {}
    png = fig_dir / f"{name}.png"
    try:
        if style is not None and callable(getattr(style, "save", None)):
            ret = style.save(fig, name)
        else:
            if png.is_symlink():                   # a linked source figure is replaced by the slide version
                png.unlink()
            fig.savefig(png, dpi=dpi, facecolor="white")
            ret = None
    finally:
        close(fig)
    if png.is_file():
        rec = png.name
    else:
        rec = str(ret) if ret is not None else png.name
        print(f"WARNING: {png} not found after saving {name!r}; style.save() returned {ret!r}")
    return rec, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="plot.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", type=Path, help="deck directory (holds plotting/ and usually deck.config.js)")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="draw only these figures (always in parallel work)")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="write the PNGs and run_meta/ here instead of the deck's figures/ (regression runs)")
    ap.add_argument("--list", action="store_true", help="print figure names and modules; draw nothing")
    args = ap.parse_args(argv)

    deck = args.deck.resolve()
    if not deck.is_dir():
        print(f"ERROR: deck directory {args.deck} not found", file=sys.stderr)
        return 2
    theme, fig_dir = resolve_dirs(deck, args.out_dir)
    if theme is not None:
        os.environ["DECK_THEME"] = str(theme)
    else:
        os.environ.pop("DECK_THEME", None)
    os.environ["DECK_FIG_DIR"] = str(fig_dir)

    try:
        style, common, figures, owner, inputs = load_registry(deck)
        if args.only:
            unknown = [n for n in args.only if n not in figures]
            if unknown:
                raise PlotError(f"unknown figure name(s): {', '.join(unknown)}\n  registered: "
                                + (", ".join(figures) or "(none)"))
    except PlotError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.list:
        for name in sorted(figures, key=lambda n: (owner[n], n)):
            print(f"{name}\t{owner[name]}")
        print(f"{len(figures)} figure(s)", file=sys.stderr)
        return 0

    selected = [n for n in figures if not args.only or n in args.only]
    common_inputs = [str(p) for p in getattr(common, "INPUTS", [])] if common is not None else []
    if style is not None and callable(getattr(style, "apply_style", None)):
        style.apply_style()
    dpi = getattr(style, "DPI", None) or theme_dpi(theme)

    meta_dir = fig_dir / "run_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    print(f"figures: {fig_dir}")
    print(f"theme:   {theme if theme is not None else '(DECK_THEME unset)'}")
    for name in selected:
        try:
            png, stats = draw_one(name, figures[name], style, fig_dir, dpi)
        except Exception:
            traceback.print_exc()
            print(f"ERROR: figure {name!r} (plotting/{owner[name]}.py) failed; "
                  f"figures after it were not drawn", file=sys.stderr)
            return 1
        mod_inputs = inputs[owner[name]]
        meta = {
            "figure": name,
            "png": png,
            "module": f"plotting.{owner[name]}",
            "stats": stats,
            "inputs": mod_inputs + [p for p in common_inputs if p not in mod_inputs],
            "versions": versions(),
            "created": datetime.now().astimezone().isoformat(timespec="seconds"),
            "theme": os.environ.get("DECK_THEME"),
        }
        write_json(meta_dir / f"{name}.json", meta)
        print(f"  {name}.png  ({owner[name]})")
    print(f"{len(selected)} figure(s) drawn; run_meta in {meta_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

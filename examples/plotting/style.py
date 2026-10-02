"""Shared style of the example figures: sizes, colors and fonts from the theme, apply_style(), save().

The theme directory comes from env ``DECK_THEME`` (set by engine/tools/plot.py), else the neutral theme
of the engine; its theme.json is deep-merged onto the neutral one, so a partial theme still works. The
output directory comes from env ``DECK_FIG_DIR``, else ``examples/figures``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
NEUTRAL_THEME = REPO / "skills" / "results-deck" / "engine" / "themes" / "neutral"
THEME_DIR = Path(os.environ.get("DECK_THEME") or NEUTRAL_THEME)
FIG_DIR = Path(os.environ.get("DECK_FIG_DIR") or HERE.parent / "figures")


def _merge(base: dict, over: dict) -> dict:
    """Deep merge as in the engine's configure({theme}): objects merge, arrays and scalars replace."""
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _read(theme_dir: Path) -> dict:
    path = theme_dir / "theme.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


THEME = _merge(_read(NEUTRAL_THEME), _read(THEME_DIR))


def _hex(value: str) -> str:
    return "#" + value.lstrip("#").lower()


DPI = THEME["dpi"]

# Slide geometry (inches) and the two figure sizes of the content box between the title and the conclusion.
SLIDE_W, SLIDE_H = THEME["slide"]["w"], THEME["slide"]["h"]
FULL = tuple(THEME["geometry"]["full"])
HALF = tuple(THEME["geometry"]["half"])

# Plot palette. KM colors go by curve position, not by group: lower curve red, upper blue, middle gray.
INK = _hex(THEME["plot"]["ink"])
MUTED = _hex(THEME["plot"]["muted"])
GRID = _hex(THEME["plot"]["grid"])
KM_LOW = _hex(THEME["plot"]["low"])
KM_HIGH = _hex(THEME["plot"]["high"])
KM_MID = _hex(THEME["plot"]["mid"])
ACCENT = _hex(THEME["color"]["accent"])
RULE = _hex(THEME["color"]["text"])          # table rules and header text: the slide body text color
FONT = list(THEME["font"]["plot"])


def apply_style():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": FONT,
        "pdf.fonttype": 42, "axes.unicode_minus": False,
        "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 12, "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    })


def save(fig, name: str) -> Path:
    """Write <FIG_DIR>/<name>.png at the theme dpi on white; no tight bbox (figures are drawn at slide size)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    if path.is_symlink():
        path.unlink()
    fig.savefig(path, dpi=DPI, facecolor="white")
    return path

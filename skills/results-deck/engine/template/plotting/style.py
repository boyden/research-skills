"""Shared figure style read from the deck theme: sizes, colors, fonts, ``apply_style()`` and ``save()``.

Directories (engine/SPEC.md §6):

- theme: env ``DECK_THEME`` (``tools/plot.py`` sets it from the ``theme`` field of deck.config.js), else
  ``../theme`` next to this package. Its ``theme.json`` must be complete (the template's ``theme/`` is a full
  copy of the engine's neutral theme, and ``tools/theme_from_pptx.py`` writes complete themes).
- figures: env ``DECK_FIG_DIR`` (``figDir`` of deck.config.js, or ``plot.py --out-dir``), else ``../figures``.

Figures are drawn at their on-slide size (``FULL`` / ``HALF`` in inches) and saved without a tight bbox, so a
point size here is the point size on screen.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
THEME_DIR = Path(os.environ.get("DECK_THEME") or HERE.parent / "theme")
FIG_DIR = Path(os.environ.get("DECK_FIG_DIR") or HERE.parent / "figures")
THEME = json.loads((THEME_DIR / "theme.json").read_text(encoding="utf-8"))


def _hex(value: str) -> str:
    return "#" + value.lstrip("#").lower()


DPI = THEME["dpi"]

# Figure slots of the content box between the slide title and the conclusion (inches).
FULL = tuple(THEME["geometry"]["full"])
HALF = tuple(THEME["geometry"]["half"])

# Plot palette. Survival curves are colored by position, not by group: lower curve LOW (red), upper HIGH
# (blue), any curve in between MID (gray).
INK = _hex(THEME["plot"]["ink"])
MUTED = _hex(THEME["plot"]["muted"])
GRID = _hex(THEME["plot"]["grid"])
LOW = _hex(THEME["plot"]["low"])
HIGH = _hex(THEME["plot"]["high"])
MID = _hex(THEME["plot"]["mid"])
ACCENT = _hex(THEME["color"]["accent"])
RULE = _hex(THEME["color"]["text"])            # table rules and header text: the slide body text color
FONT = list(THEME["font"]["plot"])

# On-screen font sizes (pt): BASE for labels, MIN (the smallest allowed) for ticks, legends and annotations.
BASE = THEME["size"]["plotBase"]
MIN = THEME["size"]["plotMin"]


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": FONT,
        "pdf.fonttype": 42, "axes.unicode_minus": False,
        "font.size": BASE, "axes.titlesize": BASE + 2, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": BASE, "xtick.labelsize": MIN, "ytick.labelsize": MIN, "legend.fontsize": MIN,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    })


def save(fig, name: str) -> Path:
    """Write ``<FIG_DIR>/<name>.png`` at the theme dpi on white; no tight bbox."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, facecolor="white")
    return path

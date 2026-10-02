"""Shared style of the fixture's figures: reads the theme named by DECK_THEME, saves into DECK_FIG_DIR."""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
THEME_DIR = Path(os.environ.get("DECK_THEME") or HERE.parent / "theme")
FIG_DIR = Path(os.environ.get("DECK_FIG_DIR") or HERE.parent / "figures")
THEME = json.loads((THEME_DIR / "theme.json").read_text(encoding="utf-8")) if (THEME_DIR / "theme.json").is_file() else {}
DPI = THEME.get("dpi", 200)
FULL = tuple(THEME.get("geometry", {}).get("full", [12.1, 4.6]))
HALF = tuple(THEME.get("geometry", {}).get("half", [5.9, 4.6]))
INK = "#" + THEME.get("plot", {}).get("ink", "222222")
APPLIED = []


def apply_style():
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": THEME.get("font", {}).get("plot", ["DejaVu Sans"])})
    APPLIED.append(True)


def save(fig, name):
    """Write <FIG_DIR>/<name>.png at the theme dpi; no tight bbox."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, facecolor="white")
    return path.name


def env_stats():
    """What this module saw, so the tests can check it through run_meta."""
    return {"deck_theme": os.environ.get("DECK_THEME"), "deck_fig_dir": os.environ.get("DECK_FIG_DIR"),
            "theme_name": THEME.get("name"), "applied": bool(APPLIED)}

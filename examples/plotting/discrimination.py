"""Discrimination figures: ROC curves and AUC bars, both with bootstrap 95% CIs."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from plotting.common import auc_ci, load
from plotting.style import ACCENT, FULL, GRID, HALF, INK, MUTED

INPUTS: list = []


def er_positive(d: pd.DataFrame) -> pd.Series:
    """ER-positive = estrogen receptor >= 10 fmol/mg."""
    return (d["estrec"] >= 10).astype(int)


def event_by_5y(d: pd.DataFrame):
    """1 = recurrence or death before 5 years, 0 = followed for >= 5 years; censored before 5 years excluded."""
    early = (d["event"] == 1) & (d["years"] < 5)
    sub = d[early | (d["years"] >= 5)]
    return sub, early[sub.index].astype(int)


def roc_panel(ax, y, score, title):
    """One square ROC panel: curve in the accent color, dashed chance diagonal, AUC [95% CI], n and positives."""
    s = auc_ci(y, score)
    fpr, tpr, _ = roc_curve(y, score)
    ax.plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1)
    ax.plot(fpr, tpr, color=ACCENT, lw=2)
    ax.set_box_aspect(1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(title)
    ax.grid(color=GRID, lw=0.8)
    ax.text(0.97, 0.04, f"AUC {s['auc']:.3f} [{s['lo']:.3f}–{s['hi']:.3f}]\n"
            f"n = {s['n']}, positive = {s['positives']}", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=11, linespacing=1.5)
    return s


def fig_roc():
    """(a) PR receptor level for ER status; (b) positive nodes for recurrence or death within 5 years."""
    d = load()
    fig = plt.figure(figsize=FULL)
    side, bottom = 3.6, 0.65                 # two equal squares, the pair centered on the slide
    axes = [fig.add_axes([x / FULL[0], bottom / FULL[1], side / FULL[0], side / FULL[1]]) for x in (2.15, 7.05)]
    stats = {"er_status_progrec": roc_panel(axes[0], er_positive(d), d["progrec"], "ER status from PR level")}
    sub, y5 = event_by_5y(d)
    stats["event_5y_pnodes"] = roc_panel(axes[1], y5, sub["pnodes"], "5-year recurrence from nodes")
    return fig, stats


AUC_ROWS = [  # (column, label, sign): sign -1 = lower values go with ER-positive, so the score is flipped
    ("progrec", "PR receptor, higher", 1),
    ("age", "Age, older", 1),
    ("grade_3", "Grade I–II (not III)", -1),
    ("pnodes", "Positive nodes, fewer", -1),
    ("tsize", "Tumor size, smaller", -1),
]


def fig_auc_bars():
    """AUC for ER status of single predictors, bars from chance (0.5) with bootstrap 95% CIs.

    Orientation is flipped explicitly (``sign`` in AUC_ROWS) for predictors whose lower values go with
    ER-positive, and the row label names the direction. The direction was read off the same data, so a flipped
    AUC near 0.5 is descriptive only. Accent = CI excludes 0.5; gray = it does not.
    """
    d = load()
    y = er_positive(d)
    rows = [dict(label=lab, sign=sg, **auc_ci(y, sg * d[col].astype(float))) for col, lab, sg in AUC_ROWS]
    t = pd.DataFrame(rows).sort_values("auc").reset_index(drop=True)

    fig = plt.figure(figsize=HALF)
    ax = fig.add_axes([0.37, 0.15, 0.58, 0.72])
    yy = np.arange(len(t))
    for yi, r in zip(yy, t.itertuples()):
        c = ACCENT if r.lo > 0.5 else MUTED
        ax.barh(yi, r.auc - 0.5, left=0.5, height=0.6, color=c)
        ax.plot([r.lo, r.hi], [yi, yi], color=INK, lw=1.2)
        for xe in (r.lo, r.hi):
            ax.plot([xe, xe], [yi - 0.12, yi + 0.12], color=INK, lw=1.2)
        ax.text(r.hi + 0.012, yi, f"{r.auc:.3f}", va="center", ha="left", fontsize=11)
    # Bars start at chance; the axis reaches a little below 0.5 so CIs that cross chance are not cut off.
    ax.axvline(0.5, color=INK, lw=1, ls="--")
    ax.set_xlim(0.4, 1.0)
    ax.set_xticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_ylim(-0.6, len(t) - 0.4)
    ax.set_yticks(yy)
    ax.set_yticklabels(t["label"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("AUC [95% CI]; bars start at chance (0.5)")
    ax.set_title(f"AUC for ER status (n = {len(y)})")
    return fig, t.to_dict(orient="records")


FIGURES = {
    "roc_example": fig_roc,
    "auc_bars_example": fig_auc_bars,
}

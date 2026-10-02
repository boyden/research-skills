"""Survival figures: KM with the four statistics, and a forest plot with a three-line number table."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
from lifelines.utils import restricted_mean_survival_time
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter
from matplotlib.transforms import blended_transform_factory

from plotting.common import bh, cox_one, fmt_p, load
from plotting.style import ACCENT, FULL, GRID, INK, KM_HIGH, KM_LOW, KM_MID, MUTED, RULE

INPUTS: list = []

# ---- KM with the four statistics -----------------------------------------------------------------------
KM_TICKS = [0, 2, 4, 6]


def km_panel(ax, d, groups, title, stats_lines):
    """One square KM panel with censor marks, the four statistics to its right and a number-at-risk table below.

    ``groups``: [(short label, mask)]; colors by curve position (RMST), not by group. The at-risk counts
    (n with follow-up >= t at each x tick) are drawn by hand: lifelines' add_at_risk_counts resizes the axes
    and breaks the fixed on-slide layout.
    """
    fig = ax.figure
    fits = []
    horizon = min(d.loc[m, "years"].max() for _, m in groups)
    for label, m in groups:
        k = KaplanMeierFitter().fit(d.loc[m, "years"], d.loc[m, "event"], label=f"{label} (n = {int(m.sum())})")
        fits.append((restricted_mean_survival_time(k, t=horizon), k, label, m))
    ranked = sorted(fits, key=lambda t: t[0])
    colors = {id(ranked[0][1]): KM_LOW, id(ranked[-1][1]): KM_HIGH}
    for _, k, _, _ in fits:
        c = colors.get(id(k), KM_MID)
        k.plot_survival_function(ax=ax, ci_show=False, color=c, lw=2, show_censors=True,
                                 censor_styles={"marker": "|", "ms": 5, "mew": 1})
    ax.set_box_aspect(1)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, 7.5)
    ax.set_xticks(KM_TICKS)
    ax.set_xlabel("Years", labelpad=2)
    ax.set_ylabel("Recurrence-free survival")
    ax.set_title(title)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.legend(loc="lower left", frameon=False, handlelength=1.6)
    # Statistics beside the panel (inside, they would sit on the curves at this panel size).
    ax.text(1.04, 1.0, "\n".join(stats_lines), transform=ax.transAxes, ha="left", va="top", fontsize=11,
            linespacing=1.5)

    # Number at risk: x in data units (aligned with the ticks), y in inches from the figure bottom.
    tr = blended_transform_factory(ax.transData, fig.dpi_scale_trans)
    label_x = -0.09 * 7.5                    # row labels end just left of the y axis
    ax.text(label_x, 0.56, "Number at risk", transform=tr, ha="right", va="center", fontsize=11,
            color=MUTED, clip_on=False)
    for i, (_, k, label, m) in enumerate(fits):
        y_in = 0.34 - i * 0.2
        c = colors.get(id(k), KM_MID)
        ax.text(label_x, y_in, label, transform=tr, ha="right", va="center", fontsize=11, color=c, clip_on=False)
        yrs = d.loc[m, "years"]
        for t in KM_TICKS:
            ax.text(t, y_in, f"{int((yrs >= t).sum())}", transform=tr, ha="center", va="center", fontsize=11,
                    color=c, clip_on=False)


def fig_km():
    d = load()
    fig = plt.figure(figsize=FULL)
    # Two equal 2.95 in squares, placed in inches: room on the left for the at-risk row labels, on the right
    # for the four statistics, and below for the number-at-risk table.
    side, bottom = 2.95, 1.2
    axes = [fig.add_axes([x / FULL[0], bottom / FULL[1], side / FULL[0], side / FULL[1]]) for x in (1.4, 7.25)]
    stats = {}

    # Binary: hormone therapy yes vs no (HR per unit).
    s = cox_one(d, "hormone_therapy", per_sd=False)
    lr = logrank_test(d.loc[d.hormone_therapy == 1, "years"], d.loc[d.hormone_therapy == 0, "years"],
                      d.loc[d.hormone_therapy == 1, "event"], d.loc[d.hormone_therapy == 0, "event"])
    km_panel(axes[0], d, [("Tamoxifen", d.hormone_therapy == 1), ("No tamoxifen", d.hormone_therapy == 0)],
             "Hormone therapy", [f"HR {s['hr']:.2f} [{s['lo']:.2f}–{s['hi']:.2f}]", f"Cox p {fmt_p(s['p'])}",
                                 f"C-index {s['c']:.2f}", f"Log-rank p {fmt_p(lr.p_value)}"])
    stats["hormone_therapy"] = {**s, "logrank_p": lr.p_value}

    # Continuous: positive nodes, HR per SD of log1p(nodes), drawn as a median split.
    s = cox_one(d, "log_pnodes", per_sd=True)
    hi = d.pnodes > d.pnodes.median()
    lr = logrank_test(d.loc[hi, "years"], d.loc[~hi, "years"], d.loc[hi, "event"], d.loc[~hi, "event"])
    km_panel(axes[1], d, [(f"Nodes > {d.pnodes.median():.0f}", hi), (f"Nodes ≤ {d.pnodes.median():.0f}", ~hi)],
             "Positive lymph nodes (median split)",
             [f"HR/SD {s['hr']:.2f} [{s['lo']:.2f}–{s['hi']:.2f}]", f"Cox p {fmt_p(s['p'])}",
              f"C-index {s['c']:.2f}", f"Log-rank p {fmt_p(lr.p_value)}"])
    axes[1].set_ylabel("")
    stats["log_pnodes"] = {**s, "logrank_p": lr.p_value}
    return fig, stats


# ---- Forest plot with a three-line number table --------------------------------------------------------
FOREST_ROWS = [  # (column, label on the figure, per SD?)
    ("age", "Age (per SD)", True),
    ("tsize", "Tumor size (per SD)", True),
    ("log_pnodes", "Positive nodes, log (per SD)", True),
    ("log_progrec", "PR receptor, log (per SD)", True),
    ("log_estrec", "ER receptor, log (per SD)", True),
    ("grade_3", "Grade III vs I–II", False),
    ("postmenopausal", "Postmenopausal", False),
    ("hormone_therapy", "Tamoxifen", False),
]


def fig_forest():
    d = load()
    rows = [dict(label=lab, **cox_one(d, col, sd)) for col, lab, sd in FOREST_ROWS]
    t = pd.DataFrame(rows)
    t["q"] = bh(t["p"].values)

    fig = plt.figure(figsize=FULL)
    ax = fig.add_axes([0.24, 0.16, 0.36, 0.74])
    y = np.arange(len(t))[::-1]
    for yi, r in zip(y, t.itertuples()):
        c = ACCENT if r.q < 0.05 else MUTED
        ax.plot([r.lo, r.hi], [yi, yi], color=c, lw=1.6)
        ax.plot(r.hr, yi, "s", color=c, ms=7)
    ax.axvline(1, color=INK, lw=0.8, ls="--")
    ax.set_xscale("log")
    ax.set_xticks([0.5, 1, 2])
    ax.set_xticklabels(["0.5", "1", "2"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(-0.7, len(t) - 0.3)
    ax.set_yticks(y)
    ax.set_yticklabels(t["label"])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Hazard ratio (95% CI), recurrence-free survival")

    # Number columns: header and values share one column center; three rules only (top, under header, bottom).
    cols = [("HR [95% CI]", 0.70), ("p", 0.81), ("q", 0.88), ("n", 0.945)]
    top_y = len(t) - 0.3
    to_fig = lambda yy: ax.transData.transform((1, yy))[1] / fig.bbox.height
    head_y = to_fig(top_y) + 0.045
    for name, x in cols:
        fig.text(x, head_y, name, ha="center", va="center", weight="bold", color=RULE)
    for yi, r in zip(y, t.itertuples()):
        fy = to_fig(yi)
        vals = [f"{r.hr:.2f} [{r.lo:.2f}–{r.hi:.2f}]", fmt_p(r.p), fmt_p(r.q), f"{r.n}"]
        for (_, x), v in zip(cols, vals):
            fig.text(x, fy, v, ha="center", va="center")
    x0, x1 = 0.635, 0.985
    for yy, lw in [(head_y + 0.04, 1.5), (head_y - 0.035, 0.75), (to_fig(-0.7), 1.5)]:
        fig.add_artist(Line2D([x0, x1], [yy, yy], color=RULE, lw=lw, transform=fig.transFigure))
    return fig, t.to_dict(orient="records")


FIGURES = {
    "km_example": fig_km,
    "forest_example": fig_forest,
}

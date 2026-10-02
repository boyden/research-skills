"""Figures of the ``results`` section: Kaplan-Meier panels and a univariate Cox forest plot (GBSG2).

Registered names start with the section name (``results_*``). Each callable returns ``(figure, stats)``;
``stats`` holds every number shown on the slides that use the figure and is written to
``figures/run_meta/<name>.json`` by ``tools/plot.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter
from matplotlib.transforms import blended_transform_factory

from . import common, style

INPUTS: list[str] = []

# ---- Kaplan-Meier with the four statistics ---------------------------------------------------------------
KM_TICKS = [0, 2, 4, 6]
KM_XMAX = 7.5


def km_panel(ax, d, groups, title, stats_lines):
    """One square KM panel with censor marks, the four statistics to its right and a number-at-risk table below.

    ``groups``: [(short label, mask)]. Curves are colored by position (restricted mean survival time), not by
    group. The at-risk counts (n with follow-up >= t at each x tick) are drawn by hand: lifelines'
    add_at_risk_counts resizes the axes and breaks the fixed on-slide layout.
    """
    from lifelines import KaplanMeierFitter
    from lifelines.utils import restricted_mean_survival_time

    fig = ax.figure
    fits = []
    horizon = min(d.loc[m, "years"].max() for _, m in groups)
    for label, m in groups:
        k = KaplanMeierFitter().fit(d.loc[m, "years"], d.loc[m, "event"], label=f"{label} (n = {int(m.sum())})")
        fits.append((restricted_mean_survival_time(k, t=horizon), k, label, m))
    ranked = sorted(fits, key=lambda t: t[0])
    colors = {id(ranked[0][1]): style.LOW, id(ranked[-1][1]): style.HIGH}
    for _, k, _, _ in fits:
        k.plot_survival_function(ax=ax, ci_show=False, color=colors.get(id(k), style.MID), lw=2, show_censors=True,
                                 censor_styles={"marker": "|", "ms": 5, "mew": 1})
    ax.set_box_aspect(1)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, KM_XMAX)
    ax.set_xticks(KM_TICKS)
    ax.set_xlabel("Years", labelpad=2)
    ax.set_ylabel("Recurrence-free survival")
    ax.set_title(title)
    ax.grid(axis="y", color=style.GRID, lw=0.8)
    ax.legend(loc="lower left", frameon=False, handlelength=1.6)
    # Statistics beside the panel (inside, they would sit on the curves at this panel size).
    ax.text(1.04, 1.0, "\n".join(stats_lines), transform=ax.transAxes, ha="left", va="top", fontsize=style.MIN,
            linespacing=1.5)

    # Number at risk: x in data units (aligned with the ticks), y in inches from the figure bottom.
    tr = blended_transform_factory(ax.transData, fig.dpi_scale_trans)
    label_x = -0.09 * KM_XMAX                 # row labels end just left of the y axis
    ax.text(label_x, 0.56, "Number at risk", transform=tr, ha="right", va="center", fontsize=style.MIN,
            color=style.MUTED, clip_on=False)
    for i, (_, k, label, m) in enumerate(fits):
        y_in = 0.34 - i * 0.2
        c = colors.get(id(k), style.MID)
        ax.text(label_x, y_in, label, transform=tr, ha="right", va="center", fontsize=style.MIN, color=c,
                clip_on=False)
        yrs = d.loc[m, "years"]
        for t in KM_TICKS:
            ax.text(t, y_in, f"{int((yrs >= t).sum())}", transform=tr, ha="center", va="center",
                    fontsize=style.MIN, color=c, clip_on=False)


def fig_km():
    """Two KM panels: hormone therapy (yes vs no) and positive lymph nodes (median split, HR per SD)."""
    from lifelines.statistics import logrank_test

    d = common.load()
    w, h = style.FULL
    fig = plt.figure(figsize=style.FULL)
    # Two equal 2.95 in squares, placed in inches: room on the left for the at-risk row labels, on the right
    # for the four statistics, and below for the number-at-risk table.
    side, bottom = 2.95, 1.2
    axes = [fig.add_axes([x / w, bottom / h, side / w, side / h]) for x in (1.4, 7.25)]
    stats = {}

    def logrank(mask):
        return logrank_test(d.loc[mask, "years"], d.loc[~mask, "years"],
                            d.loc[mask, "event"], d.loc[~mask, "event"]).p_value

    # Binary: hormone therapy yes vs no (HR per unit).
    tam = d.hormone_therapy == 1
    s = common.cox_one(d, "hormone_therapy", per_sd=False)
    lr = logrank(tam)
    km_panel(axes[0], d, [("Tamoxifen", tam), ("No tamoxifen", ~tam)], "Hormone therapy",
             [f"HR {s['hr']:.2f} [{s['lo']:.2f}–{s['hi']:.2f}]", f"Cox p {common.fmt_p(s['p'])}",
              f"C-index {s['c']:.2f}", f"Log-rank p {common.fmt_p(lr)}"])
    stats["hormone_therapy"] = {**s, "logrank_p": lr}

    # Continuous: positive nodes, HR per SD of log(1 + nodes), drawn as a median split.
    s = common.cox_one(d, "log_pnodes", per_sd=True)
    med = d.pnodes.median()
    hi = d.pnodes > med
    lr = logrank(hi)
    km_panel(axes[1], d, [(f"Nodes > {med:.0f}", hi), (f"Nodes ≤ {med:.0f}", ~hi)],
             "Positive lymph nodes (median split)",
             [f"HR/SD {s['hr']:.2f} [{s['lo']:.2f}–{s['hi']:.2f}]", f"Cox p {common.fmt_p(s['p'])}",
              f"C-index {s['c']:.2f}", f"Log-rank p {common.fmt_p(lr)}"])
    axes[1].set_ylabel("")
    stats["log_pnodes"] = {**s, "logrank_p": lr, "median_split": med}

    # Baseline characteristics by hormone therapy: the numbers of the supplementary cohort table.
    stats["cohort"] = {"all": common.cohort(d), "tamoxifen": common.cohort(d[tam]),
                       "no_tamoxifen": common.cohort(d[~tam])}
    return fig, stats


# ---- Forest plot with a three-line number table ----------------------------------------------------------
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
    """Eight univariate Cox models on a log axis; rows with q < 0.05 in the accent color."""
    d = common.load()
    t = pd.DataFrame([dict(label=lab, **common.cox_one(d, col, sd)) for col, lab, sd in FOREST_ROWS])
    t["q"] = common.bh(t["p"].values)

    fig = plt.figure(figsize=style.FULL)
    ax = fig.add_axes([0.24, 0.16, 0.36, 0.74])
    y = np.arange(len(t))[::-1]
    for yi, r in zip(y, t.itertuples()):
        c = style.ACCENT if r.q < 0.05 else style.MUTED
        ax.plot([r.lo, r.hi], [yi, yi], color=c, lw=1.6)
        ax.plot(r.hr, yi, "s", color=c, ms=7)
    ax.axvline(1, color=style.INK, lw=0.8, ls="--")
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
    to_fig = lambda yy: ax.transData.transform((1, yy))[1] / fig.bbox.height  # noqa: E731
    head_y = to_fig(len(t) - 0.3) + 0.045
    for name, x in cols:
        fig.text(x, head_y, name, ha="center", va="center", weight="bold", color=style.RULE)
    for yi, r in zip(y, t.itertuples()):
        vals = [f"{r.hr:.2f} [{r.lo:.2f}–{r.hi:.2f}]", common.fmt_p(r.p), common.fmt_p(r.q), f"{r.n}"]
        for (_, x), v in zip(cols, vals):
            fig.text(x, to_fig(yi), v, ha="center", va="center")
    x0, x1 = 0.635, 0.985
    for yy, lw in [(head_y + 0.04, 1.5), (head_y - 0.035, 0.75), (to_fig(-0.7), 1.5)]:
        fig.add_artist(Line2D([x0, x1], [yy, yy], color=style.RULE, lw=lw, transform=fig.transFigure))
    return fig, {"rows": t.to_dict(orient="records")}


FIGURES = {
    "results_km": fig_km,
    "results_forest": fig_forest,
}

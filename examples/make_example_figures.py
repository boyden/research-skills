"""
Example figures for the shared rules (shared/figures.md, shared/tables.md, skills/results-deck/).

All data are public: the GBSG2 breast cancer trial (686 women, recurrence-free survival) shipped with
lifelines (``lifelines.datasets.load_gbsg2``; Schumacher et al., J Clin Oncol 1994; Sauerbrei & Royston,
JRSS A 1999). Every figure is drawn at the size it occupies on a 13.333 x 7.5 in (16:9) slide, so a
point size here is the point size on screen.

    python examples/make_example_figures.py                    # all figures -> examples/figures/*.png
    python examples/make_example_figures.py --only km_example  # just these; each writes run_meta/<name>.json

Needs matplotlib, numpy, pandas, lifelines, scikit-learn.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.datasets import load_gbsg2
from lifelines.statistics import logrank_test
from lifelines.utils import restricted_mean_survival_time
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullFormatter
from matplotlib.transforms import blended_transform_factory
from sklearn.metrics import roc_auc_score, roc_curve

OUT = Path(__file__).resolve().parent / "figures"
DPI = 200

# Slide geometry (inches) and the content box between the title and the conclusion.
SLIDE_W, SLIDE_H = 13.333, 7.5
FULL = (12.1, 4.6)
HALF = (5.9, 4.6)

# Neutral palette. KM colours go by curve position, not by group: lower curve red, upper blue, middle grey.
INK = "#222222"
MUTED = "#6b6b6b"
GRID = "#e6e6e6"
ACCENT = "#a51c30"
KM_LOW = "#c0392b"
KM_HIGH = "#2a78d6"
KM_MID = "#8a8a8a"
RULE = "#595959"


def apply_style():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "pdf.fonttype": 42, "axes.unicode_minus": False,
        "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 12, "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    })


def fmt_p(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg q-values."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    out = np.empty_like(q)
    out[order] = q
    return out


def load() -> pd.DataFrame:
    d = load_gbsg2()
    d["years"] = d["time"] / 365.25
    d["event"] = d["cens"].astype(int)
    d["hormone_therapy"] = (d["horTh"] == "yes").astype(int)
    d["postmenopausal"] = (d["menostat"] == "Post").astype(int)
    d["grade_3"] = (d["tgrade"] == "III").astype(int)
    for c in ["pnodes", "progrec", "estrec"]:
        d[f"log_{c}"] = np.log1p(d[c])
    return d


def cox_one(d: pd.DataFrame, col: str, per_sd: bool):
    """Univariate Cox: HR per SD for a continuous variable, per unit (yes vs no) for a binary one."""
    x = d[col].astype(float)
    if per_sd:
        x = (x - x.mean()) / x.std()
    df = pd.DataFrame({"x": x, "years": d["years"], "event": d["event"]})
    m = CoxPHFitter().fit(df, "years", "event")
    s = m.summary.loc["x"]
    return dict(hr=s["exp(coef)"], lo=s["exp(coef) lower 95%"], hi=s["exp(coef) upper 95%"], p=s["p"],
                c=m.concordance_index_, n=len(df), events=int(df["event"].sum()))


# ---- 1 · Slide anatomy -------------------------------------------------------------------------------
def fig_slide_anatomy():
    """The fixed zones of a result slide, to scale."""
    fig = plt.figure(figsize=(SLIDE_W * 0.6, SLIDE_H * 0.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, SLIDE_W)
    ax.set_ylim(SLIDE_H, 0)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), SLIDE_W, SLIDE_H, fill=False, ec=INK, lw=1.2))

    def zone(x, y, w, h, label, fc, ec=MUTED, color=INK, size=9, weight="normal"):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=size, color=color,
                weight=weight, wrap=True)

    zone(0.59, 0.36, 8.8, 0.6, "Title: topic, not finding (28 pt bold)", "#f3f3f3", weight="bold")
    zone(9.55, 0.13, 3.6, 0.45, "Logo", "#f3f3f3", size=8)
    fx = (SLIDE_W - FULL[0]) / 2
    zone(fx, 1.1, FULL[0], FULL[1], "Figure drawn at this exact size: 12.1 × 4.6 in\n"
         "(font sizes in the plotting code = font sizes on screen; placed 1:1, never scaled)", "#eaf1fb",
         ec=KM_HIGH, size=10)
    zone(0.6, 5.75, SLIDE_W - 1.2, 1.05, "Conclusion: one finding, bold black (18 pt; split into bullets if long)",
         "#fbeaec", ec=ACCENT, size=10, weight="bold")
    zone(6.3, 6.85, 5.9, 0.35, "Source: table / reference (9 pt serif)", "#f3f3f3", size=8)
    zone(12.35, 6.95, 0.5, 0.35, "n", "#f3f3f3", size=8)
    for y, lab in [(1.1, "y 1.1"), (5.7, "y 5.7"), (5.75, ""), (6.8, "y 6.8")]:
        if lab:
            ax.text(0.08, y, lab, fontsize=7, color=MUTED, va="center")
    return fig, {"slide_in": [SLIDE_W, SLIDE_H], "figure_box_in": [fx, 1.1, *FULL]}


# ---- 2 · KM with the four statistics ---------------------------------------------------------------------
KM_TICKS = [0, 2, 4, 6]


def km_panel(ax, d, groups, title, stats_lines):
    """One square KM panel with censor marks, the four statistics to its right and a number-at-risk table below.

    ``groups``: [(short label, mask)]; colours by curve position (RMST), not by group. The at-risk counts
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
    colours = {id(ranked[0][1]): KM_LOW, id(ranked[-1][1]): KM_HIGH}
    for _, k, _, _ in fits:
        c = colours.get(id(k), KM_MID)
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
        c = colours.get(id(k), KM_MID)
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


# ---- 2b · ROC and AUC bars with bootstrap CIs ------------------------------------------------------------------
N_BOOT = 2000
RANDOM_STATE = 0


def er_positive(d: pd.DataFrame) -> pd.Series:
    """ER-positive = oestrogen receptor >= 10 fmol/mg."""
    return (d["estrec"] >= 10).astype(int)


def event_by_5y(d: pd.DataFrame):
    """1 = recurrence or death before 5 years, 0 = followed for >= 5 years; censored before 5 years excluded."""
    early = (d["event"] == 1) & (d["years"] < 5)
    sub = d[early | (d["years"] >= 5)]
    return sub, early[sub.index].astype(int)


def auc_ci(y, score, n_boot=N_BOOT, random_state=RANDOM_STATE):
    """AUC with a percentile bootstrap 95% CI (patients resampled with replacement; one-class resamples skipped)."""
    y, score = np.asarray(y), np.asarray(score, float)
    rng = np.random.default_rng(random_state)
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            boots.append(roc_auc_score(y[i], score[i]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return dict(auc=roc_auc_score(y, score), lo=lo, hi=hi, n=len(y), positives=int(y.sum()),
                n_boot=n_boot, random_state=random_state)


def roc_panel(ax, y, score, title):
    """One square ROC panel: curve in the accent colour, dashed chance diagonal, AUC [95% CI], n and positives."""
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
    side, bottom = 3.6, 0.65                 # two equal squares, the pair centred on the slide
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
    ("tsize", "Tumour size, smaller", -1),
]


def fig_auc_bars():
    """AUC for ER status of single predictors, bars from chance (0.5) with bootstrap 95% CIs.

    Orientation is flipped explicitly (``sign`` in AUC_ROWS) for predictors whose lower values go with
    ER-positive, and the row label names the direction. The direction was read off the same data, so a flipped
    AUC near 0.5 is descriptive only. Accent = CI excludes 0.5; grey = it does not.
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


# ---- 3 · Forest plot with a three-line number table --------------------------------------------------------
FOREST_ROWS = [  # (column, label on the figure, per SD?)
    ("age", "Age (per SD)", True),
    ("tsize", "Tumour size (per SD)", True),
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

    # Number columns: header and values share one column centre; three rules only (top, under header, bottom).
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


# ---- 4 · Three-line table ---------------------------------------------------------------------------------
def fig_table():
    d = load()
    groups = [("All", d), ("Tamoxifen", d[d.hormone_therapy == 1]), ("No tamoxifen", d[d.hormone_therapy == 0])]
    med = lambda s: f"{s.median():.0f} ({s.quantile(.25):.0f}–{s.quantile(.75):.0f})"
    pct = lambda m: f"{int(m.sum())} ({100 * m.mean():.0f}%)"
    body = [
        ("Patients", [f"{len(g)}" for _, g in groups]),
        ("Age, years, median (IQR)", [med(g.age) for _, g in groups]),
        ("Postmenopausal", [pct(g.postmenopausal) for _, g in groups]),
        ("Tumour size, mm, median (IQR)", [med(g.tsize) for _, g in groups]),
        ("Grade III", [pct(g.grade_3) for _, g in groups]),
        ("Positive nodes, median (IQR)", [med(g.pnodes) for _, g in groups]),
        ("Recurrence or death", [pct(g.event) for _, g in groups]),
    ]
    fig = plt.figure(figsize=(8.0, 3.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    xs = [0.04, 0.55, 0.72, 0.89]          # first column left edge, other columns centres
    n = len(body) + 1
    ys = [0.88 - i * 0.75 / (n - 1) for i in range(n)]
    ax.text(xs[0], ys[0], "Characteristic", ha="left", va="center", weight="bold", color=RULE)
    for x, (name, _) in zip(xs[1:], groups):
        ax.text(x, ys[0], name, ha="center", va="center", weight="bold", color=RULE)
    for yy, (label, vals) in zip(ys[1:], body):
        ax.text(xs[0], yy, label, ha="left", va="center")
        for x, v in zip(xs[1:], vals):
            ax.text(x, yy, v, ha="center", va="center")
    step = ys[0] - ys[1]
    for yy, lw in [(ys[0] + step / 2, 1.5), (ys[0] - step / 2, 0.75), (ys[-1] - step / 2, 1.5)]:
        ax.plot([0.02, 0.98], [yy, yy], color=RULE, lw=lw)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig, {"n": len(d)}


FIGURES = {
    "slide_anatomy": fig_slide_anatomy,
    "km_example": fig_km,
    "roc_example": fig_roc,
    "auc_bars_example": fig_auc_bars,
    "forest_example": fig_forest,
    "three_line_table_example": fig_table,
}


def write_run_meta(name: str, png: Path, stats) -> Path:
    """One JSON per figure (run_meta/<name>.json), so --only runs never overwrite other figures' records."""
    import lifelines
    meta_dir = OUT / "run_meta"
    meta_dir.mkdir(exist_ok=True)
    meta = {
        "figure": name,
        "png": png.name,
        "script": Path(__file__).name,
        "data": "GBSG2 trial, lifelines.datasets.load_gbsg2",
        "versions": {"lifelines": lifelines.__version__, "matplotlib": matplotlib.__version__},
        "created": pd.Timestamp.now().isoformat(timespec="seconds"),
        "stats": stats,
    }
    path = meta_dir / f"{name}.json"
    path.write_text(json.dumps(meta, indent=2, default=float) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", choices=sorted(FIGURES), help="draw only these figures")
    args = ap.parse_args()
    apply_style()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in args.only or FIGURES:
        fig, stats = FIGURES[name]()
        path = OUT / f"{name}.png"
        fig.savefig(path, dpi=DPI, facecolor="white")
        plt.close(fig)
        print(path, "->", write_run_meta(name, path, stats).name)


if __name__ == "__main__":
    main()

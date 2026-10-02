"""Tables drawn as figures: a three-line cohort table (shared/tables.md)."""

from __future__ import annotations

import matplotlib.pyplot as plt

from plotting.common import load
from plotting.style import RULE

INPUTS: list = []


def fig_table():
    d = load()
    groups = [("All", d), ("Tamoxifen", d[d.hormone_therapy == 1]), ("No tamoxifen", d[d.hormone_therapy == 0])]
    med = lambda s: f"{s.median():.0f} ({s.quantile(.25):.0f}–{s.quantile(.75):.0f})"
    pct = lambda m: f"{int(m.sum())} ({100 * m.mean():.0f}%)"
    body = [
        ("Patients", [f"{len(g)}" for _, g in groups]),
        ("Age, years, median (IQR)", [med(g.age) for _, g in groups]),
        ("Postmenopausal", [pct(g.postmenopausal) for _, g in groups]),
        ("Tumor size, mm, median (IQR)", [med(g.tsize) for _, g in groups]),
        ("Grade III", [pct(g.grade_3) for _, g in groups]),
        ("Positive nodes, median (IQR)", [med(g.pnodes) for _, g in groups]),
        ("Recurrence or death", [pct(g.event) for _, g in groups]),
    ]
    fig = plt.figure(figsize=(8.0, 3.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    xs = [0.04, 0.55, 0.72, 0.89]          # first column left edge, other columns centers
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
    "three_line_table_example": fig_table,
}

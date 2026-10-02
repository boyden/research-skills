"""Data loading and statistics shared by the figure modules; registers no figures.

Data: the GBSG2 trial shipped with lifelines (``lifelines.datasets.load_gbsg2``; 686 women, recurrence-free
survival). A project deck reads its result tables here instead and lists their paths in ``INPUTS``, which
``tools/plot.py`` adds to every figure's run_meta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

INPUTS: list[str] = []          # the public dataset ships with lifelines; there is no result table to list


def fmt_p(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def bh(p) -> np.ndarray:
    """Benjamini-Hochberg q-values."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    out = np.empty_like(q)
    out[order] = q
    return out


def load() -> pd.DataFrame:
    """GBSG2 with follow-up in years, the event flag and the derived binary / log-scaled factors."""
    from lifelines.datasets import load_gbsg2

    d = load_gbsg2()
    d["years"] = d["time"] / 365.25
    d["event"] = d["cens"].astype(int)
    d["hormone_therapy"] = (d["horTh"] == "yes").astype(int)
    d["postmenopausal"] = (d["menostat"] == "Post").astype(int)
    d["grade_3"] = (d["tgrade"] == "III").astype(int)
    for c in ["pnodes", "progrec", "estrec"]:
        d[f"log_{c}"] = np.log1p(d[c])
    return d


def cox_one(d: pd.DataFrame, col: str, per_sd: bool) -> dict:
    """Univariate Cox: HR per SD for a continuous variable, per unit (yes vs no) for a binary one."""
    from lifelines import CoxPHFitter

    x = d[col].astype(float)
    if per_sd:
        x = (x - x.mean()) / x.std()
    df = pd.DataFrame({"x": x, "years": d["years"], "event": d["event"]})
    m = CoxPHFitter().fit(df, "years", "event")
    s = m.summary.loc["x"]
    return dict(hr=s["exp(coef)"], lo=s["exp(coef) lower 95%"], hi=s["exp(coef) upper 95%"], p=s["p"],
                c=m.concordance_index_, n=len(df), events=int(df["event"].sum()))


def cohort(d: pd.DataFrame) -> dict:
    """Descriptive statistics of one group: n, medians with quartiles, counts with percentages."""
    def med(col):
        q1, q2, q3 = d[col].quantile([0.25, 0.5, 0.75])
        return {"median": q2, "q1": q1, "q3": q3}

    def count(mask):
        return {"n": int(mask.sum()), "pct": 100 * float(mask.mean())}

    return {"n": len(d), "age": med("age"), "postmenopausal": count(d["postmenopausal"] == 1),
            "tumor_size_mm": med("tsize"), "grade_3": count(d["grade_3"] == 1), "positive_nodes": med("pnodes"),
            "events": count(d["event"] == 1)}

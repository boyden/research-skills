"""Data loading and statistics shared by the example figure modules; registers no figures.

Data: the GBSG2 trial shipped with lifelines (``lifelines.datasets.load_gbsg2``), so there are no result
tables to list in ``INPUTS``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.datasets import load_gbsg2
from sklearn.metrics import roc_auc_score

INPUTS: list = []

N_BOOT = 2000
RANDOM_STATE = 0


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

"""
Numbers for the results example deck (examples/slides/results/) that are not in examples/figures/run_meta/:
cohort table, feature ranges, C-index of nested Cox models (apparent and 5-fold CV, random_state=0) and the
multivariable Cox. Computed from lifelines' load_gbsg2; written to results_stats.json next to this file
and copied by hand into the page files slides/<key>.js (the numbers on a slide must match this file).

    python examples/slides/results/results_stats.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.datasets import load_gbsg2
from lifelines.utils import concordance_index
from sklearn.model_selection import KFold

d = load_gbsg2()
d["years"] = d["time"] / 365.25
d["event"] = d["cens"].astype(int)
d["hormone_therapy"] = (d["horTh"] == "yes").astype(int)
d["postmenopausal"] = (d["menostat"] == "Post").astype(int)
d["grade_3"] = (d["tgrade"] == "III").astype(int)
for c in ["pnodes", "progrec", "estrec"]:
    d[f"log_{c}"] = np.log1p(d[c])

out = {}
groups = [("All", d), ("Tamoxifen", d[d.hormone_therapy == 1]), ("No tamoxifen", d[d.hormone_therapy == 0])]
med = lambda s: f"{s.median():.0f} ({s.quantile(.25):.0f}–{s.quantile(.75):.0f})"
pct = lambda m: f"{int(m.sum())} ({100 * m.mean():.0f}%)"
out["cohort"] = {
    "Patients": [f"{len(g)}" for _, g in groups],
    "Age": [med(g.age) for _, g in groups],
    "Postmenopausal": [pct(g.postmenopausal) for _, g in groups],
    "Tumor size": [med(g.tsize) for _, g in groups],
    "Grade III": [pct(g.grade_3) for _, g in groups],
    "Positive nodes": [med(g.pnodes) for _, g in groups],
    "Events": [pct(g.event) for _, g in groups],
    "Follow-up median years": [f"{g.years.median():.1f}" for _, g in groups],
}

# Feature ranges for the definition table
out["ranges"] = {c: [float(d[c].min()), float(d[c].median()), float(d[c].max())]
                 for c in ["age", "tsize", "pnodes", "progrec", "estrec"]}
out["sd"] = {c: float(d[c].std()) for c in ["age", "tsize", "log_pnodes", "log_progrec", "log_estrec"]}

MODELS = [
    ("Positive nodes", ["log_pnodes"]),
    ("Nodes + size + grade", ["log_pnodes", "tsize", "grade_3"]),
    ("All clinical", ["log_pnodes", "tsize", "grade_3", "age", "postmenopausal", "log_progrec", "log_estrec",
                      "hormone_therapy"]),
]


def std(df, cols, ref):
    x = df[cols].astype(float).copy()
    for c in cols:
        if ref[c].nunique() > 2:
            x[c] = (x[c] - ref[c].mean()) / ref[c].std()
    return x


rows = []
for name, cols in MODELS:
    x = std(d, cols, d)
    df = x.assign(years=d.years, event=d.event)
    m = CoxPHFitter().fit(df, "years", "event")
    app = m.concordance_index_
    cv = []
    for tr, te in KFold(5, shuffle=True, random_state=0).split(d):
        dtr, dte = d.iloc[tr], d.iloc[te]
        xtr = std(dtr, cols, dtr).assign(years=dtr.years, event=dtr.event)
        mm = CoxPHFitter().fit(xtr, "years", "event")
        risk = mm.predict_partial_hazard(std(dte, cols, dtr))
        cv.append(concordance_index(dte.years, -risk, dte.event))
    rows.append(dict(model=name, k=len(cols), c_app=app, c_cv=float(np.mean(cv)), c_cv_sd=float(np.std(cv)),
                     aic=m.AIC_partial_, n=len(d), events=int(d.event.sum())))
out["models"] = rows

# Multivariable (all clinical) HRs for the supplementary table
cols = MODELS[-1][1]
m = CoxPHFitter().fit(std(d, cols, d).assign(years=d.years, event=d.event), "years", "event")
s = m.summary
out["multi"] = [dict(var=c, hr=s.loc[c, "exp(coef)"], lo=s.loc[c, "exp(coef) lower 95%"],
                     hi=s.loc[c, "exp(coef) upper 95%"], p=s.loc[c, "p"]) for c in cols]

# Events by group for the supplementary table / numbers
out["events_by_arm"] = {"tam": int(d[d.hormone_therapy == 1].event.sum()),
                        "notam": int(d[d.hormone_therapy == 0].event.sum())}
out["median_nodes"] = float(d.pnodes.median())
text = json.dumps(out, indent=1, default=float, ensure_ascii=False)
(Path(__file__).resolve().parent / "results_stats.json").write_text(text + "\n")
print(text)

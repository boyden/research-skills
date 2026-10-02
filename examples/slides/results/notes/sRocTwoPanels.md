PATTERN: two panels side by side with one shared conclusion. Use it when two analyses answer the same question (here: how well does one variable discriminate) and the comparison is the point.

Design rules shown: both ROC panels are square and the same size, drawn in ONE native full-width figure (12.1 x 4.6 in); each panel states AUC [95% CI], n and positives; the diagonal marks chance.

Why not two separate figures: roc_example.png is already full width (12.1 in) and auc_bars_example.png is half width (5.9 in), so together they would need 18 in. Result figures are never scaled, so the pair would not fit; the two-panel ROC figure is used instead (the AUC bars appear on the figure + takeaways slide).

Numbers: roc_example run_meta. ER-positive = estrogen receptor >= 10 fmol/mg (n = 686, 497 positive). 5-year panel: recurrence or death before 5 years (285) vs followed >= 5 years event-free; patients censored before 5 years are excluded (n = 406). Bootstrap: 2,000 resamples, percentile CI, random_state 0.

Caution: PR and ER are correlated receptor assays, so AUC 0.877 shows co-expression, not a clinical test.

PATTERN: model comparison table. Use it to compare nested models on one metric; order rows from simplest to fullest so the gain per added block reads top to bottom.

Design rules shown: three-line table, numbers to three decimals in every column; the apparent C-index is labeled as apparent (same patients), next to a cross-validated value; the conclusion says 'same patients'.

Numbers: recomputed from load_gbsg2. Continuous variables standardized (per SD); nodes, PR and ER as log(1 + x). Apparent C-index = lifelines concordance_index_ of the fitted model. CV: sklearn KFold(5, shuffle=True, random_state=0), standardization from the training fold, Harrell's C on the test fold, mean over folds (fold SD 0.052, 0.061, 0.043).

Over-reading: there is no external validation set; the gain of 0.04–0.05 is within the fold-to-fold spread.

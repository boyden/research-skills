**English** | [简体中文](01_results.zh-CN.md)

# 1 Results (example chapter on the public GBSG2 data)

> This chapter covers {{sTitle}}–{{sSuppTable}}. The block format is in `reference/outline-format.md` §2. The slide order is set by `section` and `order` in each page file; the numbers here (1.1, 1.2 …) are content numbers, not page numbers.
> For your own project, keep the block structure and replace the titles, Messages, figures, numbers and sources. All example numbers come from the GBSG2 data shipped with lifelines (686 women, 299 recurrence or death events) and are drawn by `plotting/results.py`.

## Title

### 0.1 Title ✏️ · {{sTitle}}
- **Message**: <Talk title in English>
- **On screen**: title, presenter and role, affiliation, date; no numbers, no figure.
- **Speaker notes** (`notes/sTitle.md`): one opening sentence: what the talk covers and which data it uses.

## Results

### 1.1 Hormone Therapy — Recurrence-free Survival ✅ · {{sKm}}
- **Message**: Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).
- **Figure**: `figures/results_km.png` (`fig_km` in `plotting/results.py`, registered name `results_km`, 12.1 × 4.6 in):
  two equal square KM panels, tamoxifen vs no tamoxifen on the left, positive lymph nodes split at the median on the right; each panel shows HR [95% CI],
  Cox p, C-index and log-rank p on its right, with the number at risk below. The lower curve (worse prognosis) is red, the upper one blue.
- **Numbers** (run_meta `results_km.json`, `stats.hormone_therapy`): HR 0.695 [0.544–0.888] (yes vs no), Cox p 0.0036,
  C-index 0.543, log-rank p 0.0034; n = 686, 299 events. On screen, HR has two decimals and p three.
  The right panel's numbers (`stats.log_pnodes`) are only in the figure; the conclusion does not mention them.
- **Source**: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival
- **What could be over-read (speaker notes only, not on screen)**: univariate Cox, not adjusted for age or menopausal status, and the two groups differ in both (see {{sSuppTable}}), so it says *associated with*, not *improves*.
- **Speaker notes** (`notes/sKm.md`): the HR is yes vs no; the right panel's HR is per SD of log(1 + nodes), drawn as a median split.

### 1.2 Clinical Factors — Univariate Cox ✅ · {{sForest}}
- **Message**: More positive lymph nodes are most strongly associated with shorter recurrence-free survival (HR 1.65 [1.48–1.84] per SD, q < 0.001; n = 686, 299 events).
- **Figure**: `figures/results_forest.png` (`fig_forest` in `plotting/results.py`, registered name `results_forest`, 12.1 × 4.6 in):
  one row per factor, log x axis with the reference line at 1; the number columns on the right are a three-line table; rows with q < 0.05 in the accent color, the others gray.
- **Numbers** (run_meta `results_forest.json`, `stats.rows`; eight univariate Cox models, BH q computed over these eight):
  positive nodes, per SD of log(1 + nodes), HR 1.650 [1.479–1.841], p 3.5e-19, q 2.8e-18; PR per SD 0.661 [0.590–0.739];
  tumor size per SD 1.236 [1.121–1.364]; six of eight have q < 0.05. Continuous factors always per SD, binary ones yes vs no.
- **Source**: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival
- **What could be over-read (speaker notes only, not on screen)**: "strongest" means the largest absolute log HR per SD among univariate models; the eight factors are not mutually adjusted.
- **Speaker notes** (`notes/sForest.md`).

## Summary

### 2.1 Summary ✏️ · {{sSummary}}
- **Message** (three items, each one claim and one line of evidence):
  1. Tamoxifen is associated with longer recurrence-free survival — HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events (univariate Cox)
  2. Positive lymph nodes carry the strongest univariate association — HR 1.65 [1.48–1.84] per SD, q < 0.001; largest effect of eight clinical factors
  3. The tamoxifen group differs at baseline — Older (median 58 vs 50 years) and more often postmenopausal (76% vs 48%); see Supplementary
- **Numbers**: items 1 and 2 are copied from the blocks of {{sKm}} and {{sForest}}, item 3 from {{sSuppTable}}; no new numbers here.
- **Speaker notes** (`notes/sSummary.md`): say which slide each item comes from; item 3 is the limitation: the univariate tamoxifen HR may be confounded by age and menopausal status.

## Supplementary

### S.1 Supplementary — Cohort Characteristics ✏️ · {{sSuppTable}}
- **Message**: Women given tamoxifen were older (median 58 vs 50 years) and more often postmenopausal (76% vs 48%); tumor size, grade and nodes were similar (n = 686).
- **On screen**: native three-line table, 7 rows × 4 columns (characteristic; All n = 686, Tamoxifen n = 246, No tamoxifen n = 440), 16 pt, first column left-aligned, the others centered;
  this section is hidden in the pptx and exported to the PDF as usual.
- **Numbers** (run_meta `results_km.json`, `stats.cohort.all` / `tamoxifen` / `no_tamoxifen`): median age 53 / 58 / 50 years;
  postmenopausal 396 (58%) / 187 (76%) / 209 (48%); grade III 161 (23%) / 50 (20%) / 111 (25%); recurrence or death 299 (44%) / 94 (38%) / 205 (47%).
  Tumor size 25 (20–35) mm and positive nodes 3 (1–7) are the same in all three columns: confirmed (2026-10-01, recomputed per group from `load_gbsg2` in `common.cohort`).
- **Source**: GBSG2 trial (lifelines load_gbsg2), descriptive statistics; reference `schumacher1994` (`refs` in `deck.config.js`)
- **What could be over-read (speaker notes only, not on screen)**: "similar" is descriptive; no group comparison was tested.
- **Speaker notes** (`notes/sSuppTable.md`).

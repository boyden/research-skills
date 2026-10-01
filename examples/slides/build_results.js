/*
 * Gallery of classic result-slide patterns, built on the public GBSG2 example figures.
 *
 *   NODE_PATH=<dir with pptxgenjs> node examples/slides/build_results.js
 *   -> examples/slides/output/results_examples.pptx
 *
 * Every number on a slide comes from the stats printed by examples/make_example_figures.py
 * (figures/run_meta/*.json) or from lifelines' load_gbsg2 recomputed in Python (cohort table,
 * C-index of nested Cox models, multivariable Cox); the values are written in RESULTS below.
 * Each slide carries a small grey "Pattern: ..." label and speaker notes on when to use it.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const {
  C, FONT, SW, MX, CW, FIG_Y, b, toRuns, text, bullets, rect, figure, table,
  newSlide, conclusion, source, draft, newDeck, pattern, line, emphasis,
} = require("./common");

const OUT = path.join(__dirname, "output");

// ---- Numbers (GBSG2, n = 686, 299 recurrence-or-death events) ----------------------------------
// km_example / forest_example run_meta; cohort, models and multivariable Cox recomputed from load_gbsg2.
const SRC_COX = "Source: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival";
const SRC_KM = "Source: GBSG2 trial (lifelines load_gbsg2); Kaplan–Meier, univariate Cox and log-rank, recurrence-free survival";

// ---- Local helpers -----------------------------------------------------------------------------
// "ABBR: expansion; ABBR: expansion." bottom left, bottom-aligned so it sits on the source line.
function abbr(slide, entries, w = 6.0) {
  const runs = entries.flatMap(([a, e], i) => [...(i ? [" "] : []), b(`${a}: `), `${e}${i < entries.length - 1 ? ";" : "."}`]);
  slide.addText(toRuns({ runs }, { fontSize: 9.5, color: C.muted }),
    { x: MX, y: 6.85, w, h: 0.55, margin: 0, valign: "bottom", align: "left", fontFace: FONT, wrap: true });
}

const ABBR_COX = [["HR", "hazard ratio"], ["CI", "confidence interval"], ["SD", "standard deviation"],
  ["PR", "progesterone receptor"], ["ER", "oestrogen receptor"], ["q", "Benjamini–Hochberg adjusted p"]];

// ---- Deck --------------------------------------------------------------------------------------
const pres = newDeck("Result slide patterns");
let n = 0;

// 1 · Assertion–evidence ------------------------------------------------------------------------
{
  const s = newSlide(pres, "Recurrence-free Survival", ++n);
  pattern(s, "Pattern: assertion–evidence");
  figure(s, "km_example.png");
  conclusion(s, "Tamoxifen is associated with longer, and more positive nodes with shorter, recurrence-free " +
    "survival (HR 0.69 [0.54–0.89], p = 0.004; HR 1.65 [1.48–1.84] per SD, p < 0.001; n = 686, 299 events).");
  abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["C-index", "concordance index"]]);
  source(s, SRC_KM);
  s.addNotes([
    "PATTERN: assertion–evidence. Use it for the main result of a section: one figure, one sentence.",
    "Design rules shown: the title names the topic, not the finding; the figure is drawn at its on-slide size " +
    "(12.1 x 4.6 in, 200 dpi) and placed 1:1, never scaled; the single bold conclusion at the bottom carries the " +
    "effect size with interval, p, n and events; the source line sits bottom right in 9 pt serif.",
    "Numbers: km_example run_meta (hormone_therapy: HR 0.695 [0.544–0.888], Cox p 0.0036, log-rank p 0.0034; " +
    "log_pnodes: HR per SD 1.650 [1.479–1.841], Cox p 3.5e-19). HR for tamoxifen is yes vs no; nodes per SD of log(1 + nodes).",
    "Wording: observational association, so 'associated with', not 'improves'.",
  ].join("\n\n"));
}

// 2 · Two panels, one shared conclusion -----------------------------------------------------------
{
  const s = newSlide(pres, "Discrimination — ROC", ++n);
  pattern(s, "Pattern: two panels, one conclusion");
  figure(s, "roc_example.png");
  conclusion(s, "PR level separates ER status well (AUC 0.877 [0.849–0.904]; 497 of 686 ER-positive), whereas " +
    "nodes predict 5-year recurrence only moderately (AUC 0.671 [0.619–0.724]; 285 of 406 recurred).");
  abbr(s, [["ROC", "receiver operating characteristic"], ["AUC", "area under the curve"],
    ["PR", "progesterone receptor"], ["ER", "oestrogen receptor"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); ROC with 2,000-sample bootstrap 95% CI, random_state 0");
  s.addNotes([
    "PATTERN: two panels side by side with one shared conclusion. Use it when two analyses answer the same " +
    "question (here: how well does one variable discriminate) and the comparison is the point.",
    "Design rules shown: both ROC panels are square and the same size, drawn in ONE native full-width figure " +
    "(12.1 x 4.6 in); each panel states AUC [95% CI], n and positives; the diagonal marks chance.",
    "Why not two separate figures: roc_example.png is already full width (12.1 in) and auc_bars_example.png is " +
    "half width (5.9 in), so together they would need 18 in. Result figures are never scaled, so the pair would " +
    "not fit; the two-panel ROC figure is used instead (the AUC bars appear on the figure + takeaways slide).",
    "Numbers: roc_example run_meta. ER-positive = oestrogen receptor >= 10 fmol/mg (n = 686, 497 positive). " +
    "5-year panel: recurrence or death before 5 years (285) vs followed >= 5 years event-free; patients censored " +
    "before 5 years are excluded (n = 406). Bootstrap: 2,000 resamples, percentile CI, random_state 0.",
    "Caution: PR and ER are correlated receptor assays, so AUC 0.877 shows co-expression, not a clinical test.",
  ].join("\n\n"));
}

// 3 · Forest plot, full width ------------------------------------------------------------------------
{
  const s = newSlide(pres, "Clinical Factors — Univariate Cox", ++n);
  pattern(s, "Pattern: forest plot");
  figure(s, "forest_example.png");
  conclusion(s, "More positive lymph nodes are most strongly associated with shorter recurrence-free survival " +
    "(HR 1.65 [1.48–1.84] per SD, q < 0.001; n = 686, 299 events).");
  abbr(s, ABBR_COX);
  source(s, SRC_COX);
  s.addNotes([
    "PATTERN: forest plot, full width. Use it for many effect sizes on one scale (one row per factor).",
    "Design rules shown: log x axis with a reference line at 1; the number column on the right is a three-line " +
    "table with centred columns; only rows with q < 0.05 are drawn in the accent colour, the rest grey; HR is " +
    "per SD for continuous and yes vs no for binary factors, fixed once for the whole deck.",
    "Numbers: forest_example run_meta (8 univariate Cox models, Benjamini–Hochberg q over the 8). Strongest: " +
    "positive nodes, log(1 + nodes) per SD, HR 1.650 [1.479–1.841], p 3.5e-19.",
    "'Strongest' means largest |log HR| per SD in univariate models; it is not adjusted for the other factors.",
  ].join("\n\n"));
}

// 4 · Native three-line table ------------------------------------------------------------------------
{
  const s = newSlide(pres, "Cohort Characteristics", ++n);
  pattern(s, "Pattern: native three-line table");
  const rows = [
    ["Characteristic", ["All", "n = 686"], ["Tamoxifen", "n = 246"], ["No tamoxifen", "n = 440"]],
    ["Age, years, median (IQR)", "53 (46–61)", "58 (50–63)", "50 (45–59)"],
    ["Postmenopausal, n (%)", "396 (58%)", "187 (76%)", "209 (48%)"],
    ["Tumour size, mm, median (IQR)", "25 (20–35)", "25 (20–35)", "25 (20–35)"],
    ["Grade III, n (%)", "161 (23%)", "50 (20%)", "111 (25%)"],
    ["Positive nodes, median (IQR)", "3 (1–7)", "3 (1–7)", "3 (1–7)"],
    ["Recurrence or death, n (%)", "299 (44%)", "94 (38%)", "205 (47%)"],
  ];
  const colW = [4.3, 2.5, 2.5, 2.5];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.3, colW, [0.8, ...Array(rows.length - 1).fill(0.5)], rows, { fontSize: 16 });
  conclusion(s, "Women given tamoxifen were older (median 58 vs 50 years) and more often postmenopausal " +
    "(76% vs 48%); tumour size, grade and nodes were similar (n = 686).");
  abbr(s, [["IQR", "interquartile range"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); descriptive statistics by hormone therapy");
  s.addNotes([
    "PATTERN: native three-line table. Use it for a cohort table or any small grid of numbers the audience reads " +
    "cell by cell; native tables stay editable and sharp, unlike a table pasted as an image.",
    "Design rules shown: three rules only (thick top, thin under header, thick bottom), no vertical lines, no fill; " +
    "first column left-aligned, all other columns centred (header and values share a centre); header bold, same " +
    "size as the body; n per group in the header; ranges with an en dash.",
    "Numbers: recomputed from lifelines load_gbsg2 (same code as fig_table in make_example_figures.py).",
    "Over-reading: the age and menopause imbalance means the univariate tamoxifen HR may be confounded; see the " +
    "multivariable supplementary slide.",
  ].join("\n\n"));
}

// 5 · Key numbers ------------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Study at a Glance", ++n);
  pattern(s, "Pattern: key numbers");
  const items = [
    ["686", "patients", "Node-positive breast cancer"],
    ["299", "recurrence-or-death events", "44% of patients"],
    ["0.69", "HR, tamoxifen vs none", "95% CI 0.54–0.89; p = 0.004"],
  ];
  const colW = CW / 3;
  items.forEach(([num, label, sub], i) => {
    const x = MX + i * colW;
    const y0 = 1.9;
    text(s, x, y0, colW, 1.3, { runs: [num], align: "center" }, { fontSize: 72, bold: true, color: C.accent, valign: "middle" });
    text(s, x, y0 + 1.35, colW, 0.45, { runs: [label], align: "center" }, { fontSize: 20, bold: true, color: C.text });
    text(s, x + 0.3, y0 + 1.85, colW - 0.6, 0.7, { runs: [sub], align: "center" }, { fontSize: 14, color: C.muted });
  });
  conclusion(s, "Tamoxifen is associated with longer recurrence-free survival " +
    "(HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).");
  abbr(s, [["HR", "hazard ratio"], ["CI", "confidence interval"]]);
  source(s, SRC_COX);
  s.addNotes([
    "PATTERN: key numbers ('big number'). Use it sparingly: opening a results section, or the one slide people " +
    "should remember. Three numbers at most; each needs a one-line label and its context (interval, denominator).",
    "Design rules shown: large numerals in the single accent colour, labels in grey, no decoration; conclusion " +
    "and source still present, so the big number is never shown without its n and interval.",
    "Numbers: n and events from load_gbsg2; 44% = 299/686; median observed time (not reverse Kaplan–Meier " +
    "follow-up) 3.0 years; HR from km_example run_meta (0.695 [0.544–0.888], p 0.0036).",
  ].join("\n\n"));
}

// 6 · Figure + takeaways ---------------------------------------------------------------------------
{
  const s = newSlide(pres, "Single Predictors of ER Status", ++n);
  pattern(s, "Pattern: figure + takeaways");
  const f = figure(s, "auc_bars_example.png", FIG_Y, MX);
  const x = f.x + f.w + 0.4;
  text(s, x, 1.55, SW - MX - x, 0.4, "Takeaways", { fontSize: 18, bold: true, color: C.text });
  bullets(s, x, 2.1, SW - MX - x, 3.3, [
    "PR level is by far the strongest (AUC 0.877)",
    "Grade and age add little (AUC 0.656, 0.568)",
    "Nodes and tumour size: CIs include 0.5",
  ], 18);
  conclusion(s, "Of five clinical variables, only PR level discriminates ER status well " +
    "(AUC 0.877 [0.849–0.904]; 497 of 686 ER-positive).");
  abbr(s, [["AUC", "area under the curve"], ["CI", "confidence interval"], ["ER", "oestrogen receptor"],
    ["PR", "progesterone receptor"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); AUC with 2,000-sample bootstrap 95% CI, random_state 0");
  s.addNotes([
    "PATTERN: figure + takeaways split. Use it when a half-width figure needs two or three reading hints that do " +
    "not fit into one sentence. The takeaways guide the eye; the conclusion still states the one finding.",
    "Design rules shown: the figure is drawn half width (5.9 x 4.6 in) and placed 1:1 on the left; at most three " +
    "short grey bullets at 18 pt on the right; bars start at chance (0.5); accent = CI excludes 0.5.",
    "Numbers: auc_bars_example run_meta (n = 686, 497 ER-positive, 2,000 bootstrap resamples, random_state 0). " +
    "Grade I–II [0.618–0.694], age [0.519–0.618], nodes [0.498–0.602], tumour size [0.458–0.554].",
    "Over-reading: the direction of the flipped predictors (grade, nodes, size) was read off the same data, so " +
    "AUCs near 0.5 are descriptive only.",
  ].join("\n\n"));
}

// 7 · Callout / annotated figure ---------------------------------------------------------------------
{
  const s = newSlide(pres, "Reading the Kaplan–Meier Panel", ++n);
  pattern(s, "Pattern: callout");
  const f = figure(s, "km_example.png");
  // Number-at-risk table of the left panel (measured on the 12.1 x 4.6 in figure: x 0.09–3.99, y 3.90–4.55 in).
  const box = { x: f.x + 0.06, y: f.y + 3.87, w: 3.97, h: 0.71 };
  rect(s, box.x, box.y, box.w, box.h, { line: C.accent, lineW: 1.5 });
  // Callout in the white space right of the left panel's statistics.
  const cx = f.x + 4.55, cy = f.y + 1.35, cw = 2.2, ch = 1.45;
  rect(s, cx, cy, cw, ch, { fill: C.white, line: C.accent, lineW: 0.75 });
  text(s, cx + 0.08, cy + 0.06, cw - 0.16, ch - 0.12, [
    { runs: [b("Number at risk")], after: 4 },
    "Patients still event-free and followed at 0, 2, 4 and 6 years. Only 18 per arm remain at 6 years.",
  ], { fontSize: 12, color: C.ink });
  line(s, cx + 0.05, cy + ch, box.x + box.w - 0.05, box.y);
  conclusion(s, "By 6 years only 18 women per arm remain at risk, so the curves beyond 6 years rest on " +
    "few patients (n = 686, 299 events).");
  abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["C-index", "concordance index"]]);
  source(s, SRC_KM);
  s.addNotes([
    "PATTERN: callout / annotated figure. Use it when the audience must learn to read a figure type (first KM in " +
    "a talk, an unfamiliar plot), or when one region carries the message.",
    "Design rules shown: the figure itself is unchanged and placed 1:1; the highlight is a thin accent rectangle " +
    "and the callout a small native text box joined by a thin line, so both stay editable and can be removed; " +
    "the callout sits in white space and covers no data.",
    "Numbers: at-risk counts drawn in km_example (follow-up >= t): tamoxifen 246, 177, 104, 18; no tamoxifen " +
    "440, 281, 124, 18 at 0, 2, 4, 6 years.",
  ].join("\n\n"));
}

// 8–9 · Progressive emphasis (build without animation) --------------------------------------------------
// Rows 2–6 and 8 of the forest figure have q < 0.05 (row pitch 0.405 in, row 1 centre at y 0.74 in).
const FOREST_ROW = (i) => 0.74 + (i - 1) * 0.405;
for (const step of [1, 2]) {
  const s = newSlide(pres, "Clinical Factors — Univariate Cox", ++n);
  pattern(s, `Pattern: progressive emphasis ${step}/2`);
  const f = figure(s, "forest_example.png");
  if (step === 1) {
    conclusion(s, "Hazard ratios range from 0.66 per SD (PR receptor) to 1.65 per SD (positive nodes) " +
      "across eight clinical factors (n = 686, 299 events).");
  } else {
    const x0 = f.x + 0.85, x1 = f.x + 11.97, half = 0.2;
    emphasis(s, x0, f.y + FOREST_ROW(2) - half, x1 - x0, FOREST_ROW(6) - FOREST_ROW(2) + 2 * half);
    emphasis(s, x0, f.y + FOREST_ROW(8) - half, x1 - x0, 2 * half);
    conclusion(s, "Six of eight factors have q < 0.05 (all q ≤ 0.005): larger tumours, more nodes and grade III " +
      "with shorter, higher receptor levels and tamoxifen with longer recurrence-free survival.");
  }
  abbr(s, ABBR_COX);
  source(s, SRC_COX);
  s.addNotes([
    `PATTERN: progressive emphasis, step ${step} of 2. Use two consecutive slides with the same figure in the same ` +
    "position instead of an animation: step 1 shows the whole picture, step 2 adds a highlight and a new " +
    "conclusion. It survives PDF export and printed handouts, where animations are lost.",
    "Design rules shown: the figure does not move between the two slides (identical x, y, size), so flipping " +
    "between them reads as a build; the highlight is a semi-transparent accent box over the q < 0.05 rows only; " +
    "the conclusion changes with the emphasis.",
    "Numbers: forest_example run_meta. q < 0.05: tumour size, nodes, PR, ER, grade III, tamoxifen (largest q = " +
    "0.0048 for grade III and tamoxifen). Not significant: age (q 0.510), postmenopausal (q 0.596).",
  ].join("\n\n"));
}

// 10 · Feature-definition table ---------------------------------------------------------------------
{
  const s = newSlide(pres, "Feature Definitions", ++n);
  pattern(s, "Pattern: feature-definition table");
  const rows = [
    ["Feature", "Low → high", "What is computed (unit)", "Higher value", "Lower value", "HR > 1 means"],
    ["Age", "21 → 80 years", ["Age at entry (years)", "per SD = 10.1 years"], "Older", "Younger",
      "Older recur sooner"],
    ["Tumour size", "3 → 120 mm", ["Largest diameter (mm)", "per SD = 14.3 mm"], "Larger", "Smaller",
      "Larger recur sooner"],
    ["Positive nodes", "1 → 51 nodes", ["log(1 + nodes)", "per SD = 0.72"], "More nodes", "Fewer nodes",
      "More nodes recur sooner"],
    ["PR receptor", "0 → 2,380 fmol/mg", ["log(1 + PR, fmol/mg)", "per SD = 1.93"], "More PR", "Less PR",
      "More PR recur sooner"],
    ["Grade III", "I–II → III", ["Grade III vs I–II", "yes vs no"], "Grade III", "Grade I–II",
      "Grade III recur sooner"],
  ];
  const colW = [1.6, 2.0, 3.0, 1.5, 1.5, 2.5];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.3, colW, [0.5, 0.72, 0.72, 0.72, 0.72, 0.72], rows, { fontSize: 13, labelCol: true });
  conclusion(s, "Continuous features are scaled per SD in this cohort (n = 686), so HR > 1 means a one-SD " +
    "higher value goes with shorter recurrence-free survival.");
  abbr(s, [["HR", "hazard ratio"], ["SD", "standard deviation"], ["PR", "progesterone receptor"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); ranges and SDs over all 686 patients");
  s.addNotes([
    "PATTERN: feature-definition table. Use it before the first result that uses engineered or transformed " +
    "features, so 'HR 1.65 per SD' can be read without the methods section.",
    "Design rules shown: three-line table; first column left (bold feature names), all other columns centred; " +
    "the 'Low → high' column gives the observed range (text here; a pair of small icons can replace it when " +
    "suitable ones exist); the last column turns the sign of the HR into plain words.",
    "Numbers: min, max and SD recomputed from load_gbsg2 (SD of log1p values for nodes and PR). The 'HR > 1 means' " +
    "column defines how to read the sign; the observed direction for PR is HR < 1 (forest plot).",
  ].join("\n\n"));
}

// 11 · Model comparison ----------------------------------------------------------------------------
{
  const s = newSlide(pres, "Model Comparison — C-index", ++n);
  pattern(s, "Pattern: model comparison");
  const rows = [
    ["Cox model", "Variables", "Apparent C-index", "5-fold CV C-index"],
    ["Positive nodes", "1", "0.645", "0.646"],
    ["Nodes + size + grade", "3", "0.655", "0.650"],
    ["All clinical", "8", "0.698", "0.688"],
  ];
  const colW = [4.0, 2.0, 2.8, 2.8];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.7, colW, 0.6, rows, { fontSize: 16 });
  text(s, (SW - w) / 2, 4.35, w, 0.9, [
    "All clinical = nodes, tumour size, grade III, age, postmenopausal, PR, ER and tamoxifen. Apparent C-index: " +
    "fitted and evaluated on the same 686 patients.",
  ], { fontSize: 14, color: C.text });
  conclusion(s, "Adding all eight clinical variables raises the apparent C-index from 0.645 (nodes only) to 0.698 " +
    "on the same patients (n = 686, 299 events); 5-fold CV gives 0.688.");
  abbr(s, [["C-index", "concordance index"], ["CV", "cross-validation"], ["PR", "progesterone receptor"],
    ["ER", "oestrogen receptor"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); multivariable Cox, Harrell's C; KFold(5, shuffle, random_state 0)");
  s.addNotes([
    "PATTERN: model comparison table. Use it to compare nested models on one metric; order rows from simplest to " +
    "fullest so the gain per added block reads top to bottom.",
    "Design rules shown: three-line table, numbers to three decimals in every column; the apparent C-index is " +
    "labelled as apparent (same patients), next to a cross-validated value; the conclusion says 'same patients'.",
    "Numbers: recomputed from load_gbsg2. Continuous variables standardised (per SD); nodes, PR and ER as " +
    "log(1 + x). Apparent C-index = lifelines concordance_index_ of the fitted model. CV: sklearn KFold(5, " +
    "shuffle=True, random_state=0), standardisation from the training fold, Harrell's C on the test fold, mean " +
    "over folds (fold SD 0.052, 0.061, 0.043).",
    "Over-reading: there is no external validation set; the gain of 0.04–0.05 is within the fold-to-fold spread.",
  ].join("\n\n"));
}

// 12 · Draft slide ---------------------------------------------------------------------------------
{
  const s = newSlide(pres, "Tamoxifen — Adjusted Hazard Ratio", ++n);
  draft(s);
  text(s, SW - 3.75, 1.02, 3.4, 0.3, "Pattern: draft", { fontSize: 12, italic: true, color: C.muted, align: "right" });
  const rows = [
    ["Cox model for tamoxifen", "HR [95% CI]", "p", "n (events)"],
    ["Univariate", "0.69 [0.54–0.89]", "0.004", "686 (299)"],
    ["Adjusted for 7 clinical variables", "0.68 [0.53–0.88]", "0.003", "686 (299)"],
  ];
  const colW = [4.6, 2.8, 1.6, 2.2];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.9, colW, 0.6, rows, { fontSize: 16 });
  text(s, (SW - w) / 2, 3.95, w, 0.9, [
    "Adjusted for positive nodes, tumour size, grade III, age, postmenopausal status, PR and ER (continuous per SD).",
  ], { fontSize: 14, color: C.text });
  conclusion(s, "After adjustment for seven clinical variables the tamoxifen HR barely changes " +
    "(0.68 [0.53–0.88] vs 0.69 unadjusted, p = 0.003; n = 686, 299 events).");
  abbr(s, [["HR", "hazard ratio"], ["CI", "confidence interval"], ["PR", "progesterone receptor"],
    ["ER", "oestrogen receptor"]]);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); multivariable Cox, recurrence-free survival");
  s.addNotes([
    "PATTERN: draft. Use the grey 'DRAFT – to be confirmed' tag on any slide whose numbers are not yet final, so " +
    "nobody copies them into a report; remove the tag only after the checks below are done.",
    "⚠️ CAVEAT (to confirm before removing the DRAFT tag): proportional hazards not yet checked for the adjusted " +
    "model; the adjustment set was chosen for this example, not prespecified; hormone therapy was not randomised " +
    "for every patient in GBSG2, so residual confounding remains.",
    "Numbers: univariate HR from km_example run_meta; adjusted HR recomputed from load_gbsg2 (lifelines " +
    "CoxPHFitter, 8 covariates, HR 0.681 [0.529–0.877], p 0.0029).",
  ].join("\n\n"));
}

// 13 · Supplementary (hidden) ------------------------------------------------------------------------
{
  const s = newSlide(pres, "Supplementary — Univariate vs Multivariable", ++n);
  s.hidden = true;
  pattern(s, "Pattern: supplementary (hidden)");
  const rows = [
    ["Variable", "Univariate HR [95% CI]", "p", "q", "Multivariable HR [95% CI]", "p"],
    ["Age (per SD)", "0.96 [0.85–1.07]", "0.446", "0.510", "0.92 [0.77–1.10]", "0.341"],
    ["Tumour size (per SD)", "1.24 [1.12–1.36]", "<0.001", "<0.001", "1.05 [0.94–1.18]", "0.348"],
    ["Positive nodes, log (per SD)", "1.65 [1.48–1.84]", "<0.001", "<0.001", "1.58 [1.41–1.78]", "<0.001"],
    ["PR receptor, log (per SD)", "0.66 [0.59–0.74]", "<0.001", "<0.001", "0.67 [0.58–0.78]", "<0.001"],
    ["ER receptor, log (per SD)", "0.78 [0.69–0.87]", "<0.001", "<0.001", "1.06 [0.91–1.24]", "0.456"],
    ["Grade III vs I–II", "1.48 [1.14–1.91]", "0.003", "0.005", "1.09 [0.83–1.44]", "0.524"],
    ["Postmenopausal", "1.06 [0.84–1.34]", "0.596", "0.596", "1.22 [0.86–1.75]", "0.266"],
    ["Tamoxifen", "0.69 [0.54–0.89]", "0.004", "0.005", "0.68 [0.53–0.88]", "0.003"],
  ];
  const colW = [3.4, 2.4, 1.1, 1.1, 2.7, 1.1];
  const w = colW.reduce((a, c) => a + c, 0);
  table(s, (SW - w) / 2, 1.2, colW, 0.44, rows, { fontSize: 13 });
  conclusion(s, "Nodes, PR receptor and tamoxifen stay associated in the multivariable model (HR 1.58, 0.67, 0.68; " +
    "all p ≤ 0.003); tumour size, grade III and ER do not (n = 686, 299 events).");
  abbr(s, ABBR_COX);
  source(s, "Source: GBSG2 trial (lifelines load_gbsg2); univariate (forest_example) and 8-variable Cox");
  s.addNotes([
    "PATTERN: supplementary slide, hidden in the slide show. Use it for the dense supplementary table you expect a " +
    "question about; it stays in the file and can be jumped to, but is skipped when presenting.",
    "Design rules shown: still one topic title, one conclusion and a source; the table may be denser (13 pt, 9 " +
    "rows) because it is read on demand, not presented. Hidden with pptxgenjs slide.hidden = true (show=\"0\").",
    "Numbers: univariate from forest_example run_meta; multivariable recomputed from load_gbsg2 (same 8 " +
    "covariates, continuous per SD). q only for the univariate screen (8 tests).",
    "Over-reading: ER loses its association once PR is in the model (the two receptors are correlated); this is " +
    "not evidence that ER is irrelevant.",
  ].join("\n\n"));
}

fs.mkdirSync(OUT, { recursive: true });
pres.writeFile({ fileName: path.join(OUT, "results_examples.pptx") }).then((f) => console.log("wrote", f));

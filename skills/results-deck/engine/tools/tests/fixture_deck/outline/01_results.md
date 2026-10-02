[English](01_results.md) | **简体中文**

# 1 结果（公开数据 GBSG2 的示例章）

> 本章管 {{sTitle}}–{{sSuppTable}}。逐页块的格式见 `reference/outline-format.md` §2；页序由各页文件的 `section` 和 `order` 决定，这里的编号（1.1、1.2 …）是内容编号，不是页号。
> 换成自己的项目时，保留块的结构，替换标题、Message、图、数字和来源；示例数字全部来自 lifelines 自带的 GBSG2（686 例，299 个复发或死亡事件），由 `plotting/results.py` 画出。

## 标题页

### 0.1 Title ✏️ · {{sTitle}}
- **Message**: <Talk title in English>
- **上屏**：题目、讲者职称、单位、日期；不放数字，不放图。
- **Speaker notes**（`notes/sTitle.md`）：一句开场：这次讲什么、用的什么数据。

## 结果

### 1.1 Hormone Therapy — Recurrence-free Survival ✅ · {{sKm}}
- **Message**: Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).
- **Figure**: `figures/results_km.png`（`plotting/results.py` 的 `fig_km`，注册名 `results_km`，12.1 × 4.6 in）：
  两个等大的正方形 KM，左边 tamoxifen vs no tamoxifen，右边阳性淋巴结按中位数分组；每个 panel 右侧写 HR [95% CI]、
  Cox p、C-index、log-rank p，下方是 number at risk。预后差的那条红、预后好的那条蓝。
- **数字**（run_meta `results_km.json` 的 `stats.hormone_therapy`）：HR 0.695 [0.544–0.888]（yes vs no），Cox p 0.0036，
  C-index 0.543，log-rank p 0.0034；n = 686，299 个事件。上屏 HR 两位小数，p 三位小数。右边 panel 的数字（`stats.log_pnodes`）只在图里，结论句不讲它。
- **Source**: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival
- **可能被过度解读（只在讲稿，不上屏）**：单变量 Cox，没有调整年龄和绝经状态，而两组在这两项上不同（见 {{sSuppTable}}），所以写 *associated with*，不写 *improves*。
- **Speaker notes**（`notes/sKm.md`）：HR 是 yes vs no；右边 panel 的 HR 是 log(1 + nodes) 每 SD，画成中位数分组。

### 1.2 Clinical Factors — Univariate Cox ✅ · {{sForest}}
- **Message**: More positive lymph nodes are most strongly associated with shorter recurrence-free survival (HR 1.65 [1.48–1.84] per SD, q < 0.001; n = 686, 299 events).
- **Figure**: `figures/results_forest.png`（`plotting/results.py` 的 `fig_forest`，注册名 `results_forest`，12.1 × 4.6 in）：
  8 个因素一行一个，对数横轴，参考线在 1；右边数字列是三线表；q < 0.05 的行用强调色，其余灰色。
- **数字**（run_meta `results_forest.json` 的 `stats.rows`，8 个单变量 Cox，BH 校正 q 在这 8 个里算）：
  阳性淋巴结 log(1 + nodes) 每 SD HR 1.650 [1.479–1.841]，p 3.5e-19，q 2.8e-18；PR 每 SD 0.661 [0.590–0.739]；
  肿瘤大小每 SD 1.236 [1.121–1.364]；8 个里 6 个 q < 0.05。连续变量一律每 SD，二分类一律 yes vs no。
- **Source**: GBSG2 trial (lifelines load_gbsg2); univariate Cox, recurrence-free survival
- **可能被过度解读（只在讲稿，不上屏）**：「最强」指单变量模型里每 SD 的 |log HR| 最大，8 个因素没有相互调整。
- **Speaker notes**（`notes/sForest.md`）。

## 总结

### 2.1 Summary ✏️ · {{sSummary}}
- **Message**（三条，每条一句结论加一行证据）:
  1. Tamoxifen is associated with longer recurrence-free survival — HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events (univariate Cox)
  2. Positive lymph nodes carry the strongest univariate association — HR 1.65 [1.48–1.84] per SD, q < 0.001; largest effect of eight clinical factors
  3. The tamoxifen group differs at baseline — Older (median 58 vs 50 years) and more often postmenopausal (76% vs 48%); see Supplementary
- **数字**：第 1、2 条照抄 {{sKm}}、{{sForest}} 的块，第 3 条照抄 {{sSuppTable}}；这里不出现新数字。
- **Speaker notes**（`notes/sSummary.md`）：每条说一句它来自哪一页；第 3 条是限制：单变量的 tamoxifen HR 可能被年龄和绝经状态混杂。

## Supplementary

### S.1 Supplementary — Cohort Characteristics ✏️ · {{sSuppTable}}
- **Message**: Women given tamoxifen were older (median 58 vs 50 years) and more often postmenopausal (76% vs 48%); tumor size, grade and nodes were similar (n = 686).
- **上屏**：原生三线表，7 行 × 4 列（特征；All n = 686、Tamoxifen n = 246、No tamoxifen n = 440），16 pt，第一列左对齐、其余居中；
  这一节在 pptx 里隐藏，PDF 里照常导出。
- **数字**（run_meta `results_km.json` 的 `stats.cohort.all` / `tamoxifen` / `no_tamoxifen`）：年龄中位数 53 / 58 / 50 岁；
  绝经后 396 (58%) / 187 (76%) / 209 (48%)；Grade III 161 (23%) / 50 (20%) / 111 (25%)；复发或死亡 299 (44%) / 94 (38%) / 205 (47%)。
  肿瘤大小 25 (20–35) mm 和阳性淋巴结 3 (1–7) 三列相同：已确认（2026-10-01，用 `common.cohort` 从 `load_gbsg2` 按组重算）。
- **Source**: GBSG2 trial (lifelines load_gbsg2), descriptive statistics; 文献 `schumacher1994`（`deck.config.js` 的 `refs`）
- **可能被过度解读（只在讲稿，不上屏）**：「similar」只是描述，没有做组间检验。
- **Speaker notes**（`notes/sSuppTable.md`）。

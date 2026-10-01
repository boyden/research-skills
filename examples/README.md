# examples

`shared/` 和各 skill 文档里引用的示例：图、示例 deck、图标。数据和图标都是公开、可再分发的。

| 目录 | 内容 |
|---|---|
| `figures/` | 示例图（PNG）和每张图一份的 `run_meta/<图名>.json`，由 [make_example_figures.py](make_example_figures.py) 生成 |
| [slides/](slides/) | 经典页型的示例 deck：结果类（`results_examples`）和叙事类（`narrative_examples`），附 pptx、PDF 和逐页预览 |
| [icons/](icons/README.md) | 开放许可图标（AI / LLM / VLM / Agent、计算病理、空间组学、通用科研），带 SVG、512 px PNG、总览图 `icon_sheet.png` |

## 示例图

每张图都按它在 16:9 slide 上的实际尺寸画。结果图按整宽（12.1 × 4.6 in）或半宽（5.9 × 4.6 in）画；`slide_anatomy`（8.0 × 4.5）和 `three_line_table_example`（8.0 × 3.2）是示意用的小图：

```bash
cd research-skills
python examples/make_example_figures.py                    # 全部；需要 matplotlib、numpy、pandas、lifelines、scikit-learn
python examples/make_example_figures.py --only km_example  # 只画几张
```

| 注册名 | 内容 |
|---|---|
| `slide_anatomy` | 结果页的版面分区（标题、图框、结论句、来源行） |
| `km_example` | 两个正方形 KM 面板：删失标记、at-risk 表、HR / Cox p / C-index / log-rank p |
| `roc_example` | 两个正方形 ROC 面板：AUC [95% bootstrap CI]、n、阳性数 |
| `auc_bars_example` | AUC 条形图，从 0.5（随机）起画 |
| `forest_example` | 单变量 Cox 森林图，右侧三线表数字栏 |
| `three_line_table_example` | 画进图里的三线表（队列基线特征） |

- 数据：GBSG2 乳腺癌试验，686 例淋巴结阳性患者，终点是无复发生存，随 lifelines 一起发布（`lifelines.datasets.load_gbsg2`）。
  - 数据来自 R 包 TH.data（GPL-2），由 lifelines（MIT）转发。本仓库不带数据文件：脚本运行时从 lifelines 读，只提交由它画出的图。
  - 原始研究：Schumacher M, et al. *J Clin Oncol* 12.10 (1994): 2086–2093。
  - 数据集的常用引用：Sauerbrei W, Royston P. *J R Stat Soc A* 162.1 (1999): 71–94。
- bootstrap 用 2000 次重抽样、`random_state = 0`，记在各图的 run_meta 里。
- 这里的数字只用来演示画法，不代表任何临床结论。

## 图标

完整索引（每个图标的来源、许可、作者、原始 URL）见 [icons/README.md](icons/README.md)，逐个列表在 `icons/manifest.csv`。
需要署名的 CC BY 图标在索引里单独列出；用到时，在那一页的来源行或 deck 的 credits 页写上署名。
其他开放许可的图标库和各自的署名要求，见 [shared/figures.md](../shared/figures.md)「图标与外部图片」。

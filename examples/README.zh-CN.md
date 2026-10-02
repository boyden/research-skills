[English](README.md) | **简体中文**

# examples

`shared/` 和各 skill 文档里引用的示例：图、示例 deck、图标。数据和图标都是公开、可再分发的。

| 目录 | 内容 |
|---|---|
| `figures/` | 示例图（PNG）和每张图一份的 `run_meta/<图名>.json`，由 [plotting/](plotting/__init__.py) 包经 engine 的 [plot.py](../skills/results-deck/engine/tools/plot.py) 画出 |
| [slides/](slides/README.zh-CN.md) | 经典页型的示例 deck：结果类（`results_examples`）和叙事类（`narrative_examples`），附 pptx、PDF 和逐页预览 |
| [icons/](icons/README.zh-CN.md) | 开放许可图标（AI / LLM / VLM / Agent、计算病理、空间组学、通用科研），带 SVG、512 px PNG、总览图 `icon_sheet.png` |

## 示例图

每张图都按它在 16:9 slide 上的实际尺寸画。结果图按整宽（12.1 × 4.6 in）或半宽（5.9 × 4.6 in）画；`layout_*`（8.0 × 4.5，即 slide 的 0.6 倍）和 `three_line_table_example`（8.0 × 3.2）是示意用的小图：

```bash
cd research-skills
python skills/results-deck/engine/tools/plot.py examples                    # 全部；需要 matplotlib、numpy、pandas、lifelines、scikit-learn
python skills/results-deck/engine/tools/plot.py examples --only km_example  # 只画几张
python skills/results-deck/engine/tools/plot.py examples --list             # 注册名和所在模块
```

`examples/` 没有 `deck.config.js`，所以用 neutral 主题，图写到 `figures/`。包按 engine 的结构组织（[SPEC.zh-CN.md](../skills/results-deck/engine/SPEC.zh-CN.md) §6）：`style.py`（尺寸、颜色、字体取自主题）、`common.py`（数据读取和统计）、每组图一个模块：`layouts.py`（`layout_*`）、`survival.py`（`km_example`、`forest_example`）、`discrimination.py`（`roc_example`、`auc_bars_example`）、`tables.py`（`three_line_table_example`）。

| 注册名 | 内容 |
|---|---|
| `layout_figure_conclusion` | 最常用的「图 + 结论」页的版面分区（标题、图框、结论句、来源行），框里写明图按上屏尺寸画、1:1 放置 |
| `layout_*` | 其余 16 种页型的版面分区，按比例画，坐标同 neutral 主题（[theme.json](../skills/results-deck/engine/themes/neutral/theme.json)）和两份示例 deck 的页文件；嵌在 [slide-types.md](../skills/results-deck/reference/slide-types.zh-CN.md) 各页型下 |
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

完整索引（每个图标的来源、许可、作者、原始 URL）见 [icons/README.md](icons/README.zh-CN.md)，逐个列表在 `icons/manifest.csv`。
需要署名的 CC BY 图标在索引里单独列出；用到时，在那一页的来源行或 deck 的 credits 页写上署名。
其他开放许可的图标库和各自的署名要求，见 [shared/figures.md](../shared/figures.zh-CN.md)「图标与外部图片」。

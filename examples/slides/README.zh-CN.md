[English](README.md) | **简体中文**

# 经典页型示例

两份示例 deck，每页演示一种经典页型。页面右上角的灰色小字写着页型名，speaker notes 里写什么时候用、演示了哪些规则。
规则本身见 [shared/](../../shared/) 和 [skills/results-deck/reference/slide-types.md](../../skills/results-deck/reference/slide-types.zh-CN.md)。

- **结果类**（[results/](results/)，`results_examples`）：数字全部来自公开的 GBSG2 数据。其中一部分取自 [../figures/run_meta/](../figures/run_meta/)，其余由 [results/results_stats.py](results/results_stats.py) 算出，写在 `results/results_stats.json` 里。
- **叙事类**（[narrative/](narrative/)，`narrative_examples`）：用一个虚构的「AI 做计算病理和空间组学」研究演示结构页。结果都用 `XX` 占位，不编数字。

两份都是 v2 engine deck（一页一个文件；接口约定见 [skills/results-deck/engine/SPEC.md](../../skills/results-deck/engine/SPEC.zh-CN.md)）：

```
<deck>/
  deck.config.js        名称、节（含一个隐藏的 supplementary 节）、主题、figDir、文献
  slides/<key>.js       一页一个文件：{section, order, build(pres, n, P)}
  slides/_lib/*.js      本 deck 共用的常量和版式（来源行、缩写表 …）
  notes/<key>.md        这一页的讲稿，一行一个段落
```

两份 deck 直接用 engine 的 neutral 主题（`theme: "../../../skills/results-deck/engine/themes/neutral"`），不另存主题副本；图取自 `../../figures`（examples/figures），图标取自 examples/icons（`iconDir: null`）。

## 构建

```bash
cd research-skills
NODE_PATH=<含 pptxgenjs 的 node_modules> bash examples/slides/render.sh            # 两份都出
NODE_PATH=<…> bash examples/slides/render.sh results                                 # 只出一份
```

`render.sh` 对每份 deck 跑一次 engine 构建，再把逐页 PNG 挪进 `preview/`：

```bash
node skills/results-deck/engine/js/build.js examples/slides/results \
  --out examples/slides/output/results_examples.pptx --png
```

1. `build.js` 写出 `output/<deck>_examples.pptx`（supplementary 页隐藏）、`output/<deck>_examples.pages.json` 和 `output/<deck>_examples.pdf`（LibreOffice 转出，隐藏页照出）；
2. `--png` 按 60 dpi 逐页渲染 PNG，`render.sh` 把它们改名为 `preview/<deck>-NN.png`。

需要 node + pptxgenjs、LibreOffice、pdftoppm。示例图有变化时，先在仓库根目录用 `python skills/results-deck/engine/tools/plot.py examples --only <图名 …>` 重画。
列出一份 deck 的页：`node skills/results-deck/engine/js/build.js examples/slides/results --list`，或者构建之后跑
`python3 skills/results-deck/engine/tools/pages.py examples/slides/results --keys --pages examples/slides/output/results_examples.pages.json`
（这两份 deck 用 `--out` 构建，不出 `_wip` 工作副本，所以要给 `--pages`）。

| 文件 | 作用 |
|---|---|
| [results/deck.config.js](results/deck.config.js)、[narrative/deck.config.js](narrative/deck.config.js) | deck 元数据、节的顺序、主题和图目录 |
| `results/slides/`、`narrative/slides/` | 一页一个页文件（key 见下面两张表） |
| [results/slides/_lib/results.js](results/slides/_lib/results.js) | 来源行、缩写表，以及两页共用的渐进强调版式 |
| [narrative/slides/_lib/narrative.js](narrative/slides/_lib/narrative.js) | 议程页和节标题页共用的节名 |
| `results/notes/`、`narrative/notes/` | 讲稿，一页一个 `<key>.md` |
| [results/results_stats.py](results/results_stats.py) | 结果类 deck 里不在 run_meta 中的数字（基线表、模型 C-index、多变量 Cox） |
| [render.sh](render.sh) | 用 engine 构建两份 deck（pptx、PDF）并出预览 |

## 结果类页型

| 页 | key | 页型 | 什么时候用 | 预览 |
|---|---|---|---|---|
| 1 | `sKmSurvival` | Assertion–evidence | 一页一个发现：主题标题、一张整宽图、底部一句结论 | [results-01](preview/results-01.png) |
| 2 | `sRocTwoPanels` | 两个面板、一句结论 | 同一个问题的两个角度（这里是两个 ROC） | [results-02](preview/results-02.png) |
| 3 | `sForestPlot` | 森林图 | 多个变量的效应量一起比较 | [results-03](preview/results-03.png) |
| 4 | `sCohortTable` | 原生三线表 | 队列基线特征这类要能在 PowerPoint 里编辑的表 | [results-04](preview/results-04.png) |
| 5 | `sKeyNumbers` | 关键数字 | 开场或小结时用 2–3 个大数字定住规模 | [results-05](preview/results-05.png) |
| 6 | `sAucTakeaways` | 图 + 要点 | 半宽图加 3 条要点，适合图本身要解释的情况 | [results-06](preview/results-06.png) |
| 7 | `sKmCallout` | 标注（callout） | 教观众怎么读一张图：高亮框加一条细线连到说明 | [results-07](preview/results-07.png) |
| 8–9 | `sForestEmphasis1`、`sForestEmphasis2` | 渐进强调 | 同一张图连放两页，第二页高亮要看的行，不用动画 | [results-08](preview/results-08.png)、[results-09](preview/results-09.png) |
| 10 | `sFeatureDefinitions` | 特征定义表 | 先讲清每个特征是什么、值大值小代表什么、HR > 1 的意思 | [results-10](preview/results-10.png) |
| 11 | `sModelComparison` | 模型比较 | C-index 表；写明是 apparent 还是 CV | [results-11](preview/results-11.png) |
| 12 | `sDraftAdjustedHr` | DRAFT 页 | 数字还没确认的页：右上角标签，notes 里写待确认什么 | [results-12](preview/results-12.png) |
| 13 | `sSuppMultivariable` | Supplementary 页（隐藏） | 放映时跳过，答问时调出来 | [results-13](preview/results-13.png) |

节：`results`（第 1–12 页）、`supplementary`（第 13 页）。

## 叙事类页型

| 页 | key | 页型 | 什么时候用 | 预览 |
|---|---|---|---|---|
| 1 | `sTitle` | 标题页 | 题目、副标题、讲者和单位（占位） | [narrative-01](preview/narrative-01.png) |
| 2 | `sAgenda` | 议程 | 开头列出各节，当前一节用强调色 | [narrative-02](preview/narrative-02.png) |
| 3 | `sSectionDivider` | 节标题页 | 长 deck 的分节 | [narrative-03](preview/narrative-03.png) |
| 4 | `sBigStatement` | 大字陈述 | 背景页：一句主张，加 2–3 条支撑和文献 | [narrative-04](preview/narrative-04.png) |
| 5 | `sProblemApproachImpact` | 问题 → 方法 → 影响 | 三栏讲清为什么做、怎么做、有什么用 | [narrative-05](preview/narrative-05.png) |
| 6 | `sDataModalities` | 数据模态网格 | 并列介绍几类数据，每类一个图标、一行说明、n | [narrative-06](preview/narrative-06.png) |
| 7 | `sMethodsFlow` | 方法流程 | 编号步骤卡片加箭头，下面是定义，最后一句结论 | [narrative-07](preview/narrative-07.png) |
| 8 | `sFramework` | 框架图 | 输入 → 处理带 → 输出；带内细灰箭头，带外粗强调色箭头 | [narrative-08](preview/narrative-08.png) |
| 9 | `sAgentLoop` | Agent 循环 | 计划 → 调工具 → 观察 → 产出的闭环，旁边列可调用的工具 | [narrative-09](preview/narrative-09.png) |
| 10 | `sTimeline` | 时间线 | 研究设计或治疗线，标签上下交替 | [narrative-10](preview/narrative-10.png) |
| 11 | `sComparison` | 两栏对比 | 已有方法 vs 本工作，用形状画的 ✓ / ✗ / – 标记 | [narrative-11](preview/narrative-11.png) |
| 12 | `sLimitations` | 局限 | 3–4 条，每条写影响到哪个结论 | [narrative-12](preview/narrative-12.png) |
| 13 | `sSummary` | 要点总结 | 3 条编号要点 | [narrative-13](preview/narrative-13.png) |
| 14 | `sNextSteps` | 下一步 | 3 张带时间段的卡片 | [narrative-14](preview/narrative-14.png) |
| 15 | `sThankYou` | 致谢 / 提问 | 结尾页，联系方式占位 | [narrative-15](preview/narrative-15.png) |
| 16 | `sSuppModelSettings` | Supplementary 页（隐藏） | 模型设置等细节 | [narrative-16](preview/narrative-16.png) |
| 17 | `sCredits` | Credits | 用到的图标库、许可和数据来源 | [narrative-17](preview/narrative-17.png) |

节：`opening`（1–3）、`background`（4–5）、`methods`（6–10）、`discussion`（11–12）、`closing`（13–15）、`supplementary`（16）、`credits`（17）。

## 注意

- 叙事类第 6 页用了 CC BY 图标，署名写在该页的来源行和第 17 页上。用到 CC BY 图标时都要这样做。
- 页脚页码就是这一页在整套 deck 里的序号（engine 的规则），所以两份 deck 的预览文件编号都和页脚页码一致。叙事类的标题页和结尾页不显示页码。
- 版式元素都在 [skills/results-deck/engine/js/primitives.js](../../skills/results-deck/engine/js/primitives.js)（`abbr`、`arrow` / `thinArrow` / `thickArrow`、`cite`、`mark` 等），engine 把它作为 `P` 传给每一页。
  页文件的颜色取自 `P.C`、几何取自 `P.G`，不写十六进制颜色和字体名（`build.js` 会对这些打 WARNING）。
- 标注页和渐进强调页的高亮框位置是按当前 PNG 手量的。重画示例图后，如果版面变了，要重新量。

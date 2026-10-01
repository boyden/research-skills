# 经典页型示例

两份示例 deck，每页演示一种经典页型。页面右上角的灰色小字写着页型名，speaker notes 里写什么时候用、演示了哪些规则。
规则本身见 [shared/](../../shared/) 和 [skills/results-deck/reference/slide-types.md](../../skills/results-deck/reference/slide-types.md)。

- **结果类**（`results_examples`）：数字全部来自公开的 GBSG2 数据。其中一部分取自 [../figures/run_meta/](../figures/run_meta/)，其余由 [results_stats.py](results_stats.py) 算出，写在 `results_stats.json` 里。
- **叙事类**（`narrative_examples`）：用一个虚构的「AI 做计算病理和空间组学」研究演示结构页。结果都用 `XX` 占位，不编数字。

## 构建

```bash
cd research-skills
NODE_PATH=<含 pptxgenjs 的 node_modules> bash examples/slides/render.sh            # 两份都出
NODE_PATH=<…> bash examples/slides/render.sh results                                 # 只出一份
```

`render.sh` 依次做三件事：
1. 跑 `build_<deck>.js`，写出 `output/<deck>_examples.pptx`；
2. 用 LibreOffice 转出 PDF（supplementary 页在 pptx 里隐藏，在 PDF 里照出）；
3. 渲染逐页预览 `preview/<deck>-NN.png`。

需要 node + pptxgenjs、LibreOffice、pdftoppm。示例图有变化时，先跑 `python examples/make_example_figures.py`。

| 文件 | 作用 |
|---|---|
| [common.js](common.js) | 主题（灰色加一个占位强调色）、版面几何、版式元素：`newSlide`、`figure`（原尺寸放置）、`table`（三线表）、`conclusion`、`source`、`icon`、`draft`、`pattern` 等 |
| [build_results.js](build_results.js) | 结果类 deck |
| [build_narrative.js](build_narrative.js) | 叙事类 deck |
| [results_stats.py](results_stats.py) | 结果类 deck 里不在 run_meta 中的数字（基线表、模型 C-index、多变量 Cox） |
| [render.sh](render.sh) | 构建、转 PDF、出预览 |

## 结果类页型

| 页 | 页型 | 什么时候用 | 预览 |
|---|---|---|---|
| 1 | Assertion–evidence | 一页一个发现：主题标题、一张整宽图、底部一句结论 | [results-01](preview/results-01.png) |
| 2 | 两个面板、一句结论 | 同一个问题的两个角度（这里是两个 ROC） | [results-02](preview/results-02.png) |
| 3 | 森林图 | 多个变量的效应量一起比较 | [results-03](preview/results-03.png) |
| 4 | 原生三线表 | 队列基线特征这类要能在 PowerPoint 里编辑的表 | [results-04](preview/results-04.png) |
| 5 | 关键数字 | 开场或小结时用 2–3 个大数字定住规模 | [results-05](preview/results-05.png) |
| 6 | 图 + 要点 | 半宽图加 3 条要点，适合图本身要解释的情况 | [results-06](preview/results-06.png) |
| 7 | 标注（callout） | 教观众怎么读一张图：高亮框加一条细线连到说明 | [results-07](preview/results-07.png) |
| 8–9 | 渐进强调 | 同一张图连放两页，第二页高亮要看的行，不用动画 | [results-08](preview/results-08.png)、[results-09](preview/results-09.png) |
| 10 | 特征定义表 | 先讲清每个特征是什么、值大值小代表什么、HR > 1 的意思 | [results-10](preview/results-10.png) |
| 11 | 模型比较 | C-index 表；写明是 apparent 还是 CV | [results-11](preview/results-11.png) |
| 12 | DRAFT 页 | 数字还没确认的页：右上角标签，notes 里写待确认什么 | [results-12](preview/results-12.png) |
| 13 | Supplementary 页（隐藏） | 放映时跳过，答问时调出来 | [results-13](preview/results-13.png) |

## 叙事类页型

| 页 | 页型 | 什么时候用 | 预览 |
|---|---|---|---|
| 1 | 标题页 | 题目、副标题、讲者和单位（占位） | [narrative-01](preview/narrative-01.png) |
| 2 | 议程 | 开头列出各节，当前一节用强调色 | [narrative-02](preview/narrative-02.png) |
| 3 | 节标题页 | 长 deck 的分节 | [narrative-03](preview/narrative-03.png) |
| 4 | 大字陈述 | 背景页：一句主张，加 2–3 条支撑和文献 | [narrative-04](preview/narrative-04.png) |
| 5 | 问题 → 方法 → 影响 | 三栏讲清为什么做、怎么做、有什么用 | [narrative-05](preview/narrative-05.png) |
| 6 | 数据模态网格 | 并列介绍几类数据，每类一个图标、一行说明、n | [narrative-06](preview/narrative-06.png) |
| 7 | 方法流程 | 编号步骤卡片加箭头，下面是定义，最后一句结论 | [narrative-07](preview/narrative-07.png) |
| 8 | 框架图 | 输入 → 处理带 → 输出；带内细灰箭头，带外粗强调色箭头 | [narrative-08](preview/narrative-08.png) |
| 9 | Agent 循环 | 计划 → 调工具 → 观察 → 产出的闭环，旁边列可调用的工具 | [narrative-09](preview/narrative-09.png) |
| 10 | 时间线 | 研究设计或治疗线，标签上下交替 | [narrative-10](preview/narrative-10.png) |
| 11 | 两栏对比 | 已有方法 vs 本工作，用形状画的 ✓ / ✗ / – 标记 | [narrative-11](preview/narrative-11.png) |
| 12 | 局限 | 3–4 条，每条写影响到哪个结论 | [narrative-12](preview/narrative-12.png) |
| 13 | 要点总结 | 3 条编号要点 | [narrative-13](preview/narrative-13.png) |
| 14 | 下一步 | 3 张带时间段的卡片 | [narrative-14](preview/narrative-14.png) |
| 15 | 致谢 / 提问 | 结尾页，联系方式占位 | [narrative-15](preview/narrative-15.png) |
| 16 | Supplementary 页（隐藏） | 模型设置等细节 | [narrative-16](preview/narrative-16.png) |
| 17 | Credits | 用到的图标库、许可和数据来源 | [narrative-17](preview/narrative-17.png) |

## 注意

- 叙事类第 6 页用了 CC BY 图标，署名写在该页的来源行和第 17 页上。用到 CC BY 图标时都要这样做。
- 叙事类的页脚页码从第 2 页开始算（标题页不编号），所以预览文件的编号比页脚页码大 1；结果类没有标题页，两者一致。
- `build_results.js` 和 `build_narrative.js` 里各有一份本地的 `abbr()`；叙事类还有 `arrow()`、`cite()`、`mark()` 等小工具。等第二期 engine 再统一并入 `common.js`。
- 标注页和渐进强调页的高亮框位置是按当前 PNG 手量的。重画示例图后，如果版面变了，要重新量。

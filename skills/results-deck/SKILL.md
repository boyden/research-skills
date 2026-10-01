---
name: results-deck
description: 从分析结果做或修改汇报 deck / slides / pptx（结果汇报、组会、答辩、进展汇报）。用户说「做 deck」「出 slides」「把结果做成 pptx」「改某几页」「加一页 KM / 森林图 / 方法页」「同步讲稿」「发布新版本」时使用。产出是 16:9 pptx + PDF：每页一个主题标题、一句结论、按上屏尺寸画好的图、来源行，数字全部可溯源。
---

# results-deck：从分析结果出汇报 deck

## 什么时候用

- 要把已有分析结果（结果表、图）做成对外汇报的 deck，或改已有 deck 的某几页。
- 要加页、挪页、改页标题、同步讲者改过的讲稿、发布一个新版本。
- 不用于：从头做分析（先把结果表做出来）、论文排版、纯文字报告。

## 前置条件

开始前先查这些在不在；缺了就写出用户该跑的安装命令，问过再装，不自己装：

- node 和 pptxgenjs（`NODE_PATH` 或本地 `node_modules`）；
- LibreOffice（`soffice`）和 pdftoppm（poppler），用来转 PDF、出预览 PNG；
- Python 和 matplotlib、pandas；画生存或 ROC 图时还要 lifelines、scikit-learn；
- 模板用的字体已装进系统（`fc-list | grep <字体名>`，见 [reference/checks.md](reference/checks.md) §4）；
- 可选：Anthropic pptx skill 自带的 `validate.py`，做结构检查。

## 先读共同规则

动手前读完这四份，本 skill 不重复它们，只在冲突时以它们为准：

- [../../shared/numbers-and-sources.md](../../shared/numbers-and-sources.md)：每个数字指到来源、找不到就停下来问、p / HR / 区间格式、candidate 与 significant 的措辞。
- [../../shared/figures.md](../../shared/figures.md)：按最终尺寸画图、英文、方形面板、KM 配色和四个量、框架图箭头、图标许可、`FIGURES` 注册与 `--only`。
- [../../shared/tables.md](../../shared/tables.md)：三线表，含 pptxgenjs 的逐格边框写法。
- [../../shared/writing-style.md](../../shared/writing-style.md)：标题写主题、结论句写发现、用户定的说法照原样、缩写格式、人名、wip 与版本号。

本目录的参考文档：

- [reference/outline-format.md](reference/outline-format.md)：大纲目录和逐页块的格式，`{{key}}` 页引用。
- [reference/slide-types.md](reference/slide-types.md)：页面几何（坐标、字号）和页型目录。
- [reference/checks.md](reference/checks.md)：验证流程和踩过的坑。

## 项目里的目录约定

deck 放在项目里的一个目录下（如 `presentation/`），结构如下。名字可以按项目改，分工不变。

```
presentation/
  outline/              大纲：内容的唯一来源（格式见 reference/outline-format.md）
    README.md           索引、生成的页码对照表、各节页数
    01_<chapter>.md …   一章一个文件
    CHANGELOG.md        挪页、改名、删页的历史
  plotting/             画图代码包：只读结果表，不做分析
    main.py             入口：--only <图名> …，--out-dir；自动发现各模块的 FIGURES
    <section>.py        一节一个模块，导出 FIGURES = {"km_example": fig_km, ...}（可选：模块的输入表清单 INPUTS，写进 run_meta）
  figures/              上屏尺寸的 PNG
    run_meta/<图名>.json  每张图一份：输入、统计量、脚本、时间
  js/                   构建脚本（pptxgenjs）
    style.js            颜色、字体、文献登记表 REF、图片登记表
    primitives.js       版式元素和页型模板
    slides_<block>.js   一段连续的页一个文件，每页一个 builder 函数
    build_deck.js       只定页序：SLIDES = [[section, [builders…]], …]，再写 pptx
    notes.json          讲稿：{builder key: 全文}
  output/
    <deck>_wip.pptx / .pdf / .pages.json      工作版，每次覆盖
    <deck>_v<N>.pptx / .pdf / .pages.json     发布版，只增不改
  tools/                页引用、版面、讲稿检查（见 reference/checks.md）
```

- **一页一个 builder 函数**，函数名就是这一页的 key：大纲、讲稿、检查工具都用它指页，不用页号。
- **`SLIDES` 按节分组**（`[["title", [...]], ["results", [...]], ["supplementary", [...]]]`）：页序只在这里定；
  节 key 用于只构建部分页（`--sections`）和列页数（`--list-sections`）。
- **每次构建写 `<输出名>.pages.json`**：`[{page, title, section, builder}, …]`，页号 ↔ 标题 ↔ key 的唯一真相。
- 图一张一个注册名，平时只用 `--only` 画改过的那几张；每张图写自己的 run_meta，并行画图不会互相覆盖。

## 工作流

1. **大纲**：先在 `outline/` 对应章节写或改这一页的块：主题标题、`Message`（上屏英文原句）、图、数字及来源、Source 行、状态。
   用户没确认的说法不进 Message。数字从结果表或 run_meta 取，旧版 deck 只提供结构。
2. **画图**：先定版位（整宽 12.1 × 4.6 in，两张并排各 5.9 × 4.6 in），按版位尺寸画，字号就是上屏字号。
   新图在对应模块里写 `fig_xxx()` 返回 `(fig, stats)`，注册进 `FIGURES`，`--only xxx` 画出并写 run_meta。
3. **构建**：在对应的 `slides_<block>.js` 里加 builder，把它放进 `SLIDES`；改动期间只构建自己那几节到临时路径。
4. **渲染并检查**：pptx → PDF → PNG，逐页看改过的页（清单见 [reference/checks.md](reference/checks.md)）。
5. **wip 与发布**：平时整套构建写 `_wip`（覆盖）；到节点或用户确认时 `--release` 写 `_v<N>`，N = 现有最大 + 1，旧版全部保留。
   pptx、PDF、pages.json 一起出。
6. **讲稿同步**：讲者在 PowerPoint 里改讲稿后，从他的 pptx 读回 `notes.json`（按页标题配 key），再构建；
   挪页后查讲稿里的相对引用（「next slide」）。
7. **刷新引用**：增删页、挪页、改标题后重新生成大纲里的页码表，检查 `{{key}}` 全部能解析。

## 每页的规则（摘要）

| 元素 | 规则 | 为什么 |
|---|---|---|
| 标题 | 写主题，如 `Hormone Therapy — Recurrence-free Survival`，28 pt；一节内同一前缀 | 结论放标题会和结论句重复，且标题要稳定作为引用目标 |
| 结论句 | 每页一句，就是大纲的 `Message`，18 pt 黑色粗体；太长拆成 bullet，不缩字号 | 听众只记一句话；字号统一，页与页之间不跳 |
| Source 行 | 右下角 9 pt 衬线：结果表 / 数据集 + 方法 | 每个数字都能指回去 |
| DRAFT 标签 | 大纲标 ⚠️ 的页照样出，右上角灰色 `DRAFT – to be confirmed`，待确认的说明抄进讲稿 | 页面先占位，不让未确认的数字被当成定论 |
| 图 | 1:1 放置，不缩放、不裁剪、不拉伸；主图放到 z 序最底 | 字号各页一致；标题折行时不被图盖住 |
| 原生表格 | 一律走一个 `table()` helper（三线表），不直接 `addTable` | 表格样式只在一处定义 |
| 文献 | 上屏引用从一个登记表（`REF`）取，先登记再用；格式 `Surname, Given, et al. Journal vol.issue (year): pages` | 作者、卷期只核对一次 |
| 缩写 | 每页一行 `ABBR: expansion; ABBR: expansion.` | 见 writing-style.md |
| 讲稿 | 为版面从页上挪走的细节写成 `Note: …`；「可能被过度解读」写在讲稿，不上屏 | 讲者能核对哪些话页上没有 |

## 什么时候停下来问

- 上屏的数字在结果表、run_meta 或大纲写明的来源里**找不到或对不上**：停下来问，不自己挑一个。
- **图是错的**（数字、标签、配色、尺寸不对）：回 `plotting/` 改画图代码，`--only` 重画；不在 deck 里遮、裁、拉伸或叠文字修补。
- 用户的说法和来源矛盾（如时间范围写错）：照来源，直接告诉用户差在哪里。
- 改动要碰共享文件（`primitives.js`、`style.js`、`build_deck.js`）的已有函数签名或行为：先说明，等确认。
  新的版式元素先放在自己的 `slides_<block>.js` 里。

## 不做

- 不上传（Google Drive、云盘等）；用户自己拖进去。
- 不 commit，除非用户要求。
- 不安装、升级包（包括 npm、字体）；缺什么就写出用户该跑的命令，然后停下。
- 不改分析结果文件；不改已发布的 `_v<N>` 文件。
- 不重写已有的页来加新页；在对应的 builder 文件里追加。

## 构建引擎（规划中）

可复用的引擎（pptxgenjs 版式元素、`build_deck.js`、页引用 / 版面 / 讲稿检查工具）计划放在
`skills/results-deck/engine/`（第二阶段）。在那之前，把 [examples/slides/](../../examples/slides/)
（`common.js` + `build_results.js` / `build_narrative.js` + `render.sh`）拷进项目当起步骨架，按
[reference/slide-types.md](reference/slide-types.md) 的几何和页型改成项目的 `primitives.js` 和 builder，
检查按 [reference/checks.md](reference/checks.md) 手动或用项目自带脚本做。

这套骨架还没有、要等 engine 或在项目里自己补的：

- `SLIDES` 分节和 `--sections` / `--list-sections`；
- `--release` 发布 `_v<N>`；
- 写 `pages.json`；
- `{{key}}` 页引用的解析和检查工具；
- `notes.json` 与讲者 pptx 的讲稿同步（示例 builder 里的讲稿直接写在 `addNotes()` 里）。

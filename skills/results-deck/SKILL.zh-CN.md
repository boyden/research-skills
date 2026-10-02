[English](SKILL.md) | **简体中文**

# results-deck：从分析结果制作汇报 deck

从已有分析结果制作可追溯的 16:9 汇报 deck。通常产出 `.pptx`；依赖的本地工具齐全时，engine 还会尝试生成对应的 PDF 和预览 PNG。

## 什么时候使用

用户要做以下事情时使用本 skill：

- 把结果表或已有图做成汇报 deck；
- 增加、删除、移动或修改页面；
- 增加 KM、ROC、forest、方法、框架图、表格或总结页；
- 同步讲者在 PowerPoint 中修改过的讲稿；
- 明确请求发布一个 deck 版本。

不用于执行底层统计分析、论文排版或纯文字报告。应先准备并核对结果表。

## 前置条件与安装边界

构建前先检查这些依赖是否存在：

- Node.js 和 `pptxgenjs`（通过 `NODE_PATH` 或本地 `node_modules`）；
- LibreOffice（`soffice`）和 Poppler（`pdftoppm`；做版面检查还需要 `pdftotext`）；
- Python、`matplotlib` 和 `pandas`；只有请求的图确实需要时才使用 `lifelines` 或 `scikit-learn`；
- 当前主题使用的字体；
- 可选的 PowerPoint 结构检查工具，例如 `validate.py`。

缺依赖时，告诉用户可以执行的安装命令，并先征得同意。不要自行安装或升级包、字体及其他系统资源。

## 先读共同规则

修改内容或图之前，先读下面四份共同规则。它们分别约束数据溯源、措辞、画图、表格和写作风格：

- [numbers-and-sources.md](../../shared/numbers-and-sources.zh-CN.md)：数字来源、效应量格式、区间，以及 candidate 与 significant 的措辞；
- [figures.md](../../shared/figures.zh-CN.md)：按最终尺寸画图、KM / ROC / forest 约定、示意图、图标、图注册和 `--only`；
- [tables.md](../../shared/tables.zh-CN.md)：三线表和原生 `pptxgenjs` 表格边框；
- [writing-style.md](../../shared/writing-style.zh-CN.md)：标题、结论句、缩写、人名、用户给定的措辞和版本命名。

可执行的 v2 接口以 [engine/SPEC.md](engine/SPEC.zh-CN.md) 为准。内容规划、页面类型和验证分别看 [reference/outline-format.md](reference/outline-format.zh-CN.md)、[reference/slide-types.md](reference/slide-types.zh-CN.md) 和 [reference/checks.md](reference/checks.zh-CN.md)。

## 语言和文档约定

- 所有生成的产出物都用英文：页标题和结论句、图中文字、表格、Source 行、speaker notes、PPTX、PDF 和预览图。
- 仓库文档采用双语维护。每份面向用户的 skill、engine、reference 和 template 文档都要有英文 `X.md` 和中文 `X.zh-CN.md`，两份第一行都放语言切换链接；有 YAML front matter 时放在 front matter 后的第一行。
- 代码标识符、文件名、图中文字和上屏文字保持英文。中文只放在对应的说明文档或明确的本地化工具输出里，不进入产出物。

## 项目目录结构

engine v2 按“一页一个文件”组织 deck。通常结构如下：

```text
presentation/<deck>/
  deck.config.js             元数据、主题、lang、文献和章节顺序
  theme/theme.json           颜色、字体、几何和素材
  slides/<key>.js            每页一个页面模块
  slides/_lib/               deck 自己的可复用版式辅助，不算页面
  notes/<key>.md             每页一个讲稿文件，可选
  notes/_aliases.json        从 PPTX 导入讲稿时使用的标题别名
  outline/                   内容、来源、状态和生成的页码表
  plotting/                  只读结果、不做分析的画图模块
  figures/                   按上屏尺寸画好的 PNG
    run_meta/<figure>.json   每张注册图的输入和统计量
  output/                    工作版和发布版产物
```

新 deck 从复制 [engine/template/](engine/template/README.zh-CN.md) 开始；`lang`（`"en"` 或 `"zh"`）决定 `pages.py` 在大纲里写的生成块用哪种语言。

项目大纲是内容和溯源的审查来源；页面模块是可执行的版式来源。engine 不会从 Markdown 自动推导页面内容，所以大纲和页面模块中的 `Message`、数字、图和 Source 行必须保持同步。

## 页面模块接口

`slides/` 中文件名不以 `_` 开头的每个文件，都必须导出如下对象：

```js
module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Topic title", n);
    P.figure(s, "figure_name.png");
    P.conclusion(s, "One evidence-backed conclusion sentence.");
    P.source(s, "Source: result table or dataset; method");
    return s;
  },
};
```

保持以下不变量：

- `deck.config.js.sections` 只放章节 key，并按 deck 顺序排列；
- `section` 必须是其中一个 key；同一章节内由 `order` 决定页序；
- 页面 key 是文件名去掉 `.js` 后的部分，必须稳定、唯一，并匹配 `^[A-Za-z][A-Za-z0-9_]*$`；
- 每个页面模块只能通过 `P.newSlide()` 创建一页；
- 共用版式放进 `slides/_lib/`，不要让辅助文件被当成页面；
- 颜色、字体、字号和几何从 `P.T`、`P.G` 读取，或使用已经封装好的 primitives；页面模块不要写死主题颜色、字体名或页面坐标；
- 结果图使用 `P.figure()`，以原生上屏尺寸放置，并置于标题之后的底层；只有缩略图等明确不是结果主图的素材才使用适配或缩放。

## 工作流

1. **检查输入和范围。** 找出结果表、来源图、已有 deck、目标听众和要改的章节。不要臆造缺失数字，也不要悄悄改变分析口径。
2. **更新大纲。** 记录主题标题、准确的上屏 `Message`、图名、每个上屏数字及其来源、Source 行、状态和讲稿中的注意事项。未确认的措辞或数字保留 draft 状态。
3. **准备图。** 只从结果表或其他明确命名的输入画图。注册每张图，返回上屏统计量，写入 `run_meta`，并使用 `engine/tools/plot.py <deck> --only <figure>`。按最终上屏尺寸绘制。
4. **构建改动页。** 局部构建使用 `node engine/js/build.js <deck> --only <key,...> --out <scratch>/x.pptx --png` 或 `--sections <section,...> --out <scratch>/x.pptx --png`，页脚写的是整套 deck 里的页码。整套构建（`node engine/js/build.js <deck>`，覆盖 `_wip` 产物）用于集成和发布检查，由集成者跑。
5. **渲染并检查。** 转成 PDF 和 PNG，或使用 engine 的 `--png` 选项。检查所有改动页是否有溢出、重叠、缺少页脚或 DRAFT 状态、图尺寸错误、非英文标签和数字不一致。`engine/tools/layout_check.py` 只能作为筛查工具，最终以渲染出的 PNG 为准。
6. **同步讲稿。** 讲者修改 PPTX 后，先用 dry-run 运行 `engine/tools/pull_notes.py`；对无法匹配或标题重复的页面，用 `notes/_aliases.json` 解决；再运行 `--write`，它只为讲稿有变化的匹配页面写 `notes/<key>.md`。页面移动后重新检查「下一页」等相对表述。
7. **挪页并刷新页引用。** 用 `engine/tools/move.py <deck> <key> --after <key>`（或 `--before <key>`、`--to <section>`）挪页，它只改这一页文件的 `section` 和 `order`。增删、移动或改名后，先整套构建，再运行 `engine/tools/pages.py <deck> --table --write` 和 `--check`。正文中用 `{{key}}`、`{{key.title}}` 和 `{{key.page}}`，不要手写页号。
8. **只在确认后发布。** 日常工作覆盖 `_wip` 产物；只有用户明确要求发布或确认里程碑时才使用 `--release`，绝不修改已有的 `_v<N>` 产物。

几个 agent 并行改同一份 deck 时，每个 agent 只写自己的页文件、讲稿和画图模块，用局部构建检查自己的页。整套构建、`--release`、`move.py --respace`、`pages.py --table --write`、`pull_notes.py --write` 和 commit 由集成者串行做，见 [reference/checks.md](reference/checks.zh-CN.md#8-wip发布和并行改页)。

## 每页规则

| 元素 | 规则 |
|---|---|
| 标题 | 写主题，不写结论；使用稳定标题，并保持同一章节的前缀一致。 |
| 结论 | 使用一句有证据支持的结论，通常就是大纲中的准确 `Message`；过长时拆成 bullet，不要缩小字号。 |
| Source 行 | 写明结果表、数据集和方法，让每个上屏数字都有可追溯来源。 |
| Draft 状态 | 内容未解决的页面仍可构建，但要带 `DRAFT – to be confirmed`，并把待解决事项写入讲稿。 |
| 图 | 按最终尺寸绘制；不要在 deck 里裁剪、拉伸或遮盖错误的图。应修改画图代码后重画。 |
| 表格 | 使用共同的三线 `table()` helper，不直接调用 `addTable()`。 |
| 文献 | 上屏引用统一登记一次，并使用共同的引用 helper。 |
| 缩写 | 页面出现缩写时，保持统一的缩写说明行。 |
| 讲稿 | 从页面移出的细节和可能的过度解读写入讲稿，必要时明确标记。 |

## 什么时候停下来问

出现以下情况时停下来问用户：

- 上屏数字在结果表、图的 metadata 或指定来源中找不到，或对不上；
- 用户措辞与来源冲突，或改变了 estimand、时间范围、比较对象或统计解释；
- 图的数字、标签、配色或预期尺寸有误；
- 请求会改变 `primitives.js`、`build.js` 等共享 engine 文件的签名或行为；
- 缺少依赖或输入，无法可靠构建。

不要在冲突数字中自行选择，不要用叠加对象修补错误图，也不要把未确认结果呈现为最终结论。

## 不做

- 不在 deck 排版任务中执行底层分析，也不修改分析结果文件；
- 未经用户同意，不安装或升级包、字体和系统工具；
- 不覆盖已发布的 `_v<N>` 产物；
- 用户未明确要求时，不上传 deck 到云盘，也不 commit；
- 不把页号当作稳定标识，使用页面 key 和生成的 `pages.json`。

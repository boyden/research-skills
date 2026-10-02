[English](SPEC.md) | **简体中文**

# engine 接口约定（v2）

engine 是可复用的部分：版式元素（JS）、构建脚本（JS）、主题、画图入口和页引用 / 讲稿 / 挪页 / 主题 / 版面检查工具（Python，只用标准库；
画图入口另需 matplotlib，主题图标和 SVG logo 的栅格化另需 headless Chrome），外加一个可以直接复制的 deck 骨架 `template/`。
各部分只通过下面这些文件格式、命令行和函数签名打交道。

设计目标有三个：

1. **多个 agent 并行**：新增、修改、挪动一页，画一张图，改一页讲稿，都只写这一页或这张图自己的文件，不碰共享文件（§9）。
2. **换模板就换风格**：颜色、字体、几何、logo 都在 `theme/` 里，从一份模板 pptx 生成；页文件和画图代码里不写死（§5）。
3. **大纲、画图、构建分开**：大纲按章分文件（§7），画图是一个包、按节分模块（§6），构建只认页文件（§3、§8）。

> **相对 v1 的变更**（2026-10-01；按 v1 已经写了一半的代码照此调整）
> - 页序不再写在 `deck.config.js` 的 `sections` 里：`sections` 只列节，**每页一个文件** `slides/<key>.js`，
>   页自己声明 `section` 和 `order`，构建时排序（§3）。挪页 = 改这一页自己的两个字段。
> - **key = 页文件名**（不含 `.js`），不再是 builder 函数名；`sXxx#2` 的规则作废（key 由文件系统保证唯一）。
> - builder 签名改为 `build(pres, n, P, ctx)`，`P` 是 primitives（由 build.js 传入，页文件不 `require` engine 路径）。
> - 讲稿从一个 `notes.json` 改为**一页一个** `notes/<key>.md`；别名表挪到 `notes/_aliases.json`，配不上的页记在
>   `notes/_unmatched.json`（§8.3）。
> - 新增主题 `theme/theme.json`（§5），`configure()` 多一个 `theme`；primitives 里不再有写死的颜色、字体、坐标。
> - 新增 `--only <key,…>`、`--png`；部分构建（`--only` / `--sections`）的页脚写**整套 deck 里的真实页码**，而且对选中范围以外的页
>   文件宽松（§8.1）。
> - 新增整套构建锁 `<outDir>/.build.lock`（§8.1）、画图入口 `tools/plot.py`（§6）、
>   `tools/move.py`（§3.1）、`tools/theme_from_pptx.py`（§5.2）、`tools/theme_icons.py` 和 `tools/svg_raster.py`（§5.4）、
>   `tools/layout_check.py`（§8.5）。
> - `pages.json` 每条多一个 `order` 字段；`builder` 字段保留，值就是 key（§8.2）。
> - `deck.config.js` 多一个 `lang`，决定 `pages.py` 写的生成块用英文还是中文（§8.4）。

## 1. 目录

```
engine/
  SPEC.md / SPEC.zh-CN.md    本文件（英文版 / 中文版）
  README.md                  怎么用（复制 template/、画图、构建、自查、换主题）
  js/primitives.js           版式元素：newSlide、figure、table、conclusion、source、cite、abbr、icon、arrow …（全部读主题）
  js/build.js                构建：收集页文件、排序、wip / release / 部分构建、pages.json、讲稿、隐藏 supplementary、PDF、PNG
  themes/neutral/            默认主题（theme.json），template/theme/ 是它的副本
  tools/README.md            每个工具的命令行、读写的文件和退出码
  tools/plot.py              画图入口：载入 deck 的 plotting/ 包，--only、--out-dir、--list，每张图一份 run_meta（§6）
  tools/pages.py             {{key}} 页引用：--check / --show / --keys / --table [--write]（§8.4）
  tools/pull_notes.py        从讲者改过的 pptx 把讲稿同步回 notes/<key>.md（§8.3）
  tools/move.py              挪页：只改这一页文件的 section / order；--respace 重排一节的 order（集成者用）（§3.1）
  tools/theme_from_pptx.py   从模板 pptx 生成主题目录（§5.2）
  tools/theme_icons.py       按主题颜色渲染 deck 用到的图标（§5.4）
  tools/svg_raster.py        用 headless Chrome 把 SVG 渲成透明 PNG（可改色）；theme_icons 和 theme_from_pptx 共用（§5.4）
  tools/layout_check.py      PDF + pptx 版面碰撞检查（标题被图遮住、文字压图、文字压文字）（§8.5）
  tools/tests/               工具的回归测试和测试用 deck
  template/                  新 deck 的骨架（复制整个目录开始）
```

## 2. deck 目录（template/ 的结构，也是每个新 deck 的结构）

```
<deck>/
  deck.config.js             元数据和节的顺序（§2.1）；只列节，不列页
  theme/                     theme.json + 素材（logo 等）；换风格 = 换这个目录（§5）
  theme/icons/png/           按主题颜色渲染的图标（tools/theme_icons.py 写，可以没有；§5.4）
  slides/<key>.js            一页一个文件（§3）
  slides/_lib/*.js           本 deck 自己的复用版式片段（集成者维护，只追加）；构建时不当页收集
  notes/<key>.md             一页一份讲稿，可以没有（§8.3）
  notes/_aliases.json        {pptx 页标题: key}，pull_notes 用，可以没有
  notes/_unmatched.json      pull_notes --write 写的配不上的 pptx 页（§8.3）
  outline/README.md          大纲索引，含生成块（§7、§8.4）
  outline/NN_<章>.md         一章一个文件
  outline/CHANGELOG.md       挪页、改名、合并、删页的历史
  outline/archive/           冻结的旧版，工具不碰
  plotting/                  画图包（§6）：style.py、common.py、<节>.py
  figures/<图名>.png         按上屏尺寸画好的图（dpi 见主题）
  figures/run_meta/<图名>.json
  pages_ignore.txt           pages.py 的忽略规则，一行一条 `file:regex`，可以没有（§8.4）
  .backups/<时间戳>/          pages.py --table --write 和 pull_notes --write 改文件之前的备份
  output/                    构建产物（位置由 outDir 决定，可以在 deck 目录外；§2.1）
```

以 `_` 开头的文件和目录（`slides/_lib/`、`notes/_aliases.json`、`notes/_unmatched.json`、`plotting/_*.py`）是共享的辅助文件，
工具不把它们当页、讲稿或图。

`template/.gitignore` 忽略 `output/*.pptx`、`output/*.pdf`、`output/*_png/`、`output/.*`（构建锁和中断构建的临时文件）、`.backups/` 和
`notes/_unmatched.json`；`output/*.pages.json` 和 `figures/` 进 git（`pages.py --check` 在新 checkout 上不用 node 也能跑，pages.json 的 diff
记下了挪页）。复制 `template/` 开新 deck 之后，删掉复制过来的 `output/*.pptx`、`output/*.pdf`、`output/*_png/`。

### 2.1 deck.config.js

```js
module.exports = {
  name: "my_deck",                 // 输出文件名前缀
  title: "My Deck",                // pptx 元数据标题
  outDir: "output",                // 以下路径都相对 deck 目录，可以指到 deck 目录外
  figDir: "figures",
  iconDir: null,                   // null = 用 research-skills/examples/icons
  theme: "theme",                  // 主题目录，可以是指向共享主题的相对路径；目录里没有 theme.json 时用 engine/themes/neutral（打一行 WARNING）
  lang: "en",                      // "en" | "zh"：pages.py 写的生成块（页数行、页码表表头、占位 Note）用哪种语言
  refs: {},                        // 文献注册表 {key: [author, journal, rest, isOrg?]}，cite() 用
  sections: ["title", "background", "methods", "results", "summary", "supplementary"],  // 节的顺序；key 唯一
  supplementary: "supplementary",  // 这一节的页在 pptx 里隐藏
};
```

- 所有路径都相对 deck 目录，可以指到 deck 外。示例 deck `examples/slides/results/` 写的是 `outDir: "../output"`（两份示例 deck 共用
  `examples/slides/output/`）、`figDir: "../../figures"`、`theme: "../../../skills/results-deck/engine/themes/neutral"`（直接用 engine 的默认主题，
  不复制一份）。
- build.js 用 node 载入 deck.config.js；Python 工具不运行 node，只用正则读其中的**字面字符串**字段（`name`、`outDir`、`figDir`、`theme`、
  `lang`、`iconDir`；move.py 另读 `sections` 列表）。这些字段要写成字面字符串，不要拼接，也不要引用变量。
- `theme` 不写时，build.js 和 theme_icons.py 用 `<deck>/theme`，plot.py 和 layout_check.py 直接用 `engine/themes/neutral`。所以 `theme` 总是显式写出。
- `name` 缺失或 `sections` 不是非空的节 key 列表（比如还是 v1 的 `[key, [builders]]`）时，构建报错退出（退出码 2）；v1 的 `notes` 字段被忽略并打 WARNING。

节的增删和换序很少发生，由集成者改。页属于哪一节、排第几，写在页文件里。

## 3. 页文件 `slides/<key>.js`

```js
"use strict";
module.exports = {
  section: "results",
  order: 20,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Recurrence-free Survival", n);
    P.figure(s, "survival_km_tamoxifen.png");
    P.conclusion(s, "Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89]; n = 686).");
    P.source(s, "Source: GBSG2 trial; univariate Cox");
    return s;
  },
};
```

- **key = 文件名**，须匹配 `^[A-Za-z][A-Za-z0-9_]*$`（如 `sKmTamoxifen`）。大纲、讲稿、图的注释、工具都用 key 指页。
- **`section`** 必须在 `deck.config.js` 的 `sections` 里。
- **`order`** 是数字，同一节内按它从小到大排。约定按 10、20、30 留空位，插页时取中间值（25）；
  空位用完时由集成者跑 `move.py --respace <节>`，把这一节重新排成 10 的倍数。这一步会一次改多个页文件，只能串行。
  同一节里两页 `order` 相同时，构建报错退出（退出码 2），并列出两个文件。
- **`build(pres, n, P, ctx)`**：`pres` 是 pptxgenjs 实例，`n` 是页脚页码（标题页可以忽略），
  `P` 是 primitives，`ctx = {key, section, config, theme, deckDir}`。页文件只 `require` 自己 deck 里的 `slides/_lib/*`，
  不 `require` engine 的路径，所以 engine 挪了位置，deck 不用改。`slides/_lib/*.js` 要用 primitives 时写
  `require("results-deck")`：build.js 把这个模块名映射到 engine 的 primitives.js，拿到的和 `P` 是同一个对象
  （`require("pptxgenjs")`、`require("jszip")` 同样映射到 build.js 找到的那份）。
- 每页必须经 `P.newSlide(pres, title, n, opts)` 建（标题页用 `{chrome: false}`），页标题才会进页表。一个文件只出一页：
  `build()` 建出的页不是恰好一页时，构建报错退出（退出码 2），什么都不写。
- **两页共用一种版式**时，把版式写成 `slides/_lib/` 里的函数，两个页文件各调一次。没有「一个 builder 出两页」。
- 页文件里**不写颜色和字体名**，一律从 `P.T`（主题色和字体）取；**共用的版面区域**（标题、logo、主图框、结论框、来源行、页码、页边距）
  由 primitives 按 `P.G` 画，页文件不另写它们的坐标。这样换主题时颜色、字体和这些区域都不用改页。
  只属于这一页的摆放（卡片、示意图里各元素的位置和字号）可以直接写数字，最好写成相对 `P.G`（如 `G.margin`、`G.contentW`）的偏移；
  换了尺寸不同的主题时，这些页要逐页看一遍。示例 deck 里画廊式的页就是这样写的。build.js 发现页文件里有 6 位十六进制颜色字面量或字体名时打 WARNING，不报错（坐标不查）。
- 讲稿先找 `notes/<key>.md`，没有时用页里 `slide.addNotes()` 的文字。

### 3.1 挪页：`tools/move.py`

```
python3 engine/tools/move.py <deck> <key> (--after <key> | --before <key> | --to <节> [--first | --last]) [--dry-run]
python3 engine/tools/move.py <deck> --respace <节> [--dry-run]        # 集成者用，串行
```

- 只替换这一页文件里 `section` 和 `order` 两个值，文件其余字节不变。页文件用正则读，不运行 node。
  `--after` / `--before` 同时把页挪进那一页所在的节；`--to` 默认放到节末（`--last`）。
- **新 order**：两个新邻居的中点，取能严格落在两者之间的最少小数位（能取整数就取整数，最多 3 位小数）。
  放到节首时取第一页 order 以下最大的 10 的倍数（可以是 0 或负数），放到节末时取最后一页以上最小的 10 的倍数，空节取 10。
- 两个邻居之间没有这样的值时什么都不写，退出码 2，并打印集成者要跑的 `move.py <deck> --respace <节>` 命令。
  `--respace` 把一节重排成 10、20、30 …，一次改多个页文件。
- 挪动页及其新旧邻居的页文件**和 `notes/<key>.md`** 里依赖页序的字样（"next slide"、"as shown before"、「下一页」「如前所示」…）
  打印成 WARNING，由负责人改。
- 不构建，只打印接下来要跑的 `build.js <deck> --list` 和 `--only <key> --out <scratchpad>/<key>.pptx --png`。
- 退出码：0 完成（或无需改动），2 用法或 deck 错误（含没有空位）。

## 4. primitives.js 必须导出（build.js 和页文件依赖）

- `configure({figDir, iconDir, refs, theme})`：build.js 在调用任何页之前调一次，`theme` 是读进来的 theme.json 对象（带 `_dir` = 主题目录，
  素材路径相对它解析）。没给的键保持原值；`figDir` / `iconDir` 为 `null` 时恢复默认（`research-skills/examples/figures`、`.../icons`），
  `theme` 为 `null` 时恢复 neutral。
- `T`：主题里除 `geometry` 以外的部分（`T.color.accent`、`T.font.body`、`T.size.title`、`T.dpi` …）；`G`：`geometry`
  （`G.margin`、`G.full`、`G.conclusion.yFigure` …），另加 `G.slideW` / `G.slideH`（= `slide.w` / `slide.h`）和 `G.contentW`（= slideW − 2 × margin）。
  两个都是活的只读视图：`configure()` 换了主题，读到的就是新值。没调过 `configure()` 时是 `themes/neutral` 的值。
- v1 的扁平常量（`C`、`FONT`、`SERIF`、`SW`、`SH`、`MX`、`CW`、`FIG_Y`、`CONC_Y`、`CONC_H`、`CONC_TEXT_Y`、`CONC_PT`、`CONC_INDENT`、
  `CONC_AFTER`、`FIG_DPI`，以及 `FIG`、`ICONS` 两个目录）继续导出，也是活视图、取自主题，供旧代码用；新代码用 `T` / `G`。
  `themes/neutral` 的值与 v1 常量逐一相同，所以用默认主题时输出与 v1 逐像素一致。
- `newDeck(title)` → pptxgenjs 实例，版面尺寸取主题的 `slide`。
- `newSlide(pres, title, n, opts)` → slide；按主题画背景、标题、logo、页码，把 `{page: n, title}` 记进内部页表。
  `opts.logo = false` 不画 logo，`opts.chrome = false` 三样都不画（标题仍记进页表）。
- `takePageLog()` → 取出并清空页表（按调用顺序）。
- `icon(slide, name, x, y, size, variant)`：`name` 是 `<来源>/<图标>`（如 `healthicons/microscope`），`variant` 是 `"grey"`（正文色）或
  `"accent"`。先找 `<主题目录>/icons/png/<name>[_accent].png`（`tools/theme_icons.py` 写），没有时用 `<iconDir>/png/` 下的同名文件。
- 其余版式元素（`figure`、`fitImage`、`table`、`conclusion`、`source`、`cite`、`abbr`、`draft`、`arrow` / `thinArrow` /
  `thickArrow`、`stepArrow`、`mark`、`titleFrame`、`emphasis` …）的样式全部取自 `T` / `G`。
  规则不变：结果图 1:1 放置、不缩放（`figure()` 按「像素 / 主题 dpi」算尺寸）；主图放到本页 z 序最底。
- primitives.js 是共享文件，只追加，由集成者改。新版式元素先放在 deck 的 `slides/_lib/` 里，用过两次再并进来。

## 5. 主题：换模板就换风格

### 5.1 theme.json

**完整字段以 [themes/neutral/theme.json](themes/neutral/theme.json) 为准**，当前内容如下：

```json
{
  "name": "neutral",
  "source": null,
  "slide": {"w": 13.333, "h": 7.5},
  "dpi": 200,
  "color": {
    "background": "FFFFFF", "text": "595959", "ink": "222222", "black": "000000",
    "muted": "7F7F7F", "rule": "D9D9D9", "tint": "F3F3F3",
    "accent": "A51C30", "accentTints": ["C45566", "DD99A3", "F1D3D8"],
    "blue": "2A78D6",
    "emphasisTransparency": 88
  },
  "plot": {"ink": "222222", "muted": "6B6B6B", "grid": "E6E6E6", "low": "C0392B", "high": "2A78D6", "mid": "8A8A8A"},
  "font": {"display": "Arial", "body": "Arial", "serif": "Times New Roman", "plot": ["Arial", "DejaVu Sans"]},
  "size": {"title": 28, "body": 16, "conclusion": 18, "table": 12, "source": 9, "abbr": 9.5, "page": 12,
           "plotBase": 12, "plotMin": 11,
           "logo": 11, "draft": 12, "pattern": 12},
  "geometry": {
    "margin": 0.6,
    "title": [0.59, 0.36, 9.6, 0.6],
    "logo": [10.983, 0.2, 2.0, 0.35],
    "figureTop": 1.1, "full": [12.1, 4.6], "half": [5.9, 4.6], "gap": 0.2,
    "conclusion": {"yFigure": 5.75, "yText": 5.95, "h": 1.05, "indent": 22, "after": 10},
    "source": [0.6, 6.82, 11.683, 0.6],
    "page": [12.363, 7.0, 0.6, 0.3],
    "titleSlide": {"logo": [0.6, 0.3, 2.4, 0.35], "accentBar": [0.6, 2.3, 0.1, 1.86], "accentRule": [0, 6.83, 13.333, 0.05]},
    "abbr": [0.6, 6.85, 6.0, 0.55],
    "draft": [10.683, 0.66, 2.35, 0.32],
    "pattern": [9.583, 0.62, 3.4, 0.3],
    "bullet": {"indent": 16, "after": 8, "afterLarge": 10, "largeFrom": 18},
    "tableCellMargin": [0.04, 0.1, 0.04, 0.1],
    "mark": 0.36,
    "stepArrow": [0.2, 0.24],
    "stroke": {"line": 0.75, "rule": 1, "arrowThin": 1, "arrowThick": 3.5, "mark": 1.5, "markGlyph": 2,
               "emphasis": 1, "tableOuter": 1.5, "tableInner": 0.75}
  },
  "asset": {"logo": null, "titleLogo": null},
  "provenance": {}
}
```

- `configure({theme})` 把给的主题深合并到 neutral 上（对象逐键合并，数组和标量替换），所以缺字段的主题也能用。
- 坐标单位是英寸，框写成 `[x, y, w, h]`，原点在左上。`geometry.abbr` / `draft` / `pattern` 是绝对框，不随 `margin` 变。
  `color.emphasisTransparency` 是数字（强调框的透明度），不是颜色，`theme_from_pptx` 不改它；`color.blue` 只用在图里用蓝色的地方；
  `geometry.stroke` 是各种线宽（pt）。
- **accentTints 的规则**：`color.accent` 和白色按 25 %、50 %、75 % 的白色比例混合，每个通道 c′ = c + (255 − c) × f，四舍五入
  （`000000` → `404040`、`808080`、`BFBFBF`）。`theme_from_pptx` 按这条规则写；手改 `accent` 时按同一规则重算。neutral 主题的
  `accentTints` 沿用 v1 的手调值，不是按这条规则混出来的。
- `asset` 里的路径相对主题目录；`asset.logo` 为 `null` 时在 `geometry.logo` 画灰色的 `YOUR LOGO` 占位字，给了图片就画图片
  （拉伸到框里，所以框要按图片比例量）；`asset.titleLogo` 同理，画在 `geometry.titleSlide.logo`。只有 SVG 的 logo 由 `theme_from_pptx`
  另渲一份 PNG，`asset` 指向 PNG，SVG 留在主题目录里（§5.2）。
- `templatePictures`（neutral 里没有，由 `theme_from_pptx` 写）：模板 slide master 和各 layout 上的每张图片，每个（文件，框）一条
  `{file, svg, box, background, from}`。`file` 是拷进主题目录的文件名（有栅格图时是栅格图）；`svg` 是同一张图的 SVG 文件名，
  只在栅格图和 SVG 都有时才有，否则 `null`；`box` 是 `[x, y, w, h]`（英寸）；`background` 为 `true` 表示它盖住超过半张页面，
  算背景，不会被选作 logo；`from` 是它出现的位置列表（`"master"`、`"layout '<名字>'"` …）。primitives 不读这个字段：它记下模板里有什么，
  需要的话把其中的图片手工接进 `asset`。
- **图标跟着主题变色**：`icon(…, "accent")` 用按强调色渲染的 PNG。换了 `color.text` 或 `color.accent` 后用 `tools/theme_icons.py`
  重新生成主题图标（§5.4）；`icon()` 先找 `<主题目录>/icons/png/`，找不到再用 `iconDir`。
- `plot` 是画图用的颜色（`low` / `high` / `mid` 是按位置配色的三条曲线：下面的红、上面的蓝、中间的灰），由 `plotting/style.py` 读；
  `size.plotBase` / `plotMin` 是图里的字号。
- `provenance` 记录每个字段（点分 key）的来源：`"template"`（从模板读出）或 `"default"`（模板里没有，沿用 base 主题）。由 `theme_from_pptx.py` 写。
- 主题只管样式，不管内容：讲者姓名、文献、节名不进主题。

### 5.2 从模板生成：`tools/theme_from_pptx.py`

```
python3 engine/tools/theme_from_pptx.py <template.pptx> --out <主题目录> [--base <theme.json>] [--force]
```

只用标准库读 pptx 里的 XML，从模板里能读到什么就取什么：

| 主题字段 | 读自模板的 |
|---|---|
| `name` / `source` | 模板文件的主名 / 文件名 |
| `slide` | `ppt/presentation.xml` 的 `sldSz`（EMU ÷ 914400，保留 3 位小数） |
| `color.background` / `text` / `accent` | `ppt/theme/theme1.xml` 的 `clrScheme`：`lt1`、`dk2`（没有时用 `dk1`）、`accent1`；取 `srgbClr`，或 `sysClr` 的 `lastClr` |
| `color.accentTints` | 由 `accent` 按 §5.1 的规则和白色混出（25 %、50 %、75 % 白） |
| `font.display` / `body` | `fontScheme` 的 `majorFont` / `minorFont`（`latin`） |
| `geometry.title` | slide master 里 `type="title"` 占位符的 `xfrm`；master 上没有时取第一个有它的 layout（先看 title-only / title-and-body 版式） |
| `geometry.margin` | slide master 里 body 占位符的左边 x（同样可以回落到 layout） |
| `asset.logo` + `geometry.logo` | slide master 上最靠右上角的图片；master 上没有图片时，取被最多 layout 共用的那张（并列时取最靠右上的）；标题页 layout 的图片不参与 |
| `asset.titleLogo` + `geometry.titleSlide.logo` | 标题页 layout（`type="title"`，或名字含 "Title Slide"）上的图片；多张时取最上面那张 |
| `templatePictures` | master 和各 layout 上的全部图片（§5.1） |

- `--out` 是要写的主题目录（theme.json + 图片）。每张图片的媒体文件按原文件名（含扩展名）拷进去；一张图同时有栅格图和 SVG 时，
  栅格图作素材，SVG 记在 `svg`。盖住超过半张页面的图片算背景：列进 `templatePictures`，但不会被选作 logo。
- 选中的 logo 或 titleLogo **只有 SVG** 时，用 `tools/svg_raster.py`（headless Chrome）在 SVG 旁边渲一份 PNG
  （高度 = 框高 × 600 px/英寸，保持比例；和已有文件重名时叫 `<名>_from_svg.png`），`asset` 指向这份 PNG，SVG 保留。
  找不到 Chrome（环境变量 `DECK_CHROME` 可以指定）或渲染失败时 SVG 仍作素材，打一行 WARNING。
- 模板里没有的字段（图框、结论框、来源行、字号、画图颜色）沿用 `--base`（默认 `engine/themes/neutral/theme.json`；这个文件不存在时用
  脚本里内置的一份 §5.1 默认值），并在 `provenance` 里标 `"default"`。工具运行结束后打印两列清单：哪些字段取自模板，哪些沿用默认，
  沿用默认的需要人看一眼。
- 总会打印一条 NOTE：`color.accent` 取的是模板的 `accent1`，它**常常不是品牌色**（品牌色可能只在 logo 里），必须人工核对，
  必要时手改 `color.accent` 和 `color.accentTints`。
- 其余提示：模板没有 `dk2`、标题框取自 layout、某个 layout 挪了标题框时打 NOTE；模板页面尺寸与 base 不同时打 WARNING（默认框需要检查）；
  模板字体本机没装时（例如 Aptos，用 `fc-list` 查）打 WARNING：LibreOffice 预览会换成更宽的字体，折行和 PowerPoint 不同。字体文件不进仓库。
- 已有 `<out>/theme.json` 时不覆盖，除非给 `--force`。退出码：0 写成，2 用法错误（pptx 读不了、theme.json 已存在又没给 `--force`、base 读不了）。
- 不做的事：不复制模板的 slide master 本身（pptxgenjs 不能载入现成的 master），只取它的样式。所以模板里复杂的背景图案和装饰不会自动跟过来，
  需要的话把它们存成图片放进 `asset`，再在 `newSlide` 里画。

### 5.3 换风格的流程（集成者做，串行）

1. `theme_from_pptx.py <新模板>.pptx --out <deck>/theme_<名字>`，看清单和 NOTE（尤其是强调色），必要时手改 theme.json；
2. 把 `deck.config.js` 的 `theme` 指过去（旧主题目录保留）；
3. 用 `tools/theme_icons.py <deck>` 按新主题的颜色重新生成图标（写进 `theme` 指向的目录）；
4. 主题的 `geometry.full` / `half`、`dpi`、`font.plot`、`size.plotBase` / `plotMin`、`plot` 颜色变了时，用 `tools/plot.py <deck>` 整套重画；没变时不用重画；
5. 整套构建，跑 `layout_check.py`，逐页看 PNG。

页文件、大纲和讲稿都不用改。

### 5.4 主题图标和 SVG 栅格化：`tools/theme_icons.py`、`tools/svg_raster.py`

```
python3 engine/tools/theme_icons.py <deck> [--all] [--size 512] [--dry-run] [--workers 4]
python3 engine/tools/svg_raster.py <in.svg> <out.png> [--height PX] [--width PX] [--size PX] [--color RRGGBB]
```

**theme_icons.py** 按 deck 主题的颜色渲染这个 deck 用到的图标：

- 主题目录取 deck.config.js 的 `theme`（不写时 `<deck>/theme`），里面必须有 theme.json；单色图标的两种颜色取 `color.text`（`grey` 变体）
  和 `color.accent`（`accent` 变体）。图标库取 `iconDir`（`null` = `research-skills/examples/icons`），里面是 `<来源>/<名>.svg` 和 `manifest.csv`。
- 渲哪些：`slides/*.js` 和 `slides/_lib/*.js` 里所有 `icon(<slide>, "<来源>/<名>", …)` 的字面字符串；名字不是字面字符串的调用打成 NOTE，不渲。
  `--all` 改为渲 `manifest.csv` 里的全部图标。
- 写什么：`<主题目录>/icons/png/<来源>/<名>.png`（单色图标，正文色）和 `<名>_accent.png`（单色图标，强调色）；多色图标只有一份
  `<名>.png`，从 `<iconDir>/png/` 复制（没有时按原色渲），没有 accent 变体。列出的 PNG 每次运行都重写（它们取决于主题颜色）；
  `--dry-run` 只打印计划。`--size` 是 PNG 边长（像素），`--workers` 是并行的 Chrome 进程数。
- 写进的是 `theme` 指向的目录：deck 用的是共享主题（如 engine 的 neutral）时，图标也写进那个共享目录。
- 退出码：0 完成，1 有图标渲染失败，2 用法错误（没有 deck.config.js 或 theme.json、颜色读不了、要渲染却找不到 headless Chrome）。

**svg_raster.py** 用 headless Chrome 把一个 SVG 渲成透明 PNG，theme_icons.py 和 theme_from_pptx.py 都调它：

- `--height` 或 `--width` 只给一个时，另一边按 SVG 的 viewBox 比例算；两个都给就用两个；`--size` 是正方形。三个至少给一个。
- `--color` 只给单色 SVG 改色：用 `currentColor` 或最多一种显式颜色、且不嵌 `<image>` 的 SVG 算单色；改色时替换 `currentColor` 或那一种颜色，
  没有显式颜色时在根元素上设 `fill`。多色 SVG 按原色渲。规则与 `examples/icons/render_pngs.py` 相同。磁盘上的 SVG 不改。
- 浏览器：设了 `DECK_CHROME` 时只用它；否则用 PATH 上 `google-chrome`、`chromium-browser`、`chromium` 中的第一个。
- 退出码：0 写成，2 错误（参数不对、找不到 Chrome、SVG 读不了、渲染失败）。

## 6. 画图：`plotting/` 包

不用一个大脚本（`make_figures.py`）画全部图，而是一个包、按 deck 的节分模块，这样几个 agent 可以各管各的模块：

```
plotting/
  __init__.py
  style.py        读主题：FULL / HALF / DPI、颜色、字体，apply_style()、save()；所有模块共用。主题目录取环境变量
                  DECK_THEME（plot.py 按 deck.config.js 的 theme 设好），没有时用 ../theme；figures 目录取 DECK_FIG_DIR，没有时用 ../figures
  common.py       几个模块共用的数据读取和小工具；不注册图；可以导出 INPUTS
  <节>.py         图模块，如 survival.py、methods.py；一个模块同一时间只由一个 agent / 人负责
```

- **图模块**在文件末尾导出 `FIGURES = {注册名: 可调用对象}` 和 `INPUTS = [结果表路径, …]`。可调用对象返回 `(figure, stats)`，
  `stats` 是能写成 JSON 的 dict：上屏的数字都要在这里能找到。
- 注册名就是 PNG 名，用节名开头（`survival_km_tamoxifen`），这样不同模块不会重名。
- 图模块之间不互相 `import`；只依赖 `style`、`common` 和第三方库。耗时或有副作用的 import（scanpy 之类）放在函数里。
- 图一律按上屏尺寸画（`style.FULL`、`HALF` 或自定义），`save()` 不用 tight bbox。字号就是上屏字号，规则见 [figures.md](../../../shared/figures.zh-CN.md)。

**入口** `python3 engine/tools/plot.py <deck> [--only a b …] [--out-dir <目录>] [--list]`：

- 先设 `DECK_THEME`（deck.config.js 的 `theme`，相对 deck 目录；目录不存在时打 WARNING 用 `engine/themes/neutral`；没有 deck.config.js
  或没写 `theme` 时也用 `engine/themes/neutral`）和 `DECK_FIG_DIR`（`figDir`，默认 `<deck>/figures`；`--out-dir` 时是它），
  再把 `<deck>` 放进 `sys.path` 后 import `plotting`。deck.config.js 只用正则读 `theme:` 和 `figDir:` 两个字符串字段，不运行 node。
- 不认识任何一张图的名字：import `plotting/` 里除 `style`、`common` 和 `_*` 以外的每个模块，合并它们的 `FIGURES` / `INPUTS`；
  两个模块注册了同名的图时，退出码 2，并报出两个模块名。
- 有 `style.apply_style()` 时先调它。每张图：有 `style.save(fig, name)` 时用它存，否则 `fig.savefig(<图目录>/<名>.png,
  dpi=<style.DPI，或主题 dpi，默认 200>, facecolor="white")`，不用 tight bbox；存完关掉 figure。
- 写 `figures/<名>.png` 和 `figures/run_meta/<名>.json`：`{figure, png, module, stats, inputs, versions, created, theme}`（`theme` = 所用主题目录，
  即 `DECK_THEME`），其中 `inputs` 是这个模块的 `INPUTS` 加上 `common.INPUTS`。`--only` 只写自己那几张图的文件，并行运行互不覆盖。
- `--out-dir` 把 PNG 和 run_meta 写到别处（回归对比），不碰 `figures/`。`--list` 打印注册名和所属模块，不画图。
- 退出码：0 完成；1 某张图画失败或没有返回 `(figure, stats)`（打印 traceback，后面的图不再画）；2 用法或注册错误
  （deck 目录不存在、同名注册、`--only` 里有未注册的名字）。
- **并行时永远带 `--only`**。整套重画只在换主题时由集成者做。

## 7. 大纲：`outline/`

格式见 [outline-format.md](../reference/outline-format.zh-CN.md)，要点：

- `outline/README.md` 是索引：约定、目录（每个章节文件写它管哪几页，用 `{{keyA}}–{{keyB}}`），以及两个生成块
  `pages:counts`、`pages:table`（§8.4）。生成块只由集成者用 `pages.py --table --write` 重写。
- 一章一个文件 `NN_<章>.md`，每页一个块，块标题带 `{{key}}`；块里写 Message（上屏原句）、Figure（`plotting/<模块>.py` 的注册名）、
  数字及其来源（表的行列或 run_meta 的键）、可能被过度解读的地方、状态（✅ / ⚠️ / ✏️）。
- 活文档里不手写页号和页标题，只写 `{{key}}`、`{{key.title}}`、`{{key.page}}`；反引号里的不展开、不检查。
- 历史进 `CHANGELOG.md`，章节文件只写当前状态。

## 8. 构建与数据文件

### 8.1 build.js 命令行

```
node engine/js/build.js <deck 目录> [--list] [--list-sections]
                                     [--only k1,k2 | --sections a,b] [--out <file.pptx>] [--png]
                                     [--release] [--pdf | --no-pdf]
```

- **收集页**：读 `slides/*.js`（不递归，跳过 `_*`），校验 key、`section`、`order` 和 `build`，有问题时一次列出全部问题，退出码 2。
  排序：先按 `sections` 里节的顺序，再按 `order`。
- **严格与宽松**：整套构建（默认、`--release`、只带 `--out`）和 `--list` / `--list-sections` 要求所有页文件都没问题。
  部分构建（`--only` / `--sections`）只在问题涉及选中的页（或选中的节）、不涉及具体页（比如 `slides/` 不存在），或者 `--only` 给了
  不存在的 key、`--sections` 给了不存在的节时才报错退出；选中范围以外的页文件有问题时只打一行 WARNING
  （"other page files have problems (not built here; page numbers may be off)"）照常构建。这样别的 agent 改了一半的页不会挡住自查；
  有问题的页不计入页序，所以这时页脚的页码可能偏。
- **默认（不带参数）**：整套构建，写 `<outDir>/<name>_wip.pptx`、`.pages.json`、`.pdf`，覆盖上一版 wip。先写临时文件，成功后改名，中途失败时上一版 wip 原样保留。
- **`--release`**：写 `<outDir>/<name>_v<N>.pptx`（N 为现有最大版本号 + 1），连同 `.pages.json` 和 `.pdf`，已有版本不覆盖（同名 PDF 已存在时也不覆盖）。
  不能和 `--out`、`--only`、`--sections` 同时用。
- **只带 `--out <file.pptx>`**：整套 deck 构建到这个文件（路径相对当前目录，已存在时替换），不拿锁，默认不出 PDF。`--out` 必须以 `.pptx` 结尾，
  不能是 wip 或 release 的文件名。示例 deck（`examples/slides/render.sh`）就是这样构建的。
- **整套构建锁**：默认构建和 `--release` 先建 `<outDir>/.build.lock`（独占创建，内容是 pid 和开始时间），结束时删掉（失败或被信号中断时也删）。
  锁已存在且那个 pid 还活着时，退出码 3，提示另一个整套构建正在进行；pid 已经不在时打印一行 WARNING，接管这把锁。
  锁里读不出 pid 时（另一个构建可能刚建锁还没写完），锁文件最后一次修改后 10 秒内算活着，超过 10 秒按过期接管。
- **部分构建** `--only k1,k2` 或 `--sections a,b`：必须给 `--out`（放在自己的 scratchpad 里），不能写 wip / release，也不拿锁。
  页按整套 deck 的顺序出，**页脚写整套 deck 里的真实页码**。页码由全部页文件的 section 和 order 算出，所以不用把别的页也建一遍。默认不出 PDF。
  `--only` 和 `--sections` 不能同时用。
- **`--png`**：隐含出 PDF（部分构建也出），再用 pdftoppm 按 60 dpi 把每页渲成 PNG，放到 `<out 的主名>_png/<页码两位>-<key>.png`，
  这个目录每次整个替换，给 agent 自己看页。`--png` 和 `--no-pdf` 同时给是参数错误（退出码 2）。`--pdf` / `--no-pdf` 强制出 / 不出 PDF。
- **`--list`**：打印整套页序（页码、节、order、key，隐藏页标 `(hidden)`），不构建；**`--list-sections`**：打印每节的 key、页数和页 key。
- supplementary 节的页设为隐藏（`show="0"`）。PDF 从一份去掉 `show="0"` 的临时副本转出（LibreOffice < 7.4 会跳过隐藏页），所以 PDF 的页和 pages.json 一一对应。
  soffice 用独立的 `-env:UserInstallation` 临时 profile，可以并行转换；soffice 依次找 `$DECK_SOFFICE`、PATH、`/usr/bin/soffice`、`/opt/libreoffice*/program/soffice`。
  找不到 soffice 或转换失败时只打 WARNING，pptx 照写、旧 PDF 不动，退出码 0；找不到 pdftoppm 时同样只打 WARNING。
- 讲稿见 §8.3；页文件里的颜色、字体字面量打 WARNING（§3）；`notes/` 里没有对应页文件的 `.md`、deck 里残留的 v1 `notes.json` 各打一行 WARNING。
- pptxgenjs 依次从 `NODE_PATH`、`<deck>/node_modules`、`<research-skills>/node_modules` 找；找不到时退出码 1，并提示 `npm install pptxgenjs`。
- **退出码**：0 成功；1 构建失败（页的 `build()` 抛错、找不到 pptxgenjs、写文件失败），上一版输出原样保留；
  2 deck 或参数无效（deck.config.js、页文件、order 冲突、某页没有恰好建出一页——这时什么都不写）；3 另一个整套构建持有锁。
- stdout 最后一行是 pptx 路径。

### 8.2 pages.json（每次构建都写在 pptx 旁边，文件名 `<输出名>.pages.json`）

```json
[{"page": 1, "title": "Title", "section": "title", "order": 10, "builder": "sTitle"},
 {"page": 2, "title": "Recurrence-free Survival", "section": "results", "order": 20, "builder": "sKmTamoxifen"}]
```

- 一页一行。`page` 是这一页在整份 deck 里的序号（从 1 起，含标题页和 supplementary 页）；部分构建写的也是这个序号。`builder` 就是 key。
- 页标题可以重复（比如渐进强调，同一个标题连放两页）。build.js 和 pages.py 遇到重复只打 WARNING，`{{key.title}}` 照常展开。
- 没有标题的页（`newSlide(pres, null, n)`，比如节的分隔页）`title` 是 `null`，pages.py 当空标题显示。
- key 或页码重复时 pages.py 报 FATAL，退出码 2。

### 8.3 讲稿：`notes/<key>.md`

- 一页一个纯文本文件，UTF-8，一行一个段落。构建时用它整段替换这一页的讲稿，再按换行拆成多个 `<a:p>`。**空文件 = 清空这一页的讲稿**
  （`addNotes()` 的文字也不要）。没有文件的页保留 `addNotes()` 的文字。

```
python3 engine/tools/pull_notes.py <deck> [pptx] [--dry-run | --write] [--pages <pages.json>]
```

- `pptx` 可以不给，默认是 `<outDir>/<name>_v<N>.pptx` 里版本号最大的 release（没有 release 时报错，要显式给讲者的 pptx）；
  pages.json 默认 `<outDir>/<name>_wip.pages.json`。不带 `--write` 只报告（`--dry-run` 只是把这一点写明）。
- 按页标题把 pptx 的讲稿配到 key 上，依次试：(a) 第一页配 pages.json 的第一条（那条标题是 `Title` 或与该页标题相同时）；
  (b) `notes/_aliases.json` 里的别名 `{"<pptx 页标题>": "<key>"}`，同一标题在 pptx 里出现多次时写 `"<标题>"`、`"<标题>#2"` …；
  (c) 标题在 pages.json 里恰好一条、在 pptx 里只出现一次。重复的标题从不自动配，必须写别名。
- **只写内容有变化的** `notes/<key>.md`（比较前两边做同样的规范化，行尾空白、CRLF、末尾缺换行都不算变化）。pptx 里讲稿为空、而这一页还没有
  讲稿文件或文件里是别的文字时，写一个**空文件**（构建时清空这一页的讲稿）。
- **从不删文件**。`notes/` 里不对应 pages.json 任何 key 的文件列出来（保留；页确实删了就手删）。
- 标题配不上、重名又没有别名、key 不在 pages.json 里或已被前面的页占用的 pptx 页不写，列在报告里和 `notes/_unmatched.json` 里
  （每条 `{slide, title, occurrence, reason, notes}`）；`--write` 每次重写这个文件（全部配上时是 `[]`）。加别名后重跑。
- `--write` 先把要改的已有文件拷到 `<deck>/.backups/<时间戳>/notes/`（时间戳 `YYYYMMDD_HHMMSS`），再写。
- 讲稿文本取 notes 页的 body 占位符：段落和软换行都变成换行，格式（粗体、字号）不保留；讲者误打在页码占位符里数字后面的字作为额外一段保留。
- 退出码：0 完成（包括有配不上的页）；2 deck、pptx、pages.json 或 `_aliases.json` 有问题（FATAL）。
- 讲者在 PowerPoint 里改过讲稿之后，讲者的 pptx 就是真相来源，`--write` 由集成者跑。

### 8.4 大纲生成块（tools/pages.py 维护）

```
python3 engine/tools/pages.py [<deck>] [--check | --show <文件> | --keys | --table [--write]] [--pages <pages.json>] [--ignore-file <txt>]
```

生成块的语言由 deck.config.js 的 `lang` 决定。`lang: "en"`（默认）：

```markdown
<!-- pages:counts:start -->
N slides (section key and slide count): `title` 1 · `results` 2 · …
<!-- pages:counts:end -->

<!-- pages:table:start -->
| Page | Section | Subsection | Slide title | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | … |
<!-- pages:table:end -->
```

`lang: "zh"`：

```markdown
<!-- pages:counts:start -->
共 N 页（节 key 和页数）：`title` 1 · `results` 2 · …
<!-- pages:counts:end -->

<!-- pages:table:start -->
| 页 | 节 | 小节 | 页标题 | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | … |
<!-- pages:table:end -->
```

- 表里「小节」「Note」两列是手写的，`--table --write` 按 key 保留；其余列从 pages.json 生成。新行的占位是 `—` 和
  `(Note to be added)`（`zh`：`（待补 Note）`）；已经不是页的 key 打印出来（它的 Note 丢掉）。
- 表行按位置读，所以表头是哪种语言（或 v1 的 `key（builder）`）都认；Note 还是任一语言的占位时按 deck 的语言重写。改了 `lang` 后跑
  `--table --write` 就切换过来，在此之前 `--check` 报生成块过期。
- 扫描的文件：`README.md`、`TODO.md`、`outline/*.md`（`lang: "zh"` 时优先用对应的 `.zh-CN.md`），另一种语言的跳过，`outline/archive/` 不读。
- `--check`（默认，只读）报：[k] 没有对应页的 `{{key}}` 或格式不对的 `{{…}}`；[r] 代码和生成块以外手写的页号 `P<数字>`（页码表里手写的 Note 也查）；
  [b] 行内代码里像 key 的名字 `sXxx`，既不是 pages.json 的 key 也没有页文件；[g] 过期的生成块。有错时退出码 1。
  `--show <文件>` 打印展开后的文件（有未知 key 时退出码 1），`--keys` 打印每页的页码、key、节和标题，
  `--table` 不带 `--write` 只打印 diff；`--write` 先把要改的文件拷到 `<deck>/.backups/<时间戳>/<相对路径>`。
- 默认 pages.json 是 `<deck>/<outDir>/<name>_wip.pages.json`。用 `--out` 构建的 deck（比如 `examples/slides/` 的示例 deck）没有 wip，
  要传 `--pages <out 的主名>.pages.json`。
- 不是页号的命中（比如蛋白 P53）：在 `<deck>/pages_ignore.txt` 里写一行 `file:regex`（`--ignore-file` 可以换文件）；含 `<!--pages:ignore-->` 的行跳过 [r] 检查。
- pages.json 缺失或读不了、key 或页码重复、deck.config.js 读不出 `name` 时 FATAL，退出码 2。

### 8.5 版面检查：`tools/layout_check.py`

```
python3 engine/tools/layout_check.py [<deck>] [--pptx <f>] [--pdf <f>] [--pages-json <f>] [--pages N …] [--png-dir <目录>] [--tol <pt>]
```

- 只读。默认读 `<deck>/<outDir>/<name>_wip.{pptx,pdf,pages.json}`，也可以不给 deck、直接给 `--pptx` 和 `--pdf`。
  标题字号取 deck 主题的 `size.title`（没有时用 neutral，再没有时 28 pt）。需要 poppler 的 `pdftotext`。
- 逐页报：HIDDEN-TITLE（标题被 z 序更高的图盖住）、TITLE-OVER-PIC、TITLE-WRAP（标题折行，报和下方元素的间距）、HIDDEN-TEXT、
  TEXT-OVER-PIC、TEXT-OVER-TEXT。`--pages` 只查这些页；`--png-dir` 把有问题的页用 `pdftoppm -r 60` 渲成 `page_<NN>.png`；
  `--tol` 是重叠阈值（pt，默认 3）。会有少量误报，渲出来的页说了算。
- 退出码：0 干净（或只有与下方元素间距 ≥ 4 pt 的 TITLE-WRAP），1 发现问题，2 用法错误（没有 pdftotext、文件缺失或读不了）。

## 9. 并行改 deck 的约定

| 操作 | 只写这些文件 | 谁做 |
|---|---|---|
| 新增一页 | `slides/<key>.js`，以及可选的 `notes/<key>.md`、所在章的大纲块、图模块里的新图 | 这一页的负责人 |
| 改一页 | 同上 | 这一页的负责人 |
| 挪一页 | 这一页文件的 `section` / `order`（`move.py <key> --after <key>`，只改这一个文件） | 这一页的负责人 |
| 删一页 | 删掉 `slides/<key>.js` 和 `notes/<key>.md`，在大纲块里写明已删 | 这一页的负责人；生成块由集成者刷新 |
| 画图 | `plotting/<模块>.py`、`figures/<名>.png`、`figures/run_meta/<名>.json` | 这个模块的负责人 |
| 改讲稿 | `notes/<key>.md` | 这一页的负责人；`pull_notes --write` 由集成者跑 |
| 版式元素、主题、节、共享代码 | `primitives.js`、`theme/`（含 `theme_from_pptx`、`theme_icons` 写的文件）、`deck.config.js`、`slides/_lib/`、`plotting/style.py`、`plotting/common.py` | 集成者，只追加 |
| 整套构建、release、`--respace`、`pages.py --table --write`、`pull_notes --write`、整套 `plot.py`、commit | wip / release 产物、生成块、`notes/`、`figures/`、git | 集成者，串行 |

- **自查**：每个 agent 用 `build.js <deck> --only <自己的 key> --out <scratchpad>/x.pptx --png` 出自己的页、看 PNG，
  用 `plot.py <deck> --only <自己的图>` 画图，不等整套构建。部分构建对选中范围以外的页宽松（§8.1），别人改到一半的页不会挡住自查。
- **还会冲突的地方**都会在构建时报出来：同一节里两页的 `order` 相同（build.js 报错，由其中一页的负责人改），以及两个模块注册了同名的图（plot.py 报错）。
  两个 agent 改同一个章节文件时只用 Edit 逐处改，不用 Write 整体重写（Edit 发现文件已被改时会失败，要求重读）。
- **措辞上的依赖**（「下一页」「如前页所示」）文件层面管不了。`move.py` 会把挪动页及其新旧邻居的页文件和讲稿里的这类字样打印出来，由负责人改。
- **git**：并行的 agent 各用自己的 worktree，由集成者合并；在同一个工作区时，集成者 commit 要显式列路径，**不用 `git add -A`**，
  免得把别人改了一半的文件一起提交。
- 并行安全不等于内容一致：同一个数字在几页上的说法、结论的口径，最后要由集成者对照大纲统一审一遍。

## 10. 沿用自一份已用过的 deck 的做法

下面这些做法在一份 90 页的项目 deck 里已经验证过，engine 原样保留：wip 先写临时文件再改名；release 按 `v<N>` 递增、不覆盖；
PDF 和 pptx 一起出，soffice 用独立 profile；supplementary 在 pptx 里隐藏、PDF 里照出；`pages.json` 加 `{{key}}` 页引用；
讲稿作为数据存放，并能从讲者改过的 pptx 同步回来；主图放到 z 序最底；用 `layout_check` 查碰撞；画图按节拆成模块、每张图一份 run_meta；
大纲按章拆文件，历史写进 CHANGELOG，旧版放 archive。

和那份 deck 不同的地方都是为了并行和换主题：那份 deck 一个 `slides_<节>.js` 管一串页，页序集中在一个 `SLIDES` 列表里（挪页、加页都要改它），
讲稿是一个整体重写的 `notes.json`，设计常量写在 `style.js` 里。

## 11. 语言约定

所有生成的产出物都用英文：页上文字、图中文字、表格、Source 行、speaker notes、PPTX、PDF 和预览图。`lang: "zh"` 只改变 pages.py 写进
大纲文档的生成块。面向用户的仓库文档维护为成对的 `X.md`（英文，GitHub 默认显示）和 `X.zh-CN.md`，两者第一行都是语言切换。

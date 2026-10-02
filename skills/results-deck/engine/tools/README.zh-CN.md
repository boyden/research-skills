[English](README.md) | **简体中文**

# engine/tools

results deck 的命令行工具：画图、页引用、讲稿同步、挪页、主题、图标和版面检查。只需要 Python 3.10+ 和标准库；`plot.py` 运行 deck 自己的画图代码（matplotlib），`theme_icons.py` 和 `svg_raster.py` 需要 headless Chrome，`layout_check.py` 需要 Poppler。每个工具都能用 `--help` 打印完整用法。背后的接口约定见 [../SPEC.zh-CN.md](../SPEC.zh-CN.md)；构建脚本 `js/build.js` 见 [../SPEC.zh-CN.md](../SPEC.zh-CN.md) §8.1。

第一个参数是 deck 目录，里面有 `deck.config.js`。这些工具不运行 node：它们用正则从 deck.config.js 读字面字符串字段 `name`、`outDir`、`figDir`、`theme`、`lang`、`iconDir`（move.py 另读 `sections`），所以这些字段要写成普通的字面字符串。下面的例子都在 engine 目录里、对模板 deck `template/` 运行。

| 工具 | 读 | 写 |
|---|---|---|
| [plot.py](#plotpy) | `plotting/`、主题 | `figures/<名>.png`、`figures/run_meta/<名>.json` |
| [pages.py](#pagespy) | pages.json，README / TODO / 大纲文档 | 这些文档里的生成块（`--table --write`） |
| [pull_notes.py](#pull_notespy) | 讲者改过的 PPTX、pages.json | `notes/<key>.md`、`notes/_unmatched.json`（`--write`） |
| [move.py](#movepy) | `slides/*.js`、`notes/<key>.md` | 一个页文件的 `section` / `order`（`--respace`：多个） |
| [theme_from_pptx.py](#theme_from_pptxpy) | 模板 PPTX | 一个主题目录（theme.json + 图片） |
| [theme_icons.py](#theme_iconspy) | 页文件、主题颜色、图标库 | `<主题目录>/icons/png/` |
| [svg_raster.py](#svg_rasterpy) | 一个 SVG | 一个 PNG |
| [layout_check.py](#layout_checkpy) | 构建出的 PPTX + PDF + pages.json | 不写（只报告） |

备份：`pages.py --table --write` 和 `pull_notes.py --write` 改文件之前，先把每个要改的已有文件拷到 `<deck>/.backups/<YYYYMMDD_HHMMSS>/<相对路径>`。

## plot.py

```
python3 tools/plot.py <deck> [--only NAME [NAME ...]] [--out-dir OUT_DIR] [--list]
```

```bash
python3 tools/plot.py template --list                         # 注册名和所属模块
python3 tools/plot.py template --only results_km              # 一张图（并行时永远带 --only）
python3 tools/plot.py template --only results_km --out-dir /tmp/figs   # 回归对比，不碰 figures/
python3 tools/plot.py template                                # 全部图（集成者，换主题之后）
```

- 按 deck.config.js 的 `theme` 设 `DECK_THEME`（相对 deck 目录；目录不存在时用 `engine/themes/neutral` 并打 WARNING，没写这个字段或没有 deck.config.js 时也用它，不打 WARNING），按 `figDir` 设 `DECK_FIG_DIR`（默认 `<deck>/figures`；给了 `--out-dir` 时是它）。然后 import `<deck>/plotting/` 里除 `style`、`common`、`_*` 以外的每个模块，合并它们的 `FIGURES = {注册名: 函数}` 和 `INPUTS = [...]`。
- 有 `style.apply_style()` 时先调它，再调每个选中的函数，函数必须返回 `(figure, stats)`。PNG 由 `style.save(fig, name)` 存（有的话），否则按主题 dpi、白底、不用 tight bbox 存。
- 写 `<图目录>/<名>.png` 和 `<图目录>/run_meta/<名>.json`：`{figure, png, module, stats, inputs, versions, created, theme}`；`inputs` 是模块的 `INPUTS` 加 `common.INPUTS`，`theme` 是所用主题目录。`--only` 只碰自己画的图的文件。
- 退出码：0 完成；1 某张图画失败或没返回 `(figure, stats)`（后面的图不再画）；2 用法或注册错误（deck 目录不存在、两个模块注册了同名的图、`--only` 里有未注册的名字）。

## pages.py

```
python3 tools/pages.py [deck] [--check | --show FILE | --keys | --table] [--write] [--pages JSON] [--ignore-file TXT]
```

```bash
python3 tools/pages.py template --check                       # 默认模式，只读
python3 tools/pages.py template --show outline/01_results.md  # 打印展开了每个 {{key}} 的文件
python3 tools/pages.py template --keys                        # 每页的页码、key、节、标题
python3 tools/pages.py template --table                       # 生成块的 diff（演练）
python3 tools/pages.py template --table --write               # 重写生成块（集成者）
```

活文档用 key 指页，不手写页号或页标题：

| 写法 | 展开为 | 用途 |
|---|---|---|
| `{{sKm}}` | `P2「Hormone Therapy — Recurrence-free Survival」` | 页号和标题 |
| `{{sKm}}–{{sForest}}` | `P2「…」–P3「…」` | 范围：两端各自展开 |
| `{{sKm.title}}` | `Hormone Therapy — Recurrence-free Survival` | 只要标题 |
| `{{sKm.page}}` | `P2` | 只要页号 |

- 默认读 `<deck>/<outDir>/<name>_wip.pages.json`。用 `build.js --out` 构建的 deck（比如 `examples/slides/` 的示例 deck）没有 wip，要传 `--pages <out 的主名>.pages.json`。
- 扫描 deck 的 `README.md`、`TODO.md` 和 `outline/*.md`；`lang: "zh"` 时优先用对应的 `.zh-CN.md`。`outline/archive/` 不读。行内代码和代码块里的 token 原样保留，不展开也不检查。
- `--check` 报：[k] 没有对应页的 `{{key}}` 或格式不对的 `{{…}}`；[r] 代码和生成块以外手写的页号 `P<数字>`；[b] 行内代码里像 key 的名字 `sXxx`，既不是 key 也没有页文件；[g] 过期的生成块。不是页号的命中（比如 P53）在 `<deck>/pages_ignore.txt` 里写一行 `file:regex` 忽略（`--ignore-file` 可以换文件），或在那一行加 `<!--pages:ignore-->`。
- `--table` 重写 `<!-- pages:counts:start/end -->` 和 `<!-- pages:table:start/end -->` 之间的生成块。手写的「小节」「Note」两列按 key 保留，新行填 `—` 和 Note 占位。`lang: "en"` 时生成块是 `N slides (section key and slide count): …` 和 `| Page | Section | Subsection | Slide title | key | Note |`，占位 `(Note to be added)`；`lang: "zh"` 时是中文（`共 N 页（节 key 和页数）：…`、`| 页 | 节 | 小节 | 页标题 | key | Note |`、`（待补 Note）`）。两种语言的表头都能读；改了 `lang` 再跑 `--table --write` 就切换过来。
- 退出码：0 干净；1 `--check` 发现错误，或 `--show` 遇到未知 key；2 FATAL（pages.json 缺失或读不了、key 或页码重复、deck.config.js 读不出 `name`、生成块的标记不配对）。

## pull_notes.py

```
python3 tools/pull_notes.py [--dry-run | --write] [--pages JSON] deck [pptx]
```

```bash
python3 tools/pull_notes.py template template/output/example_deck_wip.pptx   # 演练：只报告
python3 tools/pull_notes.py template <讲者改过的.pptx> --write                 # 集成者
python3 tools/pull_notes.py template --write                                  # pptx = 版本号最大的 output/example_deck_v<N>.pptx
```

- `pptx` 默认是版本号最大的 release `<outDir>/<name>_v<N>.pptx`（没有 release 时 FATAL）；`--pages` 默认 `<outDir>/<name>_wip.pages.json`。不带 `--write` 什么都不写。
- 按标题把 PPTX 的每页配到 key：第一页配 pages.json 第一条（那条标题是 `Title` 或相同时）；再查 `notes/_aliases.json`；再按在 pages.json 和 PPTX 里都只出现一次的标题配。重复的标题只能靠别名配，第一次出现写 `"<标题>"`，之后写 `"<标题>#2"`、`"<标题>#3"` …：

  ```json
  {
    "Clinical Factors — Univariate Cox": "sForest",
    "Clinical Factors — Univariate Cox#2": "sForestEmphasis"
  }
  ```

- 只写文字有变化的 `notes/<key>.md`（行尾和末尾空白不算变化）。PPTX 里讲稿为空时写一个空文件，构建时会清空这一页的讲稿。从不删文件；key 不在 pages.json 里的讲稿文件列出来，由人手删。
- 配不上的页（配不到、重复标题没有别名、key 不在 pages.json 里或已被占用）不写，列在报告和 `notes/_unmatched.json` 里（每次 `--write` 都重写，全配上时是 `[]`）。段落和换行保留，粗体和字号不保留。
- `--write` 先把要改的文件备份到 `<deck>/.backups/<时间戳>/notes/`。
- 退出码：0 完成（有配不上的页也是 0）；2 FATAL（deck、PPTX、pages.json 或 `_aliases.json` 缺失或读不了）。

## move.py

```
python3 tools/move.py (--after KEY | --before KEY | --to SECTION | --respace SECTION) [--first | --last] [--dry-run] deck [key]
```

```bash
python3 tools/move.py template sForest --before sKm --dry-run          # order 20 -> 0，成为 results 节第一页
python3 tools/move.py template sSummary --to results --last            # 挪进另一节的末尾
python3 tools/move.py template --respace results                       # 只有集成者用：10、20、30 …
```

- 只替换 `slides/<key>.js` 里 `section` 和 `order` 两个值，其余字节不变。`--after` / `--before` 同时把页挪进那一页所在的节；`--to` 默认放到节末，`--first` 放到节首。
- 新 order 是两个新邻居的中点，取能严格落在两者之间的最少小数位（能取整数就取整数，最多 3 位小数）。节首取第一页 order 以下最大的 10 的倍数（可以是 0 或负数），节末取最后一页以上最小的 10 的倍数，空节取 10。
- 没有这样的值时什么都不写，退出码 2，并打印给集成者的 `--respace` 命令。`--respace` 一次改多个页文件，只能串行。
- 挪动页及其新旧邻居的页文件和 `notes/<key>.md` 里依赖页序的字样（"next slide"、"as shown before"、「下一页」…）打印成 WARNING。不构建，只打印接下来要跑的 `build.js --list` 和 `--only <key> --out … --png`。
- 退出码：0 完成（或无需改动）；2 用法或 deck 错误（含没有空位）。

## theme_from_pptx.py

```
python3 tools/theme_from_pptx.py <template.pptx> --out OUT [--base BASE] [--force]
```

```bash
python3 tools/theme_from_pptx.py <品牌模板>.pptx --out template/theme_brand
```

- 读页面尺寸、主题色（`lt1`、`dk2` 或 `dk1`、`accent1`）、标题 / 正文字体、标题和正文占位符的框，以及 slide master 和各 layout 上的图片。logo 取 master 上最靠右上角的图片（master 上没有时取被最多 layout 共用的那张），标题页 logo 取标题页 layout 上的图片。`accentTints` 由强调色和 25 %、50 %、75 % 的白色混出。完整的字段对照见 [../SPEC.zh-CN.md](../SPEC.zh-CN.md) §5.2。
- 写 `<OUT>/theme.json`，把 master / layout 上的每张图片拷进 `<OUT>`；theme.json 的 `templatePictures` 把它们全部列出（`file`、`svg`、`box`、`background`、`from`）。只有 SVG 的 logo 用 `svg_raster.py` 另渲一份 PNG，素材指向 PNG（SVG 保留）。模板里没有的字段沿用 `--base`（默认 `engine/themes/neutral/theme.json`），`provenance` 把每个字段标成 `"template"` 或 `"default"`。
- 打印两列清单（取自模板 / 沿用默认）、一条 NOTE（`color.accent` 是模板的 `accent1`，常常不是品牌色，要人工核对），以及字体没装、页面尺寸和 base 不同时的 WARNING。
- 已有 `<OUT>/theme.json` 时不覆盖，除非给 `--force`。
- 退出码：0 写成；2 用法错误（PPTX 读不了、theme.json 已存在又没给 `--force`、base 读不了）。

## theme_icons.py

```
python3 tools/theme_icons.py [--all] [--size SIZE] [--dry-run] [--workers WORKERS] deck
```

```bash
python3 tools/theme_icons.py template --dry-run          # slides/*.js 和 slides/_lib/*.js 里点名的图标
python3 tools/theme_icons.py template                    # 按 template/theme 的颜色渲染
python3 tools/theme_icons.py template --all              # 图标库 manifest.csv 里的全部图标
```

- 主题目录：deck.config.js 的 `theme`（不写时 `<deck>/theme`），里面必须有 theme.json；颜色：`color.text`（`grey` 变体）和 `color.accent`（`accent` 变体）。图标库：`iconDir`（`null` = `research-skills/examples/icons`）。
- 渲染 `slides/*.js` 和 `slides/_lib/*.js` 里 `icon(<slide>, "<来源>/<名>", …)` 调用中以字面字符串给出的每个图标；名字不是字面字符串的打成 NOTE。`--all` 改为渲整个 `manifest.csv`。
- 单色图标写 `<主题目录>/icons/png/<来源>/<名>.png` 和 `<名>_accent.png`；多色图标只有一份，从 `<iconDir>/png/<来源>/<名>.png` 复制（没有时按原色渲），没有 accent 变体。列出的 PNG 每次都重写。primitives.js 的 `icon()` 先读这些文件，没有时用 `<iconDir>/png/`。deck 的 `theme` 是共享目录（比如 engine 的 neutral 主题）时，图标就写进那个共享目录。
- `--size` 是 PNG 边长（像素，默认 512）；`--workers` 是并行的 Chrome 进程数（默认 4）。
- 退出码：0 完成；1 有图标渲染失败；2 用法错误（没有 deck.config.js 或 theme.json、颜色读不了、找不到 headless Chrome）。

## svg_raster.py

```
python3 tools/svg_raster.py [--height HEIGHT] [--width WIDTH] [--size SIZE] [--color COLOR] svg png
```

```bash
python3 tools/svg_raster.py logo.svg logo.png --height 210          # 宽度按 viewBox 比例
python3 tools/svg_raster.py icon.svg icon.png --size 512 --color A51C30
```

- 用 headless Chrome 把一个 SVG 渲成透明 PNG。`--height`、`--width`、`--size`（正方形）至少给一个。`--color RRGGBB` 只给单色 SVG（用 `currentColor` 或最多一种显式颜色、不嵌图片）改色；多色 SVG 保持原色。磁盘上的 SVG 不改。
- 浏览器：设了 `$DECK_CHROME` 时只用它；否则用 PATH 上 `google-chrome`、`chromium-browser`、`chromium` 中的第一个。
- `theme_icons.py` 和 `theme_from_pptx.py` 都调它。
- 退出码：0 写成；2 错误（参数不对、找不到 Chrome、SVG 读不了、渲染失败）。

## layout_check.py

```
python3 tools/layout_check.py [--pptx PPTX] [--pdf PDF] [--pages-json PAGES_JSON] [--pages [PAGES ...]] [--png-dir PNG_DIR] [--tol TOL] [deck]
```

```bash
python3 tools/layout_check.py template                              # wip 的 pptx / pdf / pages.json
python3 tools/layout_check.py template --pages 2 3 --png-dir /tmp/lc   # 只查两页，有问题的页渲出来
python3 tools/layout_check.py --pptx /tmp/x.pptx --pdf /tmp/x.pdf  # 任意一对文件，不需要 deck
```

- 结合 `pdftotext -bbox-layout`（渲染出的文字行）和 PPTX 的 XML（图片框、文字框、z 序），逐页报 HIDDEN-TITLE、TITLE-OVER-PIC、TITLE-WRAP、HIDDEN-TEXT、TEXT-OVER-PIC、TEXT-OVER-TEXT。标题行按主题的 `size.title` 识别。
- 默认读 `<deck>/<outDir>/<name>_wip.{pptx,pdf,pages.json}`。`--png-dir` 把有问题的页渲成 `page_<NN>.png`（`pdftoppm -r 60`）；`--tol` 是重叠阈值（pt，默认 3）。除此之外只读。会有少量误报，渲出来的页说了算。
- 退出码：0 干净（或只有间距 ≥ 4 pt 的 TITLE-WRAP）；1 发现问题；2 用法错误（没有 pdftotext、文件缺失或读不了）。

## 语言约定

deck.config.js 里的 `lang: "zh"` 只改变 `pages.py` 写进大纲文档的生成块。deck 内容和生成的产出物仍然用英文。本文件与 [README.md](README.md) 是双语文档对。

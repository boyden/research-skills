[English](README.md) | **简体中文**

# Deck 模板

一套按 engine v2 结构写好的完整五页 deck（标题页、两页结果、总结、一页隐藏的 supplementary 表），数据是公开的 GBSG2 试验。它拿来就能构建：复制过去，先确认能构建，再替换内容。接口见 [../SPEC.zh-CN.md](../SPEC.zh-CN.md)，工具见 [../tools/README.zh-CN.md](../tools/README.zh-CN.md)。

```
deck.config.js        名称、标题、路径、主题、lang、文献、节的顺序
theme/theme.json      颜色、字体、字号、几何、logo（engine/themes/neutral 的副本）
slides/<key>.js       一页一个：{section, order, build(pres, n, P, ctx)}；共用版式在 slides/_lib/layouts.js
notes/<key>.md        讲稿，一页一份；notes/_aliases.json（空）给 pull_notes.py 用
outline/              README.md（索引 + 生成的页码表）和一章一个文件，各有 .zh-CN.md 中文版
plotting/             style.py（主题）、common.py（数据）、results.py（results 节的图）
figures/              按上屏尺寸画好的 PNG + run_meta/<名>.json（上屏的数字都在里面）
output/               构建产物；只有 *.pages.json 进 git（见 .gitignore）
.gitignore            忽略 output/*.pptx、*.pdf、*_png/、构建锁、.backups/、notes/_unmatched.json
```

下面 `E` 指 `<research-skills>/skills/results-deck/engine`，命令都在 deck 目录里跑。

## 开始一个 deck

```bash
cp -r $E/template <项目>/presentation/my_deck && cd <项目>/presentation/my_deck
rm -rf output/*.pptx output/*.pdf output/*_png               # 复制过来的构建产物（git 忽略）
NODE_PATH=<node_modules> node $E/js/build.js . --png      # 冒烟测试：5 页，没有 WARNING 行
```

复制之后删掉 `output/*.pptx`、`output/*.pdf` 和 `output/*_png/`：它们是模板的构建产物，git 忽略，冒烟测试会重新生成。`output/*.pages.json` 保留（进 git；`pages.py --check` 靠它展开 `{{key}}`）。然后在 `deck.config.js` 里改 `name`、`title`、`refs`、`sections`，再替换页、讲稿、大纲和图。`theme` 要一直显式写着（`"theme"`）：没有这个字段时，画图和版面检查工具会回落到 engine 的 neutral 主题。

## 改页、讲稿和大纲

- 一页就是 `slides/<key>.js`，文件名就是到处用的 key（大纲里的 `{{sKm}}`、`notes/sKm.md`、`--only sKm`）。`section` 必须在 `sections` 里；`order` 决定节内顺序（10、20、30 …，插页取 25）。
- 页文件的颜色、字体、几何一律取自 `P.T` / `P.G`，不写死（构建时会警告）。两页共用的版式放进 `slides/_lib/`，如 `slides/_lib/layouts.js` 里的 `titleSlide`、`numberedTakeaways`、`centeredTable`。
- 讲稿写在 `notes/<key>.md`（一行一段），会替换页里 `addNotes()` 的文字；空文件 = 清空这一页的讲稿。讲者改过 pptx 之后，`python3 $E/tools/pull_notes.py . <pptx>` 报告有哪些变化，加 `--write` 同步回来（不给 `<pptx>` 时读最新的 release `output/<name>_v<N>.pptx`）。
- 大纲记上屏原句、图的注册名、数字及其 run_meta 键、状态；页号一律写 `{{key}}`。挪页用 `python3 $E/tools/move.py . <key> --after <key>`（或 `--before <key>`、`--to <节>`），只改这一个页文件。

## 画图

```bash
python3 $E/tools/plot.py . --only results_km    # 一张图：figures/results_km.png + figures/run_meta/results_km.json
python3 $E/tools/plot.py . --list               # 注册名：results_km、results_forest
python3 $E/tools/plot.py .                      # 全部图（换主题之后）
```

`plotting/` 按节一个模块，文件末尾导出 `FIGURES = {注册名: 函数}` 和 `INPUTS = [...]`；注册名以节名开头（`results_km`）。每个函数返回 `(figure, stats)`，上屏的数字都要能在 `stats` 里找到。需要 matplotlib、numpy、pandas、lifelines。

## 构建

```bash
NODE_PATH=<node_modules> node $E/js/build.js .                     # output/<name>_wip.pptx + .pages.json + .pdf
NODE_PATH=<node_modules> node $E/js/build.js . --only sKm --out /tmp/x.pptx --png   # 只出一页，看 /tmp/x_png/
NODE_PATH=<node_modules> node $E/js/build.js . --release           # output/<name>_v<N>.pptx，不覆盖旧版本
NODE_PATH=<node_modules> node $E/js/build.js . --list              # 页序，不构建
```

PDF 需要 LibreOffice，`--png` 需要 Poppler；没有时构建只打警告。supplementary 一节在 pptx 里隐藏，PDF 里照出。部分构建（`--only`）的页脚写整套 deck 里的页码，别的页文件有问题时只打警告。

## 换主题

从模板 pptx 生成主题，把 `deck.config.js` 的 `theme` 指过去，再按新颜色渲图标：

```bash
python3 $E/tools/theme_from_pptx.py <模板>.pptx --out theme_<名字>   # 然后改成 theme: "theme_<名字>"
python3 $E/tools/theme_icons.py .
```

`theme_from_pptx.py` 从模板读出颜色、字体、标题框和 logo，并列出哪些字段沿用了 neutral 主题；`color.accent` 要人工核对，因为模板的 accent1 常常不是品牌色。页文件、讲稿和大纲都不用改；图的尺寸、dpi、画图字体或画图颜色变了时用 `plot.py .` 重画，再构建。

## 检查

```bash
python3 $E/tools/pages.py . --check               # {{key}} 页引用、手写页号、过期的生成块
python3 $E/tools/pages.py . --table --write       # 构建之后刷新 outline/README.md 里的生成块
python3 $E/tools/layout_check.py .                # 标题或文字被图遮住、文字压文字
```

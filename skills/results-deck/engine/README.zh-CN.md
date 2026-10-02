[English](README.md) | **简体中文**

# results-deck engine

engine 把一个 deck 目录构建成 16:9 PPTX，同时写出 PDF、页表（`pages.json`）和 PNG 预览。deck 目录里是一页一个的页文件、按上屏尺寸画好的图、讲稿、大纲和主题。每页是自己的文件、每个图模块只有一个负责人，所以几个 agent 可以并行改同一份 deck；风格都在主题目录里，换模板就是换主题。

接口约定（deck 结构、页文件、主题字段、文件格式、命令行参数、退出码、谁管哪些文件）见 [SPEC.zh-CN.md](SPEC.zh-CN.md)。每个工具的命令行见 [tools/README.zh-CN.md](tools/README.zh-CN.md)。

## 快速开始

`E` 指 `<research-skills>/skills/results-deck/engine`，命令都在 deck 目录里跑。

```bash
# 1. 复制模板，再删掉复制过来的构建产物（git 忽略，随时可以重建）
cp -r $E/template <项目>/presentation/my_deck && cd <项目>/presentation/my_deck
rm -rf output/*.pptx output/*.pdf output/*_png

# 2. 用 plotting/ 包画图：figures/<名>.png + figures/run_meta/<名>.json
python3 $E/tools/plot.py . --only results_km          # 一张图；不带 --only 是全部图

# 3. 整套构建：output/<name>_wip.pptx + .pages.json + .pdf
NODE_PATH=<node_modules> node $E/js/build.js .

# 4. 不等整套构建，自查自己的页，然后看 /tmp/x_png/*.png
NODE_PATH=<node_modules> node $E/js/build.js . --only sKm,sForest --out /tmp/x.pptx --png

# 5. 检查页引用和版面
python3 $E/tools/pages.py . --check
python3 $E/tools/layout_check.py .

# 6. 换主题：从模板 PPTX 生成主题，把 deck.config.js 的 `theme` 指过去，再按新颜色渲图标
python3 $E/tools/theme_from_pptx.py <模板>.pptx --out theme_<名字>
python3 $E/tools/theme_icons.py .
```

第 1 步之后，在 `deck.config.js` 里改 `name`、`title`、`refs`、`sections`，再替换页、讲稿、大纲和图，详见 [template/README.zh-CN.md](template/README.zh-CN.md)。第 6 步之后看主题工具打印的清单（强调色要人工核对）；图的尺寸、dpi、画图字体或画图颜色变了时重画，再构建（[SPEC.zh-CN.md](SPEC.zh-CN.md) §5.3）。

依赖：Node.js 和 `pptxgenjs`（从 `NODE_PATH`、`<deck>/node_modules` 或 `<research-skills>/node_modules` 找），Python 3.10+。可选：出 PDF 要 LibreOffice；PNG 预览和 `layout_check.py` 要 Poppler（`pdftoppm`、`pdftotext`）；`plot.py` 要 matplotlib（模板的图另需 numpy、pandas、lifelines）；`theme_icons.py` 和只有 SVG 的 logo 要 headless Chrome。没有 LibreOffice 或 Poppler 时构建只打警告，照样写出 PPTX。

## 组成

| 文件 | 作用 |
|---|---|
| [js/build.js](js/build.js) | 收集、排序 `slides/<key>.js`；构建 wip、release、`--out` 和部分构建（`--only` / `--sections`）的 PPTX，连同 `pages.json`、讲稿、隐藏的 supplementary 页、PDF 和 PNG；整套构建时持有构建锁 |
| [js/primitives.js](js/primitives.js) | 主题驱动的版式元素（`newSlide`、`figure`、`table`、`conclusion`、`source`、`cite`、`abbr`、`icon`、箭头 …）和主题的活视图 `T` / `G` |
| [themes/neutral/theme.json](themes/neutral/theme.json) | 默认主题，也是主题字段的完整清单 |
| [tools/plot.py](tools/plot.py) | 画 deck 的 `plotting/` 包里注册的图，每张图一份 run_meta |
| [tools/pages.py](tools/pages.py) | 检查、展开 `{{key}}` 页引用；重写大纲里的页数和页码表生成块 |
| [tools/pull_notes.py](tools/pull_notes.py) | 把讲者改过的 PPTX 里的讲稿同步回 `notes/<key>.md` |
| [tools/move.py](tools/move.py) | 挪页：只改这一页的 `section` / `order`；`--respace` 重排一节 |
| [tools/theme_from_pptx.py](tools/theme_from_pptx.py) | 从模板 PPTX 生成主题目录（theme.json + 图片） |
| [tools/theme_icons.py](tools/theme_icons.py) | 按主题颜色渲染 deck 用到的图标 |
| [tools/svg_raster.py](tools/svg_raster.py) | 用 headless Chrome 把 SVG（可改色）渲成透明 PNG |
| [tools/layout_check.py](tools/layout_check.py) | 在构建出的 PDF 里找被图遮住或压在别的文字上的标题和文字 |
| [template/](template/README.zh-CN.md) | 一套完整的五页 deck，复制过去作为新 deck 的起点 |

## 语言约定

所有生成的产出物都用英文：页上文字、图中文字、表格、Source 行、speaker notes、PPTX、PDF 和预览图。仓库文档维护为成对的 `X.md` 和 `X.zh-CN.md`，GitHub 默认显示英文版。

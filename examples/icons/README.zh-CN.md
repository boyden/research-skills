[English](README.md) | **简体中文**

# icons

科研 slide 用的开放许可图标库，覆盖七个主题：AI / 机器学习、LLM、VLM / 多模态、AI agent、计算病理、空间组学、通用科研 / 数据。共 104 个图标，来自 4 个图标库，每个都记了许可、作者（Bioicons）和原始链接。总览图：[icon_sheet.png](icon_sheet.png)。总览图里也画了 7 个 CC BY 图标，署名如下（详见下文「Bioicons」一节）：`attention-mechanism`（Noelia Ferruz）、`expression-heatmap`（Chenxin Li）、`volcano-plot`（Lucas Diedrich）、`confocal-microscope`（DBCLS (TogoTV)），均 CC BY 4.0；`glass-slide`、`carcinoma`、`epithelium`（Servier Medical Art），CC BY 3.0。

| 来源 | 数量 | 许可 | 是否要求署名 |
|:--|:-:|:-:|:-:|
| Health Icons | 14 | CC0-1.0 | 否 |
| Lucide | 41 | ISC（`code` 一个来自 Feather，MIT） | 否（再分发源文件时保留 LICENSE） |
| Tabler Icons | 32 | MIT | 否（再分发源文件时保留 LICENSE） |
| Bioicons | 17 | 10 个 CC0-1.0，4 个 CC-BY-4.0，3 个 CC-BY-3.0 | CC BY 的 7 个要求署名 |

## 目录结构

```
icons/
  <source>/<name>.svg          上游原文件，未修改（只改了文件名）
  <source>/LICENSE.txt         该来源的许可原文
  png/<source>/<name>.png      512 x 512 透明底，灰 #595959（slide 正文色）
  png/<source>/<name>_accent.png   同上，强调色 #A51C30；只有单色图标有
  manifest.csv                 主题、名称、上游路径、许可、作者、用途
  render_pngs.py               SVG -> PNG
  make_icon_sheet.py           生成 icon_sheet.png
```

## 在 slide 里用

LibreOffice < 7.4 画不出 pptx 里嵌的 SVG，所以 slide 一律用 PNG。页文件用 engine [primitives.js](../../skills/results-deck/engine/js/primitives.js) 的 `P.icon()`：

```js
P.icon(slide, "lucide/brain-circuit", x, y, size, "grey");   // png/lucide/brain-circuit.png
P.icon(slide, "tabler/robot", x, y, size, "accent");         // png/tabler/robot_accent.png
P.icon(slide, "bioicons/glass-slide", x, y, size);           // 多色图标只有 "grey" 这一个变体（原色）
```

- `name` 是 `<source>/<name>`，`size` 是正方形边长（英寸）。
- `P.icon()` 先找按 deck 主题配色渲染的副本（`<theme>/icons/png/…`，由 engine 的 `tools/theme_icons.py <deck>` 生成），找不到再用这里的 PNG（`deck.config.js` 的 `iconDir`；`null` 即本目录）。
- Bioicons 多为多色插画，按原色渲染，**没有 `_accent` 版本**；对它们传 `"accent"` 会找不到文件。表里「颜色」一列写了哪些有 accent。
- 线条风格（Lucide / Tabler）和填充风格（Health Icons）混在同一张 slide 上会显得不统一；一张 slide 内尽量用同一个来源。

## 重新渲染

```bash
cd research-skills
python3 examples/icons/render_pngs.py            # 只渲染缺的 PNG
python3 examples/icons/render_pngs.py --force    # 全部重渲染
python3 examples/icons/render_pngs.py --only lucide/bot tabler/robot
python3 examples/icons/make_icon_sheet.py        # 需要 matplotlib
```

- `render_pngs.py` 只用 Python 标准库加 headless Chrome（`google-chrome --headless=new`）。原 SVG 不动：脚本把 `currentColor`（或单一的显式颜色）换成目标色、把根元素 width/height 改成 512（viewBox 不变，线宽随之等比缩放），写到临时目录再截图。
- headless Chrome 的可视区域比 `--window-size` 矮约 87 px，直接截 512 x 512 会把图标底部截掉；脚本因此把窗口开高 200 px，再把 PNG 裁回顶部 512 行。
- 加新图标：把 SVG 下载到 `<source>/<name>.svg`，在 `manifest.csv` 加一行，再跑上面两条命令。含嵌入位图（`<image>`）的 SVG 不要收（不是矢量，也没法改色）。

## 各来源的许可与署名

### Health Icons（`healthicons/`）

- https://healthicons.org ，https://github.com/resolvetosavelives/healthicons ，路径 `public/icons/svg/outline/<category>/<name>.svg`。
- 图标是 CC0："To the extent possible under law, Health Icons has waived all copyright and related or neighboring rights to icons available at Health Icons." 不需要署名。网站 / 仓库代码另为 MIT。
- 上游文件名里的下划线在这里改成连字符（如 `microscope-with_specimen` → `microscope-with-specimen`）。

### Lucide（`lucide/`）

- https://github.com/lucide-icons/lucide ，路径 `icons/<name>.svg`。ISC 许可；少数源自 Feather 的图标为 MIT（本库里只有 `code`）。许可原文见 [lucide/LICENSE.txt](lucide/LICENSE.txt)。
- 在 slide 上使用不需要署名；再分发 SVG 时保留 LICENSE.txt。

### Tabler Icons（`tabler/`）

- https://github.com/tabler/tabler-icons ，路径 `icons/outline/<name>.svg`。MIT 许可，原文见 [tabler/LICENSE.txt](tabler/LICENSE.txt)。
- 在 slide 上使用不需要署名；再分发 SVG 时保留 LICENSE.txt。

### Bioicons（`bioicons/`）

- https://bioicons.com ，https://github.com/duerrsimon/bioicons ，路径 `static/icons/<license>/<category>/<author>/<name>.svg`，许可和作者就写在路径里。逐个图标的对照见 [bioicons/LICENSE.txt](bioicons/LICENSE.txt)。仓库的 MIT LICENSE 只管网站代码，不管图标。
- **CC BY 图标必须署名**：在用到它的 slide 上，或在 deck 的 credits 页写明图标名、作者、许可和链接。上游给的格式：

  > glassslide-top icon by Servier https://smart.servier.com/ is licensed under CC-BY 3.0 Unported https://creativecommons.org/licenses/by/3.0/

  需要署名的 7 个：

  | 图标 | 作者 | 许可 |
  |:--|:-:|:-:|
  | `bioicons/attention-mechanism` | Noelia Ferruz | CC BY 4.0 |
  | `bioicons/expression-heatmap` | Chenxin Li | CC BY 4.0 |
  | `bioicons/volcano-plot` | Lucas Diedrich | CC BY 4.0 |
  | `bioicons/confocal-microscope` | DBCLS (TogoTV) | CC BY 4.0 |
  | `bioicons/glass-slide` | Servier Medical Art | CC BY 3.0 |
  | `bioicons/carcinoma` | Servier Medical Art | CC BY 3.0 |
  | `bioicons/epithelium` | Servier Medical Art | CC BY 3.0 |

- 没有收 CC BY-SA 的图标。
- 上游有两个候选因为内嵌位图被剔除：`cc-0/Computer_hardware/Simon_Dürr/gpu.svg`（约 730 KB，大半是嵌入 PNG）和 `cc-by-4.0/Blood_Immunology/El-Jayawant/cancer_cell.svg`（整张是嵌入 PNG）。

## 图标清单（按主题）

「颜色」：`grey + accent` 表示有两种 PNG；`原色，无 accent` 表示多色插画，只有一张按原色渲染的 PNG。

### AI / machine learning（14）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `lucide/brain-circuit` | AI model | lucide | ISC | — | grey + accent | [brain-circuit.svg](https://github.com/lucide-icons/lucide/blob/main/icons/brain-circuit.svg) |
| `lucide/brain-cog` | training | lucide | ISC | — | grey + accent | [brain-cog.svg](https://github.com/lucide-icons/lucide/blob/main/icons/brain-cog.svg) |
| `lucide/network` | network / graph | lucide | ISC | — | grey + accent | [network.svg](https://github.com/lucide-icons/lucide/blob/main/icons/network.svg) |
| `lucide/cpu` | compute | lucide | ISC | — | grey + accent | [cpu.svg](https://github.com/lucide-icons/lucide/blob/main/icons/cpu.svg) |
| `lucide/gpu` | GPU | lucide | ISC | — | grey + accent | [gpu.svg](https://github.com/lucide-icons/lucide/blob/main/icons/gpu.svg) |
| `lucide/layers` | model layers | lucide | ISC | — | grey + accent | [layers.svg](https://github.com/lucide-icons/lucide/blob/main/icons/layers.svg) |
| `lucide/sparkles` | AI / generative | lucide | ISC | — | grey + accent | [sparkles.svg](https://github.com/lucide-icons/lucide/blob/main/icons/sparkles.svg) |
| `tabler/brain` | AI / intelligence | tabler | MIT | — | grey + accent | [brain.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/brain.svg) |
| `tabler/model-ai` | AI model | tabler | MIT | — | grey + accent | [model-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/model-ai.svg) |
| `tabler/chart-scatter-3d` | embeddings | tabler | MIT | — | grey + accent | [chart-scatter-3d.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/chart-scatter-3d.svg) |
| `tabler/cube-spark` | foundation model | tabler | MIT | — | grey + accent | [cube-spark.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/cube-spark.svg) |
| `bioicons/neural-network` | neural network | bioicons | CC0-1.0 | Simon Dürr | 原色，无 accent | [neural-network-1.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Machine_Learning/Simon_D%C3%BCrr/neural-network-1.svg) |
| `bioicons/attention-mechanism` | attention / transformer | bioicons | CC-BY-4.0 | Noelia Ferruz | 原色，无 accent | [Attention-mechanism.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-4.0/Machine_Learning/Noelia_Ferruz/Attention-mechanism.svg) |
| `bioicons/autoencoder` | encoder-decoder | bioicons | CC0-1.0 | Simon Dürr | 原色，无 accent | [autoencoder.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Machine_Learning/Simon_D%C3%BCrr/autoencoder.svg) |

### LLM（13）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `lucide/message-square-text` | chat message | lucide | ISC | — | grey + accent | [message-square-text.svg](https://github.com/lucide-icons/lucide/blob/main/icons/message-square-text.svg) |
| `lucide/messages-square` | conversation | lucide | ISC | — | grey + accent | [messages-square.svg](https://github.com/lucide-icons/lucide/blob/main/icons/messages-square.svg) |
| `lucide/bot-message-square` | chatbot | lucide | ISC | — | grey + accent | [bot-message-square.svg](https://github.com/lucide-icons/lucide/blob/main/icons/bot-message-square.svg) |
| `lucide/text-cursor-input` | prompt input | lucide | ISC | — | grey + accent | [text-cursor-input.svg](https://github.com/lucide-icons/lucide/blob/main/icons/text-cursor-input.svg) |
| `lucide/whole-word` | tokens / words | lucide | ISC | — | grey + accent | [whole-word.svg](https://github.com/lucide-icons/lucide/blob/main/icons/whole-word.svg) |
| `lucide/languages` | language | lucide | ISC | — | grey + accent | [languages.svg](https://github.com/lucide-icons/lucide/blob/main/icons/languages.svg) |
| `lucide/pencil-sparkles` | text generation | lucide | ISC | — | grey + accent | [pencil-sparkles.svg](https://github.com/lucide-icons/lucide/blob/main/icons/pencil-sparkles.svg) |
| `lucide/book-open-text` | text corpus | lucide | ISC | — | grey + accent | [book-open-text.svg](https://github.com/lucide-icons/lucide/blob/main/icons/book-open-text.svg) |
| `tabler/message-chatbot` | chatbot | tabler | MIT | — | grey + accent | [message-chatbot.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/message-chatbot.svg) |
| `tabler/prompt` | prompt | tabler | MIT | — | grey + accent | [prompt.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/prompt.svg) |
| `tabler/message-sparkle` | generated reply | tabler | MIT | — | grey + accent | [message-sparkle.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/message-sparkle.svg) |
| `tabler/file-text-ai` | generated document | tabler | MIT | — | grey + accent | [file-text-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/file-text-ai.svg) |
| `tabler/letter-case` | tokens / text | tabler | MIT | — | grey + accent | [letter-case.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/letter-case.svg) |

### VLM / multimodal（11）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `lucide/scan-eye` | vision | lucide | ISC | — | grey + accent | [scan-eye.svg](https://github.com/lucide-icons/lucide/blob/main/icons/scan-eye.svg) |
| `lucide/scan-text` | read text in image | lucide | ISC | — | grey + accent | [scan-text.svg](https://github.com/lucide-icons/lucide/blob/main/icons/scan-text.svg) |
| `lucide/image` | image input | lucide | ISC | — | grey + accent | [image.svg](https://github.com/lucide-icons/lucide/blob/main/icons/image.svg) |
| `lucide/images` | image set | lucide | ISC | — | grey + accent | [images.svg](https://github.com/lucide-icons/lucide/blob/main/icons/images.svg) |
| `lucide/eye` | vision | lucide | ISC | — | grey + accent | [eye.svg](https://github.com/lucide-icons/lucide/blob/main/icons/eye.svg) |
| `tabler/photo-ai` | image + AI | tabler | MIT | — | grey + accent | [photo-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/photo-ai.svg) |
| `tabler/camera-ai` | vision model | tabler | MIT | — | grey + accent | [camera-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/camera-ai.svg) |
| `tabler/eye-spark` | vision model | tabler | MIT | — | grey + accent | [eye-spark.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/eye-spark.svg) |
| `tabler/photo-scan` | image understanding | tabler | MIT | — | grey + accent | [photo-scan.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/photo-scan.svg) |
| `tabler/subtitles-ai` | captioning | tabler | MIT | — | grey + accent | [subtitles-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/subtitles-ai.svg) |
| `tabler/text-scan-ai` | image to text | tabler | MIT | — | grey + accent | [text-scan-ai.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/text-scan-ai.svg) |

### AI agents（15）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `lucide/bot` | agent / bot | lucide | ISC | — | grey + accent | [bot.svg](https://github.com/lucide-icons/lucide/blob/main/icons/bot.svg) |
| `lucide/workflow` | workflow | lucide | ISC | — | grey + accent | [workflow.svg](https://github.com/lucide-icons/lucide/blob/main/icons/workflow.svg) |
| `lucide/wrench` | tool use | lucide | ISC | — | grey + accent | [wrench.svg](https://github.com/lucide-icons/lucide/blob/main/icons/wrench.svg) |
| `lucide/toolbox` | tool set | lucide | ISC | — | grey + accent | [toolbox.svg](https://github.com/lucide-icons/lucide/blob/main/icons/toolbox.svg) |
| `lucide/list-checks` | planning / task list | lucide | ISC | — | grey + accent | [list-checks.svg](https://github.com/lucide-icons/lucide/blob/main/icons/list-checks.svg) |
| `lucide/route` | plan / trajectory | lucide | ISC | — | grey + accent | [route.svg](https://github.com/lucide-icons/lucide/blob/main/icons/route.svg) |
| `lucide/repeat` | agent loop | lucide | ISC | — | grey + accent | [repeat.svg](https://github.com/lucide-icons/lucide/blob/main/icons/repeat.svg) |
| `tabler/robot` | robot | tabler | MIT | — | grey + accent | [robot.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/robot.svg) |
| `tabler/robot-face` | robot | tabler | MIT | — | grey + accent | [robot-face.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/robot-face.svg) |
| `tabler/ai-agent` | AI agent | tabler | MIT | — | grey + accent | [ai-agent.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/ai-agent.svg) |
| `tabler/ai-agents` | multi-agent | tabler | MIT | — | grey + accent | [ai-agents.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/ai-agents.svg) |
| `tabler/automation` | automation | tabler | MIT | — | grey + accent | [automation.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/automation.svg) |
| `tabler/subtask` | task decomposition | tabler | MIT | — | grey + accent | [subtask.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/subtask.svg) |
| `tabler/api` | API / tool call | tabler | MIT | — | grey + accent | [api.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/api.svg) |
| `bioicons/automation` | automation | bioicons | CC0-1.0 | Simon Dürr | 原色，无 accent | [automation.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Machine_Learning/Simon_D%C3%BCrr/automation.svg) |

Tabler 的 `ai-agent` / `ai-agents` 画的是点阵，单独放不一定能读成「agent」，最好配文字标签。

### Computational pathology（16）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `healthicons/microscope` | microscope | healthicons | CC0-1.0 | — | grey + accent | [microscope.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/devices/microscope.svg) |
| `healthicons/biopsy` | biopsy | healthicons | CC0-1.0 | — | grey + accent | [biopsy.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/diagnostics/biopsy.svg) |
| `healthicons/tissue` | tissue | healthicons | CC0-1.0 | — | grey + accent | [tissue.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/body/tissue.svg) |
| `healthicons/cell-nuclei` | cells / nuclei | healthicons | CC0-1.0 | — | grey + accent | [cell-nuclei.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/body/cell-nuclei.svg) |
| `healthicons/microscope-with-specimen` | microscope with slide | healthicons | CC0-1.0 | — | grey + accent | [microscope-with_specimen.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/devices/microscope-with_specimen.svg) |
| `healthicons/cancerous-cell-nuclei` | tumour nuclei | healthicons | CC0-1.0 | — | grey + accent | [cancerous-cell_nuclei.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/conditions/cancerous-cell_nuclei.svg) |
| `healthicons/medical-sample` | specimen | healthicons | CC0-1.0 | — | grey + accent | [medical-sample.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/devices/medical-sample.svg) |
| `lucide/microscope` | microscope | lucide | ISC | — | grey + accent | [microscope.svg](https://github.com/lucide-icons/lucide/blob/main/icons/microscope.svg) |
| `lucide/scan` | scanner / field of view | lucide | ISC | — | grey + accent | [scan.svg](https://github.com/lucide-icons/lucide/blob/main/icons/scan.svg) |
| `lucide/grid-3x3` | tiles / patches | lucide | ISC | — | grey + accent | [grid-3x3.svg](https://github.com/lucide-icons/lucide/blob/main/icons/grid-3x3.svg) |
| `tabler/grid-scan` | tiling a slide | tabler | MIT | — | grey + accent | [grid-scan.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/grid-scan.svg) |
| `tabler/lasso-polygon` | segmentation / annotation | tabler | MIT | — | grey + accent | [lasso-polygon.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/lasso-polygon.svg) |
| `bioicons/microscope-cartoon` | microscope | bioicons | CC0-1.0 | Derek Croote | 原色，无 accent | [microscope-cartoon.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Lab_apparatus/Derek-Croote/microscope-cartoon.svg) |
| `bioicons/glass-slide` | glass slide | bioicons | CC-BY-3.0 | Servier | 原色，无 accent | [glassslide-top.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-3.0/Lab_apparatus/Servier/glassslide-top.svg) |
| `bioicons/carcinoma` | tumour cells | bioicons | CC-BY-3.0 | Servier | 原色，无 accent | [carcinoma.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-3.0/Oncology/Servier/carcinoma.svg) |
| `bioicons/epithelium` | epithelium | bioicons | CC-BY-3.0 | Servier | 原色，无 accent | [epithelium-stratified-columnar.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-3.0/Tissues/Servier/epithelium-stratified-columnar.svg) |

`bioicons/microscope-cartoon` 是黑白两色，按原色渲染（黑色，不是 #595959）。开放图标库里没有现成的「全切片图像 / WSI」图标：可以用 `bioicons/glass-slide`，或者用 `tabler/grid-scan`、`lucide/grid-3x3` 表示切 tile。

### Spatial omics（16）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `healthicons/dna` | DNA | healthicons | CC0-1.0 | — | grey + accent | [dna.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/body/dna.svg) |
| `lucide/dna` | DNA / genes | lucide | ISC | — | grey + accent | [dna.svg](https://github.com/lucide-icons/lucide/blob/main/icons/dna.svg) |
| `tabler/dna-2` | DNA / RNA | tabler | MIT | — | grey + accent | [dna-2.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/dna-2.svg) |
| `lucide/chart-network` | cell graph | lucide | ISC | — | grey + accent | [chart-network.svg](https://github.com/lucide-icons/lucide/blob/main/icons/chart-network.svg) |
| `tabler/topology-star-ring` | cell neighbourhood | tabler | MIT | — | grey + accent | [topology-star-ring.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/topology-star-ring.svg) |
| `tabler/chart-grid-dots` | spatial map | tabler | MIT | — | grey + accent | [chart-grid-dots.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/chart-grid-dots.svg) |
| `tabler/grid-dots` | spot array | tabler | MIT | — | grey + accent | [grid-dots.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/grid-dots.svg) |
| `tabler/hexagons` | hexagonal spots / bins | tabler | MIT | — | grey + accent | [hexagons.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/hexagons.svg) |
| `lucide/map-pinned` | spatial location | lucide | ISC | — | grey + accent | [map-pinned.svg](https://github.com/lucide-icons/lucide/blob/main/icons/map-pinned.svg) |
| `tabler/stack-2` | multiplex channels | tabler | MIT | — | grey + accent | [stack-2.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/stack-2.svg) |
| `bioicons/single-cell-umap` | single-cell UMAP | bioicons | CC0-1.0 | James Lloyd | 原色，无 accent | [SingleCell_Clustering_DataReduction_UMAP.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Scientific_graphs/James-Lloyd/SingleCell_Clustering_DataReduction_UMAP.svg) |
| `bioicons/expression-heatmap` | gene expression heatmap | bioicons | CC-BY-4.0 | Chenxin Li | 原色，无 accent | [heatmap.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-4.0/Scientific_graphs/ChenxinLi/heatmap.svg) |
| `bioicons/volcano-plot` | differential expression | bioicons | CC-BY-4.0 | Lucas Diedrich | 原色，无 accent | [differential_gene_expression.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-4.0/Chemo-_and_Bioinformatics/Lucas-Diedrich/differential_gene_expression.svg) |
| `bioicons/cell-group` | cell cluster | bioicons | CC0-1.0 | JhonnyXC | 原色，无 accent | [cell_group.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Cell_types/JhonnyXC/cell_group.svg) |
| `bioicons/single-cell-droplet` | single-cell droplets | bioicons | CC0-1.0 | Xi Chen | 原色，无 accent | [singlecell_droplet_overloading.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Lab_apparatus/Xi-Chen/singlecell_droplet_overloading.svg) |
| `bioicons/confocal-microscope` | imaging system | bioicons | CC-BY-4.0 | DBCLS | 原色，无 accent | [confocal-scanning-laser-microscope-CSLM.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-4.0/Lab_apparatus/DBCLS/confocal-scanning-laser-microscope-CSLM.svg) |

`bioicons/expression-heatmap` 和 `bioicons/volcano-plot` 自带小字（High / Low、坐标轴），缩到 1 英寸以下会看不清。

### Generic science / data（19）

| 图标 | 用途 | 来源 | 许可 | 作者 | 颜色 | 原始链接 |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|
| `healthicons/regular-patient` | patient | healthicons | CC0-1.0 | — | grey + accent | [regular-patient.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/people/regular-patient.svg) |
| `healthicons/chart-line` | line chart | healthicons | CC0-1.0 | — | grey + accent | [chart-line.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/graphs/chart-line.svg) |
| `healthicons/laptop` | computer | healthicons | CC0-1.0 | — | grey + accent | [laptop.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/objects/laptop.svg) |
| `healthicons/people` | cohort | healthicons | CC0-1.0 | — | grey + accent | [people.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/people/people.svg) |
| `healthicons/database` | database | healthicons | CC0-1.0 | — | grey + accent | [database.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/symbols/database.svg) |
| `healthicons/hospital` | hospital / site | healthicons | CC0-1.0 | — | grey + accent | [hospital.svg](https://github.com/resolvetosavelives/healthicons/blob/main/public/icons/svg/outline/places/hospital.svg) |
| `lucide/users` | cohort | lucide | ISC | — | grey + accent | [users.svg](https://github.com/lucide-icons/lucide/blob/main/icons/users.svg) |
| `lucide/chart-scatter` | scatter plot | lucide | ISC | — | grey + accent | [chart-scatter.svg](https://github.com/lucide-icons/lucide/blob/main/icons/chart-scatter.svg) |
| `lucide/chart-column` | bar chart | lucide | ISC | — | grey + accent | [chart-column.svg](https://github.com/lucide-icons/lucide/blob/main/icons/chart-column.svg) |
| `tabler/chart-histogram` | distribution | tabler | MIT | — | grey + accent | [chart-histogram.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/chart-histogram.svg) |
| `lucide/sigma` | statistics | lucide | ISC | — | grey + accent | [sigma.svg](https://github.com/lucide-icons/lucide/blob/main/icons/sigma.svg) |
| `lucide/trending-down` | decline / survival | lucide | ISC | — | grey + accent | [trending-down.svg](https://github.com/lucide-icons/lucide/blob/main/icons/trending-down.svg) |
| `lucide/cloud` | cloud | lucide | ISC | — | grey + accent | [cloud.svg](https://github.com/lucide-icons/lucide/blob/main/icons/cloud.svg) |
| `lucide/code` | code | lucide | MIT (Feather) | — | grey + accent | [code.svg](https://github.com/lucide-icons/lucide/blob/main/icons/code.svg) |
| `lucide/clipboard-list` | clinical data / protocol | lucide | ISC | — | grey + accent | [clipboard-list.svg](https://github.com/lucide-icons/lucide/blob/main/icons/clipboard-list.svg) |
| `tabler/report-medical` | medical record | tabler | MIT | — | grey + accent | [report-medical.svg](https://github.com/tabler/tabler-icons/blob/main/icons/outline/report-medical.svg) |
| `bioicons/patient` | patient | bioicons | CC0-1.0 | Marcel Tisch | 原色，无 accent | [patient.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Human_physiology/Marcel_Tisch/patient.svg) |
| `bioicons/supercomputer` | compute cluster | bioicons | CC0-1.0 | Simon Dürr | 原色，无 accent | [supercomputer.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Computer_hardware/Simon_D%C3%BCrr/supercomputer.svg) |
| `bioicons/pipeline` | processing pipeline | bioicons | CC0-1.0 | Simon Dürr | 原色，无 accent | [pipeline.svg](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Machine_Learning/Simon_D%C3%BCrr/pipeline.svg) |

没有找到开放许可的 Kaplan–Meier 阶梯曲线图标；`lucide/trending-down` 只能当「下降」的示意。真要画生存曲线，用 `examples/figures/` 里的 KM 示例图。

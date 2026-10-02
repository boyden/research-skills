[English](checks.md) | **简体中文**

# 验证流程与踩过的坑

每次改页后至少做 §1–§3（自查：局部构建自己的页、看 PNG、跑碰撞检查）；挪页、增删页、改标题后加做 §7 的「页引用」；讲者改过讲稿后做 §7 的「讲稿是数据」。
默认只验证自己改的那几页，整套 deck 的构建和逐页检查由集成者做（§8）。
下文的 `<engine>` 指 `skills/results-deck/engine`，`<deck>` 指 deck 目录，`$SCRATCH` 指自己的临时目录。

## 1. 语法和结构

```bash
node --check <deck>/slides/<key>.js                         # 每个改过的页文件的语法
node <engine>/js/build.js <deck> --only <key>[,<key>] --out "$SCRATCH/x.pptx" --png
python <pptx skill 目录>/scripts/office/validate.py "$SCRATCH/x.pptx"   # 要求 All validations PASSED
python3 <engine>/tools/layout_check.py <deck> --pptx "$SCRATCH/x.pptx" --pdf "$SCRATCH/x.pdf" \
        --pages-json "$SCRATCH/x.pages.json" --png-dir "$SCRATCH/flagged"
```

- 构建先校验全部页文件（key、`section`、`order`、`build`；同一节两页 `order` 相同），有问题时一次列出全部问题（退出码 2）。要按整节构建时把 `--only` 换成 `--sections <节>[,<节>]`。
- 部分构建（`--only` / `--sections`）必须给 `--out`，从不写 wip 或 release，也不拿锁；页脚写整套 deck 里的页码。`--png` 另出 `x.pdf` 和 `x_png/<页码>-<key>.png`；`x.pages.json` 总是写在 `x.pptx` 旁边。
- 结构检查用 Anthropic pptx skill 自带的 `validate.py`（装了才有；没装就跳过并在汇报里写明没做）。
  LibreOffice 能打开不等于 PowerPoint 能打开，所以渲染通过不能代替这一步。
- 构建先写临时文件，成功后才改名；中途失败（如缺图）时上一版输出原样保留。

## 2. 渲染

`--png` 用独立的 LibreOffice profile 把 pptx 转成 PDF，再用 `pdftoppm -r 60` 把每页渲到 `<out 的主名>_png/<页码>-<key>.png`。手动渲染一份 pptx（比如讲者改过的那份）时用：

```bash
soffice -env:UserInstallation=file://$SCRATCH/lo_profile_$$ --headless \
        --convert-to pdf --outdir "$SCRATCH" "$SCRATCH/x.pptx"
pdftoppm -r 60 -png "$SCRATCH/x.pdf" "$SCRATCH/preview/page"
```

- **每次转换用独立的 LibreOffice profile**（`-env:UserInstallation=file://<唯一目录>`）：几个转换同时跑时共用默认 profile 会互相锁住，
  表现为转换静默失败或卡住。build.js 已经这样做；`$DECK_SOFFICE` 可以指定 `soffice` 的位置。
- 预览写在自己的临时目录，不写 `output/`。60 dpi（和 `--png`、examples/slides/render.sh 一致）够看版面；看小字或细线时对单页用 100–150 dpi。
- 转换失败时只警告，不让构建失败：pptx 照常保留，旧 PDF 不动。

## 3. 逐页看 PNG

只看改过的页，每页过一遍：

- [ ] 文字溢出或被截断（结论框超过 3 行、表格最后一行出框、bullet 掉出页面）
- [ ] 元素重叠（标题折行压到图、结论框压到来源行、图标偏离自己那一行）
- [ ] 图被拉伸、压扁或缩放（对比图的像素尺寸 / dpi 与放置尺寸）
- [ ] 页脚缺失（来源行、页码）；⚠️ 页有 DRAFT 标签，✅ 页没有
- [ ] 出现非英文文字（图里、页上、表格里）
- [ ] 数字和大纲的 Message、来源表一致

发现问题就改了重出，再看一遍；图本身的问题回画图代码改，再用 `plot.py <deck> --only <图名>` 重画（见 SKILL.md「[什么时候停下来问](../SKILL.zh-CN.md#什么时候停下来问)」）。

## 4. 字体与 z 序：预览和 PowerPoint 不一样的地方

- **模板字体要装进系统**，否则 LibreOffice 用更宽的替代字体，长标题折成两行、结论句多一行，预览和 PowerPoint 对不上。
  不需要 root：把字体文件放进用户字体目录 `~/.local/share/fonts/<字体名>/`，再 `fc-cache -f ~/.local/share/fonts`。
  检查主题字体在不在（`fc-list | grep <字体名>`）：`theme_from_pptx.py` 会对没装的模板字体打警告，build.js 只在缺 Arial（或 Liberation Sans）时警告。
- **商业字体文件不提交、不再分发**：多数「可装在自己设备上使用」的许可不允许放进仓库。在文档里写清从哪里下载、装到哪里。
- 装不了字体时：预览里放得下，PowerPoint 里一定放得下（替代字体更宽），但换行位置只是近似。
- **主图放到 z 序最底**：图在标题之后加入，z 序就在标题之上，标题一折行第二行就被图盖住、在 PNG 里看不见。
  `P.figure()` 加完图后立刻置底（同页多张图保持彼此顺序）；本来就该盖在形状上的图标、小图不动。

## 5. 自动碰撞检查（`layout_check.py`）

几十页逐页肉眼看容易漏，`<engine>/tools/layout_check.py` 先筛一遍（默认读 wip 的 pptx、PDF 和 pages.json；部分构建用 `--pptx` / `--pdf` / `--pages-json` 指定，只查几页用 `--pages`）：

- 文字框：`pdftotext -bbox-layout <pdf>` 给出每一行渲染后的框（pt）。
- 图片框和 z 序：从 pptx 的 slide XML 读每个 `p:pic` 的位置（EMU → pt）和它在 `spTree` 里的次序；
  PDF 里的一行文字按内容匹配回 pptx 的文本框，得到它的 z 序。
- 逐页报：标题行被 z 序更高的图盖住（hidden title）；标题和图相交但字在上面；标题折成 2 行以上及它到下一个元素的距离；
  其他文字行与图相交超过 3 pt（`--tol`）；两行文字框互相重叠。`--png-dir` 把有问题的页渲成低分辨率 PNG 供目测。
- **误报是预期的**：PNG 的白边或透明边、特意盖在图上的比例尺和标签、表格列里的图标都会被报成相交；
  PDF 的行框比字形高。**最终以 PNG 为准**，脚本只决定先看哪几页。

## 6. Supplementary 页隐藏，PDF 照出

- `deck.config.js` 的 `supplementary` 指定的那一节，页在 pptx 里设成隐藏（slide XML 的 `show="0"`），放映时跳过。
- LibreOffice 7.4 以前转 PDF 会**跳过隐藏页**，也没有导出隐藏页的选项。所以 build.js 转 PDF 时转的是一份去掉了 `show="0"` 的临时副本。
  pptx 保持隐藏，PDF 每页一张，页数与 `pages.json` 一致。
- 核对：PDF 页数 = `pages.json` 条数。

## 7. 页引用和讲稿

**页引用**（挪页、增删页、改标题之后）：

1. 改页文件：`move.py <deck> <key> --after <key>`（或 `--before <key>`、`--to <节>`）只改这一页的 `section` / `order`；改标题就改它的页文件；增删页就是增删 `slides/<key>.js`（连同 `notes/<key>.md`）。
2. 集成者整套构建（pptx + PDF + `pages.json`），再跑 `pages.py <deck> --table --write` 重写大纲里的生成块（页数、页码表）。
3. `pages.py <deck> --check`：不存在的 key、手写的 `P<数字>`、过期的生成块都要清零。
4. 挪页、改名、合并、删页记进 `outline/CHANGELOG.md`；章节文件只写当前状态。

**讲稿是数据**：

- 讲稿一页一个文件，存在 `notes/<key>.md`（UTF-8 纯文本，一行一个段落），构建时用它整段替换该页的 notes；没有文件的页保留页文件里 `slide.addNotes()` 的文字。
- 讲者在 PowerPoint 里改了讲稿后，**真相来源是讲者的 pptx**。`pull_notes.py <deck> [pptx]` 读 pptx 每页的备注，按页标题配 key：
  第一页是标题页；然后查别名表 `notes/_aliases.json`（重复的标题写成 `"<标题>"`、`"<标题>#2"` …）；再按标题在 `pages.json` 里唯一匹配。配不上、标题重复又没有别名、key 已被占用的页**不写**，
  列进 `notes/_unmatched.json`，加别名后重跑。先 `--dry-run` 看哪些 key 是 new、changed、unchanged，再由集成者跑 `--write`；它先把要改的文件备份到 `.backups/`，从不删文件。
- 只读回纯文字：加粗、字号不保留；段落和软换行都变成换行。
- pptxgenjs 把整段讲稿写成一个段落；build.js 按换行拆成多个 `a:p`，PowerPoint 里的段落才和 `notes/<key>.md` 的行一致。
- **挪页后查讲稿里的相对引用**：「the next slide」「the previous slide」「the supplementary slide '…'」「Next, I'll show …」挪页后会悄悄变错。
  `move.py` 把挪动页及其新旧邻页（页文件和讲稿）里的这类字样作为 WARNING 打印出来；逐条对照当前邻页（或被点名的页）的标题人读；关键词重叠只是分诊，泛词会把错的判成对的。
  工具只报告、不改措辞：讲稿是讲者的，要改就在 pptx 里改，再同步。
- 为版面从页上挪进讲稿的细节写成 `Note: …`，讲者能一眼看出哪些话页上没有。

## 8. wip、发布和并行改页

- **整套构建写 wip**（`<outDir>/<name>_wip.pptx`，连同 PDF 和 `pages.json`），每次覆盖；构建时拿 `<outDir>/.build.lock`（另一个整套构建在跑时退出码 3）；只由集成者跑。
- **发布**：`--release` 写 `<outDir>/<name>_v<N>.pptx`（+ PDF + `pages.json`），N = 现有最大版本号 + 1；文件名只带版本号不带日期；已发布的不覆盖、不删除。
- **并行改页**：每个人 / agent 管自己的页文件 `slides/<key>.js`、自己的 `notes/<key>.md`、自己的大纲块和画图模块，只把自己那几页构建到临时路径：
  `node <engine>/js/build.js <deck> --only <key>[,<key>] --out $SCRATCH/x.pptx --png`。这种构建拒绝写 wip、不拿锁，页脚写整套 deck 里的页码，不给 `--png` 或 `--pdf` 时不出 PDF。
- **只由集成者做、串行做的步骤**：整套构建、`--release`、`move.py --respace <节>`（把一整节重新编号，会改多个页文件）、`pages.py --table --write`、`pull_notes.py --write`、不带 `--only` 的 `plot.py <deck>`（换主题后）以及 commit。commit 显式列出路径，**不用 `git add -A`**，免得把别的 agent 改了一半的文件一起提交。
- 共享文件（`primitives.js`、`build.js`、`theme/`、`deck.config.js`、`slides/_lib/`、`plotting/style.py`、`plotting/common.py`、大纲索引）只做追加式修改，由集成者合并；不改已有函数的签名和行为。
- 图的 run_meta 每张图一份、画图永远带 `--only`，并行画图不会互相覆盖。PDF 只和最近一次整套构建一样新。

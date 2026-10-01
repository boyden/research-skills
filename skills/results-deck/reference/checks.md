# 验证流程与踩过的坑

每次改页后至少做 §1–§3；挪页、增删页、改标题后加做 §7 的「页引用」；讲者改过讲稿后做 §7 的「讲稿是数据」。
默认只验证自己改的那几节，整套 deck 的构建和逐页检查由集成者做（§8）。

## 1. 语法和结构

```bash
for f in js/*.js; do node --check "$f"; done                 # builder 语法
node js/build_deck.js --sections results --out "$SCRATCH/results.pptx"
python <pptx skill 目录>/scripts/office/validate.py "$SCRATCH/results.pptx"   # 要求 All validations PASSED
```

- 结构检查用 Anthropic pptx skill 自带的 `validate.py`（装了才有；没装就跳过并在汇报里写明没做）。
  LibreOffice 能打开不等于 PowerPoint 能打开，所以渲染通过不能代替这一步。
- 构建先写临时文件，成功后才改名；中途失败（如缺图）时上一版输出原样保留。

## 2. 渲染

```bash
soffice -env:UserInstallation=file://$SCRATCH/lo_profile_$$ --headless \
        --convert-to pdf --outdir "$SCRATCH" "$SCRATCH/results.pptx"
pdftoppm -r 60 -png "$SCRATCH/results.pdf" "$SCRATCH/preview/page"
```

- **每次转换用独立的 LibreOffice profile**（`-env:UserInstallation=file://<唯一目录>`）：几个转换同时跑时共用默认 profile 会互相锁住，
  表现为转换静默失败或卡住。
- 预览写在自己的临时目录，不写 `output/`。60 dpi（和 examples/slides/render.sh 一致）够看版面；看小字或细线时对单页用 100–150 dpi。
- 转换失败时只警告，不让构建失败：pptx 照常保留，旧 PDF 不动。

## 3. 逐页看 PNG

只看改过的页，每页过一遍：

- [ ] 文字溢出或被截断（结论框超过 3 行、表格最后一行出框、bullet 掉出页面）
- [ ] 元素重叠（标题折行压到图、结论框压到来源行、图标偏离自己那一行）
- [ ] 图被拉伸、压扁或缩放（对比图的像素尺寸 / dpi 与放置尺寸）
- [ ] 页脚缺失（来源行、页码）；⚠️ 页有 DRAFT 标签，✅ 页没有
- [ ] 出现非英文文字（图里、页上、表格里）
- [ ] 数字和大纲的 Message、来源表一致

发现问题就改了重出，再看一遍；图本身的问题回画图代码改（见 SKILL.md「什么时候停下来问」）。

## 4. 字体与 z 序：预览和 PowerPoint 不一样的地方

- **模板字体要装进系统**，否则 LibreOffice 用更宽的替代字体，长标题折成两行、结论句多一行，预览和 PowerPoint 对不上。
  不需要 root：把字体文件放进用户字体目录 `~/.local/share/fonts/<字体名>/`，再 `fc-cache -f ~/.local/share/fonts`。
  构建时检查字体在不在（`fc-list | grep <字体名>`），不在就打印一行警告。
- **商业字体文件不提交、不再分发**：多数「可装在自己设备上使用」的许可不允许放进仓库。在文档里写清从哪里下载、装到哪里。
- 装不了字体时：预览里放得下，PowerPoint 里一定放得下（替代字体更宽），但换行位置只是近似。
- **主图放到 z 序最底**：图在标题之后加入，z 序就在标题之上，标题一折行第二行就被图盖住、在 PNG 里看不见。
  主图 helper 加完图后立刻置底（同页多张图保持彼此顺序）；本来就该盖在形状上的图标、小图不动。

## 5. 自动碰撞检查（思路）

几十页逐页肉眼看容易漏，可以先用脚本筛一遍：

- 文字框：`pdftotext -bbox-layout <pdf>` 给出每一行渲染后的框（pt）。
- 图片框和 z 序：从 pptx 的 slide XML 读每个 `p:pic` 的位置（EMU → pt）和它在 `spTree` 里的次序；
  PDF 里的一行文字按内容匹配回 pptx 的文本框，得到它的 z 序。
- 逐页报：标题行被 z 序更高的图盖住（hidden title）；标题和图相交但字在上面；标题折成 2 行以上及它到下一个元素的距离；
  其他文字行与图相交超过 3 pt；两行文字框互相重叠。有问题的页渲成低分辨率 PNG 供目测。
- **误报是预期的**：PNG 的白边或透明边、特意盖在图上的比例尺和标签、表格列里的图标都会被报成相交；
  PDF 的行框比字形高。**最终以 PNG 为准**，脚本只决定先看哪几页。

## 6. Supplementary 页隐藏，PDF 照出

- `supplementary` 节的页在 pptx 里设成隐藏（slide XML 的 `show="0"`），放映时跳过。
- LibreOffice 7.4 以前转 PDF 会**跳过隐藏页**，也没有导出隐藏页的选项。做法：转 PDF 前复制一份 pptx，去掉副本里的 `show="0"`，转副本。
  pptx 保持隐藏，PDF 每页一张，页数与 `pages.json` 一致。
- 核对：PDF 页数 = `pages.json` 条数。

## 7. 页引用和讲稿

**页引用**（挪页、增删页、改标题之后）：

1. 改 `SLIDES`（或 builder 里的标题）→ 整套构建（pptx + PDF + `pages.json`）；
2. 重写大纲里的生成块（页码表、页数）；
3. `--check`：不存在的 key、手写的 `P<数字>`、过期的生成块都要清零。
4. 挪页工具可以把这几步串起来，并顺手往 `CHANGELOG.md` 追加一行；它只改 `SLIDES` 那一段，改前备份。

**讲稿是数据**：

- 讲稿存在 `notes.json`（`{builder key: 全文}`，按页序），构建时整段替换该页的 notes；没有条目的页用 builder 里的兜底文字。
- 讲者在 PowerPoint 里改了讲稿后，**真相来源是讲者的 pptx**。同步脚本读 pptx 每页的备注，按页标题（左上第一个文本框）配 key：
  第一页固定是标题页；然后查别名表；再按标题在 `pages.json` 里唯一匹配。配不上、重名、key 已被占用的页**不写**，
  列进 unmatched 文件，加别名后重跑。先 `--dry-run` 看每个 key 是 identical / changed / new，再 `--write`。
- 只读回纯文字：加粗、字号不保留；段落和软换行都变成换行。
- pptxgenjs 把整段讲稿写成一个段落；构建后按换行拆成多个 `a:p`，PowerPoint 里的段落才和 JSON 一致。
- **挪页后查讲稿里的相对引用**：「the next slide」「the previous slide」「the supplementary slide '…'」「Next, I'll show …」挪页后会悄悄变错。
  用脚本把这些句子连同当前邻页（或被点名的页）的标题列出来，逐条人读；关键词重叠只是分诊，泛词会把错的判成对的。
  脚本只报告不改：讲稿是讲者的，要改就在 pptx 里改，再同步。
- 为版面从页上挪进讲稿的细节写成 `Note: …`，讲者能一眼看出哪些话页上没有。

## 8. wip、发布和并行改页

- **整套构建写 wip**（`<deck>_wip.pptx`，连同 PDF 和 `pages.json`），每次覆盖；只由集成者跑。
- **发布**：`--release` 写 `<deck>_v<N>.pptx`（+ PDF + `pages.json`），N = 现有最大版本号 + 1；文件名只带版本号不带日期；已发布的不覆盖、不删除。
- **并行改页**：每个人 / agent 管自己的节和自己的 `slides_<block>.js`，只构建自己那几节到临时路径：
  `node js/build_deck.js --sections <key>[,<key>] --out $SCRATCH/<名字>.pptx`。这种构建拒绝写 wip，页码是节内页码，默认不出 PDF。
- 共享文件（`primitives.js`、`style.js`、`build_deck.js`、大纲索引）只做追加式修改，由集成者合并；不改已有函数的签名和行为。
- 图的 run_meta 每张图一份、画图永远带 `--only`，并行画图不会互相覆盖。PDF 只和最近一次整套构建一样新。

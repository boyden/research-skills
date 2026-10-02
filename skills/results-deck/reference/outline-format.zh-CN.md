[English](outline-format.md) | **简体中文**

# 大纲格式

大纲是 deck 内容的唯一来源：页序之外的一切（标题、上屏原句、图、数字和来源、状态、讲稿要点）都先写在这里，
再由各页文件 `slides/<key>.js` 照抄；engine 不读大纲。页序由每个页文件的 `section` 和 `order` 决定（节按 `deck.config.js` 里 `sections` 的顺序），大纲不手写页号。

## 1. 目录结构

```
outline/
  README.md          索引
  00_title_background.md
  01_<chapter>.md    一章一个文件；章内按内容编号（1.1、1.2 …）排
  …
  CHANGELOG.md       挪页、改名、合并、删页的历史
  archive/           冻结的旧版（拆分前的整份大纲、换稿前的讲稿），工具不碰
```

- **一章一个文件**：改一页只读索引和那一章，不必把整份大纲读一遍；几个人 / agent 并行改不同章不冲突。
- 内容编号（`4.1`、`4.0a`）只是大纲里的编号，不是页序；页号随构建变，从 `pages.json` 查。
- 历史写进 `CHANGELOG.md`，章节文件只写当前状态。旧版冻结到 `archive/`，保留旧页号，不再改。
- 从 `engine/template/` 复制出来的新 deck 已经带一个这样组织的 `outline/`（README 含两个生成块，外加一个章节文件）。

### README.md（索引）包含

1. 一段约定：`Message` 是上屏英文原句、其余说明用项目文档语言；状态图标的含义；页引用写法（见 §3）。
2. 目录：每个章节文件一行，写它管哪几页（用 `{{keyA}}–{{keyB}}`）。
3. **生成的页数块和页码对照表**，放在标记注释之间，由 `pages.py <deck> --table --write`（集成者）重写，不手改：

```markdown
<!-- pages:counts:start -->

共 24 页（节 key 和页数）：`title` 1 · `background` 3 · `results` 14 · `summary` 2 · `supplementary` 4

<!-- pages:counts:end -->

<!-- pages:table:start -->

| 页 | 节 | 小节 | 页标题 | key | Note |
|---|---|---|---|---|---|
| P5 | results | 2.1 | Hormone Therapy — Recurrence-free Survival | `sKmTamoxifen` | tamoxifen 与无 tamoxifen 的 KM；图 km_example |

<!-- pages:table:end -->
```

- 页、节、页标题、key、页数每次按 `pages.json` 重写；「小节」「Note」两列是手写的，按 key 保留。
- 新页的小节写「—」、Note 写「（待补 Note）」，提醒手补；key 被删时丢掉那一行和它的 Note（`--write` 先把文件备份到 `.backups/`）。
- 页数行、表头和占位 Note 用哪种语言由 `deck.config.js` 的 `lang` 决定：`"zh"` 写上面这些字样；`"en"`（默认）写 `N slides (section key and slide count): …`、`| Page | Section | Subsection | Slide title | key | Note |` 和 `(Note to be added)`。
  `lang: "zh"` 时 pages.py 读存在的 `.zh-CN.md` 大纲文件；两种语言的表都按列位置读，所以改了 `lang` 再跑 `--table --write` 就会改写过来。

## 2. 逐页块

每页一个块，模板如下（`<>` 处替换）：

```markdown
### <内容编号> <主题标题> <状态> · {{<key>}}
- **Message**: <上屏的英文原句，一字不差>
- **Figure**: `figures/<图名>.png`（`plotting/<模块>.py` 的 `fig_<名>`，注册名 `<图名>`）：<图里画了什么，panel 怎么排>
- **数字**：<每个上屏数字，带 n、事件数、区间；来源表 + 列 / run_meta 键>
- **Source**: <Source 行原文>
- **可能被过度解读（只在讲稿，不上屏）**：<一两句>
- **Speaker notes**：<讲稿要点，或「见 notes/<key>.md」>
- 待确认：<⚠️ 页写清楚要确认什么、问谁、卡在哪个数字>
```

- **标题**写主题，不写结论（见 [writing-style.md](../../../shared/writing-style.zh-CN.md)）。
- **Message** 就是上屏那句，照抄进页文件；太长时拆成编号的几条 bullet，每条也是原句。用户改过的措辞照用户的写，口径放到讲稿。
- **Figure** 写到画图函数和注册名，图有问题时知道去哪改（`plot.py <deck> --only <图名>` 重画）；不是按上屏尺寸画的图（原样链接的外部图）注明。
- **数字**每个都能指到表的行列或 run_meta 的键（见 [numbers-and-sources.md](../../../shared/numbers-and-sources.zh-CN.md)）；
  上屏的数字必须在这里出现，这里有的不一定上屏。
- **可能被过度解读**单独一条，只进讲稿或限制页，不堆到 Message 里。
- 人工核对过的事实写「已确认（日期，核对方式）」，不写人名。

### 状态图标

| 图标 | 含义 | 构建时 |
|---|---|---|
| ✅ | 图和数字都就绪 | 正常出页 |
| ⚠️ | 要先确认或补分析 | 照样出页，右上角加 `DRAFT – to be confirmed`（`P.draft(s)`），「待确认」一条抄进讲稿 |
| ✏️ | 文字页或原生表格页（方法、定义、总结） | 数字从块里写明的来源抄，讲稿里写出处 |

确认之后把 ⚠️ 改成 ✅，在块里记一句「已确认（日期，核对方式）」，去掉 DRAFT 标签。

## 3. 页引用：`{{key}}`

活文档里**不手写页号，也不手写页标题**。页号会随增删页、挪页变，标题会改名，手写的引用会悄悄过期。

- key = 这一页的页文件名去掉 `.js`（`slides/<key>.js`，写进 `pages.json` 的 `builder` 字段），如 `sKmTamoxifen`。一个页文件只出一页，所以 key 唯一。
- 页标题可以重复（比如渐进强调，同一个标题连放两页）；build.js 和 pages.py 只打 WARNING，每个 token 照样按 key 展开。
  讲稿同步按标题配页，所以重复的标题要在 `notes/_aliases.json` 里写别名（`"<标题>"`、`"<标题>#2"`）。

| 写法 | 展开后 | 用途 |
|---|---|---|
| `{{sKmTamoxifen}}` | `P5「Hormone Therapy — Recurrence-free Survival」` | 一页：页号加标题 |
| `{{sMethods}}–{{sForest}}` | `P3「…」–P7「…」` | 范围：两端各一个 token，各自展开 |
| `{{sKmTamoxifen.title}}` | `Hormone Therapy — Recurrence-free Survival` | 正文点名某页，不要页号 |
| `{{sKmTamoxifen.page}}` | `P5` | 只要页号 |

- 反引号（行内代码、代码块）里的写法是字面文字：不展开、不检查。在文档里举例就放进反引号。
- 页号和标题从最近一次整套构建的 `pages.json`（`<outDir>/<name>_wip.pages.json`）查，所以挪页、改标题都不用改 md。只有页文件改名（即 key 变了）才要全局替换 key，`notes/<key>.md` 也要跟着改名。

`engine/tools/pages.py <deck>` 有这几个模式：

| 模式 | 读 / 写 | 做什么 |
|---|---|---|
| `--check` | 只读，有错退出码 1 | 不存在或写错的 key；手写的 `P<数字>`（含 Note 格）；反引号里像 key 的 `sXxx` 既不是 `pages.json` 的 key 也不是页文件 `slides/<名>.js`；生成块过期 |
| `--show <文件>` | 只读 | 把文件里每个 token 展开成页号加标题再打印 |
| `--keys` | 只读 | 列出每页的页号、key、节、标题 |
| `--table [--write]` | 默认演练 | 重写标记注释之间的页码表和页数块，手写列按 key 保留 |

不是页号的 `P21` 这类字符串（如蛋白名）登记进 `<deck>/pages_ignore.txt`（每行 `文件:正则`），或在行里加 `<!--pages:ignore-->`。

## 4. 完整示例块（公开数据 GBSG2）

```markdown
### 2.1 Hormone Therapy — Recurrence-free Survival ✅ · {{sKmTamoxifen}}
- **Message**: Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).
- **Figure**: `figures/km_example.png`（`examples/plotting/survival.py` 的 `fig_km`，注册名 `km_example`，12.1 × 4.6 in）：
  两个等大的正方形 KM，左边 tamoxifen vs no tamoxifen，右边阳性淋巴结按中位数分组；每个 panel 右侧写 HR [95% CI]、
  Cox p、C-index、log-rank p，下方是 number at risk。下面那条（预后差）红、上面那条蓝。
- **数字**（run_meta `km_example.json` 的 `hormone_therapy`）：HR 0.695 [0.544–0.888]（yes vs no），Cox p 0.0036，
  C-index 0.543，log-rank p 0.0034；n = 686，299 个复发或死亡事件。上屏 HR 两位小数，p 三位小数。
  右边 panel 的数字只在图里，结论句不讲它。
- **Source**: GBSG2 trial (lifelines `load_gbsg2`); univariate Cox, recurrence-free survival
- **可能被过度解读（只在讲稿，不上屏）**：单变量 Cox，没有调整肿瘤大小、分级、淋巴结和激素受体，
  所以写 *associated with*，不写 *improves*；C-index 0.543 说明单靠这一个变量区分能力很弱。
- **Speaker notes**：Both panels use the same endpoint. Note: the HR is yes vs no; the right panel's HR is per SD of log(1 + nodes), drawn as a median split.
```

构建出来的这一页（`slides/sKmTamoxifen.js`）：标题 `Hormone Therapy — Recurrence-free Survival`，图 1:1 放在 y = 1.1 in（主题的 `geometry.figureTop`），底部是 Message 那句，
右下角是 Source 行，讲稿是 Speaker notes 那段，存在 `notes/sKmTamoxifen.md`。

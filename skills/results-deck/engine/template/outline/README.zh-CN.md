[English](README.md) | **简体中文**

# Deck 大纲：<题目>

> 下面两个生成块（各节页数、页码对照表）由 `python3 <engine>/tools/pages.py <deck 目录> --table --write` 按最近一次构建的 `pages.json` 重写，块里只手改「小节」「Note」两列。

## 约定

- **Message** 一行是上屏的英文原句，页文件照抄；其余说明用中文。图、数字、来源的写法见各章文件里的逐页块。
- 状态：✅ 图和数字都就绪 · ⚠️ 要先确认或补分析（照样出页，页文件里调 `P.draft(s)`，右上角显示 `DRAFT – to be confirmed`）· ✏️ 文字页或原生表格页（方法、定义、总结）。
- 页引用：不手写页号，也不手写页标题，写页的 key（页文件名 `slides/<key>.js`）。读的时候用 `pages.py <deck 目录> --show <文件>` 展开。

  | 写法 | 展开后 | 用途 |
  |---|---|---|
  | `{{sKm}}` | `P2「Hormone Therapy — Recurrence-free Survival」` | 一页：页号加标题 |
  | `{{sKm}}–{{sForest}}` | `P2「…」–P3「…」` | 范围：两端各自展开 |
  | `{{sKm.title}}` | `Hormone Therapy — Recurrence-free Survival` | 只要标题 |
  | `{{sKm.page}}` | `P2` | 只要页号 |

  反引号里的写法是字面文字，不展开、不检查（上表就是这样写的）。`pages.py <deck 目录> --check` 会拦下手写的页号、不存在的 key 和过期的生成块。
- 人工核对过的事实写「已确认（日期，核对方式）」，不写人名。

## 目录

- [01_results.md](01_results.zh-CN.md)：全部五页，{{sTitle}}–{{sSuppTable}}（标题页、结果、总结、Supplementary）；章多了再按章拆成 `NN_<章>.md`。
- `CHANGELOG.md`：挪页、改名、合并、删页的历史，第一次改页序时建；章节文件只写当前状态。
- `archive/`：冻结的旧版大纲，保留旧页号，工具不读。

## 页码对照（wip）

<!-- pages:counts:start -->

共 5 页（节 key 和页数）：`title` 1 · `results` 2 · `summary` 1 · `supplementary` 1

<!-- pages:counts:end -->

表里的页、节、页标题、key 每次按 `pages.json` 重写；「小节」是本大纲的内容编号，「Note」是一两句概括和定位线索（图、函数），两列手写、按 key 保留。
新页的小节是「—」、Note 是「（待补 Note）」，要手补；key 被删时 `--table --write` 先备份这个文件再丢掉那行。
`supplementary` 一节的页在 pptx 里隐藏，PDF 里照常导出。

<!-- pages:table:start -->

| 页 | 节 | 小节 | 页标题 | key | Note |
|---|---|---|---|---|---|
| P1 | title | 0.1 | Title | `sTitle` | 标题页：题目、讲者职称、日期，不放数字。 |
| P2 | results | 1.1 | Hormone Therapy — Recurrence-free Survival | `sKm` | tamoxifen 与无 tamoxifen 的 KM，HR 0.69 [0.54–0.89]（n = 686，299 个事件）；图 `results_km`。 |
| P3 | results | 1.2 | Clinical Factors — Univariate Cox | `sForest` | 8 个临床因素的单变量 Cox forest，阳性淋巴结最强；图 `results_forest`。 |
| P4 | summary | 2.1 | Summary | `sSummary` | 三条结论，数字分别抄自 {{sKm}}、{{sForest}}、{{sSuppTable}}。 |
| P5 | supplementary | S.1 | Supplementary — Cohort Characteristics | `sSuppTable` | 按 hormone therapy 分组的队列特征原生三线表。 |

<!-- pages:table:end -->

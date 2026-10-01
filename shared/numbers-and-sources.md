# 数字与来源

适用于所有把分析结果写给别人看的产出：deck、论文、报告、回复审稿意见。

## 规则

1. **每个数字都能指到来源。** 来源是结果表（文件 + 行 / 列）或文献。deck 写在页上的 Source 行，
   论文写在图注或方法里；更细的口径写在大纲或 speaker notes。
2. **找不到或对不上就停下来问**，不要自己挑一个看起来对的。旧版 deck、旧草稿只提供结构，
   里面的数字一个都不抄，全部从当前结果重新取。
3. **数字从表里读，不手抄。** 画图脚本读结果表，把画图时用到的统计量写进每张图一份的 run_meta
   （`run_meta/<图名>.json`：输入（文件路径或数据集名）、统计量、脚本、时间）。正文里的数字从 run_meta 或结果表抄。
   画图时重算的量（如 log-rank p）和表里不一致就报错退出，保证画的就是表里的那个分组。
4. **效应量带上下文。** 写区间、n、事件数，写清单位（per SD / per unit / yes vs no）。
   同一份产出里口径只定一次（例如「HR 一律 per SD」），之后不混用。
5. **多重检验的措辞。**
   - 名义 p < 0.05 但没过 FDR：叫 *candidate* 或 *nominal*，不写 *significant*。
   - 一个都没过 FDR 时，不写任何「过了 FDR」的说法。
   - 在同一批样本上选出又评估的，不叫 *validation*；样本小或事后选择的，标 *exploratory*。
6. **格式统一。**
   - p 值三位小数，小于 0.001 写 `<0.001`。
   - HR 两位或三位小数，同一份产出里统一。
   - 区间用 en dash（`0.54–0.89`），千分位用逗号（`3,334,358`）。
7. **人工核对过的事实**写成「已确认（日期，核对方式）」，不写是谁确认的。
8. **可能被过度解读的地方**单独写一句，放在 notes 或限制一节，不堆到上屏的那句话里。

## 示例（公开数据 GBSG2，见 [examples/](../examples/)）

上屏结论句：

> Tamoxifen is associated with longer recurrence-free survival (HR 0.69 [0.54–0.89], p = 0.004; n = 686, 299 events).

Source 行：

> Source: GBSG2 trial (lifelines `load_gbsg2`); univariate Cox, recurrence-free survival

对应的 run_meta 片段（`examples/figures/run_meta/km_example.json` 的 `stats` 字段；文件里是未取整的值，这里为排版截短）：

```json
{"hormone_therapy": {"hr": 0.695, "lo": 0.544, "hi": 0.888, "p": 0.0036, "c": 0.543,
                     "n": 686, "events": 299, "logrank_p": 0.0034}}
```

反例：

- 「Tamoxifen significantly improves survival」：没有区间、n、来源，*improves* 还暗示了因果。
- 只写 Cox p、图上画的却是中位数分组：两个 p 在 0.05 附近时会对不上，所以两个都写（见 [figures.md](figures.md)「生存分析图」）。

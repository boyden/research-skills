**English** | [简体中文](tables.zh-CN.md)

# Tables: three-line tables

Tables in outputs (slides, figures, papers, reports) are all three-line tables: native deck tables, tables drawn into figures, the number columns to the right of forest plots, and paper tables. The only exception is when the user says otherwise.
Markdown tables in this repository's docs are not covered: markdown cannot draw three-line tables.

## Rules

- Only three horizontal rules: top rule (thick), rule under the header (thin), bottom rule (thick). No vertical lines, no inner horizontal lines, no background fill.
- First column left-aligned; the other columns centered, with the header and the values below it sharing the same column center.
- Header in bold, at the same font size as the body. Group label rows may be bold in the accent color, written across the whole row, not squeezed into the first column and wrapped.
- Number formats follow [numbers-and-sources.md](numbers-and-sources.md): the same number of decimals within a column, intervals with an en dash.

![Three-line table example](../examples/figures/three_line_table_example.png)

## Implementation

**matplotlib** (tables drawn into figures):
- Place the text with `ax.text`: first column `ha="left"`, other columns `ha="center"`.
- Then draw the three rules: top / bottom rules 1.5 pt, header rule 0.75 pt.
- Rules and text must use the same coordinates, with `xlim` / `ylim` fixed; otherwise `plot` stretches the data range and the text ends up outside the canvas.
- For a full example see `fig_table()` in [examples/plotting/tables.py](../examples/plotting/tables.py).

**pptxgenjs** (native deck tables): set borders cell by cell, `border: [top, right, bottom, left]`:

```js
const none = { type: "none" };
const outer = { type: "solid", pt: 1.5, color: "595959" };  // top and bottom rules
const mid = { type: "solid", pt: 0.75, color: "595959" };   // rule under the header
// row i of rows[0..last]; set the header rule on BOTH cells of the shared edge,
// otherwise some renderers let the blank edge win.
const top = i === 0 ? outer : i === 1 ? mid : none;
const bottom = i === last ? outer : i === 0 ? mid : none;
options = { align: j === 0 ? "left" : "center", valign: "middle", border: [top, none, bottom, none] };
```

Also pass the table frame height `h` explicitly, as the sum of the row heights; without it pptxgenjs writes a 1 in table frame.

**LaTeX**: the `booktabs` package, `\toprule`, `\midrule`, `\bottomrule`, column spec `l c c c`; no `|` and no `\hline`.

**Word / docx**: keep only the table borders above and below the header row and below the last row, and set all others to none; first column left-aligned, the other columns centered.

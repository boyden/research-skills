#!/usr/bin/env python3
"""Contact sheet of all grey icon PNGs, grouped by topic (order and topics from manifest.csv).

Writes examples/icons/icon_sheet.png. Needs matplotlib; run render_pngs.py first.
    python3 examples/icons/make_icon_sheet.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
COLS = 10
CELL = 1.25          # inches per icon cell (width)
LABEL_H = 0.32       # inches of label text under each icon
HEADER_H = 0.45      # inches per topic header

plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]


def main():
    rows = list(csv.DictReader(open(HERE / "manifest.csv", encoding="utf-8")))
    topics = list(dict.fromkeys(r["topic"] for r in rows))
    groups = {t: [r for r in rows if r["topic"] == t] for t in topics}

    # layout in inches, top to bottom
    blocks, y = [], 0.25
    for t in topics:
        n_rows = -(-len(groups[t]) // COLS)
        blocks.append((t, y, n_rows))
        y += HEADER_H + n_rows * (CELL + LABEL_H) + 0.15
    width, height = COLS * CELL + 0.4, y + 0.1

    fig = plt.figure(figsize=(width, height))
    for t, top, _ in blocks:
        fig.text(0.2 / width, 1 - (top + 0.3) / height, f"{t}  ({len(groups[t])})",
                 fontsize=13, fontweight="bold", color="#A51C30", va="baseline")
        for i, r in enumerate(groups[t]):
            row, col = divmod(i, COLS)
            x0 = 0.2 + col * CELL
            y0 = top + HEADER_H + row * (CELL + LABEL_H)
            size = CELL * 0.62
            ax = fig.add_axes([(x0 + (CELL - size) / 2) / width, 1 - (y0 + 0.08 + size) / height,
                               size / width, size / height])
            ax.imshow(mpimg.imread(HERE / "png" / r["source"] / f"{r['name']}.png"))
            ax.axis("off")
            fig.text((x0 + CELL / 2) / width, 1 - (y0 + 0.08 + size + 0.07) / height,
                     f"{r['source']}/\n{r['name']}", fontsize=6.5, color="#333333",
                     ha="center", va="top", linespacing=1.1)
    out = HERE / "icon_sheet.png"
    fig.savefig(out, dpi=110, facecolor="white")
    print(out)


if __name__ == "__main__":
    main()

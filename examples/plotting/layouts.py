"""Slide layouts: one to-scale diagram per page type in skills/results-deck/reference/slide-types.md.

Coordinates are the defaults of the neutral theme (skills/results-deck/engine/themes/neutral/theme.json) and
of the page files of the two example decks (examples/slides/results/slides/, examples/slides/narrative/slides/);
the constants below document the neutral layout and do not follow the theme.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from plotting.style import ACCENT, FULL, HALF, INK, KM_HIGH, MUTED, RULE, SLIDE_H, SLIDE_W

INPUTS: list = []

MX = 0.6                         # side margin
CW = SLIDE_W - 2 * MX            # content width
CONC_FIG_Y, CONC_TEXT_Y, CONC_H = 5.75, 5.95, 1.05
CHROME, FIG_FC, CONC_FC = "#f3f3f3", "#eaf1fb", "#fbeaec"


class Layout:
    """A 16:9 slide drawn at 0.6 scale (8.0 x 4.5 in), in slide inches with the origin top left."""

    SCALE = 0.6

    def __init__(self):
        self.fig = plt.figure(figsize=(SLIDE_W * self.SCALE, SLIDE_H * self.SCALE))
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, SLIDE_W)
        ax.set_ylim(SLIDE_H, 0)
        ax.axis("off")
        ax.add_patch(Rectangle((0, 0), SLIDE_W, SLIDE_H, fill=False, ec=INK, lw=1.2))
        self.ax = ax
        self.boxes = {}

    def zone(self, x, y, w, h, label="", fc=CHROME, ec=MUTED, color=INK, size=8, weight="normal", ls="-",
             ha="center", key=None):
        if fc or ec:
            self.ax.add_patch(Rectangle((x, y), w, h, fc=fc or "none", ec=ec or "none", lw=0.8, ls=ls))
        if label:
            tx = {"center": x + w / 2, "left": x + 0.1, "right": x + w - 0.1}[ha]
            self.ax.text(tx, y + h / 2, label, ha=ha, va="center", fontsize=size, color=color, weight=weight,
                         linespacing=1.3)
        if key:
            self.boxes[key] = [round(v, 3) for v in (x, y, w, h)]

    def textbox(self, x, y, w, h, label, **kw):
        """A native text box: white, dashed outline."""
        self.zone(x, y, w, h, label, fc="white", ls=(0, (3, 2)), **kw)

    def figure(self, x, y, w, h, label, size=9, key="figure"):
        self.zone(x, y, w, h, label, fc=FIG_FC, ec=KM_HIGH, size=size, key=key)

    def conclusion(self, y=CONC_FIG_Y, label="Conclusion: one finding, bold black (18 pt; split into bullets if long)",
                   size=9):
        self.zone(MX + 0.1, y, CW - 0.2, CONC_H, label, fc=CONC_FC, ec=ACCENT, size=size, weight="bold",
                  key="conclusion")

    def chrome(self, title="Title: topic, not finding (28 pt bold)", page=True, source=True, abbr=False):
        """Title, logo placeholder, page number, source line (primitives.js newSlide / source / abbr)."""
        if title:
            self.zone(0.59, 0.36, 9.6, 0.6, title, weight="bold", key="title")
        self.zone(SLIDE_W - 2.35, 0.2, 2.0, 0.35, "Logo", size=7, key="logo")
        if page:
            self.zone(SLIDE_W - 0.97, 7.0, 0.6, 0.3, "n", size=7, key="page")
        if source:
            self.zone(6.4, 7.05, 5.88, 0.33, "Source / citation (9 pt serif, right-aligned)", size=7, key="source")
        if abbr:
            self.zone(MX, 7.05, 5.5, 0.33, "Abbreviations (9.5 pt gray)", size=7, key="abbreviations")

    def ymarks(self, *ys):
        for y in ys:
            self.ax.text(0.08, y, f"y {y:g}", fontsize=7, color=MUTED, va="center")

    def arrow(self, x1, y1, x2, y2, color=MUTED, lw=1.0, scale=8):
        self.ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                         arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=scale,
                                         shrinkA=0, shrinkB=0))

    def done(self, name):
        return self.fig, {"layout": name, "slide_in": [SLIDE_W, SLIDE_H], "boxes_in": self.boxes,
                          "geometry": "engine/themes/neutral/theme.json and examples/slides/*/slides/*.js"}


def fig_layout_figure_conclusion():
    """Figure + conclusion, the most common result slide, with the fixed zones labeled."""
    L = Layout()
    L.chrome(abbr=True)
    fx = (SLIDE_W - FULL[0]) / 2
    L.figure(fx, 1.1, *FULL, "Figure drawn at this exact size: 12.1 × 4.6 in\n"
             "(font sizes in the plotting code = font sizes on screen; placed 1:1, never scaled)", size=10)
    L.conclusion(label="Conclusion: one finding, bold black (18 pt; split into bullets if long)", size=10)
    L.ymarks(1.1, 5.7, 6.8)
    return L.done("figure + conclusion")


def fig_layout_title():
    """Title slide (the closing slide uses the same frame)."""
    L = Layout()
    L.zone(MX, 0.3, 2.4, 0.35, "Logo (top left here)", size=7, key="logo")
    L.zone(MX, 2.3, 0.1, 1.86, fc=ACCENT, ec=None, key="accent_bar")
    L.textbox(0.95, 2.3, 11.2, 1.3, "Talk title, up to two lines in one text box (40 pt bold gray)", size=10,
              weight="bold", key="title")
    L.textbox(0.95, 3.72, 11.2, 0.45, "Subtitle (20 pt gray)", key="subtitle")
    L.textbox(6.4, 4.75, SLIDE_W - MX - 6.4, 1.3, "Presenter, role\nDepartment, institution\nMeeting · date\n"
              "(16 pt, right-aligned)", ha="right", key="presenter")
    L.zone(0, 6.83, SLIDE_W, 0.05, fc=ACCENT, ec=None, key="accent_rule")
    L.ax.text(0.95, 6.6, "No topic title, no page number; the presenter's name appears only here",
              fontsize=7, color=MUTED, va="center")
    L.ymarks(2.3)
    L.ax.text(SLIDE_W - 0.1, 6.98, "accent rule y 6.83", fontsize=7, color=MUTED, ha="right", va="center")
    return L.done("title slide")


def fig_layout_agenda():
    """Agenda / roadmap: numbered sections, the current one highlighted."""
    L = Layout()
    L.chrome(title="Agenda", source=False)
    y0, pitch, x0 = 1.45, 0.88, 1.0
    w = SLIDE_W - 2 * x0
    for i in range(5):
        y, on = y0 + i * pitch, i == 1
        if on:
            L.zone(x0, y, w, pitch - 0.1, fc=CHROME, ec=None)
            L.zone(x0, y, 0.08, pitch - 0.1, fc=ACCENT, ec=None)
        elif i < 4 and i != 0:
            L.ax.plot([x0 + 0.35, x0 + w], [y + pitch - 0.05] * 2, color="#d9d9d9", lw=0.8)
        L.ax.text(x0 + 0.35, y + (pitch - 0.1) / 2, f"{i + 1:02d}", fontsize=28 * Layout.SCALE, weight="bold",
                  color=ACCENT if on else "#d9d9d9", va="center")
        L.ax.text(x0 + 1.4, y + (pitch - 0.1) / 2, "Current section (22 pt bold black)" if on else
                  "Section name (22 pt bold, muted)", fontsize=8, weight="bold", color=INK if on else MUTED,
                  va="center")
        L.ax.text(x0 + 6.0, y + (pitch - 0.1) / 2, "Tint band + accent edge bar + accent numeral" if on else
                  "One-line subtitle (16 pt)", fontsize=8, color=INK if on else MUTED, va="center")
    L.ax.text(x0, 6.15, "Repeat at each section start with the same geometry; only the highlight moves",
              fontsize=7, color=MUTED, va="center")
    L.ymarks(1.45)
    return L.done("agenda")


def fig_layout_section_divider():
    """Section divider: big accent numeral, thin rule, section name."""
    L = Layout()
    L.chrome(title=None, source=False)
    L.ax.text(1.2, 3.1, "02", fontsize=120 * Layout.SCALE, weight="bold", color=ACCENT, va="center")
    L.zone(1.2, 2.0, 3.2, 2.2, fc=None, ec=MUTED, ls=(0, (3, 2)), key="numeral")
    L.ax.text(2.8, 4.4, "Numeral (120 pt bold accent)", fontsize=7, color=MUTED, ha="center", va="center")
    L.zone(4.45, 2.35, 0.04, 1.5, fc="#d9d9d9", ec=None, key="rule")
    L.textbox(4.85, 2.35, 7.5, 0.8, "Section name (40 pt bold gray)", size=10, weight="bold", ha="left",
              key="name")
    L.textbox(4.85, 3.2, 7.5, 0.6, "One-line subtitle (20 pt gray)", ha="left", key="subtitle")
    L.ymarks(2.0, 4.2)
    return L.done("section divider")


def fig_layout_big_statement():
    """Big statement: one sentence the audience should accept, with two or three supporting bullets."""
    L = Layout()
    L.chrome()
    L.zone(MX, 1.75, 0.08, 1.35, fc=ACCENT, ec=None, key="accent_bar")
    L.textbox(MX + 0.35, 1.7, CW - 0.6, 1.45, "Statement: one complete sentence (30 pt bold black)", size=10,
              weight="bold", key="statement")
    L.textbox(MX + 0.35, 3.75, CW - 0.6, 2.3, "2–3 supporting bullets, bold lead phrase (18 pt gray)\n"
              "The claim is backed by the citation in the source position", key="bullets")
    L.ymarks(1.7, 3.75)
    return L.done("big statement")


def fig_layout_text_bullets():
    """Text / bullet slide: background, problem statement, design notes."""
    L = Layout()
    L.chrome(abbr=True)
    L.textbox(MX, 1.3, CW, 4.4, "3–6 bullets, one complete idea each; bold lead phrase (16–18 pt gray)\n"
              "Single line spacing, 0 pt before, 8 pt after (10 pt at ≥ 18 pt); hanging indent 16 pt\n"
              "Numbers still carry a source line or citation", key="bullets")
    L.conclusion(CONC_TEXT_Y, label="Conclusion (y 5.95 on slides without a figure; 18 pt bold black)")
    L.ymarks(1.3, 5.95)
    return L.done("text / bullets")


def fig_layout_two_figures():
    """Two figures side by side, one shared conclusion."""
    L = Layout()
    L.chrome(abbr=True)
    gap = 0.2
    x0 = (SLIDE_W - (2 * HALF[0] + gap)) / 2
    for i, lab in enumerate("AB"):
        L.figure(x0 + i * (HALF[0] + gap), 1.1, *HALF, f"Figure {lab}: 5.9 × 4.6 in\nplaced 1:1\n\n"
                 "same height, font sizes\nand axis ranges as the other\n\ngap 0.2 in; the pair is centered "
                 "as one group", key=f"figure_{lab}")
    L.conclusion(label="Conclusion: one shared finding (18 pt bold black)")
    L.ymarks(1.1, 5.7)
    return L.done("two figures")


def fig_layout_figure_takeaways():
    """Half-width figure on the left, two or three reading hints on the right."""
    L = Layout()
    L.chrome(abbr=True)
    L.figure(MX, 1.1, *HALF, "Half-width figure\n5.9 × 4.6 in, placed 1:1", key="figure")
    x = MX + HALF[0] + 0.4
    w = SLIDE_W - MX - x
    L.textbox(x, 1.55, w, 0.4, "Takeaways (18 pt bold gray)", weight="bold", key="heading")
    L.textbox(x, 2.1, w, 3.3, "At most 3 short bullets\nthat guide the eye\n(18 pt gray)", key="bullets")
    L.conclusion(label="Conclusion: still the one finding (18 pt bold black)")
    L.ymarks(1.1, 5.7)
    return L.done("figure + takeaways")


def fig_layout_km_grid():
    """KM grid: one column per variable, one row per endpoint, all panels equal squares."""
    L = Layout()
    L.chrome(title="Title: must fit on one line here (28 pt bold)", abbr=True)
    fx, fy, fw, fh = (SLIDE_W - FULL[0]) / 2, 0.95, FULL[0], 4.9
    L.figure(fx, fy, fw, fh, "", key="figure")
    sq = 1.6
    for r, end in enumerate(["PFS", "OS"]):
        y = fy + 0.2 + r * 2.05
        L.ax.text(fx + 0.3, y + sq / 2, end, fontsize=8, weight="bold", color=INK, ha="center", va="center",
                  rotation=90)
        for c in range(3):
            x = fx + 0.6 + c * 3.9
            L.zone(x, y, sq, sq, f"{end} ·\nvariable {c + 1}", fc="white", ec=KM_HIGH, size=7)
            L.zone(x + sq + 0.1, y, 1.85, sq, "HR [95% CI]\nCox p\nC-index\nlog-rank p", fc="white",
                   ec=MUTED, ls=(0, (3, 2)), size=7)
    L.ax.text(SLIDE_W / 2, fy + fh - 0.3, "12.1 × 4.9 in figure; equal square panels, one shared x range "
              "(at-risk tables under each panel)", fontsize=7, color=KM_HIGH, ha="center", va="center")
    L.conclusion(5.87, label="Conclusion (moved down to y 5.87)")
    L.ymarks(0.95, 5.85)
    return L.done("KM grid")


def _three_line_rules(L, x0, x1, ys):
    """Rules of a three-line table: thick above the header, thin under it, thick under the last row."""
    for y, lw in zip(ys, (1.5, 0.75, 1.5)):
        L.ax.plot([x0, x1], [y, y], color=RULE, lw=lw)


def fig_layout_table():
    """Native three-line table (cohort table, small grid of numbers)."""
    L = Layout()
    L.chrome(abbr=True)
    col_w = [4.3, 2.5, 2.5, 2.5]
    x0 = (SLIDE_W - sum(col_w)) / 2
    xs = np.concatenate([[x0], x0 + np.cumsum(col_w)])
    head_h, row_h, rows = 0.8, 0.5, 6
    y_body = 1.3 + head_h
    L.ax.text(xs[0] + 0.1, 1.3 + head_h / 2, "Characteristic", fontsize=8, weight="bold", color=RULE, va="center")
    for j in range(1, 4):
        L.ax.text((xs[j] + xs[j + 1]) / 2, 1.3 + head_h / 2, f"Group {j}\nn = …", fontsize=8, weight="bold",
                  color=RULE, ha="center", va="center")
    for i in range(rows):
        yc = y_body + (i + 0.5) * row_h
        L.ax.text(xs[0] + 0.1, yc, f"Row label {i + 1} (left)", fontsize=8, color=INK, va="center")
        for j in range(1, 4):
            L.ax.text((xs[j] + xs[j + 1]) / 2, yc, "value (centered)", fontsize=7, color=MUTED, ha="center",
                      va="center")
    _three_line_rules(L, xs[0], xs[-1], [1.3, y_body, y_body + rows * row_h])
    L.boxes["table"] = [round(x0, 3), 1.3, sum(col_w), head_h + rows * row_h]
    L.ax.text(SLIDE_W / 2, 5.4, "Native pptx table: three rules, no vertical lines, no fill; header bold, "
              "same size as the body (16 pt here)", fontsize=7, color=MUTED, ha="center", va="center")
    L.conclusion()
    L.ymarks(1.3, 5.1)
    return L.done("three-line table")


def fig_layout_feature_table():
    """Feature-definition table with a low -> high thumbnail pair per feature and spanning group rows."""
    L = Layout()
    L.chrome(abbr=True)
    col_w = [1.6, 2.0, 3.0, 1.5, 1.5, 2.5]
    heads = ["Feature", "Low → high", "What is computed\n(unit)", "Higher\nvalue", "Lower\nvalue",
             "HR > 1: shorter\nsurvival with"]
    x0 = (SLIDE_W - sum(col_w)) / 2
    xs = np.concatenate([[x0], x0 + np.cumsum(col_w)])
    y, head_h, row_h, grp_h = 1.05, 0.55, 0.62, 0.38
    for j, h in enumerate(heads):
        L.ax.text(xs[0] + 0.1 if j == 0 else (xs[j] + xs[j + 1]) / 2, y + head_h / 2, h, fontsize=7,
                  weight="bold", color=RULE, ha="left" if j == 0 else "center", va="center")
    y_body = y + head_h
    yy = y_body
    for g in range(2):
        L.ax.text(xs[0] + 0.1, yy + grp_h / 2, f"Group {g + 1} (spanning text box, accent bold)", fontsize=7,
                  weight="bold", color=ACCENT, va="center")
        yy += grp_h
        for r in range(2):
            yc = yy + row_h / 2
            L.ax.text(xs[0] + 0.1, yc, "Feature", fontsize=7, weight="bold", color=INK, va="center")
            cx = (xs[1] + xs[2]) / 2
            for dx in (-0.55, 0.15):
                L.zone(cx + dx, yc - 0.24, 0.4, 0.48, fc="white", ec=MUTED)
            L.ax.text(cx, yc, "→", fontsize=7, color=MUTED, ha="center", va="center")
            for j in range(2, 6):
                L.ax.text((xs[j] + xs[j + 1]) / 2, yc, "text", fontsize=7, color=MUTED, ha="center", va="center")
            yy += row_h
    _three_line_rules(L, xs[0], xs[-1], [y, y_body, yy])
    L.boxes["table"] = [round(x0, 3), y, sum(col_w), round(yy - y, 3)]
    L.ax.text((xs[1] + xs[2]) / 2, yy + 0.17, "thumbnails: same size, low left, high right", fontsize=6.5,
              color=MUTED, ha="center", va="center")
    L.textbox(x0, yy + 0.36, sum(col_w), 0.3, "Note line (12 pt gray)", size=7, ha="left", key="note")
    L.conclusion(label="Conclusion: what this group of features answers, not a result")
    L.ymarks(1.05)
    return L.done("feature-definition table")


def fig_layout_key_numbers():
    """Key numbers: at most three large numerals, each with a label and its context."""
    L = Layout()
    L.chrome(abbr=True)
    col = CW / 3
    for i in range(3):
        x = MX + i * col
        L.zone(x + 0.3, 1.9, col - 0.6, 1.3, fc=None, ec=ACCENT, ls=(0, (3, 2)))
        L.ax.text(x + col / 2, 2.55, ["686", "299", "0.69"][i], fontsize=72 * Layout.SCALE, weight="bold",
                  color=ACCENT, ha="center", va="center")
        L.textbox(x + 0.3, 3.25, col - 0.6, 0.45, "Label (20 pt bold gray)", weight="bold")
        L.textbox(x + 0.6, 3.75, col - 1.2, 0.7, "Context: interval,\ndenominator (14 pt gray)", size=7)
    L.ax.text(MX + col / 2, 4.75, "Numeral: 72 pt bold accent", fontsize=7, color=MUTED, ha="center")
    L.conclusion(label="Conclusion: the number again, with its interval and n")
    L.ymarks(1.9, 4.45)
    return L.done("key numbers")


def fig_layout_three_columns():
    """Three columns (problem -> approach -> impact): icon, tag, heading, two lines of body."""
    L = Layout()
    L.chrome(abbr=True)
    gap, y0, isz = 0.7, 1.75, 0.9
    w = (CW - 2 * gap) / 3
    for i, tag in enumerate(["PROBLEM", "APPROACH", "IMPACT"]):
        x = MX + i * (w + gap)
        L.zone(x + (w - isz) / 2, y0, isz, isz, "icon", fc="white", ec=ACCENT, color=ACCENT, size=7)
        L.ax.text(x + w / 2, y0 + 1.275, f"{tag} (accent caps)", fontsize=7, weight="bold", color=ACCENT,
                  ha="center", va="center")
        L.textbox(x, y0 + 1.5, w, 0.5, "Heading (22 pt bold)", weight="bold")
        L.textbox(x + 0.2, y0 + 2.1, w - 0.4, 0.85, "Two lines of body,\ncentered (16 pt gray)", size=7)
        if i < 2:
            L.arrow(x + w + 0.15, y0 + isz / 2, x + w + gap - 0.15, y0 + isz / 2)
    L.conclusion(CONC_TEXT_Y, label="Conclusion: the goal in one sentence (y 5.95)")
    L.ymarks(1.75, 4.8)
    return L.done("three columns")


def fig_layout_methods_flow():
    """Methods flow: a row of 3-5 step cards joined by small arrows, definitions underneath."""
    L = Layout()
    L.chrome(abbr=True)
    gap, y0, h, hh = 0.32, 1.3, 2.3, 0.42
    w = (CW - 4 * gap) / 5
    for i in range(5):
        x = MX + i * (w + gap)
        L.zone(x, y0, w, hh, f"{i + 1} · Step name", fc=ACCENT, ec=None, color="white", size=7, weight="bold",
               ha="left")
        L.zone(x, y0 + hh, w, h - hh, "icon\n\nWhat is done +\nkey parameters\n(13 pt; no results)", fc=CHROME,
               ec=None, size=7)
        if i < 4:
            L.arrow(x + w + 0.04, y0 + h / 2, x + w + gap - 0.04, y0 + h / 2, lw=1.5, scale=7)
    L.boxes["cards"] = [MX, y0, round(CW, 3), h]
    L.textbox(MX, 3.85, CW, 1.9, "Definitions and caveats: 2–3 bullets, bold lead term (14–16 pt gray)\n"
              "Optional: one strip of per-step thumbnails between card headers and bodies (cards then y 1.05, h 3.95)",
              key="bullets")
    L.conclusion(CONC_TEXT_Y, label="Conclusion: what is fixed before outcomes are seen (y 5.95)")
    L.ymarks(1.3, 3.85)
    return L.done("methods flow")


def fig_layout_framework():
    """Framework diagram: inputs -> processing band -> outputs, built from native shapes."""
    L = Layout()
    L.chrome(abbr=True)
    rows, isz = [1.95, 3.35, 4.75], 0.7
    bx, by, bw, bh = 3.25, 1.2, 6.3, 4.3
    L.zone(bx, by, bw, bh, fc=CHROME, ec=None, key="band")
    L.ax.text(bx + 0.2, by + 0.25, "PROCESSING BAND (tint)", fontsize=7, weight="bold", color=MUTED, va="center")
    c1, c2, bwid, bht = bx + 0.3, bx + 2.35, 1.7, 0.7
    fx, fw = bx + 4.45, 1.6
    for i, y in enumerate(rows):
        L.zone(MX, y - isz / 2, isz, isz, "icon", fc="white", ec=ACCENT, color=ACCENT, size=6)
        L.ax.text(MX + 0.82, y, f"Input {i + 1}\n(14 pt bold)", fontsize=7, weight="bold", color=INK, va="center")
        L.arrow(2.7, y, bx - 0.05, y, color=ACCENT, lw=2.4, scale=9)
        L.zone(c1, y - bht / 2, bwid, bht, "Step", fc="white", ec="#d9d9d9", size=7)
        if i < 2:
            L.zone(c2, y - bht / 2, bwid, bht, "Step", fc="white", ec="#d9d9d9", size=7)
            L.arrow(c1 + bwid + 0.04, y, c2 - 0.04, y)
            L.arrow(c2 + bwid + 0.04, y, fx - 0.04, y)
        else:
            L.arrow(c1 + bwid + 0.04, y, fx - 0.04, y)
    L.zone(fx, rows[0] - 0.25, fw, rows[2] - rows[0] + 0.5, "Fusion\n(accent\noutline)", fc="white", ec=ACCENT,
           size=7, weight="bold")
    for i, y in enumerate([2.65, 4.05]):
        L.arrow(bx + bw + 0.05, y, bx + bw + 0.55, y, color=ACCENT, lw=2.4, scale=9)
        ox = bx + bw + 0.7
        L.zone(ox, y - isz / 2, isz, isz, "icon", fc="white", ec=ACCENT, color=ACCENT, size=6)
        L.ax.text(ox + 0.85, y, f"Output {i + 1}\nper patient", fontsize=7, weight="bold", color=INK, va="center")
    L.ax.text(bx + bw / 2, by + bh - 0.22, "thin gray arrows inside the band · thick accent arrows in and out, "
              "one per input / output", fontsize=6.5, color=MUTED, ha="center", va="center")
    L.conclusion()
    L.ymarks(1.2, 5.5)
    return L.done("framework diagram")


def fig_layout_comparison():
    """Two-column comparison: criteria rows, prior approaches vs this work, with check / cross marks."""
    L = Layout()
    L.chrome(abbr=True)
    xL, wL, xA, wA, xB = MX, 2.6, 3.6, 4.0, 8.3
    wB = SLIDE_W - MX - xB
    y0, hh, rh, n = 1.35, 0.55, 0.72, 5
    L.zone(xB - 0.15, y0, wB + 0.15, hh + n * rh, fc=CHROME, ec=None, key="this_work_band")
    L.ax.text(xA, y0 + hh / 2, "Prior approaches (18 pt bold, muted)", fontsize=8, weight="bold", color=MUTED,
              va="center")
    L.ax.text(xB + 0.1, y0 + hh / 2, "This work (18 pt bold, accent)", fontsize=8, weight="bold", color=ACCENT,
              va="center")
    L.ax.plot([xL, SLIDE_W - MX], [y0 + hh] * 2, color=RULE, lw=1.2)
    for i in range(n):
        y = y0 + hh + i * rh
        L.ax.text(xL, y + rh / 2, "Criterion (16 pt bold)", fontsize=8, weight="bold", color=INK, va="center")
        for x, col, lab in [(xA, MUTED, "short phrase (16 pt)"), (xB + 0.1, ACCENT, "short phrase (16 pt)")]:
            L.ax.add_patch(plt.Circle((x + 0.18, y + rh / 2), 0.18, fc="white", ec=col, lw=1.2))
            L.ax.text(x + 0.55, y + rh / 2, lab, fontsize=7, color=INK, va="center")
        L.ax.plot([xL, SLIDE_W - MX], [y + rh] * 2, color=RULE if i == n - 1 else "#d9d9d9",
                  lw=1.2 if i == n - 1 else 0.8)
    L.conclusion(CONC_TEXT_Y, label="Conclusion: the trade-off in one sentence (y 5.95)")
    L.ymarks(1.35, 5.5)
    return L.done("two-column comparison")


def fig_layout_summary():
    """Summary: one row per line of evidence; name and n left, claim and evidence right."""
    L = Layout()
    L.chrome(title="Summary", source=False)
    y0, pitch, xr = 1.3, 1.25, 3.2
    for i in range(4):
        y = y0 + i * pitch
        if i:
            L.ax.plot([MX, SLIDE_W - MX], [y - 0.08] * 2, color="#d9d9d9", lw=0.8)
        L.textbox(MX, y + 0.05, 2.35, 0.5, "Evidence line\n(24 pt bold accent)", color=ACCENT, size=7,
                  weight="bold")
        L.textbox(MX, y + 0.62, 2.35, 0.35, "n = … (12 pt gray)", size=7)
        L.textbox(xr, y + 0.05, SLIDE_W - MX - xr, 0.45, "Claim: one sentence (17 pt bold), wording as on the "
                  "result slide", weight="bold")
        L.textbox(xr, y + 0.55, SLIDE_W - MX - xr, 0.45, "1–2 sentences of evidence with numbers (gray); every "
                  "number appears on an earlier slide", size=7)
    L.ymarks(1.3, 6.3)
    return L.done("summary")


FIGURES = {
    "layout_figure_conclusion": fig_layout_figure_conclusion,
    "layout_title": fig_layout_title,
    "layout_agenda": fig_layout_agenda,
    "layout_section_divider": fig_layout_section_divider,
    "layout_big_statement": fig_layout_big_statement,
    "layout_text_bullets": fig_layout_text_bullets,
    "layout_two_figures": fig_layout_two_figures,
    "layout_figure_takeaways": fig_layout_figure_takeaways,
    "layout_km_grid": fig_layout_km_grid,
    "layout_table": fig_layout_table,
    "layout_feature_table": fig_layout_feature_table,
    "layout_key_numbers": fig_layout_key_numbers,
    "layout_three_columns": fig_layout_three_columns,
    "layout_methods_flow": fig_layout_methods_flow,
    "layout_framework": fig_layout_framework,
    "layout_comparison": fig_layout_comparison,
    "layout_summary": fig_layout_summary,
}

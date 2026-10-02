"use strict";
// Agent loop: plan → use tools → observe → draft, with the callable tools alongside. Notes in notes/sAgentLoop.md.

module.exports = {
  section: "methods",
  order: 40,
  build(pres, n, P) {
    const { C, G } = P;
    const s = P.newSlide(pres, "Report-drafting Agent", n);
    P.pattern(s, "Pattern: agent loop");
    const cx = 3.7, cy = 3.35, rx = 2.2, ry = 1.55, isz = 0.65;
    const nodes = [
      ["lucide/list-checks", "1 · Plan", 0, -ry],
      ["lucide/toolbox", "2 · Use tools", rx, 0],
      ["lucide/scan-eye", "3 · Observe", 0, ry],
      ["lucide/message-square-text", "4 · Draft report", -rx, 0],
    ];
    const pos = nodes.map(([, , dx, dy]) => [cx + dx, cy + dy]);
    // Loop arrows between consecutive nodes (thin gray, along the sides of the diamond), kept clear of the
    // icons (centered 0.15 in above each node point) and of the labels below them.
    const loopArrow = (x1, y1, x2, y2) => P.arrow(s, x1, y1, x2, y2, { color: C.muted, width: 1.5 });
    loopArrow(cx + 0.75, cy - ry + 0.05, cx + rx - 0.2, cy - 0.6);
    loopArrow(cx + rx - 0.2, cy + 0.68, cx + 0.5, cy + ry - 0.45);
    loopArrow(cx - 0.5, cy + ry - 0.45, cx - rx + 0.2, cy + 0.68);
    loopArrow(cx - rx + 0.2, cy - 0.6, cx - 0.75, cy - ry + 0.05);
    nodes.forEach(([ic, lab], i) => {
      const [x, y] = pos[i];
      P.icon(s, ic, x - isz / 2, y - isz / 2 - 0.15, isz, "accent");
      P.text(s, x - 0.9, y + 0.22, 1.8, 0.35, { runs: [lab], align: "center" }, { fontSize: 14, bold: true, color: C.text });
    });
    P.icon(s, "lucide/bot", cx - 0.35, cy - 0.5, 0.7, "grey");
    P.text(s, cx - 0.8, cy + 0.22, 1.6, 0.35, { runs: ["LLM agent"], align: "center" }, { fontSize: 12, color: C.muted });
    // Tools panel
    const px = 7.4, pw = G.slideW - G.margin - px;
    P.text(s, px, 1.3, pw, 0.4, "Tools the agent can call", { fontSize: 18, bold: true, color: C.text });
    P.hline(s, px, px + pw, 1.78);
    const tools = [
      ["tabler/photo-scan", "VLM slide reader", "Describes a region the model attended to"],
      ["tabler/api", "Feature store", "Returns the patient's risk score and inputs"],
      ["lucide/book-open-text", "Guideline lookup", "Retrieves the reporting criteria text"],
    ];
    tools.forEach(([ic, head, body], i) => {
      const y = 1.98 + i * 0.95;
      P.icon(s, ic, px, y, 0.55, "grey");
      P.text(s, px + 0.8, y - 0.05, pw - 0.8, 0.8, [{ runs: [P.b(head)], after: 2 }, body], { fontSize: 14, color: C.text });
    });
    P.rect(s, px, 4.9, pw, 0.6, { fill: C.tint });
    P.text(s, px + 0.2, 4.9, pw - 0.4, 0.6, [{ runs: [P.b("Stop: "), "draft goes to a pathologist for sign-off"] }],
      { fontSize: 14, color: C.ink, valign: "middle" });
    P.conclusion(s, "The agent drafts the report; a pathologist signs it off, and every statement points to a tool output.",
      G.conclusion.yText);
    P.abbr(s, [["LLM", "large language model"], ["VLM", "vision-language model"]]);
    return s;
  },
};

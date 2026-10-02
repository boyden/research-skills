"use strict";
// Questions / thank you: the title-slide frame, no page number. Notes in notes/sThankYou.md.

module.exports = {
  section: "closing",
  order: 30,
  build(pres, n, P) {
    const { C } = P;
    const s = P.newSlide(pres, "Thank You", n, { chrome: false });
    P.titleFrame(s, 2.3, 1.5);
    P.pattern(s, "Pattern: questions / thank you");
    P.text(s, 0.95, 2.3, 11.2, 0.9, "Thank you", { fontSize: 44, bold: true, color: C.text, valign: "top" });
    P.text(s, 0.95, 3.2, 11.2, 0.55, "Questions and discussion", { fontSize: 24, color: C.muted });
    const cy = 4.45, cx = 0.95;
    P.icon(s, "lucide/message-square-text", cx, cy, 0.45, "grey");
    P.text(s, cx + 0.65, cy - 0.05, 6, 0.55, "contact@institution.org", { fontSize: 16, color: C.text, valign: "middle" });
    P.icon(s, "lucide/code", cx, cy + 0.65, 0.45, "grey");
    P.text(s, cx + 0.65, cy + 0.6, 6, 0.55, "github.com/<org>/<repo>", { fontSize: 16, color: C.text, valign: "middle" });
    return s;
  },
};

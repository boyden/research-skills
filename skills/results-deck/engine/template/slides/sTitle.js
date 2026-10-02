"use strict";
// Title slide: no topic-title chrome and no page number. Replace the placeholders; notes in notes/sTitle.md.
const { titleSlide } = require("./_lib/layouts");

module.exports = {
  section: "title",
  order: 10,
  build(pres, n, P) {
    const s = P.newSlide(pres, "Title", n, { chrome: false });
    titleSlide(s, {
      title: ["Recurrence-free Survival", "in the GBSG2 Trial"],
      subtitle: "A template deck built with the results-deck engine",
      presenter: ["Presenter Name, Role", "Department, Institution", "Meeting name · Month DD, YYYY"],
    });
    return s;
  },
};

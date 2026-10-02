"use strict";
module.exports = {
  section: "results", order: 30,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Nodes", n);
    P.conclusion(s, "As shown before, nodes dominate.");
    return s;
  },
};

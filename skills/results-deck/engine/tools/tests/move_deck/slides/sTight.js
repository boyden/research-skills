"use strict";
module.exports = {
  section: "results",
  order: 30.001,
  build(pres, n, P, ctx) {
    return P.newSlide(pres, "Tight", n);
  },
};

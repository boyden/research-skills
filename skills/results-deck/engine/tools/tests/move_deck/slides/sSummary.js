"use strict";
module.exports = {
  section: "summary",
  order: 10,
  build(pres, n, P, ctx) {
    return P.newSlide(pres, "Summary", n);
  },
};

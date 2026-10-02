"use strict";
module.exports = {
  section: "title",
  order: 10,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Title", n, { chrome: false });
    return s;
  },
};

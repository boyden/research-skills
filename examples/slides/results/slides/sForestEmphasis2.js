"use strict";
// Progressive emphasis, step 2 of 2: same figure, q < 0.05 rows highlighted (layout in _lib/results.js).
// Notes in notes/sForestEmphasis2.md.
const { forestEmphasis } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 90,
  build(pres, n, P) {
    return forestEmphasis(pres, n, P, 2);
  },
};

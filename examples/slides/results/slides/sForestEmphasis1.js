"use strict";
// Progressive emphasis, step 1 of 2: the whole forest plot (layout in _lib/results.js). Notes in notes/sForestEmphasis1.md.
const { forestEmphasis } = require("./_lib/results");

module.exports = {
  section: "results",
  order: 80,
  build(pres, n, P) {
    return forestEmphasis(pres, n, P, 1);
  },
};

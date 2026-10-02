'use strict';
module.exports = {
  section: 'results',
  order: 20,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, 'Clinical Factors', n);
    P.figure(s, 'survival_forest.png');
    P.conclusion(s, 'Positive nodes carry the largest effect (n = 686).');
    return s;
  },
};

"use strict";
// order: 99 in a comment is not the order; neither is section: "summary".
module.exports = {
  section: "results",
  order: 10,
  build(pres, n, P, ctx) {
    const s = P.newSlide(pres, "Recurrence-free Survival", n);
    P.figure(s, "survival_km.png");
    P.conclusion(s, "Treatment is associated with longer survival (n = 686).");
    s.addNotes("The next slide breaks this down by nodes.");
    return s;
  },
};

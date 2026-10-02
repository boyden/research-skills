"""Example figures for the shared rules (shared/figures.md, shared/tables.md, skills/results-deck/).

A plotting package in the engine layout (skills/results-deck/engine/SPEC.md §6), drawn by the generic entry
point; ``examples/`` has no deck.config.js, so the neutral theme is used and the PNGs go to examples/figures/::

    python skills/results-deck/engine/tools/plot.py examples                    # all figures
    python skills/results-deck/engine/tools/plot.py examples --only km_example  # just these
    python skills/results-deck/engine/tools/plot.py examples --list             # names and modules

Modules: ``style`` (theme, sizes, colors, apply_style, save), ``common`` (data loading and statistics),
and the figure modules ``layouts``, ``survival``, ``discrimination``, ``tables``.

All data are public: the GBSG2 breast cancer trial (686 women, recurrence-free survival) shipped with
lifelines (``lifelines.datasets.load_gbsg2``; Schumacher et al., J Clin Oncol 1994; Sauerbrei & Royston,
JRSS A 1999). Every figure is drawn at the size it occupies on a 13.333 x 7.5 in (16:9) slide, so a
point size here is the point size on screen. Needs matplotlib, numpy, pandas, lifelines, scikit-learn.
"""

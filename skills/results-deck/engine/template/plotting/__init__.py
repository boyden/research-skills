"""Figures of this deck (engine/SPEC.md §6), drawn by the engine's plotting entry point::

    python <engine>/tools/plot.py <deck>                       # every figure (after a theme change)
    python <engine>/tools/plot.py <deck> --only results_km     # just these: the form to use in parallel work
    python <engine>/tools/plot.py <deck> --list                # registered names and their modules

Modules: ``style`` (theme sizes, colors and fonts, ``apply_style()``, ``save()``), ``common`` (data loading
and statistics shared by the figure modules; registers no figures) and one figure module per deck section
(here ``results``). Each figure module ends with ``FIGURES = {name: callable}`` and ``INPUTS = [path, ...]``;
names start with the module (section) name so two modules never register the same name.

The template data are public: the GBSG2 breast cancer trial shipped with lifelines
(``lifelines.datasets.load_gbsg2``). Needs matplotlib, numpy, pandas and lifelines.
"""

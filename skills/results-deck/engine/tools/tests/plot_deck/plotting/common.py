"""Shared inputs of the fixture's figure modules; registers no figure."""

from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
INPUTS = [DATA / "cohort.csv"]

# Not a figure module: plot.py must not read this.
FIGURES = {"common_should_not_register": None}

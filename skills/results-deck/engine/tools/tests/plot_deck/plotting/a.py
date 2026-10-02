"""Section "alpha" figures of the fixture."""

import numpy as np
import matplotlib.pyplot as plt

from plotting import common, style


def alpha_line():
    fig, ax = plt.subplots(figsize=style.HALF)
    x = np.arange(5)
    ax.plot(x, x ** 2, color=style.INK)
    return fig, {"n": np.int64(5), "max": np.float64(16.0), "nan": float("nan"), **style.env_stats()}


def alpha_bar():
    fig, ax = plt.subplots(figsize=style.FULL)
    ax.bar(["a", "b"], [1, 2], color=style.INK)
    return fig, {"bars": np.array([1, 2]), "source": common.DATA / "cohort.csv"}


FIGURES = {"alpha_line": alpha_line, "alpha_bar": alpha_bar}
INPUTS = [common.DATA / "alpha.csv"]

"""Section "beta" figures of the fixture."""

import matplotlib.pyplot as plt

from plotting import style


def beta_scatter():
    fig, ax = plt.subplots(figsize=style.HALF)
    ax.scatter([0, 1, 2], [2, 0, 1], color=style.INK)
    return fig, {"points": 3, **style.env_stats()}


FIGURES = {"beta_scatter": beta_scatter}
INPUTS = ["data/beta.csv"]

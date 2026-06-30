from __future__ import annotations

import matplotlib.pyplot as plt


BG = "#F7F4EE"
INK = "#20242A"
MUTED = "#6F7782"
GRID = "#D8D2C7"
GOLD = "#C9A227"
BLUE = "#1F4E79"
RED = "#B94A48"
GREEN = "#2E8B57"

CONF_COLORS = {
    "UEFA": "#3568A8",
    "CONMEBOL": "#2E8B57",
    "CONCACAF": "#C9A227",
    "CAF": "#7B2D26",
    "AFC": "#8E44AD",
    "OFC": "#4C9BA8",
}


def apply_style():
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#A9A397",
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "axes.titleweight": "bold",
            "axes.titlesize": 18,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def stamp(fig, text="FIFA World Cup 2026 dataset · rendered by boxwheel/wc2026-viz-v2-tournament-flow"):
    fig.text(0.01, 0.012, text, ha="left", va="bottom", fontsize=7, color=MUTED)

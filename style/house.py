"""Shared house style for wc2026-viz-v2-tournament-flow."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

INK = "#1A1A1A"
SOFT_INK = "#404040"
PAPER = "#FBF8F2"
GRID = "#D9D2C5"
MUTED = "#8C8377"

GOLD = "#C9A227"
ROYAL = "#1F4E79"
ROSE = "#7B2D26"
TEAL = "#2E8B57"
LATE = "#F2D478"
STOPPAGE = "#B8B0A0"

CONF = {
    "UEFA": "#1F4E79",
    "CONMEBOL": "#2E8B57",
    "CONCACAF": "#C9A227",
    "AFC": "#7B2D26",
    "CAF": "#5C3A21",
    "OFC": "#8C5A8A",
}

COUNTRY = {"USA": "#9DB7C9", "MEX": "#CAA37A", "CAN": "#BFC9A6"}


def apply_style():
    sns.set_theme(context="talk", style="white")
    mpl.rcParams.update({
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "axes.edgecolor": SOFT_INK,
        "axes.labelcolor": SOFT_INK,
        "axes.titlecolor": INK,
        "xtick.color": SOFT_INK,
        "ytick.color": SOFT_INK,
        "text.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRID,
        "grid.alpha": 0.6,
        "axes.titleweight": "bold",
        "axes.titlesize": 18,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "font.family": ["DejaVu Sans"],
        "font.weight": "regular",
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })


def credit(fig, source="Kaggle: mominullptr/fifa-world-cup-2026-dataset",
           repo="boxwheel/wc2026-viz-v2-tournament-flow"):
    fig.text(
        0.99, 0.005, f"Source: {source}   ·   {repo}",
        ha="right", va="bottom", fontsize=8, color=MUTED, style="italic",
    )

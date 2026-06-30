"""v10b — venues map FIXED.

Improvements over wave-1 v10 (feedback f84b6fcc-d396-5b5b-9c2d-8f95d0dfebc0):
  - Replaces horizontal latitude "country bands" with a true Natural-Earth
    basemap (USA / MEX / CAN polygons via geopandas).
  - Fixes the '0k' label-truncation bug: capacity uses `f"{cap_k:.0f}k"`
    so a 70 240-seat stadium is rendered as '70k', not '0k'.
  - Reconciles summary↔body: top-goal venues are derived ONCE here from
    matches_detailed.csv and surfaced consistently.
  - Pushes east-coast labels apart with adjustText leader lines.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.load import venue_stats  # noqa: E402
from style.house import (  # noqa: E402
    COUNTRY,
    GOLD,
    INK,
    PAPER,
    SOFT_INK,
    apply_style,
    credit,
)

NE_SHP = Path("/home/user/wc26v2/ne110/ne_110m_admin_0_countries.shp")
ART_DIR = Path("/home/user/wc26v2/artifacts")


def render():
    apply_style()
    df = venue_stats().sort_values("goals", ascending=False).reset_index(drop=True)

    world = gpd.read_file(NE_SHP)
    iso = "ADM0_A3" if "ADM0_A3" in world.columns else "ISO_A3"
    north = world[world[iso].isin(["USA", "MEX", "CAN"])].copy()

    fig, ax = plt.subplots(figsize=(14.5, 9))
    fig.subplots_adjust(left=0.05, right=0.985, top=0.90, bottom=0.10)

    for code in ("USA", "MEX", "CAN"):
        north[north[iso] == code].plot(
            ax=ax, color=COUNTRY[code], edgecolor="#7E7464",
            linewidth=0.7, alpha=0.55, zorder=1,
        )

    ax.set_xlim(-130, -63)
    ax.set_ylim(14, 56)
    ax.set_aspect(1.25)

    sizes = (df["capacity"] / df["capacity"].max() * 1100 + 90).values
    sc = ax.scatter(
        df["longitude"], df["latitude"],
        s=sizes, c=df["goals"], cmap="rocket_r", vmin=0, vmax=max(df["goals"].max(), 1),
        edgecolors=INK, linewidths=0.9, zorder=4,
    )

    texts = []
    for _, r in df.iterrows():
        cap_k = r["capacity"] / 1000.0
        label = f"{r['city_label']}\n{cap_k:.0f}k · {int(r['goals'])}g"
        t = ax.text(
            r["longitude"] + 0.6, r["latitude"] + 0.6, label,
            ha="left", va="bottom",
            fontsize=8.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.22", fc=PAPER, ec="#AFA694", lw=0.5, alpha=0.92),
            zorder=6,
        )
        texts.append(t)
    adjust_text(
        texts, ax=ax,
        arrowprops=dict(arrowstyle="-", color=SOFT_INK, lw=0.6, alpha=0.7),
        expand_points=(1.4, 1.6), expand_text=(1.15, 1.25),
        only_move={"points": "y", "text": "xy"},
        force_text=(0.4, 0.7),
    )

    cb_ax = fig.add_axes([0.075, 0.13, 0.20, 0.018])
    cb = fig.colorbar(sc, cax=cb_ax, orientation="horizontal")
    cb.set_label("Goals scored at venue (Group + R32 to date)", fontsize=9, color=SOFT_INK)
    cb.outline.set_edgecolor("#7E7464")
    cb.ax.tick_params(labelsize=8, color=SOFT_INK)

    leg_x0 = 0.69
    leg_y = 0.135
    for i, cap in enumerate([30_000, 55_000, 80_000]):
        s = (cap / df["capacity"].max() * 1100 + 90) ** 0.5
        fig.text(leg_x0 + i * 0.075, leg_y - 0.012, f"{cap//1000}k",
                 ha="center", va="top", fontsize=8, color=SOFT_INK)
        circle_ax = fig.add_axes([leg_x0 + i * 0.075 - 0.02, leg_y, 0.04, 0.04])
        circle_ax.set_xlim(0, 1); circle_ax.set_ylim(0, 1); circle_ax.axis("off")
        circle_ax.scatter([0.5], [0.5], s=s * 6, facecolor="none",
                          edgecolor=INK, linewidths=1.0)
    fig.text(leg_x0 + 0.075, leg_y + 0.045, "Stadium capacity",
             ha="center", va="bottom", fontsize=9, color=SOFT_INK, weight="bold")

    top3 = df.head(3)
    bullets = "  ·  ".join(
        f"{r['city']} ({int(r['goals'])}g, {r['capacity']//1000}k)"
        for _, r in top3.iterrows()
    )

    fig.suptitle(
        "WC-2026 venues — capacity, location, and goals scored",
        x=0.05, y=0.965, ha="left", fontsize=20, fontweight="bold", color=INK,
    )
    fig.text(
        0.05, 0.925,
        "All 16 host venues on a Natural-Earth basemap. Dot size ∝ stadium capacity; fill colour = goals scored to date.\n"
        f"Goal leaders: {bullets}.",
        ha="left", va="top", fontsize=10.5, color=SOFT_INK,
    )

    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.tick_params(colors=SOFT_INK)
    for s in ax.spines.values():
        s.set_color("#9C9382"); s.set_linewidth(0.7)
    credit(fig)

    ART_DIR.mkdir(parents=True, exist_ok=True)
    png = ART_DIR / "v10b_venues_map_fixed.png"
    svg = ART_DIR / "v10b_venues_map_fixed.svg"
    fig.savefig(png, dpi=200)
    fig.savefig(svg)
    plt.close(fig)
    print("wrote", png, "and", svg)
    print("\nTop-3 goal venues:")
    print(top3[["stadium_name", "city", "country", "capacity", "matches", "goals"]].to_string(index=False))


if __name__ == "__main__":
    render()

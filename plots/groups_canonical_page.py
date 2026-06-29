"""groups_canonical_page — COMBINE of v01 + v04 for the WC-2026 group stage.

Realizes the COMBINE proposal in feedback nodes:
  - d2c7b5ad-8f9e-5167-b096-e4a5f677ae3c (on v01)
  - 8ae24f91-5aff-5679-80ee-274709065dcf (on v04)

Each of the 12 group panels stacks two stories vertically:
  TOP  — the 4×4 head-to-head score matrix from v04 (colored by home GD)
  BOT  — the diverging-bar standings from v01, with the wave-2 fix:
         the top-two rows get a faint green band so 'advanced' reads
         pre-attentively without the reader having to hunt a gold dot.

One artifact replaces two and answers both 'every game' and 'the verdict'.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.load import group_matches, teams  # noqa: E402
from transforms.groups import group_score_matrix, group_standings  # noqa: E402
from style.house import (  # noqa: E402
    INK, SOFT_INK, PAPER, GOLD, ROYAL, ROSE, TEAL, MUTED, apply_style, credit,
)

ART_DIR = Path("/home/user/wc26v2/artifacts")


def _panel_h2h(ax, gd_df, lbl_df, teams_in_grp, vmax=5):
    """Top sub-panel: 4x4 H2H matrix; row labels left, column labels above."""
    n = len(teams_in_grp)
    cmap = plt.get_cmap("vlag")
    short = lambda s: s if len(s) <= 9 else s[:8] + "."
    for i, h in enumerate(teams_in_grp):
        for j, a in enumerate(teams_in_grp):
            val = gd_df.loc[h, a]
            if i == j or (isinstance(val, float) and np.isnan(val)):
                ax.add_patch(mpatches.Rectangle(
                    (j, n - 1 - i), 1, 1,
                    facecolor="#EDE7DA", edgecolor=PAPER, linewidth=1.0))
                continue
            t = (val + vmax) / (2 * vmax)
            t = max(0.04, min(0.96, t))
            color = cmap(t)
            ax.add_patch(mpatches.Rectangle(
                (j, n - 1 - i), 1, 1,
                facecolor=color, edgecolor=PAPER, linewidth=1.2))
            text_color = "white" if abs(val) >= 3 else INK
            ax.text(j + 0.5, n - 1 - i + 0.5, lbl_df.loc[h, a],
                    ha="center", va="center", fontsize=8.5,
                    color=text_color, fontweight="bold")

    # Row labels (home team) on the left
    for i, h in enumerate(teams_in_grp):
        ax.text(-0.15, n - 1 - i + 0.5, short(h),
                ha="right", va="center", fontsize=7.5, color=SOFT_INK)
    # Column labels (away team) on top
    for j, a in enumerate(teams_in_grp):
        ax.text(j + 0.5, n + 0.15, short(a),
                ha="center", va="bottom", fontsize=7.5, color=SOFT_INK,
                rotation=30)

    ax.set_xlim(-2.4, n + 0.1)
    ax.set_ylim(0, n + 1.2)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _panel_bars(ax, group_df, max_g):
    """Bottom sub-panel: diverging GF / GA bars + advancement shading."""
    n = len(group_df)
    for idx, (_, r) in enumerate(group_df.iterrows()):
        y = n - 1 - idx
        if r["advanced"]:
            ax.add_patch(mpatches.Rectangle(
                (-max_g - 0.4, y - 0.42), 2 * max_g + 0.8, 0.85,
                facecolor="#D9E8D8", edgecolor="none", alpha=0.65, zorder=0))
        # GA (left, red)
        ax.barh(y, -r["ga"], height=0.55, color=ROSE, edgecolor="none", zorder=2)
        # GF (right, green)
        ax.barh(y, r["gf"], height=0.55, color=TEAL, edgecolor="none", zorder=2)
        # Team name on the left
        ax.text(-max_g - 0.6, y, f"{int(r['rank'])}. {r['team']}",
                ha="right", va="center", fontsize=8.5,
                color=INK if r["advanced"] else SOFT_INK,
                fontweight="bold" if r["advanced"] else "regular")
        # Points + GD on the right margin
        gd_sign = "+" if r["gd"] > 0 else ("±" if r["gd"] == 0 else "−")
        gd_str = f"{gd_sign}{abs(int(r['gd']))}"
        ax.text(max_g + 0.6, y, f"{int(r['pts'])} pts  ·  GD {gd_str}",
                ha="left", va="center", fontsize=8.5, color=INK,
                fontweight="bold" if r["advanced"] else "regular")

    ax.axvline(0, color=SOFT_INK, lw=0.7, zorder=3)
    ax.set_xlim(-max_g - 6.5, max_g + 7.5)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xticks([-max_g, 0, max_g])
    ax.set_xticklabels([f"{max_g} GA", "0", f"{max_g} GF"], fontsize=7.5, color=MUTED)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, pad=1)
    for s in ax.spines.values():
        s.set_visible(False)


def render():
    apply_style()
    matches = group_matches()
    t = teams()
    standings = group_standings(matches, t)
    groups = sorted(standings["group_letter"].unique())
    assert len(groups) == 12, groups

    max_g = int(standings[["gf", "ga"]].values.max())

    rows, cols = 4, 3
    fig = plt.figure(figsize=(22, 26))
    outer_gs = fig.add_gridspec(
        rows, cols, left=0.04, right=0.97, top=0.92, bottom=0.05,
        wspace=0.30, hspace=0.42,
    )

    for k, g in enumerate(groups):
        rr, cc = k // cols, k % cols
        inner = outer_gs[rr, cc].subgridspec(
            2, 1, height_ratios=[1.05, 0.95], hspace=0.18
        )
        ax_h2h = fig.add_subplot(inner[0, 0])
        ax_bar = fig.add_subplot(inner[1, 0])

        gd_df, lbl_df, order = group_score_matrix(matches, standings, g)
        _panel_h2h(ax_h2h, gd_df, lbl_df, order, vmax=5)

        grp = standings[standings["group_letter"] == g].sort_values("rank")
        _panel_bars(ax_bar, grp, max_g)

        # Panel title — sit just above the matrix block
        ax_h2h.set_title(f"Group {g}", loc="left", fontsize=15, color=INK,
                         fontweight="bold", pad=24)

    # Shared header
    fig.suptitle(
        "WC-2026 group stage — every game, every verdict",
        x=0.04, y=0.97, ha="left", fontsize=24, fontweight="bold", color=INK,
    )
    fig.text(
        0.04, 0.945,
        "Per panel: TOP — 4×4 head-to-head matrix (cell colour = home-team goal difference, vlag scale).   "
        "BOTTOM — points table with green / red bars for goals for / against; the soft green band marks "
        "the top-two advancers in each group.",
        ha="left", va="top", fontsize=12, color=SOFT_INK,
    )

    # Shared colour-legend (single, bottom)
    cax = fig.add_axes([0.41, 0.028, 0.18, 0.009])
    cmap = plt.get_cmap("vlag")
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    sm = ScalarMappable(norm=Normalize(-5, 5), cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("Cell colour: home goal difference (− away win, + home win)",
                 fontsize=8.5, color=SOFT_INK)
    cb.outline.set_edgecolor("#9C9382")
    cb.ax.tick_params(labelsize=7, color=SOFT_INK)

    credit(fig)

    ART_DIR.mkdir(parents=True, exist_ok=True)
    png = ART_DIR / "groups_canonical_page.png"
    svg = ART_DIR / "groups_canonical_page.svg"
    fig.savefig(png, dpi=200)
    fig.savefig(svg)
    plt.close(fig)
    print("wrote", png, "and", svg)


if __name__ == "__main__":
    render()

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
from adjustText import adjust_text
from matplotlib import patches
from matplotlib.collections import LineCollection

from data.loaders import (
    completed_matches,
    elo_expected_points,
    goal_events,
    group_standings,
    load_csv,
    long_match_results,
    match_elo_frame,
    save_both,
    team_lookup,
)
from style.house import BG, BLUE, CONF_COLORS, GOLD, GREEN, GRID, INK, MUTED, RED, apply_style, stamp


OUT = ROOT / "outputs"


def _title(fig, title, subtitle):
    fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.02, 0.952, subtitle, ha="left", va="top", fontsize=10, color=MUTED)


def goals_timeline_v2():
    apply_style()
    goals = goal_events()
    late = (goals["minute"] >= 75).mean()
    stoppage = (goals["minute"] > 90).sum()
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[4, 1], width_ratios=[5, 1], hspace=0.08, wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[0, 1], sharey=ax)
    ax_date = fig.add_subplot(gs[1, 0], sharex=ax)
    fig.add_subplot(gs[1, 1]).axis("off")
    ax.axhspan(90, 105, color="#D7D2C8", alpha=0.55, zorder=0)
    rng = np.random.default_rng(7)
    x = mdates.date2num(goals["date"]) + rng.uniform(-0.16, 0.16, len(goals))
    ax.scatter(x, goals["minute"], s=30, color=BLUE, alpha=0.72, edgecolor="white", linewidth=0.4)
    ax.set_ylim(0, 105)
    ax.set_ylabel("True goal minute")
    ax.grid(True, axis="y")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.tick_params(axis="x", labelbottom=False)
    ax.text(goals["date"].min(), 99, "stoppage time shown at true minute", color=MUTED, fontsize=9)
    bins = np.arange(0, 106, 1)
    counts, edges = np.histogram(goals["minute"], bins=bins)
    ax_hist.barh(edges[:-1], counts, height=0.92, color=GOLD, alpha=0.85)
    ax_hist.set_xlabel("goals")
    ax_hist.grid(False)
    ax_hist.tick_params(labelleft=False)
    daily = goals.groupby("date").size()
    ax_date.bar(daily.index, daily.values, width=0.72, color="#6D8BAA")
    ax_date.set_ylabel("goals/day")
    ax_date.grid(True, axis="y")
    for label in ax_date.get_xticklabels():
        label.set_rotation(35)
        label.set_ha("right")
    _title(
        fig,
        "Every WC-2026 goal by date and true minute",
        f"{late:.0%} of goals came from minute 75 onward; {stoppage} stoppage-time goals are no longer clamped into a fake 90' wall.",
    )
    stamp(fig)
    return save_both(fig, OUT / "v05b_goals_timeline_v2")


def elo_outliers_diptych():
    apply_style()
    team = elo_expected_points()
    match = match_elo_frame(True)
    over = team.iloc[0]
    under = team.iloc[-1]
    fig = plt.figure(figsize=(15, 8.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1], wspace=0.18)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    colors = np.where(match["upset"], GOLD, "#9FB0BC")
    mexico_mask = (match["home_code"].eq(over.code)) | (match["away_code"].eq(over.code))
    colors = np.where(mexico_mask, "#D9A441", colors)
    ax1.scatter(match["elo_gap"], match["gd"], s=52, c=colors, edgecolor="white", linewidth=0.5, alpha=0.9)
    coeff = np.polyfit(match["elo_gap"], match["gd"], 1)
    xx = np.linspace(match["elo_gap"].min() - 25, match["elo_gap"].max() + 25, 100)
    yy = coeff[0] * xx + coeff[1]
    resid = match["gd"] - (coeff[0] * match["elo_gap"] + coeff[1])
    sigma = resid.std()
    ax1.plot(xx, yy, color=INK, lw=1.4)
    ax1.fill_between(xx, yy - sigma, yy + sigma, color="#AAB7C2", alpha=0.28)
    texts = []
    for _, r in match.sort_values("abs_surprise", ascending=False).head(10).iterrows():
        texts.append(ax1.text(r.elo_gap, r.gd, r.label, fontsize=8, color=INK))
    adjust_text(texts, ax=ax1, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax1.axhline(0, color=GRID, lw=1)
    ax1.axvline(0, color=GRID, lw=1)
    ax1.set_xlabel("Home Elo minus away Elo")
    ax1.set_ylabel("Home goal difference")
    ax1.set_title("Match grain: who bent the Elo line?", loc="left")
    ax1.text(0.02, 0.03, f"OLS GD = {coeff[0]:.4f}×gap {coeff[1]:+.2f}; band = ±1σ", transform=ax1.transAxes, fontsize=8, color=MUTED)
    top = pd.concat([team.head(8), team.tail(8)]).sort_values("resid")
    bar_colors = [RED if v < 0 else GOLD for v in top["resid"]]
    ax2.barh(top["code"], top["resid"], color=bar_colors, alpha=0.9)
    ax2.axvline(0, color=INK, lw=1)
    for y, (_, r) in enumerate(top.iterrows()):
        ax2.text(r.resid + (0.08 if r.resid >= 0 else -0.08), y, f"{r.resid:+.1f}", va="center", ha="left" if r.resid >= 0 else "right", fontsize=8)
    ax2.set_xlabel("actual points - Elo expected points")
    ax2.set_title("Team grain: who over/under-performed?", loc="left")
    ax2.grid(True, axis="x")
    _title(
        fig,
        "Favorites held unevenly: match upsets and team residuals",
        f"{over.code} finished {over.resid:+.1f} points above Elo expectation while {under.code} finished {under.resid:+.1f}; the left panel replaces the old heuristic diagonal with a fitted line.",
    )
    stamp(fig)
    return save_both(fig, OUT / "elo_outliers_diptych")


def team_travel_paths():
    apply_style()
    matches = completed_matches(True)
    venues = load_csv("venues.csv").set_index("venue_id")
    teams = team_lookup()
    rows = []
    for _, r in matches.iterrows():
        for tid in [int(r.home_team_id), int(r.away_team_id)]:
            rows.append(
                {
                    "team_id": tid,
                    "code": teams.loc[tid, "fifa_code"],
                    "team": teams.loc[tid, "team_name"],
                    "date": pd.to_datetime(r.date),
                    "venue_id": int(r.venue_id),
                    "lat": venues.loc[int(r.venue_id), "latitude"],
                    "lon": venues.loc[int(r.venue_id), "longitude"],
                }
            )
    tv = pd.DataFrame(rows).sort_values(["team_id", "date"])

    def hav(a, b):
        r = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [a[0], a[1], b[0], b[1]])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        return 2 * r * np.arcsin(np.sqrt(h))

    totals = []
    fig = plt.figure(figsize=(15, 8.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.2, 1], wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    ax.set_xlim(-125, -65)
    ax.set_ylim(14, 51)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.grid(True)
    ax.add_patch(patches.Rectangle((-125, 24), 60, 25, facecolor="#E7E0D2", edgecolor="none", zorder=0))
    ax.add_patch(patches.Rectangle((-118, 14), 22, 12, facecolor="#DED7C8", edgecolor="none", zorder=0))
    ax.add_patch(patches.Rectangle((-141, 42), 76, 11, facecolor="#ECE6DA", edgecolor="none", zorder=0))
    ax.text(-104, 38, "USA", fontsize=20, color="#C8BFAF", ha="center", va="center", fontweight="bold")
    ax.text(-104, 21, "MEX", fontsize=15, color="#C8BFAF", ha="center", va="center", fontweight="bold")
    ax.text(-96, 47, "CAN", fontsize=15, color="#C8BFAF", ha="center", va="center", fontweight="bold")
    cmap = plt.get_cmap("tab20")
    for i, (tid, g) in enumerate(tv.groupby("team_id")):
        pts = list(zip(g["lat"], g["lon"]))
        dist = sum(hav(pts[j], pts[j + 1]) for j in range(len(pts) - 1))
        totals.append({"code": g["code"].iloc[0], "team": g["team"].iloc[0], "km": dist})
        ax.plot(g["lon"], g["lat"], color=cmap(i % 20), alpha=0.42, lw=1.2)
    v = load_csv("venues.csv")
    ax.scatter(v["longitude"], v["latitude"], s=v["capacity"] / 850, color=BLUE, alpha=0.75, edgecolor="white", lw=0.6)
    for _, r in v.iterrows():
        ax.text(r.longitude + 0.25, r.latitude + 0.2, r.city, fontsize=7, color=INK)
    top = pd.DataFrame(totals).sort_values("km", ascending=False).head(15).sort_values("km")
    axb.barh(top["code"], top["km"], color=GOLD)
    axb.set_xlabel("km between group venues")
    axb.grid(True, axis="x")
    axb.set_title("Largest group-stage travel loads", loc="left")
    _title(
        fig,
        "The 48-team group stage was also a travel draw",
        f"{top.iloc[-1].code} had the heaviest three-match venue path at about {top.iloc[-1].km:,.0f} km; paths use true venue lat/lon and great-circle distances.",
    )
    stamp(fig)
    return save_both(fig, OUT / "team_travel_paths")


def qualification_stripe():
    apply_style()
    s = group_standings().sort_values(["rank", "pts", "gd", "gf"], ascending=[True, False, False, False]).reset_index(drop=True)
    s["advance"] = s["rank"].le(2) | ((s["rank"].eq(3)) & (s.groupby("rank").cumcount() < 8))
    fig, ax = plt.subplots(figsize=(10, 14))
    y = np.arange(len(s))
    colors = np.where(s["advance"], GOLD, "#B8B2A8")
    ax.scatter(s["pts"], y, s=80 + 22 * s["gd"].clip(lower=0), color=colors, edgecolor="white", lw=0.6)
    for i, r in s.iterrows():
        ax.text(r.pts + 0.08, i, f"{r.code}  {r.pts} pts  GD {r.gd:+d}", va="center", fontsize=8)
    for cut, label in [(11.5, "12 group winners"), (23.5, "12 runners-up"), (31.5, "8 best third-place teams")]:
        ax.axhline(cut, color=INK, lw=1, ls="--")
        ax.text(0.05, cut - 0.3, label, fontsize=8, color=INK)
    ax.set_ylim(len(s), -1)
    ax.set_xlabel("group points")
    ax.set_yticks([])
    ax.set_title("Qualification stripe: the exact 32-team cutline", loc="left")
    _title(fig, "The new 48-team valve is a 32-line cut, not a ribbon knot", "Teams are sorted by finish tier and points/GD; gold marks the 32 advancers and the dashed lines expose where the format cuts.")
    stamp(fig)
    return save_both(fig, OUT / "qualification_stripe")


def treemap_v2():
    apply_style()
    goals = goal_events()
    teams = load_csv("teams.csv")
    counts = goals.groupby("team_id").size().rename("goals").reset_index()
    df = teams.merge(counts, on="team_id", how="left").fillna({"goals": 0})
    nonzero = df[df["goals"].gt(0)].copy()
    zero = df[df["goals"].eq(0)].copy()
    sizes = nonzero["goals"].to_numpy()
    fig, ax = plt.subplots(figsize=(15, 9))
    rects = squarify.squarify(squarify.normalize_sizes(sizes, 100, 82), 0, 12, 100, 82)
    colors = [CONF_COLORS.get(c, "#999999") for c in nonzero["confederation"]]
    for rect, (_, r), color in zip(rects, nonzero.iterrows(), colors):
        ax.add_patch(patches.Rectangle((rect["x"], rect["y"]), rect["dx"], rect["dy"], facecolor=color, alpha=0.82, edgecolor=BG, lw=1.2))
        if rect["dx"] * rect["dy"] > 65:
            ax.text(rect["x"] + rect["dx"] / 2, rect["y"] + rect["dy"] / 2, f"{r.fifa_code}\n{int(r.goals)}", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    if len(zero):
        w = 100 / len(zero)
        for i, (_, r) in enumerate(zero.iterrows()):
            ax.add_patch(patches.Rectangle((i * w, 0), w - 0.3, 8, facecolor=INK, edgecolor=BG, lw=1))
            ax.text(i * w + w / 2, 4, f"{r.fifa_code} · 0", ha="center", va="center", color="white", fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 96)
    ax.axis("off")
    _title(fig, "Confederation-to-team goals, with zero scorers visible", "Area encodes team goals once; alpha is no longer a second magnitude channel, and 0-goal teams get a dedicated visible strip.")
    stamp(fig)
    return save_both(fig, OUT / "v07b_treemap_v2")


def late_window_top_teams():
    apply_style()
    goals = goal_events()
    lr = long_match_results(True)
    late = goals[goals["minute"].ge(75)]
    scored = late.groupby("team_id").size().rename("late_for")
    rows = []
    for _, g in late.iterrows():
        m = lr[(lr["match_id"].eq(g.match_id)) & (lr["team_id"].eq(g.team_id))]
        if len(m):
            opp = int(m.iloc[0].opp_id)
            rows.append({"team_id": opp})
    conceded = pd.DataFrame(rows).groupby("team_id").size().rename("late_against") if rows else pd.Series(dtype=int)
    teams = load_csv("teams.csv")
    df = teams.merge(scored, on="team_id", how="left").merge(conceded, on="team_id", how="left").fillna(0)
    df["net_late"] = df["late_for"] - df["late_against"]
    top = df.sort_values(["late_for", "net_late"], ascending=False).head(14).sort_values("late_for")
    fig, ax = plt.subplots(figsize=(10, 8))
    y = np.arange(len(top))
    ax.barh(y - 0.16, top["late_for"], height=0.3, color=GOLD, label="scored 75+")
    ax.barh(y + 0.16, -top["late_against"], height=0.3, color=RED, label="conceded 75+")
    ax.set_yticks(y, top["fifa_code"])
    ax.axvline(0, color=INK, lw=1)
    ax.legend(frameon=False, loc="lower right")
    ax.set_xlabel("late goals, scored to the right and conceded to the left")
    ax.set_title("Late-window closers and leakier finishes", loc="left")
    _title(fig, "Who owned minutes 75+?", "A direct team ranking of the late-goal spike separates teams that closed games from teams that merely appeared in late drama.")
    stamp(fig)
    return save_both(fig, OUT / "late_window_top_teams")


def render(name: str):
    return globals()[name]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()
    png, svg = render(args.name)
    print(png)
    print(svg)

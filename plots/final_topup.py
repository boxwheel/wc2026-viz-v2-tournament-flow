from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.collections import LineCollection

from data.loaders import goal_events, group_standings, load_csv, long_match_results, save_both, team_lookup
from style.house import BG, BLUE, GOLD, GREEN, GRID, INK, MUTED, RED, apply_style, stamp

OUT = ROOT / "outputs"

WIN = "#25966F"
DRAW = "#A7A7A7"
LOSS = "#C92F4C"
PALE = "#EFE9DC"


def _title(fig, title: str, subtitle: str) -> None:
    fig.suptitle(title, x=0.02, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.02, 0.952, subtitle, ha="left", va="top", fontsize=10, color=MUTED)


def _actual_or_elo_winner(row: pd.Series, teams: pd.DataFrame) -> int:
    home = int(row.home_team_id)
    away = int(row.away_team_id)
    if row.status == "Completed" and pd.notna(row.home_score) and pd.notna(row.away_score):
        return home if float(row.home_score) > float(row.away_score) else away
    return home if float(teams.loc[home, "elo_rating"]) >= float(teams.loc[away, "elo_rating"]) else away


def bracket_with_elo_rail():
    apply_style()
    teams = team_lookup()
    r32 = load_csv("matches.csv")
    r32 = r32[r32["stage_id"].eq(2)].sort_values("match_id").reset_index(drop=True)
    elo_min = teams["elo_rating"].min()
    elo_max = teams["elo_rating"].max()
    cmap = plt.get_cmap("YlGnBu")
    norm = plt.Normalize(elo_min, elo_max)

    fig, (ax, rail) = plt.subplots(
        1,
        2,
        figsize=(16, 13),
        gridspec_kw={"width_ratios": [8.7, 1.2], "wspace": 0.04},
    )
    ax.set_xlim(0, 10.4)
    ax.set_ylim(-1, 33)
    ax.axis("off")

    x_round = [0.0, 2.55, 4.95, 7.15, 9.15]
    row_y = np.arange(31, -1, -1)
    slot_centers = {
        "R32": row_y,
        "R16": np.array([(row_y[i] + row_y[i + 3]) / 2 for i in range(0, 32, 4)]),
        "QF": np.array([(row_y[i] + row_y[i + 7]) / 2 for i in range(0, 32, 8)]),
        "SF": np.array([(row_y[i] + row_y[i + 15]) / 2 for i in range(0, 32, 16)]),
        "F": np.array([(row_y[0] + row_y[-1]) / 2]),
    }

    for x, label in zip(x_round, ["R32", "R16 path", "QF path", "SF path", "Final"]):
        ax.text(x + 0.02, 32.2, label, fontsize=12, fontweight="bold", color=INK)

    entrant_rows = []
    for i, r in r32.iterrows():
        y1, y2 = row_y[i * 2], row_y[i * 2 + 1]
        for side, tid, score, y in [
            ("home", int(r.home_team_id), r.home_score, y1),
            ("away", int(r.away_team_id), r.away_score, y2),
        ]:
            elo = float(teams.loc[tid, "elo_rating"])
            code = teams.loc[tid, "fifa_code"]
            face = cmap(norm(elo))
            won = _actual_or_elo_winner(r, teams) == tid
            alpha = 0.92 if won or r.status == "Scheduled" else 0.34
            ax.add_patch(
                patches.FancyBboxPatch(
                    (x_round[0], y - 0.46),
                    1.72,
                    0.82,
                    boxstyle="round,pad=0.015,rounding_size=0.04",
                    facecolor=face,
                    edgecolor="white",
                    lw=0.8,
                    alpha=alpha,
                )
            )
            text_color = "white" if norm(elo) > 0.53 else INK
            score_text = "" if pd.isna(score) else f"{int(score)}"
            ax.text(x_round[0] + 0.11, y - 0.03, code, va="center", fontsize=9.2, color=text_color, fontweight="bold")
            ax.text(x_round[0] + 1.58, y - 0.03, score_text, va="center", ha="right", fontsize=9, color=text_color, fontweight="bold")
            entrant_rows.append({"tid": tid, "code": code, "elo": elo, "y": y, "match": i})
        ax.text(x_round[0] + 1.9, (y1 + y2) / 2, pd.to_datetime(r.date).strftime("%b %d"), fontsize=7.5, color=MUTED, va="center")

    favorites = []
    for i, r in r32.iterrows():
        tid = _actual_or_elo_winner(r, teams)
        favorites.append({"tid": tid, "code": teams.loc[tid, "fifa_code"], "elo": float(teams.loc[tid, "elo_rating"]), "r32": i})

    # Seed-implied favorite rail: each unplayed favorite is advanced through the slot hierarchy.
    segments = []
    widths = []
    colors = []
    labels = []
    for fav in favorites:
        i = fav["r32"]
        elo = fav["elo"]
        y0 = row_y[i * 2] if int(r32.loc[i, "home_team_id"]) == fav["tid"] else row_y[i * 2 + 1]
        y1 = slot_centers["R16"][i // 2]
        y2 = slot_centers["QF"][i // 4]
        y3 = slot_centers["SF"][i // 8]
        y4 = slot_centers["F"][0]
        xs = [x_round[0] + 1.72, x_round[1], x_round[2], x_round[3], x_round[4]]
        ys = [y0, y1, y2, y3, y4]
        for a in range(len(xs) - 1):
            segments.append([(xs[a], ys[a]), (xs[a + 1], ys[a + 1])])
            widths.append(0.6 + 2.9 * norm(elo))
            colors.append(cmap(norm(elo)))
        if fav["code"] in {"FRA", "ARG", "ESP", "ENG", "BRA", "POR", "GER"}:
            labels.append((x_round[2] + 0.06, y2 + (0.22 if i % 2 == 0 else -0.22), fav["code"]))
    ax.add_collection(LineCollection(segments, colors=colors, linewidths=widths, alpha=0.18, zorder=0))

    # Empty future slots become labeled seed expressions instead of anonymous white space.
    for level, xs, centers, stride in [
        ("R16", x_round[1], slot_centers["R16"], 2),
        ("QF", x_round[2], slot_centers["QF"], 4),
        ("SF", x_round[3], slot_centers["SF"], 8),
    ]:
        for j, y in enumerate(centers):
            ax.add_patch(patches.Rectangle((xs - 0.1, y - 0.38), 1.55, 0.76, facecolor=BG, edgecolor=GRID, lw=0.8, zorder=1))
            lo = j * stride + 1
            hi = (j + 1) * stride
            ax.text(xs + 0.68, y, f"{level}: R32 {lo}-{hi}", ha="center", va="center", fontsize=7.2, color=MUTED, zorder=2)
    ax.add_patch(patches.Rectangle((x_round[4] - 0.08, slot_centers["F"][0] - 0.46), 1.25, 0.92, facecolor=BG, edgecolor=GOLD, lw=1.5))
    ax.text(x_round[4] + 0.54, slot_centers["F"][0], "Final", ha="center", va="center", fontsize=10, color=GOLD, fontweight="bold")
    for x, y, label in labels:
        ax.text(x, y, label, fontsize=7.6, color=INK, alpha=0.78)

    rail.set_facecolor(BG)
    rail.set_ylim(ax.get_ylim())
    rail.set_xlim(1550, 2050)
    rail.grid(True, axis="x", color=GRID, alpha=0.7)
    rail.set_xlabel("Elo", fontsize=9)
    rail.set_yticks([])
    for spine in ["left", "right", "top"]:
        rail.spines[spine].set_visible(False)
    entrants = pd.DataFrame(entrant_rows)
    rail.scatter(entrants["elo"], entrants["y"], s=44, color=BLUE, alpha=0.65, edgecolor="white", lw=0.5)
    for _, row in entrants.sort_values("elo", ascending=False).head(9).iterrows():
        rail.text(row.elo + 7, row.y, row.code, fontsize=7.4, va="center", color=INK)
    top_half = entrants[entrants["y"].ge(16)]["elo"].mean()
    bottom_half = entrants[entrants["y"].lt(16)]["elo"].mean()
    rail.axhline(15.0, color=GRID, lw=1)
    rail.text(1555, 15.35, f"half means: {top_half:.0f} / {bottom_half:.0f}", fontsize=7.2, color=MUTED)

    _title(
        fig,
        "Knockout bracket, filled by Elo gravity instead of empty slots",
        "R32 tiles use actual teams and scores; faint ribbons advance the actual/seed-implied Elo favorite through future slots, while the right rail exposes where high-Elo teams stack.",
    )
    stamp(fig)
    return save_both(fig, OUT / "bracket_with_elo_rail")


def _goal_minutes_by_match_team() -> dict[tuple[int, int], list[int]]:
    goals = goal_events()
    return goals.groupby(["match_id", "team_id"])["minute"].apply(lambda s: sorted(map(int, s))).to_dict()


def form_strips_with_minute_spark():
    apply_style()
    standings = group_standings().sort_values(["group", "rank"]).reset_index(drop=True)
    lr = long_match_results(True)
    lr["date"] = pd.to_datetime(lr["date"])
    minute_map = _goal_minutes_by_match_team()
    teams = team_lookup()

    fig, ax = plt.subplots(figsize=(21, 12))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis("off")

    cell_w = 0.26
    cell_h = 0.48
    x_gap = 0.03
    for gi, group in enumerate(list("ABCDEFGHIJKL")):
        col = gi
        ax.text(col + 0.02, 3.78, f"Group {group}", fontsize=12, fontweight="bold", color=INK)
        gteams = standings[standings["group"].eq(group)]
        for _, standing in gteams.iterrows():
            rank_idx = int(standing["rank"]) - 1
            base_y = 3.15 - rank_idx * 0.86
            ax.text(col + 0.02, base_y + 0.36, f"{int(standing['rank'])}", fontsize=8, color="white", ha="center", va="center", bbox=dict(boxstyle="round,pad=0.06", fc=GOLD if standing["rank"] <= 2 else MUTED, ec="none"))
            ax.text(col + 0.055, base_y + 0.36, standing["code"], fontsize=9, fontweight="bold", va="center")
            ax.text(col + 0.77, base_y + 0.36, f"{int(standing['pts'])} pts", fontsize=7.5, color=MUTED, ha="right", va="center")
            rows = lr[lr["team_id"].eq(int(standing["team_id"]))].sort_values("date").reset_index(drop=True)
            for mi, r in rows.iterrows():
                x = col + 0.02 + mi * (cell_w + x_gap)
                y = base_y - 0.18
                outcome = "W" if r.gf > r.ga else "D" if r.gf == r.ga else "L"
                face = WIN if outcome == "W" else DRAW if outcome == "D" else LOSS
                ax.add_patch(patches.Rectangle((x, y), cell_w, cell_h, facecolor=face, edgecolor=BG, lw=1.0))
                ax.text(x + 0.03, y + cell_h - 0.09, outcome, fontsize=8.5, color="white", fontweight="bold", va="top")
                ax.text(x + cell_w - 0.025, y + cell_h - 0.09, f"{int(r.gf)}-{int(r.ga)}", fontsize=6.6, color="white", ha="right", va="top")
                ax.plot([x + 0.035, x + cell_w - 0.035], [y + 0.235, y + 0.235], color="white", lw=0.8, alpha=0.62)
                for minute in minute_map.get((int(r.match_id), int(r.team_id)), []):
                    gx = x + 0.035 + (min(minute, 105) / 105) * (cell_w - 0.07)
                    ax.plot([gx, gx], [y + 0.245, y + 0.35], color=GOLD, lw=1.2)
                for minute in minute_map.get((int(r.match_id), int(r.opp_id)), []):
                    gx = x + 0.035 + (min(minute, 105) / 105) * (cell_w - 0.07)
                    ax.plot([gx, gx], [y + 0.12, y + 0.225], color="white", lw=1.1)
                ax.text(x + cell_w / 2, y + 0.035, f"v {r.opp_code}", fontsize=5.3, color="white", ha="center", va="bottom")

    ax.text(0.04, 0.11, "Gold ticks above each mini-axis are goals for; white ticks below are goals conceded. Each cell still carries result, score and opponent.", fontsize=8.2, color=MUTED)
    ax.plot([8.15, 8.85], [0.13, 0.13], color=INK, lw=0.8)
    ax.text(8.5, 0.18, "0' to 105'", fontsize=7.2, color=MUTED, ha="center")
    _title(
        fig,
        "Group form strips with each match's goal minutes embedded",
        "The old W/D/L grid becomes a 48-team set of tiny match stories: France and Argentina's perfect runs were steady, while several late saves and collapses are visible inside the cells.",
    )
    stamp(fig)
    return save_both(fig, OUT / "form_strips_with_minute_spark")


def render(name: str):
    return globals()[name]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=["bracket_with_elo_rail", "form_strips_with_minute_spark"])
    args = parser.parse_args()
    png, svg = render(args.name)
    print(png)
    print(svg)

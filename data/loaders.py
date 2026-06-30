from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("/home/user/research/fifa_data")


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def tables() -> dict[str, pd.DataFrame]:
    return {
        "matches": load_csv("matches.csv"),
        "matches_detailed": load_csv("matches_detailed.csv"),
        "events": load_csv("match_events.csv"),
        "teams": load_csv("teams.csv"),
        "venues": load_csv("venues.csv"),
        "players": load_csv("squads_and_players.csv"),
        "stats": load_csv("match_team_stats.csv"),
    }


def completed_matches(group_only: bool = False) -> pd.DataFrame:
    m = load_csv("matches.csv")
    out = m[m["status"].eq("Completed")].copy()
    if group_only:
        out = out[out["stage_id"].eq(1)].copy()
    return out


def team_lookup() -> pd.DataFrame:
    return load_csv("teams.csv").set_index("team_id")


def long_match_results(group_only: bool = True) -> pd.DataFrame:
    matches = completed_matches(group_only)
    teams = team_lookup()
    rows = []
    for _, r in matches.iterrows():
        h, a = int(r.home_team_id), int(r.away_team_id)
        hs, aw = int(r.home_score), int(r.away_score)
        for side, tid, opp, gf, ga in [
            ("home", h, a, hs, aw),
            ("away", a, h, aw, hs),
        ]:
            rows.append(
                {
                    "match_id": int(r.match_id),
                    "date": r.date,
                    "team_id": tid,
                    "team": teams.loc[tid, "team_name"],
                    "code": teams.loc[tid, "fifa_code"],
                    "group": teams.loc[tid, "group_letter"],
                    "conf": teams.loc[tid, "confederation"],
                    "elo": float(teams.loc[tid, "elo_rating"]),
                    "opp_id": opp,
                    "opp": teams.loc[opp, "team_name"],
                    "opp_code": teams.loc[opp, "fifa_code"],
                    "opp_elo": float(teams.loc[opp, "elo_rating"]),
                    "gf": gf,
                    "ga": ga,
                    "gd": gf - ga,
                    "pts": 3 if gf > ga else 1 if gf == ga else 0,
                    "side": side,
                    "venue_id": int(r.venue_id),
                }
            )
    return pd.DataFrame(rows)


def group_standings() -> pd.DataFrame:
    lr = long_match_results(True)
    s = (
        lr.groupby(["team_id", "team", "code", "group", "conf", "elo"], as_index=False)
        .agg(pts=("pts", "sum"), gf=("gf", "sum"), ga=("ga", "sum"), gd=("gd", "sum"))
        .sort_values(["group", "pts", "gd", "gf"], ascending=[True, False, False, False])
    )
    s["rank"] = s.groupby("group").cumcount() + 1
    return s


def elo_expected_points() -> pd.DataFrame:
    lr = long_match_results(True)
    lr["win_p"] = 1 / (1 + 10 ** (-(lr["elo"] - lr["opp_elo"]) / 400))
    # Conservative soccer expected-points proxy with a fixed draw mass.
    draw_p = 0.26
    lr["exp_pts"] = 3 * lr["win_p"] * (1 - draw_p) + draw_p
    return (
        lr.groupby(["team_id", "team", "code", "group", "conf", "elo"], as_index=False)
        .agg(pts=("pts", "sum"), exp_pts=("exp_pts", "sum"), gd=("gd", "sum"))
        .assign(resid=lambda d: d["pts"] - d["exp_pts"])
        .sort_values("resid", ascending=False)
    )


def match_elo_frame(group_only: bool = True) -> pd.DataFrame:
    matches = completed_matches(group_only)
    teams = team_lookup()
    rows = []
    for _, r in matches.iterrows():
        h, a = int(r.home_team_id), int(r.away_team_id)
        hs, aw = int(r.home_score), int(r.away_score)
        elo_gap = float(teams.loc[h, "elo_rating"] - teams.loc[a, "elo_rating"])
        gd = int(hs - aw)
        upset = (elo_gap < 0 and gd > 0) or (elo_gap > 0 and gd < 0)
        rows.append(
            {
                "match_id": int(r.match_id),
                "home": teams.loc[h, "team_name"],
                "away": teams.loc[a, "team_name"],
                "home_code": teams.loc[h, "fifa_code"],
                "away_code": teams.loc[a, "fifa_code"],
                "home_id": h,
                "away_id": a,
                "elo_gap": elo_gap,
                "gd": gd,
                "abs_surprise": abs(gd - elo_gap / 400),
                "label": f"{teams.loc[h, 'fifa_code']} {hs:.0f}-{aw:.0f} {teams.loc[a, 'fifa_code']}",
                "upset": upset,
            }
        )
    return pd.DataFrame(rows)


def goal_events() -> pd.DataFrame:
    events = load_csv("match_events.csv")
    goals = events[events["event_type"].eq("Goal")].copy()
    teams = team_lookup()
    matches = load_csv("matches.csv")[["match_id", "date", "venue_id", "home_team_id", "away_team_id"]]
    goals = goals.merge(matches, on="match_id", how="left")
    goals["team"] = goals["team_id"].map(teams["team_name"])
    goals["code"] = goals["team_id"].map(teams["fifa_code"])
    goals["conf"] = goals["team_id"].map(teams["confederation"])
    goals["date"] = pd.to_datetime(goals["date"])
    return goals


def save_both(fig, out_base: Path):
    out_base.parent.mkdir(parents=True, exist_ok=True)
    png = out_base.with_suffix(".png")
    svg = out_base.with_suffix(".svg")
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    return png, svg

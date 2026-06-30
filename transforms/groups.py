"""Group-stage frames: standings, rank, GD."""
from __future__ import annotations

import pandas as pd


def group_standings(matches: pd.DataFrame, teams: pd.DataFrame) -> pd.DataFrame:
    """Final group standings: pts, gf, ga, gd, rank within group.

    `matches` must include only Completed Group Stage rows.
    """
    rows = []
    for _, m in matches.iterrows():
        rows.append({"team": m["home_team_name"], "gf": m["home_score"], "ga": m["away_score"]})
        rows.append({"team": m["away_team_name"], "gf": m["away_score"], "ga": m["home_score"]})
    tg = pd.DataFrame(rows)
    tg["pts"] = tg.apply(lambda r: 3 if r["gf"] > r["ga"] else (1 if r["gf"] == r["ga"] else 0), axis=1)

    agg = tg.groupby("team", as_index=False).agg(
        pts=("pts", "sum"), gf=("gf", "sum"), ga=("ga", "sum")
    )
    agg["gd"] = agg["gf"] - agg["ga"]

    team_info = teams[["team_name", "group_letter", "confederation",
                       "fifa_ranking_pre_tournament", "elo_rating"]].rename(
        columns={"team_name": "team"}
    )
    out = agg.merge(team_info, on="team", how="left")
    out = out.sort_values(["group_letter", "pts", "gd", "gf"], ascending=[True, False, False, False])
    out["rank"] = out.groupby("group_letter").cumcount() + 1
    out["advanced"] = out["rank"] <= 2
    return out.reset_index(drop=True)


def group_score_matrix(matches: pd.DataFrame, standings: pd.DataFrame, group: str):
    """4x4 (home_team, away_team) score frame, ordered by final rank.

    Returns (df_gd, df_label) where df_gd has home-team GD per cell and
    df_label has the 'h-a' scoreline text. Diagonals are NaN/empty.
    """
    teams_in_grp = standings[standings["group_letter"] == group].sort_values("rank")["team"].tolist()
    n = len(teams_in_grp)
    import numpy as np
    gd = pd.DataFrame(np.nan, index=teams_in_grp, columns=teams_in_grp)
    lbl = pd.DataFrame("", index=teams_in_grp, columns=teams_in_grp)
    sub = matches[(matches["home_team_name"].isin(teams_in_grp)) &
                  (matches["away_team_name"].isin(teams_in_grp))]
    for _, m in sub.iterrows():
        h, a = m["home_team_name"], m["away_team_name"]
        gd.loc[h, a] = m["home_score"] - m["away_score"]
        lbl.loc[h, a] = f"{int(m['home_score'])}–{int(m['away_score'])}"
    return gd, lbl, teams_in_grp

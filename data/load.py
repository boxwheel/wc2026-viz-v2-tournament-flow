"""Tidy data frames for wc2026-viz-v2."""
from pathlib import Path
import pandas as pd

FIFA_DIR = Path("/home/user/research/fifa_data")


def matches() -> pd.DataFrame:
    return pd.read_csv(FIFA_DIR / "matches_detailed.csv")


def venues() -> pd.DataFrame:
    return pd.read_csv(FIFA_DIR / "venues.csv")


def teams() -> pd.DataFrame:
    return pd.read_csv(FIFA_DIR / "teams.csv")


def events() -> pd.DataFrame:
    return pd.read_csv(FIFA_DIR / "match_events.csv")


def team_stats() -> pd.DataFrame:
    return pd.read_csv(FIFA_DIR / "match_team_stats.csv")


def group_matches() -> pd.DataFrame:
    m = matches()
    return m[(m["stage_name"] == "Group Stage") & (m["status"] == "Completed")].copy()


def venue_stats() -> pd.DataFrame:
    """One row per venue with capacity, geography, match/goal totals at venue.

    Joins on (stadium_name) so venue_id stays attached, and the goal total
    is computed from matches_detailed.csv directly — not the previous
    'Earth City' rendering bug.
    """
    v = venues()
    m = matches()
    completed = m[m["status"] == "Completed"].copy()
    completed["total_goals"] = completed["home_score"] + completed["away_score"]
    agg = (
        completed.groupby("stadium_name")["total_goals"]
        .agg(matches="count", goals="sum")
        .reset_index()
    )
    out = v.merge(agg, on="stadium_name", how="left")
    out["matches"] = out["matches"].fillna(0).astype(int)
    out["goals"] = out["goals"].fillna(0).astype(int)
    out["city_label"] = out["city"]
    return out

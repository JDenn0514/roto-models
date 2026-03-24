"""Transform raw FanGraphs projections into normalized DataFrames for valuation."""

import numpy as np
import pandas as pd


# FanGraphs minpos codes → readable position names
MINPOS_MAP = {
    "C": "C",
    "1B": "1B",
    "2B": "2B",
    "3B": "3B",
    "SS": "SS",
    "LF": "OF",
    "CF": "OF",
    "RF": "OF",
    "OF": "OF",
    "DH": "DH",
}

# Scoring category columns
BATTING_CATS = ["R", "HR", "RBI", "SB", "AVG"]
PITCHING_CATS = ["W", "SV", "ERA", "WHIP", "SO"]


def _classify_pitcher_role(row: pd.Series) -> str:
    """Classify pitcher as SP or RP based on GS/G ratio."""
    g = row.get("G", 0) or 0
    gs = row.get("GS", 0) or 0
    if g == 0:
        return "P"
    if gs > 0 and gs / g > 0.5:
        return "SP"
    return "RP"


def _normalize_position(minpos) -> str:
    """Convert FanGraphs minpos to league-style position."""
    if pd.isna(minpos) or minpos is None:
        return "UT"
    pos = str(minpos).strip()
    return MINPOS_MAP.get(pos, pos)


def build_hitter_projections(bat_df: pd.DataFrame, system: str) -> pd.DataFrame:
    """Normalize batting projections."""
    df = bat_df.copy()

    # Belt-and-suspenders AL filter
    if "League" in df.columns:
        df = df[df["League"] == "AL"]

    out = pd.DataFrame({
        "player_name": df["PlayerName"],
        "team": df["Team"],
        "pos_type": "hitter",
        "position": df["minpos"].apply(_normalize_position) if "minpos" in df.columns else "UT",
        "projection_system": system,
        "fg_id": df["playerid"].astype(str) if "playerid" in df.columns else None,
        "mlbam_id": df["xMLBAMID"] if "xMLBAMID" in df.columns else np.nan,
        "PA": df["PA"],
        "AB": df["AB"],
        "IP": np.nan,
        "R": df["R"],
        "HR": df["HR"],
        "RBI": df["RBI"],
        "SB": df["SB"],
        "AVG": df["AVG"],
        "W": np.nan,
        "SV": np.nan,
        "ERA": np.nan,
        "WHIP": np.nan,
        "SO": np.nan,
    })

    return out.reset_index(drop=True)


def build_pitcher_projections(pit_df: pd.DataFrame, system: str) -> pd.DataFrame:
    """Normalize pitching projections."""
    df = pit_df.copy()

    if "League" in df.columns:
        df = df[df["League"] == "AL"]

    out = pd.DataFrame({
        "player_name": df["PlayerName"],
        "team": df["Team"],
        "pos_type": "pitcher",
        "position": df.apply(_classify_pitcher_role, axis=1),
        "projection_system": system,
        "fg_id": df["playerid"].astype(str) if "playerid" in df.columns else None,
        "mlbam_id": df["xMLBAMID"] if "xMLBAMID" in df.columns else np.nan,
        "PA": np.nan,
        "AB": np.nan,
        "IP": df["IP"],
        "R": np.nan,
        "HR": np.nan,
        "RBI": np.nan,
        "SB": np.nan,
        "AVG": np.nan,
        "W": df["W"],
        "SV": df["SV"],
        "ERA": df["ERA"],
        "WHIP": df["WHIP"],
        "SO": df["SO"],
    })

    return out.reset_index(drop=True)


def build_player_projections(
    batting_df: pd.DataFrame,
    pitching_df: pd.DataFrame,
    system: str,
    min_pa: int = 25,
    min_ip: int = 5,
) -> pd.DataFrame:
    """Normalize and combine batting + pitching projections.

    Applies minimum PA/IP thresholds to filter noise.
    """
    hitters = build_hitter_projections(batting_df, system)
    pitchers = build_pitcher_projections(pitching_df, system)

    # Apply minimum thresholds
    hitters = hitters[hitters["PA"] >= min_pa]
    pitchers = pitchers[pitchers["IP"] >= min_ip]

    combined = pd.concat([hitters, pitchers], ignore_index=True)
    return combined


def fill_minor_leaguers(
    primary_df: pd.DataFrame,
    dc_batting: pd.DataFrame,
    dc_pitching: pd.DataFrame,
    min_pa: int = 25,
    min_ip: int = 5,
) -> pd.DataFrame:
    """Add Depth Charts players not present in the primary system.

    These are typically prospects with small projected PA/IP.
    """
    dc = build_player_projections(dc_batting, dc_pitching, "dc_fill", min_pa, min_ip)

    # Find players in DC but not in primary (match by fg_id)
    existing_ids = set(primary_df["fg_id"].dropna())
    new_players = dc[~dc["fg_id"].isin(existing_ids)]

    if len(new_players) > 0:
        print(f"  Adding {len(new_players)} minor leaguers from Depth Charts")
        return pd.concat([primary_df, new_players], ignore_index=True)

    print("  No additional minor leaguers to add from Depth Charts")
    return primary_df

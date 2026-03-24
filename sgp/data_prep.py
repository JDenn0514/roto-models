"""Load historical standings, apply filters and exclusions."""

from pathlib import Path

import numpy as np
import pandas as pd

from sgp.config import SGPConfig

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_standings(config: SGPConfig) -> pd.DataFrame:
    """Load historical_standings.csv and exclude configured years."""
    df = pd.read_csv(DATA_DIR / "historical_standings.csv")
    df = df[~df["year"].isin(config.excluded_years)].copy()
    return df


def get_calibration_data(config: SGPConfig) -> pd.DataFrame:
    """Load standings filtered to calibration years (primary + optional supplemental)."""
    df = load_standings(config)
    df = df[df["year"].isin(config.active_years)].copy()
    return df


def detect_900ip_penalty(df: pd.DataFrame) -> pd.Series:
    """Identify teams that hit the 900 IP minimum penalty.

    These teams have exactly 0.0 points in BOTH ERA and WHIP but have
    non-null, reasonable ERA values (< 6.0). They were DQ'd from
    ERA/WHIP scoring, not just bad.
    """
    return (
        (df["ERA_pts"] == 0.0)
        & (df["WHIP_pts"] == 0.0)
        & df["ERA"].notna()
        & (df["ERA"] < 6.0)
    )


def get_category_data(
    df: pd.DataFrame, category: str, config: SGPConfig
) -> pd.DataFrame:
    """Get filtered data for a specific category.

    Applies per-category exclusion rules:
    - R, SO: exclude pre-2019 years (didn't exist)
    - ERA, WHIP: exclude 900 IP penalty teams
    """
    out = df.copy()

    # R and SO didn't exist before 2019
    if category in ("R", "SO"):
        out = out[out["year"] >= 2019]

    # Exclude 900 IP penalty teams from ERA/WHIP
    if category in ("ERA", "WHIP"):
        penalty_mask = detect_900ip_penalty(out)
        out = out[~penalty_mask]

    return out


def detect_punts(
    df: pd.DataFrame, category: str, config: SGPConfig
) -> pd.Series:
    """Flag teams punting a category (z-score below threshold).

    Only applies to counting stats. Returns boolean mask (True = punting).
    """
    if category in config.inverse_categories or category in config.rate_batting:
        return pd.Series(False, index=df.index)

    yearly_groups = df.groupby("year")[category]
    z_scores = yearly_groups.transform(lambda x: (x - x.mean()) / x.std())
    return z_scores < config.punt_z_threshold


def compute_time_weights(df: pd.DataFrame, config: SGPConfig) -> pd.Series:
    """Compute time-decay weights based on year.

    weight = decay_rate ^ (max_year - year)
    """
    if not config.time_decay:
        return pd.Series(1.0, index=df.index)

    max_year = df["year"].max()
    return config.time_decay_rate ** (max_year - df["year"])


def normalize_11_team_gaps(gaps: np.ndarray, n_teams: int, n_target: int = 10) -> np.ndarray:
    """Scale pairwise gaps from an N-team year to a target team count.

    Gaps are scaled by (n_target - 1) / (n_teams - 1).
    """
    if n_teams == n_target:
        return gaps
    return gaps * (n_target - 1) / (n_teams - 1)


def get_n_teams_by_year(df: pd.DataFrame) -> dict:
    """Return dict of {year: n_teams} from the data."""
    return df.groupby("year")["team"].nunique().to_dict()


def load_team_totals() -> pd.DataFrame:
    """Load team_totals.csv (year, team, total_ab, total_ip).

    Returns empty DataFrame if file doesn't exist.
    """
    path = DATA_DIR / "team_totals.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compute_league_mean_totals(config: SGPConfig) -> dict:
    """Compute league-wide mean AB and IP from team_totals.csv.

    Uses the config's active years (primary + supplemental if enabled).
    Falls back to config defaults if team_totals.csv doesn't exist.

    Returns dict with 'team_ab' and 'team_ip'.
    """
    tt = load_team_totals()
    if tt.empty:
        return {"team_ab": config.team_ab, "team_ip": config.team_ip}

    active = tt[tt["year"].isin(config.active_years)]
    if active.empty:
        return {"team_ab": config.team_ab, "team_ip": config.team_ip}

    return {
        "team_ab": float(active["total_ab"].mean()),
        "team_ip": float(active["total_ip"].mean()),
    }


def compute_team_averages(config: SGPConfig) -> dict:
    """Return team-level AB and IP for rate stat conversion.

    Loads actual values from team_totals.csv when available,
    falls back to config defaults otherwise.
    """
    return compute_league_mean_totals(config)


def load_rosters(config: SGPConfig | None = None) -> pd.DataFrame:
    """Load historical_rosters.csv."""
    path = DATA_DIR / "historical_rosters.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

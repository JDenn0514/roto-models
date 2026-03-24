"""Fetch projections from FanGraphs undocumented JSON API."""

import json
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "projections"

FANGRAPHS_API = "https://www.fangraphs.com/api/projections"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.fangraphs.com/projections",
}

# Expected columns per stat type (scoring categories + volume stats)
EXPECTED_BAT_COLS = {"PlayerName", "Team", "PA", "AB", "R", "HR", "RBI", "SB", "AVG"}
EXPECTED_PIT_COLS = {"PlayerName", "Team", "IP", "W", "SV", "ERA", "WHIP", "SO", "G", "GS"}


def _cache_path(system: str, stats: str, season: int) -> Path:
    return DATA_DIR / f"{system}_{stats}_{season}.csv"


def _cache_is_fresh(path: Path, max_age_hours: int = 24) -> bool:
    if not path.exists():
        return False
    import datetime
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return age.total_seconds() < max_age_hours * 3600


def fetch_projections(
    system: str,
    stats: str,
    league: str = "al",
    season: int = 2026,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Fetch projections from FanGraphs API. Cache to data/projections/.

    Parameters
    ----------
    system : str
        Projection system: "thebatx", "atc", "fangraphsdc"
    stats : str
        "bat" or "pit"
    league : str
        League filter (default "al")
    season : int
        Season year
    force_refresh : bool
        If True, bypass cache and re-fetch from API

    Returns
    -------
    pd.DataFrame
    """
    cache = _cache_path(system, stats, season)

    if not force_refresh and _cache_is_fresh(cache):
        print(f"  Loading cached {system} {stats} from {cache.name}")
        return pd.read_csv(cache)

    params = {
        "type": system,
        "stats": stats,
        "pos": "all",
        "team": "",
        "players": "0",
        "lg": league,
    }

    print(f"  Fetching {system} {stats} from FanGraphs API...")
    resp = requests.get(FANGRAPHS_API, params=params, headers=HEADERS, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(
            f"FanGraphs API returned {resp.status_code} for {system}/{stats}: {resp.text[:200]}"
        )

    data = resp.json()
    if not data:
        print(f"  WARNING: Empty response for {system}/{stats}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Validate expected columns
    expected = EXPECTED_BAT_COLS if stats == "bat" else EXPECTED_PIT_COLS
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns for {system}/{stats}: {missing}")

    # Cache to disk
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    print(f"  Cached {len(df)} rows to {cache.name}")

    return df


def fetch_all(
    season: int = 2026,
    force_refresh: bool = False,
    include_batx: bool = True,
) -> dict[str, pd.DataFrame]:
    """Fetch all projection sets needed for the pipeline.

    Returns dict keyed by "{system}_{stats}" → DataFrame.
    """
    fetches = [
        ("atc", "bat"),
        ("atc", "pit"),
        ("fangraphsdc", "bat"),
        ("fangraphsdc", "pit"),
    ]
    if include_batx:
        fetches.extend([
            ("thebatx", "bat"),
            ("thebatx", "pit"),
        ])

    results = {}
    for system, stats in fetches:
        df = fetch_projections(system, stats, season=season, force_refresh=force_refresh)
        results[f"{system}_{stats}"] = df
        time.sleep(1)  # rate limit

    return results

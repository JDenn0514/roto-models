"""Replacement level computation — per-category SGP baselines."""

import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import get_calibration_data, load_rosters
from sgp.sgp_calc import SGPResult


def _estimate_replacement_from_standings(
    df: pd.DataFrame, config: SGPConfig
) -> dict:
    """Estimate replacement-level stats from historical standings averages.

    Uses the heuristic that replacement level is roughly the bottom-of-roster
    starter — approximated as a fraction below the league average.

    For counting stats: replacement ~ league_mean / n_roster_slots
      (i.e., the per-slot contribution of an average team, discounted)
    For rate stats: replacement ~ league_mean (marginal player is roughly average)
    """
    repl = {}
    n_hitter_slots = config.hitter_slots
    n_pitcher_slots = config.pitcher_slots

    # Discount factor: replacement is worse than the average rostered player.
    # The average rostered player produces team_total / n_slots per slot.
    # Replacement is ~75% of that (bottom-of-roster contributor).
    discount = 0.75

    for cat in config.counting_batting:
        yearly_means = df.groupby("year")[cat].mean()
        league_mean = yearly_means.mean()
        per_slot = league_mean / n_hitter_slots
        repl[cat] = per_slot * discount

    for cat in config.counting_pitching:
        yearly_means = df.groupby("year")[cat].mean()
        league_mean = yearly_means.mean()
        per_slot = league_mean / n_pitcher_slots
        repl[cat] = per_slot * discount

    for cat in config.rate_batting:
        yearly_means = df.groupby("year")[cat].mean()
        league_mean = yearly_means.mean()
        # Replacement hitter AVG is below league average
        repl[cat] = league_mean - 0.015  # ~15 points below average

    for cat in config.rate_pitching:
        yearly_means = df.groupby("year")[cat].mean()
        league_mean = yearly_means.mean()
        if cat in config.inverse_categories:
            # Replacement pitcher ERA/WHIP is worse (higher) than average
            repl[cat] = league_mean * 1.10  # 10% worse
        else:
            repl[cat] = league_mean

    return repl


def compute_replacement_level(
    sgp_result: SGPResult,
    config: SGPConfig,
    standings_df: pd.DataFrame | None = None,
    replacement_stats: dict | None = None,
) -> dict:
    """Compute replacement-level SGP for hitters and pitchers.

    Priority:
    1. If replacement_stats provided, use those directly.
    2. Otherwise, estimate from historical standings averages.

    Returns dict with:
        - per-category replacement stat values
        - per-category replacement SGP contributions
        - total hitter and pitcher replacement SGP
    """
    if replacement_stats is not None:
        repl_stats = replacement_stats
    elif standings_df is not None:
        repl_stats = _estimate_replacement_from_standings(standings_df, config)
    else:
        raise ValueError("Need either standings_df or replacement_stats")

    # Convert replacement stats to SGP per category
    repl_sgp = {}
    for cat in config.all_batting:
        denom = sgp_result.denominators.get(cat)
        if denom is None or np.isnan(denom) or denom == 0:
            repl_sgp[cat] = 0.0
            continue

        if cat in config.rate_batting:
            # Rate stat: need to estimate replacement player's AB contribution
            # A replacement hitter gets ~350 AB (part-time / bench player)
            repl_ab = 350.0
            # SGP contribution relative to league-average rate
            # We use the league mean as the baseline for rate stats
            # The replacement player's marginal AVG contribution:
            # (repl_avg - league_avg) * (repl_ab / team_ab) / denom
            # But for replacement level calc, we just store the raw stat
            repl_sgp[cat] = repl_stats[cat] / denom if cat not in config.rate_batting else 0.0
        else:
            repl_sgp[cat] = repl_stats[cat] / denom

    for cat in config.all_pitching:
        denom = sgp_result.denominators.get(cat)
        if denom is None or np.isnan(denom) or denom == 0:
            repl_sgp[cat] = 0.0
            continue

        if cat in config.rate_pitching:
            repl_sgp[cat] = 0.0  # rate stats handled differently at player level
        elif cat in config.inverse_categories:
            # Lower is better — but this is a counting pitching cat, shouldn't happen
            repl_sgp[cat] = repl_stats[cat] / denom
        else:
            repl_sgp[cat] = repl_stats[cat] / denom

    hitter_repl_sgp = sum(repl_sgp[cat] for cat in config.all_batting)
    pitcher_repl_sgp = sum(repl_sgp[cat] for cat in config.all_pitching)

    return {
        "replacement_stats": repl_stats,
        "replacement_sgp": repl_sgp,
        "hitter_repl_sgp": hitter_repl_sgp,
        "pitcher_repl_sgp": pitcher_repl_sgp,
    }


def get_historical_reserve_counts(config: SGPConfig) -> pd.DataFrame | None:
    """Load roster data and compute DL+RES counts by year for diagnostics."""
    rosters = load_rosters(config)
    if rosters.empty:
        return None

    # Filter to primary calibration years
    rosters = rosters[rosters["year"].isin(config.primary_years)]

    # DL and RES are MLB-level reserves; FARM is minor leaguers (excluded)
    reserves = rosters[rosters["status"].isin(["dis", "res"])]

    # Classify as hitter or pitcher by position
    reserves = reserves.copy()
    reserves["is_pitcher"] = reserves["position"] == "P"

    counts = (
        reserves.groupby(["year", "is_pitcher"])
        .size()
        .unstack(fill_value=0)
        .rename(columns={False: "hitter_reserves", True: "pitcher_reserves"})
    )
    return counts

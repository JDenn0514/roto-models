"""Convert projected stats to dollar values using the calibrated SGP model."""

import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import get_calibration_data
from sgp.dollar_values import compute_dollar_values
from sgp.replacement import compute_replacement_level
from sgp.sgp_calc import compute_sgp, player_stat_to_sgp


def compute_projected_values(
    projections: pd.DataFrame,
    config: SGPConfig | None = None,
) -> pd.DataFrame:
    """Convert projected stats to dollar values using calibrated SGP model.

    Steps:
    1. Load SGP denominators (from composite config)
    2. Compute replacement level from historical standings
    3. For each player, compute per-category SGP
    4. Sum to total SGP
    5. Subtract replacement → PAR
    6. Convert PAR → dollar values

    Parameters
    ----------
    projections : DataFrame
        Output of build_player_projections() with columns:
        player_name, team, pos_type, position, PA, AB, IP,
        R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO
    config : SGPConfig, optional
        If None, uses SGPConfig.composite()

    Returns
    -------
    DataFrame with added columns: sgp_{cat}, total_sgp, par, dollar_value
    """
    if config is None:
        config = SGPConfig.composite()

    # Step 1: Compute SGP denominators from historical standings
    standings = get_calibration_data(config)
    sgp_result = compute_sgp(standings, config, bootstrap=False)

    print(f"\n  SGP denominators:")
    for cat, denom in sgp_result.denominators.items():
        print(f"    {cat}: {denom:.3f}")

    # Step 2: Compute replacement level
    replacement = compute_replacement_level(sgp_result, config, standings_df=standings)

    print(f"\n  Replacement SGP — hitters: {replacement['hitter_repl_sgp']:.2f}, "
          f"pitchers: {replacement['pitcher_repl_sgp']:.2f}")

    # Step 3: Compute per-category SGP for each player
    #
    # For counting stats, compute RAW SGP (stat / denom) with replacement_stat=0.
    # compute_dollar_values() handles the single replacement subtraction via PAR.
    #
    # For rate stats, pass the actual replacement rate as the baseline for marginal
    # contribution (volume-weighted). compute_replacement_level() returns 0 for
    # rate categories, so there's no double-subtraction.
    df = projections.copy()
    repl_stats = replacement["replacement_stats"]

    for cat in config.all_batting:
        col = f"sgp_{cat}"
        df[col] = 0.0

        hitter_mask = df["pos_type"] == "hitter"
        if not hitter_mask.any():
            continue

        is_rate = cat in config.rate_batting
        repl_for_sgp = repl_stats[cat] if is_rate else 0.0

        for idx in df.index[hitter_mask]:
            stat_val = df.at[idx, cat]
            if pd.isna(stat_val):
                continue

            ab_or_ip = df.at[idx, "AB"] if is_rate else None
            if is_rate and (pd.isna(ab_or_ip) or ab_or_ip == 0):
                continue

            df.at[idx, col] = player_stat_to_sgp(
                player_stat=stat_val,
                replacement_stat=repl_for_sgp,
                sgp_denom=sgp_result.denominators[cat],
                category=cat,
                config=config,
                player_ab_or_ip=ab_or_ip,
            )

    for cat in config.all_pitching:
        col = f"sgp_{cat}"
        df[col] = 0.0

        pitcher_mask = df["pos_type"] == "pitcher"
        if not pitcher_mask.any():
            continue

        is_rate = cat in config.rate_pitching
        repl_for_sgp = repl_stats[cat] if is_rate else 0.0

        for idx in df.index[pitcher_mask]:
            stat_val = df.at[idx, cat]
            if pd.isna(stat_val):
                continue

            ab_or_ip = df.at[idx, "IP"] if is_rate else None
            if is_rate and (pd.isna(ab_or_ip) or ab_or_ip == 0):
                continue

            df.at[idx, col] = player_stat_to_sgp(
                player_stat=stat_val,
                replacement_stat=repl_for_sgp,
                sgp_denom=sgp_result.denominators[cat],
                category=cat,
                config=config,
                player_ab_or_ip=ab_or_ip,
            )

    # Step 4: Sum to total SGP
    sgp_cols = [f"sgp_{cat}" for cat in config.all_categories]
    hitter_sgp_cols = [f"sgp_{cat}" for cat in config.all_batting]
    pitcher_sgp_cols = [f"sgp_{cat}" for cat in config.all_pitching]

    df["total_sgp"] = 0.0
    hitter_mask = df["pos_type"] == "hitter"
    pitcher_mask = df["pos_type"] == "pitcher"
    df.loc[hitter_mask, "total_sgp"] = df.loc[hitter_mask, hitter_sgp_cols].sum(axis=1)
    df.loc[pitcher_mask, "total_sgp"] = df.loc[pitcher_mask, pitcher_sgp_cols].sum(axis=1)

    # Steps 5-6: PAR and dollar values via existing function
    df = compute_dollar_values(df, replacement, config)

    return df

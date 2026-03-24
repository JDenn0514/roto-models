"""PAR → dollar conversion, inflation adjustment, keeper surplus."""

import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import load_rosters
from sgp.sgp_calc import SGPResult


def compute_dollar_values(
    player_sgp: pd.DataFrame,
    replacement: dict,
    config: SGPConfig,
) -> pd.DataFrame:
    """Convert player SGP totals to dollar values.

    Parameters
    ----------
    player_sgp : DataFrame with columns [player, pos_type, total_sgp]
        pos_type is 'hitter' or 'pitcher'.
    replacement : dict from compute_replacement_level()
    config : SGPConfig

    Returns DataFrame with added columns: par, dollar_value.
    """
    df = player_sgp.copy()

    # Compute PAR (Points Above Replacement)
    df["par"] = 0.0
    hitter_mask = df["pos_type"] == "hitter"
    pitcher_mask = df["pos_type"] == "pitcher"

    df.loc[hitter_mask, "par"] = (
        df.loc[hitter_mask, "total_sgp"] - replacement["hitter_repl_sgp"]
    )
    df.loc[pitcher_mask, "par"] = (
        df.loc[pitcher_mask, "total_sgp"] - replacement["pitcher_repl_sgp"]
    )

    # Only positive-PAR players get dollars
    positive_mask = df["par"] > 0
    total_positive_par = df.loc[positive_mask, "par"].sum()

    if total_positive_par == 0:
        df["dollar_value"] = 0.0
        return df

    # Count $1 minimum players: those with positive PAR but very small
    # We'll iterate: compute raw dollars, floor at $1, redistribute
    dollars_per_par = config.total_auction_pool / total_positive_par
    df["dollar_value"] = 0.0
    df.loc[positive_mask, "dollar_value"] = df.loc[positive_mask, "par"] * dollars_per_par

    # Apply $1 minimum and redistribute
    df = _apply_minimum_bid(df, config)

    return df


def _apply_minimum_bid(df: pd.DataFrame, config: SGPConfig) -> pd.DataFrame:
    """Floor dollar values at $1 for positive-PAR players, redistribute."""
    positive_mask = df["par"] > 0

    for _ in range(10):  # iterate until stable
        below_min = positive_mask & (df["dollar_value"] < 1.0) & (df["dollar_value"] > 0)
        if below_min.sum() == 0:
            break

        # Floor these at $1
        surplus_needed = (1.0 - df.loc[below_min, "dollar_value"]).sum()
        df.loc[below_min, "dollar_value"] = 1.0

        # Redistribute from players above $1
        above_min = positive_mask & (df["dollar_value"] > 1.0)
        if above_min.sum() == 0:
            break
        total_above = df.loc[above_min, "dollar_value"].sum()
        scale = (total_above - surplus_needed) / total_above
        df.loc[above_min, "dollar_value"] *= scale

    return df


def _apply_minimum_bid_group(
    df: pd.DataFrame, mask: pd.Series, pool: float, value_col: str
) -> pd.DataFrame:
    """Floor dollar values at $1 for a subset of positive-PAR players."""
    positive = mask & (df[value_col] > 0)

    for _ in range(10):
        below_min = positive & (df[value_col] < 1.0) & (df[value_col] > 0)
        if below_min.sum() == 0:
            break
        surplus_needed = (1.0 - df.loc[below_min, value_col]).sum()
        df.loc[below_min, value_col] = 1.0

        above_min = positive & (df[value_col] > 1.0)
        if above_min.sum() == 0:
            break
        total_above = df.loc[above_min, value_col].sum()
        scale = (total_above - surplus_needed) / total_above
        df.loc[above_min, value_col] *= scale

    return df


def compute_split_pool_values(
    player_sgp: pd.DataFrame,
    replacement: dict,
    config: SGPConfig,
    hitter_pct: float = 0.63,
) -> pd.DataFrame:
    """Convert player SGP to dollar values using separate hitter/pitcher pools.

    Instead of a single dollars-per-PAR rate, allocates a fixed percentage of
    the auction pool to hitters and the rest to pitchers, then computes
    dollars-per-PAR independently within each pool.

    Parameters
    ----------
    player_sgp : DataFrame with columns [player, pos_type, total_sgp]
    replacement : dict from compute_replacement_level()
    config : SGPConfig
    hitter_pct : fraction of auction pool allocated to hitters (default 0.63)

    Returns DataFrame with added columns: par, auction_value.
    """
    df = player_sgp.copy()

    # Compute PAR (same as single-pool)
    df["par"] = 0.0
    hitter_mask = df["pos_type"] == "hitter"
    pitcher_mask = df["pos_type"] == "pitcher"

    df.loc[hitter_mask, "par"] = (
        df.loc[hitter_mask, "total_sgp"] - replacement["hitter_repl_sgp"]
    )
    df.loc[pitcher_mask, "par"] = (
        df.loc[pitcher_mask, "total_sgp"] - replacement["pitcher_repl_sgp"]
    )

    df["auction_value"] = 0.0

    # Hitter pool
    hitter_pool = config.total_auction_pool * hitter_pct
    h_positive = hitter_mask & (df["par"] > 0)
    h_total_par = df.loc[h_positive, "par"].sum()
    if h_total_par > 0:
        h_dpp = hitter_pool / h_total_par
        df.loc[h_positive, "auction_value"] = df.loc[h_positive, "par"] * h_dpp
        df = _apply_minimum_bid_group(df, hitter_mask, hitter_pool, "auction_value")

    # Pitcher pool
    pitcher_pool = config.total_auction_pool * (1.0 - hitter_pct)
    p_positive = pitcher_mask & (df["par"] > 0)
    p_total_par = df.loc[p_positive, "par"].sum()
    if p_total_par > 0:
        p_dpp = pitcher_pool / p_total_par
        df.loc[p_positive, "auction_value"] = df.loc[p_positive, "par"] * p_dpp
        df = _apply_minimum_bid_group(df, pitcher_mask, pitcher_pool, "auction_value")

    return df


def compute_hitter_pitcher_split(df: pd.DataFrame) -> dict:
    """Compute the hitter/pitcher dollar split from valued players."""
    positive = df[df["dollar_value"] > 0]
    hitter_dollars = positive.loc[positive["pos_type"] == "hitter", "dollar_value"].sum()
    pitcher_dollars = positive.loc[positive["pos_type"] == "pitcher", "dollar_value"].sum()
    total = hitter_dollars + pitcher_dollars

    if total == 0:
        return {"hitter_pct": 0.0, "pitcher_pct": 0.0, "total": 0.0}

    return {
        "hitter_pct": hitter_dollars / total * 100,
        "pitcher_pct": pitcher_dollars / total * 100,
        "hitter_dollars": hitter_dollars,
        "pitcher_dollars": pitcher_dollars,
        "total": total,
    }


def compute_inflation(
    base_values: pd.DataFrame,
    keeper_data: pd.DataFrame,
    config: SGPConfig,
) -> tuple[float, pd.DataFrame]:
    """Compute inflation factor and adjusted dollar values.

    Steps:
    1. Identify keepers (contract year b or c)
    2. Sum keeper salaries (cost) and base values (worth)
    3. inflation = (pool - keeper_salary) / (pool - keeper_value)
    4. Inflate non-keeper values

    Returns (inflation_factor, dataframe with inflated values).
    """
    if keeper_data.empty:
        return 1.0, base_values.copy()

    # Identify keepers: contract_year in ('b', 'c', 'br', 'cr')
    keeper_contracts = keeper_data[
        keeper_data["contract_year"].str.startswith(("b", "c"), na=False)
    ].copy()

    if keeper_contracts.empty:
        return 1.0, base_values.copy()

    # Match keepers to base values by player name
    # This requires player_name in both dataframes
    if "player_name" not in base_values.columns:
        return 1.0, base_values.copy()

    merged = base_values.merge(
        keeper_contracts[["player_name", "salary"]].rename(
            columns={"salary": "keeper_salary"}
        ),
        on="player_name",
        how="left",
    )
    merged["is_keeper"] = merged["keeper_salary"].notna()

    keeper_total_salary = merged.loc[merged["is_keeper"], "keeper_salary"].sum()
    keeper_total_value = merged.loc[merged["is_keeper"], "dollar_value"].sum()

    pool = config.total_auction_pool
    remaining_pool = pool - keeper_total_salary
    remaining_value = pool - keeper_total_value

    if remaining_value <= 0:
        inflation = 1.0
    else:
        inflation = remaining_pool / remaining_value

    result = merged.copy()
    result["inflated_value"] = result["dollar_value"]
    non_keeper_mask = ~result["is_keeper"]
    result.loc[non_keeper_mask, "inflated_value"] = (
        result.loc[non_keeper_mask, "dollar_value"] * inflation
    )

    if config.inflation_model == "tiered" and non_keeper_mask.sum() > 0:
        result = _apply_tiered_inflation(result, inflation, non_keeper_mask)

    return inflation, result


def _apply_tiered_inflation(
    df: pd.DataFrame, base_inflation: float, non_keeper_mask: pd.Series
) -> pd.DataFrame:
    """Apply tiered inflation: top players inflate more."""
    non_keepers = df.loc[non_keeper_mask].copy()
    if non_keepers.empty:
        return df

    # Rank non-keepers by base dollar value
    ranks = non_keepers["dollar_value"].rank(pct=True)

    # Tiered multipliers on the inflation factor
    tier_mult = pd.Series(1.0, index=ranks.index)
    tier_mult[ranks >= 0.9] = 1.2   # top 10% inflate more
    tier_mult[(ranks >= 0.5) & (ranks < 0.9)] = 1.0  # middle
    tier_mult[ranks < 0.5] = 0.8   # bottom inflate less

    # Scale so total inflated value matches what uniform would produce
    uniform_total = non_keepers["dollar_value"].sum() * base_inflation
    tiered_raw = non_keepers["dollar_value"] * base_inflation * tier_mult
    if tiered_raw.sum() > 0:
        scale = uniform_total / tiered_raw.sum()
        tiered_raw *= scale

    df.loc[non_keeper_mask, "inflated_value"] = tiered_raw.values
    return df


def compute_keeper_surplus(
    valued_players: pd.DataFrame,
    roster_data: pd.DataFrame,
) -> pd.DataFrame:
    """Compute keeper surplus = base_value - salary for kept players."""
    if "player_name" not in valued_players.columns:
        return pd.DataFrame()

    keepers = roster_data[
        roster_data["contract_year"].str.startswith(("b", "c"), na=False)
    ].copy()

    if keepers.empty:
        return pd.DataFrame()

    merged = keepers.merge(
        valued_players[["player_name", "dollar_value"]],
        on="player_name",
        how="inner",
    )
    merged["surplus"] = merged["dollar_value"] - merged["salary"]
    return merged


def compute_historical_spending_split(config: SGPConfig) -> pd.DataFrame | None:
    """Compute actual historical hitter/pitcher spending split from rosters."""
    rosters = load_rosters(config)
    if rosters.empty:
        return None

    active = rosters[rosters["status"] == "act"].copy()
    active["is_pitcher"] = active["position"] == "P"

    splits = []
    for year, year_df in active.groupby("year"):
        hitter_spend = year_df.loc[~year_df["is_pitcher"], "salary"].sum()
        pitcher_spend = year_df.loc[year_df["is_pitcher"], "salary"].sum()
        total = hitter_spend + pitcher_spend
        if total > 0:
            splits.append({
                "year": year,
                "hitter_spend": hitter_spend,
                "pitcher_spend": pitcher_spend,
                "hitter_pct": hitter_spend / total * 100,
            })

    return pd.DataFrame(splits) if splits else None

"""Core MSP (Marginal Standings Points) computation.

Computes how many standings points a team gains by adding each available
free agent, given their keeper roster and projected league standings.

Pipeline:
    1. compute_keeper_baselines — sum keeper stats per team
    2. compute_fill_rates — per-dollar stat rates from the FA pool
    3. project_full_season — keeper + fill → projected team stats
    4. rank_standings — rank teams 1-10 per category, sum standings points
    5. compute_msp — marginal standings points per available player
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from targeting.name_match import build_name_index, match_name


# League constants (from sgp/config.py)
N_TEAMS = 10
HITTER_SLOTS = 15
PITCHER_SLOTS = 11
BUDGET_PER_TEAM = 360

COUNTING_BATTING = ["R", "HR", "RBI", "SB"]
COUNTING_PITCHING = ["W", "SV", "SO"]
RATE_BATTING = ["AVG"]
RATE_PITCHING = ["ERA", "WHIP"]
INVERSE_CATEGORIES = ["ERA", "WHIP"]

ALL_CATEGORIES = COUNTING_BATTING + RATE_BATTING + COUNTING_PITCHING + RATE_PITCHING


@dataclass
class MSPConfig:
    """Configuration for the MSP targeting model."""

    baseline_type: str = "proportional_fill"  # keeper_only, proportional_fill, historical_average
    fill_discount: float = 0.75  # fraction of per-dollar rates teams actually capture
    budget_displacement: bool = True  # reduce fill when adding a player

    def label(self) -> str:
        return f"{self.baseline_type}_fd{self.fill_discount}_disp{self.budget_displacement}"


def compute_keeper_baselines(
    keepers: pd.DataFrame,
    valuations: pd.DataFrame,
) -> pd.DataFrame:
    """Sum keeper projected stats per team.

    Args:
        keepers: Pre-auction keeper roster with columns [team, player_name, salary, position, status].
        valuations: Player valuations with stat columns + player_name.

    Returns:
        DataFrame with one row per team: counting stats summed, rate stats
        volume-weighted, plus keeper_AB, keeper_IP, n_keeper_hitters,
        n_keeper_pitchers, keeper_salary.
    """
    proj_index = build_name_index(valuations["player_name"].unique().tolist())

    records = []
    for team, group in keepers.groupby("team"):
        stats = {cat: 0.0 for cat in COUNTING_BATTING + COUNTING_PITCHING}
        total_ab = 0.0
        total_ip = 0.0
        weighted_avg = 0.0
        weighted_era = 0.0
        weighted_whip = 0.0
        n_hitters = 0
        n_pitchers = 0
        keeper_salary = group["salary"].sum()

        for _, row in group.iterrows():
            matched = match_name(row["player_name"], proj_index)
            if matched is None:
                # Unmatched keeper: count roster slot but no stats
                if row.get("position", "") == "P":
                    n_pitchers += 1
                else:
                    n_hitters += 1
                continue

            player = valuations[valuations["player_name"] == matched]
            if player.empty:
                if row.get("position", "") == "P":
                    n_pitchers += 1
                else:
                    n_hitters += 1
                continue
            p = player.iloc[0]

            is_pitcher = p.get("is_pitcher", p.get("pos_type") == "pitcher")
            if is_pitcher:
                n_pitchers += 1
                ip = p.get("IP", 0) or 0
                total_ip += ip
                for cat in COUNTING_PITCHING:
                    stats[cat] += p.get(cat, 0) or 0
                weighted_era += (p.get("ERA", 0) or 0) * ip
                weighted_whip += (p.get("WHIP", 0) or 0) * ip
            else:
                n_hitters += 1
                ab = p.get("AB", 0) or 0
                total_ab += ab
                for cat in COUNTING_BATTING:
                    stats[cat] += p.get(cat, 0) or 0
                weighted_avg += (p.get("AVG", 0) or 0) * ab

        record = {"team": team, **stats}
        record["AVG"] = weighted_avg / total_ab if total_ab > 0 else 0.0
        record["ERA"] = weighted_era / total_ip if total_ip > 0 else 4.50
        record["WHIP"] = weighted_whip / total_ip if total_ip > 0 else 1.30
        record["keeper_AB"] = total_ab
        record["keeper_IP"] = total_ip
        record["n_keeper_hitters"] = n_hitters
        record["n_keeper_pitchers"] = n_pitchers
        record["keeper_salary"] = keeper_salary
        records.append(record)

    return pd.DataFrame(records)


def compute_fill_rates(
    valuations: pd.DataFrame,
    keeper_names: set[str],
) -> dict:
    """Compute per-dollar stat rates from the non-keeper free agent pool.

    Returns dict with per-dollar rates for each stat + AB_per_dollar, IP_per_dollar.
    """
    # Identify free agents: not keepers and with positive value
    fa = valuations[~valuations["player_name"].isin(keeper_names)].copy()
    fa = fa[fa.get("dollar_value", fa.get("production_value", pd.Series(dtype=float))) > 0]

    if fa.empty:
        return {cat: 0.0 for cat in ALL_CATEGORIES}

    # Determine dollar value column
    dv_col = "dollar_value" if "dollar_value" in fa.columns else "production_value"
    total_dollars = fa[dv_col].sum()

    if total_dollars <= 0:
        return {cat: 0.0 for cat in ALL_CATEGORIES}

    rates = {}
    for cat in COUNTING_BATTING + COUNTING_PITCHING:
        rates[cat] = fa[cat].fillna(0).sum() / total_dollars

    # Volume per dollar for rate stat weighting
    is_pitcher = fa.get("is_pitcher", fa.get("pos_type") == "pitcher")
    hitters = fa[~is_pitcher] if isinstance(is_pitcher, pd.Series) else fa[fa["pos_type"] != "pitcher"]
    pitchers = fa[is_pitcher] if isinstance(is_pitcher, pd.Series) else fa[fa["pos_type"] == "pitcher"]

    hitter_dollars = hitters[dv_col].sum()
    pitcher_dollars = pitchers[dv_col].sum()

    rates["AB_per_dollar"] = hitters["AB"].fillna(0).sum() / hitter_dollars if hitter_dollars > 0 else 0
    rates["IP_per_dollar"] = pitchers["IP"].fillna(0).sum() / pitcher_dollars if pitcher_dollars > 0 else 0

    # Pool-average rate stats (volume-weighted)
    total_ab = hitters["AB"].fillna(0).sum()
    total_ip = pitchers["IP"].fillna(0).sum()
    rates["pool_AVG"] = (hitters["AB"].fillna(0) * hitters["AVG"].fillna(0)).sum() / total_ab if total_ab > 0 else 0.260
    rates["pool_ERA"] = (pitchers["IP"].fillna(0) * pitchers["ERA"].fillna(0)).sum() / total_ip if total_ip > 0 else 4.20
    rates["pool_WHIP"] = (pitchers["IP"].fillna(0) * pitchers["WHIP"].fillna(0)).sum() / total_ip if total_ip > 0 else 1.25

    return rates


def project_full_season(
    baselines: pd.DataFrame,
    fill_rates: dict,
    config: MSPConfig,
) -> pd.DataFrame:
    """Project full-season team stats by adding fill production to keeper baselines.

    Returns DataFrame with one row per team, columns for all categories + team_AB, team_IP.
    """
    proj = baselines.copy()

    for _, row in proj.iterrows():
        idx = proj.index[proj["team"] == row["team"]][0]
        remaining_hitter_slots = HITTER_SLOTS - row["n_keeper_hitters"]
        remaining_pitcher_slots = PITCHER_SLOTS - row["n_keeper_pitchers"]
        remaining_budget = BUDGET_PER_TEAM - row["keeper_salary"]
        remaining_slots = remaining_hitter_slots + remaining_pitcher_slots

        if config.baseline_type == "keeper_only":
            # No fill — just keeper stats
            proj.at[idx, "team_AB"] = row["keeper_AB"]
            proj.at[idx, "team_IP"] = row["keeper_IP"]
            continue

        # Allocate budget proportionally to remaining slots
        min_cost = max(remaining_slots, 0) * 1  # $1 minimum per player
        flexible_budget = max(remaining_budget - min_cost, 0)

        if remaining_slots > 0:
            hitter_fraction = remaining_hitter_slots / remaining_slots
            pitcher_fraction = remaining_pitcher_slots / remaining_slots
        else:
            hitter_fraction = 0.5
            pitcher_fraction = 0.5

        hitter_budget = remaining_hitter_slots * 1 + flexible_budget * hitter_fraction
        pitcher_budget = remaining_pitcher_slots * 1 + flexible_budget * pitcher_fraction

        discount = config.fill_discount

        # Add fill counting stats
        for cat in COUNTING_BATTING:
            proj.at[idx, cat] = row[cat] + fill_rates.get(cat, 0) * hitter_budget * discount
        for cat in COUNTING_PITCHING:
            proj.at[idx, cat] = row[cat] + fill_rates.get(cat, 0) * pitcher_budget * discount

        # Fill volume
        fill_ab = fill_rates.get("AB_per_dollar", 0) * hitter_budget * discount
        fill_ip = fill_rates.get("IP_per_dollar", 0) * pitcher_budget * discount
        total_ab = row["keeper_AB"] + fill_ab
        total_ip = row["keeper_IP"] + fill_ip

        # Recompute rate stats as weighted average of keeper + fill
        if total_ab > 0:
            proj.at[idx, "AVG"] = (
                row["AVG"] * row["keeper_AB"] + fill_rates.get("pool_AVG", 0.260) * fill_ab
            ) / total_ab
        if total_ip > 0:
            proj.at[idx, "ERA"] = (
                row["ERA"] * row["keeper_IP"] + fill_rates.get("pool_ERA", 4.20) * fill_ip
            ) / total_ip
            proj.at[idx, "WHIP"] = (
                row["WHIP"] * row["keeper_IP"] + fill_rates.get("pool_WHIP", 1.25) * fill_ip
            ) / total_ip

        proj.at[idx, "team_AB"] = total_ab
        proj.at[idx, "team_IP"] = total_ip

    if "team_AB" not in proj.columns:
        proj["team_AB"] = proj["keeper_AB"]
    if "team_IP" not in proj.columns:
        proj["team_IP"] = proj["keeper_IP"]

    return proj


def rank_standings(projected: pd.DataFrame) -> pd.DataFrame:
    """Rank teams 1-10 in each category, compute total standings points.

    Returns projected DataFrame with added rank columns and total_pts.
    """
    result = projected.copy()
    total_pts = pd.Series(0.0, index=result.index)

    for cat in ALL_CATEGORIES:
        if cat in INVERSE_CATEGORIES:
            # Lower is better: lowest value gets rank 10 (most points)
            result[f"rank_{cat}"] = result[cat].rank(ascending=False, method="average")
        else:
            # Higher is better: highest value gets rank 10
            result[f"rank_{cat}"] = result[cat].rank(ascending=True, method="average")
        total_pts += result[f"rank_{cat}"]

    result["total_pts"] = total_pts
    return result


def compute_msp(
    target_team: str,
    projected: pd.DataFrame,
    valuations: pd.DataFrame,
    baselines: pd.DataFrame,
    fill_rates: dict,
    config: MSPConfig,
    keeper_names: set[str],
) -> pd.DataFrame:
    """Compute Marginal Standings Points for each available player.

    For each non-keeper player, simulates adding them to the target team
    and computes the change in total standings points.

    Returns the valuations DataFrame with added msp and msp_per_dollar columns.
    """
    ranked = rank_standings(projected)
    team_idx = ranked.index[ranked["team"] == target_team]
    if len(team_idx) == 0:
        raise ValueError(f"Team '{target_team}' not found in projected standings")
    team_idx = team_idx[0]
    baseline_pts = ranked.at[team_idx, "total_pts"]
    baseline_row = ranked.loc[team_idx]

    # Identify available players (not keepers)
    available = valuations[~valuations["player_name"].isin(keeper_names)].copy()

    # Determine pitcher column
    if "is_pitcher" in available.columns:
        pitcher_col = "is_pitcher"
    elif "pos_type" in available.columns:
        available["_is_pitcher"] = available["pos_type"] == "pitcher"
        pitcher_col = "_is_pitcher"
    else:
        available["_is_pitcher"] = False
        pitcher_col = "_is_pitcher"

    # Dollar value column
    dv_col = "dollar_value" if "dollar_value" in available.columns else "production_value"

    # Get target team's baseline data for budget displacement
    team_baseline = baselines[baselines["team"] == target_team].iloc[0]
    remaining_budget = BUDGET_PER_TEAM - team_baseline["keeper_salary"]

    msp_values = []
    delta_ranks = {cat: [] for cat in ALL_CATEGORIES}

    for _, player in available.iterrows():
        player_cost = max(player.get(dv_col, 1), 1)
        is_pitcher = player.get(pitcher_col, False)

        # Start from current projected stats for the target team
        new_projected = projected.copy()
        new_row = new_projected.loc[new_projected["team"] == target_team].copy()
        ni = new_row.index[0]

        if config.budget_displacement and config.baseline_type != "keeper_only":
            # Reduce fill by player's cost — recompute fill for this team
            displaced_budget = min(player_cost, remaining_budget)
            remaining_after = remaining_budget - displaced_budget
            rem_h = HITTER_SLOTS - team_baseline["n_keeper_hitters"]
            rem_p = PITCHER_SLOTS - team_baseline["n_keeper_pitchers"]
            rem_slots = rem_h + rem_p
            min_cost = max(rem_slots, 0)
            flex = max(remaining_after - min_cost, 0)
            if rem_slots > 0:
                h_frac = rem_h / rem_slots
                p_frac = rem_p / rem_slots
            else:
                h_frac = 0.5
                p_frac = 0.5
            h_budget = rem_h * 1 + flex * h_frac
            p_budget = rem_p * 1 + flex * p_frac
            discount = config.fill_discount

            # Recompute from keeper baseline
            for cat in COUNTING_BATTING:
                new_projected.at[ni, cat] = team_baseline[cat] + fill_rates.get(cat, 0) * h_budget * discount
            for cat in COUNTING_PITCHING:
                new_projected.at[ni, cat] = team_baseline[cat] + fill_rates.get(cat, 0) * p_budget * discount

            fill_ab = fill_rates.get("AB_per_dollar", 0) * h_budget * discount
            fill_ip = fill_rates.get("IP_per_dollar", 0) * p_budget * discount
            t_ab = team_baseline["keeper_AB"] + fill_ab
            t_ip = team_baseline["keeper_IP"] + fill_ip
            if t_ab > 0:
                new_projected.at[ni, "AVG"] = (
                    team_baseline["AVG"] * team_baseline["keeper_AB"]
                    + fill_rates.get("pool_AVG", 0.260) * fill_ab
                ) / t_ab
            if t_ip > 0:
                new_projected.at[ni, "ERA"] = (
                    team_baseline["ERA"] * team_baseline["keeper_IP"]
                    + fill_rates.get("pool_ERA", 4.20) * fill_ip
                ) / t_ip
                new_projected.at[ni, "WHIP"] = (
                    team_baseline["WHIP"] * team_baseline["keeper_IP"]
                    + fill_rates.get("pool_WHIP", 1.25) * fill_ip
                ) / t_ip
            new_projected.at[ni, "team_AB"] = t_ab
            new_projected.at[ni, "team_IP"] = t_ip

        # Add player's stats on top
        if is_pitcher:
            player_ip = player.get("IP", 0) or 0
            for cat in COUNTING_PITCHING:
                new_projected.at[ni, cat] = new_projected.at[ni, cat] + (player.get(cat, 0) or 0)
            old_ip = new_projected.at[ni, "team_IP"]
            new_ip = old_ip + player_ip
            if new_ip > 0:
                new_projected.at[ni, "ERA"] = (
                    new_projected.at[ni, "ERA"] * old_ip + (player.get("ERA", 0) or 0) * player_ip
                ) / new_ip
                new_projected.at[ni, "WHIP"] = (
                    new_projected.at[ni, "WHIP"] * old_ip + (player.get("WHIP", 0) or 0) * player_ip
                ) / new_ip
            new_projected.at[ni, "team_IP"] = new_ip
        else:
            player_ab = player.get("AB", 0) or 0
            for cat in COUNTING_BATTING:
                new_projected.at[ni, cat] = new_projected.at[ni, cat] + (player.get(cat, 0) or 0)
            old_ab = new_projected.at[ni, "team_AB"]
            new_ab = old_ab + player_ab
            if new_ab > 0:
                new_projected.at[ni, "AVG"] = (
                    new_projected.at[ni, "AVG"] * old_ab + (player.get("AVG", 0) or 0) * player_ab
                ) / new_ab
            new_projected.at[ni, "team_AB"] = new_ab

        # Re-rank
        new_ranked = rank_standings(new_projected)
        new_pts = new_ranked.at[ni, "total_pts"]
        msp_values.append(new_pts - baseline_pts)

        # Per-category deltas
        for cat in ALL_CATEGORIES:
            new_rank = new_ranked.at[ni, f"rank_{cat}"]
            old_rank = baseline_row[f"rank_{cat}"]
            delta_ranks[cat].append(new_rank - old_rank)

    available = available.copy()
    available["msp"] = msp_values
    for cat in ALL_CATEGORIES:
        available[f"delta_rank_{cat}"] = delta_ranks[cat]
    available["msp_per_dollar"] = available["msp"] / available[dv_col].clip(lower=1)

    # Add baseline context columns
    for cat in ALL_CATEGORIES:
        available[f"team_rank_{cat}"] = baseline_row[f"rank_{cat}"]
    available["team_baseline_pts"] = baseline_pts

    return available


def run_msp(
    keepers: pd.DataFrame,
    valuations: pd.DataFrame,
    target_team: str,
    config: MSPConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """End-to-end MSP computation.

    Args:
        keepers: Pre-auction roster (all teams). Columns: team, player_name, salary, position, status.
        valuations: Player stats/projections. Must have stat columns + player_name.
        target_team: The team to compute MSP for.
        config: MSP model configuration.

    Returns:
        (msp_results, projected_standings) — MSP-augmented valuations and projected standings.
    """
    if config is None:
        config = MSPConfig()

    # Only active keepers
    active_keepers = keepers[keepers["status"].isin(["act", "dis"])]

    # Compute keeper baselines
    baselines = compute_keeper_baselines(active_keepers, valuations)

    # Build set of keeper names (projection-side) for filtering
    proj_index = build_name_index(valuations["player_name"].unique().tolist())
    keeper_names = set()
    for name in active_keepers["player_name"]:
        matched = match_name(name, proj_index)
        if matched:
            keeper_names.add(matched)

    # Compute fill rates from free agent pool
    fill_rates = compute_fill_rates(valuations, keeper_names)

    # Project full season
    projected = project_full_season(baselines, fill_rates, config)

    # Compute MSP for all available players
    msp_results = compute_msp(
        target_team, projected, valuations, baselines, fill_rates, config, keeper_names
    )

    # Add projected standings with ranks
    ranked_standings = rank_standings(projected)

    return msp_results, ranked_standings


def compute_tps(msp_results: pd.DataFrame) -> pd.DataFrame:
    """Compute Target Priority Score (TPS) on a 1-100 scale.

    TPS measures how much a player's MSP *diverges* from what you'd expect
    given their dollar value. High TPS = this player helps your team MORE
    than their price suggests (target them). Low TPS = they help LESS than
    their price suggests (let someone else overpay).

    Method: fit a LOESS-style baseline of MSP vs dollar_value using quantile
    bins, compute the residual (actual MSP - expected MSP), then scale to 1-100.

    Args:
        msp_results: DataFrame with msp, msp_per_dollar, and dollar_value columns.

    Returns:
        Same DataFrame with added tps column.
    """
    df = msp_results.copy()

    # Determine dollar value column
    if "dollar_value" in df.columns:
        dv_col = "dollar_value"
    elif "production_value" in df.columns:
        dv_col = "production_value"
    else:
        df["tps"] = 50
        return df

    dv = df[dv_col].fillna(0).clip(lower=0)
    msp = df["msp"].fillna(0)

    # Compute expected MSP for each dollar value level using rolling quantile bins.
    # This captures the natural baseline: expensive players have higher MSP.
    n_bins = 20
    df["_dv_bin"] = pd.qcut(dv.rank(method="first"), q=n_bins, labels=False, duplicates="drop")
    bin_means = df.groupby("_dv_bin")["msp"].transform("mean")

    # Residual: how much more MSP than expected for this price tier
    residual = msp - bin_means

    # Scale residual to 1-100 via percentile rank
    pctile = residual.rank(pct=True, method="average")
    tps = (pctile * 99 + 1).round(0).astype(int)

    # Clamp negative-MSP players to 1
    tps = tps.where(msp >= 0, 1)

    df["tps"] = tps
    df = df.drop(columns=["_dv_bin"])
    return df

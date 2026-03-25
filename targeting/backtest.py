"""Historical backtesting for the MSP targeting model.

Reconstructs pre-auction state for each validation year (2019, 2021-2025),
runs the MSP framework with actual end-of-season stats as 'perfect projections',
and evaluates using three metrics.

Uses player_valuations_{year}.csv which already contains fantasy_team,
contract_year, status, actual stats, and SGP values for all rostered players.
"""

import numpy as np
import pandas as pd
from scipy import stats

from targeting.model import (
    ALL_CATEGORIES,
    BUDGET_PER_TEAM,
    HITTER_SLOTS,
    PITCHER_SLOTS,
    MSPConfig,
    compute_fill_rates,
    compute_keeper_baselines,
    compute_msp,
    project_full_season,
    rank_standings,
)
from targeting.name_match import build_name_index, match_name

VALIDATION_YEARS = [2019, 2021, 2022, 2023, 2024, 2025]

# Contract codes that indicate keepers (retained from prior year)
KEEPER_CODES = {"b", "c", "x", "y", "z", "br", "cr", "xr", "yr", "zr"}

# Contract codes that indicate auction draftees (acquired at auction)
DRAFT_CODES = {"a", "ar"}


def load_year_data(year: int) -> pd.DataFrame:
    """Load player valuations for a given year."""
    path = f"data/player_valuations_{year}.csv"
    df = pd.read_csv(path)

    # Normalize column names for compatibility with model.py
    if "fantasy_team" in df.columns and "team" not in df.columns:
        df = df.rename(columns={"fantasy_team": "team"})
    if "production_value" in df.columns and "dollar_value" not in df.columns:
        df = df.rename(columns={"production_value": "dollar_value"})
    if "is_pitcher" not in df.columns:
        df["is_pitcher"] = df["position"].str.contains("P|SP|RP", na=False)

    # Ensure pos_type column exists
    if "pos_type" not in df.columns:
        df["pos_type"] = np.where(df["is_pitcher"], "pitcher", "hitter")

    return df


def reconstruct_preauction(year: int) -> dict:
    """Reconstruct pre-auction state for a given year.

    Returns dict with:
        - keepers: DataFrame of keeper players per team
        - draftees: DataFrame of auction-drafted players per team
        - all_players: Full valuations (used as 'perfect projections')
        - teams: list of team names
    """
    df = load_year_data(year)

    # Classify players by contract type
    keepers = df[df["contract_year"].isin(KEEPER_CODES)].copy()
    draftees = df[df["contract_year"].isin(DRAFT_CODES)].copy()

    # Only active players count as keepers
    keepers = keepers[keepers["status"].isin(["act", "dis"])]

    teams = sorted(df["team"].unique())

    return {
        "keepers": keepers,
        "draftees": draftees,
        "all_players": df,
        "teams": teams,
    }


def run_msp_for_year(
    year: int,
    config: MSPConfig,
) -> dict:
    """Run full MSP computation for all teams in a given year.

    Returns dict with:
        - msp_by_team: {team_name: DataFrame of MSP-scored available players}
        - standings: projected standings DataFrame
        - preauction: the reconstructed pre-auction state
    """
    preauction = reconstruct_preauction(year)
    keepers = preauction["keepers"]
    all_players = preauction["all_players"]
    teams = preauction["teams"]

    # For the MSP model, we need keepers in the format expected by model.py:
    # columns: team, player_name, salary, position, status
    keeper_roster = keepers[["team", "player_name", "salary", "position", "status"]].copy()

    # Build keeper baselines
    baselines = compute_keeper_baselines(keeper_roster, all_players)

    # Build keeper name set
    proj_index = build_name_index(all_players["player_name"].unique().tolist())
    keeper_names = set()
    for name in keepers["player_name"]:
        matched = match_name(name, proj_index)
        if matched:
            keeper_names.add(matched)

    # Compute fill rates
    fill_rates = compute_fill_rates(all_players, keeper_names)

    # Project full season
    projected = project_full_season(baselines, fill_rates, config)

    # Run MSP for each team
    msp_by_team = {}
    for team in teams:
        if team not in baselines["team"].values:
            continue
        try:
            msp_results = compute_msp(
                team, projected, all_players, baselines, fill_rates, config, keeper_names
            )
            msp_by_team[team] = msp_results
        except (ValueError, IndexError):
            continue

    ranked = rank_standings(projected)

    return {
        "msp_by_team": msp_by_team,
        "standings": ranked,
        "preauction": preauction,
    }


def evaluate_standings_correlation(
    msp_by_team: dict,
    preauction: dict,
    actual_standings: pd.DataFrame,
    projected_standings: pd.DataFrame,
    year: int,
) -> dict:
    """Metric 1: Standings Point Correlation.

    Two sub-metrics:
    - predicted_vs_actual_r: correlation of (baseline_pts + sum MSP of draftees) with actual pts
    - draftee_msp_vs_residual_r: correlation of sum MSP with (actual - baseline), measuring
      whether the model captures draft-driven standings movement

    Returns dict with correlations and per-team data.
    """
    draftees = preauction["draftees"]
    year_standings = actual_standings[actual_standings["year"] == year]

    team_data = []
    for team, msp_df in msp_by_team.items():
        # Find this team's actual draftees
        team_draftees = draftees[draftees["team"] == team]["player_name"].tolist()

        # Sum MSP of players this team actually drafted
        drafted_msp = msp_df[msp_df["player_name"].isin(team_draftees)]
        msp_sum = drafted_msp["msp"].sum() if not drafted_msp.empty else 0.0

        # Baseline standings points (projected from keepers + fill)
        team_proj = projected_standings[projected_standings["team"] == team]
        baseline_pts = team_proj.iloc[0]["total_pts"] if not team_proj.empty else np.nan

        # Predicted total = baseline + draft MSP
        predicted_pts = baseline_pts + msp_sum if not np.isnan(baseline_pts) else np.nan

        # Get actual standings points
        actual = year_standings[year_standings["team"] == team]
        if actual.empty:
            continue
        actual_pts = actual.iloc[0]["total_pts"]

        team_data.append({
            "year": year,
            "team": team,
            "baseline_pts": baseline_pts,
            "msp_sum_draftees": msp_sum,
            "predicted_pts": predicted_pts,
            "actual_total_pts": actual_pts,
            "n_draftees_matched": len(drafted_msp),
            "n_draftees_total": len(team_draftees),
        })

    if len(team_data) < 3:
        return {"predicted_vs_actual_r": np.nan, "draftee_msp_r": np.nan, "team_data": team_data}

    df = pd.DataFrame(team_data)

    # Primary: does predicted total correlate with actual?
    valid = df.dropna(subset=["predicted_pts", "actual_total_pts"])
    if len(valid) >= 3:
        r_pred, _ = stats.spearmanr(valid["predicted_pts"], valid["actual_total_pts"])
    else:
        r_pred = np.nan

    # Secondary: does MSP sum correlate with standings movement above baseline?
    valid2 = df.dropna(subset=["baseline_pts", "actual_total_pts"])
    if len(valid2) >= 3:
        residual = valid2["actual_total_pts"] - valid2["baseline_pts"]
        r_msp, _ = stats.spearmanr(valid2["msp_sum_draftees"], residual)
    else:
        r_msp = np.nan

    return {"predicted_vs_actual_r": r_pred, "draftee_msp_r": r_msp, "team_data": team_data}


def evaluate_draft_prediction(
    msp_by_team: dict,
    preauction: dict,
) -> dict:
    """Metric 2: Draft Prediction Accuracy.

    For each team, rank all available players by MSP. Compute the average
    percentile rank of players the team actually drafted. Higher = better.
    Also computes AUC-ROC (drafted vs. not drafted, scored by MSP).

    Returns dict with mean_percentile, mean_auc, and per-team data.
    """
    draftees = preauction["draftees"]
    team_data = []

    for team, msp_df in msp_by_team.items():
        team_draftees = set(draftees[draftees["team"] == team]["player_name"].tolist())

        if not team_draftees or msp_df.empty:
            continue

        # Rank by MSP (highest = best)
        ranked = msp_df.sort_values("msp", ascending=False).reset_index(drop=True)
        ranked["msp_rank"] = range(1, len(ranked) + 1)
        n_available = len(ranked)

        # Percentile rank of drafted players (1.0 = top, 0.0 = bottom)
        drafted_rows = ranked[ranked["player_name"].isin(team_draftees)]
        if drafted_rows.empty:
            continue

        percentiles = 1.0 - (drafted_rows["msp_rank"] - 1) / n_available
        mean_pctile = percentiles.mean()

        # AUC: can we distinguish drafted from undrafted?
        ranked["drafted"] = ranked["player_name"].isin(team_draftees).astype(int)
        n_pos = ranked["drafted"].sum()
        n_neg = len(ranked) - n_pos

        if n_pos > 0 and n_neg > 0:
            # Mann-Whitney U for AUC
            drafted_ranks = ranked[ranked["drafted"] == 1]["msp_rank"]
            u_stat = n_pos * n_neg + n_pos * (n_pos + 1) / 2 - drafted_ranks.sum()
            auc = u_stat / (n_pos * n_neg)
        else:
            auc = np.nan

        team_data.append({
            "year": preauction["all_players"]["year"].iloc[0],
            "team": team,
            "mean_percentile": mean_pctile,
            "auc": auc,
            "n_drafted": n_pos,
            "n_available": n_available,
        })

    if not team_data:
        return {"mean_percentile": np.nan, "mean_auc": np.nan, "team_data": team_data}

    df = pd.DataFrame(team_data)
    return {
        "mean_percentile": df["mean_percentile"].mean(),
        "mean_auc": df["auc"].mean(),
        "team_data": team_data,
    }


def evaluate_optimal_draft(
    msp_by_team: dict,
    preauction: dict,
    actual_standings: pd.DataFrame,
    year: int,
) -> dict:
    """Metric 3: Optimal Draft Simulation.

    For each team, greedily draft the highest-MSP player that fits within
    the remaining budget, filling roster slots. Compare the sum of MSP
    from the optimal draft to the sum of MSP from the actual draft.

    Returns dict with mean_uplift, and per-team data.
    """
    draftees = preauction["draftees"]
    keepers = preauction["keepers"]
    year_standings = actual_standings[actual_standings["year"] == year]

    team_data = []
    for team, msp_df in msp_by_team.items():
        # Team's keeper info
        team_keepers = keepers[keepers["team"] == team]
        n_keeper_hitters = team_keepers[~team_keepers["is_pitcher"]].shape[0]
        n_keeper_pitchers = team_keepers[team_keepers["is_pitcher"]].shape[0]
        keeper_salary = team_keepers["salary"].sum()
        remaining_budget = BUDGET_PER_TEAM - keeper_salary

        hitter_slots = HITTER_SLOTS - n_keeper_hitters
        pitcher_slots = PITCHER_SLOTS - n_keeper_pitchers

        # Dollar value column
        dv_col = "dollar_value" if "dollar_value" in msp_df.columns else "production_value"

        # Greedy optimal draft
        available = msp_df.sort_values("msp", ascending=False).copy()
        budget_left = remaining_budget
        h_slots_left = max(hitter_slots, 0)
        p_slots_left = max(pitcher_slots, 0)
        optimal_msp = 0.0
        optimal_picks = []

        for _, player in available.iterrows():
            if h_slots_left <= 0 and p_slots_left <= 0:
                break

            cost = max(player.get(dv_col, 1), 1)
            # Reserve $1 per remaining unfilled slot
            slots_after = h_slots_left + p_slots_left - 1
            min_reserve = max(slots_after, 0)

            if cost > budget_left - min_reserve:
                continue

            is_pitcher = player.get("is_pitcher", False)
            if is_pitcher and p_slots_left <= 0:
                continue
            if not is_pitcher and h_slots_left <= 0:
                continue

            optimal_picks.append(player["player_name"])
            optimal_msp += player["msp"]
            budget_left -= cost
            if is_pitcher:
                p_slots_left -= 1
            else:
                h_slots_left -= 1

        # Actual draft MSP sum
        team_draftees = draftees[draftees["team"] == team]["player_name"].tolist()
        actual_drafted_msp = msp_df[msp_df["player_name"].isin(team_draftees)]
        actual_msp_sum = actual_drafted_msp["msp"].sum() if not actual_drafted_msp.empty else 0.0

        # Actual standings
        actual = year_standings[year_standings["team"] == team]
        actual_pts = actual.iloc[0]["total_pts"] if not actual.empty else np.nan

        uplift = optimal_msp - actual_msp_sum

        team_data.append({
            "year": year,
            "team": team,
            "optimal_msp_sum": optimal_msp,
            "actual_msp_sum": actual_msp_sum,
            "msp_uplift": uplift,
            "actual_total_pts": actual_pts,
            "n_optimal_picks": len(optimal_picks),
            "n_actual_draftees": len(team_draftees),
        })

    if not team_data:
        return {"mean_uplift": np.nan, "team_data": team_data}

    df = pd.DataFrame(team_data)
    return {
        "mean_uplift": df["msp_uplift"].mean(),
        "median_uplift": df["msp_uplift"].median(),
        "team_data": team_data,
    }


def run_backtest(
    config: MSPConfig,
    years: list[int] | None = None,
    verbose: bool = False,
) -> dict:
    """Run full backtest across all validation years.

    Returns aggregated metrics and per-year detail.
    """
    if years is None:
        years = VALIDATION_YEARS

    standings = pd.read_csv("data/historical_standings.csv")

    all_standings_corr = []
    all_draft_pred = []
    all_optimal_draft = []
    year_results = {}

    for year in years:
        if verbose:
            print(f"  Year {year}...", end=" ", flush=True)

        try:
            result = run_msp_for_year(year, config)
        except Exception as e:
            if verbose:
                print(f"FAILED: {e}")
            continue

        msp_by_team = result["msp_by_team"]
        preauction = result["preauction"]

        # Metric 1: Standings correlation
        m1 = evaluate_standings_correlation(
            msp_by_team, preauction, standings, result["standings"], year
        )
        all_standings_corr.extend(m1["team_data"])

        # Metric 2: Draft prediction
        m2 = evaluate_draft_prediction(msp_by_team, preauction)
        all_draft_pred.extend(m2["team_data"])

        # Metric 3: Optimal draft simulation
        m3 = evaluate_optimal_draft(msp_by_team, preauction, standings, year)
        all_optimal_draft.extend(m3["team_data"])

        year_results[year] = {"m1": m1, "m2": m2, "m3": m3}

        if verbose:
            print(f"pred_r={m1['predicted_vs_actual_r']:.3f}, "
                  f"msp_r={m1['draftee_msp_r']:.3f}, "
                  f"AUC={m2['mean_auc']:.3f}, "
                  f"uplift={m3['mean_uplift']:.1f}")

    # Aggregate metrics across all team-years
    agg = {}

    if all_standings_corr:
        df1 = pd.DataFrame(all_standings_corr)
        valid1 = df1.dropna(subset=["predicted_pts", "actual_total_pts"])
        if len(valid1) >= 3:
            r_pred, _ = stats.spearmanr(valid1["predicted_pts"], valid1["actual_total_pts"])
        else:
            r_pred = np.nan
        valid2 = df1.dropna(subset=["baseline_pts", "actual_total_pts"])
        if len(valid2) >= 3:
            residual = valid2["actual_total_pts"] - valid2["baseline_pts"]
            r_msp, _ = stats.spearmanr(valid2["msp_sum_draftees"], residual)
        else:
            r_msp = np.nan
        agg["predicted_vs_actual_r"] = r_pred
        agg["draftee_msp_r"] = r_msp
    else:
        agg["predicted_vs_actual_r"] = np.nan
        agg["draftee_msp_r"] = np.nan

    if all_draft_pred:
        df2 = pd.DataFrame(all_draft_pred)
        agg["draft_auc"] = df2["auc"].mean()
        agg["draft_percentile"] = df2["mean_percentile"].mean()
    else:
        agg["draft_auc"] = np.nan
        agg["draft_percentile"] = np.nan

    if all_optimal_draft:
        df3 = pd.DataFrame(all_optimal_draft)
        agg["optimal_uplift_mean"] = df3["msp_uplift"].mean()
        agg["optimal_uplift_median"] = df3["msp_uplift"].median()
    else:
        agg["optimal_uplift_mean"] = np.nan
        agg["optimal_uplift_median"] = np.nan

    return {
        "config": config,
        "aggregate": agg,
        "year_results": year_results,
        "standings_detail": all_standings_corr,
        "draft_detail": all_draft_pred,
        "optimal_detail": all_optimal_draft,
    }

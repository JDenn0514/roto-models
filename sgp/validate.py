"""End-to-end validation: run actual player stats through the SGP valuation pipeline.

Computes per-player SGP, PAR, and dollar values using calibrated SGP denominators,
then merges with roster salary data for surplus analysis.

Usage:
    python3 -m sgp.validate --year 2024
    python3 -m sgp.validate --year 2024 --report
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import DATA_DIR, get_calibration_data, load_rosters
from sgp.dollar_values import (
    compute_dollar_values,
    compute_hitter_pitcher_split,
    compute_historical_spending_split,
    compute_split_pool_values,
)
from sgp.replacement import compute_replacement_level
from sgp.sgp_calc import SGPResult, compute_sgp, player_stat_to_sgp

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
PLOTS_DIR = Path(__file__).resolve().parent.parent / "plots"


def load_player_stats(year: int) -> pd.DataFrame:
    """Load player stats for a given year from data/player_stats.csv.

    The CSV is produced by get_player_stats.py, which fetches FanGraphs stats
    and matches them to fantasy rosters. Stats and roster data (salary,
    contract, fantasy_team) are already merged.

    Players who appear on multiple fantasy teams (mid-season trades) are
    deduplicated: we keep the row with 'act' status if one exists, otherwise
    the row with the highest salary (the team that invested most).
    """
    path = DATA_DIR / "player_stats.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run get_player_stats.py first."
        )
    df = pd.read_csv(path)
    df = df[df["year"] == year].copy()
    if df.empty:
        raise ValueError(f"No player stats found for {year}")

    # Deduplicate players on multiple teams
    before = len(df)
    # Priority: 'act' status first, then highest salary
    df["_sort_status"] = (df["status"] == "act").astype(int)
    df = df.sort_values(["_sort_status", "salary"], ascending=[False, False])
    df = df.drop_duplicates(subset=["player_name", "is_pitcher"], keep="first")
    df = df.drop(columns=["_sort_status"])
    after = len(df)
    if before != after:
        print(f"  Deduplicated: {before} → {after} rows ({before - after} multi-team duplicates)")

    return df


def merge_roster_data(players: pd.DataFrame, year: int) -> pd.DataFrame:
    """Ensure roster data (salary, contract) is present.

    When using get_player_stats.py (pybaseball), roster data is already merged
    into the player_stats.csv. This function just reports match quality.
    """
    if "salary" not in players.columns:
        players["salary"] = np.nan
    if "contract_year" not in players.columns:
        players["contract_year"] = None
    if "fantasy_team" not in players.columns:
        players["fantasy_team"] = None

    n_with_salary = players["salary"].notna().sum()
    print(f"  {n_with_salary}/{len(players)} players have salary data")
    return players


def compute_player_sgp(
    players: pd.DataFrame,
    sgp_result: SGPResult,
    replacement: dict,
    config: SGPConfig,
) -> pd.DataFrame:
    """Compute per-category RAW SGP and total SGP for each player.

    Returns raw SGP (not above replacement) so that compute_dollar_values()
    can subtract replacement once when computing PAR.

    For counting stats: player_stat / denom  (raw, no replacement subtraction)
    For rate stats: uses replacement as baseline (replacement SGP = 0 by design)
    """
    df = players.copy()

    repl_stats = replacement["replacement_stats"]

    # Initialize SGP columns
    for cat in config.all_categories:
        df[f"sgp_{cat}"] = 0.0

    df["total_sgp"] = 0.0

    for idx, row in df.iterrows():
        is_pitcher = row["is_pitcher"]
        cats = config.all_pitching if is_pitcher else config.all_batting
        total = 0.0

        for cat in cats:
            denom = sgp_result.denominators.get(cat)
            if denom is None or np.isnan(denom) or denom == 0:
                continue

            player_stat = row.get(cat)
            if pd.isna(player_stat):
                continue

            is_rate = cat in config.rate_batting or cat in config.rate_pitching

            if is_rate:
                # Rate stats: use replacement as baseline via player_stat_to_sgp.
                # The replacement-level contribution for rate stats is 0 by design
                # (replacement.py sets repl_sgp=0 for rate categories), so this
                # formula is compatible with compute_dollar_values().
                repl_stat = repl_stats.get(cat, 0)
                ab_or_ip = None
                if cat in config.rate_batting:
                    ab_or_ip = row.get("AB")
                    if pd.isna(ab_or_ip) or ab_or_ip == 0:
                        continue
                elif cat in config.rate_pitching:
                    ab_or_ip = row.get("IP")
                    if pd.isna(ab_or_ip) or ab_or_ip == 0:
                        continue

                sgp = player_stat_to_sgp(
                    player_stat, repl_stat, denom, cat, config, ab_or_ip
                )
            else:
                # Counting stats: raw SGP = player_stat / denom.
                # Do NOT subtract replacement here — compute_dollar_values()
                # will subtract hitter/pitcher replacement SGP from the total.
                sgp = player_stat / denom

            df.at[idx, f"sgp_{cat}"] = sgp
            total += sgp

        df.at[idx, "total_sgp"] = total

    return df


def validate_year(year: int, config: SGPConfig = None) -> pd.DataFrame:
    """Run full valuation on actual player stats for a given year.

    1. Load player stats for the year
    2. Merge with roster data (salary, contract)
    3. Calibrate SGP denominators from historical standings
    4. Compute replacement level
    5. Compute per-player SGP
    6. Convert to dollar values
    7. Return DataFrame with stats + SGP + dollars + salary + surplus
    """
    if config is None:
        config = SGPConfig.composite()

    print(f"\n=== Validating {year} ===")

    # Step 1: Load player stats
    print("Loading player stats...")
    players = load_player_stats(year)
    n_hitters = (~players["is_pitcher"]).sum()
    n_pitchers = players["is_pitcher"].sum()
    print(f"  {len(players)} players: {n_hitters} hitters, {n_pitchers} pitchers")

    # Step 2: Merge with roster data
    print("Merging roster data...")
    players = merge_roster_data(players, year)

    # Step 3: Calibrate SGP
    print("Computing SGP denominators...")
    standings = get_calibration_data(config)
    sgp_result = compute_sgp(standings, config, bootstrap=False)
    print("  Denominators:", {c: f"{d:.2f}" for c, d in sgp_result.denominators.items()})

    # Step 4: Replacement level
    print("Computing replacement level...")
    replacement = compute_replacement_level(sgp_result, config, standings_df=standings)
    print(f"  Hitter repl SGP: {replacement['hitter_repl_sgp']:.2f}")
    print(f"  Pitcher repl SGP: {replacement['pitcher_repl_sgp']:.2f}")

    # Step 5: Per-player SGP
    print("Computing player SGP values...")
    players = compute_player_sgp(players, sgp_result, replacement, config)

    # Step 6: Dollar values — both single-pool and split-pool
    print("Converting to dollar values...")
    player_sgp_df = players[["player_name", "is_pitcher", "total_sgp"]].copy()
    player_sgp_df["pos_type"] = player_sgp_df["is_pitcher"].map(
        {True: "pitcher", False: "hitter"}
    )

    # Single-pool: production value (where does value actually come from?)
    single_df = compute_dollar_values(player_sgp_df, replacement, config)
    players["par"] = single_df["par"].values
    players["production_value"] = single_df["dollar_value"].values

    # Compute hitter/pitcher spending split from historical roster data
    hist_split = compute_historical_spending_split(config)
    if hist_split is not None and not hist_split.empty:
        hitter_pct = hist_split["hitter_pct"].mean() / 100.0
        print(f"  Historical spending split: {hitter_pct:.1%} hitters / {1 - hitter_pct:.1%} pitchers")
    else:
        hitter_pct = 0.63
        print(f"  Using default spending split: {hitter_pct:.0%} hitters / {1 - hitter_pct:.0%} pitchers")

    # Split-pool: auction value (what should you bid?)
    split_df = compute_split_pool_values(player_sgp_df, replacement, config, hitter_pct=hitter_pct)
    players["auction_value"] = split_df["auction_value"].values

    # Surplus based on auction value (what matters for draft strategy)
    players["surplus"] = np.nan
    has_salary = players["salary"].notna()
    players.loc[has_salary, "surplus"] = (
        players.loc[has_salary, "auction_value"] - players.loc[has_salary, "salary"]
    )

    # Production surplus (where the market misprices)
    players["production_surplus"] = np.nan
    players.loc[has_salary, "production_surplus"] = (
        players.loc[has_salary, "production_value"] - players.loc[has_salary, "salary"]
    )

    # Print validation summary
    _print_validation_summary(players, config, hitter_pct=hitter_pct)

    # Save output
    output_path = DATA_DIR / f"player_valuations_{year}.csv"
    players.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")

    return players


def _print_validation_summary(df: pd.DataFrame, config: SGPConfig, hitter_pct: float = 0.63):
    """Print key validation checks."""
    print("\n--- Validation Summary ---")

    # Determine which value columns exist
    has_dual = "auction_value" in df.columns and "production_value" in df.columns
    val_col = "auction_value" if has_dual else "dollar_value"

    # Total dollar pools
    if has_dual:
        prod_total = df["production_value"].sum()
        auct_total = df["auction_value"].sum()
        print(f"Production pool: ${prod_total:,.0f}  |  Auction pool: ${auct_total:,.0f}  (target: ${config.total_auction_pool:,})")

        # Hitter/pitcher split for production (single-pool)
        prod_split_df = df.assign(pos_type=df["is_pitcher"].map({True: "pitcher", False: "hitter"}))
        prod_split_df["dollar_value"] = prod_split_df["production_value"]
        prod_split = compute_hitter_pitcher_split(prod_split_df)
        print(f"Production split: {prod_split.get('hitter_pct', 0):.1f}% hitters / {prod_split.get('pitcher_pct', 0):.1f}% pitchers")
        print(f"Auction split:    {hitter_pct*100:.1f}% hitters / {(1-hitter_pct)*100:.1f}% pitchers (from historical spending)")
    else:
        total_dollars = df.get("dollar_value", pd.Series(dtype=float)).sum()
        print(f"Total dollar pool: ${total_dollars:,.0f}  (expected: ${config.total_auction_pool:,})")

    # Positive-PAR counts
    pos_par_hitters = ((df["par"] > 0) & (~df["is_pitcher"])).sum()
    pos_par_pitchers = ((df["par"] > 0) & (df["is_pitcher"])).sum()
    print(f"Positive-PAR players: {pos_par_hitters} hitters, {pos_par_pitchers} pitchers")

    # Top 10 hitters
    hitters = df[~df["is_pitcher"]].sort_values(val_col, ascending=False)
    print(f"\nTop 10 Hitters:")
    if has_dual:
        print(f"  {'Auction':>8s} {'Prod':>6s}  {'Player':<22s} {'Pos':>3s}  Salary")
        for _, row in hitters.head(10).iterrows():
            sal = f"${row['salary']:.0f}" if pd.notna(row.get("salary")) else "N/A"
            print(f"  ${row['auction_value']:6.1f} ${row['production_value']:5.1f}"
                  f"  {row['player_name']:<22s} {row.get('position', ''):>3s}  sal={sal}")
    else:
        for _, row in hitters.head(10).iterrows():
            sal = f"${row['salary']:.0f}" if pd.notna(row.get("salary")) else "N/A"
            print(f"  ${row[val_col]:5.1f}  {row['player_name']:<22s}  "
                  f"{row.get('position', ''):>3s}  sal={sal}")

    # Top 10 pitchers
    pitchers = df[df["is_pitcher"]].sort_values(val_col, ascending=False)
    print(f"\nTop 10 Pitchers:")
    if has_dual:
        print(f"  {'Auction':>8s} {'Prod':>6s}  {'Player':<22s} Salary")
        for _, row in pitchers.head(10).iterrows():
            sal = f"${row['salary']:.0f}" if pd.notna(row.get("salary")) else "N/A"
            print(f"  ${row['auction_value']:6.1f} ${row['production_value']:5.1f}"
                  f"  {row['player_name']:<22s} sal={sal}")
    else:
        for _, row in pitchers.head(10).iterrows():
            sal = f"${row['salary']:.0f}" if pd.notna(row.get("salary")) else "N/A"
            print(f"  ${row[val_col]:5.1f}  {row['player_name']:<22s}  sal={sal}")

    # Top surplus (based on auction value)
    has_surplus = df["surplus"].notna()
    if has_surplus.any():
        print(f"\nTop 10 Surplus (auction value - salary):")
        surplus = df[has_surplus].sort_values("surplus", ascending=False)
        for _, row in surplus.head(10).iterrows():
            print(f"  {row['surplus']:+6.1f}  {row['player_name']:<22s}  "
                  f"auct=${row[val_col]:.1f}  sal=${row['salary']:.0f}")

        print(f"\nTop 10 Overpaid (salary - auction value):")
        overpaid = df[has_surplus].sort_values("surplus", ascending=True)
        for _, row in overpaid.head(10).iterrows():
            print(f"  {row['surplus']:+6.1f}  {row['player_name']:<22s}  "
                  f"auct=${row[val_col]:.1f}  sal=${row['salary']:.0f}")


def generate_validation_plots(df: pd.DataFrame, year: int):
    """Generate diagnostic plots for the validation results."""
    import matplotlib.pyplot as plt

    PLOTS_DIR.mkdir(exist_ok=True)

    # 1. Dollar value distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    hitters = df[~df["is_pitcher"]]
    pitchers = df[df["is_pitcher"]]

    axes[0].hist(hitters["auction_value"], bins=30, color="#2196F3", edgecolor="black", alpha=0.8)
    axes[0].set_title("Hitter Auction Values")
    axes[0].set_xlabel("Auction Value ($)")
    axes[0].set_ylabel("Count")
    axes[0].axvline(hitters["auction_value"].median(), color="red", linestyle="--",
                     label=f"Median: ${hitters['auction_value'].median():.1f}")
    axes[0].legend()

    axes[1].hist(pitchers["auction_value"], bins=30, color="#FF5722", edgecolor="black", alpha=0.8)
    axes[1].set_title("Pitcher Auction Values")
    axes[1].set_xlabel("Auction Value ($)")
    axes[1].axvline(pitchers["auction_value"].median(), color="red", linestyle="--",
                     label=f"Median: ${pitchers['auction_value'].median():.1f}")
    axes[1].legend()

    fig.suptitle(f"Dollar Value Distribution — {year}", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / f"validation_dollar_dist_{year}.png", dpi=150)
    plt.close(fig)

    # 2. Value vs Salary scatter
    has_salary = df["salary"].notna() & (df["auction_value"] > 0)
    if has_salary.any():
        fig, ax = plt.subplots(figsize=(10, 8))
        sal_df = df[has_salary]

        h_mask = ~sal_df["is_pitcher"]
        p_mask = sal_df["is_pitcher"]

        ax.scatter(sal_df.loc[h_mask, "salary"], sal_df.loc[h_mask, "auction_value"],
                   color="#2196F3", alpha=0.6, s=30, label="Hitters", edgecolors="black", linewidth=0.3)
        ax.scatter(sal_df.loc[p_mask, "salary"], sal_df.loc[p_mask, "auction_value"],
                   color="#FF5722", alpha=0.6, s=30, label="Pitchers", edgecolors="black", linewidth=0.3)

        # 1:1 line
        max_val = max(sal_df["salary"].max(), sal_df["auction_value"].max())
        ax.plot([0, max_val], [0, max_val], "k--", alpha=0.4, label="Fair value line")

        ax.set_xlabel("Actual Salary ($)")
        ax.set_ylabel("Auction Value ($)")
        ax.set_title(f"Auction Value vs. Actual Salary — {year}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"validation_value_vs_salary_{year}.png", dpi=150)
        plt.close(fig)

    # 3. Category SGP leaders (top 5 per category)
    config = SGPConfig.composite()
    sgp_cats = [f"sgp_{c}" for c in config.all_categories if f"sgp_{c}" in df.columns]
    n_cats = len(sgp_cats)
    if n_cats > 0:
        fig, axes = plt.subplots(2, 5, figsize=(22, 10))
        axes = axes.flatten()

        for i, sgp_col in enumerate(sgp_cats):
            ax = axes[i]
            cat = sgp_col.replace("sgp_", "")
            top5 = df.nlargest(5, sgp_col)
            names = [n[:15] for n in top5["player_name"].values]
            vals = top5[sgp_col].values

            ax.barh(range(len(names)), vals, color="#4CAF50", edgecolor="black")
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names, fontsize=9)
            ax.invert_yaxis()
            ax.set_title(cat, fontsize=12, fontweight="bold")
            ax.set_xlabel("SGP")

        for i in range(n_cats, 10):
            axes[i].set_visible(False)

        fig.suptitle(f"Category SGP Leaders — {year}", fontsize=14, fontweight="bold")
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"validation_sgp_leaders_{year}.png", dpi=150)
        plt.close(fig)

    print(f"  Plots saved to {PLOTS_DIR}/validation_*_{year}.png")


def generate_report(df: pd.DataFrame, year: int):
    """Generate a Quarto validation report."""
    REPORTS_DIR.mkdir(exist_ok=True)

    # Also generate plots for embedding
    generate_validation_plots(df, year)

    config = SGPConfig.composite()
    hitters = df[~df["is_pitcher"]].sort_values("auction_value", ascending=False)
    pitchers = df[df["is_pitcher"]].sort_values("auction_value", ascending=False)

    total_dollars = df["auction_value"].sum()
    # Production split for diagnostics
    prod_split_df = df.assign(
        pos_type=df["is_pitcher"].map({True: "pitcher", False: "hitter"}),
        dollar_value=df["production_value"],
    )
    split = compute_hitter_pitcher_split(prod_split_df)
    pos_par_h = ((df["par"] > 0) & (~df["is_pitcher"])).sum()
    pos_par_p = ((df["par"] > 0) & (df["is_pitcher"])).sum()

    def _fmt_table(subset, cols, n=25):
        """Format a DataFrame subset as a markdown table."""
        lines = []
        top = subset.head(n)
        # Header
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in top.iterrows():
            vals = []
            for c in cols:
                v = row.get(c)
                if pd.isna(v):
                    vals.append("")
                elif isinstance(v, float):
                    if c in ("AVG", "ERA", "WHIP"):
                        vals.append(f"{v:.3f}")
                    elif c in ("dollar_value", "auction_value", "production_value",
                               "salary", "surplus", "production_surplus", "par"):
                        vals.append(f"${v:.1f}" if "surplus" not in c else f"{v:+.1f}")
                    else:
                        vals.append(f"{v:.1f}")
                else:
                    vals.append(str(v))
            lines.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines)

    top25_hitter_cols = ["player_name", "fantasy_team", "position", "auction_value",
                         "production_value", "salary", "surplus", "R", "HR", "RBI", "SB", "AVG"]
    top25_pitcher_cols = ["player_name", "fantasy_team", "auction_value",
                          "production_value", "salary", "surplus", "W", "SV", "SO", "ERA", "WHIP"]

    has_surplus = df["surplus"].notna()
    surplus_top = df[has_surplus].sort_values("surplus", ascending=False)
    overpaid_top = df[has_surplus].sort_values("surplus", ascending=True)
    surplus_cols = ["player_name", "fantasy_team", "position", "auction_value",
                    "production_value", "salary", "surplus"]

    qmd_content = f"""---
title: "SGP Validation Report — {year}"
format:
  html:
    toc: true
    theme: cosmo
    self-contained: true
---

## Summary

| Metric | Value | Expected | Status |
|--------|-------|----------|--------|
| Total auction pool | ${total_dollars:,.0f} | ${config.total_auction_pool:,} | {"OK" if abs(total_dollars - config.total_auction_pool) < 50 else "CHECK"} |
| Production hitter % | {split.get('hitter_pct', 0):.1f}% | 60-67% | {"OK" if 55 <= split.get('hitter_pct', 0) <= 75 else "CHECK"} |
| Auction split | {split.get('hitter_pct', 63):.1f}% / {100 - split.get('hitter_pct', 63):.1f}% | from historical spending | OK |
| Positive-PAR hitters | {pos_par_h} | 120-170 | {"OK" if 100 <= pos_par_h <= 200 else "CHECK"} |
| Positive-PAR pitchers | {pos_par_p} | 80-130 | {"OK" if 60 <= pos_par_p <= 150 else "CHECK"} |

## Dollar Value Distribution

![Dollar value distribution](../plots/validation_dollar_dist_{year}.png)

## Top 25 Most Valuable Hitters

{_fmt_table(hitters, top25_hitter_cols)}

## Top 25 Most Valuable Pitchers

{_fmt_table(pitchers, top25_pitcher_cols)}

## Top 25 Surplus Players (Value - Salary)

{_fmt_table(surplus_top, surplus_cols)}

## Top 25 Overpaid Players (Salary - Value)

{_fmt_table(overpaid_top, surplus_cols)}

## Model Value vs. Actual Salary

![Value vs salary scatter](../plots/validation_value_vs_salary_{year}.png)

## Category SGP Leaders

![SGP leaders by category](../plots/validation_sgp_leaders_{year}.png)
"""

    report_path = REPORTS_DIR / f"validation-{year}.qmd"
    report_path.write_text(qmd_content)
    print(f"  Report written to {report_path}")

    # Try to render with Quarto
    try:
        result = subprocess.run(
            ["quarto", "render", str(report_path)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            html_path = report_path.with_suffix(".html")
            print(f"  Rendered: {html_path}")
        else:
            print(f"  Quarto render failed: {result.stderr[:200]}")
    except FileNotFoundError:
        print("  Quarto not found, skipping render (report .qmd is still available)")
    except subprocess.TimeoutExpired:
        print("  Quarto render timed out")


def generate_stretch_diagnostics(years: list[int] = None, config: SGPConfig = None):
    """Generate multi-year stretch diagnostics across all validated years.

    1. Year-over-year surplus: players who are repeatedly undervalued
    2. Team-level drafting skill: which teams consistently find surplus
    3. Position scarcity: model vs market valuation by position
    """
    import matplotlib.pyplot as plt

    if years is None:
        years = [2019, 2021, 2022, 2023, 2024]
    if config is None:
        config = SGPConfig.composite()

    PLOTS_DIR.mkdir(exist_ok=True)

    # Load all valuations
    frames = []
    for year in years:
        path = DATA_DIR / f"player_valuations_{year}.csv"
        if path.exists():
            df = pd.read_csv(path)
            df["year"] = year
            frames.append(df)
    if not frames:
        print("No valuation files found. Run validate_year() first.")
        return

    all_df = pd.concat(frames, ignore_index=True)
    has_surplus = all_df["surplus"].notna()

    # --- 1. Year-over-year surplus ---
    print("\n=== Stretch Diagnostic: Repeat Surplus Players ===")
    surplus_df = all_df[has_surplus & (all_df["auction_value"] > 0)].copy()
    player_years = surplus_df.groupby("player_name").agg(
        n_years=("year", "nunique"),
        mean_surplus=("surplus", "mean"),
        total_surplus=("surplus", "sum"),
        years=("year", lambda x: sorted(int(y) for y in x.unique())),
    ).reset_index()
    repeat_surplus = player_years[
        (player_years["n_years"] >= 2) & (player_years["mean_surplus"] > 10)
    ].sort_values("mean_surplus", ascending=False)

    if not repeat_surplus.empty:
        print(f"\nPlayers with mean surplus > $10 across 2+ years:")
        print(f"  {'Player':<25s} {'Years':>5s} {'Avg Surplus':>12s} {'Total':>8s}  Seasons")
        for _, row in repeat_surplus.head(15).iterrows():
            print(f"  {row['player_name']:<25s} {row['n_years']:>5d} "
                  f"  ${row['mean_surplus']:>8.1f}  ${row['total_surplus']:>6.0f}"
                  f"  {row['years']}")

    # Also show repeat overpaid
    repeat_overpaid = player_years[
        (player_years["n_years"] >= 2) & (player_years["mean_surplus"] < -10)
    ].sort_values("mean_surplus", ascending=True)

    if not repeat_overpaid.empty:
        print(f"\nRepeatedly overpaid (mean surplus < -$10 across 2+ years):")
        print(f"  {'Player':<25s} {'Years':>5s} {'Avg Surplus':>12s}  Seasons")
        for _, row in repeat_overpaid.head(10).iterrows():
            print(f"  {row['player_name']:<25s} {row['n_years']:>5d} "
                  f"  ${row['mean_surplus']:>8.1f}  {row['years']}")

    # --- 2. Team-level drafting skill ---
    print("\n=== Stretch Diagnostic: Team Drafting Skill ===")
    team_surplus = surplus_df.groupby(["fantasy_team", "year"]).agg(
        total_surplus=("surplus", "sum"),
        n_players=("player_name", "nunique"),
        mean_surplus=("surplus", "mean"),
    ).reset_index()

    team_avg = team_surplus.groupby("fantasy_team").agg(
        seasons=("year", "nunique"),
        avg_total_surplus=("total_surplus", "mean"),
        avg_per_player=("mean_surplus", "mean"),
    ).sort_values("avg_total_surplus", ascending=False).reset_index()

    if not team_avg.empty:
        print(f"\n  {'Team':<20s} {'Seasons':>7s} {'Avg Total Surplus':>18s} {'Avg/Player':>11s}")
        for _, row in team_avg.iterrows():
            print(f"  {row['fantasy_team']:<20s} {row['seasons']:>7d}"
                  f"    ${row['avg_total_surplus']:>12.0f}"
                  f"    ${row['avg_per_player']:>6.1f}")

    # Team drafting skill plot
    if len(team_surplus) > 0:
        fig, ax = plt.subplots(figsize=(12, 6))
        teams = team_avg["fantasy_team"].values
        for team in teams:
            td = team_surplus[team_surplus["fantasy_team"] == team]
            ax.plot(td["year"], td["total_surplus"], "o-", label=team, markersize=5)
        ax.axhline(0, color="black", linestyle="--", alpha=0.3)
        ax.set_xlabel("Year")
        ax.set_ylabel("Total Team Surplus ($)")
        ax.set_title("Team Drafting Skill — Total Surplus by Year")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "stretch_team_drafting_skill.png", dpi=150)
        plt.close(fig)

    # --- 3. Position scarcity ---
    print("\n=== Stretch Diagnostic: Position Scarcity ===")
    pos_df = surplus_df[surplus_df["position"].notna()].copy()
    # Normalize multi-position eligibility to primary position
    pos_summary = pos_df.groupby("position").agg(
        n_players=("player_name", "nunique"),
        avg_auction=("auction_value", "mean"),
        avg_salary=("salary", "mean"),
        avg_surplus=("surplus", "mean"),
    ).sort_values("avg_surplus", ascending=False).reset_index()

    if not pos_summary.empty:
        print(f"\n  {'Position':<10s} {'Players':>8s} {'Avg Auction':>12s} {'Avg Salary':>11s} {'Avg Surplus':>12s}")
        for _, row in pos_summary.iterrows():
            print(f"  {row['position']:<10s} {row['n_players']:>8d}"
                  f"    ${row['avg_auction']:>8.1f}"
                  f"    ${row['avg_salary']:>7.1f}"
                  f"    {row['avg_surplus']:>+8.1f}")

    # Position scarcity plot
    if not pos_summary.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        positions = pos_summary["position"].values
        x = range(len(positions))
        width = 0.35
        ax.bar([i - width/2 for i in x], pos_summary["avg_auction"], width,
               label="Avg Auction Value", color="#2196F3", edgecolor="black")
        ax.bar([i + width/2 for i in x], pos_summary["avg_salary"], width,
               label="Avg Salary", color="#FF5722", edgecolor="black")
        ax.set_xticks(list(x))
        ax.set_xticklabels(positions, rotation=45, ha="right")
        ax.set_ylabel("Dollars ($)")
        ax.set_title("Position Scarcity — Model Value vs. Market Price")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "stretch_position_scarcity.png", dpi=150)
        plt.close(fig)

    print(f"\n  Stretch plots saved to {PLOTS_DIR}/stretch_*.png")


def main():
    parser = argparse.ArgumentParser(
        description="Validate SGP model with actual player stats"
    )
    parser.add_argument(
        "--year", type=int, required=True,
        help="Year to validate (e.g., 2024)"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Generate Quarto validation report"
    )
    parser.add_argument(
        "--plots", action="store_true",
        help="Generate diagnostic plots (included automatically with --report)"
    )
    parser.add_argument(
        "--stretch", action="store_true",
        help="Generate multi-year stretch diagnostics"
    )
    args = parser.parse_args()

    df = validate_year(args.year)

    if args.plots or args.report:
        generate_validation_plots(df, args.year)

    if args.report:
        generate_report(df, args.year)

    if args.stretch:
        generate_stretch_diagnostics()


if __name__ == "__main__":
    main()

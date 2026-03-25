"""CLI runner for MSP targeting model.

Usage:
    python3 -m targeting [--team TEAM] [--system atc|thebatx|combined]
                         [--fill-discount FLOAT] [--no-displacement]
                         [--output PATH]
"""

import argparse
import sys

import pandas as pd

from targeting.model import MSPConfig, run_msp, compute_tps

DEFAULT_TEAM = "Gusteroids"

# Best proportional_fill config from sweep
DEFAULT_CONFIG = MSPConfig(
    baseline_type="proportional_fill",
    fill_discount=0.5,
    budget_displacement=True,
)

VALUATION_FILES = {
    "atc": "data/valuations_atc_2026.csv",
    "thebatx": "data/valuations_thebatx_2026.csv",
    "combined": "data/valuations_combined_2026.csv",
}

KEEPER_FILE = "data/preauction_rosters_2026.csv"


def load_data(system: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load keeper rosters and valuations."""
    keepers = pd.read_csv(KEEPER_FILE)

    val_path = VALUATION_FILES[system]
    valuations = pd.read_csv(val_path)

    # Ensure is_pitcher column exists
    if "is_pitcher" not in valuations.columns and "pos_type" in valuations.columns:
        valuations["is_pitcher"] = valuations["pos_type"] == "pitcher"

    return keepers, valuations


def format_results(msp_results: pd.DataFrame, standings: pd.DataFrame, team: str) -> str:
    """Format MSP results for display."""
    lines = []

    # Projected standings
    lines.append("=" * 80)
    lines.append("PROJECTED STANDINGS (with keeper + fill)")
    lines.append("=" * 80)
    st = standings.sort_values("total_pts", ascending=False)
    rank_cols = [c for c in st.columns if c.startswith("rank_")]
    display_cols = ["team", "total_pts"] + rank_cols
    lines.append(st[display_cols].to_string(index=False))

    # Team's category breakdown
    lines.append("")
    team_row = standings[standings["team"] == team].iloc[0]
    lines.append(f"--- {team} category ranks ---")
    from targeting.model import ALL_CATEGORIES
    for cat in ALL_CATEGORIES:
        val = team_row[cat]
        rank = team_row[f"rank_{cat}"]
        lines.append(f"  {cat:>5s}: {val:>10.3f}  (rank {rank:.1f})")
    lines.append(f"  {'TOTAL':>5s}: {' ' * 10}  ({team_row['total_pts']:.1f} pts)")

    # Top MSP targets
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"TOP MSP TARGETS FOR {team.upper()}")
    lines.append("=" * 80)

    top = msp_results[msp_results["dollar_value"] >= 1].nlargest(40, "tps").copy()
    display = top[["player_name", "pos_type", "position", "dollar_value", "msp", "msp_per_dollar", "tps"]].copy()
    display["dollar_value"] = display["dollar_value"].round(1)
    display["msp"] = display["msp"].round(3)
    display["msp_per_dollar"] = display["msp_per_dollar"].round(4)
    display.columns = ["Player", "Type", "Pos", "$Value", "MSP", "MSP/$", "TPS"]
    lines.append(display.to_string(index=False))

    # Top MSP per dollar (min $1 value)
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"TOP MSP EFFICIENCY (MSP per dollar) FOR {team.upper()}")
    lines.append("=" * 80)

    efficient = msp_results[msp_results["dollar_value"] >= 5].nlargest(40, "msp_per_dollar").copy()
    display2 = efficient[["player_name", "pos_type", "position", "dollar_value", "msp", "msp_per_dollar", "tps"]].copy()
    display2["dollar_value"] = display2["dollar_value"].round(1)
    display2["msp"] = display2["msp"].round(3)
    display2["msp_per_dollar"] = display2["msp_per_dollar"].round(4)
    display2.columns = ["Player", "Type", "Pos", "$Value", "MSP", "MSP/$", "TPS"]
    lines.append(display2.to_string(index=False))

    # Category-level breakdown for top targets
    lines.append("")
    lines.append("=" * 80)
    lines.append("CATEGORY IMPACT — TOP 20 MSP TARGETS")
    lines.append("=" * 80)

    delta_cols = [f"delta_rank_{cat}" for cat in ALL_CATEGORIES]
    top20 = msp_results[msp_results["dollar_value"] >= 1].nlargest(20, "msp").copy()
    cat_display = top20[["player_name", "msp"] + delta_cols].copy()
    cat_display["msp"] = cat_display["msp"].round(3)
    for col in delta_cols:
        cat_display[col] = cat_display[col].apply(lambda x: f"{x:+.1f}" if x != 0 else ".")
    short_cols = ["Player", "MSP"] + [cat.replace("delta_rank_", "") for cat in delta_cols]
    cat_display.columns = short_cols
    lines.append(cat_display.to_string(index=False))

    # Strategic needs summary
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"STRATEGIC NEEDS SUMMARY — {team.upper()}")
    lines.append("=" * 80)

    # Aggregate: which categories do top targets most often improve?
    positive_targets = msp_results[msp_results["msp"] > 0]
    if not positive_targets.empty:
        cat_impact = {}
        for cat in ALL_CATEGORIES:
            col = f"delta_rank_{cat}"
            # Sum of positive rank changes weighted by MSP
            gains = positive_targets[positive_targets[col] > 0]
            cat_impact[cat] = {
                "current_rank": team_row[f"rank_{cat}"],
                "n_players_help": len(gains),
                "avg_gain": gains[col].mean() if len(gains) > 0 else 0,
                "total_weighted_gain": (gains[col] * gains["msp"]).sum(),
            }

        lines.append(f"  {'Category':>8s}  {'Rank':>5s}  {'Upside':>8s}  {'# Help':>7s}  {'Avg Gain':>9s}")
        lines.append(f"  {'--------':>8s}  {'-----':>5s}  {'------':>8s}  {'------':>7s}  {'---------':>9s}")
        # Sort by upside potential (total weighted gain)
        for cat, info in sorted(cat_impact.items(), key=lambda x: -x[1]["total_weighted_gain"]):
            rank_str = f"{info['current_rank']:.0f}/10"
            lines.append(
                f"  {cat:>8s}  {rank_str:>5s}  {info['total_weighted_gain']:>8.1f}"
                f"  {info['n_players_help']:>7d}  {info['avg_gain']:>+9.2f}"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MSP targeting model")
    parser.add_argument("--team", default=DEFAULT_TEAM, help="Target team name")
    parser.add_argument("--system", default="atc", choices=VALUATION_FILES.keys(),
                        help="Projection system to use")
    parser.add_argument("--fill-discount", type=float, default=DEFAULT_CONFIG.fill_discount,
                        help="Fill discount factor (0-1)")
    parser.add_argument("--no-displacement", action="store_true",
                        help="Disable budget displacement")
    parser.add_argument("--baseline", default=DEFAULT_CONFIG.baseline_type,
                        choices=["proportional_fill", "keeper_only"],
                        help="Baseline type")
    parser.add_argument("--output", "-o", help="Output CSV path")
    args = parser.parse_args()

    config = MSPConfig(
        baseline_type=args.baseline,
        fill_discount=args.fill_discount,
        budget_displacement=not args.no_displacement,
    )

    print(f"Loading data (system={args.system})...")
    keepers, valuations = load_data(args.system)

    print(f"Computing MSP for {args.team} ({config.label()})...")
    msp_results, standings = run_msp(keepers, valuations, args.team, config)
    msp_results = compute_tps(msp_results)

    print(format_results(msp_results, standings, args.team))

    # Always save CSV output
    output_path = args.output or f"data/msp_{args.team.lower().replace(' ', '_')}_{args.system}_2026.csv"
    out = msp_results.sort_values("msp", ascending=False)
    out.to_csv(output_path, index=False)
    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()

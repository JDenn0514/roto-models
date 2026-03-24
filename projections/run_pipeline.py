"""End-to-end projection pipeline: fetch → transform → valuate → output."""

import argparse
from pathlib import Path

import pandas as pd

from projections.fetch import fetch_all, fetch_projections
from projections.transform import build_player_projections, fill_minor_leaguers
from projections.valuate import compute_projected_values
from sgp.dollar_values import compute_hitter_pitcher_split

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

MIN_PA = 25
MIN_IP = 5


def run_pipeline(
    season: int = 2026,
    force_refresh: bool = False,
    system: str | None = None,
    include_batx: bool = True,
) -> dict[str, pd.DataFrame]:
    """Run the full projection → valuation pipeline.

    Parameters
    ----------
    season : int
        Projection season
    force_refresh : bool
        Bypass cache and re-fetch from FanGraphs
    system : str, optional
        If set, only run for this system ("atc", "thebatx")
    include_batx : bool
        Whether to fetch THE BAT X for cross-reference

    Returns
    -------
    dict with keys: "atc", optionally "thebatx", "combined"
    """
    results = {}

    # --- Fetch ---
    print("=" * 60)
    print(f"FETCHING PROJECTIONS — {season}")
    print("=" * 60)

    raw = fetch_all(
        season=season,
        force_refresh=force_refresh,
        include_batx=include_batx and system != "atc",
    )

    # --- Depth Charts for minor leaguer fill ---
    dc_bat = raw.get("fangraphsdc_bat", pd.DataFrame())
    dc_pit = raw.get("fangraphsdc_pit", pd.DataFrame())

    # --- ATC (primary) ---
    if system is None or system == "atc":
        print("\n" + "=" * 60)
        print("PROCESSING ATC (PRIMARY)")
        print("=" * 60)

        atc = build_player_projections(
            raw["atc_bat"], raw["atc_pit"], "atc", min_pa=MIN_PA, min_ip=MIN_IP
        )
        if not dc_bat.empty and not dc_pit.empty:
            atc = fill_minor_leaguers(atc, dc_bat, dc_pit, min_pa=MIN_PA, min_ip=MIN_IP)

        print(f"  Total players: {len(atc)} ({(atc['pos_type']=='hitter').sum()} hitters, "
              f"{(atc['pos_type']=='pitcher').sum()} pitchers)")
        print(f"  Teams: {atc['team'].nunique()}")

        print("\n  Computing valuations...")
        atc_valued = compute_projected_values(atc)
        _save_valuations(atc_valued, f"valuations_atc_{season}.csv")
        results["atc"] = atc_valued

    # --- THE BAT X (cross-reference) ---
    if (system is None or system == "thebatx") and include_batx:
        print("\n" + "=" * 60)
        print("PROCESSING THE BAT X (CROSS-REFERENCE)")
        print("=" * 60)

        if f"thebatx_bat" not in raw:
            # Fetch if not already fetched
            raw["thebatx_bat"] = fetch_projections("thebatx", "bat", season=season, force_refresh=force_refresh)
            raw["thebatx_pit"] = fetch_projections("thebatx", "pit", season=season, force_refresh=force_refresh)

        batx = build_player_projections(
            raw["thebatx_bat"], raw["thebatx_pit"], "thebatx", min_pa=MIN_PA, min_ip=MIN_IP
        )
        if not dc_bat.empty and not dc_pit.empty:
            batx = fill_minor_leaguers(batx, dc_bat, dc_pit, min_pa=MIN_PA, min_ip=MIN_IP)

        print(f"  Total players: {len(batx)} ({(batx['pos_type']=='hitter').sum()} hitters, "
              f"{(batx['pos_type']=='pitcher').sum()} pitchers)")

        print("\n  Computing valuations...")
        batx_valued = compute_projected_values(batx)
        _save_valuations(batx_valued, f"valuations_thebatx_{season}.csv")
        results["thebatx"] = batx_valued

    # --- Combined output ---
    if "atc" in results and "thebatx" in results:
        print("\n" + "=" * 60)
        print("BUILDING COMBINED OUTPUT")
        print("=" * 60)
        combined = _build_combined(results["atc"], results["thebatx"])
        _save_valuations(combined, f"valuations_combined_{season}.csv")
        results["combined"] = combined

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, df in results.items():
        if name == "combined":
            continue
        _print_summary(name, df)

    return results


def _save_valuations(df: pd.DataFrame, filename: str):
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    print(f"\n  Saved to {path}")


def _build_combined(atc_df: pd.DataFrame, batx_df: pd.DataFrame) -> pd.DataFrame:
    """Build side-by-side comparison with ATC dollar values as authoritative."""
    # Rename dollar columns for clarity
    atc_slim = atc_df[["fg_id", "player_name", "team", "pos_type", "position",
                        "PA", "AB", "IP",
                        "R", "HR", "RBI", "SB", "AVG",
                        "W", "SV", "ERA", "WHIP", "SO",
                        "total_sgp", "par", "dollar_value"]].copy()
    atc_slim = atc_slim.rename(columns={
        "total_sgp": "sgp_atc",
        "par": "par_atc",
        "dollar_value": "dollar_value",  # authoritative
    })

    batx_cols = ["fg_id",
                 "R", "HR", "RBI", "SB", "AVG",
                 "W", "SV", "ERA", "WHIP", "SO",
                 "total_sgp", "par", "dollar_value"]
    batx_slim = batx_df[batx_cols].copy()
    batx_slim = batx_slim.rename(columns={
        col: f"{col}_batx" for col in ["R", "HR", "RBI", "SB", "AVG",
                                         "W", "SV", "ERA", "WHIP", "SO",
                                         "total_sgp", "par", "dollar_value"]
    })

    combined = atc_slim.merge(batx_slim, on="fg_id", how="outer", indicator=True)

    # Flag which system(s) the player appears in
    combined["systems"] = combined["_merge"].map({
        "left_only": "atc",
        "right_only": "thebatx",
        "both": "both",
    })
    combined = combined.drop(columns=["_merge"])

    # Sort by ATC dollar value descending
    combined = combined.sort_values("dollar_value", ascending=False, na_position="last")

    return combined.reset_index(drop=True)


def _print_summary(name: str, df: pd.DataFrame):
    """Print summary stats for a valuation."""
    print(f"\n--- {name.upper()} ---")

    split = compute_hitter_pitcher_split(df)
    total = split["total"]
    print(f"  Total dollar pool: ${total:,.0f}")
    print(f"  Hitter/pitcher split: {split['hitter_pct']:.1f}% / {split['pitcher_pct']:.1f}%")
    print(f"  Hitter dollars: ${split['hitter_dollars']:,.0f}")
    print(f"  Pitcher dollars: ${split['pitcher_dollars']:,.0f}")

    positive = df[df["dollar_value"] > 0]
    n_hitters = (positive["pos_type"] == "hitter").sum()
    n_pitchers = (positive["pos_type"] == "pitcher").sum()
    print(f"  Positive-value players: {len(positive)} ({n_hitters} hitters, {n_pitchers} pitchers)")

    teams = df["team"].nunique()
    print(f"  Teams represented: {teams}")

    # Top hitters
    hitters = df[df["pos_type"] == "hitter"].nlargest(15, "dollar_value")
    print(f"\n  Top 15 hitters:")
    for _, row in hitters.iterrows():
        print(f"    ${row['dollar_value']:5.1f}  {row['player_name']:<25s} {row['team']}  {row['position']}")

    # Top pitchers
    pitchers = df[df["pos_type"] == "pitcher"].nlargest(15, "dollar_value")
    print(f"\n  Top 15 pitchers:")
    for _, row in pitchers.iterrows():
        print(f"    ${row['dollar_value']:5.1f}  {row['player_name']:<25s} {row['team']}  {row['position']}")


def main():
    parser = argparse.ArgumentParser(description="Projection → Valuation Pipeline")
    parser.add_argument("--season", type=int, default=2026, help="Projection season")
    parser.add_argument("--force-refresh", action="store_true", help="Bypass cache")
    parser.add_argument("--system", choices=["atc", "thebatx"], help="Run single system only")
    parser.add_argument("--no-batx", action="store_true", help="Skip THE BAT X cross-reference")
    args = parser.parse_args()

    run_pipeline(
        season=args.season,
        force_refresh=args.force_refresh,
        system=args.system,
        include_batx=not args.no_batx,
    )


if __name__ == "__main__":
    main()

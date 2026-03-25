"""Autoresearch sweep for the MSP targeting model.

Loops over 18 config variants (3 baseline types × 3 fill discounts × 2 displacement)
across 6 validation years, aggregates metrics, and outputs results.

Usage:
    python3 -m targeting.sweep [--output PATH] [--verbose]
"""

import argparse
import itertools
import sys
import time

import pandas as pd

from targeting.backtest import run_backtest
from targeting.model import MSPConfig

# Sweep parameter grid
BASELINE_TYPES = ["proportional_fill", "keeper_only"]
FILL_DISCOUNTS = [0.50, 0.75, 1.0]
DISPLACEMENT_OPTIONS = [True, False]


def generate_configs() -> list[MSPConfig]:
    """Generate all config variants for the sweep."""
    configs = []
    for bt, fd, disp in itertools.product(BASELINE_TYPES, FILL_DISCOUNTS, DISPLACEMENT_OPTIONS):
        # keeper_only doesn't use fill_discount or displacement — only run once
        if bt == "keeper_only" and (fd != 0.75 or disp is not True):
            continue
        configs.append(MSPConfig(baseline_type=bt, fill_discount=fd, budget_displacement=disp))
    return configs


def run_sweep(verbose: bool = False) -> pd.DataFrame:
    """Run the full sweep and return results DataFrame."""
    configs = generate_configs()
    results = []

    if verbose:
        print(f"Running sweep: {len(configs)} configs")
        print()

    for i, config in enumerate(configs):
        label = config.label()
        if verbose:
            print(f"[{i+1}/{len(configs)}] {label}")

        t0 = time.time()
        result = run_backtest(config, verbose=verbose)
        elapsed = time.time() - t0

        agg = result["aggregate"]
        row = {
            "config": label,
            "baseline_type": config.baseline_type,
            "fill_discount": config.fill_discount,
            "budget_displacement": config.budget_displacement,
            "predicted_vs_actual_r": agg["predicted_vs_actual_r"],
            "draftee_msp_r": agg["draftee_msp_r"],
            "draft_auc": agg["draft_auc"],
            "draft_percentile": agg["draft_percentile"],
            "optimal_uplift_mean": agg["optimal_uplift_mean"],
            "optimal_uplift_median": agg["optimal_uplift_median"],
            "elapsed_s": round(elapsed, 1),
        }
        results.append(row)

        if verbose:
            print(f"  pred_r={agg['predicted_vs_actual_r']:.3f}  "
                  f"msp_r={agg['draftee_msp_r']:.3f}  "
                  f"AUC={agg['draft_auc']:.3f}  "
                  f"uplift={agg['optimal_uplift_mean']:.1f}  "
                  f"({elapsed:.1f}s)")
            print()

        # METRIC lines for autoresearch.sh compatibility
        print(f"METRIC config={label}")
        print(f"METRIC predicted_vs_actual_r={agg['predicted_vs_actual_r']:.4f}")
        print(f"METRIC draftee_msp_r={agg['draftee_msp_r']:.4f}")
        print(f"METRIC draft_auc={agg['draft_auc']:.4f}")
        print(f"METRIC draft_percentile={agg['draft_percentile']:.4f}")
        print(f"METRIC optimal_uplift_mean={agg['optimal_uplift_mean']:.4f}")
        sys.stdout.flush()

    return pd.DataFrame(results)


def print_summary(df: pd.DataFrame):
    """Print a summary of sweep results, highlighting the best config."""
    print()
    print("=" * 90)
    print("SWEEP RESULTS SUMMARY")
    print("=" * 90)

    # Sort by primary metric (predicted_vs_actual_r)
    display = df.sort_values("predicted_vs_actual_r", ascending=False).copy()
    display_cols = [
        "config", "predicted_vs_actual_r", "draftee_msp_r",
        "draft_auc", "optimal_uplift_mean",
    ]
    for col in display_cols[1:]:
        display[col] = display[col].round(4)
    print(display[display_cols].to_string(index=False))

    # Highlight winner
    best = display.iloc[0]
    print()
    print(f"BEST CONFIG (by predicted_vs_actual_r): {best['config']}")
    print(f"  predicted_vs_actual_r = {best['predicted_vs_actual_r']:.4f}")
    print(f"  draftee_msp_r         = {best['draftee_msp_r']:.4f}")
    print(f"  draft_auc             = {best['draft_auc']:.4f}")
    print(f"  optimal_uplift_mean   = {best['optimal_uplift_mean']:.4f}")


def main():
    parser = argparse.ArgumentParser(description="MSP targeting sweep")
    parser.add_argument("--output", "-o", default="data/targeting_sweep_results.csv",
                        help="Output CSV path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    df = run_sweep(verbose=args.verbose)
    df.to_csv(args.output, index=False)
    print(f"\nResults written to {args.output}")

    print_summary(df)


if __name__ == "__main__":
    main()

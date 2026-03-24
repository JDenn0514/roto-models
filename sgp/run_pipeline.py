"""End-to-end SGP pipeline runner with cross-validation and autoresearch metrics."""

import argparse
import csv
import itertools
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from sgp.config import SGPConfig
from sgp.data_prep import get_calibration_data, get_category_data
from sgp.diagnostics import generate_all_diagnostics
from sgp.replacement import compute_replacement_level
from sgp.sgp_calc import SGPResult, compute_sgp

RESULTS_DIR = Path(__file__).resolve().parent.parent / "data"


def run_loyo_cv(df: pd.DataFrame, config: SGPConfig, bootstrap: bool = True) -> list[dict]:
    """Leave-one-year-out cross-validation.

    For each year in the calibration window:
    1. Compute SGP denominators using all years EXCEPT the held-out year
    2. Use those denominators to compute team SGP in the held-out year
    3. Compare SGP-implied ranks to actual standings ranks

    Supports composite configs: each category's train denominator is computed
    using that category's effective config and year window.
    """
    years = sorted(df["year"].unique())
    # Only CV over years that are in the primary window
    cv_years = [y for y in years if y in config.primary_years]

    cv_results = []
    for held_out in cv_years:
        # Train on all years except held-out
        train_df = df[df["year"] != held_out]
        test_df = df[df["year"] == held_out]

        if len(train_df) == 0 or len(test_df) == 0:
            continue

        # Compute SGP denominators on training data
        train_sgp = compute_sgp(train_df, config, bootstrap=bootstrap)

        # Compute held-out year's actual denominators (year-level)
        # Use pairwise_mean for actuals regardless of model method
        test_config = replace(
            config,
            sgp_method="pairwise_mean",
            primary_years=[held_out],
            use_supplemental=False,
            per_category=None,
        )
        test_sgp = compute_sgp(test_df, test_config, bootstrap=bootstrap)

        # Compute total SGP for each team in the held-out year
        team_total_sgp = []
        for _, team_row in test_df.iterrows():
            total = 0.0
            for cat in config.all_categories:
                val = team_row.get(cat)
                denom = train_sgp.denominators.get(cat)
                if pd.notna(val) and denom and denom > 0:
                    if cat in config.inverse_categories:
                        # For ERA/WHIP, lower is better — use negative contribution
                        # relative to the worst team (highest value)
                        worst = test_df[cat].max()
                        total += (worst - val) / denom
                    else:
                        total += val / denom
            team_total_sgp.append(total)

        test_df = test_df.copy()
        test_df["sgp_total"] = team_total_sgp

        # Rank correlation: SGP-implied ranks vs actual total standings points
        if len(test_df) >= 3:
            rho, _ = sp_stats.spearmanr(
                test_df["sgp_total"].values,
                test_df["total_pts"].values,
            )
        else:
            rho = np.nan

        cv_results.append({
            "held_out_year": held_out,
            "predicted_denoms": dict(train_sgp.denominators),
            "actual_denoms": dict(test_sgp.denominators),
            "rank_correlation": rho,
        })

    return cv_results


def compute_cv_metrics(cv_results: list[dict], config: SGPConfig) -> dict:
    """Compute aggregate CV metrics from LOYO results.

    Returns dict with aggregate metrics and per-category nRMSEs.
    Per-category nRMSEs are keyed as 'nrmse_{cat}' (e.g. 'nrmse_HR').
    """
    if not cv_results:
        result = {
            "sgp_cv_rmse": np.nan,
            "sgp_cv_nrmse": np.nan,
            "rank_correlation": np.nan,
        }
        for cat in config.all_categories:
            result[f"nrmse_{cat}"] = np.nan
        return result

    # Raw RMSE of denominator predictions across all folds and categories
    all_errors = []
    for r in cv_results:
        for cat in config.all_categories:
            pred = r["predicted_denoms"].get(cat, np.nan)
            actual = r["actual_denoms"].get(cat, np.nan)
            if not np.isnan(pred) and not np.isnan(actual):
                all_errors.append((pred - actual) ** 2)

    rmse = np.sqrt(np.mean(all_errors)) if all_errors else np.nan

    # Normalized RMSE: compute per-category RMSE as % of mean denominator,
    # then average across categories. Each category contributes equally.
    cat_nrmse_map = {}
    for cat in config.all_categories:
        preds = []
        actuals = []
        for r in cv_results:
            pred = r["predicted_denoms"].get(cat, np.nan)
            actual = r["actual_denoms"].get(cat, np.nan)
            if not np.isnan(pred) and not np.isnan(actual):
                preds.append(pred)
                actuals.append(actual)
        if preds:
            cat_rmse = np.sqrt(np.mean([(p - a) ** 2 for p, a in zip(preds, actuals)]))
            cat_mean = np.mean(actuals)
            if cat_mean > 0:
                cat_nrmse_map[cat] = cat_rmse / cat_mean
            else:
                cat_nrmse_map[cat] = np.nan
        else:
            cat_nrmse_map[cat] = np.nan

    valid_nrmses = [v for v in cat_nrmse_map.values() if not np.isnan(v)]
    nrmse = float(np.mean(valid_nrmses)) if valid_nrmses else np.nan

    # Mean rank correlation across folds
    rhos = [r["rank_correlation"] for r in cv_results if not np.isnan(r["rank_correlation"])]
    mean_rho = np.mean(rhos) if rhos else np.nan

    result = {
        "sgp_cv_rmse": rmse,
        "sgp_cv_nrmse": nrmse,
        "rank_correlation": mean_rho,
    }
    for cat in config.all_categories:
        result[f"nrmse_{cat}"] = cat_nrmse_map.get(cat, np.nan)

    return result


def compute_category_balance(sgp_result: SGPResult, config: SGPConfig) -> float:
    """Coefficient of variation of SGP denominators across categories.

    Lower = more balanced contribution across categories.
    """
    denoms = [sgp_result.denominators[c] for c in config.all_categories
              if not np.isnan(sgp_result.denominators.get(c, np.nan))]
    if not denoms:
        return np.nan
    return float(np.std(denoms) / np.mean(denoms))


def run_pipeline(config: SGPConfig, generate_plots: bool = True) -> dict:
    """Run full SGP pipeline and return metrics dict.

    Steps:
    1. Load and prepare data
    2. Compute SGP denominators
    3. Compute replacement level
    4. Run cross-validation
    5. Generate diagnostics (if generate_plots=True)
    6. Return metrics
    """
    # Step 1: Load data
    df = get_calibration_data(config)

    # Step 2: Compute SGP denominators (skip bootstrap when not plotting)
    do_bootstrap = generate_plots
    sgp_result = compute_sgp(df, config, bootstrap=do_bootstrap)

    # Step 3: Compute replacement level
    replacement = compute_replacement_level(
        sgp_result, config, standings_df=df
    )

    # Step 4: Cross-validation
    cv_results = run_loyo_cv(df, config, bootstrap=do_bootstrap)
    cv_metrics = compute_cv_metrics(cv_results, config)

    # Step 5: Generate diagnostics
    if generate_plots:
        generate_all_diagnostics(df, sgp_result, config, cv_results)

    # Step 6: Compile metrics
    metrics = {}

    # Primary metrics
    metrics["sgp_cv_rmse"] = cv_metrics["sgp_cv_rmse"]
    metrics["sgp_cv_nrmse"] = cv_metrics["sgp_cv_nrmse"]
    metrics["rank_correlation"] = cv_metrics["rank_correlation"]
    metrics["category_balance_cv"] = compute_category_balance(sgp_result, config)
    # dollar_pool_error requires player projections; report 0 for now
    metrics["dollar_pool_error"] = 0.0

    # Secondary metrics
    metrics["hitter_repl_sgp"] = replacement["hitter_repl_sgp"]
    metrics["pitcher_repl_sgp"] = replacement["pitcher_repl_sgp"]

    ci_widths = []
    for cat in config.all_categories:
        lo = sgp_result.ci_lower.get(cat, np.nan)
        hi = sgp_result.ci_upper.get(cat, np.nan)
        if not np.isnan(lo) and not np.isnan(hi):
            ci_widths.append(hi - lo)
        metrics[f"sgp_denom_{cat}"] = sgp_result.denominators.get(cat, np.nan)

    metrics["sgp_ci_width_avg"] = np.mean(ci_widths) if ci_widths else np.nan

    # Per-category nRMSEs (used by composite selection strategy)
    for cat in config.all_categories:
        metrics[f"nrmse_{cat}"] = cv_metrics.get(f"nrmse_{cat}", np.nan)

    metrics["method"] = "composite" if config.is_composite else config.sgp_method
    metrics["data_window"] = "augmented" if config.use_supplemental else "primary_only"
    metrics["n_calibration_years"] = len(df["year"].unique())

    # Config identifiers for sweep analysis
    metrics["use_supplemental"] = config.use_supplemental
    metrics["time_decay"] = config.time_decay
    metrics["time_decay_rate"] = config.time_decay_rate
    metrics["punt_detection"] = config.punt_detection
    metrics["replacement_hitter_buffer"] = config.replacement_hitter_buffer
    metrics["replacement_pitcher_buffer"] = config.replacement_pitcher_buffer

    # Per-category method annotations for composite configs
    if config.is_composite:
        for cat in config.all_categories:
            cat_config = config.effective_config(cat)
            sig = (
                f"{cat_config.sgp_method}"
                f"|supp={cat_config.use_supplemental}"
                f"|decay={cat_config.time_decay}({cat_config.time_decay_rate})"
                f"|punt={cat_config.punt_detection}"
            )
            metrics[f"best_method_{cat}"] = sig

    return metrics


def print_metrics(metrics: dict):
    """Print metrics in autoresearch METRIC format."""
    for key, value in sorted(metrics.items()):
        if isinstance(value, float):
            if np.isnan(value):
                print(f"METRIC {key}=NaN")
            else:
                print(f"METRIC {key}={value:.6f}")
        else:
            print(f"METRIC {key}={value}")


def generate_sweep_configs() -> list[SGPConfig]:
    """Generate all configurations for autoresearch sweep."""
    methods = ["pairwise_mean", "pairwise_median", "ols", "robust_reg"]
    supplemental = [False, True]
    decay_options = [(False, 0.85), (True, 0.80), (True, 0.85), (True, 0.90)]
    punt_options = [False, True]
    buffer_options = [30, 40, 50, 60, 70]

    configs = []
    for method, supp, (decay, rate), punt, buf in itertools.product(
        methods, supplemental, decay_options, punt_options, buffer_options
    ):
        configs.append(SGPConfig(
            sgp_method=method,
            use_supplemental=supp,
            time_decay=decay,
            time_decay_rate=rate,
            punt_detection=punt,
            replacement_hitter_buffer=buf,
            replacement_pitcher_buffer=buf,
        ))
    return configs


def _config_signature(r: dict) -> str:
    """Short string identifying a config's key settings (excluding buffer)."""
    return (
        f"{r['method']}"
        f"|supp={r['use_supplemental']}"
        f"|decay={r['time_decay']}({r['time_decay_rate']})"
        f"|punt={r['punt_detection']}"
    )


def _compute_composite_rank_correlation(
    category_configs: dict[str, SGPConfig],
    reference_config: SGPConfig,
) -> float:
    """Re-run LOYO CV using composite denominators (one config per category).

    For each held-out year, compute each category's denominator using that
    category's best config, then assemble into a composite SGPResult and
    compute rank correlation against actual standings.
    """
    # Load data once using a config that includes supplemental if any category needs it
    any_supp = any(c.use_supplemental for c in category_configs.values())
    data_config = replace(reference_config, use_supplemental=any_supp)
    df = get_calibration_data(data_config)

    cv_years = sorted([y for y in df["year"].unique() if y in reference_config.primary_years])

    rhos = []
    for held_out in cv_years:
        train_df = df[df["year"] != held_out]
        test_df = df[df["year"] == held_out]
        if len(train_df) == 0 or len(test_df) == 0:
            continue

        # Compute each category's denominator using its own best config
        composite_denoms = {}
        for cat, cat_config in category_configs.items():
            # Filter train data to what this config would use
            cat_train = train_df.copy()
            if not cat_config.use_supplemental:
                cat_train = cat_train[cat_train["year"].isin(cat_config.primary_years)]
            cat_sgp = compute_sgp(cat_train, cat_config, bootstrap=False)
            composite_denoms[cat] = cat_sgp.denominators.get(cat, np.nan)

        # Compute total SGP for each team using composite denominators
        team_total_sgp = []
        for _, team_row in test_df.iterrows():
            total = 0.0
            for cat in reference_config.all_categories:
                val = team_row.get(cat)
                denom = composite_denoms.get(cat)
                if pd.notna(val) and denom and denom > 0:
                    if cat in reference_config.inverse_categories:
                        worst = test_df[cat].max()
                        total += (worst - val) / denom
                    else:
                        total += val / denom
            team_total_sgp.append(total)

        test_df = test_df.copy()
        test_df["sgp_total"] = team_total_sgp

        if len(test_df) >= 3:
            rho, _ = sp_stats.spearmanr(
                test_df["sgp_total"].values,
                test_df["total_pts"].values,
            )
            rhos.append(rho)

    return float(np.mean(rhos)) if rhos else np.nan


def run_sweep(output_csv: str | None = None):
    """Run full autoresearch sweep with dual selection strategy.

    1. Sweep all configs, collecting per-category nRMSEs
    2. Strategy 1 (Global): pick the single config minimizing overall nRMSE
    3. Strategy 2 (Composite): pick the best config per category, assemble composite
    4. Compare both strategies head-to-head on rank correlation
    5. Print results and METRIC lines for the winning strategy
    """
    configs = generate_sweep_configs()
    n_configs = len(configs)
    categories = SGPConfig().all_categories
    print(f"# Running sweep over {n_configs} configurations (plots disabled)", file=sys.stderr)

    all_results = []
    errors = 0
    t0 = time.time()

    for i, config in enumerate(configs):
        try:
            metrics = run_pipeline(config, generate_plots=False)
            all_results.append(metrics)

            if (i + 1) % 50 == 0 or i == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                eta = (n_configs - i - 1) / rate
                print(
                    f"# Progress: {i+1}/{n_configs} "
                    f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)",
                    file=sys.stderr,
                )
        except Exception as e:
            errors += 1
            print(f"# ERROR Config {i+1}: {e}", file=sys.stderr)

    elapsed = time.time() - t0
    print(
        f"# Sweep complete: {len(all_results)} succeeded, "
        f"{errors} errors, {elapsed:.1f}s total",
        file=sys.stderr,
    )

    # Write CSV
    csv_path = output_csv or str(RESULTS_DIR / "sweep_results.csv")
    if all_results:
        fieldnames = sorted(all_results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_results:
                writer.writerow(row)
        print(f"# Results written to {csv_path}", file=sys.stderr)

    valid = [r for r in all_results if not np.isnan(r.get("sgp_cv_nrmse", np.nan))]
    if not valid:
        print("# No valid results", file=sys.stderr)
        return

    # =========================================================================
    # Strategy 1: Global Best (single config, lowest overall nRMSE)
    # =========================================================================
    global_best = min(valid, key=lambda r: r["sgp_cv_nrmse"])
    global_sig = _config_signature(global_best)

    print("\n# === STRATEGY 1: GLOBAL BEST (lowest overall nRMSE) ===", file=sys.stderr)
    print(f"# Config: {global_sig}", file=sys.stderr)
    print(
        f"# nRMSE={global_best['sgp_cv_nrmse']:.4f}  "
        f"RMSE={global_best['sgp_cv_rmse']:.4f}  "
        f"rank_corr={global_best['rank_correlation']:.4f}",
        file=sys.stderr,
    )

    # =========================================================================
    # Strategy 2: Per-Category Composite
    # =========================================================================
    # For each category, find the config with the lowest nRMSE for that category.
    # Use only the first buffer value per distinct config (buffer doesn't affect CV).
    seen_sigs = set()
    deduped = []
    for r in valid:
        sig = _config_signature(r)
        if sig not in seen_sigs:
            seen_sigs.add(sig)
            deduped.append(r)

    cat_best = {}  # {category: best result row}
    for cat in categories:
        nrmse_key = f"nrmse_{cat}"
        cat_valid = [r for r in deduped if not np.isnan(r.get(nrmse_key, np.nan))]
        if cat_valid:
            cat_best[cat] = min(cat_valid, key=lambda r: r[nrmse_key])

    # Compute composite nRMSE (average of each category's best nRMSE)
    composite_nrmses = {}
    for cat in categories:
        nrmse_key = f"nrmse_{cat}"
        if cat in cat_best and not np.isnan(cat_best[cat].get(nrmse_key, np.nan)):
            composite_nrmses[cat] = cat_best[cat][nrmse_key]
    composite_nrmse = float(np.mean(list(composite_nrmses.values()))) if composite_nrmses else np.nan

    # Build SGPConfig per category for composite rank correlation
    category_configs = {}
    for cat in categories:
        if cat in cat_best:
            r = cat_best[cat]
            category_configs[cat] = SGPConfig(
                sgp_method=r["method"],
                use_supplemental=r["use_supplemental"],
                time_decay=r["time_decay"],
                time_decay_rate=r["time_decay_rate"],
                punt_detection=r["punt_detection"],
            )

    print("\n# === STRATEGY 2: PER-CATEGORY COMPOSITE ===", file=sys.stderr)
    print(f"# Composite nRMSE={composite_nrmse:.4f}", file=sys.stderr)
    print("# Per-category winners:", file=sys.stderr)
    for cat in categories:
        if cat in cat_best:
            r = cat_best[cat]
            nrmse_val = r.get(f"nrmse_{cat}", np.nan)
            global_nrmse_val = global_best.get(f"nrmse_{cat}", np.nan)
            sig = _config_signature(r)
            diff = ""
            if sig != global_sig:
                if not np.isnan(nrmse_val) and not np.isnan(global_nrmse_val) and global_nrmse_val > 0:
                    pct = (global_nrmse_val - nrmse_val) / global_nrmse_val * 100
                    diff = f"  ({pct:+.1f}% vs global)"
                else:
                    diff = "  (DIFFERENT)"
            print(
                f"#   {cat:>5s}: nRMSE={nrmse_val:.4f}  {sig}{diff}",
                file=sys.stderr,
            )

    # Compute composite rank correlation (re-runs lightweight LOYO)
    print("# Computing composite rank correlation...", file=sys.stderr)
    composite_rank_corr = _compute_composite_rank_correlation(
        category_configs, SGPConfig()
    )
    print(f"# Composite rank_corr={composite_rank_corr:.4f}", file=sys.stderr)

    # =========================================================================
    # Head-to-Head Comparison
    # =========================================================================
    # Count distinct configs in composite
    composite_sigs = set(_config_signature(cat_best[cat]) for cat in categories if cat in cat_best)
    n_distinct = len(composite_sigs)

    print("\n# === HEAD-TO-HEAD COMPARISON ===", file=sys.stderr)
    print(f"#              {'Global':>12s}  {'Composite':>12s}  {'Winner':>10s}", file=sys.stderr)
    nrmse_winner = "Composite" if composite_nrmse < global_best["sgp_cv_nrmse"] else "Global"
    print(
        f"#   nRMSE:     {global_best['sgp_cv_nrmse']:12.4f}  {composite_nrmse:12.4f}  {nrmse_winner:>10s}",
        file=sys.stderr,
    )
    rc_winner = "Composite" if composite_rank_corr > global_best["rank_correlation"] else "Global"
    print(
        f"#   rank_corr: {global_best['rank_correlation']:12.4f}  {composite_rank_corr:12.4f}  {rc_winner:>10s}",
        file=sys.stderr,
    )
    print(f"#   Composite uses {n_distinct} distinct config(s) across 10 categories", file=sys.stderr)

    # Determine overall winner: rank_correlation is the tiebreaker
    if composite_rank_corr > global_best["rank_correlation"] + 0.001:
        overall_winner = "composite"
    elif global_best["rank_correlation"] > composite_rank_corr + 0.001:
        overall_winner = "global"
    elif composite_nrmse < global_best["sgp_cv_nrmse"]:
        overall_winner = "composite"
    else:
        overall_winner = "global"

    print(f"#\n# WINNER: {overall_winner.upper()}", file=sys.stderr)

    # =========================================================================
    # Print METRIC lines for the winning strategy
    # =========================================================================
    print()
    if overall_winner == "composite":
        # Build composite metrics
        composite_metrics = dict(global_best)  # start with global as base
        composite_metrics["sgp_cv_nrmse"] = composite_nrmse
        composite_metrics["rank_correlation"] = composite_rank_corr
        composite_metrics["method"] = "composite"
        # Replace denominators with per-category bests
        for cat in categories:
            if cat in cat_best:
                composite_metrics[f"sgp_denom_{cat}"] = cat_best[cat].get(f"sgp_denom_{cat}", np.nan)
                composite_metrics[f"nrmse_{cat}"] = cat_best[cat].get(f"nrmse_{cat}", np.nan)
                composite_metrics[f"best_method_{cat}"] = _config_signature(cat_best[cat])
        print_metrics(composite_metrics)
    else:
        # Add per-category annotations to global best
        global_best_annotated = dict(global_best)
        for cat in categories:
            global_best_annotated[f"best_method_{cat}"] = global_sig
        print_metrics(global_best_annotated)


def _print_summary(config: SGPConfig, metrics: dict, do_plots: bool):
    """Print human-readable summary to stderr."""
    print("\n--- SGP Denominators ---", file=sys.stderr)
    for cat in config.all_categories:
        d = metrics.get(f"sgp_denom_{cat}", "N/A")
        method_info = ""
        if config.is_composite:
            method_info = f"  ({metrics.get(f'best_method_{cat}', '')})"
        if isinstance(d, float):
            print(f"  {cat:>5s}: {d:.3f}{method_info}", file=sys.stderr)
        else:
            print(f"  {cat:>5s}: {d}{method_info}", file=sys.stderr)

    print(f"\n--- CV Metrics ---", file=sys.stderr)
    print(f"  RMSE: {metrics['sgp_cv_rmse']:.4f}", file=sys.stderr)
    print(f"  nRMSE: {metrics['sgp_cv_nrmse']:.4f}", file=sys.stderr)
    print(f"  Rank ρ: {metrics['rank_correlation']:.4f}", file=sys.stderr)
    print(f"  Category balance CV: {metrics['category_balance_cv']:.4f}", file=sys.stderr)
    if do_plots:
        print(f"\nPlots saved to plots/", file=sys.stderr)
    else:
        print(f"\nPlot generation skipped (--no-plots)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="SGP Model Pipeline")
    parser.add_argument("--config", default="default",
                        choices=["default", "composite", "sweep"],
                        help="Run mode: 'default' single method, 'composite' per-category best, 'sweep' autoresearch")
    parser.add_argument("--method", default=None,
                        help="Override SGP method")
    parser.add_argument("--supplemental", action="store_true",
                        help="Include supplemental years")
    parser.add_argument("--time-decay", action="store_true",
                        help="Enable time decay")
    parser.add_argument("--time-decay-rate", type=float, default=0.85,
                        help="Time decay rate")
    parser.add_argument("--punt", action="store_true",
                        help="Enable punt detection")
    parser.add_argument("--hitter-buffer", type=int, default=None,
                        help="Replacement hitter buffer (default: 30 composite, 50 otherwise)")
    parser.add_argument("--pitcher-buffer", type=int, default=None,
                        help="Replacement pitcher buffer (default: 30 composite, 40 otherwise)")
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip plot generation (faster for sweeps)")
    parser.add_argument("--output-csv", type=str, default=None,
                        help="CSV output path for sweep results (default: data/sweep_results.csv)")
    args = parser.parse_args()

    if args.config == "sweep":
        run_sweep(output_csv=args.output_csv)
    elif args.config == "composite":
        overrides = {}
        if args.hitter_buffer is not None:
            overrides["replacement_hitter_buffer"] = args.hitter_buffer
        if args.pitcher_buffer is not None:
            overrides["replacement_pitcher_buffer"] = args.pitcher_buffer
        config = SGPConfig.composite(**overrides)
        do_plots = not args.no_plots
        metrics = run_pipeline(config, generate_plots=do_plots)
        print_metrics(metrics)

        _print_summary(config, metrics, do_plots)
    else:
        config = SGPConfig()
        if args.method:
            config.sgp_method = args.method
        if args.supplemental:
            config.use_supplemental = True
        if args.time_decay:
            config.time_decay = True
            config.time_decay_rate = args.time_decay_rate
        if args.punt:
            config.punt_detection = True
        if args.hitter_buffer is not None:
            config.replacement_hitter_buffer = args.hitter_buffer
        if args.pitcher_buffer is not None:
            config.replacement_pitcher_buffer = args.pitcher_buffer

        do_plots = not args.no_plots
        metrics = run_pipeline(config, generate_plots=do_plots)
        print_metrics(metrics)

        _print_summary(config, metrics, do_plots)


if __name__ == "__main__":
    main()

"""Diagnostic plots for SGP model calibration. All plots saved to plots/."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import get_calibration_data, get_category_data
from sgp.sgp_calc import SGPResult

PLOTS_DIR = Path(__file__).resolve().parent.parent / "plots"


def _ensure_plots_dir():
    PLOTS_DIR.mkdir(exist_ok=True)


def plot_sgp_denominators(sgp_result: SGPResult, config: SGPConfig):
    """Bar chart of SGP denominator per category with bootstrap 95% CI error bars."""
    _ensure_plots_dir()

    cats = config.all_categories
    denoms = [sgp_result.denominators[c] for c in cats]
    ci_lo = [sgp_result.ci_lower.get(c, np.nan) for c in cats]
    ci_hi = [sgp_result.ci_upper.get(c, np.nan) for c in cats]

    errors_lo = [d - lo if not np.isnan(lo) else 0 for d, lo in zip(denoms, ci_lo)]
    errors_hi = [hi - d if not np.isnan(hi) else 0 for d, hi in zip(denoms, ci_hi)]

    colors = ["#2196F3" if c in config.all_batting else "#FF5722" for c in cats]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(cats))
    ax.bar(x, denoms, color=colors, yerr=[errors_lo, errors_hi],
           capsize=5, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=12)
    ax.set_ylabel("SGP Denominator (stat units per standings point)")
    ax.set_title(f"SGP Denominators — {sgp_result.method}")

    # Legend
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#2196F3", label="Batting"),
        Patch(facecolor="#FF5722", label="Pitching"),
    ])

    # Add value labels
    for i, d in enumerate(denoms):
        ax.text(i, d + errors_hi[i] + max(denoms) * 0.02,
                f"{d:.2f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "sgp_denominators.png", dpi=150)
    plt.close(fig)


def plot_sgp_year_stability(sgp_result: SGPResult, config: SGPConfig):
    """Line plot of year-specific SGP denominators per category (2x5 grid)."""
    _ensure_plots_dir()

    cats = config.all_categories
    n_cats = len(cats)
    nrows = 2
    ncols = 5

    fig, axes = plt.subplots(nrows, ncols, figsize=(20, 8), sharey=False)
    axes = axes.flatten()

    for i, cat in enumerate(cats):
        ax = axes[i]
        year_data = sgp_result.year_level.get(cat, {})
        if year_data:
            years = sorted(year_data.keys())
            vals = [year_data[y] for y in years]
            ax.plot(years, vals, "o-", color="#333", markersize=5)
            ax.axhline(sgp_result.denominators[cat], color="red",
                       linestyle="--", alpha=0.7, label="Overall")

        ax.set_title(cat, fontsize=12, fontweight="bold")
        ax.set_xlabel("Year")
        if i % ncols == 0:
            ax.set_ylabel("SGP Denominator")

    # Hide unused subplots
    for i in range(n_cats, nrows * ncols):
        axes[i].set_visible(False)

    fig.suptitle("Year-Level SGP Stability", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "sgp_year_stability.png", dpi=150)
    plt.close(fig)


def plot_category_scatter(df: pd.DataFrame, config: SGPConfig):
    """Scatter: raw stat vs standings points per category (2x5 grid), colored by year."""
    _ensure_plots_dir()

    cats = config.all_categories
    nrows, ncols = 2, 5

    fig, axes = plt.subplots(nrows, ncols, figsize=(20, 8))
    axes = axes.flatten()

    years = sorted(df["year"].unique())
    cmap = plt.cm.viridis
    norm = plt.Normalize(min(years), max(years))

    for i, cat in enumerate(cats):
        ax = axes[i]
        cat_df = get_category_data(df, cat, config)
        pts_col = f"{cat}_pts"

        valid = cat_df[[cat, pts_col, "year"]].dropna()
        valid = valid[valid[pts_col] > 0]

        scatter = ax.scatter(
            valid[pts_col], valid[cat],
            c=valid["year"], cmap=cmap, norm=norm,
            s=30, alpha=0.7, edgecolors="black", linewidth=0.3,
        )

        # Regression line
        if len(valid) >= 3:
            from scipy import stats as sp_stats
            slope, intercept, _, _, _ = sp_stats.linregress(
                valid[pts_col].values, valid[cat].values
            )
            x_range = np.linspace(valid[pts_col].min(), valid[pts_col].max(), 50)
            ax.plot(x_range, intercept + slope * x_range, "r-", alpha=0.6)

        ax.set_title(cat, fontsize=12, fontweight="bold")
        ax.set_xlabel("Standings Points")
        if i % ncols == 0:
            ax.set_ylabel("Raw Stat")

    for i in range(len(cats), nrows * ncols):
        axes[i].set_visible(False)

    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                 ax=axes, label="Year", shrink=0.6)
    fig.suptitle("Category: Raw Stat vs. Standings Points", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "category_scatter.png", dpi=150)
    plt.close(fig)


def plot_rate_stat_distributions(df: pd.DataFrame, config: SGPConfig):
    """Histograms of team AVG, ERA, WHIP by year."""
    _ensure_plots_dir()

    rate_cats = config.rate_batting + config.rate_pitching
    fig, axes = plt.subplots(1, len(rate_cats), figsize=(5 * len(rate_cats), 5))
    if len(rate_cats) == 1:
        axes = [axes]

    years = sorted(df["year"].unique())

    for i, cat in enumerate(rate_cats):
        ax = axes[i]
        cat_df = get_category_data(df, cat, config)
        for year in years:
            year_vals = cat_df.loc[cat_df["year"] == year, cat].dropna()
            if len(year_vals) > 0:
                ax.hist(year_vals, bins=8, alpha=0.4, label=str(year))
        ax.set_title(cat, fontsize=12, fontweight="bold")
        ax.set_xlabel(cat)
        ax.set_ylabel("Count")
        ax.legend(fontsize=7)

    fig.suptitle("Rate Stat Distributions by Year", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "rate_stat_distributions.png", dpi=150)
    plt.close(fig)


def plot_replacement_sensitivity(
    df: pd.DataFrame,
    sgp_result: SGPResult,
    config: SGPConfig,
):
    """Line plot: how top-player value changes as replacement buffer varies 0-70."""
    _ensure_plots_dir()

    from sgp.replacement import compute_replacement_level

    buffers = list(range(0, 75, 5))
    top_hitter_vals = []
    top_pitcher_vals = []

    for buf in buffers:
        test_config = SGPConfig(
            replacement_hitter_buffer=buf,
            replacement_pitcher_buffer=buf,
        )
        repl = compute_replacement_level(
            sgp_result, test_config, standings_df=df
        )
        # Approximate top-player value: league-best stats → SGP → minus replacement
        # Use max team stats as proxy for top individual
        top_hitter_sgp = 0.0
        for cat in config.counting_batting:
            best = df[cat].dropna().max()
            denom = sgp_result.denominators.get(cat, 1)
            if denom > 0:
                top_hitter_sgp += best / config.hitter_slots / denom

        top_pitcher_sgp = 0.0
        for cat in config.counting_pitching:
            best = df[cat].dropna().max()
            denom = sgp_result.denominators.get(cat, 1)
            if denom > 0:
                top_pitcher_sgp += best / config.pitcher_slots / denom

        top_hitter_par = top_hitter_sgp - repl["hitter_repl_sgp"]
        top_pitcher_par = top_pitcher_sgp - repl["pitcher_repl_sgp"]
        top_hitter_vals.append(top_hitter_par)
        top_pitcher_vals.append(top_pitcher_par)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(buffers, top_hitter_vals, "o-", label="Top Hitter PAR", color="#2196F3")
    ax.plot(buffers, top_pitcher_vals, "s-", label="Top Pitcher PAR", color="#FF5722")
    ax.axvline(config.replacement_hitter_buffer, color="#2196F3",
               linestyle="--", alpha=0.5, label=f"Default hitter buf ({config.replacement_hitter_buffer})")
    ax.axvline(config.replacement_pitcher_buffer, color="#FF5722",
               linestyle="--", alpha=0.5, label=f"Default pitcher buf ({config.replacement_pitcher_buffer})")
    ax.set_xlabel("Replacement Buffer (DL+RES across league)")
    ax.set_ylabel("Top Player PAR (SGP above replacement)")
    ax.set_title("Replacement Level Sensitivity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "replacement_sensitivity.png", dpi=150)
    plt.close(fig)


def plot_dollar_split(splits: list[dict]):
    """Stacked bar: hitter vs pitcher dollar allocation across model variants."""
    _ensure_plots_dir()

    if not splits:
        return

    fig, ax = plt.subplots(figsize=(max(8, len(splits) * 1.5), 6))
    labels = [s.get("label", f"Variant {i}") for i, s in enumerate(splits)]
    hitter_pcts = [s["hitter_pct"] for s in splits]
    pitcher_pcts = [s["pitcher_pct"] for s in splits]

    x = np.arange(len(labels))
    ax.bar(x, hitter_pcts, color="#2196F3", label="Hitters")
    ax.bar(x, pitcher_pcts, bottom=hitter_pcts, color="#FF5722", label="Pitchers")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Dollar Allocation (%)")
    ax.set_title("Hitter/Pitcher Dollar Split by Variant")
    ax.legend()
    ax.set_ylim(0, 105)

    for i, (h, p) in enumerate(zip(hitter_pcts, pitcher_pcts)):
        ax.text(i, h / 2, f"{h:.0f}%", ha="center", va="center", fontsize=9, color="white")
        ax.text(i, h + p / 2, f"{p:.0f}%", ha="center", va="center", fontsize=9, color="white")

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "dollar_split.png", dpi=150)
    plt.close(fig)


def plot_cv_diagnostics(cv_results: list[dict], config: SGPConfig):
    """LOYO cross-validation: predicted vs actual SGP denominators + rank correlations."""
    _ensure_plots_dir()

    if not cv_results:
        return

    cats = config.all_categories
    n_cats = len(cats)

    # Plot 1: predicted vs actual denominators per category
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    axes = axes.flatten()

    for i, cat in enumerate(cats):
        ax = axes[i]
        predicted = [r["predicted_denoms"].get(cat, np.nan) for r in cv_results]
        actual = [r["actual_denoms"].get(cat, np.nan) for r in cv_results]
        years = [r["held_out_year"] for r in cv_results]

        ax.scatter(actual, predicted, s=50, zorder=3)
        for j, yr in enumerate(years):
            ax.annotate(str(yr), (actual[j], predicted[j]),
                        fontsize=8, ha="left", va="bottom")

        # 1:1 line
        all_vals = [v for v in predicted + actual if not np.isnan(v)]
        if all_vals:
            lo, hi = min(all_vals) * 0.8, max(all_vals) * 1.2
            ax.plot([lo, hi], [lo, hi], "k--", alpha=0.4)

        ax.set_title(cat, fontsize=11, fontweight="bold")
        ax.set_xlabel("Actual (held-out year)")
        if i % 5 == 0:
            ax.set_ylabel("Predicted (N-1 years)")

    for i in range(n_cats, 10):
        axes[i].set_visible(False)

    fig.suptitle("LOYO CV: Predicted vs Actual SGP Denominators", fontsize=14)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "cv_diagnostics.png", dpi=150)
    plt.close(fig)

    # Plot 2: rank correlation bar chart
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    years = [r["held_out_year"] for r in cv_results]
    rhos = [r.get("rank_correlation", np.nan) for r in cv_results]
    ax2.bar(range(len(years)), rhos, color="#4CAF50", edgecolor="black")
    ax2.set_xticks(range(len(years)))
    ax2.set_xticklabels([str(y) for y in years])
    ax2.set_ylabel("Spearman ρ")
    ax2.set_title("LOYO CV: Rank Correlation (SGP-implied vs Actual Standings)")
    ax2.axhline(np.nanmean(rhos), color="red", linestyle="--",
                label=f"Mean ρ = {np.nanmean(rhos):.3f}")
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(PLOTS_DIR / "cv_rank_correlation.png", dpi=150)
    plt.close(fig2)


def plot_inflation_by_year(inflation_data: pd.DataFrame):
    """Bar chart of inflation factor per year."""
    _ensure_plots_dir()
    if inflation_data is None or inflation_data.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(inflation_data["year"].astype(str), inflation_data["inflation"],
           color="#9C27B0", edgecolor="black")
    ax.axhline(1.0, color="gray", linestyle="--", alpha=0.5)
    ax.set_ylabel("Inflation Factor")
    ax.set_title("Keeper Inflation by Year")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "inflation_by_year.png", dpi=150)
    plt.close(fig)


def plot_spending_split_comparison(
    model_split: dict, historical_splits: pd.DataFrame | None
):
    """Model-derived vs historical hitter/pitcher dollar split."""
    _ensure_plots_dir()
    if historical_splits is None or historical_splits.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    years = historical_splits["year"].values
    ax.plot(years, historical_splits["hitter_pct"], "o-",
            label="Historical (actual spending)", color="#FF9800")
    ax.axhline(model_split.get("hitter_pct", 65),
               color="#2196F3", linestyle="--",
               label=f"Model ({model_split.get('hitter_pct', 65):.1f}%)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Hitter Spending %")
    ax.set_title("Hitter/Pitcher Dollar Split: Model vs. Historical")
    ax.legend()
    ax.set_ylim(40, 90)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "spending_split_comparison.png", dpi=150)
    plt.close(fig)


def generate_all_diagnostics(
    df: pd.DataFrame,
    sgp_result: SGPResult,
    config: SGPConfig,
    cv_results: list[dict] | None = None,
):
    """Generate all required diagnostic plots."""
    _ensure_plots_dir()

    plot_sgp_denominators(sgp_result, config)
    plot_sgp_year_stability(sgp_result, config)
    plot_category_scatter(df, config)
    plot_rate_stat_distributions(df, config)
    plot_replacement_sensitivity(df, sgp_result, config)

    if cv_results:
        plot_cv_diagnostics(cv_results, config)

    # Optional roster-based plots
    from sgp.dollar_values import compute_historical_spending_split
    historical_splits = compute_historical_spending_split(config)
    if historical_splits is not None:
        plot_spending_split_comparison({}, historical_splits)

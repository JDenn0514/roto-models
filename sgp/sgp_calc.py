"""SGP denominator calculation — pairwise, OLS, robust regression + bootstrap."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.linear_model import HuberRegressor

from sgp.config import SGPConfig
from sgp.data_prep import (
    compute_time_weights,
    detect_punts,
    get_calibration_data,
    get_category_data,
    get_n_teams_by_year,
    normalize_11_team_gaps,
)


@dataclass
class SGPResult:
    """Container for SGP calibration results."""

    denominators: dict  # {category: sgp_denominator}
    ci_lower: dict  # {category: 95% CI lower bound}
    ci_upper: dict  # {category: 95% CI upper bound}
    method: str
    n_observations: dict  # {category: number of gaps/data points used}
    year_level: dict = field(default_factory=dict)  # {category: {year: year-specific denom}}


def _pairwise_gaps_one_year(
    year_df: pd.DataFrame,
    category: str,
    config: SGPConfig,
    n_teams_actual: int,
) -> np.ndarray:
    """Compute pairwise gaps for one year and category.

    Returns array of gaps (positive = one standings point improvement).
    """
    values = year_df[category].dropna().values
    if len(values) < 2:
        return np.array([])

    # Sort ascending, compute absolute gaps between adjacent teams.
    # The denominator is always positive — sign convention (lower=better for ERA/WHIP)
    # is handled in the player-level SGP conversion, not here.
    values = np.sort(values)
    gaps = values[1:] - values[:-1]  # always positive (sorted ascending)

    # Normalize 11-team years to 10-team scale
    gaps = normalize_11_team_gaps(gaps, n_teams_actual, config.n_teams)

    return gaps


def compute_pairwise_gaps(
    df: pd.DataFrame, category: str, config: SGPConfig
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Compute all pairwise gaps for a category across years.

    Returns (gaps, weights, year_denoms).
    """
    cat_df = get_category_data(df, category, config)
    n_teams_by_year = get_n_teams_by_year(cat_df)

    # Optional punt detection
    if config.punt_detection:
        punt_mask = detect_punts(cat_df, category, config)
        cat_df = cat_df[~punt_mask]

    all_gaps = []
    all_weights = []
    year_denoms = {}

    for year, year_df in cat_df.groupby("year"):
        n_teams = n_teams_by_year.get(year, config.n_teams)
        gaps = _pairwise_gaps_one_year(year_df, category, config, n_teams)
        if len(gaps) == 0:
            continue

        year_denoms[year] = float(np.mean(gaps))

        # Time-decay weight for this year
        if config.time_decay:
            max_year = cat_df["year"].max()
            w = config.time_decay_rate ** (max_year - year)
        else:
            w = 1.0

        all_gaps.extend(gaps)
        all_weights.extend([w] * len(gaps))

    return np.array(all_gaps), np.array(all_weights), year_denoms


def _sgp_pairwise(
    gaps: np.ndarray, weights: np.ndarray, use_median: bool
) -> float:
    """Compute SGP denominator from pairwise gaps."""
    if len(gaps) == 0:
        return np.nan
    if use_median:
        # For weighted median, use repeated samples approach
        if np.allclose(weights, weights[0]):
            return float(np.median(gaps))
        # Weighted median via sorting
        sorted_idx = np.argsort(gaps)
        sorted_gaps = gaps[sorted_idx]
        sorted_weights = weights[sorted_idx]
        cum_weight = np.cumsum(sorted_weights)
        midpoint = cum_weight[-1] / 2.0
        idx = np.searchsorted(cum_weight, midpoint)
        return float(sorted_gaps[min(idx, len(sorted_gaps) - 1)])
    else:
        return float(np.average(gaps, weights=weights))


def _sgp_ols(
    cat_df: pd.DataFrame, category: str, config: SGPConfig
) -> float:
    """Compute SGP denominator via OLS regression (stat ~ points)."""
    pts_col = f"{category}_pts"
    valid = cat_df[[category, pts_col]].dropna()
    valid = valid[valid[pts_col] > 0]  # exclude DQ'd teams

    if len(valid) < 3:
        return np.nan

    x = valid[pts_col].values
    y = valid[category].values

    weights = compute_time_weights(cat_df.loc[valid.index], config).values

    if config.time_decay and not np.allclose(weights, 1.0):
        # Weighted least squares
        W = np.diag(weights)
        X = np.column_stack([np.ones(len(x)), x])
        beta = np.linalg.lstsq(W @ X, W @ y, rcond=None)[0]
        slope = beta[1]
    else:
        slope, _, _, _, _ = sp_stats.linregress(x, y)

    # For inverse categories, slope is negative (more points = lower ERA)
    # We want the absolute value as the denominator
    return float(abs(slope))


def _sgp_robust(
    cat_df: pd.DataFrame, category: str, config: SGPConfig
) -> float:
    """Compute SGP denominator via Huber robust regression."""
    pts_col = f"{category}_pts"
    valid = cat_df[[category, pts_col]].dropna()
    valid = valid[valid[pts_col] > 0]

    if len(valid) < 3:
        return np.nan

    x = valid[pts_col].values.reshape(-1, 1)
    y = valid[category].values

    weights = compute_time_weights(cat_df.loc[valid.index], config).values

    reg = HuberRegressor(epsilon=1.35, max_iter=200)
    reg.fit(x, y, sample_weight=weights)
    return float(abs(reg.coef_[0]))


def bootstrap_sgp(
    gaps: np.ndarray,
    weights: np.ndarray,
    use_median: bool = False,
    n_boot: int = 10_000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Return (estimate, ci_lower, ci_upper) via bootstrap."""
    rng = np.random.default_rng(seed)
    if len(gaps) == 0:
        return np.nan, np.nan, np.nan

    estimate = _sgp_pairwise(gaps, weights, use_median)

    boot_estimates = []
    n = len(gaps)
    for _ in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        sample_gaps = gaps[idx]
        sample_weights = weights[idx]
        boot_estimates.append(_sgp_pairwise(sample_gaps, sample_weights, use_median))

    boot_estimates = np.array(boot_estimates)
    ci_lower = float(np.percentile(boot_estimates, 2.5))
    ci_upper = float(np.percentile(boot_estimates, 97.5))
    return estimate, ci_lower, ci_upper


def _filter_to_config_years(df: pd.DataFrame, cat_config: SGPConfig) -> pd.DataFrame:
    """Filter dataframe to the years this config should use."""
    return df[df["year"].isin(cat_config.active_years)]


def _compute_one_category(
    df: pd.DataFrame, cat: str, cat_config: SGPConfig, bootstrap: bool
) -> tuple[float, float, float, int, dict]:
    """Compute SGP denominator for a single category with its config.

    Returns (denominator, ci_lower, ci_upper, n_obs, year_denoms).
    """
    cat_df = get_category_data(df, cat, cat_config)

    if cat_config.punt_detection:
        punt_mask = detect_punts(cat_df, cat, cat_config)
        cat_df = cat_df[~punt_mask]

    method = cat_config.sgp_method

    if method in ("pairwise_mean", "pairwise_median"):
        gaps, weights, year_denoms = compute_pairwise_gaps(df, cat, cat_config)
        use_median = method == "pairwise_median"
        if bootstrap:
            est, lo, hi = bootstrap_sgp(gaps, weights, use_median)
        else:
            est = _sgp_pairwise(gaps, weights, use_median)
            lo, hi = np.nan, np.nan
        return est, lo, hi, len(gaps), year_denoms

    elif method == "ols":
        denom = _sgp_ols(cat_df, cat, cat_config)
        _, _, year_denoms = compute_pairwise_gaps(df, cat, cat_config)
        return denom, np.nan, np.nan, len(cat_df), year_denoms

    elif method == "robust_reg":
        denom = _sgp_robust(cat_df, cat, cat_config)
        _, _, year_denoms = compute_pairwise_gaps(df, cat, cat_config)
        return denom, np.nan, np.nan, len(cat_df), year_denoms

    else:
        raise ValueError(f"Unknown SGP method: {method}")


def compute_sgp(
    df: pd.DataFrame, config: SGPConfig, bootstrap: bool = True
) -> SGPResult:
    """Compute SGP denominators for all categories using configured method.

    Supports per-category composite configs: when config.per_category is set,
    each category uses its own method/settings from effective_config().

    Set bootstrap=False to skip CI computation (much faster for sweeps).
    """
    denominators = {}
    ci_lower = {}
    ci_upper = {}
    n_obs = {}
    year_level = {}

    for cat in config.all_categories:
        cat_config = config.effective_config(cat)

        # Filter data to the years this category's config uses
        if config.is_composite:
            cat_df = _filter_to_config_years(df, cat_config)
        else:
            cat_df = df

        est, lo, hi, n, year_denoms = _compute_one_category(
            cat_df, cat, cat_config, bootstrap
        )
        denominators[cat] = est
        ci_lower[cat] = lo
        ci_upper[cat] = hi
        n_obs[cat] = n
        year_level[cat] = year_denoms

    return SGPResult(
        denominators=denominators,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        method="composite" if config.is_composite else config.sgp_method,
        n_observations=n_obs,
        year_level=year_level,
    )


def player_stat_to_sgp(
    player_stat: float,
    replacement_stat: float,
    sgp_denom: float,
    category: str,
    config: SGPConfig,
    player_ab_or_ip: float | None = None,
) -> float:
    """Convert a single player stat to SGP above replacement.

    For counting stats: (player - replacement) / denom
    For rate stats: requires player_ab_or_ip for proportional contribution.
    """
    if category in config.rate_batting:
        # AVG: (player_avg - repl_avg) * (player_ab / team_ab) / denom
        if player_ab_or_ip is None:
            raise ValueError(f"player_ab_or_ip required for rate stat {category}")
        team_total = config.team_ab
        return (player_stat - replacement_stat) * (player_ab_or_ip / team_total) / sgp_denom

    elif category in config.rate_pitching:
        # ERA/WHIP: (repl - player) * (player_ip / team_ip) / denom  (lower is better)
        if player_ab_or_ip is None:
            raise ValueError(f"player_ab_or_ip required for rate stat {category}")
        team_total = config.team_ip
        return (replacement_stat - player_stat) * (player_ab_or_ip / team_total) / sgp_denom

    elif category in config.inverse_categories:
        # Should not reach here since ERA/WHIP are in rate_pitching
        return (replacement_stat - player_stat) / sgp_denom

    else:
        # Counting stat: higher is better
        return (player_stat - replacement_stat) / sgp_denom

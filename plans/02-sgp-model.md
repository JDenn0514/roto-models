# Plan: SGP Model (Layer 4) — SGP Calibration, Replacement Level, Dollar Values

## Goal

Build the pricing engine that converts projected player stat lines into auction dollar
values, calibrated to the Moonlight Graham league's historical standings. This is Layer 4
of the 4-layer valuation pipeline described in `getting-started.md`.

## Prerequisites

- `data/historical_standings.csv` — already exists (scraped by `scrape_standings.py`)
- `data/historical_rosters.csv` — already exists (scraped by Plan 01). Used for:
  - Replacement-level buffer calibration (actual reserve counts)
  - Inflation modeling and keeper analysis
  - Historical spending split validation

---

## Resolved Design Decisions

These questions were discussed and settled before implementation:

| Decision | Resolution | Rationale |
|----------|-----------|-----------|
| Team AB estimate | **7,300** | Back-calculated from HR/typical-HR-rate (243/0.033≈7,364) and 15-hitter roster math (10 full-time × 575 AB + 5 part-time × 350 AB). The original plan's 5,500 was an MLB-team figure, not a fantasy-team figure. |
| Team IP estimate | **1,300** | Cross-referenced: SO/typical-K9 (1207/8.75×9≈1,242), roster math (5SP×175+6RP×65=1,265), W/typical-W-rate (76/0.056≈1,357). Average ≈1,300. |
| Replacement buffer defaults | **hitter=50, pitcher=40** | Derived from `historical_rosters.csv`. Average DL+RES (MLB-level reserves, excluding FARM/minors) across 2019-2024: hitters≈53, pitchers≈42. FARM players are minor leaguers not in the MLB player pool, so they don't reduce free agent supply. Sweep 30-70 in autoresearch. |
| Hitter/pitcher dollar split | **Let model determine** | The split emerges from replacement-level math. Compare model-derived split to historical spending split from roster data as a diagnostic. Divergence = market inefficiency signal for draft day. |
| Punt detection | **Off for initial build** | Only 45 gap observations per category in primary window. Removing punt teams further shrinks the sample. Can enable later via config flag. |
| Supplemental data (2015-2018) | **Start with primary only** | Primary window: 2019, 2021-2024 (5 years, ~50 team-seasons). Supplemental adds noise from the 8→10 category transition and varying team counts. Test as an autoresearch variant. |
| 900 IP penalty detection | **Exclude exact 0.0 only** | Teams with 0.0 points in BOTH ERA and WHIP (but non-null, reasonable ERA/WHIP values) hit the IP minimum penalty. Teams with 0.5 points (e.g., HAMMERHEADS 2020) are NOT excluded — likely just bad pitching on a team where another was DQ'd. 2020 is excluded anyway. |
| Autoresearch scope | **Run full sweep (~320 configs)** | Each config takes <0.2s without bootstrap. Full sweep completes in ~60s. No reason to be conservative. |
| Primary optimization metric | **nRMSE (normalized RMSE)** | Raw RMSE is dominated by large-scale categories (R, RBI, SO ~30) and ignores small-scale ones (AVG ~0.002, WHIP ~0.017). nRMSE normalizes each category's error by its mean denominator so all 10 contribute equally. Spearman correlation between raw RMSE and nRMSE rankings is only 0.67 — they disagree meaningfully. |
| Per-category optimization | **Compare global-best vs composite** | No reason the same config should be optimal for HR and AVG. The sweep selects the best config independently for each of the 10 categories and assembles a composite SGPResult. Both strategies are evaluated head-to-head on the same sweep data. |

---

## League Context (Critical for Implementation)

Read `league-context.md` for full details. Key parameters:

| Parameter | Value |
|-----------|-------|
| Teams | 10 (11 in 2016-2017) |
| Batting categories | R, HR, RBI, SB, AVG |
| Pitching categories | W, SV, ERA, WHIP, SO |
| Hitter roster slots | 15 per team (2C, 1B, 2B, SS, 3B, 5OF, CI, MI, 2UT) |
| Pitcher roster slots | 11 per team (generic P slots, any SP/RP mix) |
| Auction budget | $360 per team ($3,600 total pool) |
| Active salary cap | $350 |
| Full roster salary cap | $500 |
| Min IP for ERA/WHIP | 900 IP (teams below score 0 points) |
| Category scoring | Linear: 1st = N pts, last = 1 pt, ties split |
| Scoring era change | 8 categories (2015-2018) → 10 categories (2019-present) |

---

## Architecture

```
sgp/
├── __init__.py
├── config.py           # League constants, category definitions, calibration window
├── data_prep.py        # Load standings, filter years, handle exclusions
├── sgp_calc.py         # SGP denominator calculation (multiple methods)
├── replacement.py      # Replacement level by position (hitter vs pitcher)
├── dollar_values.py    # PAR → dollar conversion, inflation adjustment
├── diagnostics.py      # All plots → plots/
├── run_pipeline.py     # End-to-end: data → SGP → replacement → dollars
├── autoresearch.sh     # Benchmarking entry point
└── autoresearch.md     # Session documentation for autoresearch plugin
```

---

## Step 1: Configuration (`config.py`)

Define all league constants and model hyperparameters as a dataclass or dict so
autoresearch can override them:

```python
@dataclass
class SGPConfig:
    # League structure
    n_teams: int = 10
    hitter_slots: int = 15
    pitcher_slots: int = 11
    auction_budget_per_team: int = 360
    min_ip: int = 900

    # Categories
    counting_batting: list = field(default_factory=lambda: ["R", "HR", "RBI", "SB"])
    counting_pitching: list = field(default_factory=lambda: ["W", "SV", "SO"])
    rate_batting: list = field(default_factory=lambda: ["AVG"])
    rate_pitching: list = field(default_factory=lambda: ["ERA", "WHIP"])
    inverse_categories: list = field(default_factory=lambda: ["ERA", "WHIP"])

    # Calibration window
    primary_years: list = field(default_factory=lambda: [2019, 2021, 2022, 2023, 2024])
    supplemental_years: list = field(default_factory=lambda: [2015, 2016, 2017, 2018])
    excluded_years: list = field(default_factory=lambda: [2020, 2025])

    # Model variant controls (autoresearch sweeps these)
    sgp_method: str = "pairwise_mean"  # pairwise_mean, pairwise_median, ols, robust_reg
    use_supplemental: bool = False
    time_decay: bool = False
    time_decay_rate: float = 0.85  # weight = rate^(current_year - year)
    punt_detection: bool = False
    punt_z_threshold: float = -1.5
    replacement_hitter_buffer: int = 50   # DL+RES hitters across league (avg from data: ~53)
    replacement_pitcher_buffer: int = 40  # DL+RES pitchers across league (avg from data: ~42)
    include_keeper_adjustment: bool = False
    inflation_model: str = "uniform"  # uniform, tiered

    # Team-level totals for rate stat conversion
    # Estimated from historical data cross-referencing (see Resolved Design Decisions)
    team_ab: float = 7300.0   # ~15 hitters: 10 full-time × 575 AB + 5 part-time × 350 AB
    team_ip: float = 1300.0   # ~11 pitchers: 5SP × 175 IP + 6RP × 65 IP, cross-checked vs SO and W
```

---

## Step 2: Data Preparation (`data_prep.py`)

### Load and Filter Standings

```python
def load_standings(config: SGPConfig) -> pd.DataFrame:
    """Load historical_standings.csv, apply filters."""
```

1. Read `data/historical_standings.csv`
2. Exclude years in `config.excluded_years`
3. Separate primary and supplemental year data

### Exclusion Rules

Apply these filters **per category**, not globally:

| Rule | Categories Affected | Logic |
|------|-------------------|-------|
| Exclude 2020 | All | COVID-shortened season |
| Exclude 2025 | All | Partial season |
| Exclude 900 IP penalty teams | ERA, WHIP | Teams scoring exactly 0.0 pts in BOTH ERA AND WHIP (indicates IP minimum penalty, not bad pitching) |
| Exclude Boppers 2020 | All | All-zero row — inactive/DQ team |
| Exclude 2015-2018 from R, SO | R, SO | These categories didn't exist pre-2019 |

**How to identify 900 IP penalty teams**: A team has exactly 0.0 points in BOTH ERA and
WHIP but has non-zero raw ERA/WHIP values. Known cases from the data:
- 2019: Kerry & Mitch (ERA 3.66/0pts, WHIP 1.162/0pts — best values, clearly IP penalty)
- 2017: Thunder & Lightning (ERA 3.92/0pts, WHIP 1.198/0pts)
- 2017: Boppers (ERA 4.44/0pts, WHIP 1.363/0pts)
- 2016: Taylor Applebaum (ERA 3.77/0pts, WHIP 1.24/0pts)

Detection logic: `ERA_pts == 0.0 AND WHIP_pts == 0.0 AND ERA is not null AND ERA < 6.0`
(a truly terrible team would have some points, just low ones).

Teams with 0.5 points (e.g., HAMMERHEADS 2020) are NOT excluded by this rule — they
likely just had bad pitching. (2020 is excluded entirely anyway.)

### Punt Detection (Optional, Off by Default)

If `config.punt_detection` is True:

For each year and category, compute z-scores of raw stat values. Flag teams with
z-score below `config.punt_z_threshold` as punting that category. Exclude them from
SGP calculation for that category only.

Example: Livn Lex 2022 had 13 SV (league range 13-97). Z-score ≈ -2.0 → flagged as
SV punt.

**Important**: Punt detection only applies to counting stats. Rate stats can't be
"punted" in the same way (you can't choose to have a bad ERA independent of IP).

**Default: Off.** With only 45 gap observations per category, removing punt teams
further shrinks the sample. Enable as an autoresearch variant.

### Team-Level Summary Stats

Use estimated defaults (see Resolved Design Decisions above). These estimates were
derived by cross-referencing multiple approaches against the historical standings data:

```python
def compute_team_averages(config: SGPConfig) -> dict:
    """Return team-level AB and IP estimates for rate stat conversion."""
    return {
        "team_ab": config.team_ab,  # default 7,300
        "team_ip": config.team_ip,  # default 1,300
    }
```

**How estimates were derived (for documentation, not runtime):**

Team AB (~7,300):
- Method 1: 15-hitter roster math → 10 full-time × 575 + 5 part-time × 350 = 7,500
- Method 2: mean HR (243) / typical AL HR/AB rate (0.033) ≈ 7,364
- Conservative estimate: 7,300

Team IP (~1,300):
- Method 1: mean SO (1,207) / typical AL K/9 (8.75) × 9 ≈ 1,242
- Method 2: 11-pitcher roster math → 5SP × 175 + 6RP × 65 = 1,265
- Method 3: mean W (76) / typical W/IP rate (0.056) ≈ 1,357
- Central estimate: 1,300

**TODO**: Scrape actual team AB/IP from OnRoto stats pages to replace estimates.

### Time-Decay Weighting

If `config.time_decay` is True:

```python
weight = config.time_decay_rate ** (max_year - year)
```

Where `max_year` is the most recent calibration year. Examples with rate=0.85:
- 2024: weight = 1.000
- 2023: weight = 0.850
- 2022: weight = 0.723
- 2021: weight = 0.614
- 2019: weight = 0.444
- 2018: weight = 0.377 (supplemental)
- 2015: weight = 0.232 (supplemental)

Weights are applied to the gap observations in pairwise method, or as sample weights
in regression methods.

### 11-Team Normalization (2016-2017)

If using supplemental data, 2016-2017 had 11 teams instead of 10. The pairwise gaps
are naturally smaller (more teams = denser standings). Two approaches:

**Option A**: Scale gaps by `(N_target - 1) / (N_actual - 1)` = `9/10` for 11→10 team
normalization. This assumes uniform spacing.

**Option B**: Use percentile-based gaps instead of rank-based. Convert each team's
rank to a percentile, then compute differences in stat space at percentile intervals.

**Recommendation**: Option A is simpler and sufficient. The 10% adjustment is within
noise for these sample sizes.

---

## Step 3: SGP Calculation (`sgp_calc.py`)

### Method 1: Pairwise Differences (Primary)

For each year and category:

1. Sort teams by raw stat value (ascending for ERA/WHIP, descending for others)
2. Compute the difference between adjacent teams: `gap[i] = stat[i+1] - stat[i]`
3. For ERA/WHIP (lower is better): `gap[i] = stat[i] - stat[i+1]` (so gap is positive
   when moving to a better rank)
4. Each gap represents the cost of 1 standings point in that category

Then aggregate across years:

- **`pairwise_mean`**: Mean of all gaps across all years
- **`pairwise_median`**: Median of all gaps (more robust to outlier gaps at standings
  extremes)

With N teams per year and Y years: total gaps = Y × (N-1).
For primary window: 5 years × 9 gaps = 45 observations per category.

**Output**: One SGP denominator per category = the average/median gap.

**Interpretation**: "It takes X units of stat Y to gain 1 standings point."

### Method 2: OLS Regression

For each category, regress raw stat on standings points:

```
stat = β₀ + β₁ × points + ε
```

SGP denominator = β₁ (the slope: stat units per standings point).

Pool all years together. If using time-decay, use weighted least squares with year-based
weights.

**Note**: This assumes linearity between stat value and standings points. In a 10-team
league, the relationship is actually rank-based (step function with noise). Regression
smooths this but may bias at the extremes.

### Method 3: Robust Regression

Same as OLS but using Huber regression (`sklearn.linear_model.HuberRegressor`) or RANSAC
(`sklearn.linear_model.RANSACRegressor`). These down-weight outlier teams (punters,
anomalous seasons).

### Bootstrap Confidence Intervals

For all methods, compute 95% CIs via bootstrap:

```python
def bootstrap_sgp(gaps: np.ndarray, n_boot: int = 10000) -> tuple[float, float, float]:
    """Return (estimate, ci_lower, ci_upper)."""
    boot_estimates = []
    for _ in range(n_boot):
        sample = np.random.choice(gaps, size=len(gaps), replace=True)
        boot_estimates.append(np.mean(sample))  # or median
    return np.mean(gaps), np.percentile(boot_estimates, 2.5), np.percentile(boot_estimates, 97.5)
```

### Rate Stat Handling

SGP denominators for AVG, ERA, WHIP are computed at the **team level** (same pairwise
or regression method). The denominator is in team-level units (e.g., ".004 team AVG per
standings point").

When converting a player's stats to SGP later (not in this module — that's the
integration point with Layers 1-3), the conversion is:

```python
# For AVG (higher is better):
player_sgp_avg = (player_avg - replacement_avg) * (player_ab / team_ab) / sgp_denom_avg

# For ERA (lower is better):
player_sgp_era = (replacement_era - player_era) * (player_ip / team_ip) / sgp_denom_era

# For WHIP (lower is better):
player_sgp_whip = (replacement_whip - player_whip) * (player_ip / team_ip) / sgp_denom_whip
```

This conversion logic should be a function in `sgp_calc.py` even though it won't be
called until player projections exist.

### Output Format

```python
@dataclass
class SGPResult:
    denominators: dict[str, float]        # {category: sgp_denominator}
    ci_lower: dict[str, float]            # {category: 95% CI lower bound}
    ci_upper: dict[str, float]            # {category: 95% CI upper bound}
    method: str                            # method name
    n_observations: dict[str, int]         # {category: number of gaps/data points used}
    year_level: dict[str, dict[int, float]]  # {category: {year: year-specific denominator}}
```

---

## Step 4: Replacement Level (`replacement.py`)

### Concept

Replacement level = the expected production of the best freely available (unrostered)
player. Players below replacement contribute negative value — they're worse than what
you could pick up for free.

### Roster Math

These values are derived from actual `historical_rosters.csv` data (2019-2024 averages):

| Pool | Slots | Total Rostered |
|------|-------|----------------|
| Hitters active | 15 per team × 10 teams | 150 |
| Pitchers active | 11 per team × 10 teams | 110 |
| Hitter DL+RES reserves (MLB-level) | avg ~53 league-wide | 203 |
| Pitcher DL+RES reserves (MLB-level) | avg ~42 league-wide | 152 |

**Note on FARM players**: FARM slots hold minor leaguers not on active MLB rosters.
These players are NOT in the MLB player pool, so they don't reduce the free agent
supply. Only DL and RES reserves (which hold MLB-level players) count toward the
replacement buffer.

Historical DL+RES counts from `historical_rosters.csv`:

| Year | Hitter DL+RES | Pitcher DL+RES |
|------|--------------|----------------|
| 2019 | 49 | 40 |
| 2021 | 72 | 49 |
| 2022 | 57 | 39 |
| 2023 | 47 | 37 |
| 2024 | 38 | 43 |
| **Avg** | **~53** | **~42** |

Replacement-level hitter = the (150 + buffer)th best hitter in the AL player pool.
Replacement-level pitcher = the (110 + buffer)th best pitcher in the AL player pool.

Default: `replacement_hitter_buffer=50`, `replacement_pitcher_buffer=40`.
Autoresearch sweeps 30-70 for both.

### Implementation (Without Player Projections)

Since Layers 1-3 don't exist yet, we can't rank actual players. Instead:

**Option A: Historical percentile approach**
- From historical rosters (Plan 01 data), find the actual last-rostered players
- Compute their stats as the replacement baseline
- This is the most accurate but requires roster data

**Option B: Statistical estimation**
- Compute the league-average stat line from standings data
- Estimate replacement level as a fraction below average
- Standard roto heuristic: replacement ≈ 70-75th percentile of rostered players
  (roughly the bottom-of-roster starter)
- This is a placeholder until real player projections exist

**Option C: Configurable placeholder**
- Define replacement-level stats as configurable inputs
- When Layers 1-3 are built, they compute replacement level from actual player pool
- The SGP model just needs a replacement-level SGP total to subtract

**Recommendation**: Implement Option C as the primary interface, with Option B as a
default. Option A becomes possible when player projections are connected.

```python
def compute_replacement_level(
    sgp_result: SGPResult,
    config: SGPConfig,
    player_projections: pd.DataFrame | None = None,
    replacement_stats: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Compute replacement-level SGP for hitters and pitchers.

    If player_projections provided: rank players, find the marginal rostered player.
    If replacement_stats provided: use those directly.
    Otherwise: use historical-average heuristic.

    Returns: {"hitter_repl_sgp": float, "pitcher_repl_sgp": float}
    """
```

### Replacement Level Per Category

Replacement level should be computed **per category**, not as a single number. The
replacement-level hitter has specific stats in each of R, HR, RBI, SB, AVG — and those
stats convert to SGP differently.

```python
# Replacement level hitter contributes this many SGP per category:
repl_sgp = {
    "R": repl_R / sgp_denom_R,
    "HR": repl_HR / sgp_denom_HR,
    "RBI": repl_RBI / sgp_denom_RBI,
    "SB": repl_SB / sgp_denom_SB,
    "AVG": (repl_AVG - league_avg_AVG) * (repl_AB / team_AB) / sgp_denom_AVG,
}
repl_sgp_total_hitting = sum(repl_sgp.values())
```

---

## Step 5: Dollar Value Conversion (`dollar_values.py`)

### Core Formula

```python
total_auction_pool = config.n_teams * config.auction_budget_per_team  # $3,600

# For each player:
player_par = player_total_sgp - replacement_sgp  # Position-specific replacement

# Only positive-PAR players count
positive_par_players = [p for p in players if p.par > 0]
total_par = sum(p.par for p in positive_par_players)

dollars_per_par = total_auction_pool / total_par

# Dollar value (redraft / base value):
player_dollar_value = player_par * dollars_per_par
```

### Hitter/Pitcher Dollar Split

The split emerges naturally when replacement levels are set correctly. If replacement
level for hitters is set such that exactly 150 hitters have positive PAR, and pitcher
replacement produces 110 positive-PAR pitchers, the dollar split reflects the relative
value available at each position.

Typical roto splits land around 65-70% hitters / 30-35% pitchers. If our split is far
outside this range, it may indicate a miscalibrated replacement level.

**Diagnostic checks:**
- Report the hitter/pitcher dollar split
- If outside 55-80% hitters, flag for review
- Compare model-derived split to historical spending split from roster salary data
  (divergence = market inefficiency signal for draft day)

### Historical Spending Split (from roster data)

Once `historical_rosters.csv` is loaded, compute the actual historical spending split:

```python
# For each year, sum salaries of active hitters vs active pitchers
# Compare to model-derived split
# Divergence suggests the league over/under-values one side
```

This is a diagnostic, not an input to the model. The model determines the "correct"
split; the historical data reveals whether the league agrees.

### Minimum Dollar Value

In practice, no player sells for $0 at auction — minimum bid is $1. Players near
$0 in value should be floored at $1. This means the dollar pool is slightly reduced by
the number of $1 players × $1.

### Inflation Adjustment (Requires Roster Data)

**Build this as a separate function that wraps the base dollar values.**

```python
def compute_inflation(
    base_values: pd.DataFrame,
    keeper_data: pd.DataFrame,  # from historical_rosters.csv
    config: SGPConfig,
) -> tuple[float, pd.DataFrame]:
    """
    Compute inflation factor and adjusted dollar values.

    Steps:
    1. Identify keepers (contract year b or c, or a with same-team prior-year match)
    2. Sum keeper salaries (what they cost)
    3. Sum keeper base values (what they're worth)
    4. inflation = (total_auction - keeper_salary) / (total_auction_value - keeper_value)
    5. For non-keepers: inflated_value = base_value * inflation
    6. For keepers: value stays at base_value (salary is fixed by contract)

    Returns: (inflation_factor, dataframe with inflated values)
    """
```

**Iterative convergence**: Inflation affects replacement level (because keepers remove
above-replacement players from the auction pool). The loop:

1. Compute base values with initial replacement level
2. Identify keepers, compute inflation
3. Recompute replacement level among AUCTION-AVAILABLE players only
4. Recompute base values with new replacement level
5. Repeat until inflation factor converges (typically 2-3 iterations)

**Uniform vs. Tiered inflation** (autoresearch variant):
- Uniform: every non-keeper inflated by the same factor
- Tiered: top-tier players inflate more (teams with excess budget target elite players)
  - Implementation: weight inflation by player PAR rank (top 10% get 1.2× inflation,
    middle gets 1.0×, bottom gets 0.8×) — the exact weights are a hyperparameter

### Keeper Surplus

```python
keeper_surplus = base_dollar_value - salary
```

A player with base value $25 and salary $10 has $15 surplus — that's $15 of value locked
in below market rate. High-surplus players are strong keepers.

---

## Step 6: Diagnostics (`diagnostics.py`)

All plots saved to `plots/` directory.

### Required Plots

1. **`sgp_denominators.png`** — Bar chart of SGP denominator per category with bootstrap
   95% CI error bars. One bar per category, grouped by batting/pitching.

2. **`sgp_year_stability.png`** — Line plot: year-specific SGP denominator per category
   across calibration years. Shows how stable/noisy each category is year-over-year.
   One subplot per category (2×5 grid).

3. **`category_scatter.png`** — Scatter plot: raw stat vs. standings points for each
   category, with regression line overlay. One subplot per category (2×5 grid). Color
   points by year. This is the fundamental SGP relationship visualization.

4. **`rate_stat_distributions.png`** — Histograms of team AVG, ERA, WHIP by year.
   Shows how tight the distributions are (relevant for SGP noise).

5. **`replacement_sensitivity.png`** — Line plot: total dollar value of top player as
   replacement level buffer varies from 0 to +70. Shows how sensitive valuations are
   to the replacement-level assumption. (Range expanded from 0-30 to 0-70 to cover
   the actual reserve depth in this league.)

6. **`dollar_split.png`** — Stacked bar: hitter vs pitcher dollar allocation. One bar
   per model variant tested.

7. **`cv_diagnostics.png`** — Leave-one-year-out cross-validation results. For each
   held-out year, show: predicted vs actual SGP denominators, rank correlation of
   implied valuations.

### Optional Plots (If Roster Data Available)

8. **`inflation_by_year.png`** — Bar chart of computed inflation factor per year.
9. **`keeper_surplus_distribution.png`** — Histogram of keeper surplus values.
10. **`spending_split_comparison.png`** — Model-derived vs historical hitter/pitcher
    dollar split by year.

---

## Step 7: Pipeline Runner (`run_pipeline.py`)

End-to-end execution:

```python
def run_pipeline(config: SGPConfig) -> dict:
    """
    Run full SGP pipeline and return results dict.

    Steps:
    1. Load and prepare data
    2. Compute SGP denominators
    3. Compute replacement level
    4. Compute dollar values (if player projections available)
    5. Generate diagnostics
    6. Return metrics dict for autoresearch

    Returns dict with all METRIC values.
    """
```

### Metrics for Autoresearch

The pipeline must return these metrics (printed as `METRIC name=value`):

**Primary metrics (optimization targets):**

| Metric | Description | Better |
|--------|-------------|--------|
| `sgp_cv_nrmse` | **Primary metric.** Normalized LOYO RMSE — per-category RMSE ÷ category mean denominator, averaged across all 10 categories. Each category contributes equally regardless of scale. | Lower |
| `sgp_cv_rmse` | Raw LOYO RMSE of SGP denominators. Retained for backwards compatibility but dominated by large-scale categories (R, RBI, SO). Use nRMSE for optimization. | Lower |
| `rank_correlation` | Mean Spearman correlation: SGP-implied ranks vs actual standings ranks across held-out years | Higher |
| `category_balance_cv` | CV (coefficient of variation) of total SGP allocated across 10 categories — lower means more balanced | Lower |
| `dollar_pool_error` | Absolute difference between allocated dollars and $3,600 target. Currently hardcoded to 0 (no player projections yet). | Lower (should be ~0) |

**Per-category metrics (used by composite selection):**

| Metric | Description |
|--------|-------------|
| `nrmse_{cat}` | Per-category normalized RMSE (e.g. `nrmse_HR`, `nrmse_AVG`). Used to select the best config for each category independently. |
| `best_method_{cat}` | Which config won for each category in the composite. |

**Secondary metrics (diagnostic, not optimized):**

| Metric | Description |
|--------|-------------|
| `hitter_pct` | Percentage of dollar pool allocated to hitters |
| `n_positive_par_hitters` | Count of hitters with positive PAR |
| `n_positive_par_pitchers` | Count of pitchers with positive PAR |
| `sgp_denom_R` through `sgp_denom_SO` | Individual SGP denominators (10 values) |
| `sgp_ci_width_avg` | Average CI width across categories (uncertainty measure) |
| `inflation_factor` | If keeper adjustment enabled |
| `method` | Which SGP method was used (for grouping) |
| `data_window` | primary_only or augmented (for grouping) |

---

## Step 8: Autoresearch Integration

### Entry Point

```bash
python3 -m sgp.run_pipeline --config sweep
```

The Python runner handles the sweep internally, outputting `METRIC name=value` lines
for each configuration. The sweep runs two selection strategies on the same data and
compares them head-to-head.

### Configuration Sweep

The sweep tests all combinations of:

```python
SWEEP = {
    "sgp_method": ["pairwise_mean", "pairwise_median", "ols", "robust_reg"],
    "use_supplemental": [False, True],
    "time_decay": [False, True],
    "time_decay_rate": [0.80, 0.85, 0.90],  # only when time_decay=True
    "punt_detection": [False, True],
    "replacement_hitter_buffer": [30, 40, 50, 60, 70],
    "replacement_pitcher_buffer": [30, 40, 50, 60, 70],
}
```

**Pruning rules** to avoid combinatorial explosion:
- `time_decay_rate` only varies when `time_decay=True`
- `replacement_hitter_buffer` and `replacement_pitcher_buffer` always vary together
  (same value for both) to reduce combinations

This gives: 4 methods × 2 supplemental × (1 no-decay + 3 decay rates) × 2 punt × 5
buffer = 320 configs. Each runs in <0.2s. Full sweep completes in ~60s.

**Note on replacement buffer**: The buffer has zero effect on CV metrics until player
projections exist (Layers 1-3). It only affects the placeholder replacement-level
estimate. The 5 buffer values produce identical RMSE/nRMSE/rank_correlation, yielding
only 64 truly distinct configs among the 320. The buffer sweep becomes meaningful when
Layers 1-3 are connected.

### Dual Selection Strategy

After the sweep completes, results are analyzed two ways:

#### Strategy 1: Global Best

Pick the single config that minimizes overall nRMSE. Every category uses the same
method, supplemental setting, decay setting, and punt setting.

**Pro**: Simple, consistent, one set of assumptions.
**Con**: Optimizes aggregate — may sacrifice accuracy on individual categories.

#### Strategy 2: Per-Category Composite

For each of the 10 categories independently, pick the config that minimizes that
category's nRMSE. Assemble a composite SGPResult where each denominator comes from
its category-optimal config.

**Pro**: Each category gets the treatment that best fits its statistical properties.
For example:
- SV might prefer punt detection ON (teams genuinely punt saves)
- AVG might prefer punt detection OFF (tight distributions, every data point helps)
- R/SO might prefer supplemental=False (didn't exist pre-2019)
- ERA/WHIP might prefer robust regression (handles IP-penalty outliers)

**Con**: More degrees of freedom → higher overfitting risk with only 5 primary years.
Each category has only 5 CV folds, so the per-category "best" might be a noise artifact.

#### Head-to-Head Comparison

Both strategies are evaluated on the same held-out data:

1. **Composite nRMSE**: Average of per-category nRMSEs. For the global strategy, this
   is the standard nRMSE. For the composite strategy, it's the average of each category's
   minimum nRMSE — by construction this will be ≤ the global nRMSE (it can cherry-pick).

2. **Rank correlation**: Recompute LOYO rank correlation using the composite denominators.
   This is the real test — does per-category optimization actually improve standings
   prediction, or does it just overfit each category's denominator while losing coherence
   across categories?

3. **Config diversity**: Report which config won for each category. If all 10 categories
   pick the same config, the composite collapses to the global result. If there's high
   diversity, it suggests genuine category-specific structure — OR overfitting. Interpret
   with the rank correlation.

The sweep prints both strategies' results and a summary comparison. The METRIC lines
correspond to whichever strategy produced the better rank correlation (the metric that
most directly tests "does this help predict actual standings?").

### Interpreting the Comparison

| Outcome | Interpretation |
|---------|---------------|
| Composite has better rank_correlation AND lower nRMSE | Per-category optimization is capturing real structure. Use the composite. |
| Composite has lower nRMSE but WORSE rank_correlation | Overfitting. The per-category picks optimize each denominator but lose coherence. Use the global. |
| Composite ≈ Global on both metrics | Categories don't have meaningfully different optimal configs. Use the global (simpler). |
| Composite has much higher config diversity but only marginal improvement | Likely noise. Use the global unless specific category choices have clear domain justification (e.g. punt detection for SV). |

---

## Cross-Validation Strategy

### Leave-One-Year-Out (LOYO)

For each year Y in the calibration window:
1. Compute SGP denominators using all years EXCEPT Y
2. Using those denominators, compute what each team's stat line in year Y would be
   "worth" in SGP
3. Rank teams by total SGP
4. Compare SGP-implied ranks to actual standings ranks (Spearman correlation)
5. Compare SGP denominators from training set to those from the held-out year (RMSE)

This tests: "If we calibrate on N-1 years, does the model predict relative team
performance in the held-out year?"

### Metrics from CV

- `sgp_cv_nrmse`: **Primary metric.** Normalized RMSE of denominator prediction.
  ```
  For each category:
    cat_rmse = sqrt(mean((pred_denom - actual_denom)^2 across folds))
    cat_nrmse = cat_rmse / mean(actual_denom across folds)
  sgp_cv_nrmse = mean(cat_nrmse across all 10 categories)
  ```
  Interpretation: "On average, the model predicts each category's SGP denominator within
  X% of its true value on held-out years." A value of 0.25 = 25% average prediction error.

  **Why normalized?** Raw RMSE mixes categories with vastly different scales (AVG
  denominator ~0.002 vs SO denominator ~30). A 1-unit error on SO is trivial (~3%) but
  a 1-unit error on AVG would be catastrophic (~400×). Raw RMSE treats both the same.
  nRMSE gives each category equal weight by expressing errors as proportions.

  The Spearman correlation between raw RMSE and nRMSE config rankings is ~0.67 — they
  disagree meaningfully on which configs are best. Notably, punt detection helps raw RMSE
  (reduces absolute error on big-scale categories) but hurts nRMSE (removes data from
  tight-distribution rate stats where every observation matters).

- `sgp_cv_rmse`: Raw RMSE of denominator prediction (retained for backwards compatibility)
  ```
  For each fold: denom_predicted (from N-1 years) vs denom_actual (from held-out year)
  RMSE = sqrt(mean of all squared errors across folds and categories)
  ```

- `rank_correlation`: Mean Spearman ρ between SGP-implied ranks and actual total points
  ranks in held-out years
  ```
  For held-out year Y:
    For each team: total_sgp = sum(team_stat[cat] / sgp_denom[cat] for cat in categories)
    rank_correlation_Y = spearman(total_sgp_ranks, actual_total_pts_ranks)
  rank_correlation = mean(rank_correlation_Y for Y in calibration_years)
  ```
  This is the most direct test of whether the SGP model works: "Given these denominators,
  can we rank teams in the correct order?" ρ > 0.95 across all tested configs indicates
  the SGP framework is fundamentally sound for this league.

### Small Sample Caveats

With only 5 primary years, LOYO gives 5 folds. Each fold trains on 4 years (~36-40
team-seasons). CIs will be wide. This is inherent to the problem — document it honestly
rather than overfitting to the small sample.

Specific concerns:
- **Denominator instability**: Removing one year may shift denominators 15-25%. This is
  expected with 5 years and does NOT necessarily mean the model is bad — it means our
  uncertainty is high.
- **Rank correlation floor**: With 10 teams, random ranking gives ρ ≈ 0. A model that
  captures even broad category relationships should achieve ρ > 0.5. ρ > 0.8 would be
  excellent for this sample size.
- **Overfitting risk**: With ~50 data points, the model should be simple. The pairwise
  method has essentially zero parameters (it's a summary statistic), which is a feature.
  Regression adds model complexity. Simpler is likely better here.

---

## Step 9: Interpreting Sweep Results

When the sweep runs (`python3 -m sgp.run_pipeline --config sweep`), the output includes
METRIC lines and a comparison summary. This section explains how to read those results,
assess accuracy, identify improvements, and determine next steps.

### How to Read the Output

The sweep prints to stderr (progress, summaries) and stdout (METRIC lines). Key sections:

1. **Progress**: Config count, elapsed time, ETA.
2. **Global best**: The single config minimizing overall nRMSE, with its key metrics.
3. **Per-category composite**: The composite assembled from each category's best config,
   with its key metrics and which config won for each category.
4. **Head-to-head comparison**: Side-by-side nRMSE and rank_correlation for both strategies.
5. **METRIC lines**: The winning strategy's metrics in `METRIC name=value` format.

### Accuracy Assessment

Report these for both strategies:

| Metric | What it tells you | Typical range | What's good |
|--------|-------------------|---------------|-------------|
| nRMSE | Average % error predicting held-out year denominators | 0.20–0.35 | < 0.25 is strong for 5 years of data |
| rank_correlation | How well SGP-implied ranks match actual standings | 0.95–0.97 | > 0.95 means the model reliably orders teams |
| category_balance_cv | Whether all categories contribute equally to SGP | 0.9–1.2 | < 1.0 ideal; > 1.5 means some categories dominate |

**Calibrating expectations for this dataset:**
- 5 primary years (2019, 2021-2024) → 5 LOYO folds, each trained on 4 years (~40 team-seasons)
- Removing one year can shift denominators 15-25% — this is inherent variance, not model failure
- nRMSE of 0.25 means "each category's denominator is predicted within ~25% on average"
- This is honest uncertainty. With 5 years, you cannot do much better without overfitting.

**Red flags to watch for:**
- rank_correlation < 0.90 → something is fundamentally wrong
- nRMSE > 0.40 → model is not capturing year-to-year structure
- One category's nRMSE >> others → that category's data may have quality issues
- Composite rank_correlation < global rank_correlation → overfitting (per-category picks
  optimize denominators but lose cross-category coherence)

### What the SGP Denominators Mean

Each SGP denominator answers: "How many units of stat X does it take to gain 1 standings
point in this league?"

Example from a typical best config:
```
HR:   ~11    (11 more HR → +1 standings point)
R:    ~31    (31 more runs → +1 standings point)
RBI:  ~30    (30 more RBI → +1 standings point)
SB:   ~7     (7 more SB → +1 standings point)
AVG:  ~.003  (.003 higher team AVG → +1 standings point)
W:    ~3     (3 more wins → +1 standings point)
SV:   ~6     (6 more saves → +1 standings point)
SO:   ~30    (30 more SO → +1 standings point)
ERA:  ~.09   (.09 lower team ERA → +1 standings point)
WHIP: ~.017  (.017 lower team WHIP → +1 standings point)
```

These are league-specific. Generic AL-only SGP values from public sources can serve as
a sanity check — if ours differ by >50%, investigate why (our league may genuinely differ,
or there may be a data issue).

### Identifying Improvement Opportunities

After reviewing results, assess these areas:

**1. Data quality improvements (highest impact):**
- Scrape actual team AB/IP from OnRoto to replace the 7,300/1,300 estimates
- Add 2025 data once the season completes (grows primary window to 6 years)
- Cross-reference SGP denominators against published AL-only values

**2. Model improvements (medium impact):**
- Per-category composite vs global: if composite shows genuine improvement on rank
  correlation (not just nRMSE), it should become the default
- Mixed methods: e.g., OLS for counting stats + pairwise for rate stats
- Separate punt detection per category (rather than global on/off): always on for SV,
  always off for AVG, sweep for others
- Allow hitter and pitcher buffer to vary independently (currently tied together)

**3. Validation improvements (unlocked by Layers 1-3):**
- dollar_pool_error: currently hardcoded to 0 — becomes real when player projections exist
- Replacement buffer calibration: buffer has no effect until players can be ranked
- Historical spending split comparison: model-derived vs actual league spending
- Back-test against prior drafts: would the model's dollar values have been profitable?

**4. Diminishing returns (defer):**
- More sophisticated time decay (per-category decay rates)
- Bayesian SGP estimation (proper uncertainty quantification)
- Mixed-effects models (year as random effect)
- These are statistically interesting but unlikely to move the needle with only 5 years

### Next Steps After Sweep

Based on sweep results, the recommended sequence:

1. **Lock in Layer 4 defaults**: Update `config.py` with the winning config(s). If using
   per-category composite, the config stores per-category method selections rather than a
   single global method.

2. **Build data ingestion (Layer 0)**: Get player projections flowing. Options:
   - Scrape FanGraphs Steamer/ZiPS projections for AL players
   - Scrape ATC or other consensus projections
   - Build custom models from Statcast data (Layer 1-2)
   - Simplest MVP: download a CSV of public projections and wire it in

3. **Connect Layers 1-3 → Layer 4**: Once player projections exist:
   - Compute player-level SGP using the calibrated denominators
   - Subtract replacement-level SGP to get PAR
   - Convert PAR to dollar values
   - The `dollar_pool_error` metric becomes real and validates the full pipeline

4. **Re-run sweep with player data**: The replacement buffer sweep becomes meaningful.
   Re-sweep to calibrate the buffer against actual player rankings.

5. **Add inflation model**: Use `historical_rosters.csv` keeper data to compute
   inflation factors for draft-day valuations.

### What to Report to the User

When presenting sweep results, include:

1. **Winner**: Which strategy won (global vs composite) and the specific config(s)
2. **Key metrics**: nRMSE, rank_correlation, and what they mean in plain language
3. **Per-category breakdown**: A table showing each category's best config and nRMSE,
   highlighting any categories that strongly prefer a different config
4. **Accuracy context**: What's achievable with 5 years of data, and whether results
   suggest the model is sound vs needs investigation
5. **Actionable improvements**: Ranked by expected impact and effort
6. **Next steps**: What to build next in the pipeline

1. ~~**Team AB and IP estimation**~~ **RESOLVED**: team_ab=7,300, team_ip=1,300.
   Derived from cross-referencing historical data. TODO: scrape actual values from
   OnRoto stats pages for validation.

2. **Rate stat SGP at player level**: When Layers 1-3 produce player projections, the
   rate stat SGP conversion needs the player's projected AB or IP. This is a Layer 3→4
   interface question. Document the expected input format:
   ```
   player_projections.csv: player, team, pos, PA, AB, IP, R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO
   ```

3. **Contract year codes**: The roster data contains contract codes beyond a/b/c (ar, r,
   y, L, LT, SEPT, numeric). Need to map these to keeper/non-keeper status. See Plan 01
   open questions.

4. **Historical inflation validation**: Even if we build the inflation model, we can't
   validate it against actual auction prices (the draft is offline). We CAN validate it
   against overall spending patterns (total salary deployed should roughly match
   inflation-adjusted expectations).

5. ~~**Multi-category punt strategies**~~ **RESOLVED**: Punt detection off by default.
   When enabled, operates independently per category.

6. ~~**Marginal vs. average SGP**~~ **RESOLVED**: Stick with average SGP. Standard for
   roto valuation since teams can finish anywhere.

---

## Dependencies

```
pandas
numpy
scipy
scikit-learn
matplotlib
```

All standard. No exotic dependencies.

---

## Testing Strategy

### Unit Tests

- `test_sgp_calc.py`: Verify pairwise differences on synthetic data (known gaps)
- `test_data_prep.py`: Verify exclusion logic (900 IP, punt detection, year filtering)
- `test_dollar_values.py`: Verify dollar pool sums to $3,600, PAR calculations correct

### Integration Tests

- Run full pipeline on historical data, verify outputs are reasonable:
  - All SGP denominators positive
  - SGP denominators in plausible ranges (compare to published generic AL-only values)
  - Dollar pool = $3,600 (±$1 for rounding)
  - Hitter/pitcher split between 55-80%
  - All 10 categories contribute meaningfully (no single category dominates)

### Smoke Test

```bash
python3 -m sgp.run_pipeline --config default
# Should complete without errors and produce:
# - SGP denominators for all 10 categories
# - Diagnostic plots in plots/
# - METRIC lines to stdout
```

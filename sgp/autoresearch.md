# SGP Model Calibration — Autoresearch Session

## Objective
Find the optimal SGP calibration configuration for the Moonlight Graham league.

## Data
- Historical standings: 2015-2024 (excluding 2020, 2025)
- Primary window: 2019, 2021-2024 (50 team-seasons)
- Supplemental window: 2015-2018 (42 team-seasons, 8 categories only)

## Methodology

### Configuration sweep
Tests all combinations of:
- SGP method: pairwise_mean, pairwise_median, ols, robust_reg
- Supplemental data: yes/no
- Time decay: off / 0.80 / 0.85 / 0.90
- Punt detection: on/off
- Replacement buffer: 30, 40, 50, 60, 70 (same for hitters and pitchers)

Total configurations: ~640

### Primary optimization metrics
- `sgp_cv_rmse` — LOYO RMSE of SGP denominators (lower is better)
- `rank_correlation` — Mean Spearman ρ: SGP-implied vs actual standings (higher is better)

### Secondary diagnostics
- `category_balance_cv` — CV of denominators across categories (lower = more balanced)
- `sgp_ci_width_avg` — Average bootstrap CI width (lower = more precise)
- Individual category denominators for sanity checking

## Running

```bash
# Single default config
bash sgp/autoresearch.sh --config default

# Full sweep
bash sgp/autoresearch.sh --config sweep
```

## Results
[Autoresearch fills this in]

## Best Configuration
[Which combination of parameters minimized sgp_cv_rmse while maintaining rank_correlation]

## Recommendations
[What to use going forward]

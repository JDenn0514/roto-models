# Baseball Models — Moonlight Graham League

## What This Is

A rotisserie fantasy baseball valuation model for a 10-team AL-only keeper league called
Moonlight Graham, hosted on OnRoto (onroto.fangraphs.com). The goal is to convert
projected player stat lines into auction dollar values calibrated to this specific
league's historical data.

## League Essentials

- 10 teams, AL-only player pool (15 AL teams)
- 10 scoring categories: R, HR, RBI, SB, AVG (batting) + W, SV, ERA, WHIP, SO (pitching)
- Roster: 15 hitters + 11 pitchers active, reserves (DL/FARM/RES)
- Auction: $360/team budget, $1 min bid, $75 max salary
- Keeper league: up to 3-year contracts, extensions at +$5 or +$10
- 900 IP minimum for ERA/WHIP scoring (teams below get 0 points)
- Full rules in `league-context.md`

## Model Architecture (4-Layer Pipeline)

```
Layer 1: Rate Stats    → per-PA rates (HR/PA, AVG, etc.) — NOT YET BUILT
Layer 2: Playing Time  → projected plate appearances      — NOT YET BUILT
Layer 3: Counting Stats → Layer 1 × Layer 2               — NOT YET BUILT
Layer 4: Valuation     → SGP → PAR → Dollar Values        — COMPLETE
```

Design documented in `getting-started.md`. Layers 1-3 are currently bypassed by
ingesting third-party projections (ATC, THE BAT X) via the `projections/` pipeline.
Building custom projection models is optional future work.

## Codebase Overview

### SGP Valuation Engine (`sgp/`)

The core model — calibrated and validated. Key modules:

- `config.py` — League config + composite per-category SGP settings (from autoresearch sweep)
- `sgp_calc.py` — SGP denominator calculation (pairwise, OLS, robust regression with bootstrap CIs)
- `data_prep.py` — Data loading, filtering, preprocessing from historical standings
- `replacement.py` — Replacement-level computation from standings averages
- `dollar_values.py` — PAR conversion, dollar values, keeper inflation, hitter/pitcher split
- `validate.py` — End-to-end validation pipeline for historical years (2019, 2021-2024)
- `run_pipeline.py` — Autoresearch cross-validation sweep with metrics output
- `diagnostics.py` — Plots, scatter charts, stability analysis, CV rank correlation
- `autoresearch.sh` — Bash runner for sweeping 320+ configs

### Projection Pipeline (`projections/`)

Fetches third-party projections and converts them to dollar values:

- `fetch.py` — FanGraphs API integration (THE BAT X, ATC, Depth Charts) with 24h caching
- `transform.py` — Normalize projections, classify pitcher role (SP/RP), handle minor leaguers
- `valuate.py` — Wire projected stats through SGP model to dollar values
- `run_pipeline.py` — End-to-end: fetch → transform → valuate → output (`python3 -m projections.run_pipeline`)

### MSP Targeting (`targeting/`)

Team-specific player targeting using Marginal Standings Points. Run as `python3 -m targeting`:

- `model.py` — Core MSP: keeper baselines, fill model, standings ranking, marginal computation
- `name_match.py` — Unicode normalization, Jr./Sr., manual aliases for roster↔projection joins
- `backtest.py` — Historical validation (2019, 2021-2025): reconstruct pre-auction, 3 eval metrics
- `sweep.py` — Autoresearch sweep over model variants, outputs CSV + METRIC lines
- `__main__.py` — CLI runner for 2026 live targeting

**Live config**: `proportional_fill` (fd=0.5, displacement=True). Backtests slightly favor `keeper_only`, but fill model produces realistic standings gaps needed for sensible 2026 targeting. Run sweep: `python3 -m targeting.sweep`

### OnRoto Scrapers (`scrapers/`)

Fetch league data from OnRoto using credentials in `.env`. Run as `python3 -m scrapers.<name>`:

- `auth.py` — Shared authentication module (login, BASE_URL, LEAGUE)
- `standings.py` — Team stats and standings points
- `rosters.py` — Final rosters (status, contract, salary)
- `transactions.py` — Transaction history
- `team_stats.py` — Team stat totals (AB, IP for rate stat denominators)
- `prev_active.py` — Augment roster data with previously-active players
- `rules.py` — League rules from OnRoto settings page
- `preauction_rosters.py` — Pre-auction keeper rosters
- `player_stats.py` — Player stats from FanGraphs via pybaseball (not OnRoto)

## Data

### Historical (scraped from OnRoto)
- `data/historical_standings.csv` — 92 rows, team stats + standings points (2015-2024)
- `data/historical_rosters.csv` — ~3,984 rows, player-team-year (salaries, contracts, positions, 2015-2025)
- `data/historical_transactions.csv` — ~31,362 rows, all trades/acquisitions/DL moves (2015-2025)
- `data/team_totals.csv` — 50 rows, team-year aggregates (AB, IP) for rate stat conversion
- `data/player_stats.csv` — ~3,500 rows, player stats for validation years (2019, 2021-2024)

### Validation Outputs
- `data/player_valuations_{year}.csv` — Per-player SGP + dollar values (2019, 2021-2025)
- `data/sweep_results.csv` — 320-config SGP autoresearch sweep results
- `data/targeting_sweep_results.csv` — 7-config MSP targeting sweep results
- `data/targeting_*_detail.csv` — Per-team-year backtest detail (standings, draft, optimal)

### 2026 Draft Valuations
- `data/valuations_atc_2026.csv` — Primary (ATC): 645 players
- `data/valuations_thebatx_2026.csv` — Cross-reference (THE BAT X): 618 players
- `data/valuations_combined_2026.csv` — Side-by-side comparison
- `data/msp_gusteroids_atc_2026.csv` — MSP-augmented valuations for Gusteroids
- `data/msp_projected_standings_2026.csv` — Projected standings (keeper-only)
- `data/projections/` — Cached raw projections from FanGraphs API

### Other
- `plots/` — 20 diagnostic PNGs (SGP stability, validation distributions, position scarcity, etc.)
- `reports/` — Quarto analysis reports + generated interactive HTML tables (`generate_tables.py`)
- `research/` — Per-category research notes (batting and pitching models, data sources)
- Credentials for OnRoto scraping in `.env` (never commit this)

## Key Data Quality Issues

- **2020**: COVID-shortened season — exclude from SGP calibration
- **2025**: Complete season — included in primary calibration
- **2015-2018**: Only 8 categories (no R or SO) — usable as supplemental data only
- **2016-2017**: 11 teams instead of 10
- **900 IP penalty**: Some teams score 0 in ERA+WHIP despite having stats (they didn't pitch enough innings). Exclude these from ERA/WHIP SGP calculations.
- **Primary calibration window**: 2019, 2021, 2022, 2023, 2024, 2025 (~60 team-seasons)

## Implementation Plans

Detailed plans with methodology, code architecture, and open questions:

1. `plans/01-roster-scraper.md` — Scrape roster/salary/contract data from OnRoto ✅
2. `plans/02-sgp-model.md` — SGP calibration, replacement level, dollar values, autoresearch benchmarking ✅
3. `plans/03-validation-pipeline.md` — Historical player-level validation ✅
4. `plans/04-projection-ingestion.md` — FanGraphs projection ingestion + 2026 valuations ✅
5. MSP targeting metric — team-specific MSP framework, backtest, sweep, report ✅

## What's Left

- **Layers 1-3** (custom projection models) — optional; third-party projections work well
- **Opening-day roster reconstruction** from transaction data (deferred)
- **Keeper identification logic** (contract progression → keeper decisions)
- **In-season revaluation** (ROS projections mid-season)
- **Trade/keeper decision support tools**

## Conventions

- Python only: pandas, numpy, scikit-learn, scipy, matplotlib, pybaseball (see `requirements.txt`)
- Diagnostic plots go to `plots/`
- Generated HTML reports go to `reports/`
- Autoresearch compatibility: `autoresearch.sh` outputs `METRIC name=value` lines
- Load OnRoto credentials from `.env`, never hardcode them in new code
- Run scrapers as `python3 -m scrapers.<name>` from project root

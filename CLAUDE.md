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
Layer 4: Valuation     → SGP → PAR → Dollar Values        — BUILDING NOW
```

Design documented in `getting-started.md`. Layer 4 can be built and calibrated
independently using historical standings data, then connected to Layers 1-3 later.

## Data

- `data/historical_standings.csv` — 10 years of team stats and standings points (2015-2024 + partial 2025)
- `data/historical_rosters.csv` — ~3,984 rows of player-team-year data (salaries, contracts, positions, eligibility) for 2015-2024
- Credentials for OnRoto scraping in `.env` (never commit this)
- Existing scrapers: `scrape_standings.py`, `scrape_rules.py`

## Key Data Quality Issues

- **2020**: COVID-shortened season — exclude from SGP calibration
- **2025**: Partial season — exclude
- **2015-2018**: Only 8 categories (no R or SO) — usable as supplemental data only
- **2016-2017**: 11 teams instead of 10
- **900 IP penalty**: Some teams score 0 in ERA+WHIP despite having stats (they didn't pitch enough innings). Exclude these from ERA/WHIP SGP calculations.
- **Primary calibration window**: 2019, 2021, 2022, 2023, 2024 (~50 team-seasons)

## Implementation Plans

Detailed plans with methodology, code architecture, and open questions:

1. `plans/01-roster-scraper.md` — Scrape roster/salary/contract data from OnRoto
2. `plans/02-sgp-model.md` — SGP calibration, replacement level, dollar values, autoresearch benchmarking

## Conventions

- Python only: pandas, numpy, scikit-learn, scipy, matplotlib
- Diagnostic plots go to `plots/`
- Autoresearch compatibility: `autoresearch.sh` outputs `METRIC name=value` lines
- Load OnRoto credentials from `.env`, never hardcode them in new code

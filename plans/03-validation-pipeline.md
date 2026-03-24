# Plan: End-to-End SGP Validation with Historical Player Stats

## Goal

Validate the SGP model by running actual player stats through the full valuation
pipeline and comparing model-derived dollar values to what teams actually paid.
This answers: "Does the model produce sensible dollar values, and where does the
league misprice players?"

## Why This Matters

The SGP denominators are validated via cross-validation (rank correlation = 0.961),
but that's a team-level test. This validation is player-level:

- Does the total dollar pool sum to ~$3,600?
- Does the hitter/pitcher dollar split match historical spending (~59-65%)?
- Are the highest-valued players the ones you'd expect?
- Which players had the most surplus (value - salary)?
- Where does the league systematically overpay or underpay?

## Prerequisites

- SGP model calibrated with composite defaults (done)
- `data/historical_rosters.csv` — player names, salaries, positions, teams (done)
- `onroto_auth.py` — authentication module (done)
- `scrape_team_stats.py` — existing scraper for team totals (done, will extend pattern)

---

## Step 1: Scrape Individual Player Stats (`scrape_player_stats.py`)

### Data Source

OnRoto's `display_team_stats.pl` page shows individual player stat lines within
each team's roster. The existing `scrape_team_stats.py` only extracts the TOTAL
rows — this scraper extracts the individual player rows above them.

### URL Pattern

```
{BASE_URL}/baseball/webnew/display_team_stats.pl?{LEAGUE}+0+SORT_{IDX}+{YEAR}&session_id={SID}
```

Iterate SORT_0 through SORT_11 (10-11 teams). Stop when team name extraction fails.

### Page Structure

Each team page has two stat tables:

**Active Hitters table (2019+ layout):**

| Column | Description |
|--------|-------------|
| Name | Player name (link text) |
| Pos | Fantasy position (1B, OF, etc.) |
| Tm | MLB team abbreviation |
| G | Games |
| AB | At bats |
| HR | Home runs |
| RBI | Runs batted in |
| SB | Stolen bases |
| AVG | Batting average |
| R | Runs scored |

**Active Pitchers table (2019+ layout):**

| Column | Description |
|--------|-------------|
| Name | Player name (link text) |
| Pos | Fantasy position (P) |
| Tm | MLB team abbreviation |
| G | Games |
| IP | Innings pitched |
| W | Wins |
| SV | Saves |
| ERA | Earned run average |
| WHIP | Walks + hits per inning |
| SO | Strikeouts |

### Parsing Approach

Follow the same patterns as `scrape_team_stats.py`:

1. Find header rows by looking for `<th>` elements containing known column names
   (AB, HR, IP, W, etc.)
2. Extract column indices dynamically (column layout varies by year)
3. Parse each player row: extract name from link text, stats from `<td>` cells
4. Stop at TOTAL row (which marks end of active section)
5. Skip reserve/DL/FARM sections (stats don't count toward standings)
6. Handle the `accumulated&nbsp;current_week` format — extract only the accumulated
   portion (the number before `&nbsp;` or `<br>`)

### Player Identification

- Extract player name from `<a>` tag text within the Name cell
- Optionally extract OnRoto player_id from the link URL (for matching to rosters)
- Match to `historical_rosters.csv` by player_name + team + year for salary data

### Output

```
data/player_stats.csv
```

Columns:
```
year, fantasy_team, player_name, player_id, mlb_team, position,
AB, R, HR, RBI, SB, AVG,        # hitters (IP/pitching cols = NaN)
IP, W, SV, ERA, WHIP, SO,       # pitchers (AB/hitting cols = NaN)
is_pitcher                       # True/False
```

### Scope

- **Validation years**: 2024 and 2025 (most relevant, 10 categories, current roster era)
- **Stretch**: 2019-2025 to see valuation trends over time
- **Skip**: 2015-2018 (8 categories, different column layout, less useful)
- **Skip**: 2020 (COVID, excluded from SGP calibration anyway)
- **Active players only**: Reserve/DL/FARM stats don't count toward standings

### Rate Limiting

`time.sleep(0.3)` between team pages (same as `scrape_team_stats.py`).
~10-11 pages per year, ~2 years = ~22 requests. Under a minute total.

### Error Handling

- 404 or empty page on SORT index → stop iterating (phantom team slot)
- Duplicate team names (SORT_10 phantom) → deduplicate by team name, keep first
- Missing stat columns → log warning, fill with NaN
- Player name mismatches between scraper and rosters → report unmatched for manual review

---

## Step 2: Valuation Pipeline (`sgp/validate.py`)

### Input

- `data/player_stats.csv` (from Step 1)
- `data/historical_rosters.csv` (salaries, contracts)
- SGP composite config (calibrated denominators)

### Pipeline

```python
def validate_year(year: int, config: SGPConfig = None) -> pd.DataFrame:
    """Run full valuation on actual player stats for a given year.

    1. Load player stats for the year
    2. Merge with roster data (salary, contract)
    3. Compute per-category SGP for each player
    4. Sum to total SGP
    5. Subtract replacement level → PAR
    6. Convert PAR → dollar values
    7. Return DataFrame with stats + SGP + dollars + salary
    """
```

### SGP Conversion Details

**Counting stats (R, HR, RBI, SB, W, SV, SO):**
```python
player_sgp = player_stat / sgp_denom
```

**Rate stats — this is where AB and IP matter:**
```python
# AVG: player's marginal impact on team batting average
player_sgp_avg = (player_avg - replacement_avg) * (player_ab / team_ab) / sgp_denom_avg

# ERA: player's marginal impact on team ERA (lower = better)
player_sgp_era = (replacement_era - player_era) * (player_ip / team_ip) / sgp_denom_era

# WHIP: same as ERA
player_sgp_whip = (replacement_whip - player_whip) * (player_ip / team_ip) / sgp_denom_whip
```

`team_ab` (6514) and `team_ip` (1226) are the league-wide means from `team_totals.csv`.
These are already stored in `SGPConfig`.

`player_stat_to_sgp()` in `sgp_calc.py` already implements this logic.

### Replacement Level

Use the existing `compute_replacement_level()` from `replacement.py`, which
estimates replacement stats from historical standings averages. This is a
placeholder until we can compute it from the actual player pool — but it's
sufficient for validation.

### Dollar Value Conversion

Use `compute_dollar_values()` from `dollar_values.py`:
1. Compute PAR = total_sgp - replacement_sgp (position-appropriate)
2. Only positive-PAR players get dollars
3. dollars_per_par = $3,600 / total_positive_par
4. Apply $1 minimum floor with redistribution

---

## Step 3: Diagnostics and Reports

### Key Validation Checks

| Check | Expected | Red Flag |
|-------|----------|----------|
| Total dollar pool | $3,600 | Off by > $50 |
| Hitter/pitcher split | 60-67% hitters | Outside 55-75% |
| Top 10 hitters by value | Recognizable AL stars | Unknown names in top 10 |
| Top 10 pitchers by value | Recognizable AL aces/closers | Unknown names in top 10 |
| Positive-PAR hitters | ~120-170 | < 100 or > 200 |
| Positive-PAR pitchers | ~80-130 | < 60 or > 150 |
| Dollar pool ≈ sum of salaries | Roughly similar | > 20% divergence |

### Output Artifacts

1. **`data/player_valuations_{year}.csv`** — Full player-level output:
   ```
   player_name, fantasy_team, position, salary, contract_year,
   R, HR, RBI, SB, AVG, W, SV, SO, ERA, WHIP, AB, IP,
   sgp_R, sgp_HR, ..., sgp_WHIP,
   total_sgp, par, dollar_value, surplus
   ```

2. **`reports/validation-{year}.qmd`** — Quarto report with:
   - Dollar value distribution (histogram)
   - Top 25 most valuable players (table)
   - Top 25 surplus players: value - salary (table)
   - Top 25 overpaid players: salary - value (table)
   - Hitter/pitcher split comparison (model vs actual spending)
   - Scatter: model dollar value vs actual salary
   - Category-level SGP leaders

### Stretch Diagnostics (if running multiple years)

- Year-over-year: do the same players show up as undervalued repeatedly?
- Team-level: which fantasy teams consistently find surplus? (good drafters)
- Position scarcity: does the model value catchers/closers differently than the market?

---

## Step 4: CLI Interface

```bash
# Scrape player stats for 2024-2025
python3 scrape_player_stats.py

# Run validation for a specific year
python3 -m sgp.validate --year 2024

# Run validation and generate report
python3 -m sgp.validate --year 2024 --report
```

---

## Architecture

```
scrape_player_stats.py       # New: scrape individual player stats from OnRoto
sgp/
├── validate.py              # New: end-to-end validation pipeline
├── config.py                # Existing: SGP config with composite defaults
├── sgp_calc.py              # Existing: player_stat_to_sgp()
├── replacement.py           # Existing: compute_replacement_level()
├── dollar_values.py         # Existing: compute_dollar_values()
data/
├── player_stats.csv         # New: scraped player stat lines
├── player_valuations_2024.csv  # New: output with dollar values
reports/
├── validation-2024.qmd      # New: validation report
```

---

## Open Questions

1. **Player name matching**: The scraper extracts names from the stats page; the
   roster file has names from the roster page. These should match exactly since
   they're the same site, but verify with a sample before running the full pipeline.
   If player_id can be extracted from the stats page URL/links, use that instead.

2. **Mid-season roster changes**: A player traded mid-season may appear on two
   fantasy teams' stats pages. The stats page likely shows only their stats while
   on that team. For validation purposes, sum their stats across teams or use
   the team they finished the season on.

3. **Replacement level calibration**: The current replacement level is estimated
   from team standings averages. Once we have actual player stats, we can compute
   it properly: sort all players by total SGP, the replacement-level player is at
   position (active_slots + reserve_buffer). This becomes a calibration step in its
   own right.

---

## Dependencies

No new dependencies. Uses:
- `requests` + `beautifulsoup4` (already used by existing scrapers)
- `pandas`, `numpy` (already used by SGP model)
- `matplotlib` (already used by diagnostics)
- Quarto (already installed, used for SGP analysis report)

---

## Estimated Scope

| Step | Effort | Notes |
|------|--------|-------|
| Scraper | Medium | Extend existing pattern, main work is parsing player rows |
| Validation pipeline | Small | Mostly wiring existing functions together |
| Diagnostics/report | Medium | Tables + plots + Quarto formatting |
| **Total** | **~1 session** | Most code already exists in sgp/ |

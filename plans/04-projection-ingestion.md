# Plan: Projection Ingestion Pipeline

## Goal

Pull pre-season projections from FanGraphs (THE BAT X and ATC), filter to
AL-only players, and run them through the calibrated SGP model to produce
auction dollar values for the 2026 Moonlight Graham draft.

## Context

This pipeline connects Layers 1-3 (projections) to Layer 4 (valuation). Rather
than building custom projection models (a future effort), we ingest the two
most accurate public projection systems as our starting point:

- **THE BAT X** — most accurate standalone system for 6+ consecutive years
- **ATC** — most accurate aggregated system for 5+ consecutive years

The SGP model (Layer 4) is already built and calibrated with composite defaults.
The validation pipeline (Plan 03) validates SGP using historical actuals. This
pipeline uses projected stats instead of actuals to produce forward-looking
dollar values for draft day.

## Prerequisites

- SGP model calibrated with composite defaults (done — `sgp/` module)
- `data/historical_standings.csv` (done — for SGP denominators)
- `pybaseball` installed (done)
- FanGraphs API accessible (verified — no auth required for projections)

---

## Data Source

FanGraphs exposes an undocumented JSON API for projections:

```
GET https://www.fangraphs.com/api/projections
    ?type={system}    # thebatx, atc, fangraphsdc, steamer, zips
    &stats={bat|pit}  # batting or pitching
    &pos=all
    &team=
    &players=0
    &lg=al            # AL-only filter
```

No authentication required. Returns JSON array of player objects.

### Verified Data Availability (2026 pre-season)

| System | Batting | Pitching |
|--------|---------|----------|
| THE BAT X | 338 players | 336 players |
| ATC | 309 players | 411 players |
| Depth Charts | 312 players | 395 players |

### Key Columns Available

**Batting:** `PlayerName`, `Team`, `PA`, `AB`, `R`, `HR`, `RBI`, `SB`, `AVG`,
`H`, `BB`, `SO`, `OBP`, `SLG`, `wOBA`, `WAR`, `minpos`, `playerid`,
`xMLBAMID`, `League`

**Pitching:** `PlayerName`, `Team`, `IP`, `W`, `SV`, `ERA`, `WHIP`, `SO`,
`G`, `GS`, `BB`, `HR`, `WAR`, `K/9`, `BB/9`, `FIP`, `playerid`, `xMLBAMID`,
`League`

All 10 scoring categories (R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO) plus
AB and IP (needed for rate stat SGP conversion) are present in the API response.

### Minor Leaguers

Depth Charts projections include prospects with projected MLB playing time
(e.g., Jasson Dominguez with 98 PA). These are AL-team-assigned players who
may debut in 2026. THE BAT X and ATC also include some of these players but
with fewer low-PA entries.

**Approach**: Pull from Depth Charts in addition to THE BAT X/ATC. Use Depth
Charts to fill in any minor leaguers not present in the primary systems.

---

## Architecture

```
projections/
    __init__.py
    fetch.py           # Pull projections from FanGraphs API
    transform.py       # Normalize, merge, classify hitter/pitcher
    valuate.py         # SGP conversion + dollar values (wires into sgp/)
    run_pipeline.py    # End-to-end: fetch → transform → valuate → output
data/
    projections/
        thebatx_bat_2026.csv      # Raw API response cached
        thebatx_pit_2026.csv
        atc_bat_2026.csv
        atc_pit_2026.csv
        dc_bat_2026.csv           # Depth Charts (for minor leaguer fill)
        dc_pit_2026.csv
    valuations_thebatx_2026.csv   # Final output: projections + dollar values
    valuations_atc_2026.csv
    valuations_combined_2026.csv  # Blended from both systems
```

---

## Step 1: Fetch Projections (`projections/fetch.py`)

### Function

```python
def fetch_projections(
    system: str,         # "thebatx", "atc", "fangraphsdc"
    stats: str,          # "bat" or "pit"
    league: str = "al",
    season: int = 2026,
) -> pd.DataFrame:
    """Fetch projections from FanGraphs API. Cache to data/projections/."""
```

### Behavior

1. Hit the FanGraphs API endpoint
2. Parse JSON response into DataFrame
3. Save raw response to `data/projections/{system}_{stats}_{season}.csv`
4. Return DataFrame

### Caching

If the CSV already exists and is less than 24 hours old, load from disk instead
of hitting the API. Add a `--force-refresh` flag to bypass cache.

### Rate Limiting

`time.sleep(1)` between API calls to be respectful. Total calls per run: 6
(2 systems x 2 stat types + 2 depth chart calls).

### Error Handling

- Non-200 response → raise with status code and message
- Empty response → warn and return empty DataFrame
- Missing expected columns → raise with column name

---

## Step 2: Transform (`projections/transform.py`)

### Function

```python
def build_player_projections(
    batting_df: pd.DataFrame,
    pitching_df: pd.DataFrame,
    system: str,
) -> pd.DataFrame:
    """Normalize and combine batting + pitching projections into a single
    DataFrame ready for SGP conversion."""
```

### Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `player_name` | str | Player name |
| `team` | str | MLB team abbreviation |
| `pos_type` | str | "hitter" or "pitcher" |
| `position` | str | Position (e.g., "OF", "SS", "SP", "RP") |
| `projection_system` | str | "thebatx", "atc" |
| `fg_id` | str | FanGraphs player ID |
| `mlbam_id` | int | MLB Advanced Media ID |
| `PA` | float | Projected plate appearances (hitters) |
| `AB` | float | Projected at-bats (hitters) |
| `IP` | float | Projected innings pitched (pitchers) |
| `R` | float | Projected runs |
| `HR` | float | Projected home runs |
| `RBI` | float | Projected RBI |
| `SB` | float | Projected stolen bases |
| `AVG` | float | Projected batting average |
| `W` | float | Projected wins |
| `SV` | float | Projected saves |
| `ERA` | float | Projected ERA |
| `WHIP` | float | Projected WHIP |
| `SO` | float | Projected strikeouts |

### Transformation Rules

1. **Rename columns** to match the SGP pipeline's expectations (mostly lowercase
   mapping — the API returns proper-case column names that already match)
2. **Classify pos_type**: Players in the batting pull are "hitter"; players in
   the pitching pull are "pitcher"
3. **Derive position**: Use `minpos` field for hitters (e.g., "OF", "1B");
   for pitchers, classify as "SP" if `GS > 0 and GS/G > 0.5`, else "RP"
4. **Fill stat columns**: Hitters get `NaN` for pitching stats and vice versa
5. **Filter**: Drop any rows with `League != "AL"` (belt-and-suspenders; the
   API should already filter by league)
6. **Minimum threshold**: Drop hitters with PA < 25 and pitchers with IP < 5

### Minor Leaguer Fill

After building projections from THE BAT X and ATC, check Depth Charts for
players not present in either system. Add them with `projection_system =
"dc_fill"`. This captures prospects projected for small PA/IP who only appear
in Depth Charts.

---

## Step 3: Valuate (`projections/valuate.py`)

This wires projected stats into the existing SGP model. Uses the same functions
as the validation pipeline (Plan 03).

### Function

```python
def compute_projected_values(
    projections: pd.DataFrame,
    config: SGPConfig = None,
) -> pd.DataFrame:
    """Convert projected stats to dollar values using calibrated SGP model.

    1. Load SGP denominators (from composite config)
    2. Compute replacement level
    3. For each player, compute per-category SGP
    4. Sum to total SGP
    5. Subtract replacement → PAR
    6. Convert PAR → dollar values
    """
```

### SGP Conversion (per player)

Uses `player_stat_to_sgp()` from `sgp/sgp_calc.py`:

**Counting stats** (R, HR, RBI, SB, W, SV, SO):
```python
sgp = (player_stat - replacement_stat) / sgp_denominator
```

**Rate stats** (AVG, ERA, WHIP) — requires AB or IP for proportional weighting:
```python
# AVG
sgp = (player_avg - repl_avg) * (player_ab / team_ab) / sgp_denom

# ERA, WHIP (lower is better)
sgp = (repl_era - player_era) * (player_ip / team_ip) / sgp_denom
```

`team_ab` (6514) and `team_ip` (1226) are already in `SGPConfig`.

### Replacement Level

Use `compute_replacement_level()` from `sgp/replacement.py`. This estimates
replacement-level stats from historical standings averages.

### Dollar Value Conversion

Use `compute_dollar_values()` from `sgp/dollar_values.py`:
1. PAR = total_sgp - replacement_sgp
2. Only positive-PAR players get dollars
3. dollars_per_par = $3,600 / total_positive_par
4. Apply $1 minimum floor with redistribution

### Output Columns (added to projection DataFrame)

| Column | Description |
|--------|-------------|
| `sgp_R`, `sgp_HR`, ... `sgp_WHIP` | Per-category SGP |
| `total_sgp` | Sum of all category SGP |
| `par` | Points above replacement |
| `dollar_value` | Auction dollar value |

---

## Step 4: Pipeline Runner (`projections/run_pipeline.py`)

### CLI

```bash
# Full pipeline: fetch + transform + valuate
python3 -m projections.run_pipeline

# Force refresh from FanGraphs (bypass cache)
python3 -m projections.run_pipeline --force-refresh

# Use a specific projection system only
python3 -m projections.run_pipeline --system thebatx

# Specify season
python3 -m projections.run_pipeline --season 2026
```

### Pipeline Steps

1. **Fetch** THE BAT X (bat + pit), ATC (bat + pit), Depth Charts (bat + pit)
2. **Transform** each system into normalized DataFrames
3. **Fill** minor leaguers from Depth Charts into THE BAT X and ATC
4. **Valuate** ATC (primary) → `valuations_atc_2026.csv`
5. **Valuate** THE BAT X (cross-reference) → `valuations_thebatx_2026.csv`
6. **Combine** into side-by-side output with ATC dollars as authoritative →
   `valuations_combined_2026.csv`
6. **Print summary** to stdout:
   - Total dollar pool (should be ~$3,600)
   - Hitter/pitcher dollar split
   - Top 15 hitters by dollar value
   - Top 15 pitchers by dollar value

### Cross-Reference Output

ATC is the sole source for dollar values. THE BAT X is included for comparison:
- Match players across systems by `fg_id`
- `valuations_atc_2026.csv` is the primary output with dollar values
- `valuations_thebatx_2026.csv` is the cross-reference (no dollar values used)
- `valuations_combined_2026.csv` shows both systems' stats side-by-side
  with ATC dollar values as the authoritative column

---

## Step 5: Output Files

### `data/valuations_{system}_{season}.csv`

Full player-level output for each system:

```
player_name, team, pos_type, position, projection_system, fg_id, mlbam_id,
PA, AB, IP, R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO,
sgp_R, sgp_HR, sgp_RBI, sgp_SB, sgp_AVG, sgp_W, sgp_SV, sgp_ERA, sgp_WHIP, sgp_SO,
total_sgp, par, dollar_value
```

### `data/valuations_combined_{season}.csv`

Blended output with both systems' values:

```
player_name, team, pos_type, position, fg_id, mlbam_id,
dollar_value_thebatx, dollar_value_atc, dollar_value_combined,
R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO,
total_sgp, par, dollar_value
```

---

## Validation Checks

| Check | Expected | Red Flag |
|-------|----------|----------|
| Total dollar pool per system | $3,600 | Off by > $50 |
| Hitter/pitcher split | 58-67% hitters | Outside 50-75% |
| Top 5 hitters | AL stars (Judge, Soto, etc.) | Unknown names |
| Top 5 pitchers | AL aces + closers | Unknown names |
| Positive-value hitters | 120-170 | < 100 or > 200 |
| Positive-value pitchers | 80-130 | < 60 or > 150 |
| BAT X vs ATC correlation | r > 0.85 for dollar values | r < 0.70 |
| All 15 AL teams represented | 15 teams | Missing teams |

---

## Key Files to Modify/Use

| File | Action |
|------|--------|
| `projections/__init__.py` | Create |
| `projections/fetch.py` | Create |
| `projections/transform.py` | Create |
| `projections/valuate.py` | Create |
| `projections/run_pipeline.py` | Create |
| `sgp/sgp_calc.py` | Read — use `player_stat_to_sgp()` and `compute_sgp()` |
| `sgp/replacement.py` | Read — use `compute_replacement_level()` |
| `sgp/dollar_values.py` | Read — use `compute_dollar_values()` |
| `sgp/config.py` | Read — use `SGPConfig.composite()` |
| `sgp/data_prep.py` | Read — use `get_calibration_data()` |

---

## Dependencies

- `pybaseball` — installed (not used for projections directly, but available)
- `requests` — already installed (for FanGraphs API)
- `pandas`, `numpy` — already installed
- `sgp` module — existing, provides all valuation logic

No new dependencies needed.

---

## Resolved Questions

1. **Blending weights**: **ATC is the sole primary system.** ATC already
   incorporates THE BAT X as a component, so blending would double-count.
   THE BAT X is fetched for cross-reference only (included in output for
   comparison, not used in dollar value computation). Research confirms ATC
   has been #1 most accurate for 5+ consecutive years through optimal
   per-category weighting of its component systems.

2. **Ohtani-type players**: **Treated as separate rows.** Per league rules
   (the "Ohtani rule"), a two-way player is two distinct fantasy players —
   a hitter and a pitcher who can be on different teams. The pipeline
   naturally handles this since batting and pitching API responses return
   separate rows.

3. **Minimum PA/IP threshold**: **25 PA for hitters, 5 IP for pitchers.**
   Lower than initially proposed to capture more fringe/prospect value.

4. **Position eligibility**: **Included as informational.** Does not affect
   dollar values. Uses FanGraphs `minpos` field as a proxy for position.
   League rules: draft-day eligibility = 7 games at a position in the
   previous season. FanGraphs positions won't match exactly but provide
   useful draft-day reference.

---

## Future Steps

- **In-season updates**: Extend the pipeline to fetch rest-of-season projections
  (`rfangraphsdc`, rest-of-season Steamer/ZiPS) and re-run valuations during
  the season. Decide on update cadence and how to handle mid-season roster
  changes, trades, and keeper contract implications.
- **Custom projection models**: Replace ingested projections with proprietary
  Layer 1 rate stat models (per `getting-started.md` architecture).
- **Keeper/contract integration**: Overlay keeper salaries and contract years
  from `data/historical_rosters.csv` to compute surplus value (dollar_value -
  salary) for keeper decisions.

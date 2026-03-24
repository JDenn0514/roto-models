# Plan: Roster & Auction Data Scraper

## Status: COMPLETE

All scraping and infrastructure tasks are done. Downstream keeper identification
and additional validation remain as future work.

## Goal

Scrape historical roster data (players, salaries, contract years, positions) from OnRoto
for all available seasons (2015–2025). This data feeds the inflation model in Layer 4 and
provides replacement-level validation.

## Priority

**Build this BEFORE the SGP model.** The SGP model can run without it (using standings
data only), but the inflation layer, keeper surplus calculations, and replacement-level
validation all depend on this data. Scraping first avoids rework.

---

## Data Sources on OnRoto

All pages require authentication. Credentials are in `.env`:

```
ONROTO_USERNAME=pete@srjsteel.com
ONROTO_PASSWORD=ASUuoa12
ONROTO_LEAGUE=MoonGrahm
ONROTO_BASE_URL=https://onroto.fangraphs.com
```

### Authentication Flow — DONE

Shared auth module `onroto_auth.py` loads credentials from `.env` and provides
`login()` returning `(session, session_id)`. All three scrapers (standings, rosters,
transactions) import from it. `scrape_standings.py` was migrated to use it (hardcoded
credentials removed).

### Pages to Scrape — DONE

| Page | URL Pattern | Data |
|------|-------------|------|
| **Final Rosters** | `display_roster.pl?MoonGrahm+0+all+{YEAR}` | All teams' end-of-season rosters: player, position, MLB team, contract year, salary, status, eligibility |
| **Transactions** | `display_trans.pl?MoonGrahm+0+all+by_week+{YEAR}` | All in-season moves: date, team, player, MLB team, transaction type, timestamp |

Years scraped: 2015–2025.

---

## Output Data Schema

### `data/historical_rosters.csv` — DONE (3,983 rows)

One row per player-team-year:

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Season year |
| `team` | str | Fantasy team name |
| `player_name` | str | Player name (full name from link text, `#` prefix stripped) |
| `player_id` | str | OnRoto player ID (from the profile link URL, e.g., "7014") |
| `mlb_team` | str | MLB team abbreviation |
| `position` | str | Roster slot (1B, C, OF, P, UT, CI, MI, etc.) |
| `contract_year` | str | Contract designation (see Contract Codes below) |
| `salary` | int | Player salary in dollars |
| `status` | str | Status: act, dis, min, res |
| `eligibility` | str | Position eligibility (e.g., "1B,CI", "OF", "P") |

### `data/historical_transactions.csv` — DONE (31,362 rows)

One row per transaction:

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Season year |
| `eff_date` | str | Effective date (MM.DD format from OnRoto) |
| `team` | str | Fantasy team name |
| `player_name` | str | Player name (short form, e.g., "DFletcher") |
| `mlb_team` | str | MLB team abbreviation |
| `transaction` | str | Transaction type (see list below) |
| `submitted` | str | Submission timestamp |

Known transaction types: Acquire, Acquire on Reserve, Activate, Add to Actives,
Add to Reserves, Change Contract to {x}, Change Position to {x}, Change Salary to {x},
Claim, Disable, Move to Minors, Release, Reserve, Trade, Waive.

---

## Contract Codes — RESOLVED

### Standard contract progression
- `a` = 1st year, `b` = 2nd year, `c` = 3rd/final year (standard 3-year max contract)
- Extension bumps add years: `a` → `b` → `x` → `y` → `z`
  - `x` = 3 years remaining (player was extended/bumped for 2 additional years)
  - `y` = 2 years remaining
  - `z` = last year (equivalent to `c` for extended contracts)
- Suffix `r` = rookie contract (e.g., `ar`, `br`, `cr`)

### Non-keeper / in-season codes (exclude from opening-day roster)
- **September call-ups** (`s`, `SE`, `SEPT`, `aSEP`, `aSEPT`, `arSEP`, `ySEP`, `crS`):
  Roster expansion adds after Sept 1. Costs $25 but no salary cap impact. NOT kept.
- **Mid-season pickups** (`a-faab`, `aF`, `af`): Free agent acquisitions during the season.
- **AL trade deadline pickups** (`L`, `LT`, `bL`, `aL`, `aX`): Players traded into the AL
  at the deadline. Picked up at listed salary; if thrown back, cost double.

### Rare/edge cases
- `zz` (4 in 2020, all $1) — likely expired/end-of-line contracts
- `R` (1 occurrence) — capitalization variant of `r` (rookie)
- `Z` (1 occurrence) — capitalization variant of `z`

---

## HTML Parsing Details

### Final Rosters Page Structure — DONE

The page at `display_roster.pl?MoonGrahm+0+all+{YEAR}` contains ALL teams' rosters in
sequence. The actual structure (confirmed by inspection):

1. **Team header**: `<p class="team_NNNN">` containing `<b>` with team name, followed
   by ", owned by ..." text.

2. **Active table**: `<table class="Active_table_N">` with columns:
   - `Pos` | `Active Players` | `Team` | `Con` | `Sal` | `Stat` | `Elig` | `Games Played By Position`
   - Sub-columns under Games: DH, C, 1B, 2B, 3B, SS, OF
   - Player rows have 14 `<td>` cells (7 data + 7 games-by-position)

3. **Reserved table**: `<table class="Reserved_table_N">` with identical structure
   (header says "Reserved Players" instead of "Active Players").

4. **Salary summary**: Injected via `<script>` block using jQuery `.before()`:
   `"Total Active Player Salary: $XXX; Total Team Salary: $YYY"`

5. The player name cell contains an `<a>` link to the player profile:
   ```
   display_player_profile.pl?MoonGrahm+0+7014&session_id=...
   ```
   The `7014` is the OnRoto player ID — extracted via regex `r'\+(\d+)&'`.

6. The `#` prefix on player names appears for certain players. Stripped in parsing.

7. Reserved player names may include annotations like `(Off DL )` or `(Non Elig Pos)`
   outside the `<a>` tag — parser uses link text only to avoid these.

### Transactions Page Structure — DONE

The page at `display_trans.pl?MoonGrahm+0+all+by_week+{YEAR}` contains one table per
week, in reverse chronological order. Each table has:

- Row 0: Single cell "Weekly Transactions"
- Row 1: Header row with 6 `<td class="white_on_grey12">` cells: Eff. Date, League Team,
  Player, Tm, Transaction, Submitted
- Row 2+: Data rows with 6 `<td>` cells

Transaction tables are identified by finding `<td class="white_on_grey12">` containing
"Eff. Date". Header rows are skipped by checking for the `white_on_grey12` class.

Pages are large (~700KB for a full season like 2022).

---

## Implementation — DONE

### File: `onroto_auth.py` — DONE

Shared authentication module. Loads credentials from `.env` via `python-dotenv`.
Exports `login()`, `BASE_URL`, `LEAGUE`.

### File: `scrape_standings.py` — MIGRATED

Updated to import from `onroto_auth` instead of hardcoding credentials.

### File: `scrape_rosters.py` — DONE

Parses team blocks via `<p class="team_NNNN">` tags, navigates siblings to find
Active/Reserved tables, extracts player data including IDs from profile links.
Validates team counts per year.

### File: `scrape_transactions.py` — DONE

Identifies transaction tables by `white_on_grey12` class headers, skips non-data rows,
extracts all 6 fields. Prints per-year summary.

---

## Derived Data: Keeper Identification — NOT YET BUILT

This is NOT part of the scraper — it's a downstream analysis step in the SGP model. But
document the logic here since it drives the inflation calculation.

### Logic to Identify Keepers vs. Drafted Players

A player was **kept** (not drafted) if:
- Their contract year is `b` or `c` (2nd or 3rd year of contract)
- OR they appear on the roster at the start of the season with contract year `a` BUT
  also appeared on the PREVIOUS year's end-of-season roster for the SAME team

A player was **drafted** if:
- Contract year `a` AND they did NOT appear on the previous year's roster for that team

**Complication**: The rosters we scrape are END-of-season rosters, not opening-day rosters.
Mid-season acquisitions (free agents, trades) will appear on the final roster but were NOT
part of the auction. To isolate auction-day rosters:

- Cross-reference with transactions: players with "Add to Actives" or "Acquire"
  transactions during the season were NOT on the opening-day roster
- Players with "Trade" transactions changed teams mid-season
- The cleanest approach: for each year, take the final roster and SUBTRACT all players
  who appear in that year's transaction log as incoming (Add to Actives, Acquire, Claim,
  Trade-in). The remainder is approximately the opening-day roster.

**Alternative approach**: Look at the earliest transaction date for each year. Players on
the roster who have NO transactions are likely opening-day players. This is simpler but
less precise.

### Resolved Questions

1. **FARM/RES players and keeper identification:** Per league rules, FARM salaries do NOT
   count against the salary cap, but RES salaries DO. For inflation modeling, count RES
   keepers but exclude FARM players from the kept-salary pool.

2. **Contract codes:** RESOLVED — see Contract Codes section above. September, mid-season,
   and trade deadline codes are now classified and will be excluded from opening-day rosters.

3. **Opening-day roster reconstruction:** Will use transaction subtraction approach (take
   end-of-season roster, subtract incoming transactions). No additional scraping needed.

---

## Validation Results (2025-03-23)

### Team Counts Per Year

| Year | Teams | Players | Notes |
|------|-------|---------|-------|
| 2015 | 10 | 311 | |
| 2016 | 11 | 344 | |
| 2017 | 11 | 344 | |
| 2018 | 11 | 343 | |
| 2019 | 11 | 379 | |
| 2020 | 11 | 378 | COVID season |
| 2021 | 11 | 416 | |
| 2022 | 11 | 384 | |
| 2023 | 10 | 349 | |
| 2024 | 10 | 368 | |
| 2025 | 10 | 367 | Pre-draft/partial |

Note: 2016–2022 all have 11 teams (original plan assumed only 2016–2017).

### Team Name Consistency

Team names in `historical_rosters.csv` match `historical_standings.csv` exactly
for all overlapping years — no normalization mapping needed.

### Transaction Counts Per Year

| Year | Transactions |
|------|-------------|
| 2015 | 1,648 |
| 2016 | 1,950 |
| 2017 | 2,962 |
| 2018 | 2,910 |
| 2019 | 2,768 |
| 2020 | 1,522 |
| 2021 | 3,174 |
| 2022 | 4,522 |
| 2023 | 3,158 |
| 2024 | 2,984 |
| 2025 | 3,764 |

2020 is lower as expected (COVID). Total: 31,362 transactions.

### Remaining Validation

- [x] Team counts per year — DONE
- [x] Team name consistency — DONE
- [x] Transaction counts per year — DONE
- [x] Contract continuity checks — DONE (2026-03-23)
- Salary sum validation and player count outlier flagging deferred (low priority)

### Contract Continuity Results (2026-03-23)

Checked 1,284 contract progression codes (b, c, x, y, z and rookie variants):

| Category | Count | % |
|----------|-------|---|
| Valid standard progression | 817 | 63.6% |
| Valid 2021 freeze (same code) | 61 | 4.8% |
| Valid 2022 double-advance | 91 | 7.1% |
| Not checkable (first year of data) | 216 | 16.8% |
| Anomalous (commissioner adjustments) | 99 | 7.7% |

**Key finding: 2021 contract freeze.** The league froze all contracts in 2021 (COVID
compensation) — 202 players had identical codes in 2020 and 2021, with 0 normal advances.
In 2022, contracts double-advanced to catch up (e.g., `a→c` skipping `b`).

Additional confirmed progressions:
- `r` = `ar` (standalone rookie = first-year rookie)
- `b→y` is a valid extension path (especially pre-2018 before `x` was introduced)
- `c→y` and `cr→y` are valid late extensions from the final year

The 99 anomalies (7.7%) are concentrated in 2022-2023 and are accepted as commissioner
adjustments from the COVID-era disruption. No parsing errors detected.

---

## Dependencies — DONE

```
requests
beautifulsoup4
lxml
pandas
python-dotenv
```

## File Structure — DONE

```
onroto_auth.py             # Shared auth module (loads .env)
scrape_standings.py        # Standings scraper (migrated to shared auth)
scrape_rosters.py          # Roster scraper
scrape_transactions.py     # Transaction scraper
data/historical_standings.csv
data/historical_rosters.csv
data/historical_transactions.csv
```

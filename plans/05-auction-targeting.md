# Plan 05: Auction Targeting Tool

## Overview

**What:** A real-time auction targeting tool for the Moonlight Graham league's annual
draft. It combines player valuations with live auction state to produce a continuously
updated targeting score and bid ceiling for every available player.

**Goal:** Help make better in-auction decisions by answering two questions per player
in real time:
- *How hard should I target this player?* → Targeting Score (TS)
- *What's the most I should pay?* → Bid Ceiling

**Scope:** This covers the targeting metric design, the real-time auction UI, and the
validation strategy. Custom projection models (Layers 1–3 of the main pipeline) are
out of scope.

---

## Research Report

### Problem

Standard SGP dollar values assume a generic team drafting from scratch. But in a keeper
league auction, you are not a generic team. Your actual value of a player depends on:
1. Your current roster composition (what categories you're already strong/weak in)
2. How many comparable players are still available (scarcity)
3. Whether the market is correctly pricing the player

A player who adds 15 SB is worth more to a team ranked 9th in steals than to a team
already ranked 2nd. The existing valuation pipeline has no mechanism to capture this.

### Key Insights from Brainstorming

**Categories are the unit of value.** The right way to think about player value is not
"how many SGP does this player produce?" but "how many standings points does this player
add to my team specifically?" These are different questions with different answers
depending on where you currently rank in each category.

**Scarcity is opportunity cost.** A player is scarce not because few players exist at
their position, but because the gap between their value and the next comparable option
is large. Scarcity = `player_value - E[best_alternative | passing on this player]`.

**Market inefficiency is a gate, not a weight.** You shouldn't target a player just
because they're undervalued if they don't fill a need. And you shouldn't skip a player
just because they're overvalued if the fit and scarcity premiums justify paying more than
market. MI acts as a signal that adjusts your ceiling, not as an additive component of
equal weight.

### Validation Strategy

Proper backtesting requires auction order data (who was available when, at what price).
This data doesn't exist for the Moonlight Graham league historically, and using public
league data (NFBC, LABR, TOUT Wars) is not advisable due to structural differences
(different team counts, mixed vs. AL-only, different categories, different budget scales)
that would introduce more noise than they remove.

**Decision:** Use tonight's auction as the first live test (Angle 4). Record every
nomination, price, and winner in order. Post-season, use final standings + this recorded
data to calibrate the model weights.

---

## Metric Design

### Three Components

#### Component 1: Personal Value Premium (PVP)

> "What is this player worth to *my* team specifically?"

The core computation: simulate adding the player to my current roster, re-rank all 10
teams in each of the 10 categories, and measure the change in my expected standings
points.

**Steps:**
1. Load keeper rosters for all 10 teams
2. For each team, estimate projected full-season category totals:
   - Keeper stats come from their matched projections
   - Unfilled spots are filled at the league-average per-slot rate (discounted)
3. Rank all 10 teams in each category → current standings point matrix
4. For player P: add their projected stats to my team → re-rank → recount my standings points
5. `MSPA(P)` = new standings points − baseline standings points  (Marginal Standings Points Added)
6. Convert to dollars: `PVP = MSPA × dollars_per_standings_point`
   - Approximate conversion: `$3600 total pool / ~550 total standings points ≈ $6.55/pt`

PVP recalculates every time I win a player (my roster changes) or another team wins a
player (the standings matrix shifts).

#### Component 2: Scarcity Premium (SP)

> "If I pass, can I get something comparable later?"

**Step 1 — Classify each player into a (tier, profile) bucket**

Dollar tiers (based on production value):

| Tier    | Range    |
|---------|----------|
| Elite   | $25+     |
| Premium | $15–$24  |
| Solid   | $8–$14   |
| Filler  | $4–$7    |
| Min     | $1–$3    |

Category profiles:

*Hitters* — determined by which SGP categories dominate the player's contribution:
- **Power**: HR or RBI is primary contributor (combined share > 50%)
- **Speed**: SB is primary contributor (share > 35%)
- **Average**: AVG is primary contributor (share > 30%)
- **Balanced**: no single category dominates

*Pitchers*:
- **Closer**: projected SV ≥ 10
- **Starter**: SP, no significant save contribution
- **Bulk Reliever**: RP, no significant SV, ERA/WHIP value only

**Step 2 — Count comparable players**

Two players are comparable if they share the same tier AND the same profile.

`comparable_count(P)` = number of remaining available players in `(tier(P), profile(P))`
excluding P itself.

**Step 3 — Compute SP**

```
SP(P) = max(0, dollar_value(P) − mean_top3_comparable_value)
```

Where `mean_top3_comparable_value` is the average dollar value of the top 3 remaining
comparable players. When comparable_count = 0, fall back to the next tier down's best
available players as the reference.

SP → 0 when many comparables exist. SP > 0 when this player is the last or one of few
in their quality+role bucket.

SP recalculates every time any player is taken.

#### Component 3: Market Inefficiency (MI)

> "Is the market mispricing this player?"

```
MI = production_value − auction_value
```

Where:
- `production_value` = single-pool SGP dollar value (what the player is actually worth)
- `auction_value` = split-pool SGP dollar value (calibrated to typical auction market)

MI is positive when the player is undervalued by the market, negative when overvalued.

**Role in the framework:** MI acts as a gate on the bid ceiling. Significant market
overvaluation compresses how much of your PVP+SP premium you should actually pay.

---

### Composite Targeting Score (TS)

```
TS = PVP + SP + MI_adjustment

where:
  MI_adjustment =  0         if MI >= −$3   (market roughly fair or underprices)
               = (MI + 3)   if −$8 < MI < −$3  (partial penalty)
               = −$5 cap    if MI <= −$8   (significant overvaluation; walk away)
```

TS is the primary sorting key for the targeting table. Higher TS = target harder.

Both the composite TS and each individual component (PVP, SP, MI) are displayed.

---

### Bid Ceiling

```
Bid_Ceiling = auction_value + max(0, PVP) + max(0, SP)
Bid_Ceiling = min(Bid_Ceiling, budget_cap)

budget_cap = remaining_budget − (remaining_unfilled_spots − 1) × $1
```

Interpretation: *Never pay more than this. The floor is market price; bonuses are what
you should pay extra for roster fit and scarcity.*

---

## Real-Time Updates

As the auction progresses, the following recalculate automatically:

| Event | What recalculates |
|---|---|
| Any player taken | SP for all remaining players |
| I win a player | PVP for all remaining players (my roster changed) |
| Another team wins a player | Standings matrix shifts → PVP for all remaining players |
| My budget changes | Bid ceiling cap for all remaining players |

---

## Team Competition Model

For the standings projection (used in PVP calculation), other teams' unfilled spots are
filled using historical league-average per-slot production, discounted to account for
the fact that auction teams don't draft at theoretical maximum.

During the auction, as each team wins a player, their roster updates and the standings
matrix is recomputed. A competition flag is shown when another team appears weak in the
same category and few players remain who address that category — indicating they'll likely
bid aggressively.

---

## UI Design

**Technology:** Streamlit 1.55. Python-native, no new language, reactive state, runs
locally in a browser tab via `streamlit run auction/app.py`.

**Style reference:** `reports/valuations.html` — same color palette, fonts, and spacing.
- Fonts: Source Serif 4 (display/titles), DM Sans (body), JetBrains Mono (numbers/labels)
- Colors: `#faf9f5` background, `#3A6EA5` primary blue, `#C1666B` secondary red/coral,
  `#2A9D8F` accent teal, `#2d2d2d` text, dark table headers
- Note: Streamlit 1.55 requires `st.html()` for raw HTML injection; `st.markdown(unsafe_allow_html=True)` no longer works for actual DOM injection. CSS goes in `st.html("<style>…</style>")` blocks which are special-cased to the event container.

**Relationship to existing HTML:** `valuations.html` is a static research reference.
The Streamlit app is the live auction tool. They are separate.

### Layout — Option B: Command Bar

```
┌────────────────────────────────────────────────────────────────────┐
│  LOG AUCTION RESULT                                                 │  ← always at top
│  [Player ▼──────────────] [$__] [Team ▼──────────] [  Log ✓  ]    │
│  Recent: #3 Altuve→R&R $42 · #2 Judge→Shrooms $55                 │  ← live ticker
├─────────────────────┬──────────────────────────────────────────────┤
│ 30%: Left column    │  70%: Right column                           │
│                     │                                              │
│ BUDGET & SPOTS      │  [All positions… ▼] [Solid & above ▼] [🔍]  │
│ $272  $257          │                                              │
│ 6H    9P            │  Available Free Agents (71)                  │
│                     │  Player  Pos  Tier  Prod$  Auc$  MI  PVP … │
│ MY LINEUP           │                                              │
│  ┌ HITTERS ───────┐ │  (table sorted by TS, scrollable)           │
│  │ C  Edgar Quero  │ │                                              │
│  │ C  Ben Rice     │ │                                              │
│  │ 1B M. Vargas   │ │                                              │
│  │ 2B J. Holliday │ │                                              │
│  │ 3B —           │ │                                              │
│  │ SS —           │ │                                              │
│  │ CI T.Soderstrom│ │                                              │
│  │ MI L. Keaschall│ │                                              │
│  │ OF E. Carter   │ │                                              │
│  │ OF R. Anthony  │ │                                              │
│  │ OF —           │ │                                              │
│  │ OF —           │ │                                              │
│  │ OF —           │ │                                              │
│  │ UT J. Cag.     │ │                                              │
│  │ UT —           │ │                                              │
│  ├ PITCHERS ──────┤ │                                              │
│  │ P  M. Brash    │ │                                              │
│  │ P  G. Whitlock │ │                                              │
│  │ P  — ×9        │ │                                              │
│  ├ FARM / RESERVE ┤ │                                              │
│  │ C  Liranzo     │ │                                              │
│  │ OF E. Rodriguez│ │                                              │
│  │ P  Yamashita   │ │                                              │
│  │ SS S. Walcott  │ │                                              │
│  └────────────────┘ │                                              │
│                     │                                              │
│ CATEGORY RANKS      │                                              │
│  R  ████████ 8      │                                              │
│  HR ████████ 8      │                                              │
│  …                  │                                              │
│  W  █ 1 (red)       │                                              │
│  SO █ 1 (red)       │                                              │
│                     │                                              │
│ ▼ Full Auction Log  │                                              │
└─────────────────────┴──────────────────────────────────────────────┘
```

### Nomination Bar (top of page)

Always visible without scrolling. Uses `st.form()` so submission doesn't
prematurely re-render on every widget interaction.

- **Player** selectbox: all non-keeper, non-taken free agents (alphabetical)
- **Price** number_input: $1–$75
- **Winning team** selectbox: all 10 teams
- **Log ✓** submit button (blue, full-width in its column)
- **Live ticker** beneath the form: last 5 results as chip badges. Mine highlighted in blue.

### Left Column (30%)

**Budget & Spots** — four cards in a 2×2 grid:
- Budget Left, Effective Budget (= Budget Left − remaining open spots), H Spots, P Spots

**My Lineup** — HTML table card with dark section headers (matching valuations.html style):
- **HITTERS** section: 15 position slots in order (C, C, 1B, 2B, 3B, SS, CI, MI, OF×5, UT×2)
- **PITCHERS** section: 11 P slots
- **FARM / RESERVE** section (lighter header): farm/min-status keepers listed separately —
  they do NOT occupy active roster slots

Slot display per row: `[slot label] [player name + badge] [salary]`
- Active keepers: no badge
- Auction wins: green `new` badge
- Farm players (in reserve section only): gray `farm` badge
- Empty active slots: `—`

**Auto-placement logic** (for auction wins): `try_place_player()` uses a two-pass greedy algorithm:
1. Find first empty eligible slot, most-specific first (e.g., C before UT)
2. If no empty eligible slot, try displacing an occupant to another eligible slot so both fit
   (one level of displacement only — no recursion)
- Farm/min-status keepers are pre-loaded to the reserve section, never active slots

**Slot eligibility rules:**

| Slot | Eligible positions |
|------|-------------------|
| C    | C |
| 1B   | 1B |
| 2B   | 2B |
| 3B   | 3B |
| SS   | SS |
| CI   | 1B, 3B, CI |
| MI   | 2B, SS, MI |
| OF   | OF, DH |
| UT   | any hitter |
| P    | SP, RP, P |

**Category Ranks** — 2-column grid of all 10 categories with:
- Progress bar fill (colored by rank)
- Numeric rank (1–10)
- Color: green ≥ 7, orange 4–6, red ≤ 3

**Full Auction Log** — `st.expander()` (collapsed by default). Contains full DataFrame
+ CSV download button.

### Right Column (70%)

**Filter row** — three controls in a single row, all `label_visibility="collapsed"`
so they align at exactly the same height:

1. **Position multiselect** — options: `C, 1B, 2B, 3B, SS, OF, SP, RP`
   - Empty selection = show all positions (no filter applied)
   - Non-empty = show only players whose canonical position set overlaps the selection
   - Compound positions handled via `player_matches_positions()`:
     - `DH/OF` → `OF`; `2B/SS` → both `2B` and `SS`; `CI` → `1B` and `3B`; etc.

2. **Tier threshold selectbox** — single dropdown (not multiselect pills):
   - "All tiers"
   - "Elite only"
   - "Premium & above" (Elite + Premium)
   - "Solid & above" ← **default**
   - "Filler & above"
   - "Min & above"

3. **Player name search** — text input with 🔍 placeholder, case-insensitive substring match

**Player table** — sorted by TS descending, `height=660px`, `use_container_width=True`:

| Column | Description |
|--------|-------------|
| Player | Name |
| Pos    | Position string from MSP data (e.g. "2B/SS") |
| Tier   | Elite / Premium / Solid / Filler / Min / Sub |
| Prod $ | Single-pool SGP dollar value |
| Auc $  | Split-pool market price |
| MI     | Market Inefficiency = Prod$ − Auc$ |
| PVP    | Personal Value Premium = MSP × $6.55/pt |
| SP     | Scarcity Premium |
| TS     | Targeting Score = PVP + SP + MI_adjustment |
| Bid $  | Bid Ceiling = Auc$ + max(0,PVP) + max(0,SP), capped at budget |

Note: Profile column removed from table (redundant given position filter). Add back
if requested.

**Free agent pool:** Keepers from all 10 teams are excluded at data load time.
Pre-computed MSP data (`data/msp_gusteroids_atc_2026.csv`) includes ~12 players who
are keepers; these are filtered out in `load_players()`. ~580 free agents remain.

---

## Module Architecture

The original plan called for a modular `auction/` package. In practice, everything
was built into a single well-organized `auction/app.py` for speed. Refactoring into
submodules is future work if needed.

```
auction/
  __init__.py    — empty package init
  app.py         — entire application: data loading, scoring, state, UI, HTML builders
```

**Key sections within `app.py`:**

| Section | Contents |
|---------|----------|
| Constants | Tiers, categories, lineup slot definitions, slot rules, position filter options, tier threshold mapping |
| CSS | `inject_css()` — Google Fonts @import + full valuations.html-style stylesheet via `st.html()` |
| Data loading | `load_players()`, `load_keepers()`, `load_standings()` — all `@st.cache_data` |
| Classification | `_get_tier()`, `_classify_profiles()` |
| Eligibility & placement | `parse_eligibility()`, `is_eligible_for_slot()`, `try_place_player()`, `build_initial_roster()` |
| Position filter | `player_matches_positions()` — canonical position mapping for filter |
| Session state | `init_state()` — initializes `roster_slots`, `farm_players`, budget state |
| Scoring | `compute_scarcity()`, `compute_mi_adjustment()`, `score_players()` |
| Log | `_log_result()` — updates state + triggers auto-placement on wins |
| HTML builders | `_budget_html()`, `_lineup_section_html()`, `_lineup_html()`, `_cat_ranks_html()`, `_ticker_html()` |
| Render | `render_nomination_bar()`, `render_left_column()`, `render_right_column()` |
| Main | `main()` — page config, data load, budget calc, scoring, layout |

---

## Session State

| Key | Type | Description |
|-----|------|-------------|
| `taken` | dict | `player_name → {team, price, nom_order}` |
| `auction_log` | list | `[{nom, player, winner, price, timestamp}]` |
| `nom_counter` | int | Nomination number (increments on each log) |
| `budget_spent` | int | Total spent at auction (mine only) |
| `hitters_won` | int | Hitters I've won at auction |
| `pitchers_won` | int | Pitchers I've won at auction |
| `salary_committed` | int | Keeper salary total |
| `act_hitters` | int | Active keeper hitters (status act/dis) |
| `act_pitchers` | int | Active keeper pitchers (status act/dis) |
| `roster_slots` | list | 26-slot list (15H + 11P). Mutated by `try_place_player()` |
| `farm_players` | list | Reserve/farm keepers (status min). Displayed separately |

---

## Data Dependencies

| File | Used For |
|------|----------|
| `data/msp_gusteroids_atc_2026.csv` | Pre-computed MSP + category SGP breakdown for all ~604 players |
| `data/valuations_atc_2026.csv` | `auction_value` (split-pool) + `total_sgp` for split pool calculation |
| `data/preauction_rosters_2026.csv` | All teams' keepers — for keeper exclusion, budget, lineup init |
| `data/msp_projected_standings_2026.csv` | Projected category ranks (category rank bars) |
| `sgp/` modules | `SGPConfig`, `compute_sgp`, `compute_replacement_level`, `compute_split_pool_values` |

**Note on `auction_value`:** Split-pool value is not saved in any CSV. Computed at
startup via `compute_split_pool_values()` from `sgp/dollar_values.py`, cached via
`@st.cache_data`. Takes ~5–10 seconds on first load; instant thereafter.

---

## What This Plan Does Not Cover

- Custom projection models (Layers 1–3) — use third-party projections (ATC)
- Integration with OnRoto's live auction feed — manual input only
- Post-season backtesting — deferred until tonight's auction log is collected
- Multi-team targeting (computing TS for teams other than Gusteroids)
- PVP mid-auction recalculation — currently uses pre-computed MSP. Full implementation
  would re-run the MSP model live as rosters change (deferred)

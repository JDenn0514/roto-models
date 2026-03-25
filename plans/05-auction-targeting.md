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

**Technology:** Streamlit. Python-native, no new language, reactive state, runs locally
in a browser tab.

**Relationship to existing HTML:** The existing `valuations.html` is a static research
reference. The Streamlit app is the live auction tool. They serve different purposes.

### Layout

**Sidebar — My Team Status**
- Keepers list with salaries
- Budget: committed / spent at auction / remaining / effective (after reserving minimums)
- Roster spots: hitters and pitchers remaining
- Category rank bars: current projected rank 1–10 for each of the 10 categories,
  color-coded (green ≥ 7, yellow 4–6, red ≤ 3)

**Main Area — Targeting Table**

Sorted by TS (descending) by default. Columns:

| Player | Pos | Profile | Tier | Prod $ | Auction $ | MI | PVP | SP | TS | Bid Ceil |

Filters: position type, tier, profile, text search.

Each row is clickable to expand per-category MSP breakdown and competition notes.

**Nomination Form**
Collapsible form above the log:
- Select player (dropdown or search)
- Enter final price
- Select winning team (dropdown of all 10 teams, or "Me")
- Submit → updates all state and rerenders

**Auction Log**
Running ordered list of all transactions: nomination #, player, winner, price, timestamp.
Export to CSV button.

---

## Module Architecture

```
auction/
  __init__.py
  config.py       — tier breakpoints, profile thresholds, dollars-per-point constant
  state.py        — AuctionState: roster tracking, budget, taken players
  scarcity.py     — classify_profile(), compute_scarcity_premium()
  targeting.py    — compute_pvp(), compute_ts(), compute_bid_ceiling(), score_all_players()
  team_model.py   — TeamModel: project all teams' stats, compute standings matrix
  app.py          — Streamlit UI
```

### Build Order

1. `state.py` — foundation; everything else depends on it
2. `scarcity.py` — independent of PVP; can build and test first
3. `targeting.py` — PVP simplified first (historical averages), full standings model second
4. `team_model.py` — graduated complexity: start with historical averages, refine
5. `app.py` — built incrementally alongside the above

**If time is short before tonight:** Ship with simplified PVP (category rank vs. league
average rather than full 10-team matrix). Scarcity and MI are independent and can be
complete first. Bid ceiling still works with simplified PVP.

---

## Data Dependencies

| File | Used For |
|---|---|
| `data/valuations_atc_2026.csv` | `production_value`, projected stats, `auction_value` (computed on demand) |
| `data/preauction_rosters_2026.csv` | All teams' keepers, salaries, budget calculation |
| `data/msp_projected_standings_2026.csv` | Projected category ranks (for sidebar display) |
| `sgp/config.py` | SGP denominators, league constants |
| `data/historical_standings.csv` | League-average per-slot production (fill rates) |

**Note on `auction_value`:** The split-pool value is not saved in any CSV. It is
computed on demand by calling `compute_split_pool_values()` from `sgp/dollar_values.py`
with the historical hitter/pitcher spending split. This computation is fast (<5s) and
should be cached at app startup.

---

## What This Plan Does Not Cover

- Custom projection models (Layers 1–3) — use third-party projections
- Integration with OnRoto's live auction feed — manual input only
- Post-season backtesting — deferred until auction log data is collected tonight
- Multi-team targeting (computing TS for teams other than Gusteroids)

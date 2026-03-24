# Rotisserie Baseball Model: Design Decisions

## League Context

- **Format:** 10-team American League only rotisserie
- **Scoring:** Points distributed linearly across categories — 10 points for 1st place, 1 point for last, with teams ranked in between
- **Batting categories (5):** HRs, RBIs, AVG, SBs, Runs
- **Pitching categories (5):** Ks, Ws, ERA, WHIP, SVs
- **Keeper/contract league:** Players kept at their auction price for up to 3 years; extension options available (+$5 for 1 additional year, +$10 for 2 additional years)
- **Salary caps:** $350 active roster, $500 full roster
- **Roster structure:**
  - 15 hitters with specific positional slot requirements
  - 11 pitchers (any SP/RP combination)
  - Reserve slots: DL, FARM, RES
- **Waiver wire:** Blind bidding

---

## Model Architecture

The model is a 4-layer pipeline that converts raw player data into auction dollar values.

### Layer 1: Projected Rate Stats

Predict rate stats per plate appearance for each player:

- HR/PA
- RBI/PA
- R/PA
- SB/PA
- AVG

Each category gets its own model, trained on historical data and advanced metrics (Statcast, etc.). An **improvement/breakout model** sits on top of this layer and adjusts projected rate stats for players likely to improve — these adjustments cascade automatically through the rest of the pipeline.

### Layer 2: Projected Playing Time

Model projected plate appearances using:

- Injury history and risk
- Roster competition
- Contract status
- Age

**Two-pass approach:**

1. **Pass 1** — Estimate PT using only non-performance inputs (injury, competition, contract, age)
2. **Pass 2** — Apply a skill-tier nudge that adjusts PT up or down for fringe players based on their projected rate stats from Layer 1

The rationale: established starters' PT is mostly determined by non-performance factors. Fringe players' PT is more sensitive to how well they're actually performing. The two-pass design captures this feedback loop without full simultaneity.

### Layer 3: Counting Stat Projection

Multiply rate stats (Layer 1) by adjusted plate appearances (Layer 2) to produce full projected stat lines:

- HRs, RBIs, Runs, SBs, AVG

Using a shared playing time assumption keeps all five statistics internally consistent.

### Layer 4: SGP → PAR → Dollar Value

1. **Standings Gain Points (SGP):** Convert projected stats into standings impact, calibrated to this league's historical standings data — not generic internet baselines. This is a key competitive edge.
2. **Points Above Replacement (PAR):** Subtract replacement-level SGP to isolate value above freely available talent.
3. **Dollar Value:** Convert PAR to fair-market auction value using total available auction money across the league.

PAR and dollar value are two sides of the same coin: PAR for comparing players head-to-head, dollar value for auction decisions and contract evaluation (is a player's salary above or below market rate?).

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Individual model per rate stat category | Different stats have different predictive drivers (exit velocity/launch angle for HRs, contact rate/BABIP for AVG, sprint speed for SBs, etc.) |
| Rate-first, then scale by PT | Rate stats are more stable year-over-year than counting stats; separates skill from opportunity |
| Two-pass playing time model | Captures the performance → PT feedback loop for fringe players without introducing simultaneity problems |
| SGP calibrated to league history | Generic SGP baselines reflect average leagues; this league's historical data makes the model specific and more accurate |
| Improvement model feeds into Layer 1 | Adjustments to rate stats cascade through PT, counting stats, and dollar value automatically |
| PAR and dollar value as dual outputs | Serves two distinct use cases: player comparison and auction/contract decisions |

---

## Open Questions

- Define "significant improvement" for the breakout/improvement model
- Scope of improvement model: breakout candidates only, bounce-back candidates, or both?
- Does the improvement model feed directly into the value model, or remain a separate adjustment layer?
- Data sources: Statcast, FanGraphs, historical league data — format and ingestion approach TBD
- Validation strategy for the prediction models

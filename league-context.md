# Moonlight Graham League Rules

## League Overview

- **League name:** Moonlight Graham
- **Platform:** OnRoto (onroto.fangraphs.com)
- **Teams:** 10 (has varied 10–11 historically)
- **Player pool:** American League only — all 15 AL teams (Bal, Bos, Cle, CWS, Det, Hou, KC, LAA, Min, NYY, Oak, Sea, TB, Tex, Tor)
- **Format:** Rotisserie, YTD cumulative stats, no head-to-head, no divisions
- **Season:** Opening Day (March 25) through September 27
- **Keeper/contract league:** Yes (details in Contract & Salary section)
- **Draft date:** March 25, 7:00 PM ET (online draft room)

### Player Pool Rules

- Players traded to the NL: **future stats still count**
- NL players cannot be stashed on reserve lists
- Each player can only be on one team (no shared ownership)
- **Ohtani rule:** Treated as two completely distinct players (hitter and pitcher), can be on different teams, can both be active simultaneously (occupying one hitter slot + one pitcher slot). Counts as one roster slot unless both halves are active.

---

## Scoring System

> **This section is critical for SGP calibration.**

### Scoring Method

Rotisserie-style category rankings using YTD stats. Teams are ranked 1st through last in each category:
- **1st place** in a category = **N points** (where N = number of teams, typically 10)
- **Last place** = **1 point**
- Ties split the points (e.g., two teams tied for 3rd each get 3.5 points)
- **Total standings points** = sum across all categories

### Scoring Categories (10 total, since 2019)

| Type | Categories | Count |
|------|-----------|-------|
| Batting | R, HR, RBI, SB, AVG | 5 |
| Pitching | W, SV, ERA, WHIP, SO | 5 |

- **Historical change:** 2015–2018 used only **8 categories** (no R or SO)
- Display-only (non-scoring) stats: G, AB (hitters); G, IP (pitchers)

### Minimum Thresholds

| Threshold | Value | Consequence |
|-----------|-------|-------------|
| **Minimum IP** | **900 IP** | Teams below 900 IP score **0 points** in ERA and WHIP; other teams' rankings are unaffected |
| Minimum AB | None enforced | — |
| Maximum IP | None enforced | — |
| Maximum pitcher GS | None enforced | — |

> **SGP note:** The 900 IP minimum means teams cannot "punt pitching" on rate stats without severe penalty. This affects how SGP denominators should be calculated — teams scoring 0 in ERA/WHIP due to the IP floor should likely be excluded from SGP regression for those categories.

### Special Scoring Rules

- No cap on saves relative to wins (some leagues limit SV ≤ W)
- No cap on RBI relative to runs (some leagues limit RBI ≤ R)
- RP eligibility: A pitcher loses RP eligibility after **1 game started** (max GS threshold = 1)
- No extra decimal precision on ERA, WHIP, AVG

---

## Roster Structure

> **Roster rules affect replacement-level calculations for the SGP→PAR conversion.**

### Active Lineup

- **23–26 players** (23 minimum, 26 maximum)
- Exactly **15 hitters** and exactly **11 pitchers**
- **Salary cap:** $350 for active lineup

#### Hitter Positions (15 slots)

| Slot | Count | Eligibility |
|------|-------|-------------|
| C | 2 | C only |
| 1B | 1 | 1B only |
| 2B | 1 | 2B only |
| SS | 1 | SS only |
| 3B | 1 | 3B only |
| CI | 1 | 1B or 3B |
| MI | 1 | 2B or SS |
| OF | 5 | OF only |
| UT | 2 | Any position |

#### Pitcher Positions (11 slots)

All 11 pitchers go into generic **P** slots — any combination of SP/RP is allowed.

### Position Eligibility Rules

| Rule | Threshold |
|------|-----------|
| Previous season eligibility | **7 games** at a position |
| Current season eligibility | **1 game** at a position |
| Draft day eligibility | Based on **previous year only** (current-year pre-draft games don't count) |

- Rookies with no MLB history start at their **default (minor league) position**
- Rookies **lose default eligibility** once they earn eligibility at a new position
- Players who didn't reach 7 games at any position last year → eligible at position(s) played most
- DH-only players are eligible at **UT only** (no DH slot in league)
- Owners **can** place players at any position during the season (for expected eligibility changes) — this is a rare league-specific override
- Positional slots are strictly enforced (must fill exact positions)

### Reserve Roster

| Reserve Type | Requirement | Max Slots |
|-------------|-------------|-----------|
| DL (Disabled List) | Must be on MLB IL | 10 |
| FARM (Minor Leaguers) | Must NOT be on an active MLB roster; **draft acquisitions only** | 10 |
| RES (General Reserves) | No restriction | 10 |

- **Total reserve cap:** 26 players
- **Full roster salary cap** (active + reserves): **$500**
- **DL salaries do NOT count** against the full roster salary cap
- **FARM salaries do NOT count** against the full roster salary cap
- FARM is restricted to players with Rookie MLB status acquired at the draft (no post-draft FARM additions except via trade)
- Reserve rosters can have any mix of hitters and pitchers (no balance requirement)

### September Roster Expansion

- After **September 1**, each team may add **1 additional player** (1 hitter OR 1 pitcher, not both)

### Restricted List / Bereavement

- Restricted list players (suspensions, extended absences) treated as ordinary inactive players (like minor leaguers)
- Bereavement/paternity/family medical leave players remain on active MLB roster list (not shifted to DL)

---

## Contract & Salary System

> **Contract rules are essential for converting PAR to auction dollar values and evaluating keeper decisions.**

### Auction

- **Auction budget:** $360 per team for the starting lineup
- **Minimum bid:** $1
- **Maximum player salary:** $75
- Each team's available auction budget varies based on existing keeper/contract commitments

### Salary Caps

| Cap | Amount |
|-----|--------|
| Active lineup | $350 |
| Full roster (active + reserves) | $500 |

- Owners **cannot** submit moves that put them over the salary cap
- No minimum salary floor
- Salary caps are the same for all teams (no team-specific caps)

### Contracts

- **Contract years:** Designated "a" (1st year), "b" (2nd year), "c" (option/final year)
- **Maximum contract length:** 3 years at the same salary
- **Extension options** available before a player enters their 3rd year:
  - 1-year extension: **+$5** to salary
  - 2-year extension: **+$10** to salary
- Contracts of traded players do **not** reset to year one
- Free agent pickups receive contract designation "a" (1st year)

### Keeper Deadline

- **January 31** (or earlier), 5:00 AM ET
- Commissioner manages keeper lists (owners do not self-manage on the site)

---

## Transaction Rules

### General Transaction Framework

- **Transaction day:** Mondays
- **Deadline:** 1:00 PM ET on Monday
- Owners can set lineups up to a week in advance
- **No mid-week transactions** — no DL replacements, no activations, nothing takes effect between Mondays (commissioner cannot override this)
- Owners may **not** add free agents directly; all adds go through the Bid Meister (commissioner-administered)
- Owners may **not** make moves in the off-season or pre-season
- MLB player statuses updated once daily (~6:00 AM), not continuously

### Old School Rules

> **This is a critical constraint for replacement-level modeling.**

- Active lineup players **cannot be replaced by a free agent** unless they are **no longer on an active MLB roster** (injured, demoted, released, etc.)
- Draft-day mistakes are sticky — you can't bench a healthy underperformer for a free agent
- Players are **tied to their replacements** — if the original player returns to active MLB status, either the replacement or the original must be waived. Both cannot remain on the same team.
- Players must be moved through DL/minors before being released (two-transaction process is NOT required — direct release is allowed)

### Free Agent Pickups

- Free agents are awarded via the **Bid Meister** (blind bidding system)
- **Bid deadline:** Mondays at 1:00 PM ET
- Bids take effect the **same day** (even if deadline is after lineup change cutoff)
- Free agents added must go to the **active roster** and remain there for **one full transaction cycle** (one week)
- **No FAAB** (Free Agent Acquisition Budget) — not a budget-based system
- **Salary determination:** The greater of the player's previous salary or the **$10 default minimum**
- Minor leaguers and DL players are **not eligible** as free agents
- **Free agent pickup cutoff:** July 1 (no pickups after this date)
- **No limit** on free agents per transaction cycle
- **Yearly limit** on free agent pickups: tracked (1 per year shown in rules, but this may be a display artifact — confirm with commissioner)
- Whole dollar bids only (no fractional bids)
- If a free agent is injured/demoted between bid submission and deadline, the bid is **rejected** (player no longer eligible)
- Commissioner can enter bids on behalf of owners (can see/alter bids before sorting)
- All bids are visible to the league after the Bid Meister runs (no suppression of contingent bids)
- Bid priority for free agents: **standings order** (last place gets first choice)

### Waiver Wire

- Players cut from a team go to the **waiver wire** (distinct from the free agent pool)
- **Waiver duration:** One full transaction cycle (one week)
- Claims awarded by **standings order** (last place gets priority)
- Priority is independent of which team waived the player (no penalty for re-claiming your own waived player)
- Waivers run through the first claim cycle **7 days after** the player was waived (not the next immediate cycle)
- Players cannot be claimed before waivers expire (no early claims)
- Players sent to minors or placed on DL while on waivers → **no longer claimable**
- Players traded to NL while on waivers → **no longer eligible**
- Waiver claims must go to **active roster** for one full transaction cycle
- **Salary on waivers:** Same as previous team's salary
- **Contract year:** Same as the free agent default ("a")
- **Yearly limit** on waiver claims: tracked (1 per year shown in rules)
- Waiver claim priority: **standings order** (last place gets first choice), using **current standings** (not previous week's)
- First week of season (no standings): **random order**
- Pre-season and post-season waivers: waived players do **not** stay on waivers for claiming

### Trades

- Owners propose/accept trades on the site; **commissioner must approve and enter**
- **Trade proposal deadline:** All-Star Break
- **Absolute trade cutoff:** July 1
- After acceptance, other owners have **1 day** to vote
- Trades require approval of **all teams** in the league
- Non-votes count as **approval** (failure to vote = in favor)
- Voting is **anonymous**
- **Draft pick trading** is allowed (tracked for up to 4 rounds)
- **FAAB money trading** is disabled (N/A since league doesn't use FAAB)
- No "un-tradeable" player lists
- No "un-releasable" player lists

---

## Draft Rules

- **Online draft room** hosted on OnRoto
- **Draft date:** March 25, 7:00 PM ET
- **Auction format:** $360 budget per team, $1 minimum bid, $75 maximum salary
- DL players **can** be drafted (not excluded)
- Restricted list players **can** be drafted
- Players who opt out **can** be drafted
- Pre-Opening Day injured players are manually placed on DL by OnRoto when it's certain they'll start on IL
- Draft picks can be traded (tracked for 4 rounds)

---

## Historical Data Notes

> **Essential context for SGP calibration.**

### Available Seasons

- **On OnRoto:** 2015–2025 (11 seasons)
- **Scoring era change:** 8 categories (2015–2018) → 10 categories (2019–2025)
  - 2015–2018: HR, RBI, SB, AVG, W, SV, ERA, WHIP
  - 2019–2025: R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO

### Data Quality Considerations

| Year(s) | Issue | SGP Impact |
|---------|-------|------------|
| 2015–2018 | Only 8 categories (no R, SO) | Cannot use for R or SO SGP; usable for the other 8 categories with caution |
| 2016, 2017 | 11 teams instead of 10 | Points scale is 11→1 instead of 10→1; affects SGP denominators |
| 2020 | COVID-shortened season (~35% of normal stats) | Raw stat totals are compressed; SGP per point is much smaller |
| 2025 | Partial season (data through early March) | Exclude from SGP calculations entirely |

### Team Name Variations

Team names are inconsistent across years (e.g., "mean machine" vs "Mean Machine", "Dancing With The Dingos" vs "Dancing With Dingos"). Normalization required for cross-year analysis.

### SGP Calibration Recommendation

- **Primary calibration window:** 2019–2024 (6 full seasons with 10 categories)
- **Exclude 2020** or treat separately (COVID season distorts stat totals)
- **Exclude 2025** (incomplete season)
- **Usable seasons at full confidence:** 2019, 2021, 2022, 2023, 2024 (5 seasons, ~50 team-seasons)
- 2015–2018 data can supplement HR, RBI, SB, AVG, W, SV, ERA, WHIP SGP estimates but requires careful handling due to the 8→10 category change and varying team counts

---

## Administrative & Display Settings

These settings have minimal modeling impact but are documented for completeness.

### Site Behavior

- Scoring cycle: Every other Monday
- No weekly-only standings or split-season standings
- No daily stat corrections display with OnRoto IDs
- Games played by position data is printed on stat reports
- Stats for all players who contributed to a team are printed (including traded/cut players)
- Bench/squandered stats are printed for all players (including traded/cut)
- Transaction logs show all move types (position changes, contract adjustments, salary changes, activations/reserves)
- Transaction logs only show post-Opening Day transactions (pre-season excluded)

### Message Board & Communication

- Threaded message board enabled
- Owner emails displayed on Owner Info page
- Owner phone numbers displayed on Owner Info page
- No owner mailing addresses displayed
- Anonymous posting not allowed
- All owners can create polls; poll voting is anonymous
- Poll tallies visible before voting

### Commissioner Powers

- Commissioner can activate MLB players before they officially come off DL
- Commissioner cannot place players on DL if not on MLB DL
- Commissioner cannot make mid-week lineup changes
- Commissioner can enter Bid Meister moves for individual teams (can see/alter bids)
- Commissioner cannot restrict owners from posting to message board

### Fees & Tracking

- Fee page not displayed
- Fee structure does not change after All-Star Break
- No custom fee columns
- Pre-season trades are charged in the fee system
- Opening Day corrections count against transaction fees

### Display Preferences

- No draft countdown timer currently (draft date passed)
- Keeper countdown timer not displayed
- Each owner sets their own category display order
- Player notes are visible
- Transaction details visible to all owners in real time (not hidden until deadline)
- Roster warnings visible to all owners

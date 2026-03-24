# Baseball Data Sources: Comprehensive Research

This document consolidates all publicly available data sources relevant to both hitting and pitching stat prediction for the Moonlight Graham AL-only rotisserie league.

---

# Part 1: Hitting Data Sources


**Target categories:** R (Runs), HR (Home Runs), RBI (Runs Batted In), SB (Stolen Bases), AVG (Batting Average)
**Model architecture:** Predict rate stats per PA (HR/PA, RBI/PA, R/PA, SB/PA, AVG), then scale by playing time
**League context:** AL-only, 10-team rotisserie, 15 AL teams

---

## Table of Contents

1. [Baseball Savant / Statcast](#1-baseball-savant--statcast)
2. [FanGraphs](#2-fangraphs)
3. [Baseball Reference / Stathead](#3-baseball-reference--stathead)
4. [pybaseball (Python)](#4-pybaseball-python-package)
5. [baseballr (R)](#5-baseballr-r-package)
6. [MLB Stats API](#6-mlb-stats-api)
7. [Retrosheet](#7-retrosheet)
8. [Lahman Database](#8-lahman-database)
9. [Chadwick Bureau](#9-chadwick-bureau)
10. [Baseball Prospectus](#10-baseball-prospectus)
11. [Brooks Baseball](#11-brooks-baseball)
12. [Park Factors](#12-park-factors-data)
13. [Projection Systems](#13-projection-systems)
14. [Minor League / Prospect Data](#14-minor-league--prospect-data)
15. [Injury Data](#15-injury-data)
16. [Contract / Salary Data](#16-contract--salary-data)
17. [Lineup / Batting Order Data](#17-lineup--batting-order-data)
18. [Spring Training Data](#18-spring-training-data)
19. [Fantasy-Specific Data Sources](#19-fantasy-specific-data-sources)
20. [Kaggle / Other Open Datasets](#20-kaggle--other-open-datasets)
21. [Data Relevance Matrix](#21-data-relevance-matrix)

---

## 1. Baseball Savant / Statcast

**URL:** https://baseballsavant.mlb.com
**Historical depth:** 2015-present (Statcast era); Pitch F/X data 2008-2016
**Access:** Free web interface, CSV downloads, programmatic access via pybaseball/baseballr

### 1.1 Pitch-Level Data (Statcast Search)

The Statcast Search tool provides **pitch-by-pitch data with 92 columns** per row. This is the most granular publicly available MLB data.

**Access:** https://baseballsavant.mlb.com/statcast_search (web + CSV download)
**Documentation:** https://baseballsavant.mlb.com/csv-docs

**Key columns for hitting prediction:**

| Column | Description | Relevance to Rate Stats |
|--------|-------------|------------------------|
| `launch_speed` | Exit velocity (mph) of batted ball | **HR, AVG**: Primary predictor of batted ball outcomes. Higher EV = more HRs and higher BABIP |
| `launch_angle` | Vertical angle off bat (degrees) | **HR, AVG**: Launch angle 25-35 degrees = HR zone; 10-25 = line drive zone for hits |
| `estimated_ba_using_speedangle` | xBA per batted ball | **AVG**: Expected batting average based on EV+LA; identifies over/underperformers |
| `estimated_woba_using_speedangle` | xwOBA per batted ball | **All categories**: Comprehensive expected offensive value per batted ball |
| `bb_type` | Batted ball classification (ground_ball, line_drive, fly_ball, popup) | **AVG, HR**: Batted ball profile predicts outcome distribution |
| `hc_x`, `hc_y` | Hit coordinates (spray chart position) | **AVG**: Spray tendencies affect BABIP; pull-heavy hitters have different HR/AVG profiles |
| `hit_distance_sc` | Projected distance of batted ball | **HR**: Distance correlates with HR probability |
| `events` | Outcome of plate appearance | All: The actual outcome data for training models |
| `description` | Pitch result (ball, strike, foul, hit_into_play, etc.) | **AVG**: Swing/miss tendencies predict K rate, which affects AVG |
| `pitch_type` | Type of pitch thrown | **AVG**: Performance varies by pitch type faced |
| `release_speed` | Pitch velocity | **AVG**: Fastball velocity faced affects contact quality |
| `zone` | Strike zone location (1-14 grid) | **AVG**: Performance by pitch location |
| `stand` | Batter handedness (L/R) | **AVG, HR**: Platoon splits affect all hitting |
| `p_throws` | Pitcher handedness (L/R) | **AVG, HR**: Same-hand/opposite-hand matchup effects |
| `bat_speed` | Bat speed at contact (mph) | **HR, AVG**: NEW (2024+) - faster bat speed = higher EV potential |
| `swing_length` | Length of swing path (feet) | **AVG**: Shorter swings may produce more contact |
| `delta_run_exp` | Change in run expectancy from this event | **R, RBI**: Contextual run value of the event |
| `on_1b`, `on_2b`, `on_3b` | Runner IDs on each base | **RBI**: Context for RBI opportunity |
| `inning` | Inning of the event | **All**: Late-inning performance splits |
| `at_bat_number` | At-bat number within the game | Fatigue/pitcher familiarity effects |
| `pitch_number` | Pitch number within the at-bat | **AVG**: Count-dependent performance |
| `balls`, `strikes` | Pre-pitch count | **AVG**: Count leverage affects outcome probabilities |
| `if_fielding_alignment` | Infield defensive alignment | **AVG**: Shift data pre-2023; standard alignment post-2023 ban |
| `of_fielding_alignment` | Outfield alignment | **AVG**: Outfield positioning affects BABIP |

### 1.2 Leaderboards (Aggregated Season-Level)

Baseball Savant provides multiple specialized leaderboards, each with CSV download capability.

#### Exit Velocity & Barrels Leaderboard
**URL:** https://baseballsavant.mlb.com/statcast_leaderboard

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Avg Exit Velocity | Mean EV across all batted balls | **HR, AVG**: Core predictor of batted ball quality |
| Max Exit Velocity | Highest single EV recorded | **HR**: Raw power ceiling indicator |
| Barrel % | % of batted balls classified as "barreled" (ideal EV+LA combo) | **HR**: Most direct HR rate predictor available |
| Hard Hit % | % of batted balls with EV >= 95 mph | **AVG, HR**: Sustained hard contact predicts both |
| LA Sweet Spot % | % of batted balls with launch angle 8-32 degrees | **AVG**: Optimal angle range for hits |
| Avg Launch Angle | Mean launch angle | **HR vs AVG tradeoff**: Higher LA = more HR but potentially lower AVG |
| Batted Ball Events (BBE) | Total batted balls | Playing time proxy |

**Filters available:** Year (2015+), min PA/batted balls, position, team, batter hand
**Historical depth:** 2015-present

#### Expected Statistics Leaderboard
**URL:** https://baseballsavant.mlb.com/leaderboard/expected_statistics

| Metric | Description | Relevance |
|--------|-------------|-----------|
| xBA | Expected batting average (based on EV + LA + sprint speed on weak contact) | **AVG**: Identifies luck-adjusted AVG; players with AVG >> xBA are likely to regress |
| xSLG | Expected slugging percentage | **HR**: Proxy for expected power output |
| xwOBA | Expected weighted on-base average | **All**: Comprehensive expected offensive value |
| xOBP | Expected on-base percentage | **R**: Getting on base drives run scoring |
| xISO | Expected isolated power (xSLG - xBA) | **HR**: Expected power isolated from contact |
| BA - xBA | Difference between actual and expected BA | **AVG**: Measures luck/regression risk |
| wOBA - xwOBA | Difference between actual and expected wOBA | **All**: Overall luck/regression indicator |

**Historical depth:** 2015-present
**Critical for model:** xBA vs actual BA is one of the most powerful regression-to-the-mean signals for AVG prediction.

#### Sprint Speed Leaderboard
**URL:** https://baseballsavant.mlb.com/leaderboard/sprint_speed

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Sprint Speed (ft/sec) | Fastest 1-second window on competitive runs | **SB**: Primary predictor of stolen base ability |
| Bolts | Runs >= 30 ft/sec | **SB**: Elite speed indicator |
| HP to 1B (seconds) | Home-to-first time | **AVG**: Faster runners beat out more infield hits |
| Competitive Runs | Number of measured sprint events | Sample size indicator |

**Historical depth:** 2015-present (standardized methodology from 2016+)
**Key insight for SB prediction:** Sprint speed is the most stable year-over-year physical metric available. Combined with attempt frequency (which is opportunity/managerial driven), it forms the backbone of SB prediction.

#### Baserunning Run Value Leaderboards
**URL:** https://baseballsavant.mlb.com/leaderboard/basestealing-run-value
**URL:** https://baseballsavant.mlb.com/leaderboard/baserunning-run-value

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Basestealing Run Value | Runs created/lost via stolen bases, adjusted for catcher/pitcher matchup | **SB**: Skill-isolated SB value |
| Extra Bases Taken Run Value | Value from taking extra bases (1st to 3rd on singles, etc.) | **R**: Aggressive baserunning drives run scoring |
| Overall Baserunning Run Value | Combined basestealing + extra bases | **R, SB**: Comprehensive baserunning impact |

**Historical depth:** 2016-present

#### Bat Tracking Leaderboard (NEW - 2024+)
**URL:** https://baseballsavant.mlb.com/leaderboard/bat-tracking

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Avg Bat Speed (mph) | Speed of bat at sweet spot | **HR**: Higher bat speed = higher EV ceiling |
| Avg Swing Length (ft) | Length of swing path | **AVG**: Shorter swings may improve contact rate |
| Squared-Up Rate | % of swings where bat speed is efficiently converted to EV | **HR, AVG**: Measures quality of contact independent of pitch |
| Blast Rate | % of batted balls with high EV + optimal LA | **HR**: Elite contact events |
| Fast Swing Rate | % of swings >= 75 mph | **HR**: Frequency of power swings |
| Ideal Attack Angle % | % of swings with 5-20 degree attack angle | **AVG**: Optimal swing path for contact |

**Historical depth:** Partial 2023, full 2024-present
**Key insight:** This is the newest Statcast data and represents the cutting edge. Bat speed data adds a dimension that exit velocity alone cannot capture -- it measures the input (swing) rather than just the output (batted ball).

#### Swing Path / Attack Angle (NEW - 2025)
**URL:** https://baseballsavant.mlb.com/leaderboard/bat-tracking/swing-path-attack-angle

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Attack Angle | Vertical direction of bat at impact | **HR, AVG**: Directly relates to launch angle produced |
| Attack Direction | Horizontal direction (pull/oppo tendency) | **HR, AVG**: Pull-side fly balls become HRs more often |
| Swing Tilt | Angle of bat relative to ground at contact | **AVG**: Affects batted ball type distribution |

**Historical depth:** 2025-present (brand new)

#### Swing/Take Visual Tool
**URL:** https://baseballsavant.mlb.com/visuals/swing-take

Provides pitch-by-pitch swing decision data with run values for each decision type. This is a visual tool (not CSV) but the underlying data is in the Statcast pitch-level export.

| Metric | Description | Relevance |
|--------|-------------|-----------|
| Chase Rate | % of out-of-zone pitches swung at | **AVG**: Lower chase rate = fewer weak contacts and fewer Ks |
| Whiff Rate | % of swings that miss | **AVG**: Higher whiff rate = higher K rate = lower AVG |
| In-Zone Swing % | % of in-zone pitches swung at | **AVG**: Aggressiveness on hittable pitches |
| Meatball Swing % | % of center-zone pitches swung at | **HR, AVG**: Capitalizing on mistakes |

#### Custom Leaderboards
**URL:** https://baseballsavant.mlb.com/leaderboard/custom

Allows selecting any combination of the above metrics into a single exportable table. Selectable metrics include: xba, xslg, xwoba, xobp, xiso, exit_velocity_avg, launch_angle_avg, barrel_batted_rate, and many more.

#### Rolling Window Leaderboard
**URL:** https://baseballsavant.mlb.com/leaderboard/rolling

Provides rolling xwOBA over customizable windows (e.g., last 50 PA, last 100 PA). Useful for identifying recent trend changes.

#### Year-to-Year Comparison
**URL:** https://baseballsavant.mlb.com/leaderboard/statcast-year-to-year

Shows how player Statcast metrics changed between consecutive seasons. Directly useful for identifying breakout/decline patterns.

### 1.3 Player Pages (Percentile Rankings)

Each player's Baseball Savant page includes percentile rankings against all MLB hitters for: xBA, xSLG, xwOBA, Avg EV, Max EV, Barrel %, Hard Hit %, K%, BB%, Sprint Speed, Whiff %, Chase Rate.

---

## 2. FanGraphs

**URL:** https://www.fangraphs.com
**Historical depth:** 2002-present for most advanced stats; standard stats back to 1871
**Access:** Free leaderboards with CSV export; some premium features require membership ($5.99/mo); pybaseball and baseballr provide programmatic access

### 2.1 Leaderboard Stat Tabs

FanGraphs organizes batting stats into multiple tabs, each containing different stat groups. ALL are available for CSV export.

#### Dashboard Tab
Standard overview: G, PA, HR, R, RBI, SB, BB%, K%, ISO, BABIP, AVG, OBP, SLG, wOBA, wRC+, WAR

#### Standard Tab
Traditional counting and rate stats: G, AB, PA, H, 1B, 2B, 3B, HR, R, RBI, BB, IBB, SO, HBP, SF, SH, GDP, SB, CS, AVG, OBP, SLG, OPS

#### Advanced Tab
| Metric | Description | Relevance |
|--------|-------------|-----------|
| BB% | Walk rate | **AVG**: Walks don't affect AVG directly but indicate plate discipline; **R**: Getting on base drives runs |
| K% | Strikeout rate | **AVG**: Primary negative predictor of AVG |
| BB/K | Walk-to-strikeout ratio | **AVG**: Plate discipline composite |
| ISO | Isolated power (SLG - AVG) | **HR**: Direct power measure |
| BABIP | Batting average on balls in play | **AVG**: Key regression indicator; league avg ~.300; sustained deviations suggest skill or luck |
| AVG | Batting average | **AVG**: Target variable |
| OBP | On-base percentage | **R**: On-base drives run scoring |
| SLG | Slugging percentage | **HR**: Power proxy |
| wOBA | Weighted on-base average | **All**: Best single offensive rate stat |
| wRC+ | Weighted runs created plus (park/league adjusted) | **All**: Best context-adjusted offensive rate stat |
| BsR | Baserunning runs above average | **SB, R**: Comprehensive baserunning value |
| Off | Offensive runs above average | **All**: Total offensive contribution |
| Def | Defensive runs above average | Playing time prediction (better defenders play more) |
| WAR | Wins above replacement | Playing time prediction; overall value metric |

#### Batted Ball Tab
| Metric | Description | Relevance |
|--------|-------------|-----------|
| GB% | Ground ball rate | **AVG**: High GB% players have different BABIP profiles; **HR**: Ground balls rarely become HRs |
| FB% | Fly ball rate | **HR**: Fly ball hitters hit more HRs |
| LD% | Line drive rate | **AVG**: Line drives have highest BABIP (~.680) |
| IFFB% | Infield fly ball rate (pop-ups) | **AVG**: Pop-ups are automatic outs |
| HR/FB | Home run per fly ball rate | **HR**: Key HR rate metric; predictive when combined with EV |
| Pull% | % of batted balls pulled | **HR**: Pull-side fly balls go for HRs much more often |
| Cent% | % of batted balls hit to center | **AVG**: Center field hits have moderate BABIP |
| Oppo% | % of batted balls hit to opposite field | **AVG**: Oppo approach can sustain high BABIP |
| Soft% | % soft contact | **AVG**: Soft contact results in outs |
| Med% | % medium contact | **AVG**: Medium contact results vary |
| Hard% | % hard contact | **HR, AVG**: Hard contact drives both power and average |

**Data availability:** Batted ball direction (Pull/Cent/Oppo) from 2002+; quality of contact (Soft/Med/Hard) from 2002+ (methodology changed 2010)

#### Plate Discipline Tab
| Metric | Description | Relevance |
|--------|-------------|-----------|
| O-Swing% | Chase rate (swing at pitches outside zone) | **AVG**: Higher chase rate = more weak contact and more Ks |
| Z-Swing% | In-zone swing rate | **AVG, HR**: Aggressiveness on good pitches |
| Swing% | Overall swing rate | **AVG**: Approach profile |
| O-Contact% | Contact rate on out-of-zone swings | **AVG**: Making contact even on bad pitches can sustain AVG (or indicate chasing) |
| Z-Contact% | Contact rate on in-zone swings | **AVG**: Core contact skill measure |
| Contact% | Overall contact rate | **AVG**: Primary K-rate determinant; highly predictive of AVG |
| Zone% | % of pitches seen in the strike zone | **AVG**: Better hitters see fewer strikes (pitched around) |
| F-Strike% | First pitch strike % | **AVG**: Count leverage starting point |
| SwStr% | Swinging strike rate | **AVG**: Alternative to whiff rate; highly correlated with K rate |

#### Plus Stats (+Stats) Tab
| Metric | Description | Relevance |
|--------|-------------|-----------|
| AVG+ | AVG relative to league (100 = average) | **AVG**: League-adjusted AVG |
| BB%+ | Walk rate relative to league | Context-adjusted plate discipline |
| K%+ | K rate relative to league | **AVG**: Context-adjusted strikeout tendency |
| OBP+ | OBP relative to league | **R**: Context-adjusted on-base |
| SLG+ | SLG relative to league | **HR**: Context-adjusted power |
| ISO+ | ISO relative to league | **HR**: Context-adjusted isolated power |
| BABIP+ | BABIP relative to league | **AVG**: Context-adjusted BABIP |

#### Statcast Tab (on FanGraphs)
FanGraphs also integrates Statcast data directly: EV, MaxEV, LA, Barrel%, HardHit%, plus bat tracking metrics (Bat Speed, Swing Length, Squared-Up%) as a "New!" tab.

#### Value Tab
| Metric | Description | Relevance |
|--------|-------------|-----------|
| Batting Runs | Runs above average from batting | **All**: Comprehensive batting value |
| Baserunning Runs | Runs above average from baserunning | **R, SB**: Baserunning contribution |
| wRAA | Weighted runs above average | **All**: PA-adjusted batting runs |
| WAR | Wins above replacement | Playing time; overall value |
| Dollars | Estimated dollar value (using standard $/WAR) | Valuation reference |
| Off | Offensive value | **All**: Total offensive contribution |

### 2.2 Splits Data

**URL:** https://www.fangraphs.com/leaders/splits-leaderboards

FanGraphs provides comprehensive split leaderboards with all the above stats broken down by:

| Split Type | Dimensions | Relevance |
|-----------|-----------|-----------|
| Platoon (vs LHP / vs RHP) | Full stat line | **AVG, HR**: LH batters hit LHP worse; platoon-dependent players need adjustment; critical for AL-only where you face specific pitching staffs |
| Home / Away | Full stat line | **HR, AVG**: Park factor adjustment at individual level |
| Month (Apr, May, Jun, Jul, Aug, Sep) | Full stat line | **All**: Seasonal trends, hot/cold streaks, fatigue effects |
| Day / Night | Full stat line | **AVG**: Some players have significant day/night splits |
| Bases Occupied (empty, runners on, RISP, bases loaded) | Full stat line | **RBI**: Performance with RISP directly affects RBI rate |
| Batting Order Position (1st, 2nd, 3rd, ... 9th) | Full stat line | **R, RBI**: Lineup position determines opportunity |
| Count (ahead, behind, even, full, 2 strikes, etc.) | Full stat line | **AVG**: Count-leverage performance |
| With Team / Opponent | Full stat line | AL-specific matchup effects |

**CSV export:** Available on all split leaderboards
**Historical depth:** Varies by split type; platoon and home/away back to 2002+

### 2.3 Player Pages

Individual player pages on FanGraphs provide:
- Career stats with all the above tabs
- Game logs (game-by-game stats)
- Splits (all dimensions above)
- Spray charts
- Pitch type performance breakdowns
- Value tracking over time

### 2.4 Projection Systems Hosted on FanGraphs

FanGraphs hosts multiple projection systems, all available for CSV download:

| System | Methodology | What It Projects | Relevance |
|--------|------------|-----------------|-----------|
| **Steamer** | Weighted recent performance + aging curves + regression | Full stat lines (PA, AVG, HR, R, RBI, SB, etc.) | Baseline projection to compare against; uses 3 years of data weighted toward recent |
| **ZiPS** | Player comparisons + aging + regression; includes spring training | Full stat lines + percentile distributions (1st-99th) | Most sophisticated public system; comparable player approach |
| **Depth Charts** | Average of ZiPS + Steamer, with FanGraphs staff playing time allocation | Full stat lines with manually curated PA estimates | Best available playing time estimates from human experts |
| **ATC** | Consensus of multiple projection systems | Full stat lines | "Average" projection; reduces individual system noise |
| **THE BAT / THE BAT X** | Proprietary system by Derek Carty | Full stat lines | Alternative projection methodology |
| **Fans** | Crowdsourced projections from FanGraphs users | Full stat lines | Wisdom of crowds; sometimes captures information systems miss |

**Access:** All downloadable as CSV from https://www.fangraphs.com/projections
**Filter options:** Position, team, league (AL/NL), min PA
**Historical depth:** Projections are published preseason each year; historical projections are not systematically archived on the site (must be saved manually)

**Critical for model:** These projections are both useful as features (what do other systems think?) and as baselines to beat. The Depth Charts playing time allocation is especially valuable for Layer 2 (playing time prediction).

### 2.5 RosterResource

**URL:** https://www.fangraphs.com/roster-resource

Provides team-by-team depth charts updated daily with:
- Projected starters at each position
- Bench players and role
- Injury status
- Lineup order
- Minor league depth

**Available as Excel download for FanGraphs members.**
**Relevance:** Playing time prediction (Layer 2) -- who is starting vs. who is the backup; roster competition

---

## 3. Baseball Reference / Stathead

**URL:** https://www.baseball-reference.com
**Historical depth:** 1871-present for standard stats
**Access:** Free player/team pages; Stathead subscription ($8/mo) for advanced queries

### 3.1 Standard Player Pages

Each player page includes:
- Career statistics (standard batting line)
- Year-by-year breakdown
- **Game logs** (game-by-game stats back to the 1950s)
- **Splits** (vs LHP/RHP, home/away, by month, by day/night, etc.)
- Fielding statistics
- Postseason stats
- Similarity scores (historical comparable players)
- Transaction history (trades, DFA, IL stints)

### 3.2 Unique Data vs FanGraphs

| Data Point | Availability | Relevance |
|-----------|-------------|-----------|
| Similarity Scores | Historical player comparisons | Aging curve / career trajectory modeling |
| Transaction/IL History | Complete transaction log per player | Playing time prediction; injury risk |
| Game Logs | Day-by-day stats (1954+) | Granular performance tracking; hot/cold streaks |
| Black Ink / Gray Ink | Historical performance rankings | Career quality indicators |
| Biographical data | Height, weight, birth date, debut date | Age calculation; physical profile |
| Positional appearances | Games at each position per season | Positional eligibility for fantasy |

### 3.3 Stathead (Premium Query Tool)

Stathead allows custom queries across the entire historical database:

| Tool | Description | Relevance |
|------|-------------|-----------|
| Player Season Finder | Find player-seasons matching criteria | Identify comparable players/seasons for projection |
| Player Game Finder | Find individual games matching criteria | Streak analysis; game-level patterns |
| Split Finder | Find career/season splits matching criteria | Platoon/context analysis at scale |
| Streak Finder | Find hitting/scoring streaks | Hot streak sustainability analysis |
| Span Finder | Find performance over spans of games | Rolling performance windows |
| Event Finder | Play-by-play event queries (1912+) | Granular event analysis |

**Splits available:** Game-level splits (home/road, month, day/night) from 1901; event-level splits (inning, platoon, leverage) complete from 1969, mostly complete from 1912.

---

## 4. pybaseball (Python Package)

**URL:** https://github.com/jldbc/pybaseball
**Install:** `pip install pybaseball`
**Sources accessed:** Baseball Savant, FanGraphs, Baseball Reference, Chadwick Bureau, Retrosheet

### 4.1 Key Functions for Hitting Data

| Function | Source | Data Level | Description |
|----------|--------|-----------|-------------|
| `statcast(start_dt, end_dt)` | Baseball Savant | Pitch-level | All Statcast pitch data for date range; 92 columns per row |
| `statcast_batter(start_dt, end_dt, player_id)` | Baseball Savant | Pitch-level | Player-specific Statcast data |
| `batting_stats(start_season, end_season)` | FanGraphs | Season-level | All FanGraphs batting metrics (Standard, Advanced, Batted Ball, etc.) |
| `batting_stats_range(start_dt, end_dt)` | Baseball Reference | Custom period | Batting stats for custom date ranges |
| `batting_stats_bref(season)` | Baseball Reference | Season-level | Season batting stats from Baseball Reference |
| `playerid_lookup(last, first)` | Chadwick Bureau | Player ID | Cross-reference player IDs across systems |
| `standings(season)` | Baseball Reference | Team-level | Division standings and records |
| `schedule_and_record(season, team)` | Baseball Reference | Game-level | Game-by-game team results |
| `pitching_stats(start_season, end_season)` | FanGraphs | Season-level | Pitcher stats (relevant for opposing pitcher context) |

### 4.2 Statcast Data Fields Available via pybaseball

The `statcast()` function returns a DataFrame with all 92 Statcast CSV columns including:
- Pitch characteristics: `pitch_type`, `release_speed`, `release_spin_rate`, `release_extension`, `spin_axis`
- Pitch location: `plate_x`, `plate_z`, `zone`
- Batted ball: `launch_speed`, `launch_angle`, `hit_distance_sc`, `bb_type`, `hc_x`, `hc_y`
- Expected stats: `estimated_ba_using_speedangle`, `estimated_woba_using_speedangle`
- Context: `balls`, `strikes`, `outs_when_up`, `inning`, `on_1b`, `on_2b`, `on_3b`
- Player IDs: `batter`, `pitcher` (MLBAM IDs)
- Bat tracking (2024+): `bat_speed`, `swing_length`

### 4.3 Practical Notes

- Statcast queries are limited to ~5 days per API call (automatically paginated by pybaseball)
- Building a full season of Statcast data requires iterating across date ranges
- Caching is available via `cache.enable()` to avoid repeated API calls
- FanGraphs batting_stats returns ~300+ columns covering all leaderboard tabs
- The `qual` parameter controls minimum PA threshold

---

## 5. baseballr (R Package)

**URL:** https://billpetti.github.io/baseballr/
**Install:** `install.packages("baseballr")`
**Version:** 1.6.0+ exports ~88 functions for MLB Stats API alone

### 5.1 Data Source Functions

| Function Prefix | Source | # Functions | Key Examples |
|----------------|--------|------------|-------------|
| `statcast_` | Baseball Savant | ~10 | `statcast_search()`, `statcast_search_batters()`, `statcast_leaderboards()` |
| `fg_` | FanGraphs | ~11 | `fg_batter_leaders()`, `fg_milb_batter_stats()` |
| `bref_` | Baseball Reference | ~4 | `bref_daily_batter()` |
| `mlb_` | MLB Stats API | ~88 | `mlb_player_info()`, `mlb_game_pks()`, `mlb_pbp()`, `mlb_stats()` |
| `retrosheet_` | Retrosheet | ~3 | Event file parsing |
| `chadwick_` / `playerid_` | Chadwick Bureau | ~3 | Player ID crosswalk |

### 5.2 Notable Functions for This Model

| Function | Description | Relevance |
|----------|-------------|-----------|
| `statcast_search()` | Pull Statcast pitch-level data | All hitting metrics at granular level |
| `statcast_leaderboards()` | Download Savant leaderboard data | Aggregated Statcast metrics |
| `fg_batter_leaders()` | FanGraphs batting leaders with all metrics | Season-level advanced stats |
| `fg_milb_batter_stats()` | Minor league batting stats from FanGraphs | Prospect performance data |
| `mlb_stats()` | Pull stats from MLB API with many stat types | Official stats with many split options |
| `mlb_pbp()` | Pitch-by-pitch data from MLB API | Alternative to Statcast for PBP |
| `mlb_player_info()` | Player biographical data | Age, position, physical attributes |
| `mlb_rosters()` | Team rosters | Current roster composition |
| `mlb_game_pks()` | Game IDs for a date | Foundation for game-level queries |

---

## 6. MLB Stats API

**URL:** https://statsapi.mlb.com/api/v1/
**Historical depth:** Varies by endpoint; most stats back to 1876
**Access:** Free, no authentication required for most endpoints; Python wrappers: `MLB-StatsAPI`, `python-mlb-statsapi`

### 6.1 Key Endpoints

| Endpoint | Description | Relevance |
|----------|-------------|-----------|
| `/people/{id}` | Player biographical info (DOB, height, weight, bats, throws, debut date) | Age/physical profile for projections |
| `/people/{id}/stats` | Player stats with flexible stat types and groups | All standard stats with many split options |
| `/schedule` | Game schedule with results | Schedule-based analysis |
| `/game/{id}/boxscore` | Complete boxscore for a game | Game-level stats |
| `/game/{id}/playByPlay` | Play-by-play for a game | Event-level data |
| `/game/{id}/linescore` | Line score for a game | Inning-by-inning scoring |
| `/standings` | Current/historical standings | Team context for R/RBI prediction |
| `/teams/{id}/roster` | Team roster | Playing time competition |
| `/transactions` | Player transactions (trades, IL, callups) | Injury/playing time tracking |
| `/meta` | Lookup valid stat types, stat groups, situation codes | Discover available data dimensions |

### 6.2 Stat Types Available

The API supports numerous stat types via the `statType` parameter:
- `season`, `career`, `yearByYear`, `yearByYearAdvanced`
- `byDateRange`, `byMonth`, `byDayOfWeek`
- `vsPlayer`, `vsTeam`
- `homeAndAway`, `dayAndNight`
- `leftOnBase`
- `hotColdZones` (performance by pitch zone)

### 6.3 Situation Codes

The `situationCodes` parameter allows filtering stats by game situation:
- Bases occupied (empty, runners on, RISP, bases loaded)
- Scoring position with 2 outs
- Inning ranges
- Close and late situations

**Relevance for RBI/R prediction:** You can extract how a player performs with runners on base, which is directly relevant to RBI rate per PA.

---

## 7. Retrosheet

**URL:** https://www.retrosheet.org
**Historical depth:** Play-by-play data for 205,886 games; complete for all AL/NL seasons 1910-2025
**Access:** Free downloads (event files, CSV files, game logs); usage is unrestricted

### 7.1 Available Data Types

| Data Type | Description | Format | Relevance |
|-----------|-------------|--------|-----------|
| Event Files | Raw play-by-play records | Custom format (parsed by BEVENT tool) | Most granular historical data; every play for 110+ years |
| Parsed Play-by-Play CSV | Pre-parsed event data (16.5M+ rows) | CSV (710 MB zip) | Ready-to-use play-level data |
| Game Logs | Summary of each game | CSV | Game-level team and player stats |
| Box Scores | Game box scores | Text/HTML | Game summaries |
| Roster Files | Team rosters by season | CSV | Historical roster composition |
| Schedule Files | Game schedules | CSV | Schedule analysis |

### 7.2 Event File Fields (96 possible fields per event)

Key fields from the BEVENT parser:

| Field Category | Examples | Relevance |
|---------------|----------|-----------|
| Game Context | Game ID, date, visiting/home team, inning, outs | Contextual factors for rate stat prediction |
| Batting Order | Lineup position of batter (1-9) | **R, RBI**: Batting order position directly affects R/RBI opportunity |
| Runners on Base | Runner IDs on 1B/2B/3B | **RBI**: Defines RBI opportunity per PA |
| Event Type | 25 numeric codes for event outcomes | Classification of every PA outcome |
| Pitch Sequence | Ball-by-ball pitch outcomes | **AVG**: Count-dependent performance analysis |
| Fielder Positions | Player IDs at all 8 fielding positions | Defensive alignment context |
| Batter/Pitcher Handedness | L/R for both | **AVG**: Platoon splits |
| Hit Location | Where ball was hit | **AVG**: Spray tendencies |
| Run/RBI Info | Runs scored, RBIs credited | **R, RBI**: Direct outcome data |

### 7.3 Chadwick Bureau retrosplits

**URL:** https://github.com/chadwickbureau/retrosplits

Pre-aggregated Retrosheet data at various levels of granularity (daily, season, splits by handedness, etc.). Ready-to-use CSV files derived from Retrosheet event files.

**Relevance:** Provides historical split data (platoon, home/away, etc.) in a convenient pre-aggregated format going back decades.

---

## 8. Lahman Database

**URL:** https://sabr.org/lahman-database/ (download) | R package: `install.packages("Lahman")`
**Version:** 2025 (released January 2, 2026)
**Historical depth:** 1871-2025 (complete batting and pitching statistics)
**Access:** Free CSV download or R package; Open Data License

### 8.1 Tables Relevant to Hitting Prediction

| Table | Key Columns | Relevance |
|-------|------------|-----------|
| **Batting** | playerID, yearID, stint, teamID, G, AB, R, H, 2B, 3B, HR, RBI, SB, CS, BB, SO, IBB, HBP, SH, SF, GIDP | **All categories**: Complete season-level batting stats; the core historical training data for any model |
| **People** | playerID, birthYear, birthMonth, nameFirst, nameLast, weight, height, bats, throws, debut, finalGame | Age, handedness, physical profile; **critical for aging curves** |
| **Appearances** | playerID, yearID, G_all, G_batting, G_c, G_1b, G_2b, G_3b, G_ss, G_lf, G_cf, G_rf, G_of, G_dh, G_ph, G_pr | Positional appearances; fantasy eligibility; playing time distribution |
| **Fielding** | playerID, yearID, POS, G, GS, InnOuts, PO, A, E, DP | Defensive role; starting vs backup indicator |
| **Salaries** | playerID, yearID, teamID, salary | 1985-2018; contract/financial context for playing time |
| **Teams** | yearID, teamID, W, L, R, HR, SB, etc. | Team-level context; offensive environment |
| **Parks** | parkID, parkName, city, state, country | Park identification for park factor analysis |
| **AllstarFull** | All-Star appearances | Player quality indicator |

### 8.2 Advantages of Lahman

- **Longest historical coverage** of any source (1871-present)
- **Convenient R package** with built-in data frames
- **Stable, well-documented schema** that doesn't change
- Excellent for building **aging curves** and **historical comps**
- Player-season level makes it easy to model year-over-year changes

### 8.3 Limitations

- Season-level only (no game-by-game or pitch-by-pitch)
- No advanced metrics (no wOBA, wRC+, Statcast, etc.)
- Salary data stops at 2018 in the database
- No split data (no platoon, home/away, monthly)

---

## 9. Chadwick Bureau

**URL:** https://github.com/chadwickbureau/register
**Access:** Free (Open Data Commons Attribution License); updated weekly on GitHub

### 9.1 Player ID Crosswalk

The Chadwick Register is the most comprehensive authority file for baseball personnel, with ~500K entries.

**Key value:** Cross-references player IDs across systems:
- MLBAM (MLB Advanced Media) -- used by Statcast/Baseball Savant
- Retrosheet
- Baseball Reference
- FanGraphs
- Other systems

**Access via R:** `baseballr::chadwick_player_lu()` downloads the full crosswalk
**Access via Python:** `pybaseball.playerid_lookup()` queries the register

**Relevance:** Essential infrastructure for joining data across sources. You will need to merge FanGraphs stats (using FanGraphs IDs) with Statcast data (using MLBAM IDs) and Lahman data (using Lahman/Retrosheet IDs).

---

## 10. Baseball Prospectus

**URL:** https://www.baseballprospectus.com
**Access:** Subscription required for most data ($5.99/mo); some content free
**Historical depth:** DRC+ available from 2010+; PECOTA projections published annually

### 10.1 Unique Metrics

| Metric | Description | Relevance |
|--------|-------------|-----------|
| **DRC+** (Deserved Runs Created Plus) | Context-adjusted hitting metric; league average = 100 | **All**: Claimed to be more predictive than wRC+ or wOBA because it separates player skill from context more aggressively; weights outcomes by attributability to the hitter |
| **WARP** (Wins Above Replacement Player) | BP's version of WAR | Playing time; overall value assessment |
| **BRR** (Baserunning Runs) | Baserunning value metric | **SB, R**: Baserunning skill assessment |

### 10.2 PECOTA Projections

| Feature | Description | Relevance |
|---------|-------------|-----------|
| Comparable players | Identifies historical comparables for each player | **All**: Similar player trajectories inform projection |
| Percentile projections | 10th, 25th, 50th, 75th, 90th percentile outcomes | **All**: Range of outcomes, not just point estimate; useful for risk assessment |
| Aging model | Built-in aging curves per stat | **All**: How each stat changes with age |
| Playing time | Projected PA with injury risk factored in | Layer 2 input |

### 10.3 Injured List Ledger / Timeline

Baseball Prospectus maintains an IL tracking tool showing:
- Days missed per player per stint
- WARP lost to injury
- Historical injury patterns

**Relevance:** Playing time prediction (Layer 2); injury risk modeling

### 10.4 Leaderboards

Available stats tabs: Hitting, Pitching, Fielding, Baserunning, PECOTA
All stats available on player cards with the same categories as leaderboards.

---

## 11. Brooks Baseball

**URL:** https://www.brooksbaseball.net
**Historical depth:** PITCHf/x era (2008-present)
**Access:** Free web interface; no bulk download or API

### 11.1 Available Data

Brooks Baseball specializes in **pitcher repertoire analysis** with manually corrected pitch classifications:
- Pitch type breakdowns (velocity, movement, usage %)
- Release point consistency
- Strikezone maps
- Game-by-game pitch mix data

### 11.2 Relevance to Hitting Model

While primarily a pitching resource, Brooks Baseball data is relevant because:
- **AVG prediction:** Understanding the pitch mix a batter will face from each AL team's staff helps predict contact quality
- **Opposing pitcher context:** Pitch arsenal information helps model batter-pitcher matchups
- However, this data is largely superseded by Statcast pitch-level data, which is available in bulk

---

## 12. Park Factors Data

### 12.1 Sources

| Source | Method | Granularity | Relevance |
|--------|--------|-------------|-----------|
| **Baseball Savant** (https://baseballsavant.mlb.com/leaderboard/statcast-park-factors) | Observed effect on Statcast metrics | Per park, per stat, per year; 1999+; filterable by batter hand, day/night, roof status | **HR, AVG, R**: Adjusts predictions for home park and road schedule |
| **FanGraphs** | 5-year regressed park factors; per hit type and handedness | Per park, multi-year smoothed | **HR, AVG, R**: More stable than single-year; accounts for handedness |
| **Baseball Reference** | Multi-year park factors | Per park, per stat | **HR, AVG, R**: Alternative methodology |
| **THE BAT / EVAnalytics** | Incorporates physical park properties (altitude, fence distance/height, foul ground) | Per park, incorporates physics | **HR**: Best for new parks or parks with recent changes |

### 12.2 What Park Factors Cover

All major sources provide park factors for:
- Runs, HR, H, 2B, 3B, BB, SO
- Some provide factors for specific batted ball types
- Some provide factors split by batter handedness (LHB vs RHB)

### 12.3 Relevance by Category

| Category | Park Factor Impact |
|----------|-------------------|
| **HR** | **High impact.** Yankee Stadium inflates LHH HRs; Coors inflates all HRs. AL parks vary significantly. |
| **AVG** | **Moderate impact.** Spacious outfields (e.g., Oakland, Seattle) suppress BABIP; small foul territory (e.g., Oakland pre-move) increases it. |
| **R** | **High impact.** Run scoring environment is the sum of all park effects on all offensive events. |
| **RBI** | **Moderate impact.** Follows R but also depends on team context. |
| **SB** | **Low impact.** Park factors have minimal effect on SB; base size is standardized. |

### 12.4 AL-Specific Considerations

For an AL-only league, park factors matter in two ways:
1. **Home park effect:** A player plays ~50% of games in their home park
2. **Schedule effect:** The remaining ~50% of games are distributed across the other 14 AL parks (plus interleague)

Both effects should be incorporated. FanGraphs provides schedule-adjusted park factors that account for the specific mix of road parks a team plays in.

---

## 13. Projection Systems

### 13.1 Summary of Available Systems

| System | Publisher | Free? | Methodology | Historical Archive |
|--------|----------|-------|-------------|-------------------|
| **Steamer** | Jared Cross et al. / FanGraphs | Yes (CSV) | 3-year weighted + aging + regression | Current year only (not archived) |
| **ZiPS** | Dan Szymborski / FanGraphs | Yes (CSV) | Comparable players + aging + spring training | Current year only; blog posts archive some |
| **Depth Charts** | FanGraphs staff | Yes (CSV) | Average of ZiPS + Steamer + staff PT allocation | Current year only |
| **ATC** | Ariel Cohen / FanGraphs | Yes (CSV) | Average of multiple systems | Current year only |
| **THE BAT X** | Derek Carty / FanGraphs | Yes (CSV) | Proprietary; uses park physics | Current year only |
| **PECOTA** | Baseball Prospectus | Subscription | Comparable players + percentile distributions | Current year only |
| **Fans** | FanGraphs community | Yes (CSV) | Crowdsourced | Current year only |

### 13.2 Using Projections as Features

Other systems' projections can be used as features in your own model:
- **Consensus baseline:** Average of multiple projections as a prior
- **Disagreement signal:** When your model diverges from consensus, it may indicate edge OR error
- **Playing time inputs:** Depth Charts PA estimates are the best publicly available playing time projections

### 13.3 What Projection Systems Use (Informative for Feature Selection)

Known inputs to major projection systems:
- 3+ years of recent performance (weighted toward most recent)
- Aging curves (stat-specific)
- Regression to the mean (especially BABIP, HR/FB, strand rate)
- Park factors
- League/era adjustments
- Platoon splits
- Minor league performance (for young players)
- Spring training performance (ZiPS, weighted lightly)
- Physical comparables / body type (PECOTA)
- Injury history (for playing time)
- Team context / roster competition (for playing time)

---

## 14. Minor League / Prospect Data

### 14.1 Sources

| Source | Data Available | Access | Historical Depth |
|--------|---------------|--------|-----------------|
| **FanGraphs** (MiLB leaderboards) | Standard + advanced stats by level (A, A+, AA, AAA) | Free CSV export | 2006+ |
| **Baseball Reference** (Register) | Complete MiLB stats | Free web; Stathead for queries | Extensive historical |
| **The Baseball Cube** | MiLB stats and standings | Free web | 1977+ |
| **MLB Pipeline / Prospect Tracker** | Top prospect stats + scouting grades | Free web | Current |
| **MLB Stats API** | MiLB stats via `mlb_stats()` with level parameter | Free API | Varies |
| **baseballr** | `fg_milb_batter_stats()` function | Free R package | FanGraphs MiLB data |

### 14.2 Key Data Available

| Data Point | Source | Relevance |
|-----------|--------|-----------|
| MiLB batting stats (AVG, HR, SB, BB%, K%, etc.) by level | FanGraphs, B-Ref | **All**: Predicting rookies and young players who may enter the AL player pool |
| Scouting grades (hit, power, speed, arm, field) on 20-80 scale | MLB Pipeline, FanGraphs | **All**: Tool-based projection for players with limited MLB data |
| Level-by-level progression | FanGraphs, B-Ref | **All**: Performance trajectory through minors predicts MLB performance |
| Age relative to league | Calculable from data | **All**: Young-for-level players project better |
| MiLB park factors | Limited availability | Adjustment for minor league park effects |

### 14.3 Relevance to AL-Only Model

- Prospects on the 40-man rosters of the 15 AL teams may be called up mid-season
- FARM roster slots in this league can stash minor leaguers
- Minor league performance is the primary data source for projecting rookies
- Translation factors (how MiLB stats convert to MLB) are essential for prospect projection

---

## 15. Injury Data

### 15.1 Sources

| Source | Data Available | Access |
|--------|---------------|--------|
| **Baseball Prospectus IL Ledger** | Days missed, injury type, WARP impact | Subscription |
| **FanGraphs RosterResource Injury Report** | Current IL status, injury description, expected return | Free |
| **ProSportsTransactions.com** | Historical injury/transaction data (2000-present) | Free web |
| **Baseball Heat Maps** | Disabled list data and analysis | Free |
| **The Baseball Cube** | IL listing with injury description and cause | Free |
| **MLB Stats API** (`/transactions`) | Official transaction records including IL placements | Free API |
| **Retrosheet** | Game-by-game participation (infer missed time) | Free download |

### 15.2 Relevance

| Usage | Category Affected |
|-------|-------------------|
| Predicting games missed (Layer 2 - Playing Time) | All categories (fewer PA = fewer counting stats) |
| Identifying players returning from injury who may underperform | AVG, HR (performance may be suppressed post-injury) |
| Historical injury patterns (chronic vs. acute) | Playing time reliability |
| IL stint timing (early season vs. late season) | In-season management decisions |

---

## 16. Contract / Salary Data

### 16.1 Sources

| Source | Data Available | Access |
|--------|---------------|--------|
| **Spotrac** (spotrac.com/mlb/contracts) | Current contracts, AAV, guaranteed money, option years, salary breakdowns | Free (some premium features) |
| **Cot's Baseball Contracts** (via Baseball Prospectus) | Contract details, payroll tracking | Free for basic; BP subscription for advanced |
| **Baseball Reference** | Historical salary data (from Joint Exhibit One) | Free |
| **Lahman Database (Salaries table)** | Player-season salary data (1985-2018) | Free |
| **FanGraphs RosterResource** | Salary data on team pages | Free |

### 16.2 Relevance to Playing Time (Layer 2)

| Data Point | Relevance |
|-----------|-----------|
| Contract size/years remaining | Higher-paid players get more rope; sunk cost effect keeps them in the lineup |
| Service time / arbitration status | Pre-arb players may be manipulated for service time (delayed callups) |
| Free agent year | Players in walk years may be traded mid-season (change in team context) |
| Option years remaining | Optionable players can be sent down; non-optionable players stick on MLB roster |
| Team payroll / budget constraints | Low-budget teams more likely to give young players playing time |

---

## 17. Lineup / Batting Order Data

### 17.1 Sources

| Source | Data Type | Access |
|--------|-----------|--------|
| **FanGraphs splits leaderboards** | Stats by batting order position | Free CSV |
| **Baseball Savant Statcast** | `at_bat_number` field in pitch data; batting order derivable from game data | Free |
| **MLB Stats API** (`/game/{id}/boxscore`) | Starting lineup with batting order | Free API |
| **Retrosheet event files** | Lineup position field per event | Free download |
| **Daily MLB Lineups API** | Projected/actual daily lineups from RotoWire | Free API |
| **FanGraphs RosterResource Lineup Tracker** | Historical lineup data | Free web |
| **Baseball Reference game logs** | Starting position and batting order per game | Free |

### 17.2 Relevance

| Lineup Position | Impact on Category |
|----------------|-------------------|
| Leadoff (1st) | **R**: Most PA; highest R/PA because scores ahead of best hitters; **SB**: Often the team's primary base stealer |
| 2nd | **R**: High PA; high R potential; increasing trend of putting best hitters here |
| 3rd | **R, RBI**: Classic "best hitter" slot; balanced R/RBI |
| 4th (Cleanup) | **RBI**: Highest RBI/PA; most runners on base when batting; **HR**: Power hitters placed here |
| 5th-6th | **RBI**: Still above-average RBI opportunity; declining R opportunity |
| 7th-9th | **R, RBI**: Significantly fewer opportunities; lower quality hitters around them |
| DH | **All**: AL-specific; full-time DH gets consistent PA without defensive rest days |

**Key finding from research:** The difference between batting 4th and 3rd in the order is approximately 32 additional baserunners over a full season (~600 AB), which translates to a meaningful RBI rate difference.

---

## 18. Spring Training Data

### 18.1 Sources

| Source | Data | Access |
|--------|------|--------|
| **FanGraphs** (Spring Training leaderboards) | Full batting stats during spring training | Free CSV |
| **Baseball Reference** | Spring training game logs and stats | Free web |
| **Baseball Savant** | Statcast data during spring training games | Free (if Statcast cameras active at spring venues) |

### 18.2 Predictive Value

Research findings on spring training stats:
- **Very weak predictive power overall** -- correlation with regular season performance is ~0.15
- **Max exit velocity** is the strongest carryover metric (explains ~33% of regular season max EV variance)
- **Pitch velocity and spin rate** carry over reliably (more relevant for pitchers)
- ZiPS incorporates spring training data with very low weight; it contributes a ~1.5% RMSE reduction
- **Health/playing status** emerging from camp may be more predictive than stats themselves
- Useful as a **late-breaking signal** for players making mechanical changes or recovering from injury

### 18.3 Relevance by Category

| Category | Spring Training Signal |
|----------|----------------------|
| **HR** | Max EV in spring has some predictive value; new mechanical approach might show in EV |
| **AVG** | Very weak signal; spring BABIP is essentially noise |
| **SB** | Speed is a physical trait that doesn't need spring validation |
| **R, RBI** | No meaningful spring signal; entirely context-dependent |

---

## 19. Fantasy-Specific Data Sources

### 19.1 ADP and Auction Values

| Source | Data | Access |
|--------|------|--------|
| **NFBC** (nfc.shgn.com/adp/baseball) | Expert league ADP; keeper league data; historical auction values | Free web |
| **FantasyPros** | Consensus ADP from major platforms; auction calculator with custom league settings (including AL-only) | Free web |
| **FanGraphs Auction Calculator** | Dollar values from projections with custom league settings | Free web tool |
| **RotoWire** | Auction values based on custom settings and 2026 projections | Free web |

### 19.2 FanGraphs Auction Calculator

**URL:** https://www.fangraphs.com/fantasy-tools/auction-calculator

This tool is directly relevant because it:
- Converts projections to auction dollar values
- Supports custom league settings (# teams, budget, positions, categories)
- Can be configured for AL-only
- Uses any of the hosted projection systems as input
- Outputs dollar values per player by category

**Relevance:** Useful as a cross-check for your own Layer 4 (SGP -> PAR -> Dollar Value) calculations.

---

## 20. Kaggle / Other Open Datasets

### 20.1 Kaggle Datasets

| Dataset | Description | Size |
|---------|-------------|------|
| **MLB Statcast Data** (kaggle.com/datasets/s903124/mlb-statcast-data) | Bulk Statcast pitch-level data | Multiple GB |
| **Baseball Databank** (kaggle.com/datasets/open-source-sports/baseball-databank) | Lahman database in Kaggle format | Standard |
| **MLB Bat Tracking Dataset 2024-2025** | Bat tracking Statcast data | 2 seasons |
| **Major League Baseball Hitting Data** | Hitting stats with basic + advanced metrics | Varies |
| **MLB Game Data** | Game-level data 2010-2020 | Standard |

### 20.2 Other Sources

| Source | Data | Access |
|--------|------|--------|
| **Stat Corner** | Park factors and other analytical data | Free web |
| **Swish Analytics** | Park factors for betting markets | Free web |
| **EVAnalytics** | THE BAT's park factors using physical park properties | Free web |
| **Fangraphs Community Research** | User-published research and data | Free |
| **SABR** (sabr.org) | Research papers and sabermetric guides | Free membership |

---

## 21. Data Relevance Matrix

### By Target Category

#### HR/PA Prediction

| Feature | Source | Why It Matters | Priority |
|---------|--------|---------------|----------|
| Barrel % | Savant | Most direct HR predictor; barrels become HRs ~70% of the time | **Critical** |
| Avg/Max Exit Velocity | Savant | Raw power; higher EV = higher HR probability on fly balls | **Critical** |
| Launch Angle (avg + distribution) | Savant | 25-35 degree sweet spot for HRs; too low = grounders, too high = pop-ups | **Critical** |
| HR/FB rate | FanGraphs | Historical HR rate on fly balls; partially luck-driven but has skill component | **Critical** |
| FB% (fly ball rate) | FanGraphs | More fly balls = more HR opportunities | **High** |
| Pull% on fly balls | FanGraphs + Savant | Pull-side fly balls become HRs much more often | **High** |
| Bat Speed | Savant (2024+) | Faster bat = higher EV ceiling = more HR potential | **High** |
| Park Factor (HR) | Savant/FanGraphs/B-Ref | Park dimensions dramatically affect HR rates | **High** |
| ISO / xISO | FanGraphs / Savant | Isolated power measures | **High** |
| Hard Hit % | Savant | Sustained hard contact correlates with HR rate | **Medium** |
| Squared-Up Rate | Savant (2024+) | Efficiently converting bat speed to EV | **Medium** |
| xSLG | Savant | Expected slugging captures power potential | **Medium** |
| Age | Lahman/People table | Power peaks around age 27-30; declines slowly after | **Medium** |
| Platoon splits | FanGraphs splits | Some hitters only have HR power vs opposite-hand pitching | **Medium** |
| Opposing pitcher arsenal | Savant/Brooks | Pitch types faced affect HR probability | **Low** |

#### AVG Prediction

| Feature | Source | Why It Matters | Priority |
|---------|--------|---------------|----------|
| xBA | Savant | Expected BA based on batted ball quality; best single predictor of future AVG | **Critical** |
| BABIP | FanGraphs | Batting average on balls in play; identifies luck vs. skill in AVG | **Critical** |
| K% / Contact Rate | FanGraphs | Strikeouts are guaranteed non-hits; K% is the largest single AVG driver | **Critical** |
| Line Drive % | FanGraphs | Line drives have ~.680 BABIP; LD hitters sustain higher AVG | **Critical** |
| Sprint Speed | Savant | Faster runners beat out infield hits; affects BABIP on weak contact | **High** |
| O-Swing% (Chase Rate) | FanGraphs / Savant | Chasing = weak contact + more Ks = lower AVG | **High** |
| Z-Contact% | FanGraphs | Ability to make contact on strikes; core contact skill | **High** |
| SwStr% (Whiff Rate) | FanGraphs / Savant | Swinging strike rate is the most predictive K-rate indicator | **High** |
| Hard Hit % | Savant | Hard-hit balls have higher BABIP | **High** |
| GB% / FB% profile | FanGraphs | Batted ball mix affects BABIP baseline (GB BABIP ~.240, LD BABIP ~.680, FB BABIP ~.130) | **High** |
| Park Factor (H) | Savant/FanGraphs | Some parks suppress/inflate batting average | **Medium** |
| Platoon splits | FanGraphs | Same-side matchups suppress AVG significantly | **Medium** |
| Pull%/Oppo% | FanGraphs | Spray distribution affects BABIP and defensive positioning | **Medium** |
| Soft% / Hard% | FanGraphs | Contact quality distribution | **Medium** |
| IFFB% | FanGraphs | Infield pop-ups are automatic outs; suppress AVG | **Medium** |
| BA - xBA (prior year) | Savant | Large positive BA-xBA predicts AVG decline next year | **Medium** |
| Age | Lahman | Contact ability declines starting around age 25-26 | **Medium** |
| Shift data (pre-2023) / Positioning (post-2023) | Savant | Shift ban in 2023 raised league AVG ~5 points; LHH benefited most | **Medium** |

#### R/PA Prediction

| Feature | Source | Why It Matters | Priority |
|---------|--------|---------------|----------|
| Batting Order Position | Retrosheet/FanGraphs/MLB API | Leadoff hitters score most runs; lineup position determines opportunity | **Critical** |
| OBP / xOBP | FanGraphs / Savant | Getting on base is prerequisite to scoring | **Critical** |
| Team Offensive Quality | FanGraphs team stats | Better teammates = more chances to be driven in after reaching base | **Critical** |
| SB / Sprint Speed | Savant / FanGraphs | Stealing bases advances into scoring position; fast runners score from 1st on doubles | **High** |
| HR (own) | Model output | Solo HR = guaranteed run scored | **High** |
| BB% | FanGraphs | Getting on base via walks; correlates with R | **High** |
| Park Factor (R) | Savant/FanGraphs | Offensive environment of home park | **Medium** |
| Extra Bases Taken Run Value | Savant | Aggressive baserunning puts runners in scoring position | **Medium** |
| Quality of hitters behind in lineup | FanGraphs projections | Better hitters behind you = more likely to score after reaching base | **Medium** |

#### RBI/PA Prediction

| Feature | Source | Why It Matters | Priority |
|---------|--------|---------------|----------|
| Batting Order Position | Retrosheet/FanGraphs/MLB API | 3rd-5th hitters get most RBI opportunities (most runners on base when they bat) | **Critical** |
| HR (own) | Model output | Every HR is at least 1 RBI; more with runners on | **Critical** |
| Team OBP (hitters ahead in lineup) | FanGraphs team stats | Better OBP from 1-3 hitters = more runners on for cleanup hitter | **Critical** |
| Performance with RISP | FanGraphs splits / MLB API | Batting with runners in scoring position; has skill + luck components | **High** |
| SLG / ISO | FanGraphs | Extra-base hits drive in more runners | **High** |
| wRC+ | FanGraphs | Overall offensive quality predicts RBI rate controlling for opportunity | **High** |
| Park Factor (R) | Savant/FanGraphs | Higher-scoring environments produce more RBI opportunities | **Medium** |
| Contact Rate | FanGraphs | Making contact with RISP avoids Ks; even weak contact can score runners from 3rd | **Medium** |
| Fly Ball Rate | FanGraphs | Sacrifice flies can drive in runs; FB hitters produce more sac flies | **Medium** |

#### SB/PA Prediction

| Feature | Source | Why It Matters | Priority |
|---------|--------|---------------|----------|
| Sprint Speed | Savant | Physical speed is the primary SB determinant | **Critical** |
| Prior Year SB Totals | Lahman/FanGraphs | Historical SB volume indicates willingness + opportunity to run | **Critical** |
| SB Success Rate | FanGraphs / Savant | Higher success rate indicates both speed and baserunning skill/reads | **Critical** |
| OBP | FanGraphs | Must get on base to steal; higher OBP = more SB opportunities | **High** |
| Batting Order Position | Retrosheet/FanGraphs | Leadoff/top-of-order hitters steal more; bottom-of-order hitters rarely attempt | **High** |
| Age | Lahman | Speed declines with age; SB attempts drop significantly after age 30 | **High** |
| Manager tendencies | Team-level SB data | Some managers are more aggressive with the running game | **Medium** |
| Rule changes (2023+) | Context | Bigger bases + pickoff limits increased SB rates from 75% to ~80% success | **Medium** |
| Team context | FanGraphs | Trailing teams run less; leading teams may run less; close games = more SB | **Medium** |
| Basestealing Run Value | Savant | Context-adjusted SB value (accounts for catcher/pitcher matchup quality) | **Medium** |
| CS data | FanGraphs | Caught stealing rate; high CS can lead managers to reduce attempts | **Medium** |
| HP to 1B time | Savant | Home-to-first speed (slightly different from sprint speed) | **Low** |

---

## Key Architectural Recommendations Based on This Research

### Recommended Primary Data Sources by Model Layer

**Layer 1 (Rate Stats):**
- **Primary:** FanGraphs batting stats (via pybaseball `batting_stats()`) -- provides all advanced metrics in one pull
- **Primary:** Baseball Savant Statcast aggregates (via pybaseball or baseballr) -- provides xBA, xSLG, xwOBA, barrel %, EV, sprint speed
- **Secondary:** Statcast pitch-level data for custom feature engineering (e.g., exit velocity distribution, launch angle buckets, performance by count)
- **Secondary:** FanGraphs splits data for platoon adjustments
- **Tertiary:** Bat tracking data (2024+) for cutting-edge swing metrics

**Layer 2 (Playing Time):**
- **Primary:** FanGraphs Depth Charts projections for PA estimates
- **Primary:** Injury history from ProSportsTransactions / FanGraphs RosterResource
- **Secondary:** Contract/salary data from Spotrac/Cot's
- **Secondary:** Minor league depth from FanGraphs MiLB data
- **Tertiary:** Service time / option status from roster data

**Layer 3 (Counting Stats):**
- Derived from Layer 1 x Layer 2

**Layer 4 (SGP -> PAR -> Dollar Value):**
- **Primary:** Historical league standings (already collected in `data/historical_standings.csv`)
- **Secondary:** FanGraphs Auction Calculator as cross-check

### Recommended Tech Stack for Data Collection

**Python (pybaseball):**
- `batting_stats(start_season, end_season, qual=0, league='al')` -- season-level FanGraphs data filtered to AL
- `statcast(start_dt, end_dt)` -- pitch-level Statcast data
- `statcast_batter(start_dt, end_dt, player_id)` -- player-specific Statcast
- `batting_stats_bref(season)` -- Baseball Reference stats

**R (baseballr):**
- `fg_batter_leaders()` -- FanGraphs leaders
- `statcast_leaderboards()` -- Savant leaderboard data
- `fg_milb_batter_stats()` -- Minor league stats
- `mlb_player_info()` -- Player biographical data

**Direct CSV downloads:**
- FanGraphs leaderboards (Export button)
- Baseball Savant leaderboards and Statcast Search
- Lahman database
- Retrosheet event files

### Player ID Strategy

Use the **Chadwick Bureau register** as the master ID crosswalk. Every data source uses different player IDs:
- Statcast/Baseball Savant: MLBAM ID (numeric)
- FanGraphs: FanGraphs ID (numeric)
- Baseball Reference: BBRef ID (alphanumeric, e.g., "troutmi01")
- Lahman: Same as Retrosheet ID
- Retrosheet: Retrosheet ID (alphanumeric)

The Chadwick register maps all of these to each other. Build a master player lookup table first, then join all data sources on the appropriate ID.

---

## Appendix: Year-over-Year Stability of Key Metrics

Understanding which metrics are stable (skill) vs. volatile (luck) is critical for choosing prediction features.

| Metric | Stabilization Point (PA) | YoY Correlation | Implication |
|--------|--------------------------|-----------------|-------------|
| K% | ~60 PA | ~0.85 | **Highly stable** -- reliable predictor |
| BB% | ~120 PA | ~0.75 | **Stable** -- reliable predictor |
| HR/FB | ~300 PA | ~0.50 | **Moderately stable** -- partial regression needed |
| BABIP | ~800 BIP | ~0.35 | **Volatile** -- heavy regression to the mean |
| ISO | ~150 PA | ~0.70 | **Fairly stable** -- power is a reliable skill |
| Sprint Speed | ~10 competitive runs | ~0.90 | **Very stable** -- physical attribute |
| Barrel % | ~200 BBE | ~0.70 | **Fairly stable** -- consistent predictor |
| Exit Velocity | ~50 BBE | ~0.80 | **Very stable** -- physical attribute |
| Launch Angle | ~50 BBE | ~0.70 | **Fairly stable** -- swing path is consistent |
| xBA | ~200 PA | ~0.65 | **More stable than actual BA** -- better predictor |
| xwOBA | ~200 PA | ~0.70 | **More stable than actual wOBA** -- better predictor |
| SB Attempt Rate | ~100 PA on base | ~0.65 | **Moderately stable** -- depends on manager/context |
| Contact% | ~100 PA | ~0.80 | **Very stable** -- core skill |
| Chase Rate | ~200 pitches | ~0.75 | **Stable** -- plate discipline is consistent |
| Bat Speed | ~50 swings | ~0.90+ | **Very stable** -- physical attribute (NEW metric) |

**Key insight:** The most predictive features for rate stat models are the ones with high year-over-year stability. Volatile metrics like BABIP should be heavily regressed toward the mean, while stable metrics like K%, exit velocity, and sprint speed can be trusted at closer to face value.


---

# Part 2: Pitching Data Sources


> **League context:** AL-only, 10-team roto. Pitching categories: W, SV, ERA, WHIP, SO.
> **Model approach:** Predict rate stats, then scale by IP.
> **900 IP minimum** for ERA/WHIP to count.

---

## Table of Contents

1. [Baseball Savant / Statcast](#1-baseball-savant--statcast)
2. [FanGraphs](#2-fangraphs)
3. [Baseball Reference](#3-baseball-reference)
4. [MLB Stats API](#4-mlb-stats-api)
5. [Retrosheet](#5-retrosheet)
6. [Brooks Baseball](#6-brooks-baseball)
7. [Baseball Prospectus](#7-baseball-prospectus)
8. [Lahman Database](#8-lahman-database)
9. [Projection Systems](#9-projection-systems-steamer-zips-pecota-marcel)
10. [Park Factors](#10-park-factors)
11. [Catcher Framing](#11-catcher-framing-data)
12. [Defensive Quality](#12-defensive-quality-behind-pitchers)
13. [Bullpen Role / Closer Data](#13-bullpen-role--closer-data)
14. [Injury / Health Data](#14-injury--health-data)
15. [Minor League Data](#15-minor-league-data)
16. [Weather Data](#16-weather-data)
17. [Umpire Data](#17-umpire-data)
18. [Pitcher Aging Curves](#18-pitcher-aging-curves)
19. [R Packages](#19-r-packages)
20. [Python Packages](#20-python-packages)
21. [Other / Niche Sources](#21-other--niche-sources)
22. [Recommended Data Collection Priority](#22-recommended-data-collection-priority)

---

## 1. Baseball Savant / Statcast

**URL:** https://baseballsavant.mlb.com
**Historical depth:** Pitch-tracking from 2008 (PITCHf/x); full Statcast from 2015; bat tracking from 2024; swing path metrics from 2025.
**Access:** Web CSV export (25,000-row limit per query), pybaseball, baseballr, sabRmetrics R package, direct URL scraping of leaderboard pages.

### 1A. Pitch-Level Data (Statcast Search)

Every pitch thrown in MLB, roughly 700,000+ pitches per season, with 90+ columns per pitch.

| Field Category | Key Columns | Historical Depth |
|---|---|---|
| **Pitch identification** | pitch_type (FF, SL, CU, CH, SI, FC, KC, etc.), game_date, game_pk | 2008+ |
| **Velocity** | release_speed, effective_speed | 2008+ (PITCHf/x adjusted); 2017+ (Statcast native) |
| **Spin** | release_spin_rate, spin_axis | 2015+ (spin rate); 2020+ (spin axis reliable) |
| **Movement** | pfx_x (horizontal), pfx_z (vertical) | 2008+ |
| **Release point** | release_pos_x, release_pos_y, release_pos_z, release_extension | 2015+ (extension) |
| **Location** | plate_x, plate_z, zone (1-14 zone codes) | 2008+ |
| **Strike zone** | sz_top, sz_bot (batter-specific zone edges) | 2008+ |
| **Count state** | balls, strikes | 2008+ |
| **Batted ball outcome** | launch_speed (exit velo), launch_angle, hit_distance_sc, hc_x, hc_y | 2015+ |
| **Expected stats** | estimated_ba_using_speedangle, estimated_woba_using_speedangle | 2015+ |
| **Bat tracking** | bat_speed, swing_length | 2024+ |
| **Swing path** | attack_angle, swing_path, attack_direction | 2025+ |
| **Arm angle** | arm_angle | 2020+ |
| **Pitch result** | description (called_strike, swinging_strike, ball, foul, hit_into_play, etc.), events (strikeout, walk, single, home_run, etc.), type (S/B/X) | 2008+ |
| **Game context** | inning, inning_topbot, outs_when_up, on_1b/2b/3b, home_team, away_team | 2008+ |
| **Player IDs** | pitcher, batter, fielder_2 through fielder_9 | 2008+ |
| **Umpire** | umpire (ID for home plate umpire) | 2008+ |

**Relevance to prediction:**
- **ERA/WHIP:** Exit velocity against, launch angle against, xwOBA-against, barrel rate against, hard-hit rate against are the best Statcast predictors of future ERA. Expected stats strip out defense and luck.
- **SO:** Release speed, spin rate, movement profile, extension, and whiff rates on each pitch type are the best predictors of future K rate. Higher velocity + more vertical break on a fastball = more swings and misses. Spin-rate changes signal repertoire improvement or decline.
- **W:** Pitch quality data (velocity, movement) predicts run prevention; combined with team context, this feeds win estimates.
- **SV:** Same pitch quality data applies; pitch-level data can also identify high-leverage performance patterns.
- **Pitch mix changes:** Comparing year-over-year pitch usage percentages (e.g., throwing more sliders, adding a cutter) can signal breakouts or declines before traditional stats reflect it.

### 1B. Leaderboard Pages (Aggregated Pitcher Data)

Each leaderboard is accessible via URL and most can be scraped or downloaded as CSV.

| Leaderboard | URL Path | Key Metrics | Relevance |
|---|---|---|---|
| **Expected Stats** | /leaderboard/expected_statistics?type=pitcher | xBA-against, xSLG-against, xwOBA-against, xERA | Core ERA/WHIP prediction; xERA is the single best Statcast-based ERA estimator |
| **Pitch Arsenal Stats** | /leaderboard/pitch-arsenal-stats | Run value per pitch type, whiff%, put-away%, hard-hit% by pitch type | Identifies which pitches are elite vs. exploitable; directly feeds K rate and contact quality models |
| **Pitch Arsenal (Mix)** | /leaderboard/pitch-arsenals | Pitch usage % for each type, avg velocity, avg spin by type | Tracks repertoire changes; a pitcher adding a high-whiff pitch signals K improvement |
| **Pitch Movement** | /leaderboard/pitch-movement | Induced vertical break (IVB), horizontal break, velocity by pitch type | Movement profiles predict whiff rate and batted ball quality |
| **Arm Angle** | /leaderboard/pitcher-arm-angles | Arm angle at release by pitch type | Extreme arm angles create deception; relevant for K rate and BABIP |
| **Percentile Rankings** | /leaderboard/percentile-rankings?type=pitcher | Percentile ranks for K%, BB%, exit velo, whiff%, chase rate, barrel%, xERA, etc. | Quick snapshot of pitcher quality profile |
| **Custom Leaderboard** | /leaderboard/custom?type=pitcher | User-selected columns from full Statcast database | Build exactly the dataset needed |
| **Rolling xwOBA** | /leaderboard/rolling | Rolling 50/100/250 PA xwOBA | Identifies trend changes mid-season |
| **Swing/Take Run Values** | /leaderboard/swing-take | Run value on swings, takes, whiffs, called strikes | Decomposes value into swing inducement vs. called strike generation |
| **Year-to-Year** | /leaderboard/statcast-year-to-year | Year-over-year comparison of key metrics | Directly useful for identifying year-to-year changes for projection |
| **Pitcher Running Game** | /leaderboard/pitcher-running-game | Pickoff rates, stolen base rates allowed | Marginal for ERA (very small effect from SB allowed) |
| **Bat Tracking** | /leaderboard/bat-tracking | Bat speed, swing length against (for pitcher view) | New data (2024+); may predict contact quality against |

### 1C. Individual Pitcher Player Pages

Each pitcher's Baseball Savant page includes:
- Statcast zone charts (pitch location heatmaps by type)
- Movement profile charts
- Pitch-by-pitch rolling velocity charts
- Percentile rankings spider chart
- Game-by-game performance logs with Statcast data
- Pitch usage trends over time

---

## 2. FanGraphs

**URL:** https://www.fangraphs.com
**Historical depth:** Standard stats from 1871+; advanced stats from 2002+; Statcast integration from 2015+; PitchingBot (Stuff+/Location+/Pitching+) from 2020+.
**Access:** Web export (CSV, Members required for leaderboard export); pybaseball `pitching_stats()` pulls 334+ columns per player-season; baseballr `fg_pitcher_leaders()`.

### 2A. Standard Pitching Stats

| Stat | Description | Relevance |
|---|---|---|
| W, L, SV, HLD, BS | Wins, Losses, Saves, Holds, Blown Saves | Direct league categories (W, SV) |
| G, GS, CG, ShO | Games, Games Started, Complete Games, Shutouts | Playing time / role context |
| IP | Innings Pitched | Denominator for all rate stats; critical for 900 IP threshold |
| H, R, ER, HR | Hits, Runs, Earned Runs, Home Runs | Direct components of ERA |
| BB, IBB, HBP | Walks, Intentional Walks, Hit-By-Pitch | Direct components of WHIP |
| SO (K) | Strikeouts | Direct league category |
| ERA | Earned Run Average | Direct league category |
| WHIP | Walks + Hits per Inning Pitched | Direct league category |

### 2B. Advanced Pitching Stats

| Stat | Description | Relevance |
|---|---|---|
| **FIP** | Fielding Independent Pitching | Best simple ERA predictor; uses only K, BB, HR, HBP |
| **xFIP** | Expected FIP (normalizes HR/FB rate) | Better than FIP for projection; regresses HR/FB to league average |
| **SIERA** | Skill-Interactive ERA | Most predictive single-season ERA estimator; incorporates batted ball data, park factors |
| **K/9, BB/9, K/BB** | Rate stats per 9 innings | Core rate stat predictors; K/9 predicts SO, BB/9 predicts WHIP |
| **K%, BB%** | Per-PA rate stats | More stable than per-9 versions because they are not IP-denominated |
| **HR/9, HR/FB%** | Home run rates | Key ERA component; HR/FB regresses heavily toward league mean |
| **BABIP** | Batting Average on Balls in Play (against) | Regresses toward ~.300; deviation from expected BABIP signals luck |
| **LOB%** | Left on Base % | Regresses toward ~72%; high LOB% signals ERA inflation coming |
| **ERA-, FIP-, xFIP-** | Park-and-league adjusted versions (100 = average) | Essential for comparing AL pitchers across parks |
| **WAR (fWAR)** | Based on FIP; includes park, league, leverage adjustments | Overall value metric |
| **RA9-WAR** | Based on actual runs allowed | Captures what happened vs. what was "deserved" |

### 2C. Batted Ball Stats (Against)

Available from 2002+. Accessible via pitching leaderboard "Batted Ball" tab.

| Stat | Description | Relevance |
|---|---|---|
| **GB%** | Ground Ball % | Ground ball pitchers suppress HR; GB% predicts BABIP direction |
| **FB%** | Fly Ball % | Combined with HR/FB, predicts HR allowed -> ERA |
| **LD%** | Line Drive % | Line drives have ~.680 BA; LD% is highly predictive of BABIP |
| **IFFB%** | Infield Fly Ball % (as % of FB) | Pop-ups are ~automatic outs; treated like K in fWAR FIP |
| **HR/FB** | Home Run / Fly Ball rate | Key ERA driver; heavily regresses year-to-year |
| **GB/FB** | Ground Ball to Fly Ball ratio | Summary of batted ball profile |
| **Pull%, Cent%, Oppo%** | Directional batted ball data | Spray chart tendencies affect BABIP and defensive positioning |
| **Soft%, Med%, Hard%** | Contact quality tiers | Hard% against predicts future ERA and BABIP |

### 2D. Plate Discipline Stats (Against)

Available from 2002+. Leaderboard "Plate Discipline" tab.

| Stat | Description | Relevance |
|---|---|---|
| **O-Swing%** | Chase rate (swings outside zone / pitches outside zone) | Higher = more Ks, lower BBs -> predicts K rate and WHIP |
| **Z-Swing%** | In-zone swing rate | Baseline swing tendency |
| **Swing%** | Overall swing rate | Context for other discipline metrics |
| **O-Contact%** | Contact rate on chases | Lower = more whiffs on chases -> Ks |
| **Z-Contact%** | Contact rate on zone pitches | Lower = more whiffs in zone -> Ks |
| **Contact%** | Overall contact rate | Inverse predictor of K rate |
| **Zone%** | % of pitches in zone | Measures command; high zone% with low contact% = elite |
| **F-Strike%** | First-pitch strike % | Strongly predicts K rate and walk rate |
| **SwStr%** | Swinging strike rate (whiff per pitch) | Best single predictor of K rate |
| **CStr%** | Called strike rate | Measures command/deception; feeds WHIP prediction |
| **CSW%** | Called strikes + whiffs per pitch | Combined effectiveness metric |

### 2E. Pitch Type Stats and Values

Available from 2002+ (PITCHf/x era: 2007+). Leaderboard "Pitch Type" tab.

| Category | Metrics Available | Relevance |
|---|---|---|
| **Velocity by pitch** | vFA, vSI, vFC, vSL, vCU, vCH (average velocities) | Velocity trends predict K rate changes |
| **Usage % by pitch** | FA%, SI%, FC%, SL%, CU%, CH% | Pitch mix changes signal breakouts/declines |
| **Pitch values** | wFB, wSL, wCU, wCH (runs above average per 100 pitches by type) | Identifies which pitches are carrying or hurting a pitcher |
| **Pitch values /C** | wFB/C, wSL/C, etc. (per-100 pitch version) | Rate-stat version for comparison |

### 2F. PitchingBot / Stuff+ / Location+ / Pitching+

Available from 2020+. FanGraphs' proprietary pitch quality models. Leaderboard "PitchingBot" tab.

| Metric | Description | Relevance |
|---|---|---|
| **Stuff+** | Physical characteristics of each pitch (velocity, movement, spin, extension, release point); 100 = average | Predicts future K rate and contact quality; best single pitch-quality metric |
| **Location+** | Count-adjusted, pitch-type-adjusted command rating; 100 = average | Predicts walk rate and called strike rate -> WHIP |
| **Pitching+** | Combined model using physical characteristics + location + count; 100 = average | Overall process metric; best composite predictor |
| **Stuff+ by pitch type** | stFF, stSL, stCU, stCH, etc. | Identifies elite individual pitches; useful for pitch mix optimization |
| **Botch%** | Rate of badly located pitches | Predicts walks and hard contact -> ERA/WHIP |

### 2G. Splits Data

Accessible via Splits Leaderboard or individual player pages. Also accessible through pybaseball with the `month` parameter on `pitching_stats()`.

| Split Type | Description | Relevance |
|---|---|---|
| **vs LHH / vs RHH** | Performance against left-handed / right-handed hitters | Platoon splits affect ERA/WHIP; AL-only means facing AL lineups |
| **Home / Away** | Home vs. road performance | Park factor proxy; home/away ERA splits |
| **By month** | April, May, June, July, Aug, Sept, 1st Half, 2nd Half | Identifies fatigue effects; 2nd-half declines predict next year |
| **Day / Night** | Day game vs. night game | Minor effect on some pitchers |
| **High leverage / Low leverage** | Performance by leverage index | Critical for reliever evaluation |
| **Starter / Reliever** | Stats in each role | Essential when projecting role changes |
| **By batting order position** | Performance vs. lineup spots | Marginal but available |
| **Times through order** | 1st/2nd/3rd+ time facing lineup | Critical for starters; TTO penalty predicts IP limits and ERA inflation |

### 2H. Win Probability Stats

| Stat | Description | Relevance |
|---|---|---|
| **WPA** | Win Probability Added | Context-dependent performance value |
| **WPA/LI** | WPA adjusted for leverage | Context-neutral version |
| **REW** | Win expectancy from base-out changes | Captures run prevention in context |

---

## 3. Baseball Reference

**URL:** https://www.baseball-reference.com
**Historical depth:** Complete MLB stats from 1871+; game logs from 1901+; play-by-play from varies.
**Access:** Web scraping, pybaseball `pitching_stats_bref()`, `pitching_stats_range()`, baseballr `bref_daily_pitcher()`.

### 3A. Standard Pitching Stats

Same standard stats as FanGraphs (W, L, ERA, WHIP, K, etc.) but with different advanced metrics:
- **ERA+**: Park- and league-adjusted ERA (100 = average; higher = better)
- **bWAR**: Uses RA/9 (actual runs allowed) rather than FIP
- **Adjusted pitching runs**

### 3B. Game Logs

Game-by-game pitching lines for every pitcher, every season.

| Data Available | Relevance |
|---|---|
| Date, opponent, result, IP, H, R, ER, BB, K, HR, pitch count | Game-level granularity for modeling consistency, volatility, matchup effects |
| Game score | Single-number game quality summary |
| Cumulative season stats at each game | Tracks rate stat evolution through season |

### 3C. Pitcher Splits (Comprehensive)

Baseball Reference has the most comprehensive split tables:

| Split Category | Examples | Relevance |
|---|---|---|
| **Platoon** | vs LHB, vs RHB | ERA/WHIP/K rate by batter handedness |
| **Home/Road** | Home, Away, by specific ballpark | Park factor effects on pitcher |
| **Situational** | Runners on, RISP, bases loaded, by lead/deficit | Clutch performance, reliever evaluation |
| **Times through order** | 1st/2nd/3rd+ TTO | Starter effectiveness decay |
| **Leverage** | High/Medium/Low leverage | Reliever performance under pressure |
| **Inning** | By inning (1st through 9th+) | Fatigue effects within game |
| **Day/Night** | Day game, night game | Minor splits |
| **Count** | Ahead in count, behind, full count, first pitch | Approach analysis |
| **Month** | March-Oct, 1st half, 2nd half | Seasonal patterns |

### 3D. Relief Pitching Specific Data

| Stat | Description | Relevance |
|---|---|---|
| **IR (Inherited Runners)** | Baserunners inherited from previous pitcher | Affects ERA attribution |
| **IS (Inherited Runners Scored)** | How many inherited runners scored | Measures strand rate in relief |
| **Leverage Index (entering)** | Average leverage when entering game | Identifies high-leverage closers vs. mop-up |
| **SVO (Save Opportunities)** | Number of save chances | Directly predicts SV volume |
| **BS (Blown Saves)** | Failed save attempts | SV conversion rate |
| **Holds** | Middle relief save-like situations | Identifies setup men who might become closers |

### 3E. Reliever Pitching Leaderboards

Baseball Reference maintains annual leaderboards at `/leagues/majors/YYYY-reliever-pitching.shtml` with:
- Games finished, save opportunities, saves, blown saves
- Inherited runners, inherited runners scored
- Leverage index data
- Win probability added

---

## 4. MLB Stats API

**URL:** https://statsapi.mlb.com (official); https://docs.statsapi.mlb.com/ (documentation)
**Historical depth:** Complete historical MLB data.
**Access:** REST API (free, no authentication required); Python wrappers: `MLB-StatsAPI` (PyPI), `python-mlb-statsapi`; R: baseballr `mlb_pbp()`.

### 4A. Available Endpoints

| Endpoint | Data Returned | Relevance |
|---|---|---|
| **Game feed** | Pitch-by-pitch data with 100+ columns per pitch | Alternative to Savant for pitch-level data |
| **Player stats** | Career and season stats, splits | Standard pitching stats by player |
| **Team stats** | Team-level pitching and batting aggregates | Team offense data for W prediction |
| **Schedule** | Game schedules, probable pitchers, results | Maps pitchers to team context |
| **Standings** | Division/league standings | Team quality context |
| **Roster** | Active rosters, 40-man | Current role identification |
| **Draft** | Draft picks and signings | Prospect pedigree |

### 4B. Pitch-by-Pitch Data

The API provides ~100 columns per pitch including:
- Pitch type classification
- Velocity, spin rate, movement
- Pitch coordinates and zone
- Count, outs, runners on
- Event outcomes

**Note:** Does NOT include some Statcast-exclusive data like bat tracking, swing tracking, or arm angle. Baseball Savant remains the primary source for the full Statcast dataset.

---

## 5. Retrosheet

**URL:** https://www.retrosheet.org
**Historical depth:** Play-by-play from 1898-2024 (205,886+ games); box scores from 1871+; game logs from 1871+.
**Access:** Free CSV/event file downloads; pybaseball Lahman integration; R `retrosheet` package.

### 5A. Available Downloads

| Dataset | Format | Relevance |
|---|---|---|
| **Event files** | Custom format (parsed with Chadwick tools) | Every plate appearance with outcome, base/out state, fielding |
| **Game logs** | CSV | Team-level game results, winning/losing/saving pitcher, attendance, conditions |
| **pitching.csv** | CSV | Pitcher stats by game for every game 1898-2024 |
| **Parsed play-by-play** | CSV (16M+ rows) | Every play with full base-out-state context |

### 5B. Unique Data Points

- **Run support per start** (derivable from game logs): Critical for W prediction
- **Pitcher-specific game conditions**: Day/night, home/away, DH/no-DH
- **Complete game context**: Base-out state for every plate appearance -> custom leverage metrics
- **Historical depth**: Unmatched for studying long-term trends

---

## 6. Brooks Baseball

**URL:** https://www.brooksbaseball.net
**Historical depth:** PITCHf/x data from 2007+.
**Access:** Web interface (player card pages); no official API but scrapable.

### 6A. Unique Offerings

| Data | Description | Relevance |
|---|---|---|
| **Manually reclassified pitch types** | Brooks curators correct pitch classification errors | More accurate pitch mix data than raw Statcast |
| **Movement charts** | Visual pitch movement profiles with park normalization | Identifies true pitch quality vs. park-influenced readings |
| **Tabular pitch data** | Per-pitch-type velocity, movement, usage by count, by zone | Detailed arsenal analysis |
| **Release point tracking** | Release point consistency analysis | Release point changes can signal injury or mechanical adjustments |
| **Game-level pitch logs** | Detailed breakdown of each game appearance | In-game pitch sequencing analysis |

**Relevance:** Brooks Baseball's pitch reclassification and park-normalized movement data make it a valuable complement to raw Statcast data, especially for pitchers whose pitch types are misclassified by automated systems.

---

## 7. Baseball Prospectus

**URL:** https://www.baseballprospectus.com
**Historical depth:** DRA from 2015+; various metrics from 1950s+.
**Access:** Web (subscription required for full access); legacy leaderboards at legacy.baseballprospectus.com are free.

### 7A. Proprietary Pitching Metrics

| Metric | Description | Relevance |
|---|---|---|
| **DRA (Deserved Run Average)** | Mixed-model ERA estimator; controls for defense, park, catcher framing, opponent, umpire | Best "true talent" ERA estimator; isolates pitcher from context |
| **DRA-** | Scale-adjusted (100 = average, lower = better) | Cross-era comparison |
| **cFIP (contextual FIP)** | FIP with additional context adjustments | Enhanced FIP variant |
| **PWARP** | Pitcher Wins Above Replacement based on DRA | Overall value metric |
| **ArsenalPro / StuffPro** | Pitch quality model (similar to FanGraphs Stuff+) | Pitch-level quality assessment |
| **PitchPro** | Combined pitch quality + tunneling model | Incorporates pitch sequencing deception |

### 7B. Pitch Tunneling Data

Baseball Prospectus pioneered public pitch tunneling metrics (2017+):
- **Tunnel distance**: How far from the plate two consecutive pitches are distinguishable
- **Plate distance**: Separation at the plate
- **Tunnel differential**: Difference between tunnel point and plate point

**Relevance:** Tunneling is a strong predictor of whiff rate and deception. Pitchers who tunnel well get more swings and misses -> higher K rate, lower WHIP.

---

## 8. Lahman Database

**URL:** https://www.seanlahman.com/baseball-archive/statistics/
**Historical depth:** 1871-2024.
**Access:** R `Lahman` package (CRAN); pybaseball `download_lahman()` function; direct CSV download.

### 8A. Pitching Table

Season-level pitching stats for every pitcher in MLB history:
- W, L, G, GS, CG, SHO, SV, IP, H, ER, HR, BB, SO, ERA, etc.
- Also includes IBB, WP, HBP, BK, BFP (batters faced), GF (games finished)

### 8B. Other Relevant Tables

| Table | Relevance |
|---|---|
| **People** | Player demographics (birth year -> age), handedness |
| **Teams** | Team-level season data (runs scored -> run support for W) |
| **Parks** | Ballpark information |
| **Appearances** | Games at each position -> role identification |
| **AllstarFull** | All-Star selections (talent tier proxy) |
| **AwardsPlayers** | Cy Young, etc. |

**Relevance:** Lahman is the best source for long historical baselines. Useful for aging curves, historical rate stat distributions, and building priors for Bayesian models.

---

## 9. Projection Systems (Steamer, ZiPS, PECOTA, Marcel)

### 9A. Steamer

**Access:** FanGraphs projections page (free view, CSV for members); pybaseball `pitching_stats()` with `projection='steamer'`.
**Available:** Preseason and rest-of-season updates.
**Stats projected:** W, L, SV, G, GS, IP, K, BB, HR, ERA, WHIP, FIP, WAR, and more.
**Relevance:** Steamer's IP projection is useful as a playing time baseline. Its rate stat projections can serve as a comparison/ensemble input.

### 9B. ZiPS

**Access:** FanGraphs projections page (free view, CSV for members).
**Available:** Preseason and updated versions.
**Stats projected:** Same as Steamer plus percentile ranges.
**Relevance:** ZiPS uses player similarity for aging and regression, making it strong on breakout/decline candidates.

### 9C. Depth Charts (FanGraphs)

**Access:** FanGraphs projections page.
**Description:** Blends Steamer and ZiPS rate stats, then scales to playing time estimates by FanGraphs editors.
**Relevance:** The IP and role allocations in Depth Charts are the best public playing time estimates. Assumes ~1,500 team IP, ~200 IP for starters, ~65 IP for relievers. Essential for Layer 2 (playing time) of the model.

### 9D. PECOTA (Baseball Prospectus)

**Access:** Baseball Prospectus (Premium subscription required); downloadable spreadsheet.
**Description:** Uses player comparisons and aging curves. Provides percentile forecasts (10th, 25th, 50th, 75th, 90th).
**Relevance:** Percentile ranges are uniquely useful for modeling upside/downside risk, not just point estimates.

### 9E. Marcel

**Access:** Can be computed from Lahman data (simple weighted average of last 3 years + regression to mean).
**Description:** Baseline "no-skill" projection that weights recent performance.
**Relevance:** Useful as a baseline to beat; any model should outperform Marcel to demonstrate value.

---

## 10. Park Factors

### 10A. Sources

| Source | URL | Format | Relevance |
|---|---|---|---|
| **Baseball Savant** | /leaderboard/statcast-park-factors | Web/CSV | Statcast-era park factors based on batted ball data |
| **FanGraphs** | Park factor tables on team pages | Web | Multi-year regressed park factors; used in ERA-/FIP-/xFIP- |
| **Baseball Reference** | /about/parkadjust.shtml | Web | ERA+ adjustments by park |
| **FantasyPros** | /mlb/park-factors.php | Web | Fantasy-oriented park factors by stat |
| **EVAnalytics** | evanalytics.com/mlb/research/park-factors | Web | Statcast-based, batted-ball-derived factors |

### 10B. Park Factor Types

| Factor Type | Description | Relevance |
|---|---|---|
| **Overall runs** | How many more/fewer runs are scored in park vs. average | Directly adjusts ERA expectations |
| **HR factor** | HR frequency relative to average | Key for ERA; some parks inflate HR/FB |
| **Hits factor** | Hit frequency relative to average | Affects WHIP projections |
| **BB factor** | Walk frequency relative to average | Minor park effects on walks |
| **K factor** | Strikeout frequency relative to average | Minor park effects on Ks |
| **By handedness** | Factors split by LHB/RHB | Important for platoon-split modeling |

**Relevance:** Park factors are essential for adjusting ERA and WHIP projections. A pitcher moving from Yankee Stadium to Tropicana Field (or vice versa) will have a meaningfully different ERA projection. AL-only league means only 15 park factor sets matter.

---

## 11. Catcher Framing Data

### 11A. Sources

| Source | URL | Historical Depth | Relevance |
|---|---|---|---|
| **Baseball Savant** | /leaderboard/catcher-framing | 2015-present (full season); 2018+ (monthly, by pitch type, by pitcher hand) | Primary source |
| **Baseball Prospectus** | DRA accounts for catcher framing internally | 2015+ | Built into DRA |
| **FanGraphs** | Includes framing runs in WAR calculations | 2015+ | Integrated into metrics |

### 11B. Key Metrics

| Metric | Description | Relevance |
|---|---|---|
| **Shadow Strike %** | Called strike rate on borderline pitches | Measures catcher's ability to "steal" strikes |
| **Catcher Framing Runs** | Runs saved from extra called strikes (0.125 runs per strike) | Quantifies impact on pitcher's BB rate and K rate |
| **Strike Rate** | Overall called strike rate by catcher | Broad framing skill measure |
| **Framing by pitcher hand** | Framing splits for LHP vs RHP | Some catchers frame one side better |
| **Framing by zone area** | By glove-side, arm-side, high, low | Identifies specific strengths |

**Relevance to prediction:** A pitcher's catcher assignment directly affects walk rate and K rate. An elite framing catcher (e.g., +15 framing runs) can reduce a pitcher's BB/9 by ~0.3 and boost K/9 by a similar amount. This matters for WHIP projection, especially for pitchers with lots of borderline pitches. For the AL-only model, knowing which AL catchers are elite/poor framers is a significant edge.

---

## 12. Defensive Quality Behind Pitchers

### 12A. Sources

| Metric | Source | Historical Depth | Access |
|---|---|---|---|
| **OAA (Outs Above Average)** | Baseball Savant | 2016+ | Savant leaderboard, pybaseball |
| **UZR (Ultimate Zone Rating)** | FanGraphs | 2002+ | FanGraphs fielding leaderboard |
| **DRS (Defensive Runs Saved)** | FanGraphs (via Fielding Bible) | 2003+ | FanGraphs fielding leaderboard |
| **Def (Fielding component of WAR)** | FanGraphs | 2002+ | FanGraphs WAR tables |

### 12B. Application to Pitcher Projection

| Effect | Description | Magnitude |
|---|---|---|
| **BABIP impact** | Better defense -> lower BABIP-against | ~10-15 points of BABIP per +10 OAA |
| **ERA impact** | Better defense -> lower ERA (independent of FIP) | ~0.20-0.40 ERA per +10 OAA team-wide |
| **WHIP impact** | Better defense -> fewer hits -> lower WHIP | Proportional to BABIP effect |

**Relevance:** Team defensive quality is one of the largest non-pitcher factors in ERA and WHIP. FIP strips this out, but actual ERA (what matters for roto) does not. For pitchers with extreme GB% or FB% tendencies, the defensive effect is amplified.

---

## 13. Bullpen Role / Closer Data

### 13A. Sources

| Source | Data | URL |
|---|---|---|
| **FanGraphs RosterResource Closer Depth Charts** | Projected closers, setup men, committee situations; updated regularly | fangraphs.com/roster-resource/closer-depth-chart |
| **RotoWire Closers page** | Current closer designations | rotowire.com/baseball/closers.php |
| **RotoBaller Closer Depth Charts** | Daily-updated bullpen hierarchies | rotoballer.com |
| **FantraxHQ** | Closer rankings with handcuff recommendations | fantraxhq.com |
| **FanGraphs RosterResource Team Depth Charts** | Full bullpen hierarchy by team | fangraphs.com/roster-resource/depth-charts/{team} |

### 13B. Key Data Points for SV Prediction

| Factor | Source | Relevance |
|---|---|---|
| **Closer role security** | Depth chart sources above | Binary: is pitcher the closer? |
| **Team win total projection** | FanGraphs projections, Vegas win totals | More team wins = more SV opportunities |
| **Historical SV opportunity rate** | Baseball Reference | Teams typically get 45-55 SVO/season |
| **SV conversion rate** | Pitcher's historical BS/SVO | Typical ~85-92% for quality closers |
| **Committee risk** | Closer depth chart notes | Split saves = lower individual SV totals |

---

## 14. Injury / Health Data

### 14A. Sources

| Source | Data | Relevance |
|---|---|---|
| **FanGraphs RosterResource Injury Report** | Current IL designations, expected return dates | Playing time projection |
| **MLB.com Injury Report** | Official injury designations | Official source |
| **Sports Injury Central (sicscore.com)** | Detailed injury analysis, return timelines, historical injury data | Injury risk modeling |
| **Spotrac / Transaction logs** | IL stint history | Historical injury frequency |
| **FanGraphs player pages** | IP history year-by-year | Workload history for fatigue modeling |

### 14B. Key Injury Factors for IP Projection

| Factor | Description | Relevance |
|---|---|---|
| **Tommy John history** | UCL reconstruction | Returns typically at 60-80% IP in first year back |
| **Lat injuries** | Tend to cause longer-than-expected absences | Especially risky; 20/21 lat injuries in 2025 were pitchers |
| **Shoulder injuries** | Vary widely in severity | High variance in return timeline |
| **Prior IL stint frequency** | Number of IL stints in last 3 years | Best predictor of future IL time |
| **Age** | Older pitchers have higher injury risk | Interaction with workload |
| **Velocity decline** | Can signal subclinical injury | Early warning indicator from Statcast data |

---

## 15. Minor League Data

### 15A. Sources

| Source | Access | Data Available |
|---|---|---|
| **FanGraphs MiLB stats** | Web, baseballr `fg_milb_pitcher_game_logs()` | Game logs with 58 columns: IP, K, BB, ERA, FIP, etc. |
| **MiLB.com** | Web | Standard stats by level |
| **Baseball Savant MiLB** | Statcast search (MiLB data for select parks 2023+) | Pitch-level Statcast data for some MiLB games |
| **Baseball America** | Subscription | Prospect rankings, scouting reports, pitch grades |
| **Baseball Prospectus** | Subscription | MiLB stats + PECOTA projections for prospects |
| **FanGraphs "The Board"** | Free/subscription | Prospect rankings with tool grades, ETA |

### 15B. Relevance

Minor league data is essential for projecting:
- **Rookies entering the AL in 2026**: MiLB K rate, BB rate, and Statcast data (where available) are the only performance data available
- **Breakout candidates**: Pitchers who dominated upper minors may break out in MLB
- **Pitch development**: MiLB pitch-tracking data shows new pitch additions before MLB debut

---

## 16. Weather Data

### 16A. Sources

| Source | Data | Historical Depth |
|---|---|---|
| **FanGraphs** | Temperature, barometric pressure, elevation, air density, wind speed/direction per game | 2010+ (via OpenWeather) |
| **Retrosheet game logs** | Some weather/condition fields | Varies |
| **Baseball Savant** | Can be matched via game_pk | Pitch-level |

### 16B. Effects on Pitching

| Factor | Effect | Magnitude |
|---|---|---|
| **Temperature** | Warmer air = less dense = balls carry farther = more HR | ~1 HR/season per 10-degree increase (for home games) |
| **Altitude** | Higher elevation = less air resistance and less pitch movement | Colorado is extreme; other effects smaller |
| **Wind** | Wind out = more HR; wind in = fewer HR | Can change fly ball distance by 40+ feet |
| **Humidity** | Very low humidity slightly benefits pitchers | Small effect |

**Relevance:** Marginal for season-level projections but could matter for stadium-specific adjustments beyond standard park factors. Most useful for within-season adjustments.

---

## 17. Umpire Data

### 17A. Sources

| Source | Data | Access |
|---|---|---|
| **Baseball Savant** | Umpire ID embedded in pitch-level data | Statcast search; pybaseball |
| **Baseball Savant Edge% app** | Umpire tendencies by zone area since 2010 | Web |
| **Umpire IDs file** | Umpire assignments for games since 2008 | Can match to Savant downloads |
| **UmpScorecards (umpscorecards.com)** | Game-by-game umpire accuracy scorecards | Web |

### 17B. Relevance

- **Zone size variation**: Some umpires call a larger/smaller zone -> directly affects BB rate and K rate -> WHIP
- **Consistency**: More consistent umpires produce more predictable outcomes
- **Note:** As of 2025, the ABS challenge system is being implemented in MiLB. If/when it reaches MLB, umpire effects will diminish. Currently still relevant.

---

## 18. Pitcher Aging Curves

### 18A. Research Sources

| Source | Key Findings |
|---|---|
| **FanGraphs research** | Peak at ~27; rapid decline after 30 |
| **Baseball Prospectus "Delta Method Revisited"** | Improved aging curve methodology; peak at ~26.8 |
| **Yale (Ray Fair, updated April 2025)** | ERA decline rate at 37 is ~1.57% per year |
| **Statcast aging curves** | Fastball velocity peaks at 20-21, then gradual decline; K rate peaks at 22-28 |

### 18B. Component-Level Aging

| Component | Peak Age | Decline Pattern | Relevance |
|---|---|---|---|
| **Fastball velocity** | 20-21 | Gradual decline, ~0.5 mph/year after 30 | Drives K rate changes |
| **K rate** | 22-28 | Slow decline | Directly affects SO category |
| **BB rate** | 25-27 (best control) | Slight worsening with age | Affects WHIP |
| **HR rate** | 20-26 (lowest) | Increases with age | Affects ERA |
| **BABIP** | 20-22 (lowest) | Slight increase | Affects ERA/WHIP |
| **Overall ERA** | 26-29 | Accelerating decline after 30 | Core ERA prediction |

**Relevance:** Age adjustments should be applied to every pitcher's projection. The specific component being projected (K rate vs. BB rate vs. HR rate) ages differently, so the model should apply aging curves to each rate stat independently.

---

## 19. R Packages

| Package | Source | Key Pitching Functions |
|---|---|---|
| **baseballr** | CRAN; github.com/BillPetti/baseballr | `statcast_search()`, `fg_pitcher_leaders()`, `fg_pitcher_game_logs()`, `fg_milb_pitcher_game_logs()`, `bref_daily_pitcher()`, `mlb_pbp()`, `fip_plus()`, `scrape_statcast_savant_pitcher_all()` |
| **Lahman** | CRAN | `Pitching`, `PitchingPost`, `People`, `Teams`, `Parks`, `Appearances` tables |
| **sabRmetrics** | github.com/saberpowers/sabRmetrics | `download_baseballsavant()` (returns game/event/pitch/play tables) |
| **retrosheet** | CRAN/GitHub | Parse Retrosheet event files and game logs |

---

## 20. Python Packages

| Package | Source | Key Pitching Functions |
|---|---|---|
| **pybaseball** | PyPI; github.com/jldbc/pybaseball | See detailed function list below |
| **MLB-StatsAPI** | PyPI | `statsapi.player_stats()`, `statsapi.player_stat_data()`, `statsapi.get()` |
| **python-mlb-statsapi** | PyPI | Typed wrapper for MLB Stats API |
| **baseball-scraper** | PyPI | Fork of pybaseball with additional features |

### pybaseball Pitching Functions (Complete)

| Function | Source | Returns |
|---|---|---|
| `statcast(start_dt, end_dt)` | Baseball Savant | All pitch-level data across MLB |
| `statcast_pitcher(start_dt, end_dt, player_id)` | Baseball Savant | Pitch-level data for one pitcher |
| `pitching_stats(start_season, end_season)` | FanGraphs | 334+ columns per player-season (all FG stats) |
| `pitching_stats_bref(season)` | Baseball Reference | Season totals from B-Ref |
| `pitching_stats_range(start_dt, end_dt)` | Baseball Reference | Custom date range stats |
| `statcast_pitcher_expected_stats(year, minPA)` | Baseball Savant | xBA, xSLG, xwOBA, xERA against |
| `statcast_pitcher_pitch_arsenal(year, minP, arsenal_type)` | Baseball Savant | Pitch mix, avg speed, avg spin by type |
| `statcast_pitcher_arsenal_stats(year, minPA)` | Baseball Savant | Run value, whiff%, put-away% by pitch type |
| `statcast_pitcher_exitvelo_barrels(year, minBBE)` | Baseball Savant | Exit velo, barrel rate, hard-hit rate against |
| `statcast_pitcher_percentile_ranks(year)` | Baseball Savant | Percentile rankings for key metrics |
| `statcast_pitcher_active_spin(year, minP)` | Baseball Savant | Active spin data by pitch type |
| `statcast_pitcher_pitch_movement(year, minP)` | Baseball Savant | Pitch movement data |
| `statcast_pitcher_spin_dir_comparison(year)` | Baseball Savant | Spin direction comparisons between pitches |
| `team_pitching(start_season, end_season)` | FanGraphs | Team-level pitching stats |
| `team_batting(start_season, end_season)` | FanGraphs | Team offense (for run support -> W) |
| `schedule_and_record(season, team)` | Baseball Reference | Game-by-game results with W/L pitcher |
| `standings(season)` | Baseball Reference | Division standings |
| `playerid_lookup(last, first)` | Chadwick Bureau | Cross-reference IDs between systems |
| `download_lahman()` | Lahman DB | Full Lahman database tables |

---

## 21. Other / Niche Sources

### 21A. Pitcher List

- Weekly updated pitcher rankings (The List)
- Pitch-level grades and analysis
- Top 200/400 SP and RP rankings
- **Access:** Web (free)
- **Relevance:** Expert consensus rankings as model comparison/validation

### 21B. FanGraphs Auction Calculator

- Converts projections to dollar values using customizable league settings
- **Access:** Web (free)
- **Relevance:** Benchmark for dollar value model output

### 21C. Vegas Lines / Win Totals

- Team win totals from sportsbooks (e.g., FanDuel, DraftKings, BetMGM)
- **Access:** Various odds sites
- **Relevance:** Best market estimate of team quality -> W and SV opportunity prediction

### 21D. Pitcher Workload / Fatigue Data

Derivable from Statcast and game log data:
- Pitch count per game trend
- Velocity decline within games and across season
- Acute-to-chronic workload ratios (ACWR)
- **Relevance:** Predicts second-half decline, injury risk, and IP limits

### 21E. Spring Training Statcast Data

- Available from Baseball Savant starting 2023+ (expanded with ABS system)
- Velocity changes from prior season are highly "sticky" and predictive
- Pitch movement characteristics barely vary between spring and regular season
- **Relevance:** Early signal for velocity gains/losses, new pitch additions, and mechanical changes. Spring FIP is NOT predictive of regular-season FIP, but spring velocity IS predictive.

### 21F. Times Through the Order (TTO) Penalty

Derivable from pitch-level data or FanGraphs splits:
- Pitchers face significant performance decline 3rd+ time through order
- Average: +.015 wOBA 2nd time, +.035 wOBA 3rd time vs. 1st time
- **Relevance:** Predicts IP limits for starters; starters with small TTO penalty are more valuable (more IP at quality rate)

---

## 22. Recommended Data Collection Priority

### Tier 1: Essential (Collect First)

| Data | Source | Why |
|---|---|---|
| Season-level pitching stats (334+ columns) | FanGraphs via pybaseball `pitching_stats()` | Comprehensive feature set for all rate stat models |
| Expected stats (xERA, xwOBA, xBA, xSLG against) | Savant via pybaseball `statcast_pitcher_expected_stats()` | Best single predictor of future ERA |
| Stuff+, Location+, Pitching+ | FanGraphs via pybaseball `pitching_stats()` | Best pitch quality metrics for K rate and ERA prediction |
| Pitch arsenal stats (whiff%, run value by pitch) | Savant via pybaseball `statcast_pitcher_arsenal_stats()` | Pitch-level quality for K rate and contact quality |
| Team offensive stats (for run support) | FanGraphs via pybaseball `team_batting()` | Essential for W prediction |
| Closer depth charts / role data | FanGraphs RosterResource | Essential for SV prediction |
| Park factors | FanGraphs, Savant | ERA/WHIP/HR adjustment |
| Projection system data (Steamer, ZiPS, Depth Charts) | FanGraphs | IP estimates and comparison baselines |

### Tier 2: High Value (Collect Second)

| Data | Source | Why |
|---|---|---|
| Pitch-level Statcast data | Savant via pybaseball `statcast_pitcher()` | Granular features: velocity trends, movement changes, pitch mix |
| Catcher framing data | Savant catcher framing leaderboard | BB rate adjustment for WHIP |
| Team defensive quality (OAA, UZR) | Savant and FanGraphs | ERA/WHIP adjustment for BABIP effect |
| Pitcher splits (vs LHH/RHH, home/away, monthly) | FanGraphs splits leaderboard | Contextual performance variation |
| Pitcher game logs | FanGraphs, B-Ref | Consistency/volatility modeling |
| Reliever-specific stats (IR, SVO, LI) | Baseball Reference | SV and reliever ERA modeling |
| Injury history / IL stints | FanGraphs RosterResource | IP projection |
| Aging curve adjustments | Derived from historical data (Lahman + FanGraphs) | Age-based regression |

### Tier 3: Enhancement (Collect for Edge)

| Data | Source | Why |
|---|---|---|
| Pitch movement profiles by type | Savant via pybaseball | Detailed pitch quality assessment; detects changes |
| Active spin data | Savant via pybaseball | Spin efficiency affects movement quality |
| Arm angle data | Savant leaderboard | Deception effects on K rate and BABIP |
| Pitch tunneling data | Baseball Prospectus | Deception effect on whiff rate |
| Minor league stats | FanGraphs via baseballr | Rookie projections |
| Spring training velocity data | Savant | Early-season breakout signals |
| Umpire tendencies | Savant (derivable) | Minor BB rate adjustment |
| Weather data | FanGraphs (game-level) | Minor ERA adjustment |
| Times through order splits | FanGraphs splits | IP quality modeling for starters |
| Workload / fatigue indicators | Derived from Statcast | Second-half decline prediction |
| Vegas team win totals | Sportsbook odds | Market-based team quality for W/SV |
| Bat tracking data against | Savant (2024+) | Contact quality assessment (new, limited history) |

---

## Key Insight: Rate Stat Prediction Hierarchy

For the model's rate-stat-first approach, here is the recommended predictor hierarchy by category:

### ERA Prediction
1. xERA (Statcast expected ERA)
2. SIERA (FanGraphs; most predictive backward-looking estimator)
3. xFIP (FanGraphs; normalizes HR/FB)
4. FIP (FanGraphs; fielding independent)
5. Stuff+/Pitching+ (FanGraphs; process-based)
6. Hard-hit rate against, barrel rate against (Statcast)
7. GB% (FanGraphs; batted ball profile)
8. Park factors
9. Team defensive quality (OAA/UZR)
10. Catcher framing (BB rate adjustment)
11. BABIP regression (current BABIP vs. expected)
12. LOB% regression (current LOB% vs. expected)
13. Age adjustment

### WHIP Prediction
1. BB% (walks per PA; directly feeds WHIP denominator)
2. BABIP-against (expected vs. actual; drives hit rate)
3. Location+ (FanGraphs; command metric)
4. F-Strike% (first pitch strike rate)
5. SwStr% / CSW% (whiff + called strike rate)
6. xBA-against (Statcast; expected hit rate)
7. Catcher framing (BB rate adjustment)
8. Team defensive quality
9. Park factors (hits factor)
10. LD% against (line drives -> hits)

### SO (Strikeout) Prediction
1. K% (strikeouts per PA; most stable rate stat)
2. SwStr% (swinging strike rate per pitch)
3. Stuff+ (FanGraphs; pitch quality model)
4. Whiff rate by pitch type (Savant)
5. Fastball velocity
6. O-Swing% (chase rate)
7. O-Contact% (contact rate on chases)
8. Pitch movement profile (IVB, horizontal break)
9. Extension
10. Spin rate
11. Age adjustment (K rate peaks 22-28)

### W (Wins) Prediction
1. Team projected offense / run support
2. Pitcher ERA projection (from above)
3. IP projection (starter vs. reliever, health)
4. Team win total projection (Vegas)
5. Historical formula: W% = 0.112(RS) - 0.105(ERA) + 0.446 (R-squared = 0.827)

### SV (Saves) Prediction
1. Closer role assignment (binary: is closer?)
2. Role security (committee vs. clear closer)
3. Team projected win total (more wins = more SVO)
4. Historical SV opportunity rate (~45-55 per team per season)
5. Pitcher SV conversion rate (historical BS/SVO)
6. Health / IP projection

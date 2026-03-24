# Saves (SV) Prediction

Research for projecting saves in the Moonlight Graham AL-only rotisserie league.

---

## 2. SAVES (SV) Prediction

### 2.1 The Fundamental Nature of Saves

**Saves are primarily about ROLE, not skill.** A save requires:
1. The pitcher enters with a lead of 3 runs or fewer (most common scenario)
2. He finishes the game without losing the lead
3. He pitches at least one inning (in the typical case)

This means SV prediction decomposes into two completely separate problems:
1. **Who will be the closer?** (role identification)
2. **How many save opportunities will they get?** (opportunity volume)
3. **What percentage will they convert?** (conversion rate)

### 2.2 Save Opportunity Modeling

**SV Opportunities = f(team wins, game score distribution, closer usage)**

FanGraphs regression analysis found:
- **Runs scored** explained the most variance in save opportunities (R-squared = 0.12)
- **Bullpen FIP** explained ~5.5% of variance (R-squared = 0.055)
- **Combined model** (bullpen FIP + runs scored): only ~13% of variance explained
- The strongest positive correlation with saves is team wins, but the relationship is "pretty weak"

**Typical team save opportunity ranges:**
- Teams generate roughly 35-50 save opportunities per season
- Elite closers (on good teams) can see 40-45+ save opportunities
- Bad teams may generate 25-35 save opportunities
- Francisco Rodriguez's 2008 record: 69 save opportunities (extreme outlier)

**For an AL-only league:** Must estimate save opportunities for each of the 15 AL teams based on:
- Projected team win total
- Projected runs scored (teams that win close games generate more save situations)
- Bullpen quality (better bullpens preserve more leads)

### 2.3 Save Conversion Rate (SV%)

**League average SV% is approximately 66-70%** across all teams combined (includes committee situations, non-closers getting chances, etc.)

**For established closers:**
- Minimum acceptable: 80-85% to keep the job
- Good closers: 85-90%
- Elite closers: 90%+
- All-time greats: Mariano Rivera .890, Trevor Hoffman .888, Eric Gagne .962 (peak)

**SV% is NOT a stable, repeatable skill** in the way K% is. Research suggests saves have "not been determined to be a special, repeatable skill -- rather simply a function of opportunities." This means:
- Don't over-weight prior year SV% in projections
- Regress heavily toward the typical closer SV% (~85%)
- ERA and WHIP provide some signal for conversion ability

### 2.4 Closer Identification and Role Stability

**This is the most critical and hardest part of SV prediction.**

**Closer turnover rate:**
- **33-50% of closing situations experience turnover in a given season**
- Over a two-year window (2023-2024), only 4 out of 30 teams had the same closer throughout
- Relief pitchers spent 16,481 days on the IL in 2024 -- the most of any position
- Injury is the primary driver of closer changes, followed by ineffectiveness

**Implications for modeling:**
- Pre-season closer designations are unreliable for ~1/3 to 1/2 of teams
- Must identify backup closers ("handcuffs") for risk assessment
- Committee situations are increasingly common

**Resources for closer tracking:**
- [Closer Monkey](https://closermonkey.com/) -- real-time closer change alerts
- [FanGraphs RosterResource Closer Depth Charts](https://www.fangraphs.com/roster-resource/closer-depth-chart)
- [Closer Confidential grading system](https://athlonsports.com/fantasy/closer-confidential) -- numerical confidence scores

Source: [FanGraphs What Teams Provide the Most Saves](https://fantasy.fangraphs.com/what-kinds-of-teams-provide-the-most-saves/); [Hardball Times: Are Saves Predictable?](https://tht.fangraphs.com/are-saves-predictable/)

### 2.5 Recommended Rate Stat for Layer 1

The rate stat for saves is inherently multi-layered:

**SV = Role_Probability x SV_Opportunities x SV_Conversion_Rate**

Where:
1. **Role_Probability** = probability of being the primary closer (binary-ish: 0, 0.5 for committee, 1.0)
2. **SV_Opportunities** = team-level projection based on projected team wins and runs scored
3. **SV_Conversion_Rate** = ~85% default, adjusted slightly by pitcher quality (ERA, WHIP)

Then multiply by share of team's save opportunities that go to this pitcher.

### 2.6 Fantasy-Specific Considerations (AL-Only Roto)

- **SAGNOF principle** ("Saves Ain't Got No Face"): closers are fungible; don't overpay
- In a 10-team AL-only league, there are roughly 15 AL teams, so ~15 potential closers but only ~10-12 reliable ones
- The scarcity premium is real but volatile
- Committee situations split saves and reduce individual value dramatically
- **ZiPS and THE BAT do not project saves at all** -- they leave it to depth chart editors

Source: [Razzball SAGNOF](https://razzball.com/razzball-glossary-entry-of-the-day-sagnof/)

---

## 4. Major Projection Systems: W/SV/SO Methods

### 4.1 Steamer

- **W:** Uses Pythagorean formula with projected ERA and team run support. Prorated via FanGraphs depth charts. Steamer has beaten other systems by "significant margins" in W projection accuracy.
- **SV:** Relies on FanGraphs depth chart closer designations for role identification, then projects opportunity volume
- **SO:** Uses pitch-tracking data plus weighted historical K rates
- **IP:** Prorated to FanGraphs RosterResource playing time projections; assumes starters pitch every 4.5 days, relievers every 2.5 days; total team IP ~1,500

Source: [MLB.com Steamer Glossary](https://www.mlb.com/glossary/projection-systems/steamer); [Beyond the Box Score projection guide](https://www.beyondtheboxscore.com/2016/2/22/11079186/projections-marcel-pecota-zips-steamer-explained-guide-math-is-fun)

### 4.2 ZiPS (Dan Szymborski)

- **W:** Uses simulation-based approach -- a million season simulations produce team-level W distributions. ZiPS does NOT purely use FIP for ERA; it estimates how much of the ERA-FIP gap is attributable to the pitcher based on historical patterns. Does not produce playing-time-adjusted projections by default (uses FanGraphs depth charts when displayed there).
- **SV:** ZiPS does NOT project saves directly -- it leaves role assignment to depth chart editors.
- **SO:** Uses 3-4 years of weighted performance data. Relies on DIPS theory (regresses BABIP toward league average with individual adjustment). Incorporates velocity and injury data.
- **IP:** Uses growth/decline curves by player type. Factors velocities and injury data.

Source: [MLB.com ZiPS Glossary](https://www.mlb.com/glossary/projection-systems/szymborski-projection-system); [FanGraphs ZiPS category](https://blogs.fangraphs.com/category/2026-zips-projections/)

### 4.3 Marcel (Tom Tango)

The "minimum level of competence" baseline. Any good system should beat Marcel.

- **Methodology:** 3 years weighted 5/4/3, regressed to league average, age-adjusted
- **Regression constant:** 1200 (for pitchers, adjusted by sample size of weighted PA/BF)
- **W/SV/SO:** All projected using the same generic weighted-average + regression framework. No special handling for wins or saves.
- **Key value:** Serves as a benchmark. If your model can't beat Marcel, something is wrong.

Source: [Baseball-Reference Marcel](https://www.baseball-reference.com/about/marcels.shtml); [FanGraphs Projection Rundown](https://library.fangraphs.com/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/)

### 4.4 PECOTA (Baseball Prospectus)

- **Methodology:** Comparable-player based. Finds historical players with similar age/performance profiles and projects based on their trajectories.
- **K%/BB% are the most predictive inputs** "by a considerable margin" for pitcher projections
- Uses a weaker version of DIPS theory (assigns variance to luck, skill, and defense)
- **2025-2026 innovation:** Integrates StuffPro (boosted tree pitch quality model) for projecting balls in play. Strikeouts and walks "largely speak for themselves as-is" after regression.
- Uses 3-year performance windows matched against comparable historical pitchers
- **W/SV:** Derived from team-level simulation after individual rate projections

Source: [Baseball Prospectus PECOTA 2025](https://www.baseballprospectus.com/news/article/96300/pecota-week-pecota-2025-an-introduction/); [PECOTA Wikipedia](https://en.wikipedia.org/wiki/PECOTA)

### 4.5 THE BAT / THE BAT X (Derek Carty)

- **Methodology:** Comprehensive system with regression to mean, multiple weighted seasons, aging curves, minor league equivalencies, park factors, platoon splits. THE BAT X adds Statcast data.
- **Track record:** "Most accurate standalone projection system in fantasy baseball" for 6+ consecutive years (FanGraphs and FantasyPros studies)
- **W/SV:** Not publicly documented in detail
- **K:** Utilizes Statcast pitcher data for the most recent versions

Source: [FanGraphs THE BAT X Introduction](https://fantasy.fangraphs.com/introducing-the-bat-x/); [Derek Carty site](https://derekcarty.com/the_bat.html)

### 4.6 ATC (Average Total Cost)

- **Methodology:** Weighted average of multiple projection systems, where weights are optimized per-stat based on historical accuracy. NOT a simple average -- each system gets different weights for different stats.
- **Example:** System A might get 20% weight for HR but 5% for K, while System B gets 10% for HR but 2% for K
- **For pitchers:** Incorporates ZiPS, Steamer, FANS, plus prior 3 years of MLB stats
- **Track record:** Ranked as most accurate projections by FantasyPros for 5+ consecutive years
- **Volatility metrics:** Also provides inter-projection standard deviation (InterSD) to quantify how much systems disagree on a player -- valuable for identifying upside/risk

Source: [FanGraphs ATC Projection System](https://fantasy.fangraphs.com/the-atc-projection-system/); [FantasyPros 2025 accuracy](https://www.fantasypros.com/2026/02/most-accurate-fantasy-baseball-projections-2025-results/)

### 4.7 Key Takeaway Across Systems

**Consensus/aggregated projections consistently outperform individual systems.** The most accurate systems tend to be aggregators (ATC, FanGraphs Depth Charts, FantasyPros Consensus). This is the "wisdom of crowds" effect -- averaging removes individual system biases.

## 5. Innings Pitched Prediction

IP projection is the critical bridge between rate stats and counting stats. It affects W, SV, and SO volume.

### 5.1 Year-to-Year IP Correlation

**IP has a year-to-year correlation of only r = 0.42** -- in the bottom half of pitcher metrics. Injuries are the primary reason for instability.

### 5.2 FanGraphs Depth Chart Approach

- Assumes ~1,500 total team innings per season
- Starting pitchers prorated for ~200 IP, relievers for ~65 IP
- Starters assumed to pitch every 4.5 days, relievers every 2.5 days
- Injuries dock expected playing time
- Vacancies cascade innings down the depth chart
- FanGraphs Depth Charts = 50/50 blend of Steamer and ZiPS, prorated to RosterResource playing time

### 5.3 Steamer600 Alternative

For rate-stat comparison purposes, Steamer600 gives every SP 200 IP and every RP 65 IP. This removes playing time uncertainty and isolates rate-stat talent.

### 5.4 Age Effects on IP

- **IP peaks at age 27** and declines consistently thereafter
- Velocity peaks in early 20s and declines ~1 mph by age 26, then steeper decline into 30s
- **K/9 doesn't decline until age 32** for SP, age 31 for RP (K rate holds up longer than other skills)
- Rapid decline in overall effectiveness begins at age 30
- Older pitchers increasingly project as relievers rather than starters

Source: [FanGraphs Pitcher Aging Curves](https://blogs.fangraphs.com/pitcher-aging-curves-starters-and-relievers/)

### 5.5 Injury Risk and Workload

**Conflicting research on workload-injury relationship:**
- No clear association between cumulative innings/pitches and DL placement in several studies
- However, pitcher injury history and pitch count ARE predictive of future injury
- The number of **pitches** (not innings) is the more relevant workload metric
- Increasing from 160 to 200 IP at age 24 adds ~1% elbow injury risk at age 25

**Best predictors of pitcher injury:**
1. Previous injury history
2. Number of pitches thrown in prior season
3. Age
4. BMI and physical characteristics

Source: [PubMed workload study](https://pubmed.ncbi.nlm.nih.gov/29861301/); [Harvard Sports Analysis Collective](https://harvardsportsanalysis.org/2016/01/predicting-pitcher-injuries/)

### 5.6 Recommendation for the Model

IP projection is inherently uncertain. The best approach:
1. Start with a baseline (3-year weighted average of prior IP)
2. Apply age adjustment (decline curve after 27)
3. Apply injury risk factor (prior injury history, workload)
4. Apply role adjustment (SP vs. RP, rotation spot, closer vs. setup)
5. For the AL-only context, use FanGraphs depth charts or team-specific information to allocate innings

---

## Key Research Conclusions

### 8.2 Can SV Be Predicted?

**Partially.** Save *opportunities* are loosely tied to team quality (~13% of variance explained). Save *conversion* is modestly tied to pitcher quality but is not a stable, repeatable skill. The biggest uncertainty is **role assignment** -- 33-50% of closers change in-season. SV prediction is primarily a **role prediction** problem, not a performance prediction problem.

### 9.3 SV (Saves)

**Rate stat:** SV/G or SV per opportunity
**Prediction approach:**
1. **Identify closer role** (manual input or from depth chart data)
2. **Estimate team save opportunities** based on projected team wins and runs scored
3. **Estimate closer share** of team save opportunities (~80-90% for clear closers, 40-60% for committees)
4. **Apply conversion rate:** ~85% default, adjusted modestly by pitcher quality
5. **SV = Role_share x Team_SVO x Conversion_rate**
6. **Monitor in-season** for role changes (this is where the most value is lost/gained)

---

## Sources

## Sources

- [Beyond the Box Score: Year-to-Year SP Correlations](https://www.beyondtheboxscore.com/2012/1/9/2690405/what-starting-pitcher-metrics-correlate-year-to-year)
- [FanGraphs: Basically Every Pitching Stat Correlation](https://blogs.fangraphs.com/tool-basically-every-pitching-stat-correlation/)
- [FanGraphs: Sample Size / Stabilization](https://library.fangraphs.com/principles/sample-size/)
- [FanGraphs: Reliability Update](https://blogs.fangraphs.com/a-long-needed-update-on-reliability/)
- [FanGraphs: Projecting the Impossible - Pitcher Wins](https://fantasy.fangraphs.com/projecting-the-impossible-pitcher-wins/)
- [FanGraphs: Estimating Wins Using ERA and Run Support](https://fantasy.fangraphs.com/estimating-wins-using-era-and-run-support/)
- [FanGraphs: Definitive xK% Formula](https://fantasy.fangraphs.com/the-definitive-pitcher-expected-k-formula/)
- [FanGraphs: Updated xK% 2017](https://fantasy.fangraphs.com/introducing-the-new-pitcher-xk-updated-for-2017/)
- [FanGraphs: What Teams Provide the Most Saves](https://fantasy.fangraphs.com/what-kinds-of-teams-provide-the-most-saves/)
- [FanGraphs: The Impact of Team Wins on Saves](https://fantasy.fangraphs.com/the-impact-of-team-wins-on-saves/)
- [FanGraphs: Projection Systems](https://library.fangraphs.com/principles/projections/)
- [FanGraphs: ATC Projection System](https://fantasy.fangraphs.com/the-atc-projection-system/)
- [FanGraphs: Pitcher Aging Curves](https://blogs.fangraphs.com/pitcher-aging-curves-starters-and-relievers/)
- [FanGraphs: Contextualizing SwStr%](https://fantasy.fangraphs.com/contextualizing-the-swinging-strike-rate/)
- [FanGraphs: Closer Depth Chart](https://www.fangraphs.com/roster-resource/closer-depth-chart)
- [FanGraphs: Velocity and K/9](https://blogs.fangraphs.com/velocity-and-k9/)
- [FanGraphs: THE BAT X Introduction](https://fantasy.fangraphs.com/introducing-the-bat-x/)
- [Hardball Times: Are Saves Predictable?](https://tht.fangraphs.com/are-saves-predictable/)
- [Hardball Times: Predicting Reliever Wins](https://tht.fangraphs.com/predicting-reliever-wins/)
- [Baseball Prospectus: PECOTA 2025 Introduction](https://www.baseballprospectus.com/news/article/96300/pecota-week-pecota-2025-an-introduction/)
- [Baseball Prospectus: PECOTA 2026 Updates](https://www.baseballprospectus.com/news/article/104636/pecota-2026-updates-and-ongoing-challenges/)
- [Baseball Prospectus: StuffPro Introduction](https://www.baseballprospectus.com/news/article/89245/stuffpro-pitchpro-introduction-new-pitch-metrics-bp/)
- [Baseball Prospectus: Pitcher Stats Stabilization](https://www.baseballprospectus.com/fantasy/article/14293/resident-fantasy-genius-when-pitchers-stats-stabilize/)
- [Mastersball: Projection Process Pitchers](https://mastersball.com/index.php?option=com_content&view=article&id=5573)
- [MLB.com: Steamer Glossary](https://www.mlb.com/glossary/projection-systems/steamer)
- [MLB.com: ZiPS Glossary](https://www.mlb.com/glossary/projection-systems/szymborski-projection-system)
- [MLB.com: Marcel Glossary](https://www.mlb.com/glossary/projection-systems/marcel-the-monkey-forecasting-system)
- [MLB.com: PECOTA Glossary](https://www.mlb.com/glossary/projection-systems/player-empirical-comparison-and-optimization-test-algorithm)
- [MLB.com: Third Time Through Order](https://www.mlb.com/glossary/miscellaneous/third-time-through-the-order-penalty)
- [MLB.com: Save Percentage](https://www.mlb.com/glossary/standard-stats/save-percentage)
- [MLB.com: Pitch Timer](https://www.mlb.com/glossary/rules/pitch-timer)
- [MIT Sloan: K Rate Prediction from Pitch Characteristics](https://www.sloansportsconference.com/research-papers/predicting-major-league-baseball-strikeout-rates-from-differences-in-velocity-and-movement-among-player-pitch-types)
- [Driveline: Stuff+ Explainer](https://www.drivelinebaseball.com/2021/12/what-is-stuff-quantifying-pitches-with-pitch-models/)
- [Driveline: Fastball Spin Rate](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/)
- [Baseball-Reference: Marcel](https://www.baseball-reference.com/about/marcels.shtml)
- [Beyond the Box Score: Projection Guide](https://www.beyondtheboxscore.com/2016/2/22/11079186/projections-marcel-pecota-zips-steamer-explained-guide-math-is-fun)
- [Beyond the Box Score: K Prediction Using Velocity and Whiffs](https://www.beyondtheboxscore.com/2013/5/8/4313020/predicting-strikeouts-using-velocity-and-whiff)
- [AZ Snake Pit: CSW% Analysis](https://www.azsnakepit.com/2022/5/31/23145793/called-strike-plus-whiff-rate-how-can-we-use-it-to-determine-pitcher-performance)
- [FantasyPros: 2025 Projection Accuracy](https://www.fantasypros.com/2026/02/most-accurate-fantasy-baseball-projections-2025-results/)
- [Razzball: SAGNOF](https://razzball.com/razzball-glossary-entry-of-the-day-sagnof/)
- [TDS: Baseball and ML Part 2](https://towardsdatascience.com/baseball-and-machine-learning-part-2-a-data-science-approach-to-2021-pitching-projections-530dbfe6dcc4/)
- [GitHub: MLBStrikeoutRatePrediction](https://github.com/chrisjackson4256/MLBStrikeoutRatePrediction)
- [PubMed: Workload and Injury](https://pubmed.ncbi.nlm.nih.gov/29861301/)
- [Harvard Sports Analysis: Pitcher Injuries](https://harvardsportsanalysis.org/2016/01/predicting-pitcher-injuries/)
- [Closer Monkey](https://closermonkey.com/)

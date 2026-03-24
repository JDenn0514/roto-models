# Wins (W) Prediction

Research for projecting pitcher wins in the Moonlight Graham AL-only rotisserie league.

---

## 1. WINS (W) Prediction

### 1.1 Why Wins Are Hard to Predict

Pitcher wins are among the least predictable stats in baseball. The core problem is that a win is a *team outcome* attributed to an individual.

**Year-to-year correlation of W: only r = 0.29**
- For comparison, K/9 year-to-year correlation is r = 0.70, FIP is r = 0.65, ERA is r = 0.45
- Run support per 9 innings has a year-to-year correlation of only r = 0.16, meaning the offensive support a pitcher receives is nearly random from year to year
- W/GS correlates with ERA at only R-squared = 0.213 -- ERA explains roughly 21% of wins per game started variance

Source: [Beyond the Box Score year-to-year correlation study](https://www.beyondtheboxscore.com/2012/1/9/2690405/what-starting-pitcher-metrics-correlate-year-to-year); [FanGraphs pitching stat correlation tool](https://blogs.fangraphs.com/tool-basically-every-pitching-stat-correlation/)

**Factors that determine pitcher wins:**
1. **Pitcher's own performance** (ERA/FIP) -- necessary but insufficient
2. **Run support** (team offense quality) -- largely outside pitcher's control
3. **Bullpen quality** -- can blow leads after starter exits
4. **Defense** -- affects hits/runs allowed
5. **Innings per start** -- going deeper = more chances to be pitcher of record
6. **Decision rate** -- only ~70% of starts result in a W or L decision

### 1.2 Approaches to W Rate Prediction

#### 1.2.1 The Pythagorean Approach (Used by Steamer, Mastersball, others)

This is the dominant method used by major projection systems. Bill James' Pythagorean expectation, originally designed for teams, is adapted for individual pitchers:

**Formula:**
```
W% = RS^1.83 / (RS^1.83 + RA^1.83)
```
Where RS = runs scored (run support) and RA = runs allowed by the pitcher.

**Application to individual pitchers (Mastersball process):**
1. Project the pitcher's ERA -> convert to runs allowed per game
2. Add a bullpen component (runs allowed by relievers after SP exits)
3. Estimate team run support (based on projected team offense)
4. Apply Pythagorean formula to get expected W%
5. Calculate decisions: proportional to projected innings (IP / (9 x 162))
6. W = W% x Decisions

**Steamer's approach:** Uses ERA and expected run support via the Pythagorean formula. Steamer beat other systems "by significant margins" in wins projection accuracy.

Source: [Mastersball Projection Process: Pitchers](https://mastersball.com/index.php?option=com_content&view=article&id=5573); [Steamer methodology at MLB.com](https://www.mlb.com/glossary/projection-systems/steamer)

#### 1.2.2 Linear Regression Approach

A simpler but effective approach from FanGraphs:

**Formula:**
```
Projected Winning % = 0.112 * (Run Support) - 0.105 * (ERA) + 0.446
R-squared = 0.827
```

This shows both run support and ERA are essential -- the model explains ~83% of winning percentage variance among qualified starters.

**Alternative (FanGraphs "Projecting the Impossible"):**
```
Actual Pitcher Win% = 0.282 - 0.0585 * (proj ERA) + 0.646 * (proj team W%)
R-squared = 0.15
```
This lower R-squared used only projected (not actual) values, showing the difficulty of pre-season prediction. Key finding: **team winning percentage matters more than pitcher talent** for predicting wins. The difference between pitching on a winning vs. losing team is roughly 1.5 wins.

Source: [Estimating Wins Using ERA and Run Support](https://fantasy.fangraphs.com/estimating-wins-using-era-and-run-support/); [Projecting the Impossible: Pitcher Wins](https://fantasy.fangraphs.com/projecting-the-impossible-pitcher-wins/)

#### 1.2.3 ERA Bucket Approach

A non-parametric method: bucket pitchers by projected ERA in 0.25 increments, then separate by projected winning/losing team record. Finding: a pitcher with 4.50 projected ERA on a winning team earns roughly as many W as a 3.50 ERA pitcher on a losing team.

#### 1.2.4 Quality Start Rate as a W Proxy

Quality starts (6+ IP, 3 or fewer ER) are more predictable than wins because they remove run support and bullpen variance. However, the QS-to-W conversion rate varies substantially:
- Many pitchers with 20+ quality starts had only 9-14 wins
- QS neutralizes run support effects but doesn't directly predict wins

Source: [Quality Start Glossary](https://www.mlb.com/glossary/standard-stats/quality-start)

### 1.3 Key Drivers of W Rate

**Rank order of importance for a rate model:**
1. **Team run support** (team offensive quality, park-adjusted)
2. **Pitcher ERA/FIP** (lower = more wins, but only ~21% of variance)
3. **Innings per start** (deeper into games = more decisions, more W eligible)
4. **Bullpen quality** (good pen protects leads)
5. **League/division context** (competitive balance affects run differentials)

### 1.4 Recommended Rate Stat for Layer 1

**W/GS (Win Rate Per Game Started)** is the natural rate stat, but it is unstable. A better approach:

1. **Project ERA** (or FIP-based ERA estimate)
2. **Project team run support** (from team offensive projections, AL-only context)
3. **Apply Pythagorean formula** to get W% per decision
4. **Project decisions per start** (~0.70 historically)
5. **W/GS = W% x decisions_per_start**

Then in Layer 3: Total W = W/GS x projected GS

### 1.5 Relief Pitcher Wins

RP wins are essentially unpredictable and should be treated differently:

**Key findings from Hardball Times research:**
- **IP is the strongest predictor** of RP wins (r = 0.75 with total wins, r = 0.31 with W/G)
- **gmLI (game leverage index)** matters: high-leverage relievers are positioned to pick up vulture wins more often
- **xFIP** is the best performance metric for RP win prediction (better than ERA or runs allowed)
- **Team offense and SP quality** have almost no bearing on RP wins (r-squared near zero)
- Closer status has minimal effect on RP win rates

**Practical approach:** Project RP wins as a function of IP and leverage role. For most relievers, project 2-5 wins per season. Do not overthink this -- it is largely noise.

Source: [Predicting Reliever Wins - Hardball Times](https://tht.fangraphs.com/predicting-reliever-wins/)

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

## Machine Learning Approaches

### 6.1 XGBoost for Pitcher Stat Prediction

A Towards Data Science study used XGBoost regression to predict 11 pitching stats (IP, W, L, SV, BS, HLD, HRA, K, ERA, WHIP, dollar value):
- Used 10-fold cross-validation with MAE scoring
- **Key finding:** "Great at predicting the middle, but terrible at nailing down the outliers" -- and outliers are what fantasy managers care about most
- XGBoost yielded the best forecasts overall, especially with advanced metrics

Source: [TDS: Baseball and ML Part 2](https://towardsdatascience.com/baseball-and-machine-learning-part-2-a-data-science-approach-to-2021-pitching-projections-530dbfe6dcc4/)

### Feature Importance: Wins

**For pitcher win prediction:**
1. Team winning percentage
2. ERA / FIP
3. Innings pitched
4. Run support

### 6.4 Limitations of ML Approaches

- Outlier prediction remains the key weakness
- Playing time uncertainty swamps rate-stat prediction quality
- Most ML approaches don't clearly outperform well-tuned weighted-average systems for season-level projections
- Where ML helps most: pitch-level models aggregated to season-level K rate projections

### 7.2 Shift Ban

- Increased BABIP slightly (more hits getting through)
- Primarily affects hitter stats and pitcher ERA/BABIP, not K rates
- Some indirect effect on pitcher wins (slightly more runs scored overall)

### 7.3 Modeling Implications

For K prediction: **No significant adjustment needed** for post-2023 data. K rates have been stable across the rule change.

For W prediction: Slight increase in league-wide run scoring may affect W distributions, but the effect is modest.


## Key Research Conclusions

### 8.1 How Predictable Are W Really?

**Not very.** Year-to-year r = 0.29. Even the best models (Pythagorean with actual run support) explain only ~83% of in-season W% variance. Pre-season prediction with projected values drops to R-squared ~0.15. The best approach is the Pythagorean method with team-context inputs, but 2-3 win prediction error per pitcher is likely the floor.

### 9.2 W (Wins)

**Rate stat:** W/GS (derived, not directly modeled)
**Prediction approach:**
1. **Project ERA** (from the ERA/WHIP model)
2. **Project team run support** (from AL team offensive projections)
3. **Apply Pythagorean formula:** W% = RS^1.83 / (RS^1.83 + RA^1.83)
4. **Project decisions per start:** ~0.70 baseline, adjusted by IP/GS (deeper starters get more decisions)
5. **W/GS = W% x decisions_per_start**
6. **For RP:** Use IP and leverage role to estimate 2-5 W per season
7. **Conversion to counting stat:** W = W/GS x projected GS (or W/G x G for RP)

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

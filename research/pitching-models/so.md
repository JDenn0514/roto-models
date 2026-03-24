# Strikeouts (SO / K) Prediction

Research for projecting strikeout rates and totals in the Moonlight Graham AL-only rotisserie league.

---

## 3. STRIKEOUTS (SO / K) Prediction

### 3.1 Why K Rate Is the Most Predictable Pitching Stat

**K% year-to-year correlation: r = 0.70** (among the highest for any pitching stat)
- Compare: ERA r = 0.31-0.45, FIP r = 0.46-0.65, BABIP r = ~0.20, W r = 0.29

**K% stabilization: ~70 batters faced** (roughly 15-20 IP)
- This is remarkably fast -- one of the quickest-stabilizing stats in baseball
- BB% stabilizes at ~170 BF, ERA at ~950 BF, BABIP at ~2000 BIP (about 3 full seasons)
- The signal-to-noise ratio crosses 0.707 (more signal than noise) at the stabilization point
- "The first 200 PA are much more important than the second 200 PA for understanding K%"

**Why K% stabilizes quickly:** Strikeouts measure a near-pure batter-pitcher interaction (contact avoidance). Unlike BABIP, which involves defense, direction, weather, and luck, K% depends almost entirely on the pitcher's ability to generate swings-and-misses and called strikes.

Source: [FanGraphs Sample Size](https://library.fangraphs.com/principles/sample-size/); [FanGraphs Reliability Update](https://blogs.fangraphs.com/a-long-needed-update-on-reliability/); [Camden Depot K% stabilization](http://camdendepot.blogspot.com/2017/04/strikeout-rate-stabilization-and-time.html)

### 3.2 Traditional K Rate Predictors

#### 3.2.1 Swinging Strike Rate (SwStr%)

**SwStr% is the single best traditional predictor of K%.**
- Correlation between SwStr% and K% for starters (100+ IP): r = 0.87
- Whiff% (closely related to SwStr%) explains ~70% of K% variance (R-squared ~0.70)
- **Rule of thumb:** Double a pitcher's SwStr% to approximate K%
  - 8% SwStr% -> ~15% K%
  - 10% SwStr% -> ~18% K%
  - 12% SwStr% -> ~22% K%
  - 16% SwStr% -> ~30% K%

Source: [Fantistics SwStr% Introduction](https://www.insiderbaseball.com/blog/2020/02/an_introduction_to_swinging_strike_rate_swstr_and_how_to_get_an_edge.html); [FanGraphs Contextualizing SwStr%](https://fantasy.fangraphs.com/contextualizing-the-swinging-strike-rate/)

#### 3.2.2 CSW% (Called Strikes + Whiffs)

- CSW% correlates with K% at R-squared ~0.59
- Stabilizes after ~10 starts for SP
- Weaker than SwStr%/Whiff% alone, but captures called strike ability

Source: [AZ Snake Pit CSW Analysis](https://www.azsnakepit.com/2022/5/31/23145793/called-strike-plus-whiff-rate-how-can-we-use-it-to-determine-pitcher-performance)

#### 3.2.3 First-Pitch Strike Rate (FPS%)

- 25.3% of PA starting with a first-pitch strike end in K, vs. 18.6% for first-pitch ball
- 69% of all strikeouts start with first-pitch strikes
- FPS% has modest additive predictive value beyond SwStr%

Source: [FanGraphs F-Strike%](https://blogs.fangraphs.com/get-to-know-f-strike/)

#### 3.2.4 Fastball Velocity

- Velocity alone explains ~23% of K rate variance (R-squared ~0.23)
- Important but far from sufficient -- "about 1/4 of what needs to be accounted for"
- Velocity is likely the biggest single physical factor

Source: [FanGraphs Velocity and K/9](https://blogs.fangraphs.com/velocity-and-k9/)

#### 3.2.5 Chase Rate (O-Swing%)

- Counterintuitively, O-Swing% (chase rate) has **almost zero predictive power** for K% on its own (R-squared near zero)
- However, O-Contact% (contact rate on pitches outside the zone) is highly predictive (R-squared > 0.67)
- The distinction matters: getting batters to chase is useless for K prediction unless those chases result in whiffs

Source: [FanGraphs Plate Discipline](https://library.fangraphs.com/offense/plate-discipline/)

#### 3.2.6 Pitch Mix Effects

- **Slider** is the secondary pitch most correlated with K rate (highest whiff rate)
- **Curveball** is second
- **Changeup** grade is "almost useless" for predicting K rate
- **Fastball** correlates most among all pitch types (r = 0.35) -- but still modest alone
- Breaking balls outside the zone generate swinging strikes at 11.4% on 0-0 counts vs. 3.8% for fastballs

Source: [FanGraphs Prospect Pitch Grades & K Rate](https://fantasy.fangraphs.com/prospect-scouting-stats-pitcher-pitch-grades-strikeout-rate/)

### 3.3 The Definitive xK% Formula

FanGraphs developed regression-based expected K% formulas:

**Original formula (R-squared = 0.892):**
```
xK% = -0.61 + (L/Str * 1.1538) + (S/Str * 1.4696) + (F/Str * 0.9417)
```

**Updated 2017 formula (R-squared = 0.913):**
```
xK% = -0.8432 + (Str% * 0.2916) + (L/Str * 1.2689) + (S/Str * 1.5334) + (F/Str * 0.9672)
```

Where:
- **L/Str** = Looking Strike % (called strikes / total strikes)
- **S/Str** = Swinging Strike % (whiffs / total strikes)
- **F/Str** = Foul Ball Strike % (fouls / total strikes)
- **Str%** = Overall Strike % (strikes / total pitches)

**Key insight:** S/Str (swinging strike rate) has the largest coefficient, confirming whiff ability as the dominant driver. L/Str matters more than one might expect (called strikes contribute meaningfully).

Source: [FanGraphs Definitive xK% Formula](https://fantasy.fangraphs.com/the-definitive-pitcher-expected-k-formula/); [FanGraphs Updated xK% 2017](https://fantasy.fangraphs.com/introducing-the-new-pitcher-xk-updated-for-2017/)

### 3.4 Statcast-Based K Models

#### 3.4.1 Stuff+

- Stuff+ provides a location-agnostic pitch quality evaluation
- Uses pitch velocity, movement, spin rate to grade individual pitches
- Scaled to 100 (league average); above 100 = better "stuff"
- Primarily predicts whiffs and run value
- **PECOTA 2025/2026** integrates StuffPro (Baseball Prospectus's version) into pitcher projections, improving accuracy by 341+ runs in back-testing
- Stuff+ correlates with K rate but is **not a replacement** for observed K% in projections -- it adds signal especially for pitchers with small sample sizes or mechanics changes

Source: [Driveline Stuff+ explainer](https://www.drivelinebaseball.com/2021/12/what-is-stuff-quantifying-pitches-with-pitch-models/); [Baseball Prospectus StuffPro](https://www.baseballprospectus.com/news/article/89245/stuffpro-pitchpro-introduction-new-pitch-metrics-bp/)

#### 3.4.2 Pitch Velocity, Spin Rate, and Movement

- **Fastball velocity:** explains ~23% of K rate variance; peak velocity even more important
- **Spin rate:** Positive connection with swing-and-miss rate and fly ball rate. At 93-95 mph, hitters post .399 wOBA against <2000 RPM but only .253 against 2800+ RPM (146 wOBA point gap)
- **Pitch movement:** Both maximum vertical movement AND range of vertical movement among a pitcher's pitches are key K% predictors -- more so than speed changes or number of pitch types
- **Arsenal relationships:** The *relationships among all pitches* matter more than any single pitch's characteristics

Source: [MIT Sloan conference paper on K prediction](https://www.sloansportsconference.com/research-papers/predicting-major-league-baseball-strikeout-rates-from-differences-in-velocity-and-movement-among-player-pitch-types); [Driveline Spin Rate](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/); [FanGraphs High-Spin Fastballs](https://blogs.fangraphs.com/more-spin-more-problems-hitter-performance-against-high-spin-fastballs/)

#### 3.4.3 Multi-Variable Regression Models

Combining Statcast features yields strong K prediction:
- Whiff% alone: R-squared ~0.70-0.81 (varying by study)
- Whiff% + FPS% + fastball velocity: R-squared = 0.737
- Strike type decomposition (L/Str, S/Str, F/Str, Str%): R-squared = 0.913
- An improved multi-variable model achieved R-squared = 0.88 (8% improvement over whiff alone)
- MIT Sloan paper: **median absolute error of 2.47 percentage points** from actual K% using pitch clustering + velocity + movement features

Source: [Beyond the Box Score K prediction](https://www.beyondtheboxscore.com/2013/5/8/4313020/predicting-strikeouts-using-velocity-and-whiff)

### 3.5 SP vs. RP K Rate Differences

Relievers consistently have higher K rates than starters:
- **Relievers average ~3% higher K% and ~1% higher BB% than starters**
- **K/9 gap is roughly 3-4 points** (structural, not talent-based)

**Why:** Short stints allow maximum velocity and effort per pitch. Starters conserve energy to go deeper into games. Relievers throw harder, generate more whiffs.

**Implication for modeling:** When a pitcher transitions between SP and RP roles, adjust K rate expectations accordingly. SP-to-RP converts should see K% increase; RP-to-SP converts should see it decrease.

Source: [FanGraphs Get to Know K/9](https://blogs.fangraphs.com/get-to-know-k9/); [FanGraphs Rate Stats](https://library.fangraphs.com/pitching/rate-stats/)

### 3.6 Third Time Through the Order Penalty (TTOP) and K Rate

- OPS+ jumps from 91 to 117 the third time batters face a pitcher
- K rate declines in later innings as TTOP kicks in (hitter familiarity, not just fatigue)
- The effect is driven more by **familiarity** than fatigue
- Modern bullpen management pulls starters earlier, which inflates their apparent K/9 (they exit before the TTOP penalty fully manifests)

**Modeling implication:** Pitchers who go deeper into games will have slightly lower K/9 due to TTOP. This interacts with IP projection -- high-IP starters may have marginally lower K rates.

Source: [Third Time Through Order Penalty - MLB Glossary](https://www.mlb.com/glossary/miscellaneous/third-time-through-the-order-penalty)

### 3.7 Recommended Rate Stat for Layer 1

**K/PA (or equivalently K%) is the natural rate stat.** It is highly stable, well-understood, and benefits from strong Statcast-era predictors.

**Best predictive model for K% (choose based on data availability):**

**Tier 1 (most accurate, requires pitch-level data):**
```
xK% = -0.8432 + (Str% * 0.2916) + (L/Str * 1.2689) + (S/Str * 1.5334) + (F/Str * 0.9672)
```

**Tier 2 (strong, requires SwStr% or Whiff%):**
```
K% ~ 2 * SwStr% (approximate)
-- or --
xK% from Whiff% regression (R-squared ~0.70-0.81)
```

**Tier 3 (baseline, requires only prior K%):**
```
Weighted average of prior years' K% (Marcel-style: 5/4/3 weights), regressed toward league mean
```

Then in Layer 3: Total SO = K_rate x BF (batters faced), where BF is derived from IP projection.

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

## 6. Machine Learning Approaches

### 6.1 XGBoost for Pitcher Stat Prediction

A Towards Data Science study used XGBoost regression to predict 11 pitching stats (IP, W, L, SV, BS, HLD, HRA, K, ERA, WHIP, dollar value):
- Used 10-fold cross-validation with MAE scoring
- **Key finding:** "Great at predicting the middle, but terrible at nailing down the outliers" -- and outliers are what fantasy managers care about most
- XGBoost yielded the best forecasts overall, especially with advanced metrics

Source: [TDS: Baseball and ML Part 2](https://towardsdatascience.com/baseball-and-machine-learning-part-2-a-data-science-approach-to-2021-pitching-projections-530dbfe6dcc4/)

### 6.2 K Rate Prediction via ML

**MIT Sloan Sports Analytics Conference paper (Eric P. Martin):**
- Used 2.5 million pitches from 402 pitchers (2012-2017)
- Model-based clustering grouped each pitcher's pitches by velocity and movement
- **Median absolute error: 2.47 percentage points** from actual K%
- **Most important features:** Maximum pitch velocity, strike rate, vertical movement range
- Key insight: *arsenal relationships* matter more than individual pitch characteristics

**GitHub: MLBStrikeoutRatePrediction:**
- Uses Linear Regression, Random Forest, AdaBoost, XGBoost
- Clusters pitches by speed and movement, then predicts seasonal K rates
- [github.com/chrisjackson4256/MLBStrikeoutRatePrediction](https://github.com/chrisjackson4256/MLBStrikeoutRatePrediction)

**Medium article on RP K% prediction:**
- Uses XGBoost in R with Statcast data, pitch clustering, and situational data (leverage index, platoon advantage)
- Combines three types of data: Statcast pitch metrics, situational data, and pitch type clustering

Source: [MIT Sloan paper](https://www.sloansportsconference.com/research-papers/predicting-major-league-baseball-strikeout-rates-from-differences-in-velocity-and-movement-among-player-pitch-types); [Medium RP K% prediction](https://medium.com/@lukevh/predicting-reliever-strikeout-percentage-7c4e3c6fde88)

### 6.3 Feature Importance Findings (across studies)

**For K rate prediction:**
1. Swinging strike rate / Whiff% (dominant feature)
2. Maximum pitch velocity
3. Strike rate / zone rate
4. Vertical movement range
5. Pitch arsenal diversity (secondary)

**For game win prediction:**
1. FIP (high predictive value)
2. OPS / OBP (team offense)
3. WHIP (pitcher effectiveness)

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

## 7. Impact of 2023 Rule Changes

### 7.1 Pitch Clock

- Games ~30 minutes shorter on average
- **K% impact: minimal** -- 2023 K rate (22.7%) essentially unchanged from 2022 (22.4%)
- "Strikeouts have thus far proved impervious to change"
- Pitchers with pitch clock experience showed slightly higher K/9, but no other stats significantly affected
- Stolen bases increased dramatically (reduced pickoff attempts)

### 7.2 Shift Ban

- Increased BABIP slightly (more hits getting through)
- Primarily affects hitter stats and pitcher ERA/BABIP, not K rates
- Some indirect effect on pitcher wins (slightly more runs scored overall)

### 7.3 Modeling Implications

For K prediction: **No significant adjustment needed** for post-2023 data. K rates have been stable across the rule change.

For W prediction: Slight increase in league-wide run scoring may affect W distributions, but the effect is modest.

Source: [MLB Pitch Timer Glossary](https://www.mlb.com/glossary/rules/pitch-timer); [The Ringer analysis](https://www.theringer.com/2023/05/05/mlb/rule-changes-2023-strikeout-rate-balls-in-play)

## Key Research Conclusions

### 8.3 Is K Rate the Most Predictable Pitching Stat?

**Yes.** Year-to-year r = 0.70, stabilizes in ~70 BF, and can be predicted with median absolute error of ~2.5 percentage points using pitch-level models. The accuracy ceiling for K% prediction appears to be R-squared ~0.91 using the FanGraphs xK% formula with strike-type decomposition.

### 8.4 Summary: Predictability Ranking

| Stat | Y2Y Correlation | Stabilization (BF) | Best Model R-squared | Predictability |
|------|----------------|--------------------|-----------------------|---------------|
| K% | 0.70 | ~70 | 0.91 | **High** |
| BB% | 0.65 | ~170 | ~0.60 | Moderate-High |
| FIP | 0.46-0.65 | ~200 | ~0.50 | Moderate |
| ERA | 0.31-0.45 | ~950 | ~0.40 | Moderate-Low |
| W | 0.29 | N/A | 0.15-0.83* | **Low** |
| SV | N/A (role-dependent) | N/A | ~0.13 (opportunities) | **Very Low** |
| BABIP | ~0.20 | ~2000 BIP | ~0.15 | Very Low |

*W R-squared depends heavily on whether actual or projected run support is used

### 9.1 K (Strikeouts)

**Rate stat:** K/BF (= K%)
**Prediction approach:**
1. **Primary model:** Weighted historical K% (3 years, 5/4/3 weights) regressed toward league mean
2. **Statcast overlay:** Use xK% formula or Whiff%-based regression to identify pitchers whose K% should change
3. **Adjustment factors:** SP/RP role, age (decline after 32), pitch mix changes, velocity changes
4. **Conversion to counting stat:** K = K/BF x projected BF (derived from IP projection x ~4.3 BF/IP)

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

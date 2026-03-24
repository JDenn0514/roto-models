# Stolen Base Rate Prediction (SB/PA)

Research for projecting SB rates in the Moonlight Graham AL-only rotisserie league.

---

## 4. STOLEN BASE Rate Prediction (SB/PA)

### 4.1 The 2023+ Rule Change Revolution

Three rule changes in 2023 fundamentally altered the stolen base landscape:

1. **Larger bases:** Increased from 15 inches to 18 inches per side (3 inches larger in both dimensions).
2. **Pickoff limits:** Pitchers limited to **2 disengagements** (step-offs or pickoff throws) per plate appearance. A third disengagement that fails to record an out results in a balk.
3. **Pitch clock:** Reduced to 18 seconds with runners on (from 20), 15 seconds with bases empty. The clock reduces a pitcher's ability to vary timing.

#### Statistical Impact
| Metric | Pre-2023 (2022) | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| SB per game | ~0.46 | ~0.72 | ~0.73 | Similar |
| Total league SB | ~2,486 | ~3,503 | ~3,617 | Tracking higher |
| Success rate | 75-76% | ~79-80% | ~78-79% | ~78.8% |

- SB increased by approximately **40-45%** from 2022 to 2023.
- The 2024 season saw **3,617 SB** -- the most since the 1910s.
- Success rates jumped 3-4 percentage points and have remained elevated.
- The biggest factor: **pickoff limits** -- fewer throws over means bigger leads and more confident attempts.
- 2024 saw defensive adjustments: catcher pop times improved, pitchers threw over more strategically, but the new baseline held.

### 4.2 Sprint Speed and SB Prediction

#### Sprint Speed as a Predictor
- Correlation between sprint speed and successful SB per SB opportunity: **r = 0.6** (moderate-strong).
- Correlation between sprint speed and BsR (baserunning runs): **R-squared = 0.244** (speed explains only ~25% of total baserunning value).
- Faster runners are **more likely to attempt** steals (moderate correlation).
- Faster runners are **more likely to succeed**, but at a **smaller magnitude** than their attempt rate advantage.
- A baserunner's success rate correlates **weakly** with sprint speed -- other factors (jump, timing, reads) matter significantly.

#### Sprint Speed Aging Curve
- Speed peaks **very young** -- among qualified players in 2017:
  - 78.5% of players age 27 and under had above-average sprint speed (27 ft/sec).
  - 47.5% of ages 28-32 were above average.
  - Only 15.2% of ages 33+ were above average.
- An average runner slows approximately **1 inch per second per year**, beginning almost immediately upon debut.
- Year-to-year: 23% of players lost at least 0.5 ft/sec; only 7% gained at least 0.5 ft/sec.
- **Speed declines before stolen bases do** -- a player's willingness and baserunning instincts can partially compensate for declining speed.

#### Sprint Speed Stabilization
- Sprint speed is relatively stable year-to-year for most players.
- The measurement captures peak speed over a runner's fastest 1-second window.

### 4.3 Opportunity-Based SB Model

The canonical SB projection framework:

```
Projected SB = Opportunities x Attempt Rate x Success Rate
```

#### Opportunities
- **SBO% (Stolen Base Opportunity Average)** = (1B + BB + HBP) / TPA.
- More nuanced: a stolen base opportunity is a plate appearance where a runner on 1st sees 2nd unoccupied, or a runner on 2nd sees 3rd unoccupied, for at least one pitch.
- Opportunities depend on how often a player reaches base (OBP-driven) and the base state when they reach.

#### Attempt Rate (Takeoff Rate)
- **More stable** than success rate from year to year.
- Correlated moderately with sprint speed (faster runners attempt more often).
- Heavily influenced by **managerial philosophy** and **team/front office strategy**.
- Few players have a true "green light" to run on their own; most attempts are called from the dugout.
- **SBA% (stolen base attempt rate)** is the percentage of opportunities where an attempt is made.

#### Success Rate
- **More volatile** than attempt rate (small sample sizes within a single season).
- Success rate correlates **weakly** with sprint speed.
- Players with high success rates one year often see their **attempt rate drop** the next year (regression).
- For projections, rely on **multiple years** of data, not just the prior season.
- Post-2023 league-wide success rate is approximately **78-80%**, up from ~75%.

#### Practical Projection Example
```
SB Opportunities: 70 (based on projected reaching base)
Attempt Rate: 34% (based on sprint speed, manager, team philosophy)
Success Rate: 87% (based on sprint speed + historical rate)
Projected SB: 70 x 0.34 x 0.87 = ~20.7 SB
```

### 4.4 Managerial and Strategic Factors

- **Front offices have more impact** on stolen base rate than managers.
- Manager philosophy is "ultimately the most crucial factor" for projecting baserunning fantasy value.
- The analytics era has **rehabilitated the stolen base** -- after two decades of decline, SB is back as a valued asset since 2023.
- Team-level SB rates reflect organizational philosophy more than individual player decisions.
- When projecting SB, consider the player's team and that team's SB aggressiveness.

### 4.5 Pitcher and Catcher Effects

- **Pitchers have a bigger influence** on the running game than catchers ("you steal off the pitcher, not the catcher").
- Average MLB catcher pop time on steal attempts of 2nd base: **2.0 seconds**.
- Catcher CS% is **dramatically affected** by the pitchers they catch for and how many runners attempt against them.
- Counterintuitively, about two-thirds of catchers throw **slower** on caught stealings than on successful steals -- when the runner has a bad jump, the catcher prioritizes accuracy over speed.
- For individual SB projection, the pitcher-catcher battery a runner faces matters, but this is difficult to project at the season level.

### 4.6 SB and Batting Order Position

- Batting order position affects SB opportunities through PA count.
- Leadoff hitters get the most PA and often the most SB opportunities.
- Players in the 7-9 spots get fewer PA but may still have high attempt rates if they are speed specialists.
- The relationship between lineup position and SB is less direct than for R or RBI.

---

## 5. Major Projection Systems: Counting Stat Specifics

### 5.1 Marcel (The Baseline)

**Developer:** Tom Tango (the "monkey" -- simplest viable system)

**Methodology:**
- Weights previous 3 seasons: **5/4/3** for batting stats.
- Regresses toward league average using a factor of: weighted PA / (weighted PA + 1200).
- Age adjustment: Under 29, +0.6% per year below 29. Over 29, -0.3% per year above 29.
- Playing time: Last year PA x 0.5 + two years ago PA x 0.1 + 200.
- **Ignores minor league data entirely** -- treats unknown players as league average.

**Rate vs. counting:** Calculates per-PA rates first, then multiplies by projected PA.

### 5.2 Steamer

**Developer:** Jared Cross, Dash Davidson, Peter Rosenbloom

**Methodology:**
- Weighted average of past performance regressed toward league average.
- Regression amounts vary by stat and are set using regression analysis of historical players (not arbitrary).
- Uses pitch-tracking data for pitchers.
- **No player projected for more than 148 games.**

**How R/RBI are projected:**
- R and RBI generated via a **run expectancy matrix** based on projected offensive events.
- Final numbers adjusted for **team scoring** and **batting order position**.
- This is the key: Steamer projects component events (1B, 2B, HR, BB, etc.) as rates, then converts to counting stats through the RE matrix with team/lineup context.

### 5.3 ZiPS

**Developer:** Dan Szymborski

**Methodology:**
- Uses 4 years of stats for ages 24-38 (weighted 8/5/4/3), 3 years for very young/old players.
- Identifies comparable historical players using cluster analysis.
- Internal metrics: zBABIP, zHR, zBB, zSO establish baselines.
- Factors in velocities, injury data, and play-by-play data.
- Database covers every major leaguer since the Deadball era.

**R/RBI approach:** Component-based with comparable player adjustments and team context.

### 5.4 PECOTA

**Developer:** Baseball Prospectus (originally Nate Silver)

**Methodology:**
- Calculates weighted baseline from past performance (recent years weighted more heavily).
- Uses body type, position, and age to find comparable players.
- Comparable player careers drive the forecasts.
- Excels at counting stats (R, RBI, SB) by integrating **depth chart projections** for playing time.

**R/RBI approach:**
- Uses **lineup position integration** -- pulls lineup slots from depth charts to help calculate RBI.
- Draws from team-wide run environment and opportunity metrics.
- Percentiles key off TAv (True Average) as the primary rate stat; component stats illustrate likely paths to that TAv level.

### 5.5 THE BAT (X)

**Developer:** Derek Carty

**Methodology:**
- Uses regression and aging curves with unique twists.
- Incorporates **Statcast metrics**: launch angle, exit velocity, barrels, spray angles, sprint speed.
- Also factors in umpires, weather, and platoon splits.
- Originally designed for DFS (daily fantasy sports), expanded to season-long.
- Consistently ranks among the most accurate projection systems.

### 5.6 ATC (Average Total Cost / Ariel Cohen's Projections)

**Developer:** Ariel Cohen

**Methodology:**
- Not a simple average of projections. Each system's weight **varies by statistic**.
- Weights are based on each system's historical accuracy for that specific stat.
- Won most-accurate system in 2019, 2020, 2021, and 2022 -- four consecutive wins.

### 5.7 CAIRO

**Developer:** Replacement Level Yankees Weblog

**Methodology:**
- Weights 3 years of stats.
- Regresses for both age and **position played** (different regression amounts by position).

### 5.8 Summary: Rate vs. Counting Stat Approach

| System | Rate First? | R/RBI Context? |
|---|---|---|
| Marcel | Yes (per-PA rates x PA) | No team context |
| Steamer | Yes (per-PA x RE matrix) | Yes (team scoring, batting order) |
| ZiPS | Component-based (rates) | Yes (comparable players, context) |
| PECOTA | Yes (TAv-based rates) | Yes (lineup position, team environment) |
| THE BAT | Yes (Statcast-informed rates) | Yes |
| ATC | Weighted ensemble of above | Inherits from component systems |

**Key insight for your model:** All major systems project rates first and then convert to counting stats. R and RBI specifically require a team context adjustment layer -- raw rate prediction alone is insufficient.


## 6. Playing Time Modeling

### 6.1 Why Playing Time Matters

- Playing time is considered "the hardest thing to project" and "probably more responsible for differences of opinions than skills analysis."
- "The best way to get an accurate home run projection is to start by getting an accurate plate appearance projection."
- Playing time uncertainty is the primary source of counting stat projection error.
- Injuries are essentially unpredictable -- you cannot reliably predict injuries.

### 6.2 How Systems Estimate PA

- **FanGraphs Depth Charts:** Assume 640 PA from catchers, 700 PA from other positions, ~1,500 team innings pitched. Human writers divide playing time based on roster beliefs. Playing time is controlled by humans because "projection systems aren't very good at figuring out how much playing time a player is actually going to get."
- **Steamer:** No player projected for more than 148 games.
- **Marcel:** PT formula = (Last year PA x 0.5) + (Two years ago PA x 0.1) + 200.
- **General approach:** Most systems reference 3 seasons of PA data across MLB, AAA, and AA levels, filling missing PT with MLB averages by age.

### 6.3 Injury Risk Models

- Machine learning models analyzing 13,982 player-years (2000-2017) achieved **AUC of 0.80** for predicting next-season injury risk.
- ML outperformed regression analysis for injury prediction.
- The **DVS Injury Risk Model** achieved a Brier score of 0.134 (46% better than random) for predicting major throwing-related injuries.
- Key inputs: injury history, usage, position, age, biographical data.
- Common problem: **over-projecting injury-prone hitters** (e.g., Trout, Bryant, Marte, Story).

### 6.4 Roster Competition

- FanGraphs' approach: remove the player with the most projected WAR and increase PA for players below them on the depth chart.
- This is iterated for each team's top 10 projected performers.
- Liberal playing time estimates are by design -- league-wide total projected PA is traditionally within 110% of actual totals.

### 6.5 Age Effects on Playing Time

- Younger players ramp up. Older players see reduced PT.
- Position affects PT trajectory (catchers see less PT at all ages).
- Contract status matters (expensive veterans may get more rope).

### 6.6 Recommendations for Your Model

Your two-pass approach is well-designed:
1. **Pass 1:** PT from non-performance factors (injury history, roster competition, contract, age). This captures the biggest sources of PT variance.
2. **Pass 2:** Skill-tier nudge for fringe players. This captures the performance-PT feedback loop.

Key considerations:
- Cap individual projections reasonably (e.g., max 155 games / ~680 PA for position players).
- Weight recent injury history heavily (last 2-3 years).
- Account for AL-only roster dynamics (fewer replacement options than in mixed leagues).


## Machine Learning Approaches

### 7.1 Models Applied to Baseball Prediction

Five common ML models used in baseball stat prediction:
1. **Decision Tree**
2. **Logistic Regression**
3. **Neural Network (MLP)**
4. **Random Forest** -- 93.81% accuracy in some studies
5. **XGBoost** -- commonly used for tabular data

More advanced approaches:
- **LSTM (Long Short-Term Memory)** networks -- suited for sequential season-over-season data. An LSTM preserves long-term memory while filtering noise. Used to predict next-season HR totals.
- **Temporal Fusion Transformer** -- consistently outperformed RNN-based approaches in pitcher prediction.
- **GAM (Generalized Additive Models)** -- used for xHR probability modeling with launch angle, EV, and spray angle.

### Feature Importance: Stolen Bases

#### Stolen Bases
- **Most important features:** Prior-year SB (strongest), speed score, SB from 2 years prior, prior CS, BsR, prior CS from 2 years prior.
- Sprint speed is a strong supporting predictor.
- Projected triples (as a speed proxy) were a positive correction.
- Projected strikeouts were a negative factor for SB.

### Interaction Effects Relevant to SB

- **Speed x OBP** for SB (fast players who also reach base frequently steal more)

### 7.3 DataRobot Fantasy Baseball Model Factory

- Builds separate models for each of 5 fantasy stats (AVG, HR, R, RBI, SB).
- Uses 300+ FanGraphs features including xwOBA, Barrel%, and other advanced stats.
- DataRobot's Feature Discovery creates hundreds of rolling, time-aware features per player per season.
- Counting stats (R, HR, RBI, SB, K) were predictable with **75-80% accuracy** using common features.
- PA is the #1 factor for counting categories across all models.

### 7.4 GitHub Repositories of Note

- **datarobot-community/ai-accelerators** -- Fantasy baseball model factory notebook
- **RichieGarafola/MLB_HittingAnalysis** -- Feature engineering and random forest importance analysis
- **tweichle/Predicting-Baseball-Statistics** -- Classification and regression with scikit-learn and TensorFlow
- **eric8395/baseball-analytics** -- SVM, gradient boost, random forest, CatBoost, XGBoost, MLP
- **bdilday/marcelR** -- Marcel projections in R


## Key Research Questions

### 8.2 How have the 2023 rule changes affected SB prediction?

The changes created a **permanent structural shift**:
- SB per game increased ~45% (0.46 to ~0.72-0.73).
- Success rates increased ~3-4 percentage points (75% to ~79%).
- The speed threshold for "viable base stealer" has lowered -- marginal runners now attempt and succeed more often.
- Defensive adjustments in 2024 have stabilized (not reversed) the new baseline.
- **For modeling:** Pre-2023 SB models require recalibration. Use 2023+ data as the primary training window for SB attempt and success rates. Pre-2023 data can still inform speed-SB relationships but attempt rates need adjustment.

### SB/PA Model
**Primary inputs:**
1. Prior SB rates (2-3 years, weighted)
2. Sprint speed
3. OBP / SBO% (reaching base frequency)
4. Age (speed aging curve adjustment)
5. Team/manager SB philosophy
6. Post-2023 rule environment adjustment

**Approach:** Decompose into Opportunity x Attempt Rate x Success Rate. Model each component:
- Opportunity = f(OBP, lineup position)
- Attempt Rate = f(sprint speed, prior attempt rate, team philosophy, age)
- Success Rate = f(sprint speed, prior success rate) -- regress heavily to league average (~79%)


---

## Sources

### Stolen Base Prediction
- [Baseball Trends: The Impact of Rule Changes on Stolen Bases](https://phillybaseball.news/2025/11/17/baseball-trends-part-1-the-impact-of-rule-changes-on-stolen-bases/)
- [The Steals Will Continue Until Success Rates Decline](https://blogs.fangraphs.com/the-steals-will-continue-until-success-rates-decline/)
- [How Sprint Speed Relates to Stolen Bases](https://fantasy.fangraphs.com/how-sprint-speed-relates-to-stolen-bases/)
- [Is Stolen Base Rate Predictive of Anything?](https://fantasy.fangraphs.com/is-stolen-base-rate-predictive-of-anything/)
- [Opportunity, Takeoff Rate, and Stolen Base Opportunism](https://blogs.fangraphs.com/opportunity-takeoff-rate-and-stolen-base-opportunism/)
- [Stolen Base Opportunities](https://fantasy.fangraphs.com/stolen-base-opportunities/)
- [Projecting Stolen Bases Using SBO% and Success Rate](https://thefantasyfix.com/fantasy-baseball/projecting-stolen-bases-using-sbo-and-success-rate/)
- [Forecasting Stolen Base Success Rates (Baseball Prospectus)](https://www.baseballprospectus.com/news/article/9537/forecasting-stolen-base-success-rates-part-one/)
- [Touching Base: Who's Stealing More With the New Rules](https://pitcherlist.com/touching-base-whos-stealing-more-with-the-new-rules/)
- [Dugout Decisions: New Manager Effects on Player Stolen Base Outlooks](https://www.pitcherlist.com/dugout-decisions-new-manager-effects-on-player-stolen-base-outlooks/)
- [Diving into Statcast Sprint Speed](https://fantasy.fangraphs.com/diving-into-statcast-sprint-speed/)


### Age Curves
- [Aging Curve -- Sabermetrics Library](https://library.fangraphs.com/principles/aging-curve/)
- [Checking In on the Aging Curve](https://blogs.fangraphs.com/checking-in-on-the-aging-curve/)
- [How Power Ages (Driveline Baseball)](https://www.drivelinebaseball.com/2025/10/how-power-ages-it-might-surprise-you/)
- [Sprint Speed shows speed peaks young](https://www.mlb.com/news/statcast-sprint-speed-shows-speed-peaks-young-c239376598)
- [Examining Aging Curves for Statcast Metrics](https://medium.com/@adamsalorio/examining-aging-curves-for-statcast-metrics-18c8c2ac2a4c)

### Projection Systems
- [A Guide to the Projection Systems (Beyond the Box Score)](https://www.beyondtheboxscore.com/2016/2/22/11079186/projections-marcel-pecota-zips-steamer-explained-guide-math-is-fun)
- [Projection Systems -- Sabermetrics Library](https://library.fangraphs.com/principles/projections/)
- [The Projection Rundown (FanGraphs)](https://www.fangraphs.com/library/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/)
- [Depth Charts -- Sabermetrics Library](https://library.fangraphs.com/depth-charts/)
- [Projecting X: How to Project Players](https://plus.fangraphs.com/fg-projecting-players-101/)
- [How I Create Fantasy Baseball Projections (Draft Buddy)](https://www.draftbuddy.com/how-i-create-fantasy-baseball-projections-for-draft-buddy/)
- [Cockcroft: Inside the projections process (ESPN)](https://www.espn.com/fantasy/baseball/story/_/page/mlbdk2k15_projectionstalk/how-fantasy-baseball-projections-calculated-how-best-use-them)
- [Most Accurate Fantasy Baseball Projections, 2025 Results](https://www.fantasypros.com/2026/02/most-accurate-fantasy-baseball-projections-2025-results/)
- [Marcel on GitHub (bdilday/marcelR)](https://github.com/bdilday/marcelR)
- [Bayesian MARCEL (PyMC Labs)](https://www.pymc-labs.com/blog-posts/bayesian-marcel)

### Playing Time and Injury
- [2024 Projection Review: Batter Playing Time](https://fantasy.fangraphs.com/2024-projection-review-batter-playing-time/)
- [How to Project Plate Appearances](https://www.smartfantasybaseball.com/2015/11/how-to-project-plate-appearances/)
- [Machine Learning Outperforms Regression for MLB Injury Prediction](https://pmc.ncbi.nlm.nih.gov/articles/PMC7672741/)
- [DVS Injury Risk Model](https://www.dvsbaseball.com/dvs-ir-model)
- [MLB Health and Injury Tracking System (HITS)](https://pubmed.ncbi.nlm.nih.gov/41798093/)

### Machine Learning
- [Machine Learning in Baseball Analytics: Sabermetrics and Beyond](https://www.mdpi.com/2078-2489/16/5/361)
- [Using Recurrent Neural Networks to Predict Player Performance](https://tht.fangraphs.com/using-recurrent-neural-networks-to-predict-player-performance/)
- [Performance Prediction in MLB by LSTM Networks](https://arxiv.org/pdf/2206.09654)
- [Predicting Annual Home Runs from Sensor Data (Nature Scientific Reports)](https://www.nature.com/articles/s41598-025-18403-1)
- [Predicting Home Runs with Machine Learning (Medium)](https://nrackerman.medium.com/predicting-home-runs-for-mlb-players-with-machine-learning-a0bc9740ea1d)
- [Baseball and Machine Learning: 2021 Hitting Projections (Medium)](https://medium.com/data-science/baseball-and-machine-learning-a-data-science-approach-to-2021-hitting-projections-4d6eeed01ede)
- [DataRobot Fantasy Baseball Predictions](https://docs.datarobot.com/en/docs/api/accelerators/model-building-tuning/fantasy-baseball.html)
- [DataRobot Fantasy Baseball Model Factory Notebook](https://github.com/datarobot-community/ai-accelerators/blob/main/use_cases_and_horizontal_approaches/model_factory_selfjoin_fantasy_baseball/fantasy_baseball_predictions_model_factory.ipynb)
- [MLB_HittingAnalysis (GitHub)](https://github.com/RichieGarafola/MLB_HittingAnalysis)
- [Predicting-Baseball-Statistics (GitHub)](https://github.com/tweichle/Predicting-Baseball-Statistics)

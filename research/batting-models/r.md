# Runs Rate Prediction (R/PA)

Research for projecting Runs scored rates in the Moonlight Graham AL-only rotisserie league.

---

## 2. RUNS Rate Prediction (R/PA)

### 2.1 Context-Dependent Nature of Runs

Runs scored is one of the **most context-dependent** offensive statistics:
- R depends heavily on **who bats behind you** (can they drive you in?).
- R depends on **batting order position** (higher = more PA and more chances to score).
- R depends on **team quality** (better surrounding lineup = more R opportunities).
- R has playing time and skill elements (OBP, speed) but is also **largely team-dependent**.
- Projection systems acknowledge this by using **run expectancy matrices** adjusted for team scoring and batting order.

### 2.2 R/PA by Batting Order Position

From FanGraphs and Smart Fantasy Baseball research (AL averages):

| Batting Order | Approximate R/PA | Notes |
|---|---|---|
| 1st (Leadoff) | ~0.130 | Highest R/PA; most PA |
| 2nd | ~0.120-0.125 | High OBP hitters placed here |
| 3rd | ~0.110-0.115 | Plateau in 3-4-5 spots |
| 4th (Cleanup) | ~0.105-0.110 | Plateau in 3-4-5 spots |
| 5th | ~0.100-0.105 | Plateau in 3-4-5 spots |
| 6th | ~0.095-0.100 | Steady decline |
| 7th | ~0.085-0.090 | Steady decline |
| 8th | ~0.080-0.085 | Steady decline |
| 9th | ~0.070-0.080 | Lowest R/PA |

Key insight: A player moving from the 9th spot to leadoff might see projected runs jump from ~60 to ~95 in a full season.

### 2.3 PA by Batting Order Position

For every spot a player drops in the lineup, expect approximately **0.10-0.11 fewer PA per game** (~16 PA over 162 games). The difference between 1st and 8th is roughly **190 PA** over a season.

### 2.4 Key Drivers of R/PA

1. **OBP (On-Base Percentage)** -- Correlation with team runs scored: **r = 0.89** (team level). At the individual level, OBP has about a **30% correlation** with runs produced.
2. **Speed / Base Running** -- Advances on bases, scores from various positions, extra bases taken. However, at the team level, SB has essentially **no correlation** with team runs scored (R-squared = 0.001).
3. **Batting Order Position** -- Affects both PA count and R/PA rate.
4. **Team Quality / Surrounding Lineup** -- The team run-scoring environment influences individual run scoring.
5. **SLG** -- Contributes via extra-base hits that advance the runner or score runs. Team-level OPS correlates with runs at R-squared ~0.93.

### 2.5 Approaches to R Prediction

#### Runs Created and Variants
- Bill James' original **Runs Created** (RC) formula: RC = (H + BB) x TB / (AB + BB).
- This was superseded by Tom Tango's **Weighted Runs Created (wRC)**, based on wOBA.
- wRC uses linear weights derived from run expectancy matrices to properly value each offensive event.

#### Linear Weights
- Each offensive event has a run value derived from the run expectancy matrix.
- Typical linear weights (approximate, vary by era): 1B ~0.47, 2B ~0.77, 3B ~1.04, HR ~1.40, BB ~0.32, SB ~0.20, CS ~-0.41.
- wOBA scales these weights to an OBP-like number for convenience.

#### BaseRuns Formula
- FanGraphs uses **BaseRuns** for team-level run estimation: BsR = A x B / (B + C) + D.
  - A = baserunners, B = advancement, C = outs, D = home runs (guaranteed runs).
- Cannot be applied directly to individual players -- must calculate team BsR with and without the player to get individual contribution.

#### How Projection Systems Handle R
- **Steamer:** Generates R and RBI via a **run expectancy matrix** based on projected events, adjusted for team scoring and batting order position.
- **ZiPS:** Uses component stats and historical comparable players to project counting stats, factoring in team context.
- **PECOTA:** Integrates lineup slots and depth charts to calculate RBI/R, pulling from team-wide run environment and opportunity metrics.
- **Manual approach (FanGraphs "Projecting X"):** R and RBI are among the categories projected **completely manually** in some systems, looking at past years, expected batting order slot, lineup changes, and projected power changes.
- **Custom projection tools (e.g., Big Board):** Use batting order position from Roster Resource, combined with team projected runs, to calculate relative R/RBI expectations and R:RBI ratios.

### 2.6 Simplified R/PA Model Structure

A practical approach for your model:

```
R/PA = f(OBP, SLG, Speed, BattingOrderPosition, TeamRunEnvironment)
```

Where:
- OBP drives base-reaching frequency
- SLG captures extra-base advancement
- Speed captures baserunning value (extra bases taken, scoring from 1st on doubles, etc.)
- BattingOrderPosition adjusts for opportunity (can be a lookup table or regression coefficient)
- TeamRunEnvironment captures the quality of hitters behind you (team projected R/G)

Note: The team run environment for AL-only leagues is particularly important since you know the exact AL team rosters and can project team-level run scoring for each.

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

### Feature Importance: Runs

#### Runs
- **Most important features:** OBP, batting order position, team OBP, speed/sprint speed, SLG.
- Team-level: OPS explains **~94%** of team runs variance.
- wRC+ was the most influential predictor in broader ML models.

### Interaction Effects Relevant to R

- **OBP x TeamQuality** for R (high OBP is more valuable in a good lineup)

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

### 8.1 How context-dependent are R and RBI?

**R:** Moderately context-dependent. OBP and speed are individual-controllable; batting order position and team quality are context. A leadoff hitter with .380 OBP will score more runs on a good team than a bad team, but the OBP-driven component is somewhat portable.

**RBI:** Highly context-dependent. The same hitter batting cleanup on the Yankees vs. 7th on a rebuilding team could see a **30-40 RBI difference**. HR-driven RBI are the most "portable" component since every HR guarantees at least 1 RBI regardless of context.

**Best approach for your model:**
1. Predict individual rate stats (HR/PA, OBP, SLG, speed metrics) as context-neutral skill measures.
2. Layer on batting order position (from projected lineups / Roster Resource).
3. Layer on team run environment (from AL team-level projections).
4. Convert to R/PA and RBI/PA using lookup tables or regression coefficients by batting order slot.

### R/PA Model
**Primary inputs:**
1. Projected OBP (context-neutral)
2. Projected SLG
3. Sprint speed / BsR
4. Batting order position (projected)
5. Team run-scoring environment (team projected R/G)

**Approach:** Use a lookup table or regression model that maps (OBP, SLG, Speed, BatOrder, TeamR/G) to R/PA. Train on historical player-seasons with known batting order data.

---

## Sources

### Runs Prediction
- [Runs and Batting Order (FanGraphs)](https://fantasy.fangraphs.com/runs-and-batting-order/)
- [Making Simple Edits to Projections for R, RBI, and PA](https://fantasy.fangraphs.com/making-simple-edits-to-projections-for-r-rbi-and-pa/)
- [The Effect of Batting Order on R and RBI Production](https://www.smartfantasybaseball.com/2014/10/the-effect-of-batting-order-on-r-and-rbi-production/)
- [Runs Scored Correlations](https://www.eg.bucknell.edu/~bvollmay/baseball/runs1.html)
- [BaseRuns -- Sabermetrics Library](https://library.fangraphs.com/features/baseruns/)
- [wRC and wRC+ -- Sabermetrics Library](https://library.fangraphs.com/offense/wrc/)
- [Linear Weights -- Sabermetrics Library](https://library.fangraphs.com/principles/linear-weights/)
- [The Beginner's Guide to Deriving wOBA](https://library.fangraphs.com/the-beginners-guide-to-deriving-woba/)


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

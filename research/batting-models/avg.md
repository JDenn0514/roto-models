# Exhaustive Research: Predicting Batting Average (AVG) in Baseball

## Context
This research is oriented toward fantasy baseball application in the **Moonlight Graham League** -- a 10-team AL-only rotisserie league on OnRoto (FanGraphs) with AVG as one of five hitting categories (R, HR, RBI, SB, AVG). AVG is among the hardest fantasy categories to predict, making this research especially important for gaining an edge.

---

## 1. Major Projection Systems

### 1.1 Marcel (Tom Tango) -- The Baseline

Marcel ("Marcel the Monkey Forecasting System") is the simplest credible projection system and serves as the benchmark that all others must beat. Created by Tom Tango, it represents "the minimum level of competence that you should expect from any forecaster."

**Exact Methodology for Batting Stats:**
- **Season weights:** 5 / 4 / 3 for the most recent three seasons (year-1 / year-2 / year-3)
- **Regression constant:** 1,200 PA. The regression formula is:
  ```
  Regressed rate = (Rate * PA + League_Rate * 1200) / (PA + 1200)
  ```
  This means a player with 600 PA gets regressed roughly 67% toward league average, while a player with 1,200 PA is regressed 50%.
- **Age adjustment:** Peak at age 27, with `age_factor = 1.0 + (27 - age) * 0.003` per year
- **Playing time:** Projected as a weighted average of the past three years' PA, with weights 0.5 / 0.1 / 0.1, regressed toward 200 PA

Marcel does **not** use batted ball data, Statcast metrics, minor league data, or comparable player analysis. It projects rate stats directly (including AVG) rather than decomposing into components.

**Key insight:** Marcel has consistently frustrated more sophisticated forecasters because, despite its simplicity, it typically performs on par with or only slightly worse than far more complex systems. A recent study applying Marcel to NPB (Japanese baseball) found that it outperformed LightGBM and XGBoost for player performance prediction, confirming the well-known finding that simple regression-based approaches are surprisingly competitive.

**Open-source implementation:** [github.com/bdilday/marcelR](https://github.com/bdilday/marcelR)

---

### 1.2 Steamer (Jared Cross, Dash Davidson, Peter Rosenbloom)

Created in 2008, Steamer is a regression-based system that breaks performance into components and finds optimal weights via regression analysis.

**Methodology for AVG:**
- Uses a weighted average of past performance regressed toward league average
- How much each year is weighted and how much regression is applied **varies by statistic** and is set using regression analysis of past players (not fixed 5/4/3 like Marcel)
- Breaks batting and pitching performance into a **series of components** and uses regression to find the most effective combination
- Historically did **not** project batted ball distribution (FB%/GB%/LD%), meaning it was not observing line drive rate relative to BABIP and expecting adjustments
- Since ~2016, has incorporated **exit velocity data** from Statcast to improve BABIP projection. Jared Cross and William Sapolsky made initial adjustments to Steamer projections based on average exit velocities
- Includes park-factor adjustments (park-adjusted and park-neutral versions available)
- Uses minor league equivalencies (MLEs) for prospect projections

**AVG-specific behavior:** Steamer considers a player's full history and typical aging patterns. If a player had a "down" year but had great prior seasons, Steamer factors in how hitters of similar caliber usually age rather than simply reacting to the most recent year.

**Accuracy:** In multiple third-party evaluations, Steamer has been among the top-performing systems, particularly for rate stats. It performed better than competitors on the whole for most subgroups and statistics despite being "relatively simple."

---

### 1.3 ZiPS (Dan Szymborski)

ZiPS (sZymborski Projection System) uses comparable-player analysis with a massive historical database.

**Methodology:**
- **Database:** ~185,000 hitter baselines and ~152,000 pitcher baselines, including every major leaguer since the Deadball era and every minor league translation since the late 1960s
- **Season weights:** 8/5/4/3 for the most recent four years (ages 24-38); only three years used for very young or very old players
- **Comparable player identification:** Uses **cluster analysis** (including Mahalanobis distance) to assemble a cohort of similar historical players. Factors include production metrics (batting average, isolated power, walk rate), plus non-statistical factors like age, position, handedness, height, and weight relative to era averages
- **Ensemble modeling:** The comparable player cohort is used to calculate an ensemble forecast for a player's future career
- **Additional inputs:** Velocities, injury data, and play-by-play data
- **Probabilistic output:** ZiPS produces a full probability distribution, not just a point estimate. A ".300 AVG projection" is a midpoint -- ZiPS expects ~10% of players to exceed their 90th percentile forecast and ~10% to fall below their 10th percentile

**AVG-specific insight:** ZiPS projects rate stats including AVG by combining the weighted historical performance with comparable-player career trajectories. The comparable-player approach gives ZiPS an advantage when projecting players with unusual profiles or at inflection points in their careers.

---

### 1.4 PECOTA (Baseball Prospectus)

PECOTA (Player Empirical Comparison and Optimization Test Algorithm) was originally developed by Nate Silver in 2002-2003.

**Methodology:**
- **Nearest-neighbor analysis:** Matches each player with a set of historically comparable players using similarity scores against a database of ~20,000 major league batter seasons since WWII
- **Four attribute categories for comparability:** Production metrics (batting average, isolated power, unintentional walk rate), usage metrics, demographic factors, and physical attributes
- **Three-year performance window:** Uses a three-year window for the similarity scoring
- **Component-based:** Projects individual batting events (singles, doubles, triples, HR, strikeouts, walks) separately rather than projecting AVG directly. AVG is derived from the projected component totals
- **Career trajectory modeling:** Once comparables are identified, the player's forecast is based on how those comparable players actually performed in subsequent seasons at the same age
- **Probabilistic:** Provides percentile-based forecasts (10th, 25th, 50th, 75th, 90th percentile outcomes)
- **Park and league adjustments:** Adjusts for parks and league effects before computing similarity scores

**AVG-specific behavior:** By projecting individual hit types rather than AVG directly, PECOTA implicitly models BABIP through the projected singles, doubles, and triples rates. The comparable-player approach means PECOTA can capture career trajectory patterns (e.g., speed decline, contact skill changes) that affect AVG differently for different player types.

---

### 1.5 THE BAT / THE BAT X (Derek Carty)

THE BAT is Derek Carty's comprehensive projection system; THE BAT X extends it with Statcast data.

**Methodology:**
- **THE BAT (base version):** A comprehensive projection system in the vein of PECOTA, Oliver, or ZiPS, using historical performance, aging curves, regression, and park factors
- **THE BAT X:** Combines THE BAT with **Statcast data** including exit velocity, launch angle, barrel rate, and other contact quality metrics
- **Additional factors in THE BAT X:** Opposing hitter/pitcher matchups, ballpark, weather, umpire, catcher framing/throwing/intimidation, bullpen quality, pitch counts, home field advantage, platoon splits, defensive alignment, lineup position, quality of surrounding lineup, and air density
- **Statcast integration for AVG:** Uses barrel rate, hard-hit rate, exit velocity, and launch angle data to improve BABIP and contact quality projections beyond what traditional batted ball data (LD%/GB%/FB%) can provide

**Accuracy:** THE BAT X has been the **most accurate original projection system for four consecutive years** (as of 2023 assessment). In 2024, it earned the #1 spot overall, becoming the first original system to be the most accurate projection system, outperforming even aggregate systems. In the 2023 Projection Showdown specifically focused on batting average, THE BAT X was closer on 5 of 6 players where it was most bullish, and 5 of 7 players where Steamer was more optimistic.

THE BAT X is widely considered the **gold standard** for hitter projections in the Statcast era.

---

### 1.6 ATC (Average Total Cost -- Ariel Cohen)

ATC is a "smart" projection aggregation model.

**Methodology:**
- **Weighted aggregation:** Unlike simple consensus systems, ATC does **not** take a straight average. Each underlying system receives a different weight **for each statistic**, with weights determined by historical past performance
- **Component systems:** Incorporates ZiPS, Steamer, FanGraphs FANS projections, and other freely available systems, plus prior MLB statistics over the past 3 seasons
- **Optimization approach:** Similar to Nate Silver's political forecasting methodology at FiveThirtyEight -- finding the optimal blend of multiple information sources based on their track record
- **Volatility metrics:** ATC also publishes inter-projection volatility scores, identifying players where projection systems disagree most (higher volatility = higher uncertainty)

**Accuracy:** ATC has been the **#1 most accurate projection system for five consecutive years**. Its advantage comes from smart weighting rather than novel underlying methodology.

**AVG-specific insight:** For AVG specifically, ATC benefits from combining systems that approach the problem differently (e.g., Steamer's regression-based approach vs. ZiPS' comparable-player approach), which tends to cancel out system-specific biases.

---

### 1.7 Depth Charts (FanGraphs Composite)

**Methodology:**
- A **50/50 blend of Steamer and ZiPS** prorated to RosterResource playing time projections
- FanGraphs staff divides playing time based on roster analysis: 640 PA for catchers, 700 PA for other positions, ~1,500 IP per team
- FanGraphs makes **no individual changes** to the rate stat projections; the only FanGraphs influence comes from playing time estimates
- Updated in real time as roster news emerges (changes reflected within ~30 minutes)
- Early in the offseason (November to ~March), relies exclusively on Steamer before ZiPS becomes available

---

### 1.8 CAIRO

**Methodology:**
- Built on the Marcel framework with several enhancements:
  - Uses **four seasons** of data rather than three
  - Adjusts for **ballpark effects**
  - Uses **minor league equivalencies** (MLEs)
  - Adjusts for **defense**
  - Regresses toward league average at **differing rates depending on age and primary position**
- Developed by the "Revenge of the Replacement Level Yankees Website" (RLYW)

CAIRO has been largely surpassed by newer systems (Steamer, THE BAT X) but represents an important evolutionary step from Marcel.

---

### 1.9 Oliver (Brian Cartwright)

**Methodology:**
- Three years of player data with more recent years weighted heavier
- Factors age and regression to the mean
- Distinguishes itself through **proprietary minor league translation formulas** for projecting MiLB-to-MLB transitions
- Used by The Hardball Times

---

### 1.10 OOPSY (Jordan Rosenblum) -- NEW for 2025

**Methodology:**
- Uses OOPSY's own aging curves, major league equivalencies, park factors, league scoring environment factors, regression, and recency weights
- **Key innovation:** Incorporates **bat speed / swing speed** data from Baseball Savant (new Statcast metric available since 2024), plus barrel rate per batted ball event
- Also accounts for the usual component statistics: K%, BB%, HR%, etc.
- Barrel rate and swing speed are described as "really sticky measures... which only take a few swings to show [their] true self or stabilize"
- Tends to be **more bullish at the extremes** because bat speed and barrel rate are highly stable skills

**Debut performance:** Ranked second among standalone systems for both pitchers and hitters in its first season (2025).

---

### 1.11 Other Systems

- **Davenport:** Performed well in 2024 testing alongside Razzball, ZiPS, and THE BAT X
- **Razzball/Steamer:** A Razzball-specific version of Steamer projections; performed well in 2024
- **Zeile Consensus (FantasyPros):** A straight average of component systems with equal weighting; consistently ranks among the top aggregation systems
- **FANS (FanGraphs community):** Crowdsourced projections from FanGraphs users

---

## 2. Component-Based AVG Prediction

### 2.1 The Fundamental Decomposition

Batting average can be mathematically decomposed into three independent components:

```
AVG = (1 - K_rate) * BABIP + HR_rate_on_contact

More precisely:
K_rate = SO / AB
HR_rate = HR / (AB - SO)
BABIP = (H - HR) / (AB - SO - HR)

Then: AVG = BABIP * (1 - K_rate) + HR_rate * (1 - K_rate)
```

This decomposition is powerful because each component has **different stability characteristics:**

| Component | Year-to-Year Correlation | Stabilization Point | Nature |
|-----------|------------------------|---------------------|--------|
| Contact rate (1 - K%) | **r = .8305** | ~60-150 PA | Skill-driven |
| HR rate (AB/HR) | **r = .6245** | ~170 PA (HR/FB) | Skill-driven |
| BABIP | **r = .35** | **~820 BIP (~910 AB)** | Heavily luck-influenced |

**Key finding:** Contact rate and home run rate reflect genuine player skill and are well-predicted by direct regression. BABIP is heavily influenced by chance -- small changes are anticipated in K% and HR rate in future seasons, while a high BABIP is anticipated to regress close to average. This asymmetry is the central challenge of AVG prediction.

---

### 2.2 BABIP Prediction Models

BABIP is the most difficult component to forecast because it blends real skill with substantial noise.

#### League Average and Regression Targets

- **League-average BABIP:** ~.300 (roughly 30% of all balls in play fall for hits)
- **Typical player BABIP range:** .270 to .340 for most regulars
- **Year-to-year BABIP correlation:** ~.35 for hitters, ~.15 for pitchers
- **Regression pattern:** ~70% of players with extreme BABIP values regress toward .300 in the following season

#### BABIP by Batted Ball Type (2016 league data)

| Batted Ball Type | BABIP | Implication |
|-----------------|-------|-------------|
| Line drives | **.680** | Highest hit rate; LD% strongly influences BABIP |
| Ground balls | **.239** | Moderate; speed-dependent |
| Fly balls | **.127** | Lowest; mostly outs unless HR |
| Pop-ups | ~.020 | Nearly automatic outs |

#### BABIP Prediction Formulas

**Simple xBABIP (Studes):**
```
xBABIP = 0.245 + 0.52 * LD% - 0.16 * FB% + 0.11 * K%
```

**General approximation (Tom Tango):**
```
xBABIP ≈ LD% + .120
```

**Mike Podhorzer's xBABIP equation (2015):** Uses Out-Contact%, ISO, launch angle, LD%, FB%, IFFB%, and Sprint Speed. Multiple researchers have augmented this model, with the biggest predictive factors being:
1. Line drive rate
2. Fly ball and infield fly ball rate
3. Launch angle
4. Sprint speed

**Best xBABIP model performance:** Explains ~25% of BABIP variation (R^2 = .25) in samples of 300+ PA. One model achieved 38% less error than Statcast's model when predicting BABIP from launch characteristics.

#### Year-to-Year Correlations by Batted Ball BABIP

| Batted Ball Type | Year-to-Year BABIP Correlation |
|-----------------|------------------------------|
| Ground balls | **.30** (most stable -- speed-related) |
| Outfield fly balls | **.22** |
| Pop-ups | **.17** |
| Line drives | **.12** (least stable) |

**Implication:** A high BABIP driven by ground ball hits (i.e., speed) is more likely to persist than one driven by line drive luck. A high BABIP driven by line drive BABIP is likely to regress.

#### Sprint Speed and BABIP

- Sprint speed has a **positive correlation** with ground ball batting average
- Previous year's sprint speed has **predictive value** for projecting next year's ground ball batting average
- When a player's ground ball AVG diverges from what sprint speed would predict, it **typically regresses** the next season
- However, sprint speed's correlation with overall BABIP is **less influential than most expect** -- less influential than batted ball data
- Sprint speed matters most for infield hits and topped/weakly hit balls

#### Player-Type BABIP Ranges (True Talent Estimates)

| Player Type | Expected True-Talent BABIP Range | Driver |
|-------------|----------------------------------|--------|
| Fast ground-ball hitters | .310 - .340+ | Beat out infield hits |
| Average hitters | .290 - .310 | League average |
| Slow fly-ball hitters | .270 - .290 | Fewer infield hits, fewer LD |
| High LD% hitters | .300 - .330+ | More line drives = more hits |
| High IFFB% hitters | .260 - .290 | Infield flies are automatic outs |

---

### 2.3 Contact Quality Models (Statcast Era)

Since 2015, Statcast has provided granular batted ball data that has reshaped BABIP and AVG prediction.

#### xBA (Expected Batting Average)

**Calculation:** Each batted ball is assigned an xBA based on how often comparable balls (in terms of exit velocity, launch angle, and -- for topped/weakly hit balls -- sprint speed) have become hits since 2015.

**Seasonal xBA:** Sum of all individual batted-ball xBAs, divided by total batted ball events, with strikeout totals factored in.

**Sprint speed adjustment (added January 2019):** Fast hitters routinely outperformed their xBAs while slower hitters underperformed. The adjustment applies sprint speed to "topped" or "weakly hit" balls where speed affects outcome. Sprint speed also specifically improves infield hit percentage (IFH%) prediction.

**Predictive Value for Future AVG:**
- xBA has an **R^2 of only .114** for predicting next-year AVG (2015-present study)
- Previous-season batting average is **actually more predictive** than xBA for next-year AVG
- The difference between xBA and plain batting average at predicting future AVG is **within the margin of error**
- There is a "reasonable likelihood" xBA is **slightly** more predictive, but the difference is modest

**Conclusion:** xBA is primarily a **descriptive** metric (what should have happened) rather than a predictive one. It helps identify luck-driven outliers but should not replace traditional projection methods for future performance.

#### Exit Velocity and Hard-Hit Rate

- **Hard-hit balls** (95+ mph): Produce a leaguewide .506 AVG, 1.008 SLG, .625 wOBA
- **Below 95 mph:** Produce a .221 AVG, .261 SLG, .207 wOBA
- Average exit velocity has a **high descriptive correlation** with wOBA, HR%, ISO, and batting average
- Exit velocity has the **strongest predictive correlation** with future batting average among Statcast metrics
- **Exit velocity stabilization:** Reliable after only ~40 balls in play (one of the fastest-stabilizing metrics)

#### Barrel Rate

- **Barrel definition:** Batted ball with exit velocity 98+ mph at a launch angle producing a minimum .500 AVG and 1.500 SLG historically
- Barrel rate has **extremely high correlation** with HR rate and ISO (r = .66 to .76 with HR/FB rate)
- Barrel rate is the **most predictive power metric** and a key input for THE BAT X, OOPSY, and other modern systems
- Stabilizes relatively quickly and is considered a "sticky" skill measure

#### Sweet Spot Percentage

- Measures how consistently a player's batted balls are launched at an ideal angle
- Higher sweet spot % correlates with higher AVG and power
- Useful complementary metric to barrel rate

---

### 2.4 Plate Discipline Decomposition

#### Strikeout Rate (K%)

- **Strongest single predictor of batting average** among peripheral metrics
- **Stabilization:** ~60-150 PA (among the fastest-stabilizing stats)
- Negatively correlated with AVG: more strikeouts = fewer balls in play = fewer chances for hits
- Year-to-year K% changes explained by whiff rate and contact rate changes (R^2 = .83)
- For every 1% increase in whiff rate, K% increases by ~0.87%

#### Contact Rate and Whiff Rate

- **Contact percentage** stabilizes around 100 PA
- Contact rate, whiff rate, and swing percentage are the **quickest things to stabilize**
- Whiff rate (whiffs / swings) has a robust R^2 of .83 with strikeout rate
- These are excellent leading indicators for K% changes, which in turn affect AVG

#### Chase Rate (O-Swing%)

- Percentage of pitches outside the strike zone at which a batter swings
- Better measure of plate discipline than walk rate (accounts for all swing decisions, not just the final pitch)
- Chase rate benchmarks: Elite < 19%, Average 26.5-29%, Poor > 31%
- Indirectly affects AVG through count management and contact quality
- Advanced swing decision models (SwRV+, SEAGER) attempt to weigh the value of each swing vs. take decision

#### Walk Rate (BB%)

- Indirect effect on AVG: walks don't count as at-bats, so they don't directly affect AVG but indicate plate discipline
- BB% peaks between ages 28-32 (last skill to decline with age)
- Better count management leads to better pitches to hit, indirectly supporting BABIP

---

## 3. Statcast-Era Innovations (2015-Present)

### 3.1 How Statcast Changed AVG Prediction

Before Statcast (pre-2015), BABIP prediction relied primarily on:
- Batted ball types (LD%/GB%/FB%) from manual stringer classifications
- Sprint speed estimates
- Historical regression patterns

Statcast provided **objective, granular measurements** of exit velocity and launch angle for every batted ball, enabling:
1. More accurate BABIP models based on contact quality rather than type classifications
2. xBA as a descriptive measure of expected outcomes
3. Exit velocity as a fast-stabilizing skill measure
4. Barrel rate as a reliable power indicator
5. Sprint speed measurements for infield hit modeling

### 3.2 xwOBA and Its AVG Component

xwOBA (expected Weighted On-Base Average) uses exit velocity and launch angle to assign expected run values to each batted ball event. While broader than xBA, it provides context for AVG prediction:
- Previous-year xwOBA predicts next-year wOBA with R^2 = .218
- Previous-year wOBA predicts next-year wOBA with R^2 = .191
- The improvement from "expected" to "actual" metrics is **modest but real** for aggregate offensive value

### 3.3 Bat Speed / Swing Speed (2024+)

New Statcast bat-tracking metrics available since 2024 include:
- **Bat speed** (mph at contact)
- **Fast-swing rate** (% of competitive swings at high speed)
- **Squared-up rate** (% of swings making solid contact)
- **Swing length** (distance of the bat path)

These metrics stabilize very quickly and are incorporated into OOPSY projections. Their long-term predictive value for AVG is still being studied but early indications suggest bat speed is a genuine, stable skill measure.

### 3.4 The Limits of Statcast for AVG Prediction

Despite the richness of Statcast data, key limitations remain:
- xBA (R^2 = .114 for next-year AVG) is **not dramatically better** than actual AVG for prediction
- xStats by themselves "generally aren't much better than the actual stats at predicting the next year's actual stats"
- The largest gains from Statcast data come through **reducing sample size requirements** (e.g., exit velocity stabilizes at ~40 BIP vs. BABIP at ~820 BIP), which helps for in-season updates and small-sample situations
- Defensive alignment, shifts (now banned), and fielder positioning create variance not captured by xBA

---

## 4. Regression and Stabilization

### 4.1 Stabilization Points (Plate Appearances to Reliability)

Stabilization is defined as the point where a stat produces an R of 0.50 in split-half correlation -- where actual results are equally weighted with league average for predicting future performance.

| Statistic | Stabilization Point | Notes |
|-----------|-------------------|-------|
| Swing% | ~50 PA | Fastest to stabilize |
| Contact% | ~100 PA | Very quick |
| K% | ~60-150 PA | Quick; among most reliable early-season indicators |
| BB% | ~120 PA | Relatively quick |
| HBP rate | ~300 PA | Moderate |
| HR/FB rate | ~170 fly balls | Moderate |
| LD% | ~150 PA | Moderate |
| GB%/FB% | ~150-250 PA | Moderate |
| ISO | ~550 PA | Slow |
| OBP | ~500 PA | Slow |
| SLG | ~500 PA | Slow |
| AVG | **~910 AB** | Very slow (~2 full seasons) |
| BABIP (hitter) | **~820 BIP** | Very slow (~2 full seasons) |
| BABIP (pitcher) | ~2,000 BIP | Extremely slow (~3 years) |
| Exit velocity | **~40 BIP** | Extremely fast (Statcast era) |
| Hard-hit rate (simple) | ~190 PA | Moderate |
| xBA/xwOBA | ~50-100 BIP initial; ~300 PA for full-season confidence | Moderate |

**Key insight for AVG prediction:** AVG stabilizes at ~910 AB, nearly two full seasons. This means direct AVG from a single season contains more noise than signal. Component-based approaches that leverage faster-stabilizing inputs (K%, exit velocity, sprint speed) can theoretically outperform direct AVG regression from a single year.

### 4.2 Regression to the Mean

The formula for regressing any stat to the mean is:

```
True Talent Estimate = (Observed * n + League_Avg * Regression_Constant) / (n + Regression_Constant)
```

Where `n` is the sample size (PA, AB, or BIP depending on the stat) and the regression constant varies by stat.

For Marcel-style batting projections, the regression constant is **1,200 PA**. This means:
- 600 PA of data: Regress ~67% toward league average
- 1,200 PA of data: Regress ~50% toward league average
- 1,800 PA of data: Regress ~40% toward league average

**Player-specific vs. population regression:** Most systems regress toward the overall league average. More sophisticated approaches (PECOTA, ZiPS, THE BAT X) regress toward a player-type-specific average, accounting for the fact that fast ground-ball hitters have a different true-talent BABIP than slow fly-ball hitters.

### 4.3 Age Curves for AVG and Components

| Component | Peak Age | Decline Pattern |
|-----------|----------|----------------|
| BABIP | **28** (improves from 20 to 28, then declines) | Earliest to decline; driven by speed/athleticism loss |
| Contact ability (1 - K%) | **25** (earliest peak) | Strikeouts increase from 25 onward |
| ISO (power) | **30** | Holds longest before declining |
| BB% | **28-34** | Last component to decline; continues improving through early 30s |
| AVG overall | **29** | Combination of BABIP decline and K% increase |
| wRC+ | **26** | General offensive value |
| Sprint speed | **~22-24** | Continuous decline from earliest ages |

**Key pattern:** As players age:
1. **First to decline:** Speed (sprint speed) and contact ability -> BABIP and K% worsen
2. **Next to decline:** Power (after ~30)
3. **Last to decline:** Walk rate (improves until ~34)
4. **By age 34:** Every component except walk rate is declining

**Magnitude of BABIP aging:** A 23-year-old with a .290 BABIP can expect to peak at ~.300 around age 28, then decline back to .290 by age 32 -- modest changes that are easily masked by year-to-year noise.

---

## 5. Machine Learning Approaches

### 5.1 Multi-Layer Perceptron (Neural Network)

One study used ML to predict a player's season-long batting average given the previous year's statistics:
- **Best model:** Multi-layered perceptron (neural network) with MAE of **0.0545** on training/validation data and **0.0562** on held-out test data
- This is roughly a 55-point AVG error, meaning a projected .270 hitter actually hit anywhere from .215 to .325

### 5.2 XGBoost and Gradient Boosting

- XGBoost has been widely applied to baseball prediction problems
- For game-level prediction, XGBoost and logistic regression achieved accuracy of 0.89-0.93 with AUC-ROC of 0.97-0.98
- Feature importance analysis using XGBoost reveals which input features matter most
- XGBoost is well-suited for modeling complex nonlinear relationships and interactions among features

### 5.3 Marcel vs. Machine Learning

A particularly illuminating study built a full prediction system for NPB (Japanese baseball):
- **Marcel outperformed LightGBM** for player performance prediction
- This confirmed the well-known finding that for individual player stat projection, simple regression-based methods remain competitive with complex ML approaches
- **Why ML struggles:** Small sample sizes (each player-season is one data point), high noise-to-signal ratios, and the fact that weighted regression with proper shrinkage already captures most of the predictable variance
- **Where ML falls short:** Marcel struggles with players whose recent performance sharply diverges from previous trends; ML can theoretically capture these patterns but typically overfits on the small samples

### 5.4 Bayesian Approaches

**Bayesian Marcel (PyMC Labs):**
- Recasts Marcel in a Bayesian framework with uncertainty quantification
- Uses a **beta-binomial hierarchical model** that partially pools player data according to sample size
- Instead of fixed 5/4/3 weights, uses **Dirichlet-distributed weights** learned from data (shifted to ~6/2/1 for hard hit rate)
- Aging function with an estimated peak age
- Hierarchical random effect for league-wide mean regression
- Provides **full posterior distributions** rather than point estimates

**Jim Albert's Multilevel Model for AVG:**
- Compared three prediction methods: observed BA, xBA, and multilevel model estimates
- **Multilevel model performed best**, followed by xBA, then raw BA
- The approach models the probability of a hit as a function of launch variables through regression, then uses multilevel modeling to reflect similarity of individual regression models
- Posteriors can be conveniently **updated during the season** with new data

**Empirical Bayes / James-Stein:**
- James-Stein estimator achieved the lowest RMSE when forecasting future batting averages
- Both Bayes and James-Stein estimators outperformed naive forecasts (using a player's first 30-day average)
- These approaches formalize the intuition behind regression to the mean

### 5.5 Open-Source Projects and Datasets

- **[github.com/bdilday/marcelR](https://github.com/bdilday/marcelR)** -- Marcel projections in R
- **[github.com/rh2835/Baseball-Analytics](https://github.com/rh2835/Baseball-Analytics)** -- K-means clustering, linear regression, ridge regression for MLB predictions
- **[github.com/eric8395/baseball-analytics](https://github.com/eric8395/baseball-analytics)** -- SVM, gradient boost, random forest, CatBoost, XGBoost, MLP models
- **[github.com/nmcassa/baseball-prediction-model](https://github.com/nmcassa/baseball-prediction-model)** -- Python/sklearn models for game outcomes
- **[Kaggle: Baseball Databank](https://www.kaggle.com/datasets/open-source-sports/baseball-databank)** -- Historical MLB data
- **[mikhailtodes.github.io/Machine_Learning_Baseball](http://mikhailtodes.github.io/Machine_Learning_Baseball/)** -- ML batting average prediction project
- **[PyMC Labs: Bayesian Marcel](https://www.pymc-labs.com/blog-posts/bayesian-marcel)** -- Bayesian implementation

---

## 6. Key Research Questions for AVG

### 6.1 Components vs. Direct Projection?

**Answer: Component-based is theoretically superior, but the advantage is small in practice.**

- Projecting K% and HR rate directly is reliable (high year-to-year correlation)
- The BABIP component remains the bottleneck -- whether projected directly or via components (LD%, speed, EV), it retains substantial unpredictable variance
- The advantage of component projection is most pronounced for **small samples** (in-season updates, young players) where fast-stabilizing inputs like K% and exit velocity can outperform insufficient AVG data
- For full-season preseason projections with multiple years of data, the advantage narrows

### 6.2 How Much Does Luck Affect Year-to-Year AVG?

**A lot.**

- AVG's year-to-year correlation is only ~.515, meaning only ~26% of variance in H/PA is explained by prior year
- This means ~74% of the variance comes from factors other than persistent skill (including BABIP luck)
- AVG is **highly correlated with BABIP** (r = .79), and BABIP itself has a year-to-year correlation of only .35
- The worst projection system for stolen bases or home runs has an RMSE more than twice as low as the best projection for batting average
- Approximately 70% of players with extreme BABIP values regress toward .300 the following season

### 6.3 True-Talent BABIP by Player Type

True-talent BABIP varies primarily by:
1. **Speed:** Fast players have higher BABIP on ground balls (leg out infield hits)
2. **Line drive rate:** High LD% hitters sustainably have higher BABIP
3. **Ground ball tendency:** Higher GB% means more opportunities for speed to influence hits
4. **Infield fly ball rate:** Higher IFFB% mechanically depresses BABIP (automatic outs)

Most players' true-talent BABIP falls in a narrower range (.285-.315) than their observed single-season BABIP suggests.

### 6.4 Park Factors and AVG

- Park factors for batting average exist but are **noisy** and **handedness-specific**
- Most parks affect right-handed and left-handed hitters differently
- Statcast park factors provide more granular data (by batted ball type and handedness)
- Park factors are a "best guess" -- they don't perfectly strain out all park-related effects
- For an AL-only league, the relevant parks include Fenway (boosts AVG), Yankee Stadium, and other AL ballparks with varying AVG factors
- Park adjustments are incorporated into all major projection systems (Steamer, ZiPS, THE BAT X, PECOTA)

### 6.5 Platoon Splits and Predictive Value

- Most hitters perform better against opposite-hand pitchers (well-established platoon advantage)
- However, **yearly platoon split data is extremely noisy** -- small sample sizes swamp the true skill signal
- "Observed splits are one part true talent and one part random variation"
- Population-level platoon effects are more reliable than individual player splits
- For AVG prediction, using **league-average platoon adjustments by handedness** is generally more accurate than using individual player split data
- THE BAT X and ZiPS both incorporate platoon split adjustments

---

## 7. Historical Accuracy of Projection Systems

### 7.1 Overall Rankings (Recent Years)

| Rank | System | Type | Notes |
|------|--------|------|-------|
| 1 | ATC | Aggregation | #1 for 5 consecutive years |
| 2 | THE BAT X | Original | #1 original system for 4+ years; first original to beat aggregates (2024) |
| 3 | Zeile (FantasyPros) | Aggregation (equal weights) | Consistent top-3 |
| 4 | Steamer | Original | Strong across all categories |
| 5 | ZiPS | Original | Strong, especially for pitchers |
| 6 | OOPSY | Original | #2 standalone in debut year (2025) |
| 7 | Davenport | Original | Strong 2024 performance |
| 8 | Razzball | Original/Modified Steamer | Strong 2024 performance |

### 7.2 AVG-Specific Accuracy

- **AVG is the hardest standard roto category to project:** The worst projection for SB or HR has RMSE more than twice as low as the best projection for AVG
- **Typical AVG projection MAE:** ~0.020-0.025 for major projection systems (i.e., projections are off by about 20-25 points of AVG on average for qualifying hitters)
- **ML approaches:** MAE of ~0.055 (substantially worse than established projection systems, likely due to less sophisticated regression and aging adjustments)
- **James-Stein / Bayes estimators** outperform naive methods but have been studied primarily in academic contexts rather than head-to-head with major systems

### 7.3 Component vs. Direct Projection Accuracy

There is no definitive study showing component-based approaches are significantly more accurate than direct projection for full-season preseason AVG projections. The theoretical advantage of components is offset by:
1. Error accumulation across multiple projected components
2. BABIP remaining noisy regardless of approach
3. The interaction effects between components

However, component-based approaches likely excel in:
- **In-season updates** (leveraging fast-stabilizing metrics)
- **Young player projections** (where component data may exist from minors)
- **Identifying regression candidates** (players with sustainable vs. unsustainable AVG levels)

### 7.4 Recommendations for the Moonlight Graham League

For an AL-only roto league with AVG as a scoring category:

1. **Use ATC or THE BAT X as your primary projection source** -- these have the strongest track record
2. **Supplement with component analysis** for identifying buy-low/sell-high candidates:
   - Hitters with AVG well below their component-implied level (high contact rate, good EV, speed) are undervalued
   - Hitters with AVG well above their sustainable BABIP are overvalued
3. **Monitor K% changes early in the season** -- K% stabilizes in 60-150 PA and strongly predicts AVG direction
4. **Use exit velocity as an early-season signal** -- stabilizes at ~40 BIP, weeks before AVG becomes meaningful
5. **Apply player-type BABIP regression** rather than blanket regression to .300 -- fast players and high-LD% hitters legitimately have higher BABIP
6. **Weight aggregate projections** -- combining 3-4 systems consistently outperforms any single system
7. **Account for AL-specific park factors** -- Fenway, Minute Maid, Yankee Stadium, etc. affect AVG differently

---

## Sources

### Projection Systems
- [A Guide to the Projection Systems - Beyond the Box Score](https://www.beyondtheboxscore.com/2016/2/22/11079186/projections-marcel-pecota-zips-steamer-explained-guide-math-is-fun)
- [Projection Systems - FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/projections/)
- [The Projection Rundown - FanGraphs Sabermetrics Library](https://library.fangraphs.com/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/)
- [Marcel the Monkey Forecasting System - Baseball-Reference](https://www.baseball-reference.com/about/marcels.shtml)
- [Steamer - MLB Glossary](https://www.mlb.com/glossary/projection-systems/steamer)
- [ZiPS - MLB Glossary](https://www.mlb.com/glossary/projection-systems/szymborski-projection-system)
- [PECOTA - Wikipedia](https://en.wikipedia.org/wiki/PECOTA)
- [PECOTA 2025 Introduction - Baseball Prospectus](https://www.baseballprospectus.com/news/article/96300/pecota-week-pecota-2025-an-introduction/)
- [THE BAT X - Derek Carty](https://derekcarty.com/the_bat.html)
- [The ATC Projection System - RotoGraphs](https://fantasy.fangraphs.com/the-atc-projection-system/)
- [Depth Charts - FanGraphs Sabermetrics Library](https://library.fangraphs.com/depth-charts/)
- [OOPSY Introduction - FanGraphs](https://blogs.fangraphs.com/yet-another-projection-system-a-brief-introduction-to-oopsy/)
- [2026 ZiPS Projections - FanGraphs](https://blogs.fangraphs.com/the-2026-zips-projections-are-almost-here/)
- [2025 ZiPS Projections - FanGraphs](https://blogs.fangraphs.com/the-2025-zips-projections-are-imminent/)
- [Oliver - MLB Glossary](https://www.mlb.com/glossary/projection-systems/oliver)
- [Reviewing OOPSY's Debut Season - FanGraphs](https://blogs.fangraphs.com/reviewing-oopsys-debut-season/)

### BABIP and Components
- [BABIP - FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/babip/)
- [Examining the Components of Batting Average and BABIP - Hardball Times](https://tht.fangraphs.com/examining-the-components-of-batting-average-and-babip/)
- [Breaking Down BABIP: Ground Ball Batting Average - RotoGraphs](https://fantasy.fangraphs.com/breaking-down-babip-what-impacts-ground-ball-batting-average-for-hitters/)
- [Controlling the Strike Zone and Batting Average - Hardball Times](https://tht.fangraphs.com/controlling-the-strike-zone-and-batting-average/)
- [Predicting BABIP Using Batted Ball Data - FanGraphs Community](https://community.fangraphs.com/proejcting-babip-using-batted-ball-data/)
- [Simple xBABIP Calculator - Hardball Times](https://tht.fangraphs.com/simple-xbabip-calculator/)
- [What's the Best BABIP Estimator? - Hardball Times](https://tht.fangraphs.com/whats-the-best-babip-estimator/)

### Statcast and Expected Stats
- [Expected Batting Average (xBA) - MLB Glossary](https://www.mlb.com/glossary/statcast/expected-batting-average)
- [Augmenting xBA with Sprint Speed - MLB Technology Blog](https://technology.mlblogs.com/augmenting-statcast-expected-batting-average-with-sprint-speed-6be7f60770d2)
- [Sprint Speed Adjustment for xBA - RotoGraphs](https://fantasy.fangraphs.com/a-sprint-speed-adjustment-for-xba/)
- [Properly Diving Into Expected Stats - FanGraphs Community](https://community.fangraphs.com/properly-diving-into-expected-stats/)
- [Using Statcast Data to Predict Future Results - FanGraphs Community](https://community.fangraphs.com/using-statcast-data-to-predict-future-results/)
- [Yes, Hitter xStats Are Useful - FanGraphs](https://blogs.fangraphs.com/yes-hitter-xstats-are-useful/)
- [Improving Projections with Exit Velocity - Hardball Times](https://tht.fangraphs.com/improving-projections-with-exit-velocity/)
- [Statcast Bat Tracking - Baseball Savant](https://baseballsavant.mlb.com/leaderboard/bat-tracking)

### Stabilization and Sample Size
- [Sample Size - FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/sample-size/)
- [When Hitters' Stats Stabilize - Baseball Prospectus](https://www.baseballprospectus.com/fantasy/article/14215/resident-fantasy-genius-when-hitters-stats-stabilize/)
- [Strikeouts, Stabilization and Surprising Swings - RotoGraphs](https://fantasy.fangraphs.com/strikeouts-stabilization-and-suprising-swings/)
- [When Samples Become Reliable - FanGraphs](https://blogs.fangraphs.com/when-samples-become-reliable/)
- [Exit Velocity Stabilization - FanGraphs](https://blogs.fangraphs.com/exit-velocity-part-ii-looking-for-a-repeatable-skill/)

### Aging Curves
- [Aging Curve - FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/aging-curve/)
- [Checking In on the Aging Curve - FanGraphs](https://blogs.fangraphs.com/checking-in-on-the-aging-curve/)
- [Aging Curves Revisited: Damn Strikeouts - Hardball Times](https://tht.fangraphs.com/aging-curves-revisited-damn-strikeouts/)
- [Aging Gracefully: Advanced Stats Part II - Dynasty Guru](https://thedynastyguru.com/2019/02/27/aging-gracefully-approaching-aging-curves-and-advanced-stats-part-ii/)

### Projection Accuracy and Comparisons
- [Most Accurate Fantasy Baseball Projections 2024 - FantasyPros](https://www.fantasypros.com/2025/02/most-accurate-fantasy-baseball-projections-2024-results/)
- [Most Accurate Fantasy Baseball Projections 2025 - FantasyPros](https://www.fantasypros.com/2026/02/most-accurate-fantasy-baseball-projections-2025-results/)
- [2024 Projection Review: Batter Roto Stats - RotoGraphs](https://fantasy.fangraphs.com/2024-projection-review-batter-roto-stats/)
- [2023 Projection Showdown: THE BAT X vs Steamer AVG Part 1 - RotoGraphs](https://fantasy.fangraphs.com/2023-projection-showdown-the-bat-x-vs-steamer-batting-average-forecasts-part-1/)
- [2023 Projection Showdown AVG Part 1 Review - RotoGraphs](https://fantasy.fangraphs.com/2023-projection-showdown-the-bat-x-vs-steamer-batting-average-forecasts-part-1-a-review/)
- [Projection Wars: Which System Is Best? - MLB Data Warehouse](https://www.mlbdatawarehouse.com/p/projection-wars-which-system-is-best)

### Machine Learning
- [Batting Average Prediction via ML - Mikhail Todes](http://mikhailtodes.github.io/Machine_Learning_Baseball/)
- [Why Marcel Beat LightGBM - DEV Community](https://dev.to/yasumorishima/why-marcel-beat-lightgbm-building-an-npb-player-performance-prediction-system-2jcb)
- [Bayesian Marcel - PyMC Labs](https://www.pymc-labs.com/blog-posts/bayesian-marcel)
- [Predicting AVG Using xBA and a Multilevel Model - Jim Albert](https://baseballwithr.wordpress.com/2020/02/17/predicting-avg-using-xba-and-a-multilevel-model/)
- [Empirical Bayes Estimation Using Baseball Statistics - Variance Explained](http://varianceexplained.org/r/empirical_bayes_baseball/)
- [Hierarchical Bayesian Modeling of Hitting - Wharton](http://stat.wharton.upenn.edu/~stjensen/papers/shanejensen.traj09.pdf)
- [Application of ML Models for Baseball Outcome Prediction - MDPI](https://www.mdpi.com/2076-3417/15/13/7081)

### Year-to-Year Correlations
- [Basic Hitting Metric Correlation - FanGraphs](https://blogs.fangraphs.com/basic-hitting-metric-correlation-1955-2012-2002-2012/)
- [What Hitting Metrics Correlate Year-to-Year - Beyond the Box Score](https://www.beyondtheboxscore.com/2011/9/1/2393318/what-hitting-metrics-are-consistent-year-to-year)
- [Understanding Projections and True Talent Level - FanGraphs](https://library.fangraphs.com/understanding-projections-true-talent-level-and-variability/)

### Plate Discipline
- [Plate Discipline - FanGraphs Sabermetrics Library](https://library.fangraphs.com/offense/plate-discipline/)
- [Going Deep: Whiffs and Ks - Pitcher List](https://pitcherlist.com/going-deep-the-relationship-between-whiffs-and-ks/)
- [K% and BB% - FanGraphs Sabermetrics Library](https://library.fangraphs.com/offense/rate-stats/)
- [Swing Decision Metrics - Adam Salorio](https://adamsalorio.substack.com/p/a-closer-look-at-swing-decision-metrics)

### Park Factors and Splits
- [Park Factors - FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/park-factors/)
- [Statcast Park Factors - Baseball Savant](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)
- [Splits - FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/split/)
- [Three-Year Lefty-Righty Splits for Each MLB Park - Baseball America](https://www.baseballamerica.com/stories/three-year-lefty-righty-splits-for-each-mlb-park/)

### Building Your Own System
- [FanGraphs Prep: Build Your Own Projection System](https://blogs.fangraphs.com/fangraphs-prep-build-and-test-your-own-projection-system/)
- [10 Lessons About Creating a Projection System - Hardball Times](https://tht.fangraphs.com/10-lessons-i-have-learned-about-creating-a-projection-system/)
- [Projections 101 - Royals Review](https://www.royalsreview.com/2016/10/5/13097770/projections-101-lets-build-a-projection-system)
- [Learning About Hitting Ability Using Components of Batting Average - Jim Albert](https://baseballwithr.wordpress.com/2022/06/20/learning-about-hitting-ability-using-components-of-batting-average/)
- [Making Sense of a Batting Average - Jim Albert](https://baseballwithr.wordpress.com/2020/10/26/making-sense-of-a-batting-average/)

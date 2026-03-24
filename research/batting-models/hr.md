# Home Run Rate Prediction (HR/PA)

Research for projecting HR rates in the Moonlight Graham AL-only rotisserie league.

---

## 1. HOME RUN Rate Prediction (HR/PA)

### 1.1 Statcast-Based HR Models

#### Barrel Rate as the Primary Predictor
- Barrel rate is the **single strongest predictive Statcast metric** for forecasting future home runs.
- A barrel requires a minimum exit velocity of 98 mph; at 116 mph, launch angles of 8-50 degrees qualify.
- **85.8% of home runs are barrels**, and **50.2% of all barrels are home runs**.
- Barrels over a player's previous 100 batted balls in play were a **better predictor of the next batted ball being a home run than HR rate itself**.
- Barrel rate has a correlation of **r = 0.73** with home run rate.
- Barrel% per fly ball (Barrel FB%) is the **best single metric** for predicting how well a hitter can convert fly balls into home runs and whether his HR/FB% will regress.

#### Exit Velocity Metrics
- **80th percentile exit velocity** is the strongest predictor of future power output, outperforming both average and max exit velocity.
- EV90 (90th percentile) is more stable year-to-year than Max EV, providing a more reliable measure of power upside.
- EV50 (median EV) correlates well with barrels (r = 0.524) and barrels/PA (r = 0.641).
- Average exit velocity has a **high correlation** with wOBA, HR%, and ISO.
- For forecasting power specifically, **exit velocity on FB/LD** is more descriptive and predictive than overall average EV.

#### Launch Angle and HR Probability
- Home run probability is maximized at approximately **28 degrees** for hard-hit balls between 100-105 mph.
- Hitters with an average launch angle of 25+ degrees had an HR/FB of approximately **20%** in 2023.
- Statcast compares every batted ball to similar historical batted balls and assigns a HR probability based on exit velocity, launch angle, and spray angle.

#### How xHR (Expected Home Runs) is Calculated
- Every batted ball is compared to those with similar exit velocity, launch angle, and spray angle characteristics.
- If that specific contact resulted in a HR 75% of the time historically, the batted ball is recorded as 0.75 HR, then summed across all contacts.
- Adding **spray angle as a third predictor variable** (beyond EV and LA) in a GAM model **dramatically reduced RMSE**.
- **xHR% has an R-squared of 0.642** with second-half xHR% (comparable to K% or BB% reliability).
- **xHR% has an R-squared of 0.465** predicting second-half actual HR% from first-half xHR%.
- First-half xHR error (HR% minus xHR%) has only **R-squared of 0.08** with second-half error, meaning over/underperformance doesn't persist.

#### Hard Hit Rate
- Hard hit rate (HH%) = percentage of batted balls hit at 95+ mph.
- Hard% has a **relatively strong relationship** with both HR/FB% and ISO.
- **44% of the variance in HR/FB%** is predictable from Hard% alone.
- "Dynamic hard-hit rate" is more powerful than standard hard-hit rate for describing same-year contact quality and predicting next-year contact quality.

#### Pull Rate and HR Rate
- A hitter's run production increases the more they pull the ball.
- Players like Alex Bregman are far more likely to hit HR by pulling fly balls down the line.
- Pull FB% is a variable in the xHR/FB v4.0 equation (coefficient: 0.127).
- **Average absolute spray angle** of homers and flies has limited year-to-year stability (r = 0.157), suggesting only slight persistence in pulling tendency.

#### Fly Ball Distance
- Average HR + FB distance has a year-to-year correlation of **r = 0.61**.
- Average fly ball distance does a **better job explaining current-season HR/FB** than prior-season HR/FB rate.
- Standard deviation of fly ball distance is also important: a hitter who hits two FBs at 325 feet gets 0 HR; one who hits 450 and 200 feet gets 1 HR.
- Including both average distance and standard deviation in a regression yields **adjusted R-squared of 0.629** for HR/FB rate.

### 1.2 Traditional HR Rate Models

#### HR/FB Rate: True Talent or Luck?
- **For pitchers:** League average is approximately 10%; true talent for almost every pitcher falls between 8-12%. It takes 400+ fly balls to confidently distinguish a pitcher from league average.
- **For hitters:** HR/FB is more of a true talent, though it still has meaningful year-to-year variance.
- Year-to-year HR/FB rate has an r-squared of **0.447** (vs. 0.486 for xHR/FB predicting next-year HR/FB), meaning **xHR/FB is a slightly better predictor than actual HR/FB**.
- Using hard hit rate on fly balls (HH%-FB), barrel rate per PA (BB/PA), and FB%, researchers achieved a **0.84 correlation coefficient** (adjusted R-squared = 0.71) for all players with 100+ PA.

#### The xHR/FB Rate v4.0 Equation
The FanGraphs batter xHR/FB equation (version 4.0):

```
xHR/FB+LD = -0.462976419
  + (Std Dev of Dist FB+LD * 0.001638039)
  + (Avg Dist FB+LD * 0.001176657)
  + (Barrel FB% * 0.172323325)
  + (Barrel LD% * 0.151220016)
  + (Pull FB% * 0.127471647)
  + (Pull LD% * 0.032113658)
  + (Oppo FB% * 0.038808565)
```

Key notes:
- Uses Statcast definitions of fly balls and line drives (not FanGraphs definitions).
- Output is xHR/FB+LD rate, not directly comparable to FanGraphs HR/FB.
- Barrel FB%, Barrel LD%, Pull FB%, and distance metrics are the key inputs.

#### Fly Ball Rate as a HR Driver
- Strong correlation between fly ball percentage and home run total.
- Fly ball hitters hit more HR per at-bat **and** per fly ball than other batter types.
- Elite sluggers generally post fly ball rates around **40%**.
- A healthy FB% makes a high Hard Flyball% (HH%-FB) much more meaningful.

#### ISO and SLG as HR Predictors
- ISO (Isolated Power) is the **most predictive traditional stat** for extra-base hits.
- ISO takes approximately **550 plate appearances** to become predictive of future ISO.
- xISO (expected ISO from Statcast) can better predict future power output than actual ISO.
- HR/BBE (HR per balls in play) as a rate stat has better year-to-year correlation than raw HR counting stats.

#### Age Curves for HR Rate
- **Peak for wRC+:** Age 26.
- **ISO holds steady until age 30**, then declines.
- Max exit velocity peaks near **age 26** and begins to decline, with decline accelerating at age 31.
- Bat speed and EV peak around **age 25**, then slow, tapered decline through the 20s, steepening in the 30s.
- An odd quirk: **ability declines before performance does** -- exit velocity declines years before home runs do.
- Players lose roughly **0.5 WAR per year** after age 30 due to aging.

#### Park Factor Effects on HR Rate
- Park factors are calculated controlling for batter and pitcher handedness.
- Parks play differently for left-handed vs. right-handed batters.
- Example: Oracle Park's right field is so difficult for left-handed pulled barrels that the HR rate dropped from the 73.6% league average to **48.7%** (3+ standard deviations below mean).
- Some advanced models use semiparametric binomial regression and hierarchical GAMs for park-adjusted HR probability, accounting for launch speed, launch angle, ball location, temperature, and stadium-batter-side effects.
- Temperature and weather can change batted ball distance by **more than 20%**.
- A HR park factor of 1.03 means the park boosts HRs by 3% above average.

### 1.3 Component Approach to HR

HR can be decomposed as approximately:

```
HR = PA x BIP_Rate x FB% x HR/FB%
```

Where BIP_Rate = (1 - K% - BB% - HBP%)

Which components are most predictable?
- **K%** stabilizes at approximately **60 PA** (extremely quick).
- **BB%** stabilizes at approximately **100-120 PA**.
- **FB%** stabilizes within 1-2 months of data.
- **HR/FB%** is the least stable component, requiring 400+ fly balls for pitchers; for hitters, xHR/FB provides a better estimate.
- **ISO** takes ~550 PA to stabilize.
- **Batting average** takes 900+ PA to stabilize.

**Recommendation for modeling:** K% and BB% stabilize fastest and are most reliable inputs. FB% is moderately reliable. HR/FB% should be supplemented/replaced with Statcast-derived xHR/FB using barrel rate, EV, and distance metrics.

### 1.4 League-Relative Statcast Power Metrics for Regression Detection

A powerful approach from FanGraphs research:
- **Group A (Non-Optimal):** High HardHit% and maxEV but low Barrel% -- **72.2%** of these hitters increased Barrel% the next season (vs. 53.4% baseline).
- **Group B (Optimal):** Low HardHit% and maxEV but high Barrel% -- only **36.1%** increased Barrel%; **64%** declined.
- This provides a directional signal for whether a hitter's HR/FB (and therefore HR rate) will rise or fall.

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

### Feature Importance: Home Runs

#### Home Runs
- **Most important features:** Prior-year HR, barrel rate, exit velocity (80th/90th percentile), FB%, ISO, launch angle.
- Bat speed, bat mass, and rotational acceleration (from bat sensor data) are highly predictive in one scientific study (Nature Scientific Reports).
- A bat speed of 33.3 m/s and rotational acceleration exceeding 157 m/s^2 predict a rapid increase in annual HR.


### Interaction Effects Relevant to HR

Key interaction effects to consider in ML models:
- **HR x BattingOrder** for RBI (power hitters in middle of order amplify RBI).
- **OBP x TeamQuality** for R (high OBP is more valuable in a good lineup).
- **Speed x OBP** for SB (fast players who also reach base frequently steal more).
- **FB% x Barrel%** for HR (fly balls are only valuable for HR if they're barreled).
- **ParkFactor x Handedness** for HR (park effects differ dramatically by batter side).

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

### 8.3 Is HR/FB rate a true talent or largely luck?

**For hitters: mostly true talent, with meaningful variance.**
- Year-to-year HR/FB r-squared: **0.447**.
- xHR/FB (from barrel rate, EV, distance) predicts next-year HR/FB with r-squared: **0.486** (slightly better).
- Barrel rate, exit velocity, and distance metrics capture the underlying skill.
- However, HR/FB still has enough variance that regression toward each player's projected xHR/FB is warranted.

**For pitchers: mostly luck.**
- True talent range for almost all pitchers is 8-12%.
- Takes 400+ fly balls to distinguish from average.
- Heavily influenced by park, defense, and random variance.

### 8.4 How much do park factors matter for HR rate prediction?

**They matter significantly, especially when considering handedness.**
- Park factor effects can swing HR rates by 10-30% for extreme parks.
- Handedness matters enormously: Oracle Park's right field suppresses LHH pulled barrel HR rate from 73.6% to 48.7%.
- Temperature and altitude matter: Coors Field vs. Oracle Park can represent a 40%+ swing in HR rate.
- For an AL-only league, you have 15 parks to model. Key extreme parks include:
  - **HR-boosting:** Yankee Stadium (especially RHH to RF), Guaranteed Rate Field, Fenway (RHH)
  - **HR-suppressing:** Tropicana Field, T-Mobile Park (especially RHH), Oakland Coliseum
- Advanced models use hierarchical GAMs with stadium-batter-side interactions.

## 9. Recommended Model Architecture for Counting Stat Rates

Based on all research, here is the recommended approach for each rate stat:

### HR/PA Model
**Primary inputs:**
1. Barrel rate (Barrel%) -- strongest single predictor
2. Exit velocity, 80th/90th percentile on FB+LD
3. Average and std dev of fly ball distance
4. FB% (fly ball rate)
5. Pull FB%
6. Launch angle (average, sweet spot%)
7. Park factors (by handedness)
8. Age (aging curve adjustment)

**Supplementary:**
- Prior-year HR/PA (regressed toward xHR/PA)
- ISO, SLG
- K% (as proxy for contact rate / component model)

**Approach:** Build xHR/PA from Statcast metrics, then blend with regressed historical HR/PA.

---

## Sources

### Home Run Rate Prediction
- [Statcast Exit Velocity & Launch Angle Breakdown](https://baseballsavant.mlb.com/statcast_field)
- [Home Runs -- Beyond Launch Angle and Exit Velocity](https://baseballwithr.wordpress.com/2021/03/15/home-runs-beyond-launch-angle-and-exit-velocity/)
- [Statcast 101: Barrels, Launch Angle, and Sweet Spot Percentage](https://www.thedynastydugout.com/p/statcast-101-barrels-launch-angle-sweet-spot)
- [Determining xHR for a Pitcher](https://fantasyindex.com/2024/01/06/fantasy-baseball-index/determining-xhr-for-a-pitcher)
- [How Predictive Is Expected Home Run Rate?](https://blogs.fangraphs.com/how-predictive-is-expected-home-run-rate/)
- [Introducing Batter xHR/FB Rate, Version 4.0: The Equation](https://fantasy.fangraphs.com/introducing-batter-xhr-fb-rate-version-4-0-the-equation/)
- [Introducing Batter xHR/FB Rate, Version 4.0: The Research](https://fantasy.fangraphs.com/introducing-batter-xhr-fb-rate-version-4-0-the-research/)
- [The Quest to Predict HR/FB Rate, Parts 1-5](https://fantasy.fangraphs.com/the-quest-to-predict-hrfb-rate-part-1/)
- [HR/FB Sabermetrics Library](https://library.fangraphs.com/pitching/hrs/)
- [Using Regression Analysis for HR/FB Rate](https://www.insiderbaseball.com/blog/2018/01/using_regression_analysis_for_hrfb_rate.html)
- [Fantasy Baseball: Using Expected HR/FB Rate](https://fantraxhq.com/fantasy-baseball-using-expected-hr-fb-rate-to-analyze-hitters/)
- [How League-Relative Statcast Power Metrics Forecast Next Year's Rates](https://fantasy.fangraphs.com/how-league-relative-statcast-power-metrics-forecast-next-years-rates/)
- [HR/FB Surgers & Decliners Using League-Relative Statcast Power Metrics](https://fantasy.fangraphs.com/hr-fb-surgers-decliners-using-league-relative-statcast-power-metrics/)
- [Using Exit Velocity Percentiles for Fantasy Baseball](https://fantraxhq.com/using-exit-velocity-percentiles-for-fantasy-baseball/)
- [How Barrel Rate Helps Fantasy Baseball in 2026](https://sports.yahoo.com/articles/barrel-rate-helps-fantasy-baseball-192114887.html)
- [Validating High Hitter HR/FB Rates With Batted Ball Distance](https://fantasy.fangraphs.com/validating-high-hitter-hrfb-rates-with-batted-ball-distance/)
- [Getting to Know Batter Average Fly Ball Distance](https://fantasy.fangraphs.com/getting-to-know-batter-average-fly-ball-distance/)
- [Predicting Home Runs from Distance and Spray Angle](https://baseballwithr.wordpress.com/2024/04/08/predicting-home-runs-from-distance-and-spray-angle/)

### HR/FB and Stabilization
- [Sample Size -- Sabermetrics Library](https://library.fangraphs.com/principles/sample-size/)
- [Resident Fantasy Genius: When Hitters' Stats Stabilize](https://www.baseballprospectus.com/fantasy/article/14215/resident-fantasy-genius-when-hitters-stats-stabilize/)
- [The Beginner's Guide to Sample Size](https://library.fangraphs.com/the-beginners-guide-to-sample-size/)
- [Quality of Contact Stats](https://library.fangraphs.com/offense/quality-of-contact-stats/)

### Park Factors
- [Statcast Park Factors](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)
- [An Updated System of Park Factors (and Volatility)](https://www.baseballprospectus.com/news/article/64534/an-updated-system-of-park-factors-and-volatility/)
- [Park Factors -- Sabermetrics Library](https://library.fangraphs.com/principles/park-factors/)
- [A new way to dissect baseball's park factors](https://www.mlb.com/news/park-factors-measured-by-statcast)
- [Going Deep: Barrels and Ballpark Factors](https://pitcherlist.com/going-deep-barrels-and-ballpark-factors/)

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

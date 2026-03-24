# ERA and WHIP Prediction Methods: Comprehensive Research

## Table of Contents
1. [FIP-Based ERA Models](#1-fip-based-era-models)
2. [Component-Based ERA Models](#2-component-based-era-models)
3. [Statcast-Era ERA Models](#3-statcast-era-era-models)
4. [Defense and Context Adjustments](#4-defense-and-context-adjustments)
5. [WHIP Prediction Approaches](#5-whip-prediction-approaches)
6. [Major Projection Systems](#6-major-projection-systems)
7. [Regression and Stabilization](#7-regression-and-stabilization)
8. [Role-Specific Considerations](#8-role-specific-considerations)
9. [Machine Learning Approaches](#9-machine-learning-approaches)
10. [Historical Accuracy and Comparisons](#10-historical-accuracy-and-comparisons)
11. [Practical Implications for AL-Only Rotisserie](#11-practical-implications-for-al-only-rotisserie)

---

## 1. FIP-Based ERA Models

### FIP (Fielding Independent Pitching)

**Formula:**
```
FIP = ((13 * HR) + (3 * (BB + HBP)) - (2 * K)) / IP + FIP_constant
```

**FIP Constant:** Calculated so league-average FIP equals league-average ERA each season.
```
FIP_constant = lgERA - ((13 * lgHR) + (3 * (lgBB + lgHBP)) - (2 * lgK)) / lgIP
```
The constant typically falls around 3.10 - 3.20.

**Component Weights:**
- Home runs weighted at 13 (most damaging)
- Walks + HBP weighted at 3
- Strikeouts weighted at -2 (positive for pitcher)

**Predictive Accuracy:**
- Year-to-year correlation: r = 0.65 (vs ERA's r = 0.38)
- FIP is more predictive of future ERA than ERA itself
- RMSE for predicting next-year ERA: ~0.968

**Limitations:**
- Some pitchers consistently outperform or underperform their FIP over full careers
- Does not account for quality of contact
- Treats all balls in play equally

**Sources:**
- [FIP | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/fip/)
- [FIP | Baseball-Reference](https://www.baseball-reference.com/bullpen/Fielding_Independent_Pitching)
- [FIP | MLB Glossary](https://www.mlb.com/glossary/advanced-stats/fielding-independent-pitching)

---

### xFIP (Expected FIP)

**How it differs from FIP:** Replaces actual HR with expected HR based on league-average HR/FB rate applied to pitcher's fly balls.

**Formula:**
```
xFIP = ((13 * (FB * lgHR/FB_rate)) + (3 * (BB + HBP)) - (2 * K)) / IP + FIP_constant
```

**Rationale:** Individual HR/FB rates are highly variable and regress toward league average (~10%). By normalizing HR/FB, xFIP removes one of the noisiest components.

**Predictive Accuracy vs FIP:**
- RMSE for predicting next-year ERA: **0.892** (vs FIP's 0.968)
- Year-to-year correlation: r = 0.68 (vs FIP's 0.65)
- Consistently outperforms FIP for forward-looking analysis

**Sources:**
- [xFIP | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/xfip/)
- [xFIP | MLB Glossary](https://www.mlb.com/glossary/advanced-stats/expected-fielding-independent-pitching)

---

### SIERA (Skill-Interactive ERA)

**Creator:** Matt Swartz and Eric Seidman (introduced at Baseball Prospectus)

**Key Innovation:** Unlike FIP/xFIP which ignore batted ball outcomes, SIERA accounts for the interaction between strikeout rate, walk rate, and ground ball/fly ball rates.

**Formula:**
```
SIERA = 6.145
  - 16.986 * (SO/PA)
  + 11.434 * (BB/PA)
  - 1.858 * ((GB-FB-PU)/PA)
  + 7.653 * (SO/PA)^2
  +/- 6.664 * ((GB-FB-PU)/PA)^2
  + 10.130 * (SO/PA) * ((GB-FB-PU)/PA)
  - 5.195 * (BB/PA) * ((GB-FB-PU)/PA)
```

**Key Properties:**
- Favors high-K, high-GB pitchers
- Penalizes high-BB, high-FB pitchers
- Accounts for interaction effects (e.g., high-K pitchers benefit more from ground balls)
- Includes squared terms to capture non-linear relationships

**Predictive Accuracy:**
- RMSE for predicting next-year ERA: **0.871** (best among standard ERA estimators)
- Year-to-year correlation: r = 0.72 (highest among ERA estimators)
- Explains 20.4% of variance in subsequent-season ERA
- Slightly edges xFIP, meaningfully better than FIP and ERA

**Important caveat:** K-BB% alone is actually more predictive of future ERA than SIERA, xFIP, or FIP. The predictive formula: `future ERA = -0.0861 * (K-BB%) + 5.3793`

**Sources:**
- [SIERA | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/siera/)
- [Introducing SIERA | Baseball Prospectus](https://www.baseballprospectus.com/news/article/10027/introducing-siera-part-1/)
- [The Relative Value of FIP, xFIP, SIERA, and xERA Pt. II | Pitcher List](https://pitcherlist.com/the-relative-value-of-fip-xfip-siera-and-xera-pt-ii/)

---

### DRA (Deserved Run Average) - Baseball Prospectus

**Creators:** Jonathan Judge, Harry Pavlidis, Dan Turkenkopf

**Methodology:** Uses mixed-model regression to control for context factors on every pitching event.

**Context Adjustments:**
- Opposing hitter quality
- Park and temperature effects
- Catcher framing
- Umpire tendencies
- Handedness matchups
- Home-field advantage

**How it works:**
1. Each pitching event (K, BB, HR, BIP, etc.) is assigned a linear weight value
2. That value is adjusted for all context factors listed above
3. Base-stealing effects are factored in
4. The result is placed on a runs-per-nine-innings scale

**DRA- (minus scale):** 100 = league average, below 100 is better. Isolates pitcher contribution from defense, park, and opposition quality.

**Heritage:** Builds on Voros McCracken's DIPS theory, Tom Tango's FIP, and Colin Wyers' Fair Run Average.

**Sources:**
- [Introducing DRA | Baseball Prospectus](https://www.baseballprospectus.com/news/article/26195/prospectus-feature-introducing-deserved-run-average-draand-all-its-friends/)
- [DRA and DRA- Starter Guide | Baseball Prospectus](https://www.baseballprospectus.com/news/article/48108/dra-and-dra-a-starter-guide/)

---

### cFIP (Context-Adjusted FIP)

**Scale:** 100-centered "minus" scale (100 = average, lower = better, SD of 15)

**Methodology:**
Each FIP component (K, BB, HBP, HR) is modeled using mixed-model regression adjusting for:
- Individual batter quality
- Catcher and umpire effects
- Stadium/park factors
- Home-field advantage
- Umpire bias
- Handedness matchup

The adjusted counts are multiplied by standard FIP coefficients and summed.

**Key Advantages:**
1. More predictive than other estimators, especially in small samples
2. Uses batters faced (not IP) as denominator -- more accurate workload measure
3. Park-, league-, and opposition-adjusted
4. Equally accurate as both descriptive and predictive statistic

**Sources:**
- [FIP, In Context | The Hardball Times](https://tht.fangraphs.com/fip-in-context/)

---

### kwERA

**Formula:**
```
kwERA = constant + 11 * (UBB + HBP - SO) / PA
```
Where UBB = unintentional walks

**Properties:**
- Extremely simple -- uses only K, BB, and HBP
- Surprisingly powerful predictor of future ERA
- Serves as baseline for evaluating whether more complex models add value
- pFIP was more highly correlated with future ERA than kwERA, FIP, xFIP and SIERA (2004-2012 data)

**Sources:**
- [kwERA: The Starting Point | The Hardball Times](https://tht.fangraphs.com/kwera-the-starting-point-for-pitcher-evaluations/)

---

### Summary Table: ERA Estimator Comparison

| Metric | RMSE (Next-Year ERA) | Y-t-Y Correlation | R-squared (Next-Year ERA) | Best Use |
|--------|---------------------|-------------------|--------------------------|----------|
| ERA    | ~1.11               | 0.38              | ~0.14                    | Backward-looking |
| FIP    | 0.968               | 0.65              | ~0.17                    | In-season evaluation |
| xFIP   | 0.892               | 0.68              | ~0.19                    | Forward projection |
| SIERA  | 0.871               | 0.72              | 0.204                    | Forward projection |
| xERA   | 0.965               | --                | --                       | In-season evaluation |
| K-BB%  | < 0.871             | --                | > 0.204                  | Forward projection |

---

## 2. Component-Based ERA Models

### The Component Framework

ERA can be decomposed into underlying components:
```
ERA = f(K_rate, BB_rate, HR_rate, BABIP_against, LOB%)
```

The key question for each component: **How much is skill vs. luck?**

---

### Strikeout Rate (K%)

**Skill Classification:** Almost entirely pitcher skill

**Stabilization:** ~60-70 batters faced (very fast)

**Year-to-Year Correlation:** r = 0.84 (very sticky)

**Age Curve:** Peaks ages 22-28, tied closely to fastball velocity early, but pitchers who survive into 30s compensate with pitch mix and sequencing

**Key Insight:** The most stable and predictive pitching component. Foundation of all ERA models.

---

### Walk Rate (BB%)

**Skill Classification:** Mostly pitcher skill, but more variable than K%

**Stabilization:** ~170 batters faced

**Year-to-Year Correlation:** Moderate-high

**Age Curve:** Bottoms out around age 26, then climbs as velocity declines force pitchers to nibble

**Predictive Drivers:**
- First-Pitch Strike Rate (F-Strike%): Best predictor of future walk rate improvements
- Zone% shows surprisingly little correlation with walk rate
- Walk rates remain somewhat unpredictable due to umpire variability

**Sources:**
- [Ahead in the Count: Pitch Data and Walks | Baseball Prospectus](https://www.baseballprospectus.com/news/article/12087/ahead-in-the-count-pitch-data-and-walks/)
- [Command and Control | Baseball Prospectus](https://www.baseballprospectus.com/news/article/31022/prospectus-feature-command-and-control/)

---

### HR/FB Rate

**Skill Classification:** Mixed -- partially skill, heavily influenced by park and randomness

**League Average:** ~10% (fluctuates by era; rose significantly with juiced ball 2017-2019)

**Stabilization:** ~400+ fly balls (very slow; roughly 2+ full seasons for a starter)

**Regression Tendency:** Pitchers with HR/FB much above or below league average will regress. However, some pitchers sustain elevated/suppressed rates through:
- Extreme fly ball height (pop-up inducing)
- Low exit velocity profiles
- Favorable home parks

**Park Effects:** HR/FB is NOT park-adjusted in raw form. Home park dimensions and weather conditions naturally affect the rate. Must be considered in any model.

**Sources:**
- [HR/FB | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/hrs/)

---

### BABIP Against (Batting Average on Balls in Play)

**Skill Classification:** Overwhelmingly luck + defense; only ~7% of variance attributable to pitcher skill

**League Average for Pitchers:** ~.295-.300

**Stabilization:** ~2,000 balls in play (approximately 3 full seasons of starting pitcher work)

**Key Research Finding (Voros McCracken, 2000):** "There is little if any difference among Major League pitchers in their ability to prevent hits on balls hit into the field of play."

**Factors That Do Influence Pitcher BABIP:**
1. **Ground ball rate:** GB pitchers run higher BABIPs (~.230 hit rate on GBs vs ~.138 on FBs, but more total GBs)
2. **Line drive rate:** LD% is the strongest batted-ball correlate of BABIP
3. **Hard contact rate:** Pitchers who limit hard contact suppress BABIP
4. **Team defense quality:** Explains large portion of BABIP variance
5. **Knuckleballers and extreme outliers:** Can sustain unusual BABIP

**Expected BABIP Formula (eBABIP):**
```
eBABIP = LD% * 0.720 + GB% * 0.231 + FB% * 0.171 + PU% * 0.019
```
Alternative simplified: `xBABIP ~ LD% + 0.12`

**Implication for Projections:** Regress BABIP heavily toward ~.300, adjusted for:
- Ground ball rate
- Defense quality
- Career BABIP with large sample (if available)

**Sources:**
- [BABIP | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/babip/)
- [Expected BABIP for Pitchers | FanGraphs](https://blogs.fangraphs.com/expected-babip-for-pitchers/)
- [Understanding BABIP Pt. 1: Pitchers | Pitcher List](https://pitcherlist.com/understanding-babip-pt-1-pitchers/)

---

### LOB% (Left On Base Percentage / Strand Rate)

**Skill Classification:** Primarily luck, with a skill component for elite K pitchers

**League Average:** ~70-72%

**Year-to-Year Correlation:** R-squared = 0.048 (extremely low)

**Regression:** Most pitchers regress toward ~72%. Deviations in either direction are predominantly luck.

**Exceptions -- Skill Component:**
- High-K pitchers sustain LOB% above average (~78% for aces) because they can pitch out of jams via strikeouts
- Relievers naturally carry higher LOB% (~mid-80s) due to shorter outings and fresher arms
- Groundball pitchers may sustain slightly higher LOB% through double play opportunities

**Projection Implication:** Project ~72% for most pitchers. Adjust upward for:
- Elite K-rate pitchers (project ~75-78%)
- Relievers (project ~78-85%)
- Adjust downward for low-K pitchers who historically strand fewer runners

**Sources:**
- [LOB% | FanGraphs Sabermetrics Library](https://library.fangraphs.com/pitching/lob/)
- [xLOB%: Projecting a Pitcher's Left On Base Percentage | The Hardball Times](https://tht.fangraphs.com/xlob-projecting-a-pitchers-left-on-base-percentage/)

---

### Component ERA Model (Bill James' ERC)

**Component ERA** attempts to forecast ERA from hits, walks, and other components rather than the standard earned runs formula.

**The Gill and Reeve Formula** (used by Mastersball projections):
- Inputs: projected hits, strikeouts, walks, and home runs per nine innings
- Plus LOB% with a mean-regression factor
- Generates expected earned runs

---

## 3. Statcast-Era ERA Models

### xERA (Expected ERA from Statcast)

**Definition:** A 1:1 translation of xwOBA (Expected Weighted On-Base Average) converted to the ERA scale.

**How xwOBA is calculated:**
1. Each batted ball is assigned an expected outcome based on exit velocity and launch angle
2. Strikeouts, walks, and HBP are included at their actual values
3. The expected outcomes replace actual outcomes in the wOBA formula:
```
xwOBA = (UBB_factor * UBB + HBP_factor * HBP + expected_1B_factor * x1B +
         expected_2B_factor * x2B + expected_3B_factor * x3B +
         expected_HR_factor * xHR) / (AB + UBB + SF + HBP)
```

**Conversion to ERA scale:** Direct mathematical mapping from xwOBA to ERA.

**What it captures that FIP does not:**
- Quality of contact (exit velocity, launch angle)
- Barrel rate against
- Soft contact rates
- Does NOT require HR/FB assumptions

**Predictive Accuracy:**
- RMSE for predicting next-year ERA: **0.965** (roughly equal to FIP)
- Less predictive than xFIP and SIERA for future ERA
- Better than FIP for in-season descriptive purposes (r^2 = 0.996 in-season correlation)
- Does not account for park, defense, or weather

**Sources:**
- [Expected ERA (xERA) | MLB Glossary](https://www.mlb.com/glossary/statcast/expected-era)
- [ERA Estimators, Pt. II: Present | FanGraphs RotoGraphs](https://fantasy.fangraphs.com/era-estimators-pt-ii-present/)

---

### Stuff+ / Location+ / Pitching+ (FanGraphs PitchingBot)

**System:** FanGraphs' PitchingBot pitch-quality model using gradient boosting.

**Three Components:**

**Stuff+ (botStf):**
- Evaluates physical characteristics of each pitch only
- Inputs: release point, velocity, vertical/horizontal movement, spin rate, extension, pitcher handedness, batter handedness, count
- Measures pitch quality independent of location
- Becomes reliable after ~80 pitches (very fast)
- Scale: 100 = average, each point = ~0.3 runs/100 pitches

**Location+ (botCmd):**
- Evaluates pitch location only
- Less stable than Stuff+ within and between seasons
- Measures command quality independent of stuff

**Pitching+ (botOvr):**
- Combined model using stuff, location, and count
- NOT simply a weighted average of Stuff+ and Location+
- Most predictive overall metric

**ERA Prediction:**
- Pre-season Pitching+ has lower RMSE than most projection systems for predicting ERA
- In-season, Pitching+ beats pre-season projections by ~400 pitches (~4-5 starts)
- Stuff+ to ERA conversion: `ERA ~ 49.19 * e^(-0.025 * Stuff+)` (r^2 = 0.996)
- Stuff quality is more stable than location quality both within and between seasons

**Limitations:**
- ERA strongly influenced by parks and defense; Stuff+ does not account for these
- Predictive power weakens for pitchers who change teams
- Works better with same-team context

**Sources:**
- [Stuff+, Location+, and Pitching+ Primer | FanGraphs](https://library.fangraphs.com/pitching/stuff-location-and-pitching-primer/)
- [PitchingBot Pitch Modeling Primer | FanGraphs](https://library.fangraphs.com/pitching/pitchingbot-pitch-modeling-primer/)
- [Referencing Pitch Quality Models | FanGraphs RotoGraphs](https://fantasy.fangraphs.com/referencing-pitch-quality-models-to-more-traditional-stats/)

---

### StuffPro / PitchPro (Baseball Prospectus)

**Methodology:** Machine learning models predicting probability of each possible pitch outcome.

**Model Structure (Decision Tree):**
1. Is the pitch swung at?
2. If no swing: called strike, called ball, or HBP?
3. If swing: foul, whiff, or ball in play?
4. If ball in play: what is the result?

**Each probability is multiplied by the run value of that event and summed to get expected run value per pitch.**

**Key Distinction:**
- StuffPro: Based on physical pitch characteristics + release + count + handedness
- PitchPro: Adds context and general location
- Both produced on a pitch-type basis on a run value scale

**Sources:**
- [Introducing StuffPro and PitchPro | Baseball Prospectus](https://www.baseballprospectus.com/news/article/89245/stuffpro-pitchpro-introduction-new-pitch-metrics-bp/)

---

### pSTFERA Suite (Prospects Live)

**Four Metrics:**
1. **pSERA** (Predictive Stuff ERA)
2. **pLERA** (Predictive Location ERA)
3. **pPERA** (Predictive Pitching ERA)
4. **pAERA** (Predictive Arsenal ERA)

**Methodology:**
- Uses silhouette cluster analysis to determine optimal pitch groupings
- Mean and SD of each cluster's ERA allows conversion to ERA scale
- Cluster-based z-scores generate predictive ERA

**Performance:**
- Stabilizes much faster than traditional metrics
- Significantly predictive around 10 IP minimum threshold
- R-squared values range 0.0 to 0.6
- pSERA had best performance among all metrics in almost all samples
- FanGraphs metrics never matched the R^2 achieved by pSTFERA at 10 IP

**Sources:**
- [The Creation of Predictive Stuff Metrics: pSTFERA Suite | Prospects Live](https://www.prospectslive.com/the-creation-of-predictive-stuff-metrics-introducing-the-pstfera-suite/)

---

## 4. Defense and Context Adjustments

### Defensive Quality Behind the Pitcher

**Impact:** Defense quality is one of the largest non-pitcher factors in ERA. The difference between the best and worst team defenses can swing a pitcher's BABIP by .020-.040, translating to meaningful ERA differences.

**Measurement:**
- Defensive Runs Saved (DRS)
- Ultimate Zone Rating (UZR)
- Outs Above Average (OAA) from Statcast

**In Projection Systems:**
- ZiPS specifically adjusts pitcher BABIP projections for the defense behind them, which is why pitcher projections can change dramatically with team changes
- Steamer regresses BABIP toward average for players with similar tendencies

---

### Catcher Framing Effects

**Magnitude:** An extra called strike saves ~0.135 runs

**Impact on Pitchers:**
- One unit increase in catcher FRM (framing) associated with 0.025 unit increase in K/9
- Difference between best and worst framing catchers: ~20 runs per season
- Affects pitcher K rate, BB rate, and by extension ERA and WHIP

**Park Adjustment:** Framing numbers should be park-adjusted, as some parks naturally yield more strike calls.

**Sources:**
- [Catcher Defense | FanGraphs](https://library.fangraphs.com/defense/catcher-defense/)
- [FanGraphs Pitch Framing](https://blogs.fangraphs.com/fangraphs-pitch-framing/)
- [Framing and Blocking Pitches | Baseball Prospectus](https://www.baseballprospectus.com/news/article/22934/framing-and-blocking-pitches-a-regressed-probabilistic-model-a-new-method-for-measuring-catcher-defense/)

---

### Park Factor Adjustments

**How Park Factors Work:**
- 1.00 = league average
- Above 1.00 = hitter-friendly
- Below 1.00 = pitcher-friendly

**What Park Factors Affect:**
- HR rate (most variable park effect)
- BABIP (due to outfield dimensions, surface)
- K rate (altitude effects on breaking balls)
- Overall run scoring

**Application:** ERA-, FIP-, xFIP- all adjust for park factors. Raw ERA/FIP/WHIP do not.

**Consideration for AL-Only:** Since you're working with only AL parks, park factor variation is still significant (e.g., Yankee Stadium vs. Oakland Coliseum vs. Tropicana Field).

**Sources:**
- [Park Factors | FanGraphs Sabermetrics Library](https://library.fangraphs.com/principles/park-factors/)
- [Understanding Park Factors | FanGraphs](https://library.fangraphs.com/the-beginners-guide-to-understanding-park-factors/)

---

## 5. WHIP Prediction Approaches

### Component Decomposition

```
WHIP = (BB + H) / IP = BB/IP + H/IP
```

Two distinct sub-problems:
1. **BB/IP (Walk Rate):** Higher skill, faster stabilization
2. **H/IP (Hits per Inning):** Lower skill, driven by BABIP, K rate, defense

---

### Walk Rate (BB/IP) Prediction

**Stability:** Moderate-high; stabilizes in ~170 BF

**Key Predictors:**
- **F-Strike% (First-Pitch Strike Rate):** Best predictor of future walk rate improvements. Pitchers who throw first-pitch strikes but subsequently walk batters can adjust approach.
- **Zone%:** Surprisingly poor predictor; throwing in the zone has little correlation with walk rate
- **O-Swing%:** Decent metric but not guaranteed to reduce walks
- Career walk rate (weighted recent years)

**Age Curve:** Walk rate bottoms around age 26, then rises as velocity declines force nibbling

**Projection Approach:**
- Weight 3 years of walk rate data (recent years heavier)
- Regress toward league average
- Adjust for age
- Consider F-Strike% for additional signal

---

### Hits/IP Prediction

**Primary Drivers:**
1. **BABIP against:** Dominates the hits component
2. **K rate:** Higher K = fewer balls in play = fewer hits
3. **Ground ball rate:** GB pitchers allow more singles but fewer XBH
4. **Infield defense quality:** Major impact on ground ball hits

**Expected BABIP → Expected H/IP Pipeline:**
```
Expected BABIP = LD% * 0.720 + GB% * 0.231 + FB% * 0.171 + PU% * 0.019
Expected H/BIP = Expected BABIP
Expected H/IP = Expected H/BIP * BIP/IP = Expected BABIP * (1 - K% - BB% - HR/IP_fraction)
```

**Ground Ball vs Fly Ball Effect on H/IP:**
- Ground balls: ~23.8% become hits
- Fly balls: ~13.8% become hits
- But GB pitchers avoid HRs, which don't factor into WHIP but do factor into ERA

**Defense Quality Impact:**
- Difference between .253 and .209 BABIP on ground balls = ~86 fewer ground ball hits per season
- Infield defense is the primary lever for GB pitcher BABIP

**Projection Approach:**
- Project K rate, BB rate, GB/FB/LD rates
- Use batted-ball profile to estimate expected BABIP
- Adjust for team defense
- Calculate expected hits = expected BABIP * expected BIP
- WHIP = (projected BB + projected H) / projected IP

---

### WHIP as a Predictor

- WHIP stabilizes faster than ERA
- WHIP tends to be more predictive of future ERA than ERA itself
- Pitchers with consistently low WHIP tend to maintain run-prevention success
- In short samples (early season, relievers), WHIP gives a clearer signal than ERA

---

## 6. Major Projection Systems

### Marcel (Tom Tango)

**Philosophy:** "The minimum level of competence that you should expect from any forecaster." Deliberately simple baseline.

**Methodology:**
1. **Weighted Average:** 3 years of data, weights 3/2/1 (most recent highest) for pitchers
2. **Regression to Mean:** Reliability = weighted_outs / (weighted_outs + 134_outs). So ~44.2 IP of regression toward league average.
3. **Age Adjustment:** Under 29: increase by (29 - age) * 0.006. Over 29: decrease by (age - 29) * 0.003.
4. **Playing Time:** Projected from weighted recent playing time

**Pitching Specifics:** Weights of 3/2/1 for previous three seasons; 134 outs (~44.2 IP) of regression.

**Sources:**
- [Marcel the Monkey | Baseball-Reference](https://www.baseball-reference.com/about/marcels.shtml)
- [Projection Rundown | FanGraphs](https://library.fangraphs.com/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/)

---

### Steamer

**Methodology:** Enhanced Marcel approach using regression-optimized weights.

**Key Differences from Marcel:**
- Weighting of years and regression amounts vary by statistic, optimized via regression analysis of historical data
- For pitching ERA: uses expected runs based on K/9, BB/9, HR/9, H/9
- Applies LOB% with mean-regression factor
- BABIP forecast based on individual tendencies (GB rate, defense, pitch type) heavily regressed

**ERA Calculation:**
- Component-based: projects K, BB, HR, H rates
- Calculates expected ERA similar to FIP-style calculation
- Correctly regresses luck metrics (BABIP, LOB%, HR/FB) toward mean

**Strengths:** Consistently among the most accurate systems overall (led all categories in 2015 analysis). Reliable for pitching.

**Weaknesses:** Struggles with pitchers who show consistent BABIP or HR/FB suppression skills. Heavy regression misses on uncommon exceptions.

**Sources:**
- [A Guide to Projection Systems | Beyond the Box Score](https://www.beyondtheboxscore.com/2016/2/22/11079186/projections-marcel-pecota-zips-steamer-explained-guide-math-is-fun)
- [Projection Systems | FanGraphs](https://library.fangraphs.com/principles/projections/)

---

### ZiPS (Dan Szymborski)

**Methodology:** Hybrid weighted-average + comparable-player system

**Key Features:**
- Uses 4 years of weighted data
- PECOTA-like comparison system for age adjustments
- Incorporates DIPS theory but with nuance
- BABIP projected using individual tendencies (GB rate, defense quality, knuckleball, etc.)
- Estimates how much of ERA-FIP gap is attributable to the pitcher based on their history
- Database: ~152,000 pitcher baselines

**Pitching ERA Specifics:**
- Does NOT purely use FIP
- Adjusts for park, league, quality of competition
- Pitcher projections can change dramatically with team changes (defense adjustment)
- Known for sometimes producing ERA projections that look very different from past performance

**Sources:**
- [ZiPS | MLB Glossary](https://www.mlb.com/glossary/projection-systems/szymborski-projection-system)
- [The 2026 ZiPS Projections | FanGraphs](https://blogs.fangraphs.com/the-2026-zips-projections-are-almost-here/)

---

### PECOTA (Baseball Prospectus)

**Methodology:** Nearest-neighbor / comparable-player system

**How It Works:**
1. Calculate baseline from weighted recent performance (more recent years heavier)
2. Consider four categories of attributes:
   - **Production metrics:** K rate, GB rate, etc.
   - **Usage metrics:** Career length, IP, starter vs reliever
   - **Physical attributes:** Body type, position, age
   - **Demographic factors**
3. Match to historical comparables using 3-year performance windows
4. Project future based on comparables' actual trajectories

**Age Curve:** Custom per-player, derived from matched comparables' actual aging paths (not a generic curve)

**Key Advantage:** Creates probability distributions, not just point estimates. Provides percentile outcomes (10th, 50th, 90th percentile forecasts).

**Pitching Specifics:**
- K rate and BB rate are the most predictive inputs by a considerable margin
- Similarity scores compare age-specific 3-year windows
- Adjusts for park, league, and defensive context

**Sources:**
- [PECOTA | Wikipedia](https://en.wikipedia.org/wiki/PECOTA)
- [Reintroducing PECOTA | Baseball Prospectus](https://www.baseballprospectus.com/news/article/12133/reintroducing-pecota-the-seven-percent-solution/)

---

### THE BAT / THE BAT X (Derek Carty)

**Creator:** Derek Carty, developed over 10,000+ hours

**THE BAT:** Traditional stat-based projection system incorporating park factors, platoon splits, air density, umpire effects

**THE BAT X:** Adds Statcast data (150+ variables)
- For hitters: launch angle, exit velocity, barrels, spray angle, sprint speed
- For pitchers: Still in development as of latest information; pitch-level data (velocity, movement, spin) is more complex to integrate

**Performance:** FantasyPros' most accurate original season-long projections for 4 consecutive years. THE BAT X was the first original system to ever beat consensus systems (2024).

**Sources:**
- [THE BAT X | RotoGrinders](https://rotogrinders.com/marketplace/derek-carty-s-the-bat-projection-system-300)
- [Introducing THE BAT X | FanGraphs RotoGraphs](https://fantasy.fangraphs.com/introducing-the-bat-x/)

---

### ATC (Average Total Cost)

**Creator:** Ariel Cohen

**Methodology:** Weighted consensus system
- Combines ZiPS, Steamer, FanGraphs FANS, and other freely available projections
- Plus prior MLB statistics over past 3 seasons
- Each source system receives a different weight for each stat category
- Weights determined by historical accuracy analysis

**Performance:** #1 most accurate industry projections since 2019. #1 most accurate draft rankings in 2025.

**Why It Works:** Wisdom-of-crowds effect. Averaging diverse methodologies cancels out individual system biases.

**Sources:**
- [The ATC Projection System | FanGraphs RotoGraphs](https://fantasy.fangraphs.com/the-atc-projection-system/)
- [ATC Overview | RotoBaller](https://www.rotoballer.com/atc-fantasy-baseball-projections-the-industrys-1-accuracy-draft-projections/1829172)

---

### CAIRO

**Methodology:** Enhanced Marcel
- Uses 4 seasons of data (vs Marcel's 3)
- Adjusts for ballpark
- Utilizes minor league equivalencies (MLEs)
- Adjusts for defense
- Regression rates vary by age and position

**Sources:**
- [Projection Rundown | FanGraphs](https://library.fangraphs.com/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/)

---

### Composite / Consensus Approaches

**Key Finding:** Composite forecasts (averaging multiple systems) consistently outperform any individual system.

OOPSY (FanGraphs' new composite) averaged with THE BAT X, Steamer, and ZiPS was "the clear runaway winner" in 2025 projection accuracy.

**Implication for modeling:** Even if building a custom model, blending with existing projections is likely to improve accuracy.

---

## 7. Regression and Stabilization

### Stabilization Points for Pitching Statistics

These represent the point at which a statistic reaches a correlation of 0.7 with another equal-sized sample (i.e., the signal equals the noise):

| Statistic | Stabilization Point | Notes |
|-----------|-------------------|-------|
| K% | ~60-70 BF | Very fast; among the quickest to stabilize |
| BB% | ~170 BF | Moderately fast |
| K-BB% | ~100-150 BF | Combines two fast-stabilizing stats |
| GB% / FB% | ~150 BF | Moderately fast |
| HR/FB% | ~400+ FB | Very slow; ~2+ seasons of starter data |
| BABIP (pitcher) | ~2,000 BIP | Extremely slow; ~3 full seasons |
| LOB% | Very slow | R^2 = 0.048 year-to-year |
| ERA | ~500+ BF | Slow; influenced by all the slow-stabilizing components |
| FIP | ~300 BF | Faster than ERA |
| Stuff+ | ~80 pitches | Very fast (pitch-level metric) |

**Source methodology:** Russell Carleton's framework, updated by FanGraphs (Dolinar/Pemstein). Measure split-half reliability at each 10 PA increment until r = 0.7.

**Important:** Stabilization is a continuum, not a binary threshold. You always know more after 150 BF than after 50, but less than after 600.

**Sources:**
- [Sample Size | FanGraphs](https://library.fangraphs.com/principles/sample-size/)
- [A Long-Needed Update on Reliability | FanGraphs](https://blogs.fangraphs.com/a-long-needed-update-on-reliability/)

---

### Year-to-Year Correlations for Pitching Stats

| Statistic | Y-t-Y Correlation (r) | Classification |
|-----------|----------------------|----------------|
| Fastball Velocity (vFA) | Very high | Ability-driven |
| K% | 0.84 | Ability-driven |
| GB/FB ratio | Highest for starters | Ability-driven |
| K-BB% | High | Ability-driven |
| FIP | 0.65 | Mostly ability |
| SIERA | 0.72 | Mostly ability |
| xFIP | 0.68 | Mostly ability |
| ERA | 0.38 | Mixed luck/ability |
| BABIP | Low | Mostly luck/defense |
| LOB% | Very low (r^2 = 0.048) | Mostly luck |
| HR/FB | Low | Mostly luck/park |

**Sources:**
- [Tool: Basically Every Pitching Stat Correlation | FanGraphs](https://blogs.fangraphs.com/tool-basically-every-pitching-stat-correlation/)
- [What Metrics Correlate Year-to-Year? | Beyond the Box Score](https://www.beyondtheboxscore.com/2012/1/9/2690405/what-starting-pitcher-metrics-correlate-year-to-year)

---

### Pitcher Age Curves

| Component | Peak Age | Pattern |
|-----------|----------|---------|
| Fastball Velocity | Early 20s | Steady decline; ~1 MPH drop by 26; steep decline after |
| K Rate | 22-28 | Curved; compensatory mechanics delay decline |
| BB Rate | 25-27 (lowest) | Rises after 26 as velocity drops |
| HR Rate | 20-26 (lowest) | Climbs after 26 |
| BABIP | 20-22 (best) | Gradually worsens |
| Overall ERA | ~27-29 | Best years; decline accelerates after 30 |

**Key Insight:** Pitchers who survive into their 30s are less reliant on velocity for strikeouts, suggesting survivorship bias in aging curves.

**Sources:**
- [Pitcher Aging Curves | FanGraphs](https://blogs.fangraphs.com/pitcher-aging-curves-starters-and-relievers/)
- [Aging Curves Revisited | The Hardball Times](https://tht.fangraphs.com/aging-curves-revisited-damn-strikeouts/)

---

## 8. Role-Specific Considerations

### SP vs RP ERA/WHIP Prediction Differences

**Relievers typically have:**
- Lower ERA and WHIP than starters (selection bias + shorter outings)
- Higher K rates (can throw max effort for 1 inning)
- Higher LOB% (~mid-80s vs ~72% for starters)
- Greater ERA volatility (fewer innings = more noise)

**Projection Challenges for Relievers:**
- Small sample sizes make rate stats unreliable
- Role changes (closer to setup, setup to mop-up) dramatically affect value
- Managerial discretion determines saves opportunities
- WHIP stabilizes faster than ERA for relievers

---

### Times Through the Order (TTO) Penalty

**Magnitude:**
- 1st time through: ERA ~4.08
- 2nd time through: ERA ~4.20 (+3%)
- 3rd time through: ERA ~4.57 (+12% vs 1st time)

**Causes:**
1. Batter learning/familiarity
2. Pitcher fatigue (velocity dip, command decline)
3. Pitch count effects

**Key Research Finding (Bayesian analysis):** When both TTO and pitch count are in the same regression, pitch count tends to be significant and knocks TTO out of significance, suggesting fatigue (not familiarity) is the primary driver.

**Year-to-Year Predictability:** Individual pitcher TTO penalties have year-to-year correlations of ~0.03 (essentially unpredictable). The penalty is largely uniform across pitchers.

**Implication:** All starters should be projected with a TTO penalty baked in. Individual variation is noise.

**Sources:**
- [Third Time Through the Order Penalty | MLB Glossary](https://www.mlb.com/glossary/miscellaneous/third-time-through-the-order-penalty)
- [A Bayesian Analysis of TTO | Wharton](https://wsb.wharton.upenn.edu/wp-content/uploads/2023/08/Ryan-Brill_Research-Paper.pdf)

---

### Closer vs Setup Differences

- Closers face high-leverage situations; ERA is context-dependent
- Setup men who pitch multiple innings can significantly help fantasy ratios (ERA, WHIP)
- No inherent skill difference in ERA between roles; selection determines quality
- Modern bullpen usage increasingly based on leverage rather than traditional innings

### Opener / Bulk Reliever Considerations

- Tandem/piggyback starters can clear ~2.5 extra wins of value over 125 pitches vs traditional starters + middle relievers
- Pitchers who lack stamina past 50-75 pitches are tandem candidates
- In AL-only roto, tracking opener usage is important because it affects IP, K, ERA, WHIP volume

---

## 9. Machine Learning Approaches

### Traditional ML Models for ERA Prediction

**Models Tested:**
- Decision Tree
- Logistic Regression
- Random Forest
- XGBoost / LightGBM
- Artificial Neural Networks (ANN)

**Feature Importance (from Random Forest / XGBoost):**
Key features for predicting pitcher success include ERA, WHIP, FIP, K/9, BB/9, K/BB, HR/9, BAA (batting average against), OBP against, OPS against.

**Performance:**
- Logistic Regression and XGBoost achieved highest accuracy (0.89-0.93) for classification tasks
- Random Forest: ~59.6% accuracy for game outcome prediction

---

### Temporal Fusion Transformer (TFT) for ERA Prediction

**Paper:** Lee & Kim (2025), *Computers, Materials & Continua*

**Key Findings:**
- TFT consistently outperformed RNN-based approaches AND existing projection systems
- RMSE: **0.709** (Basic dataset) and 0.807 (Statcast dataset)
- Surprisingly, the Basic dataset outperformed the Statcast dataset across all evaluation metrics
- This suggests traditional stats may contain signal that Statcast metrics don't fully capture, or that Statcast adds noise

**Sources:**
- [TFT ERA Prediction | TechScience](https://www.techscience.com/cmc/v83n3/61073)
- [TFT ERA Prediction | ScienceDirect](https://www.sciencedirect.com/org/science/article/pii/S1546221825005028)

---

### Pitch-Level Deep Learning Models

**LSTM (Long Short-Term Memory) Models:**
- Individual pitcher-by-pitcher models
- Input: sequences of consecutive pitch observations
- Architecture: encoder-decoder with LSTM layers, L2 regularization, attention mechanism, softmax output
- Used for pitch type and outcome prediction

**Transformer Models:**
- Applied to predict pitch outcomes
- Can model complex sequential dependencies in pitch sequences
- Still emerging area of research

**Pitch Sequence Complexity:**
- Research explored relationship between pitch sequence patterns and ERA
- Single pitch motifs or motif-based diversity alone have limitations as independent ERA predictors
- Pitch sequence complexity relates to performance but is not a standalone predictor

**Sources:**
- [No Pitch Is an Island | FanGraphs Community Blog](https://community.fangraphs.com/no-pitch-is-an-island-pitch-prediction-with-sequence-to-sequence-deep-learning/)
- [Predicting Pitch Outcomes with Transformers | Medium](https://medium.com/@declankneita/predicting-baseball-pitch-outcomes-with-transformer-models-data-collection-29a4132ddc7d)

---

### Bayesian Approaches

**BayesBall Algorithm:**
- Inputs: historical season ERA values + peripheral metrics
- Uses empirical data for prior distributions
- Produces probability distributions for next year's ERA
- Reduces RMSE by ~0.1 (translates to 2-3 runs over full season for a starter)

**Hierarchical Bayesian Log5 Model:**
- Predicts probability of batter/pitcher matchup outcomes
- Uses standard log5 coefficients as prior information
- Particularly effective with small data samples

**Empirical Bayes for BABIP/Rate Stats:**
- Calculate priors from league-wide distributions
- Update with individual pitcher data
- Effective for regressing small-sample rate stats

**Sources:**
- [Empirical Bayes Baseball | Variance Explained](http://varianceexplained.org/r/empirical_bayes_baseball/)
- [BayesBall | Medium](https://medium.com/@takatanaka/bayesball-leveraging-historical-data-to-predict-performance-and-cost-25a6c1d267d1)

---

### Open-Source Tools and Packages

**Python:**
- `pybaseball`: Statcast data access
- `baseballr` (R port): Comprehensive baseball analytics
- MLBDailyProjections (GitHub): ML + regression + sabermetrics
- Predicting-Baseball-Statistics (GitHub): scikit-learn + TensorFlow-Keras

**R:**
- `baseballr` (Bill Petti): FanGraphs, Baseball Reference, Statcast data access
- `Lahman`: Historical baseball database
- Analyzing Baseball Data with R (3rd edition): Comprehensive textbook

**Sources:**
- [baseballr | GitHub](https://github.com/BillPetti/baseballr)
- [sabermetrics GitHub Topic](https://github.com/topics/sabermetrics)

---

## 10. Historical Accuracy and Comparisons

### Typical Projection Errors for ERA

- ERA is widely considered the **hardest fantasy category to project**
- RMSE for best ERA projection systems: **~0.7-1.0** (meaning typical errors of 0.7-1.0 ERA points)
- TFT deep learning model achieved RMSE of 0.709 (best reported)
- Composite/consensus projections consistently beat individual systems

### System-by-System Performance Rankings (Recent Years)

**2024:**
- #1: THE BAT X (first original system to beat consensus)
- #2: Zeile Consensus Projections (FantasyPros)
- #3: ATC

**2025:**
- Composite projection (OOPSY + THE BAT X + Steamer + ZiPS) was "clear runaway winner"
- ATC dominated pitching ratio categories (ERA, WHIP)

**General Pattern:**
- ATC has been #1 most accurate since 2019 (consensus advantage)
- Steamer has historically been the "pitching king"
- ZiPS shows impressive ERA projection accuracy
- THE BAT X has recently emerged as the top original system

### ERA Predictability: How Sticky Is ERA?

- Year-to-year ERA correlation: r = 0.38 (weak)
- FIP year-to-year: r = 0.65 (moderate)
- SIERA year-to-year: r = 0.72 (strongest ERA estimator)
- K% year-to-year: r = 0.84 (strong)
- The most reliable ERA predictors are the pitcher's own component skills (K, BB, GB), NOT their ERA itself

### Component vs Direct Projection

Component-based approaches (projecting K, BB, HR, BABIP, LOB% and computing ERA) generally outperform direct ERA projection because:
1. Components stabilize faster and are more predictive
2. Can apply appropriate regression to each component independently
3. Can adjust for context changes (new park, new defense, new league)

**Sources:**
- [Most Accurate Projections 2024 | FantasyPros](https://www.fantasypros.com/2025/02/most-accurate-fantasy-baseball-projections-2024-results/)
- [Most Accurate Projections 2025 | FantasyPros](https://www.fantasypros.com/2026/02/most-accurate-fantasy-baseball-projections-2025-results/)

---

## 11. Practical Implications for AL-Only Rotisserie

### Key Considerations

1. **Player Pool Scarcity:** Only AL pitchers available. Mediocre pitching carries more ratio damage risk in single-league formats.

2. **Budget Allocation:** More money flows to pitching in AL-only than mixed leagues. Eight starters commonly exceed $25 in auctions.

3. **Strategy Options:**
   - **Ace-heavy:** Dominate ERA, WHIP, K with 2-3 elite starters; accept losing saves
   - **Spread the dollars:** General rule: stop short of $30 on any player in single-league formats
   - **Setup man value:** Elite setup men who throw 2-3 innings help ratios and accumulate occasional wins/saves

4. **ERA/WHIP Risk Management:**
   - In roto, a single bad pitcher can tank your ratios for months
   - Project ERA/WHIP using component methods with appropriate regression
   - Pay attention to: defense changes, park changes, catcher framing changes
   - Monitor early-season Stuff+/Pitching+ (stabilizes in ~80 pitches) before full stats stabilize

5. **In-Season Monitoring:**
   - Use FIP and xERA for in-season evaluation (best backward-looking metrics)
   - Use SIERA and xFIP for projecting rest-of-season
   - K-BB% is your single best quick indicator of future ERA
   - Watch for LOB% and BABIP outliers for regression candidates

### Recommended Modeling Approach

For building an ERA/WHIP projection model:

1. **Project Component Rates:**
   - K% (weight 3 years, regress ~60-70 BF worth toward league avg)
   - BB% (weight 3 years, regress ~170 BF worth toward league avg)
   - GB/FB/LD% (weight 3 years, regress ~150 BF worth)
   - HR/FB% (weight 3 years, heavy regression toward ~10-11% league avg)

2. **Project BABIP:**
   - Calculate eBABIP from projected batted ball profile
   - Adjust for projected team defense (OAA, DRS)
   - Weight career BABIP lightly (~7% skill component)
   - Regress heavily toward league average

3. **Project LOB%:**
   - Default to ~72% for most starters
   - Adjust upward for high-K pitchers (~75-78%)
   - Adjust upward for relievers (~78-85%)

4. **Calculate ERA:**
   - Use component ERA formula (Gill/Reeve or FIP-style)
   - Apply park factors
   - Consider catcher framing effects

5. **Calculate WHIP:**
   - WHIP = (projected BB + projected H) / projected IP
   - Where projected H = projected BABIP * projected BIP + projected HR

6. **Blend with Existing Projections:**
   - Average your custom model with Steamer, ZiPS, and ATC
   - Consensus almost always wins

---

## Key Research Papers and Resources

### Academic Papers
- Lee, W. & Kim, J.H. (2025). "Pitcher Performance Prediction MLB by Temporal Fusion Transformer." *Computers, Materials & Continua*, 83(3).
- Brill, R. (2022). "A Bayesian Analysis of the Time Through the Order Penalty in Baseball." *Wharton*.
- McCracken, V. (2000). DIPS Theory (foundational BABIP research).
- Carleton, R. Various stabilization/reliability research.

### Key Online Resources
- [FanGraphs Sabermetrics Library](https://library.fangraphs.com/) - Comprehensive stat definitions and methodology
- [Pitcher List Going Deep series](https://pitcherlist.com/) - ERA estimator comparisons
- [Baseball Prospectus](https://www.baseballprospectus.com/) - DRA, PECOTA, StuffPro/PitchPro
- [Baseball Savant](https://baseballsavant.mlb.com/) - Statcast data and xERA
- [FanGraphs Lab](https://www.fangraphs.com/lab/) - PitchingBot visualizer and tools

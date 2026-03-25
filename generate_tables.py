"""Generate multi-year interactive HTML valuation table.

Combines historical validation data (2019, 2021-2024) with 2026 ATC projections
into a single self-contained HTML file with year tabs, inflation toggle, and
interactive sorting/filtering.

Usage:
    python3 generate_tables.py
"""

import json
import html as html_mod

import numpy as np
import pandas as pd

from sgp.config import SGPConfig
from sgp.data_prep import get_calibration_data
from sgp.dollar_values import compute_historical_spending_split, compute_split_pool_values
from sgp.replacement import compute_replacement_level
from sgp.sgp_calc import compute_sgp
from targeting.model import MSPConfig, run_msp


# ── Constants ────────────────────────────────────────────────────────────────

HIST_YEARS = [2019, 2021, 2022, 2023, 2024, 2025]
PROJ_YEAR = 2026

COMMON_COLS = [
    "player_name", "fantasy_team", "mlb_team", "position", "pos_type",
    "R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO",
    "sgp_R", "sgp_HR", "sgp_RBI", "sgp_SB", "sgp_AVG",
    "sgp_W", "sgp_SV", "sgp_SO", "sgp_ERA", "sgp_WHIP",
    "total_sgp", "par", "production_value", "auction_value",
    "salary", "contract_year", "surplus",
    "msp", "msp_per_dollar", "tps",
]

COLUMNS = [
    {"key": "player_name", "label": "Player", "type": "str"},
    {"key": "fantasy_team", "label": "Fantasy Team", "type": "str", "show": True},
    {"key": "mlb_team", "label": "MLB", "type": "str", "show": False},
    {"key": "position", "label": "Pos", "type": "str", "show": True},
    {"key": "R", "label": "R", "type": "num", "dec": 0, "show": False, "cat": "bat"},
    {"key": "HR", "label": "HR", "type": "num", "dec": 0, "show": False, "cat": "bat"},
    {"key": "RBI", "label": "RBI", "type": "num", "dec": 0, "show": False, "cat": "bat"},
    {"key": "SB", "label": "SB", "type": "num", "dec": 0, "show": False, "cat": "bat"},
    {"key": "AVG", "label": "AVG", "type": "num", "dec": 3, "show": False, "cat": "bat"},
    {"key": "W", "label": "W", "type": "num", "dec": 0, "show": False, "cat": "pit"},
    {"key": "SV", "label": "SV", "type": "num", "dec": 0, "show": False, "cat": "pit"},
    {"key": "ERA", "label": "ERA", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "WHIP", "label": "WHIP", "type": "num", "dec": 3, "show": False, "cat": "pit"},
    {"key": "SO", "label": "SO", "type": "num", "dec": 0, "show": False, "cat": "pit"},
    {"key": "sgp_R", "label": "sgp R", "type": "num", "dec": 2, "show": False, "cat": "bat"},
    {"key": "sgp_HR", "label": "sgp HR", "type": "num", "dec": 2, "show": False, "cat": "bat"},
    {"key": "sgp_RBI", "label": "sgp RBI", "type": "num", "dec": 2, "show": False, "cat": "bat"},
    {"key": "sgp_SB", "label": "sgp SB", "type": "num", "dec": 2, "show": False, "cat": "bat"},
    {"key": "sgp_AVG", "label": "sgp AVG", "type": "num", "dec": 2, "show": False, "cat": "bat"},
    {"key": "sgp_W", "label": "sgp W", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "sgp_SV", "label": "sgp SV", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "sgp_SO", "label": "sgp SO", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "sgp_ERA", "label": "sgp ERA", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "sgp_WHIP", "label": "sgp WHIP", "type": "num", "dec": 2, "show": False, "cat": "pit"},
    {"key": "total_sgp", "label": "Total SGP", "type": "num", "dec": 2, "show": False},
    {"key": "par", "label": "PAR", "type": "num", "dec": 2, "show": True, "highlight": True},
    {"key": "production_value", "label": "Prod $", "type": "num", "dec": 1, "show": True, "highlight": True},
    {"key": "auction_value", "label": "Auction $", "type": "num", "dec": 1, "show": True, "highlight": True, "defaultSort": True},
    {"key": "salary", "label": "Salary", "type": "num", "dec": 0, "show": False},
    {"key": "contract_year", "label": "Contract", "type": "str", "show": False},
    {"key": "surplus", "label": "Surplus", "type": "num", "dec": 1, "show": False, "colored": True},
    {"key": "msp", "label": "MSP", "type": "num", "dec": 1, "show": False, "cat": "msp"},
    {"key": "msp_per_dollar", "label": "MSP/$", "type": "num", "dec": 3, "show": False, "cat": "msp"},
    {"key": "tps", "label": "TPS", "type": "num", "dec": 0, "show": True, "highlight": True, "cat": "msp"},
]

COL_GROUPS = [
    {"name": "Info", "keys": ["fantasy_team", "mlb_team", "position"]},
    {"name": "Batting", "keys": ["R", "HR", "RBI", "SB", "AVG"]},
    {"name": "Pitching", "keys": ["W", "SV", "ERA", "WHIP", "SO"]},
    {"name": "SGP Batting", "keys": ["sgp_R", "sgp_HR", "sgp_RBI", "sgp_SB", "sgp_AVG"]},
    {"name": "SGP Pitching", "keys": ["sgp_W", "sgp_SV", "sgp_SO", "sgp_ERA", "sgp_WHIP"]},
    {"name": "Values", "keys": ["total_sgp", "par", "production_value", "auction_value",
                                 "salary", "contract_year", "surplus"]},
    {"name": "Targeting", "keys": ["tps", "msp", "msp_per_dollar"]},
]


# ── Data loading ─────────────────────────────────────────────────────────────

def load_historical(year: int) -> pd.DataFrame:
    """Load a historical player valuation CSV and normalize columns."""
    df = pd.read_csv(f"data/player_valuations_{year}.csv")
    df["pos_type"] = df["is_pitcher"].map({True: "pitcher", False: "hitter"})
    for col in COMMON_COLS:
        if col not in df.columns:
            df[col] = np.nan
    return df[COMMON_COLS].copy()


def load_2026() -> tuple[pd.DataFrame, float, float]:
    """Load 2026 ATC valuations, compute split-pool values and inflation.

    Returns (dataframe, inflation_prod, inflation_auction).
    """
    val = pd.read_csv("data/valuations_atc_2026.csv")
    val = val.rename(columns={"team": "mlb_team", "dollar_value": "production_value"})

    # Compute split-pool auction values
    print("Computing split-pool auction values for 2026...")
    config = SGPConfig.composite()
    standings = get_calibration_data(config)
    sgp_result = compute_sgp(standings, config, bootstrap=False)
    replacement = compute_replacement_level(sgp_result, config, standings_df=standings)

    hist_split = compute_historical_spending_split(config)
    hitter_pct = 0.63
    if hist_split is not None and not hist_split.empty:
        hitter_pct = hist_split["hitter_pct"].mean() / 100.0
    print(f"  Hitter/pitcher split: {hitter_pct:.1%} / {1 - hitter_pct:.1%}")

    player_sgp = val[["player_name", "pos_type", "total_sgp"]].copy()
    split_df = compute_split_pool_values(player_sgp, replacement, config, hitter_pct=hitter_pct)
    val["auction_value"] = split_df["auction_value"].values

    # Merge pre-auction roster data using fuzzy name matching
    print("Merging pre-auction roster data...")
    from targeting.name_match import build_name_index, match_name
    rosters = pd.read_csv("data/preauction_rosters_2026.csv")
    all_keeper_salary = rosters["salary"].sum()
    n_keepers = len(rosters)

    # Build name index from valuations, then match each roster name
    val_name_index = build_name_index(val["player_name"].unique().tolist())
    roster_matched = []
    for _, row in rosters.iterrows():
        matched = match_name(row["player_name"], val_name_index)
        if matched:
            roster_matched.append({
                "player_name": matched,
                "fantasy_team": row["team"],
                "salary": row["salary"],
                "contract_year": row["contract_year"],
            })
    roster_info = pd.DataFrame(roster_matched)
    val = val.merge(roster_info, on="player_name", how="left")

    val["fantasy_team"] = val["fantasy_team"].fillna("")
    keeper_mask = val["fantasy_team"] != ""
    n_matched = keeper_mask.sum()
    print(f"  Matched {n_matched}/{n_keepers} roster players to projections")

    val.loc[~keeper_mask, "salary"] = np.nan
    val["contract_year"] = val["contract_year"].fillna("")

    # Surplus for keepers only
    val["surplus"] = np.where(
        keeper_mask & val["salary"].notna(),
        val["auction_value"] - val["salary"],
        np.nan,
    )

    # Compute inflation
    pool = config.total_auction_pool
    keeper_prod = val.loc[keeper_mask & (val["production_value"] > 0), "production_value"].sum()
    keeper_auction = val.loc[keeper_mask & (val["auction_value"] > 0), "auction_value"].sum()

    infl_prod = (pool - all_keeper_salary) / max(pool - keeper_prod, 1)
    infl_auction = (pool - all_keeper_salary) / max(pool - keeper_auction, 1)

    print(f"  Keeper salary committed: ${all_keeper_salary:.0f}")
    print(f"  Available auction budget: ${pool - all_keeper_salary:.0f}")
    print(f"  Inflation (production): {infl_prod:.3f}")
    print(f"  Inflation (auction): {infl_auction:.3f}")

    val["inflated_production"] = val["production_value"].copy()
    val["inflated_auction"] = val["auction_value"].copy()
    non_keeper = ~keeper_mask
    val.loc[non_keeper, "inflated_production"] *= infl_prod
    val.loc[non_keeper, "inflated_auction"] *= infl_auction

    # Run MSP targeting for Gusteroids using winning config (keeper_only)
    print("Computing MSP targeting (Gusteroids, proportional_fill)...")
    atc_val = pd.read_csv("data/valuations_atc_2026.csv")
    if "is_pitcher" not in atc_val.columns and "pos_type" in atc_val.columns:
        atc_val["is_pitcher"] = atc_val["pos_type"] == "pitcher"
    msp_config = MSPConfig(
        baseline_type="proportional_fill", fill_discount=0.5, budget_displacement=True,
    )
    msp_results, _ = run_msp(rosters, atc_val, "Gusteroids", msp_config)
    # Compute TPS
    from targeting.model import compute_tps
    msp_results = compute_tps(msp_results)
    # Join MSP + TPS columns to val by player_name
    msp_cols = msp_results[["player_name", "msp", "msp_per_dollar", "tps"]].copy()
    val = val.merge(msp_cols, on="player_name", how="left")
    print(f"  MSP computed for {msp_cols['msp'].notna().sum()} players")

    extra_cols = COMMON_COLS + ["inflated_production", "inflated_auction"]
    for col in extra_cols:
        if col not in val.columns:
            val[col] = np.nan
    return val[extra_cols].copy(), infl_prod, infl_auction


# ── HTML generation ──────────────────────────────────────────────────────────

def build_html(year_data_json, year_positions_json, columns_json, col_groups_json,
               inflation_json, years_json):
    """Build self-contained multi-year HTML valuation table."""

    title = "Player Valuations"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --primary: #3A6EA5;
  --secondary: #C1666B;
  --accent: #2A9D8F;
  --bg: #faf9f5;
  --bg-sidebar: #f4f3ef;
  --grid: #ededeb;
  --border: #e0dfdb;
  --text: #2d2d2d;
  --mid: #666666;
  --light: #999999;
  --green: #2A9D8F;
  --red: #C1666B;
  --name-col-width: 180px;
  --sidebar-width: 220px;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'DM Sans', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}}

/* ── Layout ── */
.page {{ display: flex; min-height: 100vh; }}

/* ── Sidebar ── */
.sidebar {{
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--grid);
  padding: 32px 16px 24px;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  overflow-y: auto;
  z-index: 10;
  transition: transform 0.25s ease;
}}
.sidebar.collapsed {{ transform: translateX(calc(-1 * var(--sidebar-width))); }}

.sidebar-toggle {{
  position: fixed;
  top: 36px;
  left: calc(var(--sidebar-width) + 6px);
  z-index: 20;
  width: 24px; height: 24px;
  background: var(--bg);
  border: 1px solid var(--grid);
  border-radius: 4px;
  color: var(--light);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
  transition: left 0.25s ease, color 0.15s;
}}
.sidebar-toggle:hover {{ color: var(--text); }}
.sidebar.collapsed + .sidebar-toggle {{ left: 10px; }}

.sidebar-heading {{
  font-family: 'DM Sans', sans-serif;
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1.8px;
  color: var(--light);
  margin-bottom: 14px;
}}

.sidebar-actions {{
  display: flex; gap: 6px; margin-bottom: 12px;
}}
.sidebar-actions button {{
  flex: 1; padding: 5px 0;
  font-size: 10px; font-family: 'DM Sans', sans-serif;
  font-weight: 500; letter-spacing: 0.4px; text-transform: uppercase;
  color: var(--light); background: var(--bg);
  border: 1px solid var(--grid); border-radius: 4px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}}
.sidebar-actions button:hover {{ color: var(--text); border-color: var(--primary); }}

.col-list {{ list-style: none; }}
.col-list li {{ margin-bottom: 1px; }}

.col-list label {{
  display: flex; align-items: center; gap: 8px;
  padding: 4px 6px; border-radius: 4px; cursor: pointer;
  font-size: 12.5px; color: var(--mid);
  transition: background 0.12s, color 0.12s;
  user-select: none;
}}
.col-list label:hover {{ background: var(--bg); color: var(--text); }}

.col-list input[type="checkbox"] {{
  appearance: none;
  width: 14px; height: 14px;
  border: 1.5px solid var(--border); border-radius: 3px;
  background: var(--bg); cursor: pointer;
  position: relative; flex-shrink: 0;
  transition: border-color 0.12s, background 0.12s;
}}
.col-list input[type="checkbox"]:checked {{
  background: var(--primary); border-color: var(--primary);
}}
.col-list input[type="checkbox"]:checked::after {{
  content: ""; position: absolute;
  top: 1px; left: 4px; width: 4px; height: 7px;
  border: solid white; border-width: 0 1.5px 1.5px 0;
  transform: rotate(45deg);
}}

.sidebar-group-header {{
  margin-top: 12px; margin-bottom: 2px;
}}
.sidebar-group-header button {{
  display: block; width: 100%;
  background: none; border: none; cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1.2px;
  color: var(--light); text-align: left;
  padding: 4px 6px; border-radius: 4px;
  transition: color 0.12s, background 0.12s;
}}
.sidebar-group-header button:hover {{ color: var(--primary); background: var(--bg); }}

/* ── Main ── */
.main {{
  margin-left: var(--sidebar-width);
  flex: 1; padding: 40px 48px 48px;
  max-width: 100%; overflow: hidden;
  transition: margin-left 0.25s ease;
}}
.sidebar.collapsed ~ .main {{ margin-left: 0; }}

.header {{ margin-bottom: 28px; }}
.header h1 {{
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 28px; font-weight: 700;
  color: var(--text); letter-spacing: -0.3px; line-height: 1.2;
}}
.header .subtitle {{
  font-size: 13px; color: var(--light);
  margin-top: 4px; font-weight: 400;
}}

/* ── Controls ── */
.controls-row {{
  display: flex; gap: 10px; align-items: center;
  flex-wrap: wrap; margin-bottom: 12px;
}}

.search-box {{ position: relative; flex: 0 1 240px; }}
.search-box input {{
  width: 100%; padding: 7px 10px 7px 32px;
  background: white; border: 1px solid var(--grid); border-radius: 5px;
  color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 13px;
  outline: none; transition: border-color 0.15s;
}}
.search-box input:focus {{ border-color: var(--primary); }}
.search-box::before {{
  content: "\\2315"; position: absolute;
  left: 10px; top: 50%; transform: translateY(-50%);
  font-size: 15px; color: var(--light); pointer-events: none;
}}

.pill-group {{
  display: flex; gap: 0;
  border: 1px solid var(--grid); border-radius: 5px; overflow: hidden;
}}
.pill {{
  padding: 7px 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11.5px; font-weight: 500;
  color: var(--light); background: white;
  border: none; cursor: pointer;
  transition: all 0.12s;
  border-right: 1px solid var(--grid);
}}
.pill:last-child {{ border-right: none; }}
.pill:hover {{ color: var(--text); background: var(--bg-sidebar); }}
.pill.active {{ color: white; background: var(--primary); }}

.pill-group.year-pills .pill {{
  font-size: 13px; padding: 8px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}}

.pill-group.inflation-pills .pill.active {{
  background: var(--accent);
}}

.count-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px; color: var(--light);
  margin-left: auto;
}}

/* ── Table ── */
.table-outer {{
  border: 1px solid var(--grid); border-radius: 6px;
  overflow: hidden; background: white;
}}
.table-scroll {{
  overflow-x: auto; overflow-y: auto;
  max-height: calc(100vh - 280px);
}}

table {{
  border-collapse: separate; border-spacing: 0;
  font-size: 13px; min-width: 100%;
}}
thead {{ position: sticky; top: 0; z-index: 4; }}

th.name-header {{
  position: sticky; left: 0; z-index: 6;
  min-width: var(--name-col-width); max-width: var(--name-col-width);
}}
th {{
  background: var(--text); padding: 9px 12px; text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px; font-weight: 500;
  letter-spacing: 0.5px; text-transform: uppercase;
  color: white; border-bottom: none;
  cursor: pointer; user-select: none; white-space: nowrap;
  transition: background 0.12s;
}}
th:hover {{ background: #444444; }}
th.sorted {{ background: var(--primary); }}
th .sort-arrow {{
  display: inline-block; margin-left: 3px;
  font-size: 9px; opacity: 0; transition: opacity 0.12s;
}}
th:hover .sort-arrow, th.sorted .sort-arrow {{ opacity: 1; }}
th.num-col {{ text-align: right; }}

td {{
  padding: 7px 12px; border-bottom: 1px solid var(--grid);
  white-space: nowrap; color: var(--mid); font-size: 13px;
}}
td.num {{
  text-align: right; font-family: 'JetBrains Mono', monospace;
  font-size: 12px; color: var(--mid);
}}
td.player-name {{
  font-weight: 600; color: var(--text);
  position: sticky; left: 0; z-index: 2;
  min-width: var(--name-col-width); max-width: var(--name-col-width);
  background: white; border-right: 1px solid var(--grid); font-size: 13px;
}}

tr:nth-child(even) td {{ background: var(--bg); }}
tr:nth-child(even) td.player-name {{ background: var(--bg); }}
tr:hover td {{ background: #eef4fa !important; }}
tr:hover td.player-name {{ background: #eef4fa !important; }}

td.val-positive {{ color: var(--green); font-weight: 500; }}
td.val-negative {{ color: var(--red); font-weight: 500; }}
td.val-highlight {{ color: var(--primary); font-weight: 600; }}
td.type-hitter {{ color: var(--primary); }}
td.type-pitcher {{ color: var(--secondary); }}

/* ── Glossary ── */
.glossary {{
  margin-bottom: 16px;
}}
.glossary-toggle {{
  background: none; border: none; cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px; font-weight: 500;
  color: var(--light); padding: 4px 0;
  transition: color 0.15s;
}}
.glossary-toggle:hover {{ color: var(--primary); }}
.glossary-arrow {{
  display: inline-block; font-size: 9px;
  margin-right: 4px; transition: transform 0.15s;
}}
.glossary-body {{
  margin-top: 10px; padding: 20px 24px;
  background: white;
  border: 1px solid var(--grid); border-radius: 6px;
}}
.glossary-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}}
.glossary-section h3 {{
  font-family: 'DM Sans', sans-serif;
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1.2px;
  color: var(--primary); margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--grid);
}}
.glossary-section dl {{
  display: grid; gap: 6px;
}}
.glossary-section dt {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px; font-weight: 500;
  color: var(--text);
}}
.glossary-section dd {{
  font-size: 12px; color: var(--mid);
  line-height: 1.5; margin-bottom: 6px;
}}

.empty-state {{
  text-align: center; padding: 40px 24px;
  color: var(--light); font-size: 13px;
}}
</style>
</head>
<body>

<div class="page">
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-heading">Columns</div>
    <div class="sidebar-actions">
      <button id="btnShowAll">Show All</button>
      <button id="btnHideAll">Hide All</button>
    </div>
    <ul class="col-list" id="colList"></ul>
  </nav>

  <button class="sidebar-toggle" id="sidebarToggle" title="Toggle sidebar">&#9776;</button>

  <div class="main">
    <div class="header">
      <h1>{html_mod.escape(title)}</h1>
      <div class="subtitle" id="subtitle"></div>
    </div>

    <div class="glossary">
      <button class="glossary-toggle" id="glossaryToggle">
        <span class="glossary-arrow">&#9654;</span> Glossary
      </button>
      <div class="glossary-body" id="glossaryBody" style="display:none">
        <div class="glossary-grid">
          <div class="glossary-section">
            <h3>Value Columns</h3>
            <dl>
              <dt>Total SGP</dt>
              <dd>Standings Gain Points. The total number of standings points a player's stats are worth, computed by dividing each stat by its SGP denominator (how much of that stat it takes to gain one point in the standings).</dd>
              <dt>PAR</dt>
              <dd>Points Above Replacement. Total SGP minus a replacement-level baseline. This is the marginal value a player adds over a freely available alternative. Only players with positive PAR earn auction dollars.</dd>
              <dt>Prod $</dt>
              <dd>Production value (single-pool). Converts PAR to dollars using one shared pool across all players. Reflects each player's true share of the total value pie, regardless of position type.</dd>
              <dt>Auction $</dt>
              <dd>Auction value (split-pool). Converts PAR to dollars using separate hitter and pitcher pools (62/38 split based on historical league spending). Better reflects what you'd actually pay at auction because it accounts for the market's hitter-heavy spending pattern.</dd>
              <dt>Surplus</dt>
              <dd>Auction value minus salary. Positive surplus means the player is a bargain relative to what they'd cost at auction. Only shown for players with a salary.</dd>
            </dl>
          </div>
          <div class="glossary-section">
            <h3>SGP Per-Category</h3>
            <dl>
              <dt>sgp R, HR, RBI, SB</dt>
              <dd>Batting counting stats divided by their SGP denominator. Each point represents one standings point gained in that category.</dd>
              <dt>sgp AVG</dt>
              <dd>Volume-weighted batting average contribution above replacement. Uses plate appearances to weight how much a player's AVG moves the team average.</dd>
              <dt>sgp W, SV, SO</dt>
              <dd>Pitching counting stats divided by their SGP denominator.</dd>
              <dt>sgp ERA, WHIP</dt>
              <dd>Volume-weighted pitching rate contributions above replacement. Uses innings pitched to weight impact on team ERA/WHIP.</dd>
            </dl>
          </div>
          <div class="glossary-section">
            <h3>2026 Controls</h3>
            <dl>
              <dt>Raw $ / Inflated $</dt>
              <dd>Toggle between base dollar values and inflation-adjusted values. In a keeper league, keepers are paid below market rate, leaving more money chasing fewer free agents. Inflation shows what free agents would actually cost at auction. Keepers are unaffected.</dd>
              <dt>Rostered / Free Agent</dt>
              <dd>Filter to players currently on a team (keepers) or available for auction.</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <div class="controls-row">
      <div class="pill-group year-pills" id="yearFilter"></div>
    </div>
    <div class="controls-row">
      <div class="search-box">
        <input type="text" id="search" placeholder="Search players, teams\\u2026">
      </div>
      <div class="pill-group" id="typeFilter"></div>
      <div class="pill-group" id="posFilter"></div>
      <div class="pill-group inflation-pills" id="inflationToggle" style="display:none"></div>
      <div class="pill-group" id="rosterFilter" style="display:none"></div>
      <span class="count-badge" id="count"></span>
    </div>

    <div class="table-outer">
      <div class="table-scroll">
        <table>
          <thead><tr id="headerRow"></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<script>
const YEAR_DATA = {year_data_json};
const YEAR_POSITIONS = {year_positions_json};
const COLUMNS = {columns_json};
const COL_GROUPS = {col_groups_json};
const INFLATION = {inflation_json};
const YEARS = {years_json};

const BATTING_KEYS = new Set(["R","HR","RBI","SB","AVG","sgp_R","sgp_HR","sgp_RBI","sgp_SB","sgp_AVG"]);
const PITCHING_KEYS = new Set(["W","SV","ERA","WHIP","SO","sgp_W","sgp_SV","sgp_SO","sgp_ERA","sgp_WHIP"]);

let currentYear = "2026";
let sortCol = COLUMNS.find(c => c.defaultSort)?.key || "auction_value";
let sortAsc = false;
let filterType = "";
let filterPos = "";
let filterRoster = "";
let inflationOn = false;
let visibleCols = new Set(COLUMNS.filter(c => c.show !== false).map(c => c.key));
visibleCols.add("player_name");

/* ── Utilities ── */

function clearEl(el) {{ while (el.firstChild) el.removeChild(el.firstChild); }}

function setActivePill(group, activeBtn) {{
  group.querySelectorAll(".pill").forEach(b => b.classList.remove("active"));
  activeBtn.classList.add("active");
}}

function getResolvedKey(key) {{
  if (inflationOn && currentYear === "2026") {{
    if (key === "production_value") return "inflated_production";
    if (key === "auction_value") return "inflated_auction";
  }}
  return key;
}}

function getData() {{ return YEAR_DATA[currentYear]; }}

/* ── Init ── */

function init() {{
  /* Parse numeric values across all years */
  YEARS.forEach(y => {{
    YEAR_DATA[y].forEach(r => {{
      COLUMNS.forEach(c => {{
        if (c.type === "num" && r[c.key] != null) {{
          const v = parseFloat(r[c.key]);
          r[c.key] = isNaN(v) ? null : v;
        }}
      }});
      /* 2026 inflated values */
      if (y === "2026") {{
        ["inflated_production", "inflated_auction"].forEach(k => {{
          if (r[k] != null) {{
            const v = parseFloat(r[k]);
            r[k] = isNaN(v) ? null : v;
          }}
        }});
      }}
    }});
  }});

  buildSidebar();
  buildYearPills();
  buildTypeFilter();
  buildPosFilter();
  buildRosterFilter();
  buildInflationToggle();
  buildHeader();

  /* Show 2026-specific controls on initial load */
  const is2026 = (currentYear === "2026");
  document.getElementById("inflationToggle").style.display = is2026 ? "flex" : "none";
  document.getElementById("rosterFilter").style.display = is2026 ? "flex" : "none";

  render();

  document.getElementById("search").addEventListener("input", render);
  document.getElementById("sidebarToggle").addEventListener("click", () => {{
    document.getElementById("sidebar").classList.toggle("collapsed");
  }});
  document.getElementById("btnShowAll").addEventListener("click", () => toggleAllCols(true));
  document.getElementById("btnHideAll").addEventListener("click", () => toggleAllCols(false));

  /* Glossary toggle */
  document.getElementById("glossaryToggle").addEventListener("click", () => {{
    const body = document.getElementById("glossaryBody");
    const btn = document.getElementById("glossaryToggle");
    const open = body.style.display !== "none";
    body.style.display = open ? "none" : "block";
    btn.querySelector(".glossary-arrow").textContent = open ? "\\u25B6" : "\\u25BC";
  }});
}}

/* ── Sidebar ── */

function buildSidebar() {{
  const list = document.getElementById("colList");
  clearEl(list);

  COL_GROUPS.forEach(group => {{
    /* Group header */
    const hdr = document.createElement("li");
    hdr.className = "sidebar-group-header";
    const hdrBtn = document.createElement("button");
    hdrBtn.textContent = group.name;
    hdrBtn.addEventListener("click", () => {{
      const gCols = COLUMNS.filter(c => group.keys.includes(c.key));
      const allVis = gCols.every(c => visibleCols.has(c.key));
      gCols.forEach(c => {{
        if (allVis) visibleCols.delete(c.key);
        else visibleCols.add(c.key);
      }});
      buildSidebar();
      buildHeader();
      render();
    }});
    hdr.appendChild(hdrBtn);
    list.appendChild(hdr);

    /* Columns in group */
    COLUMNS.filter(c => group.keys.includes(c.key)).forEach(c => {{
      const li = document.createElement("li");
      const label = document.createElement("label");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = visibleCols.has(c.key);
      cb.addEventListener("change", () => {{
        if (cb.checked) visibleCols.add(c.key);
        else visibleCols.delete(c.key);
        buildHeader();
        render();
      }});
      label.appendChild(cb);
      const span = document.createElement("span");
      span.textContent = c.label;
      label.appendChild(span);
      li.appendChild(label);
      list.appendChild(li);
    }});
  }});
}}

function toggleAllCols(show) {{
  if (show) visibleCols = new Set(COLUMNS.map(c => c.key));
  else visibleCols = new Set(["player_name"]);
  buildSidebar();
  buildHeader();
  render();
}}

/* ── Year Pills ── */

function buildYearPills() {{
  const group = document.getElementById("yearFilter");
  clearEl(group);
  YEARS.forEach(y => {{
    const btn = document.createElement("button");
    btn.className = "pill" + (y === currentYear ? " active" : "");
    btn.textContent = y;
    btn.dataset.year = y;
    btn.addEventListener("click", () => switchYear(y));
    group.appendChild(btn);
  }});
}}

function switchYear(year) {{
  currentYear = year;
  filterPos = "";
  filterRoster = "";

  /* Update year pill active state */
  document.querySelectorAll("#yearFilter .pill").forEach(btn => {{
    btn.classList.toggle("active", btn.dataset.year === year);
  }});

  /* Show/hide 2026-specific controls */
  const is2026 = (year === "2026");
  document.getElementById("inflationToggle").style.display = is2026 ? "flex" : "none";
  document.getElementById("rosterFilter").style.display = is2026 ? "flex" : "none";

  /* Reset inflation when leaving 2026 */
  if (!is2026) {{
    inflationOn = false;
    const itg = document.getElementById("inflationToggle");
    itg.querySelectorAll(".pill").forEach((btn, i) => {{
      btn.classList.toggle("active", i === 0);
    }});
  }}

  /* Reset roster filter pills */
  const rfg = document.getElementById("rosterFilter");
  rfg.querySelectorAll(".pill").forEach((btn, i) => {{
    btn.classList.toggle("active", i === 0);
  }});

  buildPosFilter();
  buildHeader();
  render();
}}

/* ── Type Filter ── */

function buildTypeFilter() {{
  const group = document.getElementById("typeFilter");
  clearEl(group);
  const pairs = [["All", ""], ["Hitters", "hitter"], ["Pitchers", "pitcher"]];
  pairs.forEach(([label, val]) => {{
    const btn = document.createElement("button");
    btn.className = "pill" + (val === "" ? " active" : "");
    btn.textContent = label;
    btn.addEventListener("click", () => {{
      filterType = val;
      setActivePill(group, btn);
      render();
    }});
    group.appendChild(btn);
  }});
}}

/* ── Position Filter ── */

function buildPosFilter() {{
  const group = document.getElementById("posFilter");
  clearEl(group);

  const allBtn = document.createElement("button");
  allBtn.className = "pill active";
  allBtn.textContent = "All Pos";
  allBtn.addEventListener("click", () => {{ filterPos = ""; setActivePill(group, allBtn); render(); }});
  group.appendChild(allBtn);

  const positions = YEAR_POSITIONS[currentYear] || [];
  positions.forEach(p => {{
    const btn = document.createElement("button");
    btn.className = "pill";
    btn.textContent = p;
    btn.addEventListener("click", () => {{ filterPos = p; setActivePill(group, btn); render(); }});
    group.appendChild(btn);
  }});
}}

/* ── Roster Filter (2026 only) ── */

function buildRosterFilter() {{
  const group = document.getElementById("rosterFilter");
  clearEl(group);
  const pairs = [["All", ""], ["Rostered", "rostered"], ["Free Agent", "free"]];
  pairs.forEach(([label, val]) => {{
    const btn = document.createElement("button");
    btn.className = "pill" + (val === "" ? " active" : "");
    btn.textContent = label;
    btn.addEventListener("click", () => {{
      filterRoster = val;
      setActivePill(group, btn);
      render();
    }});
    group.appendChild(btn);
  }});
}}

/* ── Inflation Toggle (2026 only) ── */

function buildInflationToggle() {{
  const group = document.getElementById("inflationToggle");
  clearEl(group);
  ["Raw $", "Inflated $"].forEach((label, i) => {{
    const btn = document.createElement("button");
    btn.className = "pill" + (i === 0 ? " active" : "");
    btn.textContent = label;
    btn.addEventListener("click", () => {{
      inflationOn = (i === 1);
      setActivePill(group, btn);
      buildHeader();
      render();
    }});
    group.appendChild(btn);
  }});
}}

/* ── Table Header ── */

function buildHeader() {{
  const tr = document.getElementById("headerRow");
  clearEl(tr);
  COLUMNS.filter(c => visibleCols.has(c.key)).forEach(c => {{
    const th = document.createElement("th");
    if (c.type === "num") th.className = "num-col";
    if (c.key === "player_name") th.classList.add("name-header");
    if (c.key === sortCol) th.classList.add("sorted");

    /* Label — show inflated indicator */
    let label = c.label;
    if (inflationOn && currentYear === "2026") {{
      if (c.key === "production_value") label = "Prod $ *";
      if (c.key === "auction_value") label = "Auction $ *";
    }}
    const text = document.createTextNode(label + " ");
    th.appendChild(text);

    const arrow = document.createElement("span");
    arrow.className = "sort-arrow";
    arrow.textContent = (c.key === sortCol) ? (sortAsc ? "\\u25B2" : "\\u25BC") : "\\u25BC";
    th.appendChild(arrow);

    th.addEventListener("click", () => {{
      if (sortCol === c.key) sortAsc = !sortAsc;
      else {{ sortCol = c.key; sortAsc = c.type === "str"; }}
      buildHeader();
      render();
    }});
    tr.appendChild(th);
  }});
}}

/* ── Render ── */

function render() {{
  const data = getData();
  const q = document.getElementById("search").value.toLowerCase();

  let filtered = data.filter(r => {{
    if (filterType && r.pos_type !== filterType) return false;
    if (filterPos && !(r.position || "").split("/").includes(filterPos)) return false;
    if (filterRoster === "rostered" && !r.fantasy_team) return false;
    if (filterRoster === "free" && r.fantasy_team) return false;
    if (q) {{
      const s = [r.player_name, r.fantasy_team, r.mlb_team, r.position]
        .filter(Boolean).join(" ").toLowerCase();
      if (!s.includes(q)) return false;
    }}
    return true;
  }});

  /* Sort */
  const resolvedSort = getResolvedKey(sortCol);
  const col = COLUMNS.find(c => c.key === sortCol);
  filtered.sort((a, b) => {{
    let va = a[resolvedSort], vb = b[resolvedSort];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (col && col.type === "str") {{
      va = (va || "").toLowerCase();
      vb = (vb || "").toLowerCase();
    }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  /* Build rows */
  const tbody = document.getElementById("tbody");
  clearEl(tbody);

  if (filtered.length === 0) {{
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = visibleCols.size;
    td.className = "empty-state";
    td.textContent = "No players match your filters";
    tr.appendChild(td);
    tbody.appendChild(tr);
  }} else {{
    const visCols = COLUMNS.filter(c => visibleCols.has(c.key));
    filtered.forEach(r => {{
      const tr = document.createElement("tr");
      visCols.forEach(c => {{
        const td = document.createElement("td");
        const resolvedKey = getResolvedKey(c.key);
        const val = r[resolvedKey];

        if (c.key === "player_name") {{
          td.className = "player-name";
          td.textContent = val || "";
        }} else if (c.type === "num") {{
          td.className = "num";
          /* Blank out inapplicable stats */
          const isBat = BATTING_KEYS.has(c.key);
          const isPit = PITCHING_KEYS.has(c.key);
          if ((isBat && r.pos_type === "pitcher") || (isPit && r.pos_type === "hitter")) {{
            /* leave blank */
          }} else if (val != null) {{
            /* Hide zero salary for non-keepers */
            if (c.key === "salary" && val === 0) {{
              /* leave blank */
            }} else {{
              td.textContent = val.toFixed(c.dec != null ? c.dec : 1);
              if (c.colored) td.classList.add(val >= 0 ? "val-positive" : "val-negative");
              if (c.highlight) td.classList.add("val-highlight");
            }}
          }}
        }} else {{
          td.textContent = val || "";
          if (c.key === "pos_type") {{
            td.classList.add(val === "hitter" ? "type-hitter" : "type-pitcher");
          }}
        }}
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});
  }}

  /* Count badge */
  document.getElementById("count").textContent = filtered.length + " / " + data.length;

  /* Subtitle */
  updateSubtitle();
}}

function updateSubtitle() {{
  const el = document.getElementById("subtitle");
  let text;
  if (currentYear === "2026") {{
    text = "Moonlight Graham League \\u00b7 ATC projections \\u00b7 SGP valuation model";
    if (inflationOn) {{
      text += " \\u00b7 Inflation: \\u00d7" + INFLATION.auction.toFixed(2);
    }}
  }} else {{
    text = "Moonlight Graham League \\u00b7 " + currentYear + " actual stats \\u00b7 SGP valuation model";
  }}
  el.textContent = text;
}}

init();
</script>
</body>
</html>'''


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    year_dfs = {}
    year_positions = {}

    # Load historical years
    for year in HIST_YEARS:
        print(f"Loading {year}...")
        df = load_historical(year)
        year_dfs[str(year)] = df
        positions = sorted(df["position"].dropna().unique().tolist())
        year_positions[str(year)] = positions
        print(f"  {len(df)} players, positions: {positions}")

    # Load 2026 with split-pool and inflation
    print(f"\nLoading {PROJ_YEAR}...")
    df_2026, infl_prod, infl_auction = load_2026()
    year_dfs[str(PROJ_YEAR)] = df_2026
    # Decompose multi-position strings (e.g. "1B/OF" → {"1B", "OF"})
    base_pos = set()
    for p in df_2026["position"].dropna().unique():
        for part in p.split("/"):
            base_pos.add(part)
    positions = sorted(base_pos - {"DH"})
    year_positions[str(PROJ_YEAR)] = positions
    print(f"  {len(df_2026)} players, positions: {positions}")

    # Convert to JSON
    year_data_json_parts = {}
    for year_str, df in year_dfs.items():
        year_data_json_parts[year_str] = df.to_json(orient="records")

    year_data_json = "{" + ",".join(
        f'"{y}":{data}' for y, data in year_data_json_parts.items()
    ) + "}"

    year_positions_json = json.dumps(year_positions, separators=(",", ":"))
    columns_json = json.dumps(COLUMNS, separators=(",", ":"))
    col_groups_json = json.dumps(COL_GROUPS, separators=(",", ":"))
    inflation_json = json.dumps(
        {"production": round(infl_prod, 4), "auction": round(infl_auction, 4)},
        separators=(",", ":"),
    )
    years_json = json.dumps([str(y) for y in HIST_YEARS + [PROJ_YEAR]], separators=(",", ":"))

    # Generate HTML
    print("\nGenerating HTML...")
    html = build_html(
        year_data_json, year_positions_json, columns_json, col_groups_json,
        inflation_json, years_json,
    )

    output_path = "reports/valuations.html"
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Wrote {output_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()

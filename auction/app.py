"""
Moonlight Graham — 2026 Live Auction Tool

Layout (Option B: Command Bar):

  ┌────────────────────────────────────────────────────────────────────┐
  │  LOG RESULT: [Player ▼] [$] [Team ▼]  [LOG ✓]                     │  ← top
  │  Recent: #3 Altuve → R&R $42  ·  #2 Judge → Shrooms $55           │
  ├─────────────────────────┬──────────────────────────────────────────┤
  │  Budget  /  Spots       │  AVAILABLE FREE AGENTS                   │
  │  MY LINEUP CARD         │  Filters + sorted targeting table        │
  │  Category Ranks         │                                          │
  │  Full Log (▼)           │                                          │
  └─────────────────────────┴──────────────────────────────────────────┘

Run:
    streamlit run auction/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MGL 2026 Auction",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Constants ────────────────────────────────────────────────────────────────

MY_TEAM    = "Gusteroids"
TOTAL_BUDGET = 360
HITTER_SLOTS = 15
PITCHER_SLOTS = 11
DOLLARS_PER_STANDINGS_PT = 6.55
MSP_BID_RATE = 2.00             # $/SP for bid calculations (~30% of team-level $6.55)

TIERS = [
    ("Elite",   25.0),
    ("Premium", 15.0),
    ("Solid",    8.0),
    ("Filler",   4.0),
    ("Min",      1.0),
    ("Sub",      0.0),
]

CATEGORIES   = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]
INVERSE_CATS = {"ERA", "WHIP"}

TEAM_SHORT = {
    "Dancing With Dingos": "Dingos",
    "Gusteroids": "Gusteroids",
    "HAMMERHEADS": "Hammers",
    "Kerry & Mitch": "K&M",
    "Kosher Hogs": "K. Hogs",
    "Mean Machine": "Mean Mach",
    "On a Bender": "Bender",
    "R&R": "R&R",
    "Shrooms": "Shrooms",
    "Thunder & Lightning": "T&L",
}

# Lineup slots — 15 hitters, 11 pitchers (order = display order in card)
HITTER_LINEUP_SLOTS  = ["C", "C", "1B", "2B", "3B", "SS",
                         "CI", "MI", "OF", "OF", "OF", "OF", "OF", "UT", "UT"]
PITCHER_LINEUP_SLOTS = ["P"] * 11

# What positions satisfy each slot
SLOT_RULES = {
    "C":  {"C"},
    "1B": {"1B"},
    "2B": {"2B"},
    "3B": {"3B"},
    "SS": {"SS"},
    "CI": {"1B", "3B", "CI"},
    "MI": {"2B", "SS", "MI"},
    "OF": {"OF", "DH"},
    "UT": None,                  # any hitter
    "P":  {"SP", "RP", "P"},
}

# Placement priority: prefer specific slots before catch-all
SLOT_SPECIFICITY = {
    "C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1,
    "P": 1, "OF": 2, "CI": 3, "MI": 3, "UT": 5,
}

# Position filter canonical options shown in the UI
POS_FILTER_OPTIONS = ["C", "1B", "2B", "3B", "SS", "OF", "SP", "RP"]

# Tier threshold dropdown — maps label → list of included tiers (None = all)
TIER_THRESHOLDS = {
    "All tiers":       None,
    "Elite only":      ["Elite"],
    "Premium & above": ["Elite", "Premium"],
    "Solid & above":   ["Elite", "Premium", "Solid"],
    "Filler & above":  ["Elite", "Premium", "Solid", "Filler"],
    "Min & above":     ["Elite", "Premium", "Solid", "Filler", "Min"],
}

# ─── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@400;500&display=swap');
</style>""")
    st.html("""
<style>
:root {
  --primary:   #3A6EA5;
  --secondary: #C1666B;
  --accent:    #2A9D8F;
  --bg:        #faf9f5;
  --bg-card:   #f4f3ef;
  --grid:      #ededeb;
  --border:    #e0dfdb;
  --text:      #2d2d2d;
  --mid:       #666666;
  --light:     #999999;
}

/* ── Base ──────────────────────────────────────────────────── */
.stApp, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stHeader"] { background: var(--bg) !important; border-bottom: 1px solid var(--grid) !important; }
section.main .block-container { padding-top: 14px !important; max-width: 100% !important; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden !important; }

/* ── Typography ─────────────────────────────────────────────── */
body, .stApp, p, label, button, input, select {
    font-family: 'DM Sans', -apple-system, sans-serif !important;
    color: var(--text);
}

/* ── Page title ─────────────────────────────────────────────── */
.page-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 22px; font-weight: 700;
    color: var(--text); letter-spacing: -0.3px; line-height: 1.2;
    margin-bottom: 2px;
}
.page-sub {
    font-size: 11.5px; color: var(--light); margin-bottom: 14px;
    font-family: 'DM Sans', sans-serif;
}

/* ── Nomination form ─────────────────────────────────────────── */
.form-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.8px;
    color: var(--light); display: block; margin-bottom: 6px;
}
div[data-testid="stForm"] {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 14px 20px 12px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary) !important;
    color: white !important; border: none !important;
    border-radius: 5px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important;
    width: 100% !important; padding: 8px 0 !important;
    transition: background 0.15s !important;
}
div[data-testid="stFormSubmitButton"] > button:hover { background: #2d5a8a !important; }

/* ── Live ticker ─────────────────────────────────────────────── */
.ticker {
    display: flex; align-items: center; flex-wrap: wrap; gap: 5px;
    padding: 7px 4px; margin-bottom: 14px;
    border-top: 1px solid var(--grid);
}
.ticker-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; text-transform: uppercase; letter-spacing: 1.5px;
    color: var(--light); margin-right: 4px;
}
.t-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--bg-card); border: 1px solid var(--grid);
    border-radius: 4px; padding: 2px 7px; font-size: 11px;
}
.t-chip.mine { background: #eef4fa; border-color: #c5d9ef; }
.t-num  { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--light); }
.t-name { font-weight: 500; color: var(--text); }
.t-price{ font-family: 'JetBrains Mono', monospace; color: var(--secondary); }
.t-chip.mine .t-price { color: var(--primary); }
.t-team { color: var(--mid); font-size: 10.5px; }

/* ── Section label ───────────────────────────────────────────── */
.sec-hdr {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.8px;
    color: var(--light); margin: 14px 0 7px 0;
}

/* ── Budget grid ─────────────────────────────────────────────── */
.bud-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 7px;
    margin-bottom: 2px;
}
.bud-card {
    background: white; border: 1px solid var(--border);
    border-radius: 6px; padding: 9px 12px; text-align: center;
}
.bud-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 21px; font-weight: 500; color: var(--text); line-height: 1.1;
}
.bud-lbl {
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 1px; color: var(--light); margin-top: 3px;
}

/* ── Lineup card ─────────────────────────────────────────────── */
.lineup-wrap {
    border: 1px solid var(--border); border-radius: 6px;
    overflow: hidden; background: white; margin-bottom: 10px;
}
.lineup-sec-hdr {
    background: var(--text); padding: 6px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.5px; color: white;
}
.lineup-sec-hdr.reserve {
    background: var(--mid);
}
table.ltbl {
    width: 100%; border-collapse: separate; border-spacing: 0;
    font-size: 12px;
}
table.ltbl tr:nth-child(even) td { background: var(--bg); }
table.ltbl tr:hover td { background: #eef4fa !important; }
table.ltbl td { padding: 5px 10px; border-bottom: 1px solid var(--grid); }
table.ltbl tr:last-child td { border-bottom: none; }
.lt-slot {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.8px;
    color: var(--light); width: 28px;
}
.lt-player { font-weight: 500; color: var(--text); white-space: nowrap; }
.lt-empty  { color: var(--grid); font-style: italic; font-size: 11px; }
.lt-sal {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--light);
    text-align: right; width: 32px;
}
.bdg {
    display: inline-block; font-size: 7px;
    font-family: 'JetBrains Mono', monospace;
    border-radius: 2px; padding: 0 3px; margin-left: 4px;
    vertical-align: middle; letter-spacing: 0.2px; text-transform: uppercase;
}
.bdg-farm { background: #f0eeea; border: 1px solid var(--border); color: var(--light); }
.bdg-new  { background: #e8f4ea; border: 1px solid #b8d9bb; color: #2a7d3f; }

/* ── Category ranks ──────────────────────────────────────────── */
.cat-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 4px; margin-bottom: 10px;
}
.cat-row {
    background: white; border: 1px solid var(--border);
    border-radius: 4px; padding: 4px 8px;
    display: flex; align-items: center; gap: 6px;
}
.cat-nm {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500; color: var(--text); width: 28px;
}
.cat-pip {
    flex: 1; height: 3px; background: var(--grid);
    border-radius: 2px; overflow: hidden;
}
.cat-pip-fill { height: 100%; border-radius: 2px; }
.cat-rk {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 500; width: 12px; text-align: right;
}
.rk-hi  { color: var(--accent); }
.rk-mid { color: #f4a261; }
.rk-lo  { color: var(--secondary); }

/* ── Expander (full log) ─────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    background: white !important;
}

/* ── Table header ────────────────────────────────────────────── */
.tbl-heading {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 17px; font-weight: 600; color: var(--text);
    margin-bottom: 8px;
}
.tbl-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--light); font-weight: 400;
}

/* ── Streamlit metrics ───────────────────────────────────────── */
[data-testid="stMetric"] {
    background: white; border: 1px solid var(--border);
    border-radius: 6px; padding: 8px 12px !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 9px !important; color: var(--light) !important;
    text-transform: uppercase; letter-spacing: 1px;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 22px !important; color: var(--text) !important;
}

hr { border-color: var(--grid) !important; margin: 10px 0 !important; }

/* ── Collapse sidebar toggle ─────────────────────────────────── */
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ── Category breakdown panel (F1) ───────────────────────────── */
.cat-break {
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 5px; margin-top: 8px;
}
.cat-break-hdr {
    grid-column: 1 / -1;
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.5px;
    color: var(--light); padding: 6px 0 2px 0;
}
.cb-cell {
    background: white; border: 1px solid var(--border);
    border-radius: 5px; padding: 6px 8px; text-align: center;
}
.cb-cat {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500; color: var(--mid);
}
.cb-rank {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px; font-weight: 500; color: var(--text);
    margin: 2px 0;
}
.cb-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 500;
}
.cb-up   { color: var(--accent); }
.cb-flat { color: var(--light); }
.cb-down { color: var(--secondary); }

/* ── Inflation tracker (F3) ──────────────────────────────────── */
.inf-card {
    background: white; border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px; text-align: center;
    margin-bottom: 2px;
}
.inf-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 21px; font-weight: 500; line-height: 1.1;
}
.inf-hot  { color: var(--secondary); }
.inf-cool { color: var(--accent); }
.inf-flat { color: var(--text); }
.inf-lbl {
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 1px; color: var(--light); margin-top: 3px;
}
.inf-split {
    display: flex; justify-content: center; gap: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--mid); margin-top: 4px;
}

/* ── Standings heatmap (F5) ──────────────────────────────────── */
.hm-wrap {
    border: 1px solid var(--border); border-radius: 6px;
    overflow-x: auto; background: white;
}
table.hm-tbl {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
}
table.hm-tbl th {
    font-size: 8px; text-transform: uppercase; letter-spacing: 0.5px;
    color: var(--light); padding: 5px 4px; text-align: center;
    border-bottom: 1px solid var(--border);
}
table.hm-tbl td {
    padding: 4px; text-align: center; border-bottom: 1px solid var(--grid);
}
table.hm-tbl tr:last-child td { border-bottom: none; }
tr.hm-mine { background: #eef4fa !important; }
tr.hm-mine td:first-child { border-left: 3px solid var(--primary); }
.hm-team {
    text-align: left !important; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; max-width: 64px;
    font-size: 9px; font-weight: 500;
}
.hm-pts {
    font-weight: 600; border-left: 1px solid var(--border) !important;
}

/* ── Slot scarcity badges (F2) ───────────────────────────────── */
.lt-scar {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; text-align: right;
}
.lt-scar-critical { color: var(--secondary); font-weight: 600; }
.lt-scar-tight    { color: #f4a261; }
.lt-scar-ok       { color: var(--light); }

/* ── Projection card (F8) ────────────────────────────────────── */
.proj-card {
    background: white; border: 1px solid var(--border);
    border-radius: 6px; padding: 12px 14px; text-align: center;
    margin-bottom: 2px;
}
.proj-place {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 28px; font-weight: 700; color: var(--primary);
    line-height: 1.1;
}
.proj-pts {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px; color: var(--text); margin-top: 2px;
}
.proj-gap {
    font-size: 10px; color: var(--mid); margin-top: 2px;
}
.proj-cats {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 4px; margin-top: 6px;
}
.proj-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; background: var(--bg-card);
    border-radius: 3px; padding: 1px 4px;
}
</style>
""")


# ─── Data loading (cached) ────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading player valuations…")
def load_base_data() -> pd.DataFrame:
    """Load ATC valuations + compute split-pool auction values. Cached."""
    from sgp.config import SGPConfig
    from sgp.data_prep import get_calibration_data
    from sgp.dollar_values import compute_historical_spending_split, compute_split_pool_values
    from sgp.replacement import compute_replacement_level
    from sgp.sgp_calc import compute_sgp

    atc = pd.read_csv("data/valuations_atc_2026.csv")

    config = SGPConfig.composite()
    standings_hist = get_calibration_data(config)
    sgp_result = compute_sgp(standings_hist, config, bootstrap=False)
    replacement = compute_replacement_level(sgp_result, config, standings_df=standings_hist)
    hist_split = compute_historical_spending_split(config)
    hitter_pct = (
        hist_split["hitter_pct"].mean() / 100.0
        if hist_split is not None and not hist_split.empty
        else 0.63
    )
    # Recompute split-pool auction values using the same replacement dict that
    # produced the CSV's dollar_value column.  Both use SGPConfig.composite(),
    # so PAR will be consistent as long as composite config hasn't changed since
    # the projection pipeline was last run.
    player_sgp = atc[["player_name", "pos_type", "total_sgp"]].copy()
    split_df = compute_split_pool_values(player_sgp, replacement, config, hitter_pct=hitter_pct)
    atc["auction_value"] = split_df["auction_value"].values

    return atc


@st.cache_data(show_spinner="Loading keeper rosters…")
def load_keepers() -> pd.DataFrame:
    return pd.read_csv("data/preauction_rosters_2026.csv")


# ─── Live MSP recomputation ─────────────────────────────────────────────────

@st.cache_data(show_spinner="Recomputing targeting scores…")
def compute_live_msp(draft_key: tuple) -> tuple:
    """Re-run MSP pipeline with current draft state.

    Drafted players are added as virtual active keepers for their new teams,
    so MSP, projected standings, and category ranks all update live.

    Args:
        draft_key: Hashable tuple of (player, winner, price) for each draft pick.
                   Used as cache key — MSP only recomputes when draft state changes.

    Returns:
        (players_df, projected_standings) — available players with live MSP,
        and current projected standings with ranks.
    """
    from targeting.model import MSPConfig, run_msp

    valuations = load_base_data()
    keepers = load_keepers()

    # Build live keepers: original roster + drafted players as virtual keepers
    live_keepers = keepers.copy()
    for player, winner, price in draft_key:
        match = valuations[valuations["player_name"] == player]
        if not match.empty:
            row = match.iloc[0]
            pos = "P" if row.get("pos_type") == "pitcher" else row.get("position", "UT")
        else:
            pos = "UT"
        live_keepers = pd.concat([live_keepers, pd.DataFrame([{
            "team": winner, "player_name": player,
            "salary": price, "position": pos, "status": "act",
        }])], ignore_index=True)

    config = MSPConfig(
        baseline_type="proportional_fill",
        fill_discount=0.75,
        budget_displacement=True,
    )
    msp_results, projected_standings = run_msp(
        keepers=live_keepers,
        valuations=valuations,
        target_team=MY_TEAM,
        config=config,
    )

    # Exclude all owned players (farm keepers + drafted) from the auction pool
    all_owned = set(keepers["player_name"].tolist()) | {p for p, _, _ in draft_key}
    msp_results = msp_results[~msp_results["player_name"].isin(all_owned)].copy()

    # Add derived columns the app needs
    msp_results.rename(columns={"dollar_value": "production_value"}, inplace=True)
    msp_results["auction_value"] = msp_results["auction_value"].fillna(
        msp_results["production_value"]
    )
    msp_results["is_pitcher"] = msp_results["pos_type"] == "pitcher"
    msp_results["tier"] = msp_results["production_value"].apply(_get_tier)
    msp_results["profile"] = _classify_profiles(msp_results)

    return msp_results, projected_standings


# ─── Classification helpers ───────────────────────────────────────────────────

def _get_tier(v: float) -> str:
    for name, floor in TIERS:
        if v >= floor:
            return name
    return "Sub"


def _classify_profiles(df: pd.DataFrame) -> pd.Series:
    profiles = []
    for _, r in df.iterrows():
        if r.get("is_pitcher", r.get("pos_type", "") == "pitcher"):
            profiles.append("Closer" if (r.get("SV", 0) or 0) >= 10 else "Starter")
        else:
            sb  = abs(r.get("sgp_SB",  0) or 0)
            hr  = abs(r.get("sgp_HR",  0) or 0)
            rbi = abs(r.get("sgp_RBI", 0) or 0)
            avg = abs(r.get("sgp_AVG", 0) or 0)
            tot = sb + hr + rbi + avg
            if tot <= 0:
                profiles.append("Balanced")
            elif sb / tot > 0.35:
                profiles.append("Speed")
            elif (hr + rbi) / tot > 0.50:
                profiles.append("Power")
            elif avg / tot > 0.30:
                profiles.append("Average")
            else:
                profiles.append("Balanced")
    return pd.Series(profiles, index=df.index)


def _primary_pos(pos_str) -> str:
    """Extract primary position for scarcity grouping."""
    if not pos_str or (isinstance(pos_str, float) and pd.isna(pos_str)):
        return "UT"
    s = str(pos_str).strip()
    for sep in [",", "/"]:
        if sep in s:
            return s.split(sep)[0].strip()
    return s if s else "UT"


# ─── Eligibility & roster placement ──────────────────────────────────────────

def parse_eligibility(pos_str: str) -> list:
    """'2B,SS,MI' or '2B/SS' or 'OF' → list of position codes."""
    if not pos_str or (isinstance(pos_str, float) and pd.isna(pos_str)):
        return []
    s = str(pos_str).strip()
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    if "/" in s:
        return [p.strip() for p in s.split("/") if p.strip()]
    return [s] if s else []


def is_eligible_for_slot(elig: list, slot: str, is_pitcher: bool) -> bool:
    if slot == "P":
        return is_pitcher
    if is_pitcher:
        return False
    if slot == "UT":
        return True
    rules = SLOT_RULES.get(slot)
    if rules is None:
        return True
    return bool(set(elig) & rules)


def _fill_slot(s: dict, player: str, salary: int,
               elig: list, is_keeper: bool, is_farm: bool):
    s["player"]    = player
    s["salary"]    = salary
    s["eligibility"] = elig
    s["is_keeper"] = is_keeper
    s["is_farm"]   = is_farm


def try_place_player(name: str, elig: list, is_pitcher: bool,
                     salary: int, slots: list,
                     is_keeper: bool = False, is_farm: bool = False) -> bool:
    """
    Place player into roster (mutates slots). Returns True if placed.
    Strategy:
      1. Try first empty eligible slot (most-specific slot first).
      2. If all eligible slots occupied, try displacing an occupant to
         another empty slot so both players can fit.
    """
    eligible = [
        i for i, s in enumerate(slots)
        if is_eligible_for_slot(elig, s["slot"], is_pitcher)
    ]
    eligible.sort(key=lambda i: (
        0 if slots[i]["player"] is None else 1,
        SLOT_SPECIFICITY.get(slots[i]["slot"], 9),
    ))

    # Pass 1: empty slot
    for i in eligible:
        if slots[i]["player"] is None:
            _fill_slot(slots[i], name, salary, elig, is_keeper, is_farm)
            return True

    # Pass 2: displace an occupant that can move elsewhere
    for i in eligible:
        occ = slots[i]
        occ_elig = occ["eligibility"]
        occ_is_p = occ["slot"] == "P"
        # Find any OTHER empty slot the occupant could move to
        for j, s2 in enumerate(slots):
            if j == i or s2["player"] is not None:
                continue
            if is_eligible_for_slot(occ_elig, s2["slot"], occ_is_p):
                # Move occupant → j, place new player → i
                _fill_slot(s2, occ["player"], occ["salary"],
                           occ_elig, occ["is_keeper"], occ["is_farm"])
                _fill_slot(occ, name, salary, elig, is_keeper, is_farm)
                return True

    return False  # no placement found (roster full for this type)


def build_initial_roster(keepers: pd.DataFrame) -> tuple:
    """
    Build the active 26-slot roster list + a separate farm/reserve list.

    Active slots (15H + 11P) are filled only from act/dis keepers.
    Farm players (status='min') go in a separate reserve list — they do NOT
    occupy active lineup slots.

    Returns (slots, farm_players) where:
      slots        — list of 26 slot dicts
      farm_players — list of {player, slot, salary, eligibility} dicts
    """
    slots = []
    for s in HITTER_LINEUP_SLOTS:
        slots.append({"slot": s, "player": None, "salary": None,
                      "eligibility": [], "is_keeper": False, "is_farm": False})
    for s in PITCHER_LINEUP_SLOTS:
        slots.append({"slot": s, "player": None, "salary": None,
                      "eligibility": [], "is_keeper": False, "is_farm": False})

    farm_players = []
    my_k = keepers[keepers["team"] == MY_TEAM].copy()

    for _, k in my_k.iterrows():
        assigned = k["position"]
        elig     = parse_eligibility(k.get("eligibility", k["position"]))
        is_farm  = k["status"] == "min"
        is_p     = (assigned == "P")
        salary   = int(k["salary"])
        name     = k["player_name"]

        if is_farm:
            # Reserve players shown in a separate Farm section — not in active slots
            farm_players.append({
                "player":      name,
                "slot":        assigned,
                "salary":      salary,
                "eligibility": elig,
            })
        else:
            # Place active keeper in their assigned slot
            placed = False
            for slot_dict in slots:
                if slot_dict["slot"] == assigned and slot_dict["player"] is None:
                    _fill_slot(slot_dict, name, salary, elig, is_keeper=True, is_farm=False)
                    placed = True
                    break
            if not placed:
                try_place_player(name, elig, is_p, salary, slots, is_keeper=True, is_farm=False)

    return slots, farm_players


# ─── Session state ────────────────────────────────────────────────────────────

def init_state(keepers: pd.DataFrame):
    my_k  = keepers[keepers["team"] == MY_TEAM]
    act_k = my_k[my_k["status"].isin(["act", "dis"])]
    act_h = len(act_k[act_k["position"] != "P"])
    act_p = len(act_k[act_k["position"] == "P"])

    active_slots, farm_players = build_initial_roster(keepers)

    defaults = {
        "taken":            {},
        "auction_log":      [],
        "nom_counter":      0,
        "budget_spent":     0,
        "hitters_won":      0,
        "pitchers_won":     0,
        "salary_committed": int(act_k["salary"].sum()),
        "act_hitters":      act_h,
        "act_pitchers":     act_p,
        "roster_slots":     active_slots,
        "farm_players":     farm_players,
        "punted_categories": set(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Scoring ──────────────────────────────────────────────────────────────────

def _rescale_0_10(series: pd.Series) -> pd.Series:
    """Min-max rescale a Series to the 0–10 range."""
    lo, hi = series.min(), series.max()
    if hi - lo < 1e-9:
        return pd.Series(5.0, index=series.index)
    return (10.0 * (series - lo) / (hi - lo)).round(1)


def compute_scarcity(players: pd.DataFrame, taken_names: set) -> pd.Series:
    available  = players[~players["player_name"].isin(taken_names)].copy()
    available["_ppos"] = available["position"].apply(_primary_pos)
    sp         = pd.Series(0.0, index=players.index)
    tier_order = [n for n, _ in TIERS]

    for idx, row in players.iterrows():
        if row["player_name"] in taken_names:
            continue
        tier, profile, pval = row["tier"], row["profile"], row["production_value"]
        ppos = _primary_pos(row.get("position", ""))

        # Position-aware comparables: same tier + profile + primary position
        comp = available[
            (available["tier"] == tier) &
            (available["profile"] == profile) &
            (available["_ppos"] == ppos) &
            (available["player_name"] != row["player_name"])
        ]
        if len(comp) == 0:
            tidx = tier_order.index(tier) if tier in tier_order else len(tier_order) - 1
            fallback = 0.0
            for nt in tier_order[tidx + 1:]:
                # Try position-matched lower tier first
                fb = available[
                    (available["tier"] == nt) &
                    (available["profile"] == profile) &
                    (available["_ppos"] == ppos)
                ]
                if len(fb) == 0:
                    # Relax position for lower-tier fallback
                    fb = available[(available["tier"] == nt) & (available["profile"] == profile)]
                if len(fb) > 0:
                    fallback = fb["production_value"].nlargest(3).mean()
                    break
            sp[idx] = max(0.0, pval - fallback)
        elif len(comp) <= 2:
            sp[idx] = max(0.0, (pval - comp["production_value"].nlargest(3).mean()) * 0.5)
    return sp


def detect_punt_candidates(standings: pd.DataFrame, scored: pd.DataFrame) -> list:
    """Identify categories that are punt candidates.

    A category is a punt candidate if Gusteroids' rank <= 2 AND the best
    available player for that category would improve rank by <= 1.
    """
    my_row = standings[standings["team"] == MY_TEAM]
    if my_row.empty:
        return []
    mr = my_row.iloc[0]
    candidates = []
    for cat in CATEGORIES:
        rank = float(mr.get(f"rank_{cat}", 5))
        if rank <= 2:
            col = f"delta_rank_{cat}"
            if col in scored.columns and len(scored) > 0:
                best_delta = scored[col].max()
                if best_delta <= 1:
                    candidates.append(cat)
            else:
                candidates.append(cat)
    return candidates


def score_players(players: pd.DataFrame, taken_names: set, budget_cap: float,
                  punted_cats=None, inflation=None) -> pd.DataFrame:
    available = players[~players["player_name"].isin(taken_names)].copy()
    sp_series = compute_scarcity(players, taken_names)
    available["sp_raw"]  = sp_series.reindex(available.index).fillna(0.0)

    # PVP: use punted-cat-adjusted MSP if categories are punted (F9)
    if punted_cats:
        punt_cols = [f"delta_rank_{cat}" for cat in CATEGORIES
                     if cat not in punted_cats and f"delta_rank_{cat}" in available.columns]
        adjusted_msp = available[punt_cols].sum(axis=1) if punt_cols else 0.0
        available["pvp_raw"] = (adjusted_msp * DOLLARS_PER_STANDINGS_PT).round(1)
    else:
        available["pvp_raw"] = (available["msp"] * DOLLARS_PER_STANDINGS_PT).round(1)

    # MI: production value minus inflation-adjusted market price (consistent formula)
    hitter_inf = 1.0 + (inflation.get("hitter_pct", 0.0) if inflation else 0.0)
    pitcher_inf = 1.0 + (inflation.get("pitcher_pct", 0.0) if inflation else 0.0)
    adjusted_mkt = available["auction_value"].copy()
    is_p = available["is_pitcher"]
    adjusted_mkt.loc[~is_p] *= hitter_inf
    adjusted_mkt.loc[is_p] *= pitcher_inf
    available["mi"] = available["production_value"] - adjusted_mkt

    # Rescale each component to 0–10 for balanced composite targeting score
    available["pvp"] = _rescale_0_10(available["pvp_raw"])
    available["sp"]  = _rescale_0_10(available["sp_raw"])
    available["mi_sc"] = _rescale_0_10(available["mi"])
    available["ts"]  = ((available["pvp"] + available["sp"] + available["mi_sc"]) / 3).round(1)

    # Punt penalty: discount TS by fraction of SGP in punted categories
    if punted_cats:
        total_abs_sgp = pd.Series(0.0, index=available.index)
        punted_abs_sgp = pd.Series(0.0, index=available.index)
        for cat in CATEGORIES:
            col = f"sgp_{cat}"
            if col in available.columns:
                total_abs_sgp += available[col].abs()
                if cat in punted_cats:
                    punted_abs_sgp += available[col].abs()
        punt_frac = punted_abs_sgp / total_abs_sgp.clip(lower=0.01)
        available["ts"] = (available["ts"] * (1 - punt_frac)).round(1)

    # ── Bid calculations ────────────────────────────────────────────────
    # Max bid: production value + scaled MSP premium. Above this price the player
    # becomes a net negative — the opportunity cost of overspending exceeds the
    # standings-point gain.  MSP_BID_RATE ($2/SP) is ~30% of the team-level
    # $6.55/SP, discounted for cascading fill impact and projection uncertainty.
    msp_premium = available["msp"].clip(lower=0) * MSP_BID_RATE
    available["max_bid"] = (
        available["production_value"] + msp_premium
    ).clip(lower=1, upper=budget_cap).round(0).astype(int)

    # Target bid: what you should try to win the player for — market price plus
    # a modest team-fit bump.  Half the max-bid MSP rate so you're aiming for
    # value, not paying up to the ceiling.
    auc = available["auction_value"].fillna(available["production_value"])
    tgt_premium = available["msp"].clip(lower=0) * (MSP_BID_RATE * 0.5)
    available["tgt_bid"] = (auc + tgt_premium).clip(lower=1).round(0).astype(int)
    available["tgt_bid"] = available[["tgt_bid", "max_bid"]].min(axis=1)

    return available


# ─── Log result ───────────────────────────────────────────────────────────────

def _log_result(player: str, price: int, winner: str, players_df: pd.DataFrame):
    st.session_state.nom_counter += 1
    n = st.session_state.nom_counter
    st.session_state.taken[player] = {"team": winner, "price": price, "nom_order": n}
    st.session_state.auction_log.append({
        "nom":       n,
        "player":    player,
        "winner":    winner,
        "price":     price,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })
    if winner == MY_TEAM:
        st.session_state.budget_spent += price
        match = players_df[players_df["player_name"] == player]
        if not match.empty:
            row  = match.iloc[0]
            is_p = bool(row.get("is_pitcher", False))
            elig = parse_eligibility(row.get("position", ""))
            if is_p:
                st.session_state.pitchers_won += 1
            else:
                st.session_state.hitters_won += 1
            try_place_player(
                player, elig, is_p, price,
                st.session_state.roster_slots,
                is_keeper=False, is_farm=False,
            )


# ─── Undo last result ────────────────────────────────────────────────────────

def _undo_last_result():
    """Reverse the most recent auction log entry."""
    if not st.session_state.auction_log:
        return
    entry = st.session_state.auction_log.pop()
    player = entry["player"]
    winner = entry["winner"]
    price = entry["price"]
    st.session_state.taken.pop(player, None)
    st.session_state.nom_counter = max(0, st.session_state.nom_counter - 1)

    if winner == MY_TEAM:
        st.session_state.budget_spent -= price
        # Determine if pitcher by looking up in base data
        base = load_base_data()
        match = base[base["player_name"] == player]
        is_p = False
        if not match.empty:
            is_p = match.iloc[0].get("pos_type") == "pitcher"
        if is_p:
            st.session_state.pitchers_won = max(0, st.session_state.pitchers_won - 1)
        else:
            st.session_state.hitters_won = max(0, st.session_state.hitters_won - 1)
        # Remove player from roster_slots (non-keeper only)
        for s in st.session_state.roster_slots:
            if s["player"] == player and not s["is_keeper"]:
                s["player"] = None
                s["salary"] = None
                s["eligibility"] = []
                s["is_keeper"] = False
                s["is_farm"] = False
                break


# ─── Position filter helper ───────────────────────────────────────────────────

def player_matches_positions(pos_str: str, is_pitcher: bool, selected: list) -> bool:
    """Return True if the player's canonical positions overlap with `selected`."""
    if not selected:
        return True
    elig = parse_eligibility(pos_str)
    canonical: set = set()
    for p in elig:
        if p == "C":            canonical.add("C")
        elif p == "1B":         canonical.add("1B")
        elif p == "2B":         canonical.add("2B")
        elif p == "3B":         canonical.add("3B")
        elif p == "SS":         canonical.add("SS")
        elif p in ("OF", "DH"): canonical.add("OF")
        elif p == "CI":         canonical.update({"1B", "3B"})
        elif p == "MI":         canonical.update({"2B", "SS"})
        elif p == "SP":         canonical.add("SP")
        elif p == "RP":         canonical.add("RP")
        elif p == "P":          canonical.update({"SP", "RP"})
    return bool(canonical & set(selected))


# ─── HTML component builders ──────────────────────────────────────────────────

def _budget_html(budget_left: int, eff_budget: int, h_open: int, p_open: int) -> str:
    return f"""
<div class="bud-grid">
  <div class="bud-card">
    <div class="bud-val">${budget_left}</div>
    <div class="bud-lbl">Budget Left</div>
  </div>
  <div class="bud-card">
    <div class="bud-val">${eff_budget}</div>
    <div class="bud-lbl">Eff. Budget</div>
  </div>
  <div class="bud-card">
    <div class="bud-val">{h_open}</div>
    <div class="bud-lbl">H Spots</div>
  </div>
  <div class="bud-card">
    <div class="bud-val">{p_open}</div>
    <div class="bud-lbl">P Spots</div>
  </div>
</div>"""


def _lineup_section_html(title: str, slots: list, slot_scarcity=None) -> str:
    rows = ""
    for s in slots:
        idx = s.get("_idx")  # injected by _lineup_html
        if s["player"]:
            badge = ""
            if s["is_farm"]:
                badge = '<span class="bdg bdg-farm">farm</span>'
            elif not s["is_keeper"]:
                badge = '<span class="bdg bdg-new">new</span>'
            sal = f'${s["salary"]}' if s["salary"] is not None else ""
            rows += (
                f'<tr>'
                f'<td class="lt-slot">{s["slot"]}</td>'
                f'<td class="lt-player">{s["player"]}{badge}</td>'
                f'<td class="lt-sal">{sal}</td>'
                f'</tr>'
            )
        else:
            scar_html = ""
            if slot_scarcity and idx is not None and idx in slot_scarcity:
                sc = slot_scarcity[idx]
                sev_cls = f"lt-scar-{sc['severity']}"
                scar_html = f'<td class="lt-scar {sev_cls}">{sc["n_quality"]} left</td>'
            if scar_html:
                rows += (
                    f'<tr>'
                    f'<td class="lt-slot">{s["slot"]}</td>'
                    f'<td class="lt-empty">—</td>'
                    f'{scar_html}'
                    f'</tr>'
                )
            else:
                rows += (
                    f'<tr>'
                    f'<td class="lt-slot">{s["slot"]}</td>'
                    f'<td class="lt-empty" colspan="2">—</td>'
                    f'</tr>'
                )
    return f'<div class="lineup-sec-hdr">{title}</div><table class="ltbl">{rows}</table>'


def _lineup_html(slots: list, farm_players: list, slot_scarcity=None) -> str:
    # Inject original index for scarcity lookup
    for i, s in enumerate(slots):
        s["_idx"] = i
    hitter_slots  = [s for s in slots if s["slot"] != "P"]
    pitcher_slots = [s for s in slots if s["slot"] == "P"]

    html = (
        '<div class="lineup-wrap">'
        + _lineup_section_html("Hitters", hitter_slots, slot_scarcity)
        + _lineup_section_html("Pitchers", pitcher_slots, slot_scarcity)
    )

    if farm_players:
        rows = ""
        for fp in sorted(farm_players, key=lambda x: x["slot"]):
            rows += (
                f'<tr>'
                f'<td class="lt-slot">{fp["slot"]}</td>'
                f'<td class="lt-player">{fp["player"]}'
                f'<span class="bdg bdg-farm">farm</span></td>'
                f'<td class="lt-sal">${fp["salary"]}</td>'
                f'</tr>'
            )
        html += (
            '<div class="lineup-sec-hdr reserve">Farm / Reserve</div>'
            f'<table class="ltbl">{rows}</table>'
        )

    html += '</div>'
    return html


def _cat_ranks_html(standings: pd.DataFrame) -> str:
    my_row = standings[standings["team"] == MY_TEAM]
    if my_row.empty:
        return ""
    mr = my_row.iloc[0]
    items = ""
    for cat in CATEGORIES:
        rank = float(mr.get(f"rank_{cat}", 5))
        good = rank >= 7
        bad  = rank <= 3
        cls  = "rk-hi" if good else ("rk-lo" if bad else "rk-mid")
        pip_color = "#2A9D8F" if good else ("#C1666B" if bad else "#f4a261")
        pct = int(rank / 10 * 100)
        items += f"""<div class="cat-row">
  <span class="cat-nm">{cat}</span>
  <div class="cat-pip"><div class="cat-pip-fill" style="width:{pct}%;background:{pip_color};"></div></div>
  <span class="cat-rk {cls}">{int(rank)}</span>
</div>"""
    return f'<div class="cat-grid">{items}</div>'


def _ticker_html(log: list) -> str:
    if not log:
        return ""
    recent = list(reversed(log))[:5]
    chips = ""
    for e in recent:
        mine = e["winner"] == MY_TEAM
        cls = "t-chip mine" if mine else "t-chip"
        chips += (
            f'<span class="{cls}">'
            f'<span class="t-num">#{e["nom"]}</span> '
            f'<span class="t-name">{e["player"]}</span> '
            f'<span class="t-price">${e["price"]}</span> '
            f'<span class="t-team">→ {e["winner"]}</span>'
            f'</span>'
        )
    return (
        f'<div class="ticker">'
        f'<span class="ticker-label">Recent</span>{chips}'
        f'</div>'
    )


# ─── Slot scarcity (F2) ──────────────────────────────────────────────────────

def compute_slot_scarcity(roster_slots: list, scored: pd.DataFrame, taken_names: set) -> dict:
    """For each unfilled active slot, count eligible quality available players.

    Returns dict mapping slot_index -> {slot, n_quality, severity}.
    Quality = tier in {Elite, Premium, Solid}.
    """
    quality_tiers = {"Elite", "Premium", "Solid"}
    quality = scored[scored["tier"].isin(quality_tiers)]
    result = {}

    for i, s in enumerate(roster_slots):
        if s["player"] is not None:
            continue
        slot = s["slot"]
        is_pitcher_slot = (slot == "P")
        n = 0
        for _, row in quality.iterrows():
            elig = parse_eligibility(row.get("position", ""))
            is_p = bool(row.get("is_pitcher", False))
            if is_eligible_for_slot(elig, slot, is_p):
                n += 1
        if n == 0:
            severity = "critical"
        elif n <= 3:
            severity = "tight"
        else:
            severity = "ok"
        result[i] = {"slot": slot, "n_quality": n, "severity": severity}
    return result


# ─── Inflation tracking (F3) ──────────────────────────────────────────────────

def compute_inflation(auction_log: list, base_data: pd.DataFrame) -> dict:
    """Compute market inflation/deflation from auction results."""
    result = {"overall_pct": 0.0, "hitter_pct": 0.0, "pitcher_pct": 0.0,
              "total_surplus": 0.0, "n_players": 0}
    if not auction_log:
        return result

    pcts, h_pcts, p_pcts, surplus = [], [], [], 0.0
    for entry in auction_log:
        match = base_data[base_data["player_name"] == entry["player"]]
        if match.empty:
            continue
        row = match.iloc[0]
        mkt = row.get("auction_value", 0)
        if mkt is None or pd.isna(mkt) or mkt <= 0:
            continue
        actual = entry["price"]
        pct = (actual - mkt) / mkt
        pcts.append(pct)
        surplus += actual - mkt
        if row.get("pos_type") == "pitcher":
            p_pcts.append(pct)
        else:
            h_pcts.append(pct)

    if pcts:
        result["overall_pct"] = np.mean(pcts)
        result["total_surplus"] = surplus
        result["n_players"] = len(pcts)
    if h_pcts:
        result["hitter_pct"] = np.mean(h_pcts)
    if p_pcts:
        result["pitcher_pct"] = np.mean(p_pcts)
    return result


def _inflation_html(inflation: dict) -> str:
    """Render inflation tracker card."""
    pct = inflation.get("overall_pct", 0.0)
    h_pct = inflation.get("hitter_pct", 0.0)
    p_pct = inflation.get("pitcher_pct", 0.0)
    n = inflation.get("n_players", 0)

    if n == 0:
        return (
            '<div class="inf-card">'
            '<div class="inf-val inf-flat">—</div>'
            '<div class="inf-lbl">Market Inflation</div>'
            '<div class="inf-split"><span>No data yet</span></div>'
            '</div>'
        )

    sign = "+" if pct >= 0 else ""
    cls = "inf-hot" if pct > 0.02 else ("inf-cool" if pct < -0.02 else "inf-flat")
    h_sign = "+" if h_pct >= 0 else ""
    p_sign = "+" if p_pct >= 0 else ""
    return (
        f'<div class="inf-card">'
        f'<div class="inf-val {cls}">{sign}{pct:.0%}</div>'
        f'<div class="inf-lbl">Market Inflation ({n} players)</div>'
        f'<div class="inf-split">'
        f'<span>H: {h_sign}{h_pct:.0%}</span>'
        f'<span>P: {p_sign}{p_pct:.0%}</span>'
        f'</div></div>'
    )


# ─── Standings heatmap (F5) ──────────────────────────────────────────────────

def _rank_bg(rank: float) -> str:
    """Background-color CSS for a rank 1-10."""
    if rank >= 8:
        return f"rgba(42, 157, 143, {0.15 + (rank - 8) * 0.1})"
    elif rank >= 4:
        return f"rgba(244, 162, 97, {0.08 + (rank - 4) * 0.04})"
    else:
        return f"rgba(193, 102, 107, {0.15 + (3 - rank) * 0.1})"


def _standings_heatmap_html(standings: pd.DataFrame) -> str:
    """Build 10-team x 10-category heatmap HTML table."""
    sorted_st = standings.sort_values("total_pts", ascending=False)

    header = '<th class="hm-team">Team</th>'
    for cat in CATEGORIES:
        header += f'<th>{cat}</th>'
    header += '<th class="hm-pts">Pts</th>'

    rows = ""
    for _, row in sorted_st.iterrows():
        team = row["team"]
        short = TEAM_SHORT.get(team, team[:8])
        tr_cls = ' class="hm-mine"' if team == MY_TEAM else ""
        cells = f'<td class="hm-team">{short}</td>'
        for cat in CATEGORIES:
            rk = float(row.get(f"rank_{cat}", 5))
            bg = _rank_bg(rk)
            cells += f'<td style="background:{bg};">{int(rk)}</td>'
        pts = float(row.get("total_pts", 0))
        cells += f'<td class="hm-pts">{pts:.1f}</td>'
        rows += f'<tr{tr_cls}>{cells}</tr>'

    return (
        f'<div class="hm-wrap"><table class="hm-tbl">'
        f'<thead><tr>{header}</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )


# ─── Projection card (F8) ────────────────────────────────────────────────────

def _ordinal(n: int) -> str:
    """1 → '1st', 2 → '2nd', 3 → '3rd', etc."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd'][n % 10] if n % 10 < 4 else 'th'}"


def _projections_html(standings: pd.DataFrame) -> str:
    """Render projected finish card for Gusteroids."""
    sorted_st = standings.sort_values("total_pts", ascending=False).reset_index(drop=True)
    my_mask = sorted_st["team"] == MY_TEAM
    if not my_mask.any():
        return ""
    my_idx = sorted_st.index[my_mask][0]
    my_row = sorted_st.iloc[my_idx]
    place = my_idx + 1
    total_pts = float(my_row["total_pts"])

    gap_html = ""
    if place > 1:
        above = sorted_st.iloc[my_idx - 1]
        gap = float(above["total_pts"]) - total_pts
        gap_html = f'<div class="proj-gap">{gap:.1f} pts to {_ordinal(place - 1)}</div>'

    badges = ""
    for cat in CATEGORIES:
        rk = int(my_row.get(f"rank_{cat}", 5))
        cls = "rk-hi" if rk >= 7 else ("rk-lo" if rk <= 3 else "rk-mid")
        badges += f'<span class="proj-badge {cls}">{cat}:{rk}</span>'

    return (
        f'<div class="proj-card">'
        f'<div class="proj-place">{_ordinal(place)}</div>'
        f'<div class="proj-pts">{total_pts:.1f} pts</div>'
        f'{gap_html}'
        f'<div class="proj-cats">{badges}</div>'
        f'</div>'
    )


# ─── Nomination strategy (F7) ───────────────────────────────────────────────

def compute_nomination_scores(scored: pd.DataFrame, standings: pd.DataFrame) -> pd.Series:
    """Compute nomination score for each available player.

    Good nomination targets have high value (rivals will bid), fill rival
    weaknesses, and low/negative MSP for Gusteroids.
    """
    # Identify rival weak categories (rank <= 4)
    rivals = standings[standings["team"] != MY_TEAM]
    n_rivals = len(rivals)
    if n_rivals == 0:
        return pd.Series(0.0, index=scored.index)

    # For each player, count how many rivals need what they provide
    rival_need_counts = pd.Series(0.0, index=scored.index)
    for _, rival_row in rivals.iterrows():
        weak_cats = [cat for cat in CATEGORIES if float(rival_row.get(f"rank_{cat}", 5)) <= 4]
        if not weak_cats:
            continue
        for cat in weak_cats:
            sgp_col = f"sgp_{cat}"
            if sgp_col not in scored.columns:
                continue
            # For ERA/WHIP: negative sgp = good pitcher (helps that category)
            if cat in INVERSE_CATS:
                helps = scored[sgp_col] < -0.3
            else:
                helps = scored[sgp_col] > 0.3
            rival_need_counts += helps.astype(float)

    rival_need_factor = rival_need_counts / (n_rivals * len(CATEGORIES))

    # Normalize MSP to [0, 1] where 0 = highest MSP, 1 = lowest (don't need)
    msp = scored["msp"].copy()
    msp_range = msp.max() - msp.min()
    if msp_range > 1e-9:
        norm_msp = (msp - msp.min()) / msp_range
    else:
        norm_msp = pd.Series(0.5, index=scored.index)
    anti_msp = 1.0 - norm_msp

    pval = scored["production_value"].clip(lower=0)
    nom_score = (pval * rival_need_factor * anti_msp).round(1)
    return nom_score


# ─── Category breakdown HTML (F1) ─────────────────────────────────────────────

def _category_breakdown_html(player_row: pd.Series) -> str:
    """Build HTML grid showing per-category rank deltas for a selected player."""
    batting_cats = ["R", "HR", "RBI", "SB", "AVG"]
    pitching_cats = ["W", "SV", "ERA", "WHIP", "SO"]

    def _cell(cat):
        cur = int(player_row.get(f"team_rank_{cat}", 5))
        delta = float(player_row.get(f"delta_rank_{cat}", 0))
        new_rank = cur + int(round(delta))
        if delta > 0:
            cls, sign = "cb-up", f"+{delta:.1f}"
        elif delta < 0:
            cls, sign = "cb-down", f"{delta:.1f}"
        else:
            cls, sign = "cb-flat", "0"
        return (
            f'<div class="cb-cell">'
            f'<div class="cb-cat">{cat}</div>'
            f'<div class="cb-rank">{cur} → {new_rank}</div>'
            f'<div class="cb-delta {cls}">{sign}</div>'
            f'</div>'
        )

    cells_bat = "".join(_cell(c) for c in batting_cats)
    cells_pit = "".join(_cell(c) for c in pitching_cats)
    return (
        f'<div class="cat-break">'
        f'<div class="cat-break-hdr">Batting</div>{cells_bat}'
        f'<div class="cat-break-hdr">Pitching</div>{cells_pit}'
        f'</div>'
    )


# ─── Render sections ───────────────────────────────────────────────────────────

def render_nomination_bar(all_available: list, all_teams: list, players_df: pd.DataFrame):
    st.html('<span class="form-label">Log Auction Result</span>')
    with st.form("nom_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([4, 1, 3, 1])
        player = c1.selectbox(
            "Player", [""] + sorted(all_available),
            key="nom_player", label_visibility="collapsed",
            placeholder="Player sold…",
        )
        price = c2.number_input(
            "Price", min_value=1, max_value=360, value=1,
            key="nom_price", label_visibility="collapsed",
        )
        winner = c3.selectbox(
            "Winner", [""] + all_teams,
            key="nom_winner", label_visibility="collapsed",
            placeholder="Winning team…",
        )
        c4.write("")
        submitted = c4.form_submit_button("Log ✓", use_container_width=True)

        if submitted:
            if not player:
                st.warning("Select a player.", icon="⚠️")
            elif not winner:
                st.warning("Select a winning team.", icon="⚠️")
            else:
                _log_result(player, int(price), winner, players_df)
                st.rerun()

    ticker = _ticker_html(st.session_state.auction_log)
    if ticker:
        st.html(ticker)

    # Undo button (F4)
    if st.session_state.auction_log:
        undo_col, spacer = st.columns([1, 5])
        with undo_col:
            if st.button("↩ Undo Last", key="undo_btn", use_container_width=True):
                _undo_last_result()
                st.rerun()


def render_left_column(standings: pd.DataFrame,
                       budget_left: int, eff_budget: int,
                       h_open: int, p_open: int,
                       inflation: dict = None,
                       scored: pd.DataFrame = None,
                       slot_scarcity: dict = None):
    # Projected Finish (F8)
    st.html('<div class="sec-hdr">Projected Finish</div>')
    st.html(_projections_html(standings))

    # Budget cards
    st.html('<div class="sec-hdr">Budget &amp; Spots</div>')
    st.html(_budget_html(budget_left, eff_budget, h_open, p_open))

    # Inflation Tracker (F3)
    if inflation is not None:
        st.html('<div class="sec-hdr">Market</div>')
        st.html(_inflation_html(inflation))

    # Lineup card with scarcity badges (F2)
    st.html('<div class="sec-hdr">My Lineup</div>')
    st.html(_lineup_html(st.session_state.roster_slots, st.session_state.farm_players,
                         slot_scarcity=slot_scarcity))

    # Category ranks
    st.html('<div class="sec-hdr">Category Ranks</div>')
    st.html(_cat_ranks_html(standings))

    # Punt Categories (F9)
    if scored is not None:
        st.html('<div class="sec-hdr">Punt Categories</div>')
        punt_suggestions = detect_punt_candidates(standings, scored)
        punted = st.multiselect(
            "Punt categories", options=CATEGORIES,
            default=list(st.session_state.punted_categories),
            label_visibility="collapsed", key="punt_select",
            placeholder=f"Suggested: {', '.join(punt_suggestions)}" if punt_suggestions else "None suggested",
        )
        st.session_state.punted_categories = set(punted)

    # Field Standings heatmap (F5)
    with st.expander("Field Standings", expanded=False):
        st.html(_standings_heatmap_html(standings))

    # Full auction log (collapsible, collapsed by default)
    log = st.session_state.auction_log
    if log:
        with st.expander(f"Full Auction Log  ({len(log)})", expanded=False):
            log_df = pd.DataFrame(log)
            st.dataframe(log_df, hide_index=True, use_container_width=True)
            st.download_button(
                "⬇ Download CSV",
                data=log_df.to_csv(index=False),
                file_name="auction_log_2026.csv",
                mime="text/csv",
            )


def render_right_column(scored: pd.DataFrame, standings: pd.DataFrame = None):
    # ── Filter row — three controls ──────────────────────────────────
    fc1, fc2, fc3 = st.columns([4, 3, 5])

    pos_filter = fc1.multiselect(
        "Position",
        options=POS_FILTER_OPTIONS,
        default=[],
        placeholder="All positions…",
        label_visibility="collapsed",
    )

    tier_key = fc2.selectbox(
        "Tier",
        options=list(TIER_THRESHOLDS.keys()),
        index=3,   # default: "Solid & above"
        label_visibility="collapsed",
    )

    search = fc3.text_input(
        "Search",
        placeholder="🔍  Player name…",
        label_visibility="collapsed",
    )

    # ── Apply filters ────────────────────────────────────────────────
    view = scored.copy()

    # Position filter
    if pos_filter:
        view = view[view.apply(
            lambda r: player_matches_positions(
                r["position"], bool(r.get("is_pitcher", False)), pos_filter
            ), axis=1
        )]

    # Tier threshold filter
    allowed_tiers = TIER_THRESHOLDS[tier_key]
    if allowed_tiers is not None:
        view = view[view["tier"].isin(allowed_tiers)]

    # Name search
    if search:
        view = view[view["player_name"].str.contains(search, case=False, na=False)]

    # Always compute nomination scores (F7)
    if standings is not None:
        view["nom_score"] = compute_nomination_scores(view, standings)

    view = view.sort_values("ts", ascending=False)

    # ── Header ───────────────────────────────────────────────────────
    st.html(
        f'<div class="tbl-heading">Available Free Agents '
        f'<span class="tbl-count">({len(view)})</span></div>'
    )

    # ── Table — both TS and Nom always visible, click headers to sort ─
    cols = [
        "player_name", "position", "tier",
        "production_value", "auction_value",
        "pvp", "sp", "mi_sc", "ts",
        "tgt_bid", "max_bid",
    ]
    rename_map = {
        "player_name":      "Player",
        "position":         "Pos",
        "tier":             "Tier",
        "production_value": "Value $",
        "auction_value":    "Mkt $",
        "pvp":              "PVP",
        "sp":               "SP",
        "mi_sc":            "MI",
        "ts":               "TS",
        "tgt_bid":          "Target",
        "max_bid":          "Max",
    }
    col_configs = {
        "TS":     st.column_config.NumberColumn("TS",     format="%.1f",
            help="Targeting Score (0–10) = avg(PVP, SP, MI). Higher = better fit for your roster."),
        "Target": st.column_config.NumberColumn("Target", format="$%d",
            help="Target bid: market price + $1/MSP. What you should try to win them for."),
        "Max":    st.column_config.NumberColumn("Max",    format="$%d",
            help="Max bid: production value + $2/MSP. Walk-away price — above this, net negative for your team."),
        "Value $": st.column_config.NumberColumn("Value $", format="$%.1f",
            help="Position-neutral production value (single-pool SGP). What this player is worth ignoring hitter/pitcher market split."),
        "Mkt $":  st.column_config.NumberColumn("Mkt $",  format="$%.1f",
            help="Expected market price (split-pool SGP). Accounts for historical ~63/37 hitter/pitcher spending split."),
        "MI":     st.column_config.NumberColumn("MI",     format="%.1f",
            help="Market Inefficiency (0–10 scale). Production value minus inflation-adjusted market price. Higher = more undervalued."),
        "PVP":    st.column_config.NumberColumn("PVP",    format="%.1f",
            help="Personal Value Premium (0–10 scale). How much this player helps YOUR standings specifically."),
        "SP":     st.column_config.NumberColumn("SP",     format="%.1f",
            help="Scarcity Premium (0–10 scale). Higher = fewer comparable alternatives at same position."),
    }

    if "nom_score" in view.columns:
        cols.append("nom_score")
        rename_map["nom_score"] = "Nom"
        col_configs["Nom"] = st.column_config.NumberColumn("Nom", format="%.1f",
            help="Nomination score. High = good to nominate (rivals want, you don't). Click header to sort.")

    display = view[[c for c in cols if c in view.columns]].copy().rename(columns=rename_map)
    for col in ["Value $", "Mkt $", "PVP", "SP", "MI", "TS"]:
        if col in display.columns:
            display[col] = display[col].round(1)

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=600,
        column_config=col_configs,
    )

    # ── Category Breakdown (F1) ──────────────────────────────────────
    visible_players = view["player_name"].tolist()
    if visible_players:
        detail_player = st.selectbox(
            "Player Detail", options=[""] + visible_players,
            placeholder="Select player for category breakdown…",
            label_visibility="collapsed", key="detail_player",
        )
        if detail_player:
            match = scored[scored["player_name"] == detail_player]
            if not match.empty:
                st.html(_category_breakdown_html(match.iloc[0]))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    inject_css()

    keepers   = load_keepers()
    all_teams = sorted(keepers["team"].unique().tolist())

    init_state(keepers)

    # Recompute MSP with current draft state (cached on draft_key)
    draft_key = tuple(
        (e["player"], e["winner"], e["price"])
        for e in st.session_state.auction_log
    )
    players, live_standings = compute_live_msp(draft_key)

    # Budget calculations
    total_spent   = st.session_state.salary_committed + st.session_state.budget_spent
    budget_left   = TOTAL_BUDGET - total_spent
    h_open = HITTER_SLOTS  - st.session_state.act_hitters  - st.session_state.hitters_won
    p_open = PITCHER_SLOTS - st.session_state.act_pitchers - st.session_state.pitchers_won
    spots   = h_open + p_open
    eff_budget = max(0, budget_left - spots)
    budget_cap = max(1, budget_left - max(0, spots - 1))

    # Inflation tracking (F3)
    base_data = load_base_data()
    inflation = compute_inflation(st.session_state.auction_log, base_data)

    # Score available free agents with punt + inflation adjustments (F6, F9)
    taken_names = set(st.session_state.taken.keys())
    punted = st.session_state.get("punted_categories", set())
    scored = score_players(players, taken_names, budget_cap,
                           punted_cats=punted, inflation=inflation)

    # Slot scarcity (F2)
    slot_scarcity = compute_slot_scarcity(
        st.session_state.roster_slots, scored, taken_names
    )

    # ── Page title ──────────────────────────────────────────────────
    st.html(
        f'<div class="page-title">Moonlight Graham  2026</div>'
        f'<div class="page-sub">'
        f'Live Auction · Gusteroids · '
        f'Nomination <span style="font-family:JetBrains Mono,monospace;">'
        f'#{st.session_state.nom_counter}</span>'
        f'</div>'
    )

    # ── Nomination bar (F4: undo button added inside) ────────────────
    render_nomination_bar(scored["player_name"].tolist(), all_teams, players)

    # ── Two-column layout ────────────────────────────────────────────
    left, right = st.columns([30, 70])

    with left:
        render_left_column(live_standings, budget_left, eff_budget, h_open, p_open,
                           inflation=inflation, scored=scored, slot_scarcity=slot_scarcity)

    with right:
        render_right_column(scored, standings=live_standings)


main()

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

MI_FULL_PENALTY = -8.0
MI_PARTIAL_LOW  = -3.0

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
</style>
""")


# ─── Data loading (cached) ────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading player data and computing auction values…")
def load_players() -> pd.DataFrame:
    from sgp.config import SGPConfig
    from sgp.data_prep import get_calibration_data
    from sgp.dollar_values import compute_historical_spending_split, compute_split_pool_values
    from sgp.replacement import compute_replacement_level
    from sgp.sgp_calc import compute_sgp

    msp = pd.read_csv("data/msp_gusteroids_atc_2026.csv")

    # Exclude all keepers — they're already assigned to teams, not in the auction pool
    keepers_all = pd.read_csv("data/preauction_rosters_2026.csv")
    keeper_names = set(keepers_all["player_name"].tolist())
    msp = msp[~msp["player_name"].isin(keeper_names)].copy()

    # Compute split-pool auction values
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
    player_sgp = atc[["player_name", "pos_type", "total_sgp"]].copy()
    split_df = compute_split_pool_values(player_sgp, replacement, config, hitter_pct=hitter_pct)
    name_to_auction = dict(zip(atc["player_name"], split_df["auction_value"].values))

    msp["auction_value"] = msp["player_name"].map(name_to_auction)
    msp.rename(columns={"dollar_value": "production_value"}, inplace=True)
    msp["mi"] = msp["production_value"] - msp["auction_value"].fillna(msp["production_value"])
    msp["tier"] = msp["production_value"].apply(_get_tier)
    msp["profile"] = _classify_profiles(msp)
    return msp


@st.cache_data(show_spinner="Loading keeper rosters…")
def load_keepers() -> pd.DataFrame:
    return pd.read_csv("data/preauction_rosters_2026.csv")


@st.cache_data(show_spinner="Loading projected standings…")
def load_standings() -> pd.DataFrame:
    return pd.read_csv("data/msp_projected_standings_2026.csv")


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
        "salary_committed": int(my_k["salary"].sum()),
        "act_hitters":      act_h,
        "act_pitchers":     act_p,
        "roster_slots":     active_slots,
        "farm_players":     farm_players,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Scoring ──────────────────────────────────────────────────────────────────

def compute_scarcity(players: pd.DataFrame, taken_names: set) -> pd.Series:
    available  = players[~players["player_name"].isin(taken_names)].copy()
    sp         = pd.Series(0.0, index=players.index)
    tier_order = [n for n, _ in TIERS]

    for idx, row in players.iterrows():
        if row["player_name"] in taken_names:
            continue
        tier, profile, pval = row["tier"], row["profile"], row["production_value"]
        comp = available[
            (available["tier"] == tier) &
            (available["profile"] == profile) &
            (available["player_name"] != row["player_name"])
        ]
        if len(comp) == 0:
            tidx = tier_order.index(tier) if tier in tier_order else len(tier_order) - 1
            fallback = 0.0
            for nt in tier_order[tidx + 1:]:
                fb = available[(available["tier"] == nt) & (available["profile"] == profile)]
                if len(fb) > 0:
                    fallback = fb["production_value"].nlargest(3).mean()
                    break
            sp[idx] = max(0.0, pval - fallback)
        elif len(comp) <= 2:
            sp[idx] = max(0.0, (pval - comp["production_value"].nlargest(3).mean()) * 0.5)
    return sp


def compute_mi_adjustment(mi: float) -> float:
    if mi >= MI_PARTIAL_LOW:
        return 0.0
    if mi <= MI_FULL_PENALTY:
        return -5.0
    return -5.0 * (mi - MI_PARTIAL_LOW) / (MI_FULL_PENALTY - MI_PARTIAL_LOW)


def score_players(players: pd.DataFrame, taken_names: set, budget_cap: float) -> pd.DataFrame:
    available = players[~players["player_name"].isin(taken_names)].copy()
    sp_series = compute_scarcity(players, taken_names)
    available["sp"]     = sp_series.reindex(available.index).fillna(0.0)
    available["pvp"]    = (available["msp"] * DOLLARS_PER_STANDINGS_PT).round(1)
    available["mi_adj"] = available["mi"].apply(compute_mi_adjustment)
    available["ts"]     = (available["pvp"] + available["sp"] + available["mi_adj"]).round(1)
    auc = available["auction_value"].fillna(available["production_value"])
    available["bid_ceil"] = (
        auc + available["pvp"].clip(lower=0) + available["sp"].clip(lower=0)
    ).clip(upper=budget_cap).round(0).astype(int)
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


def _lineup_section_html(title: str, slots: list) -> str:
    rows = ""
    for s in slots:
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
            rows += (
                f'<tr>'
                f'<td class="lt-slot">{s["slot"]}</td>'
                f'<td class="lt-empty" colspan="2">—</td>'
                f'</tr>'
            )
    return f'<div class="lineup-sec-hdr">{title}</div><table class="ltbl">{rows}</table>'


def _lineup_html(slots: list, farm_players: list) -> str:
    hitter_slots  = [s for s in slots if s["slot"] != "P"]
    pitcher_slots = [s for s in slots if s["slot"] == "P"]

    html = (
        '<div class="lineup-wrap">'
        + _lineup_section_html("Hitters", hitter_slots)
        + _lineup_section_html("Pitchers", pitcher_slots)
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
            "Price", min_value=1, max_value=75, value=1,
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


def render_left_column(standings: pd.DataFrame,
                       budget_left: int, eff_budget: int,
                       h_open: int, p_open: int):
    # Budget cards
    st.html('<div class="sec-hdr">Budget &amp; Spots</div>')
    st.html(_budget_html(budget_left, eff_budget, h_open, p_open))

    # Lineup card
    st.html('<div class="sec-hdr">My Lineup</div>')
    st.html(_lineup_html(st.session_state.roster_slots, st.session_state.farm_players))

    # Category ranks
    st.html('<div class="sec-hdr">Category Ranks</div>')
    st.html(_cat_ranks_html(standings))

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


def render_right_column(scored: pd.DataFrame):
    # ── Filter row — three controls, all collapsed labels for alignment ──
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

    view = view.sort_values("ts", ascending=False)

    # ── Header ───────────────────────────────────────────────────────
    st.html(
        f'<div class="tbl-heading">Available Free Agents '
        f'<span class="tbl-count">({len(view)})</span></div>'
    )

    # ── Table — Profile dropped to keep Bid $ visible ────────────────
    display = view[[
        "player_name", "position", "tier",
        "production_value", "auction_value", "mi",
        "pvp", "sp", "ts", "bid_ceil",
    ]].copy().rename(columns={
        "player_name":      "Player",
        "position":         "Pos",
        "tier":             "Tier",
        "production_value": "Prod $",
        "auction_value":    "Auc $",
        "mi":               "MI",
        "pvp":              "PVP",
        "sp":               "SP",
        "ts":               "TS",
        "bid_ceil":         "Bid $",
    })
    for col in ["Prod $", "Auc $", "MI", "PVP", "SP", "TS"]:
        if col in display.columns:
            display[col] = display[col].round(1)

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=660,
        column_config={
            "TS":     st.column_config.NumberColumn("TS",     format="%.1f",
                help="Targeting Score = PVP + SP + MI gate. Primary sort."),
            "Bid $":  st.column_config.NumberColumn("Bid $",  format="$%d",
                help="Bid ceiling = Auc$ + max(0,PVP) + max(0,SP), capped at budget."),
            "Prod $": st.column_config.NumberColumn("Prod $", format="$%.1f",
                help="Single-pool production value."),
            "Auc $":  st.column_config.NumberColumn("Auc $",  format="$%.1f",
                help="Split-pool market price."),
            "MI":     st.column_config.NumberColumn("MI",     format="$%.1f",
                help="Market Inefficiency = Prod$ − Auc$. Positive = undervalued."),
            "PVP":    st.column_config.NumberColumn("PVP",    format="$%.1f",
                help="Personal Value Premium = MSP × $6.55/pt."),
            "SP":     st.column_config.NumberColumn("SP",     format="$%.1f",
                help="Scarcity Premium. Opportunity cost of passing."),
        },
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    inject_css()

    players   = load_players()
    keepers   = load_keepers()
    standings = load_standings()
    all_teams = sorted(keepers["team"].unique().tolist())

    init_state(keepers)

    # Budget calculations
    total_spent   = st.session_state.salary_committed + st.session_state.budget_spent
    budget_left   = TOTAL_BUDGET - total_spent
    h_open = HITTER_SLOTS  - st.session_state.act_hitters  - st.session_state.hitters_won
    p_open = PITCHER_SLOTS - st.session_state.act_pitchers - st.session_state.pitchers_won
    spots   = h_open + p_open
    eff_budget = max(0, budget_left - spots)
    budget_cap = max(1, budget_left - max(0, spots - 1))

    # Score available free agents
    taken_names = set(st.session_state.taken.keys())
    scored = score_players(players, taken_names, budget_cap)

    # ── Page title ──────────────────────────────────────────────────
    st.html(
        f'<div class="page-title">Moonlight Graham  2026</div>'
        f'<div class="page-sub">'
        f'Live Auction · Gusteroids · '
        f'Nomination <span style="font-family:JetBrains Mono,monospace;">'
        f'#{st.session_state.nom_counter}</span>'
        f'</div>'
    )

    # ── Nomination bar (always at top) ──────────────────────────────
    render_nomination_bar(scored["player_name"].tolist(), all_teams, players)

    # ── Two-column layout ────────────────────────────────────────────
    left, right = st.columns([30, 70])

    with left:
        render_left_column(standings, budget_left, eff_budget, h_open, p_open)

    with right:
        render_right_column(scored)


main()

"""
Moonlight Graham — 2026 Live Auction Tool

Real-time targeting scores, bid ceilings, and auction order recording.

Run with:
    streamlit run auction/app.py
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MGL 2026 Auction",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ───────────────────────────────────────────────────────────────

MY_TEAM = "Gusteroids"
TOTAL_BUDGET = 360
HITTER_SLOTS = 15
PITCHER_SLOTS = 11
DOLLARS_PER_STANDINGS_PT = 6.55   # $3600 league pool / ~550 total standings points

# Dollar tier breakpoints (name, minimum dollar value to qualify)
TIERS = [
    ("Elite",   25.0),
    ("Premium", 15.0),
    ("Solid",    8.0),
    ("Filler",   4.0),
    ("Min",      1.0),
    ("Sub",      0.0),
]

CATEGORIES = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]
INVERSE_CATS = {"ERA", "WHIP"}   # lower is better

# MI gate thresholds
MI_FULL_PENALTY = -8.0    # below this: apply $5 penalty
MI_PARTIAL_LOW  = -3.0    # between this and MI_FULL_PENALTY: partial penalty

# ─── Data loading (cached) ───────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading player data and computing auction values…")
def load_players() -> pd.DataFrame:
    """Load MSP results and compute split-pool auction values."""
    from sgp.config import SGPConfig
    from sgp.data_prep import get_calibration_data
    from sgp.dollar_values import compute_historical_spending_split, compute_split_pool_values
    from sgp.replacement import compute_replacement_level
    from sgp.sgp_calc import compute_sgp

    # Load pre-computed MSP results (available players only, for Gusteroids)
    msp = pd.read_csv("data/msp_gusteroids_atc_2026.csv")

    # Compute split-pool auction values from raw ATC projections
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

    # Map auction_value onto msp by player_name
    name_to_auction = dict(zip(atc["player_name"], split_df["auction_value"].values))
    msp["auction_value"] = msp["player_name"].map(name_to_auction)

    # Market Inefficiency: how much the market underprices this player
    # production_value = single-pool actual worth; auction_value = market price
    msp.rename(columns={"dollar_value": "production_value"}, inplace=True)
    msp["mi"] = msp["production_value"] - msp["auction_value"].fillna(msp["production_value"])

    # Dollar tier
    msp["tier"] = msp["production_value"].apply(_get_tier)

    # Category profile
    msp["profile"] = _classify_profiles(msp)

    return msp


@st.cache_data(show_spinner="Loading keeper rosters…")
def load_keepers() -> pd.DataFrame:
    return pd.read_csv("data/preauction_rosters_2026.csv")


@st.cache_data(show_spinner="Loading projected standings…")
def load_standings() -> pd.DataFrame:
    return pd.read_csv("data/msp_projected_standings_2026.csv")


# ─── Classification helpers ──────────────────────────────────────────────────

def _get_tier(v: float) -> str:
    for name, floor in TIERS:
        if v >= floor:
            return name
    return "Sub"


def _classify_profiles(df: pd.DataFrame) -> pd.Series:
    """Assign category profile to each player."""
    profiles = []
    for _, r in df.iterrows():
        if r.get("is_pitcher", r.get("pos_type", "") == "pitcher"):
            sv = r.get("SV", 0) or 0
            profiles.append("Closer" if sv >= 10 else "Starter")
        else:
            sb  = abs(r.get("sgp_SB",  0) or 0)
            hr  = abs(r.get("sgp_HR",  0) or 0)
            rbi = abs(r.get("sgp_RBI", 0) or 0)
            avg = abs(r.get("sgp_AVG", 0) or 0)
            total = sb + hr + rbi + avg
            if total <= 0:
                profiles.append("Balanced")
            elif sb / total > 0.35:
                profiles.append("Speed")
            elif (hr + rbi) / total > 0.50:
                profiles.append("Power")
            elif avg / total > 0.30:
                profiles.append("Average")
            else:
                profiles.append("Balanced")
    return pd.Series(profiles, index=df.index)


# ─── Session state ───────────────────────────────────────────────────────────

def init_state(keepers: pd.DataFrame):
    my_k = keepers[keepers["team"] == MY_TEAM]
    act_k = my_k[my_k["status"].isin(["act", "dis"])]
    act_hitters  = len(act_k[act_k["position"] != "P"])
    act_pitchers = len(act_k[act_k["position"] == "P"])

    defaults = {
        "taken":           {},     # player_name → {team, price, nom_order}
        "auction_log":     [],     # [{nom, player, winner, price, timestamp}]
        "nom_counter":     0,
        "budget_spent":    0,
        "hitters_won":     0,
        "pitchers_won":    0,
        "salary_committed": int(my_k["salary"].sum()),
        "act_hitters":     act_hitters,
        "act_pitchers":    act_pitchers,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Scarcity computation ────────────────────────────────────────────────────

def compute_scarcity(players: pd.DataFrame, taken_names: set) -> pd.Series:
    """Compute Scarcity Premium for each available player.

    SP = max(0, player_value − mean of top-3 comparable player values)
    Comparable = same tier + same profile, not yet taken.
    Falls back to next tier down when no comparables remain.
    """
    available = players[~players["player_name"].isin(taken_names)].copy()
    sp = pd.Series(0.0, index=players.index)

    tier_order = [name for name, _ in TIERS]

    for idx, row in players.iterrows():
        if row["player_name"] in taken_names:
            continue

        tier    = row["tier"]
        profile = row["profile"]
        pval    = row["production_value"]

        comp = available[
            (available["tier"] == tier) &
            (available["profile"] == profile) &
            (available["player_name"] != row["player_name"])
        ]

        if len(comp) == 0:
            # Last of this bucket — compare to next tier down, same profile
            tier_idx = tier_order.index(tier) if tier in tier_order else len(tier_order) - 1
            fallback_val = 0.0
            for next_tier in tier_order[tier_idx + 1:]:
                fb = available[
                    (available["tier"] == next_tier) &
                    (available["profile"] == profile)
                ]
                if len(fb) > 0:
                    fallback_val = fb["production_value"].nlargest(3).mean()
                    break
            sp[idx] = max(0.0, pval - fallback_val)

        elif len(comp) <= 2:
            # Very scarce — partial premium
            top_val = comp["production_value"].nlargest(3).mean()
            sp[idx] = max(0.0, (pval - top_val) * 0.5)

        # else: enough comparables, SP = 0

    return sp


# ─── Targeting score and bid ceiling ─────────────────────────────────────────

def compute_mi_adjustment(mi: float) -> float:
    if mi >= MI_PARTIAL_LOW:
        return 0.0
    if mi <= MI_FULL_PENALTY:
        return -5.0
    # Linear interpolation in the partial zone
    frac = (mi - MI_PARTIAL_LOW) / (MI_FULL_PENALTY - MI_PARTIAL_LOW)
    return -5.0 * frac


def score_players(players: pd.DataFrame, taken_names: set, budget_cap: float) -> pd.DataFrame:
    """Add sp, ts, and bid_ceil to available players."""
    available = players[~players["player_name"].isin(taken_names)].copy()

    # Scarcity Premium
    sp_series = compute_scarcity(players, taken_names)
    available["sp"] = sp_series.reindex(available.index).fillna(0.0)

    # PVP in dollars (MSP × $/pt)
    available["pvp"] = (available["msp"] * DOLLARS_PER_STANDINGS_PT).round(1)

    # MI adjustment (gate)
    available["mi_adj"] = available["mi"].apply(compute_mi_adjustment)

    # Targeting Score
    available["ts"] = (available["pvp"] + available["sp"] + available["mi_adj"]).round(1)

    # Bid Ceiling = auction_value + max(0, pvp) + max(0, sp), capped at budget
    auc_val = available["auction_value"].fillna(available["production_value"])
    available["bid_ceil"] = (
        auc_val
        + available["pvp"].clip(lower=0)
        + available["sp"].clip(lower=0)
    ).clip(upper=budget_cap).round(0).astype(int)

    return available


# ─── Sidebar ─────────────────────────────────────────────────────────────────

def render_sidebar(keepers: pd.DataFrame, standings: pd.DataFrame):
    st.sidebar.header("My Team — Gusteroids")

    # Budget and spots
    total_spent     = st.session_state.salary_committed + st.session_state.budget_spent
    budget_remaining = TOTAL_BUDGET - total_spent
    hitters_remaining = (
        HITTER_SLOTS - st.session_state.act_hitters - st.session_state.hitters_won
    )
    pitchers_remaining = (
        PITCHER_SLOTS - st.session_state.act_pitchers - st.session_state.pitchers_won
    )
    spots_remaining  = hitters_remaining + pitchers_remaining
    effective_budget = max(0, budget_remaining - spots_remaining)

    col1, col2 = st.sidebar.columns(2)
    col1.metric("Budget Left", f"${budget_remaining}")
    col2.metric("Eff. Budget", f"${effective_budget}",
                help="After reserving $1 per remaining spot")

    col3, col4 = st.sidebar.columns(2)
    col3.metric("H Spots", hitters_remaining)
    col4.metric("P Spots", pitchers_remaining)

    st.sidebar.divider()

    # Category ranks
    my_row = standings[standings["team"] == MY_TEAM]
    if not my_row.empty:
        st.sidebar.subheader("Category Ranks")
        mr = my_row.iloc[0]
        for cat in CATEGORIES:
            rank = mr.get(f"rank_{cat}", 5.0)
            if cat in INVERSE_CATS:
                color = "🟢" if rank >= 7 else ("🟡" if rank >= 4 else "🔴")
            else:
                color = "🟢" if rank >= 7 else ("🟡" if rank >= 4 else "🔴")
            st.sidebar.write(f"{color} **{cat}** — {rank:.0f} / 10")

    st.sidebar.divider()

    # My keepers
    my_k = keepers[keepers["team"] == MY_TEAM].sort_values("salary", ascending=False)
    st.sidebar.subheader("Keepers")
    for _, k in my_k.iterrows():
        status_tag = " *(farm)*" if k["status"] == "min" else ""
        st.sidebar.caption(f"${k['salary']:>3}  {k['player_name']}{status_tag}")

    # Auction wins so far
    my_wins = [(n, d) for n, d in st.session_state.taken.items() if d["team"] == MY_TEAM]
    if my_wins:
        st.sidebar.divider()
        st.sidebar.subheader("Auction Wins")
        for name, d in sorted(my_wins, key=lambda x: x[1]["nom_order"]):
            st.sidebar.caption(f"#{d['nom_order']}  ${d['price']:>3}  {name}")


# ─── Nomination form ─────────────────────────────────────────────────────────

def render_nomination_form(available_names: list, all_teams: list):
    with st.expander("📝 Log Auction Result", expanded=True):
        cols = st.columns([3, 1, 2, 1])
        player = cols[0].selectbox("Player Sold", [""] + sorted(available_names),
                                   key="nom_player", label_visibility="collapsed",
                                   placeholder="Select player…")
        price  = cols[1].number_input("Price", min_value=1, max_value=75, value=1,
                                       key="nom_price", label_visibility="collapsed")
        winner = cols[2].selectbox("Winner", [""] + all_teams,
                                   key="nom_winner", label_visibility="collapsed",
                                   placeholder="Winning team…")
        cols[3].write("")  # vertical spacing
        submit = cols[3].button("Log ✓", type="primary", use_container_width=True)

        if submit:
            if not player:
                st.warning("Select a player.")
            elif not winner:
                st.warning("Select the winning team.")
            else:
                _log_result(player, int(price), winner)
                st.rerun()


def _log_result(player: str, price: int, winner: str):
    st.session_state.nom_counter += 1
    n = st.session_state.nom_counter

    st.session_state.taken[player] = {
        "team": winner, "price": price, "nom_order": n,
    }
    st.session_state.auction_log.append({
        "nom":       n,
        "player":    player,
        "winner":    winner,
        "price":     price,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })

    if winner == MY_TEAM:
        st.session_state.budget_spent += price
        players_df = load_players()
        match = players_df[players_df["player_name"] == player]
        if not match.empty:
            is_p = bool(match.iloc[0].get("is_pitcher", False))
            if is_p:
                st.session_state.pitchers_won += 1
            else:
                st.session_state.hitters_won += 1


# ─── Auction log ─────────────────────────────────────────────────────────────

def render_log():
    log = st.session_state.auction_log
    if not log:
        return

    with st.expander(f"📋 Auction Log  ({len(log)} transactions)", expanded=False):
        log_df = pd.DataFrame(log)
        st.dataframe(log_df, hide_index=True, use_container_width=True)

        csv = log_df.to_csv(index=False)
        st.download_button(
            "⬇ Download Log CSV",
            data=csv,
            file_name="auction_log_2026.csv",
            mime="text/csv",
        )


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load data
    players  = load_players()
    keepers  = load_keepers()
    standings = load_standings()
    all_teams = sorted(keepers["team"].unique().tolist())

    # Initialize session state
    init_state(keepers)

    # Compute budget cap for bid ceilings
    total_spent       = st.session_state.salary_committed + st.session_state.budget_spent
    budget_remaining  = TOTAL_BUDGET - total_spent
    hitters_remaining = HITTER_SLOTS - st.session_state.act_hitters  - st.session_state.hitters_won
    pitchers_remaining = PITCHER_SLOTS - st.session_state.act_pitchers - st.session_state.pitchers_won
    spots_remaining   = hitters_remaining + pitchers_remaining
    budget_cap        = max(1, budget_remaining - max(0, spots_remaining - 1))

    # Score available players
    taken_names = set(st.session_state.taken.keys())
    scored = score_players(players, taken_names, budget_cap)

    # Sidebar
    render_sidebar(keepers, standings)

    # ── Header row ──────────────────────────────────────────────────────────
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns(5)
    hcol1.metric("Nomination #", st.session_state.nom_counter)
    hcol2.metric("Budget Left", f"${budget_remaining}")
    hcol3.metric("Effective Budget", f"${max(0, budget_remaining - spots_remaining)}")
    hcol4.metric("H Spots Left", hitters_remaining)
    hcol5.metric("P Spots Left", pitchers_remaining)

    st.divider()

    # ── Filters ─────────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 4])
    pos_filter     = fc1.selectbox("Position type", ["All", "Hitter", "Pitcher"],
                                   label_visibility="collapsed")
    tier_filter    = fc2.multiselect("Tier", ["Elite", "Premium", "Solid", "Filler", "Min", "Sub"],
                                     default=["Elite", "Premium", "Solid"],
                                     placeholder="Filter tiers…")
    profile_filter = fc3.multiselect("Profile",
                                      ["Power", "Speed", "Average", "Balanced", "Starter", "Closer"],
                                      placeholder="Filter profiles…")
    search         = fc4.text_input("Search", placeholder="Player name…",
                                    label_visibility="collapsed")

    # Apply filters
    view = scored.copy()
    if pos_filter == "Hitter":
        view = view[view["pos_type"] == "hitter"]
    elif pos_filter == "Pitcher":
        view = view[view["pos_type"] == "pitcher"]
    if tier_filter:
        view = view[view["tier"].isin(tier_filter)]
    if profile_filter:
        view = view[view["profile"].isin(profile_filter)]
    if search:
        view = view[view["player_name"].str.contains(search, case=False, na=False)]

    view = view.sort_values("ts", ascending=False)

    # ── Targeting table ──────────────────────────────────────────────────────
    st.subheader(f"Available Players  ({len(view)} shown)")

    display = view[[
        "player_name", "position", "profile", "tier",
        "production_value", "auction_value", "mi",
        "pvp", "sp", "ts", "bid_ceil",
        "msp", "tps",
    ]].copy().rename(columns={
        "player_name":      "Player",
        "position":         "Pos",
        "profile":          "Profile",
        "tier":             "Tier",
        "production_value": "Prod $",
        "auction_value":    "Auction $",
        "mi":               "MI",
        "pvp":              "PVP",
        "sp":               "SP",
        "ts":               "TS",
        "bid_ceil":         "Bid Ceil",
        "msp":              "MSP",
        "tps":              "TPS (raw)",
    })

    for col in ["Prod $", "Auction $", "MI", "PVP", "SP", "TS", "MSP"]:
        if col in display.columns:
            display[col] = display[col].round(1)

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=520,
        column_config={
            "TS": st.column_config.NumberColumn(
                "TS",
                help="Targeting Score = PVP + SP + MI adjustment. Higher = target harder.",
                format="%.1f",
            ),
            "TPS (raw)": st.column_config.ProgressColumn(
                "TPS (raw)",
                help="Pre-computed Target Priority Score (1–100). Based on MSP residual vs expected for price tier.",
                min_value=1, max_value=100, format="%d",
            ),
            "Bid Ceil": st.column_config.NumberColumn(
                "Bid Ceil",
                help="Max you should pay = Auction$ + PVP + SP, capped at budget.",
                format="$%d",
            ),
            "Prod $":    st.column_config.NumberColumn("Prod $",    format="$%.1f"),
            "Auction $": st.column_config.NumberColumn("Auction $", format="$%.1f"),
            "MI":        st.column_config.NumberColumn("MI",    format="$%.1f",
                help="Market Inefficiency = Prod$ − Auction$. Positive = undervalued."),
            "PVP":       st.column_config.NumberColumn("PVP",   format="$%.1f",
                help="Personal Value Premium = MSP × $/standings point. How much extra this is worth to YOUR team."),
            "SP":        st.column_config.NumberColumn("SP",    format="$%.1f",
                help="Scarcity Premium. How much extra to pay because comparable alternatives are limited."),
            "MSP":       st.column_config.NumberColumn("MSP",   format="%.2f",
                help="Marginal Standings Points: how many standings points this player adds to your team."),
        },
    )

    st.divider()

    # ── Nomination form ──────────────────────────────────────────────────────
    available_names = view["player_name"].tolist()
    render_nomination_form(available_names, all_teams)

    # ── Auction log ──────────────────────────────────────────────────────────
    render_log()


main()

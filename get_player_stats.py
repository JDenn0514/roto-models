"""
Fetch player stats from FanGraphs via pybaseball and match to fantasy rosters.

For each year, pulls batting and pitching leaderboards from FanGraphs,
then joins to historical_rosters.csv to attach fantasy team, salary, and
contract data. Only players on a fantasy roster are kept.

Output: data/player_stats.csv
"""

import pandas as pd
import pybaseball

pybaseball.cache.enable()

YEARS = [2019, 2021, 2022, 2023, 2024]  # skip 2020 (COVID), skip 2025 (partial)

# FanGraphs team abbreviation → OnRoto abbreviation
TEAM_MAP = {
    # AL teams
    "BAL": "Bal", "BOS": "Bos", "CHW": "CWS", "CLE": "Cle", "DET": "Det",
    "HOU": "Hou", "KCR": "KC",  "LAA": "LAA", "MIN": "Min", "NYY": "NYY",
    "OAK": "Oak", "SEA": "Sea", "TBR": "TB",  "TEX": "Tex", "TOR": "Tor",
    # NL teams (for players traded mid-season)
    "ARI": "Ari", "ATL": "Atl", "CHC": "ChC", "CIN": "Cin", "COL": "Col",
    "LAD": "LAD", "MIA": "Mia", "MIL": "Mil", "NYM": "NYM", "PHI": "Phi",
    "PIT": "Pit", "SDP": "SD",  "SFG": "SF",  "STL": "StL", "WSN": "Was",
    "- - -": "FA",
}

# Common name normalizations (FanGraphs name → OnRoto name)
NAME_FIXES = {
    "Cedric Mullins II": "Cedric Mullins",
    "Lourdes Gurriel Jr.": "Lourdes Gurriel",
    "Ha-Seong Kim": "Ha-seong Kim",
    "Giovanny Urshela": "Gio Urshela",
    "Enrique Hernandez": "Kike Hernandez",
    "Kiké Hernández": "Kike Hernandez",
    "Hyun Jin Ryu": "Hyun-Jin Ryu",
    "Shohei Ohtani": "Shohei Ohtani-Pitcher",  # pitching stats entry
}

# Reverse fixes: OnRoto name → FanGraphs name (for roster-side matching)
ROSTER_NAME_FIXES = {
    "Bobby Witt": "Bobby Witt Jr.",
    "Luis M. Castillo": "Luis Castillo",
    "Luis Castillo": "Luis Castillo",
    "Mike King": "Michael King",
    "Mark Leiter": "Mark Leiter Jr.",
    "Daniel Coulombe": "Danny Coulombe",
    "Zach Britton": "Zack Britton",
    "Dee Gordon": "Dee Strange-Gordon",
    "Robert Stephenson": "Robert Stephenson",
    "Giovanny Urshela": "Gio Urshela",
    "D.J. LeMahieu": "DJ LeMahieu",
    "Lance McCullers": "Lance McCullers Jr.",
    "Triston McKenzie": "Triston McKenzie",
    "Bobby Witt Jr.": "Bobby Witt Jr.",
}


def _normalize_name(name: str) -> str:
    """Normalize a player name for matching."""
    name = name.strip()
    # Apply known fixes
    if name in NAME_FIXES:
        return NAME_FIXES[name]
    return name


def fetch_batting_stats(year: int) -> pd.DataFrame:
    """Fetch season batting stats from FanGraphs. qual=0 gets all players."""
    print(f"  Fetching {year} batting stats from FanGraphs...")
    bat = pybaseball.batting_stats(year, qual=0)

    # Map team abbreviations
    bat["mlb_team"] = bat["Team"].map(TEAM_MAP).fillna(bat["Team"])

    # Normalize names
    bat["player_name"] = bat["Name"].apply(_normalize_name)

    # Select relevant columns
    cols = {
        "player_name": "player_name",
        "mlb_team": "mlb_team",
        "IDfg": "fg_id",
        "G": "G",
        "AB": "AB",
        "PA": "PA",
        "R": "R",
        "HR": "HR",
        "RBI": "RBI",
        "SB": "SB",
        "AVG": "AVG",
    }
    out = bat[[c for c in cols if c in bat.columns]].rename(
        columns={k: v for k, v in cols.items() if k != v and k in bat.columns}
    )
    out["is_pitcher"] = False
    out["year"] = year
    return out


def fetch_pitching_stats(year: int) -> pd.DataFrame:
    """Fetch season pitching stats from FanGraphs. qual=0 gets all players."""
    print(f"  Fetching {year} pitching stats from FanGraphs...")
    pit = pybaseball.pitching_stats(year, qual=0)

    pit["mlb_team"] = pit["Team"].map(TEAM_MAP).fillna(pit["Team"])
    pit["player_name"] = pit["Name"].apply(_normalize_name)

    cols = {
        "player_name": "player_name",
        "mlb_team": "mlb_team",
        "IDfg": "fg_id",
        "G": "G",
        "IP": "IP",
        "W": "W",
        "SV": "SV",
        "ERA": "ERA",
        "WHIP": "WHIP",
        "SO": "SO",
    }
    out = pit[[c for c in cols if c in pit.columns]].rename(
        columns={k: v for k, v in cols.items() if k != v and k in pit.columns}
    )
    out["is_pitcher"] = True
    out["year"] = year
    return out


def match_to_rosters(
    stats: pd.DataFrame, rosters: pd.DataFrame, year: int
) -> pd.DataFrame:
    """Match FanGraphs stats to fantasy roster data for a given year.

    Matching strategy:
    1. Exact name match (primary)
    2. Name + mlb_team match (for disambiguation when multiple players share a name)
    3. Report unmatched for manual review
    """
    year_rosters = rosters[rosters["year"] == year].copy()
    # Strip leading * from player names (added by scrape_prev_active.py for
    # previously active players like waived/traded/released)
    year_rosters["player_name"] = year_rosters["player_name"].str.lstrip("*").str.strip()
    year_rosters["player_name_clean"] = year_rosters["player_name"]

    # Separate hitters and pitchers in roster
    roster_hitters = year_rosters[year_rosters["position"] != "P"]
    roster_pitchers = year_rosters[year_rosters["position"] == "P"]

    stat_hitters = stats[~stats["is_pitcher"]].copy()
    stat_pitchers = stats[stats["is_pitcher"]].copy()

    matched_h = _match_group(stat_hitters, roster_hitters, "hitters")
    matched_p = _match_group(stat_pitchers, roster_pitchers, "pitchers")

    return pd.concat([matched_h, matched_p], ignore_index=True)


def _match_group(
    stats_df: pd.DataFrame, roster_df: pd.DataFrame, label: str
) -> pd.DataFrame:
    """Match stats to roster for one group (hitters or pitchers)."""
    # Try exact name match first
    merged = stats_df.merge(
        roster_df[["player_name", "team", "salary", "contract_year",
                    "status", "position", "mlb_team", "eligibility"]].rename(
            columns={"team": "fantasy_team", "mlb_team": "roster_mlb_team"}
        ),
        on="player_name",
        how="inner",
    )

    matched_names = set(merged["player_name"].unique())
    roster_names = set(roster_df["player_name"].unique())
    unmatched_roster = roster_names - matched_names

    if unmatched_roster:
        # Try matching unmatched roster players by:
        # 1. Known roster-side name fixes
        # 2. Normalized string comparison (strip punctuation, case-insensitive)
        # 3. Jr./Sr. suffix matching
        stats_name_map = {n.lower().replace(".", "").replace("-", " "): n
                          for n in stats_df["player_name"].unique()}
        # Also index by name without Jr./Sr. suffix
        for fg_name in stats_df["player_name"].unique():
            base = fg_name.replace(" Jr.", "").replace(" Sr.", "").replace(" II", "").replace(" III", "")
            key = base.lower().replace(".", "").replace("-", " ")
            if key not in stats_name_map:
                stats_name_map[key] = fg_name

        for roster_name in sorted(unmatched_roster):
            # Try known roster-side fix first
            lookup_name = ROSTER_NAME_FIXES.get(roster_name, roster_name)
            norm = lookup_name.lower().replace(".", "").replace("-", " ")
            if norm in stats_name_map:
                fg_name = stats_name_map[norm]
                # Get the stats row and roster row
                s_rows = stats_df[stats_df["player_name"] == fg_name]
                r_rows = roster_df[roster_df["player_name"] == roster_name]
                if not s_rows.empty and not r_rows.empty:
                    for _, r_row in r_rows.iterrows():
                        for _, s_row in s_rows.iterrows():
                            row = s_row.to_dict()
                            row["fantasy_team"] = r_row["team"]
                            row["salary"] = r_row["salary"]
                            row["contract_year"] = r_row["contract_year"]
                            row["status"] = r_row["status"]
                            row["position"] = r_row["position"]
                            row["roster_mlb_team"] = r_row["mlb_team"]
                            row["eligibility"] = r_row.get("eligibility")
                            merged = pd.concat(
                                [merged, pd.DataFrame([row])], ignore_index=True
                            )
                            matched_names.add(roster_name)

    unmatched_final = roster_names - matched_names
    n_matched = len(matched_names)
    n_total = len(roster_names)
    print(f"  {label}: {n_matched}/{n_total} roster players matched to FanGraphs stats")
    if unmatched_final and len(unmatched_final) <= 15:
        print(f"    Unmatched: {', '.join(sorted(unmatched_final))}")
    elif unmatched_final:
        print(f"    {len(unmatched_final)} unmatched (showing first 10):")
        print(f"    {', '.join(sorted(unmatched_final)[:10])}")

    return merged


def get_all_player_stats():
    """Main function: fetch stats for all years and match to rosters."""
    rosters = pd.read_csv("data/historical_rosters.csv")
    print(f"Loaded {len(rosters)} roster rows")

    all_matched = []

    for year in YEARS:
        print(f"\n=== {year} ===")
        bat = fetch_batting_stats(year)
        pit = fetch_pitching_stats(year)
        stats = pd.concat([bat, pit], ignore_index=True)
        print(f"  FanGraphs: {len(bat)} hitters, {len(pit)} pitchers")

        matched = match_to_rosters(stats, rosters, year)
        all_matched.append(matched)

    df = pd.concat(all_matched, ignore_index=True)

    # Output columns
    output_cols = [
        "year", "fantasy_team", "player_name", "fg_id", "mlb_team",
        "position", "salary", "contract_year", "status", "eligibility",
        "G", "AB", "PA", "R", "HR", "RBI", "SB", "AVG",
        "IP", "W", "SV", "ERA", "WHIP", "SO", "is_pitcher",
    ]
    output_cols = [c for c in output_cols if c in df.columns]
    df = df[output_cols]

    output_path = "data/player_stats.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} rows to {output_path}")

    for year in sorted(df["year"].unique()):
        ydf = df[df["year"] == year]
        n_h = (~ydf["is_pitcher"]).sum()
        n_p = ydf["is_pitcher"].sum()
        n_teams = ydf["fantasy_team"].nunique()
        print(f"  {year}: {n_teams} teams, {n_h} hitters, {n_p} pitchers")

    return df


if __name__ == "__main__":
    get_all_player_stats()

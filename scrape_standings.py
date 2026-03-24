"""
Scrape historical standings from OnRoto for the Moonlight Graham league.
Produces a CSV with raw stats and standings points for each team/year.

Note: The league changed scoring categories between 2018 and 2019:
  2015-2018: 8 categories (HR, RBI, SB, AVG, W, SV, ERA, WHIP)
  2019-2025: 10 categories (R, HR, RBI, SB, AVG, W, SV, ERA, WHIP, SO)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

from onroto_auth import login, BASE_URL, LEAGUE

TEAM_IDX = "0"
YEARS = range(2015, 2026)

# All possible categories across both eras
ALL_CATS = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]

# Category names as they appear in the per-category table headers
CAT_HEADER_MAP = {
    "RUNS": "R",
    "HOME RUNS": "HR",
    "RBIS": "RBI",
    "STOLEN BASES": "SB",
    "AVERAGE": "AVG",
    "WINS": "W",
    "SAVES": "SV",
    "ERA": "ERA",
    "(W + H) / IP": "WHIP",
    "STRIKE OUTS": "SO",
}


def fetch_standings_page(session: requests.Session, session_id: str, year: int) -> str:
    """Fetch the standings HTML for a given year."""
    url = (
        f"{BASE_URL}/baseball/webnew/display_stand.pl?"
        f"{LEAGUE}+{TEAM_IDX}+{year}&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def parse_summary_table(soup: BeautifulSoup) -> tuple[list[str], dict[str, dict]]:
    """
    Parse the main summary standings table.
    Returns (list of category names in this year's table,
             {team_name: {cat_pts: value, ..., total_pts: value}})
    """
    teams = {}
    year_cats = []
    for table in soup.find_all("table"):
        ths = table.find_all("th")
        headers = [th.get_text(strip=True) for th in ths]
        if "Team Name" not in headers or "TOTAL" not in headers:
            continue
        if len(headers) > 15:
            continue

        # Extract the category columns dynamically from headers
        # Headers are: Team Name, <cats...>, TOTAL, +/-
        total_idx = headers.index("TOTAL")
        year_cats = headers[1:total_idx]  # Everything between Team Name and TOTAL

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells or len(cells) < len(year_cats) + 2:
                continue
            team_name = cells[0].get_text(strip=True)
            if not team_name:
                continue
            team_data = {}
            for i, cat in enumerate(year_cats):
                team_data[f"{cat}_pts"] = float(cells[i + 1].get_text(strip=True))
            team_data["total_pts"] = float(cells[total_idx].get_text(strip=True))
            teams[team_name] = team_data
        if teams:
            break
    return year_cats, teams


def parse_category_tables(soup: BeautifulSoup) -> dict[str, dict]:
    """
    Parse the per-category detail tables to extract raw stat values.
    """
    teams: dict[str, dict] = {}

    for table in soup.find_all("table"):
        ths = table.find_all("th")
        if not ths:
            continue
        first_th = ths[0].get_text(strip=True)
        if first_th not in CAT_HEADER_MAP:
            continue
        if len(ths) > 8:
            continue

        cat_key = CAT_HEADER_MAP[first_th]

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            # Cells come in groups of 5: Team, Year, Wk, PTS, +/-
            i = 0
            while i + 4 < len(cells):
                team_name = cells[i].get_text(strip=True)
                raw_str = cells[i + 1].get_text(strip=True)
                i += 5

                if not team_name or not raw_str:
                    continue

                try:
                    if cat_key in ("AVG", "ERA", "WHIP"):
                        raw_value = float(raw_str)
                    else:
                        raw_value = int(raw_str)
                except ValueError:
                    continue

                if team_name not in teams:
                    teams[team_name] = {}
                teams[team_name][cat_key] = raw_value

    return teams


def scrape_all_years():
    """Main scraping function."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    all_records = []

    for year in YEARS:
        print(f"Fetching {year} standings...")
        html = fetch_standings_page(session, session_id, year)
        soup = BeautifulSoup(html, "lxml")

        year_cats, points_data = parse_summary_table(soup)
        raw_data = parse_category_tables(soup)

        if not points_data:
            print(f"  WARNING: No summary table found for {year}")
            continue

        if not raw_data:
            print(f"  WARNING: No category tables found for {year}")

        print(f"  Categories: {year_cats}")

        for team_name, pts in points_data.items():
            record = {"year": year, "team": team_name}
            raw = raw_data.get(team_name, {})
            for cat in ALL_CATS:
                record[cat] = raw.get(cat)
                record[f"{cat}_pts"] = pts.get(f"{cat}_pts")
            record["total_pts"] = pts.get("total_pts")
            all_records.append(record)

        n_teams = len(points_data)
        n_raw = len(raw_data)
        print(f"  {n_teams} teams, {n_raw} with raw stats")
        time.sleep(0.5)

    df = pd.DataFrame(all_records)

    # Reorder columns
    cols = ["year", "team"]
    for cat in ALL_CATS:
        cols.extend([cat, f"{cat}_pts"])
    cols.append("total_pts")
    df = df[cols]

    output_path = "/Users/jacobdennen/baseball-models/data/historical_standings.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} rows to {output_path}")
    print("\n" + df.to_string())
    return df


if __name__ == "__main__":
    scrape_all_years()

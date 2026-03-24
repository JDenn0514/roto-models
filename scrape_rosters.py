"""
Scrape historical roster data from OnRoto for the Moonlight Graham league.

Fetches roster pages for each year (2015-2025) and produces a CSV with
player-level data including team, position, contract, salary, and status.

HTML structure: each page has all teams' rosters in sequence. Teams are
identified by <p class="team_NNNN"> tags, followed by Active and Reserved
player tables.
"""

import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from onroto_auth import login, BASE_URL, LEAGUE

YEARS = range(2015, 2026)
OUTPUT_PATH = "/Users/jacobdennen/baseball-models/data/historical_rosters.csv"

# Regex to extract player ID from profile link URL
# e.g. "...display_player_profile.pl?MoonGrahm+0+7014&session_id=..."
PLAYER_ID_RE = re.compile(r"\+(\d+)&")

# Regex to strip annotations like "(Off DL )", "(Non Elig Pos)" from link text
ANNOTATION_RE = re.compile(r"\s*\((?:Off DL|Non Elig Pos|DL|Farm|Res)\s*\)\s*$")


def fetch_roster_page(session: requests.Session, session_id: str, year: int) -> str:
    """Fetch the all-teams roster HTML for a given year."""
    url = (
        f"{BASE_URL}/baseball/webnew/display_roster.pl?"
        f"{LEAGUE}+0+all+{year}&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def parse_player_name_and_id(name_cell: Tag) -> tuple[str | None, str | None]:
    """
    Extract player name and OnRoto player ID from the name <td> cell.

    The first <a> in the cell links to the player profile and contains the
    player name. The link text may include trailing whitespace, a leading '#',
    and/or annotations like "(Off DL )" or "(Non Elig Pos)" that need to be
    stripped.

    Returns (player_name, player_id) or (None, None) if no link found.
    """
    link = name_cell.find("a", href=True)
    if link is None:
        # Fallback: use cell text directly
        raw = name_cell.get_text(strip=True)
        if raw:
            return raw.lstrip("#").strip(), None
        return None, None

    href = link["href"]
    raw_name = link.get_text()

    # Strip annotations that appear inside the link text
    clean_name = ANNOTATION_RE.sub("", raw_name)
    # Strip leading '#' and whitespace
    clean_name = clean_name.lstrip("#").strip()

    # Extract player ID from URL
    player_id = None
    m = PLAYER_ID_RE.search(href)
    if m:
        player_id = m.group(1)

    return clean_name if clean_name else None, player_id


def parse_player_table(table: Tag) -> list[dict]:
    """
    Parse a player table (Active or Reserved) and return a list of player dicts.

    Each player row has 14 cells:
      [0] Pos, [1] Name (with link), [2] MLB team, [3] Contract year,
      [4] Salary, [5] Status, [6] Eligibility, [7-13] Games by position
    """
    players = []
    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 7:
            # Header rows or sub-header rows use <th>, skip any short rows
            continue

        position = cells[0].get_text(strip=True)
        player_name, player_id = parse_player_name_and_id(cells[1])

        if not player_name:
            continue

        mlb_team = cells[2].get_text(strip=True)
        contract_year = cells[3].get_text(strip=True)

        # Salary: parse as int, handle empty/missing
        sal_text = cells[4].get_text(strip=True)
        try:
            salary = int(sal_text)
        except (ValueError, TypeError):
            salary = 0

        status = cells[5].get_text(strip=True)
        eligibility = cells[6].get_text(strip=True)

        players.append({
            "player_name": player_name,
            "player_id": player_id,
            "mlb_team": mlb_team,
            "position": position,
            "contract_year": contract_year,
            "salary": salary,
            "status": status,
            "eligibility": eligibility,
        })

    return players


def find_team_tables(team_p: Tag) -> list[Tag]:
    """
    Given a team's <p> tag, find its Active and Reserved player tables.

    The tables follow the <p> tag as siblings. We look for <table> tags
    whose class contains 'Active_table' or 'Reserved_table'.
    """
    tables = []
    sibling = team_p.next_sibling

    while sibling is not None:
        if isinstance(sibling, Tag):
            if sibling.name == "p":
                # Hit the next team's <p> tag — stop
                break
            if sibling.name == "table":
                classes = " ".join(sibling.get("class", []))
                if "Active_table" in classes or "Reserved_table" in classes:
                    tables.append(sibling)
        sibling = sibling.next_sibling

    return tables


def extract_team_name(team_p: Tag) -> str:
    """Extract the team name from the team <p> tag's <b> element."""
    b_tag = team_p.find("b")
    if b_tag:
        return b_tag.get_text(strip=True)
    # Fallback: try <font> > <b>
    font_tag = team_p.find("font")
    if font_tag:
        b_tag = font_tag.find("b")
        if b_tag:
            return b_tag.get_text(strip=True)
    # Last resort: use first text chunk
    return team_p.get_text(strip=True).split(",")[0].strip()


def parse_roster_page(html: str, year: int) -> list[dict]:
    """
    Parse a full roster page and return a list of player records for all teams.
    """
    soup = BeautifulSoup(html, "lxml")
    records = []

    # Find all team <p> tags — they have class starting with "team_"
    team_ps = soup.find_all("p", class_=re.compile(r"^team_"))

    if not team_ps:
        print(f"  WARNING: No team blocks found for {year}")
        return records

    for team_p in team_ps:
        team_name = extract_team_name(team_p)
        tables = find_team_tables(team_p)

        if not tables:
            print(f"  WARNING: No player tables found for team '{team_name}' in {year}")
            continue

        team_players = []
        for table in tables:
            players = parse_player_table(table)
            team_players.extend(players)

        for player in team_players:
            record = {
                "year": year,
                "team": team_name,
                **player,
            }
            records.append(record)

    return records


def scrape_all_years():
    """Main scraping function."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    all_records = []

    for year in YEARS:
        print(f"\nFetching {year} rosters...")
        html = fetch_roster_page(session, session_id, year)
        records = parse_roster_page(html, year)

        # Count teams and players
        teams_in_year = set(r["team"] for r in records)
        n_teams = len(teams_in_year)
        n_players = len(records)
        print(f"  {n_teams} teams, {n_players} players")

        all_records.extend(records)
        time.sleep(0.5)

    if not all_records:
        print("\nERROR: No data scraped.")
        return None

    df = pd.DataFrame(all_records)

    # Reorder columns to match the desired schema
    columns = [
        "year", "team", "player_name", "player_id", "mlb_team",
        "position", "contract_year", "salary", "status", "eligibility",
    ]
    df = df[columns]

    # Validation: print team counts per year and flag anomalies
    print("\n--- Validation ---")
    year_team_counts = df.groupby("year")["team"].nunique()
    for yr, count in year_team_counts.items():
        flag = ""
        if yr in (2016, 2017) and count != 11:
            flag = f"  *** EXPECTED 11 TEAMS (got {count})"
        elif yr not in (2016, 2017) and count != 10:
            flag = f"  *** EXPECTED 10 TEAMS (got {count})"
        print(f"  {yr}: {count} teams, {len(df[df['year'] == yr])} players{flag}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} rows to {OUTPUT_PATH}")

    return df


if __name__ == "__main__":
    scrape_all_years()

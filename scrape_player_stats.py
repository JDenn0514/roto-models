"""
Scrape individual player stats from OnRoto team stats pages.

For each team/year, fetches the display_team_stats.pl page and extracts
individual player stat lines (active hitters and active pitchers only).

Output: data/player_stats.csv
"""

import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from onroto_auth import BASE_URL, LEAGUE, login

TEAM_IDX = "0"
YEARS = [2019, 2021, 2022, 2023, 2024, 2025]  # skip 2020 (COVID), skip pre-2019 (8-cat)
MAX_SORT = 12  # SORT_0 through SORT_11

# Column names we expect in each section (2019+ layout)
HITTER_STAT_COLS = ["G", "AB", "HR", "RBI", "SB", "AVG", "R"]
PITCHER_STAT_COLS = ["G", "IP", "W", "SV", "ERA", "WHIP", "SO"]


def fetch_team_stats_page(
    session: requests.Session, session_id: str, sort_idx: int, year: int
) -> str:
    """Fetch team stats HTML for a given SORT index and year."""
    url = (
        f"{BASE_URL}/baseball/webnew/display_team_stats.pl?"
        f"{LEAGUE}+{TEAM_IDX}+SORT_{sort_idx}+{year}&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def parse_team_name(soup: BeautifulSoup) -> str | None:
    """Extract the team name from the page."""
    for tag in soup.find_all(["b", "strong", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if "owned by" in text.lower():
            name = re.split(r"\s*owned by", text, flags=re.IGNORECASE)[0].strip()
            name = re.sub(r"\s*\(.*$", "", name).strip()
            if name:
                return name

    for tag in soup.find_all(string=re.compile(r"owned by", re.IGNORECASE)):
        parent = tag.parent
        if parent:
            text = parent.get_text(strip=True)
            name = re.split(r"\s*owned by", text, flags=re.IGNORECASE)[0].strip()
            name = re.sub(r"\s*\d{4}\s*(Final|Current)\s*Stats.*$", "", name).strip()
            name = re.sub(r"\s*\(.*$", "", name).strip()
            if name:
                return name

    return None


def _extract_accumulated(cell) -> str:
    """Extract the accumulated (first) value from a cell.

    Cells may contain "accumulated&nbsp;current_week" — we want only the
    accumulated portion (the number before &nbsp; or <br>).
    """
    raw = cell.decode_contents()
    raw = re.sub(r"&nbsp;|<br\s*/?>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)  # strip remaining HTML tags
    parts = [p.strip() for p in raw.split("\n") if p.strip()]
    return parts[0] if parts else ""


def _find_stat_sections(soup: BeautifulSoup) -> list[dict]:
    """Find all stat table sections (hitter and pitcher) by locating header rows.

    Returns a list of dicts:
        {
            "type": "hitter" | "pitcher",
            "header_tr": <tr element>,
            "col_map": {stat_name: column_index_in_header},
            "stat_cols": [ordered list of stat column names found],
        }
    """
    sections = []
    for tr in soup.find_all("tr"):
        ths = tr.find_all("th")
        if not ths:
            continue
        headers = [th.get_text(strip=True) for th in ths]

        if "AB" in headers and "HR" in headers:
            # Hitter section
            col_map = {}
            for col in HITTER_STAT_COLS:
                if col in headers:
                    col_map[col] = headers.index(col)
            sections.append({
                "type": "hitter",
                "header_tr": tr,
                "col_map": col_map,
                "stat_cols": [c for c in HITTER_STAT_COLS if c in col_map],
            })
        elif "IP" in headers and "W" in headers:
            # Pitcher section
            col_map = {}
            for col in PITCHER_STAT_COLS:
                if col in headers:
                    col_map[col] = headers.index(col)
            sections.append({
                "type": "pitcher",
                "header_tr": tr,
                "col_map": col_map,
                "stat_cols": [c for c in PITCHER_STAT_COLS if c in col_map],
            })

    return sections


def _parse_player_name_and_id(cell) -> tuple[str, str | None]:
    """Extract player name and optional player_id from a table cell.

    The player name is usually in an <a> tag. The player_id may be in the
    link URL as a query parameter. Names may have a leading '#' (indicating
    the player was dropped/released) which we strip.
    """
    link = cell.find("a")
    if link:
        name = link.get_text(strip=True)
        href = link.get("href", "")
        # Try to extract player_id from URL
        pid_match = re.search(r"player_id=(\d+)", href)
        pid = pid_match.group(1) if pid_match else None
        # Strip leading '#' (marks dropped/released players)
        name = name.lstrip("#").strip()
        return name, pid
    # Fallback: just get cell text
    name = cell.get_text(strip=True).lstrip("#").strip()
    return name, None


def _parse_player_rows(
    soup: BeautifulSoup, section: dict
) -> list[dict]:
    """Parse individual player rows from a stat section.

    Starts after the header row and stops at the TOTAL row.
    Skips the Reserved sections (only processes Active).
    """
    all_trs = soup.find_all("tr")
    tr_positions = {id(tr): i for i, tr in enumerate(all_trs)}
    header_pos = tr_positions.get(id(section["header_tr"]), -1)
    if header_pos < 0:
        return []

    col_map = section["col_map"]
    players = []

    for tr in all_trs[header_pos + 1:]:
        cells = tr.find_all("td")
        if not cells:
            continue

        first_text = cells[0].get_text(strip=True)

        # Stop at TOTAL row (marks end of active section)
        if first_text.startswith("TOTAL"):
            break

        # Skip rows that look like section headers or empty rows
        if len(cells) < 4:
            continue

        # The Name column is typically the first or second cell.
        # Look for the cell containing an <a> tag (player link).
        name_cell_idx = None
        for ci, cell in enumerate(cells):
            if cell.find("a"):
                name_cell_idx = ci
                break

        if name_cell_idx is None:
            continue

        player_name, player_id = _parse_player_name_and_id(cells[name_cell_idx])
        if not player_name or player_name == "TOTAL:":
            continue

        # Find Pos and Tm columns relative to the header
        # The header has column names; player rows have corresponding data cells.
        # However, player rows may have a different number of cells than headers
        # because of row structure differences. Use the header col_map indices directly.
        row = {"player_name": player_name, "player_id": player_id}

        # Extract position (Pos column)
        # Pos is typically right after or before the name column
        # Use header index if available
        header_ths = section["header_tr"].find_all("th")
        header_names = [th.get_text(strip=True) for th in header_ths]

        if "Pos" in header_names:
            pos_idx = header_names.index("Pos")
            if pos_idx < len(cells):
                row["position"] = cells[pos_idx].get_text(strip=True)

        if "Tm" in header_names:
            tm_idx = header_names.index("Tm")
            if tm_idx < len(cells):
                row["mlb_team"] = cells[tm_idx].get_text(strip=True)

        # Extract stat values using header column indices
        for stat, col_idx in col_map.items():
            if col_idx < len(cells):
                val_str = _extract_accumulated(cells[col_idx])
                try:
                    row[stat] = float(val_str)
                except (ValueError, TypeError):
                    row[stat] = None

        players.append(row)

    return players


def parse_players_from_page(soup: BeautifulSoup) -> list[dict]:
    """Parse all active player stats from a team stats page.

    Returns list of player dicts, each tagged with is_pitcher.
    """
    sections = _find_stat_sections(soup)
    all_players = []

    # We only want the first hitter section and first pitcher section
    # (the "Active" sections — Reserved sections come after TOTAL)
    seen_types = set()
    for section in sections:
        if section["type"] in seen_types:
            continue  # skip Reserved sections (second occurrence)
        seen_types.add(section["type"])

        players = _parse_player_rows(soup, section)
        for p in players:
            p["is_pitcher"] = section["type"] == "pitcher"
        all_players.extend(players)

    return all_players


def scrape_player_stats():
    """Main scraping function."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    all_records = []

    for year in YEARS:
        print(f"\nFetching {year} player stats...")
        year_records = []
        seen_teams = set()

        for sort_idx in range(MAX_SORT):
            try:
                html = fetch_team_stats_page(session, session_id, sort_idx, year)
            except requests.HTTPError:
                continue

            soup = BeautifulSoup(html, "lxml")
            team_name = parse_team_name(soup)

            if not team_name:
                break

            # Skip duplicate team names (phantom SORT entries)
            if team_name in seen_teams:
                print(f"  SKIP: {team_name} (SORT_{sort_idx}) duplicate")
                continue
            seen_teams.add(team_name)

            players = parse_players_from_page(soup)

            for p in players:
                p["year"] = year
                p["fantasy_team"] = team_name

            year_records.extend(players)
            print(f"  {team_name}: {len(players)} players")
            time.sleep(0.3)

        all_records.extend(year_records)
        n_hitters = sum(1 for r in year_records if not r.get("is_pitcher"))
        n_pitchers = sum(1 for r in year_records if r.get("is_pitcher"))
        print(f"  {year} total: {n_hitters} hitters, {n_pitchers} pitchers")

    # Build DataFrame with canonical column order
    df = pd.DataFrame(all_records)

    # Ensure all expected columns exist
    hitter_cols = ["AB", "R", "HR", "RBI", "SB", "AVG"]
    pitcher_cols = ["IP", "W", "SV", "ERA", "WHIP", "SO"]
    for col in hitter_cols + pitcher_cols + ["G"]:
        if col not in df.columns:
            df[col] = None

    # Reorder columns
    output_cols = [
        "year", "fantasy_team", "player_name", "player_id", "mlb_team",
        "position", "G", "AB", "R", "HR", "RBI", "SB", "AVG",
        "IP", "W", "SV", "ERA", "WHIP", "SO", "is_pitcher",
    ]
    # Only include columns that exist
    output_cols = [c for c in output_cols if c in df.columns]
    df = df[output_cols]

    output_path = "data/player_stats.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} rows to {output_path}")

    # Summary
    for year in sorted(df["year"].unique()):
        ydf = df[df["year"] == year]
        n_h = (~ydf["is_pitcher"]).sum()
        n_p = ydf["is_pitcher"].sum()
        n_teams = ydf["fantasy_team"].nunique()
        print(f"  {year}: {n_teams} teams, {n_h} hitters, {n_p} pitchers")

    return df


if __name__ == "__main__":
    scrape_player_stats()

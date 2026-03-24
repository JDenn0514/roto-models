"""
Scrape previously active players from OnRoto stats pages.

These are players who were on a fantasy team's active roster during the season
but were later traded (trd), waived (wai), released (rel), or moved to reserve
(res). They appear on the stats page below a "stats of previously active
hitters/pitchers ----->" divider.

The roster scraper (scrape_rosters.py) only captures the end-of-season roster
snapshot, missing these players. This script supplements historical_rosters.csv
with the missing entries.

Output: updates data/historical_rosters.csv in-place (adds new rows).
"""

import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from onroto_auth import BASE_URL, LEAGUE, login

TEAM_IDX = "0"
YEARS = range(2015, 2026)
MAX_SORT = 12

# Regex for player ID extraction and name cleaning (same as scrape_rosters.py)
PLAYER_ID_RE = re.compile(r"\+(\d+)&")
ANNOTATION_RE = re.compile(r"\s*\((?:Off DL|Non Elig Pos|DL|Farm|Res)\s*\)\s*$")

ROSTER_PATH = "data/historical_rosters.csv"


def fetch_team_stats_page(
    session: requests.Session, session_id: str, sort_idx: int, year: int
) -> str:
    url = (
        f"{BASE_URL}/baseball/webnew/display_team_stats.pl?"
        f"{LEAGUE}+{TEAM_IDX}+SORT_{sort_idx}+{year}&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def parse_team_name(soup: BeautifulSoup) -> str | None:
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


def _parse_name_and_id(cell: Tag) -> tuple[str | None, str | None]:
    """Extract player name and ID from a table cell."""
    link = cell.find("a", href=True)
    if link is None:
        raw = cell.get_text(strip=True)
        if raw:
            return raw.lstrip("#").strip(), None
        return None, None

    href = link["href"]
    raw_name = link.get_text()
    clean_name = ANNOTATION_RE.sub("", raw_name)
    clean_name = clean_name.lstrip("#").strip()

    player_id = None
    m = PLAYER_ID_RE.search(href)
    if m:
        player_id = m.group(1)

    return clean_name if clean_name else None, player_id


def parse_previously_active(soup: BeautifulSoup) -> list[dict]:
    """Find 'previously active' dividers and parse player rows after them.

    Returns list of player dicts with keys:
        player_name, player_id, mlb_team, position, contract_year, salary, status
    """
    players = []
    all_trs = soup.find_all("tr")

    # Find divider rows containing "previously active"
    divider_indices = []
    for i, tr in enumerate(all_trs):
        text = tr.get_text(strip=True).lower()
        if "previously active" in text:
            is_pitcher = "pitcher" in text
            divider_indices.append((i, is_pitcher))

    for div_idx, is_pitcher in divider_indices:
        # Parse rows after the divider until we hit TOTAL or another divider
        for tr in all_trs[div_idx + 1:]:
            cells = tr.find_all("td")
            if not cells:
                continue

            first_text = cells[0].get_text(strip=True)

            # Stop at TOTAL row
            if first_text.startswith("TOTAL"):
                break

            # Stop at another section divider
            row_text = tr.get_text(strip=True).lower()
            if "previously active" in row_text or "reserved" in row_text:
                break

            # Need at least: Pos, Name, Tm, Cont, Salary, Status
            if len(cells) < 6:
                continue

            position = cells[0].get_text(strip=True)
            player_name, player_id = _parse_name_and_id(cells[1])
            if not player_name:
                continue

            mlb_team = cells[2].get_text(strip=True)
            contract_year = cells[3].get_text(strip=True)

            sal_text = cells[4].get_text(strip=True)
            try:
                salary = int(sal_text)
            except (ValueError, TypeError):
                salary = 0

            status = cells[5].get_text(strip=True)

            # Eligibility: may be in cell 6 if present
            eligibility = ""
            if len(cells) > 6:
                eligibility = cells[6].get_text(strip=True)

            # Override position to "P" for pitchers (the Pos column on stats
            # page may say "P" already, but be safe)
            if is_pitcher:
                position = "P"

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


def scrape_all_prev_active():
    """Scrape previously active players for all years and merge into roster CSV."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    # Load existing roster data
    existing = pd.read_csv(ROSTER_PATH)
    print(f"Existing roster: {len(existing)} rows")

    # Build a set of (year, team, player_name) for deduplication
    existing_keys = set(
        zip(existing["year"], existing["team"], existing["player_name"])
    )

    new_records = []

    for year in YEARS:
        print(f"\n{year}:")
        seen_teams = set()
        year_new = 0

        for sort_idx in range(MAX_SORT):
            try:
                html = fetch_team_stats_page(session, session_id, sort_idx, year)
            except requests.HTTPError:
                continue

            soup = BeautifulSoup(html, "lxml")
            team_name = parse_team_name(soup)
            if not team_name:
                break

            if team_name in seen_teams:
                continue
            seen_teams.add(team_name)

            players = parse_previously_active(soup)

            added = 0
            for p in players:
                key = (year, team_name, p["player_name"])
                if key not in existing_keys:
                    record = {"year": year, "team": team_name, **p}
                    new_records.append(record)
                    existing_keys.add(key)
                    added += 1

            if added > 0:
                print(f"  {team_name}: +{added} previously active")

            time.sleep(0.3)

        year_new = sum(1 for r in new_records if r["year"] == year)
        print(f"  {year} total new: {year_new}")

    if not new_records:
        print("\nNo new players found.")
        return

    new_df = pd.DataFrame(new_records)

    # Ensure column order matches existing
    for col in existing.columns:
        if col not in new_df.columns:
            new_df[col] = None

    new_df = new_df[existing.columns]

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.to_csv(ROSTER_PATH, index=False)
    print(f"\nAdded {len(new_records)} previously active players to {ROSTER_PATH}")
    print(f"New total: {len(combined)} rows")

    # Verify Judge
    judge = combined[
        (combined["player_name"].str.contains("Judge", case=False, na=False))
        & (combined["year"] == 2024)
    ]
    if not judge.empty:
        print(f"\nVerification — Aaron Judge 2024:")
        print(judge[["year", "team", "salary", "status"]].to_string(index=False))
    else:
        print("\nWARNING: Aaron Judge still not found for 2024")


if __name__ == "__main__":
    scrape_all_prev_active()

"""
Scrape team-level AB and IP totals from OnRoto team stats pages.

For each team/year, fetches the player stats page and sums AB (hitters)
and IP (pitchers) across all players (active + reserve).

Output: data/team_totals.csv with columns: year, team, total_ab, total_ip
"""

import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from onroto_auth import BASE_URL, LEAGUE, login

TEAM_IDX = "0"  # fixed league parameter
YEARS = range(2015, 2026)
MAX_SORT = 12  # try SORT_0 through SORT_11 (covers 11-team years)


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
    # Look for the team name in header/title area
    # Typically appears in a bold or header element near the top
    for tag in soup.find_all(["b", "strong", "h2", "h3"]):
        text = tag.get_text(strip=True)
        # The team name line often contains "owned by" after it
        if "owned by" in text.lower():
            # Extract team name before "owned by"
            name = re.split(r"\s*owned by", text, flags=re.IGNORECASE)[0].strip()
            # Clean up parentheses
            name = re.sub(r"\s*\(.*$", "", name).strip()
            if name:
                return name

    # Fallback: look for text that contains "owned by" in any element
    for tag in soup.find_all(string=re.compile(r"owned by", re.IGNORECASE)):
        parent = tag.parent
        if parent:
            text = parent.get_text(strip=True)
            name = re.split(r"\s*owned by", text, flags=re.IGNORECASE)[0].strip()
            # Remove "Final Stats" suffix
            name = re.sub(r"\s*\d{4}\s*(Final|Current)\s*Stats.*$", "", name).strip()
            name = re.sub(r"\s*\(.*$", "", name).strip()
            if name:
                return name

    return None


def _extract_accumulated(cell) -> str:
    """Extract the accumulated (first) value from a TOTAL cell.

    TOTAL cells contain "accumulated&nbsp;current_week" values.
    We want only the accumulated portion.
    """
    # Get raw HTML content and split on &nbsp; or <br>
    raw = cell.decode_contents()
    # Replace HTML entities and tags that separate the two values
    raw = re.sub(r"&nbsp;|<br\s*/?>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)  # strip remaining HTML tags
    parts = [p.strip() for p in raw.split("\n") if p.strip()]
    return parts[0] if parts else ""


def parse_ab_ip(soup: BeautifulSoup) -> tuple[float, float]:
    """Extract team AB and IP from the Active section TOTAL rows.

    The page has 4 sections (Active Hitters, Reserved Hitters, Active
    Pitchers, Reserved Pitchers), each with a header row and a TOTAL row.
    Column layout varies by era:
      2015-2018 (8-cat):  hitters have AVG,HR,RBI,SB,AB; pitchers W,SV,ERA,WHIP,IP
      2019+ (10-cat):     hitters have G,AB,HR,RBI,SB,AVG,R; pitchers G,IP,W,SV,ERA,WHIP,SO

    Only Active section totals count toward standings.
    Strategy: find TH headers, determine AB/IP column index, then extract
    from the first TOTAL row in that section.
    """
    total_ab = 0.0
    total_ip = 0.0
    found_hitter_total = False
    found_pitcher_total = False

    # Collect all header rows that define stat columns
    # Each maps to either AB (hitters) or IP (pitchers)
    header_targets = []  # (header_tr_element, "ab"|"ip", column_index)

    for tr in soup.find_all("tr"):
        ths = tr.find_all("th")
        if not ths:
            continue
        headers = [th.get_text(strip=True) for th in ths]
        if "AB" in headers:
            # +1 offset: TOTAL row has "TOTAL:" in cell[0], stats start at [1]
            # Find AB position in the stat-only columns (exclude Pos, Name, Tm, Cont, Sta)
            ab_stat_idx = [h for h in headers if h not in ("Pos", "Name", "Tm", "Cont", "Sta")
                          and "Games by Position" not in h].index("AB")
            header_targets.append((tr, "ab", ab_stat_idx + 1))
        elif "IP" in headers:
            ip_stat_idx = [h for h in headers if h not in ("Pos", "Name", "Tm", "Cont", "Sta")].index("IP")
            header_targets.append((tr, "ip", ip_stat_idx + 1))

    # For each header, find the next TOTAL row in the document
    all_trs = soup.find_all("tr")
    tr_positions = {id(tr): i for i, tr in enumerate(all_trs)}

    for header_tr, stat_type, col_idx in header_targets:
        header_pos = tr_positions.get(id(header_tr), -1)
        if header_pos < 0:
            continue

        # Search forward for the first TOTAL row
        for tr in all_trs[header_pos + 1:]:
            cells = tr.find_all("td")
            if not cells:
                continue
            first_text = cells[0].get_text(strip=True)
            if first_text.startswith("TOTAL"):
                if col_idx < len(cells):
                    val_str = _extract_accumulated(cells[col_idx])
                    try:
                        val = float(val_str)
                    except (ValueError, TypeError):
                        break

                    if stat_type == "ab" and not found_hitter_total:
                        total_ab = val
                        found_hitter_total = True
                    elif stat_type == "ip" and not found_pitcher_total:
                        total_ip = val
                        found_pitcher_total = True
                break  # only take the first TOTAL after each header

    return total_ab, total_ip


def scrape_all_team_stats():
    """Main scraping function."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    all_records = []

    for year in YEARS:
        print(f"\nFetching {year} team stats...")
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

            ab, ip = parse_ab_ip(soup)

            if ab == 0 and ip == 0:
                print(f"  WARNING: {team_name} (SORT_{sort_idx}) has 0 AB and 0 IP")
                continue

            year_records.append({
                "year": year,
                "team": team_name,
                "total_ab": int(ab),
                "total_ip": round(ip, 1),
            })
            time.sleep(0.3)

        all_records.extend(year_records)
        print(f"  {len(year_records)} teams scraped")

    df = pd.DataFrame(all_records)
    output_path = "data/team_totals.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} rows to {output_path}")

    # Summary stats
    for year in sorted(df["year"].unique()):
        ydf = df[df["year"] == year]
        print(f"  {year}: {len(ydf)} teams, "
              f"mean AB={ydf['total_ab'].mean():.0f}, "
              f"mean IP={ydf['total_ip'].mean():.0f}")

    return df


if __name__ == "__main__":
    scrape_all_team_stats()

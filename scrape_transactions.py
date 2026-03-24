"""
Scrape historical transaction data from OnRoto for the Moonlight Graham league.
Produces data/historical_transactions.csv with all transactions from 2015-2025.

Each season's transactions are displayed on a single page organized into
weekly tables in reverse chronological order.
"""

import time

import pandas as pd
from bs4 import BeautifulSoup

from onroto_auth import login, BASE_URL, LEAGUE

YEARS = range(2015, 2026)
OUTPUT_PATH = "/Users/jacobdennen/baseball-models/data/historical_transactions.csv"


def fetch_transactions_page(session, session_id: str, year: int) -> str:
    """Fetch the full-season transaction page for a given year."""
    url = (
        f"{BASE_URL}/baseball/webnew/display_trans.pl?"
        f"{LEAGUE}+0+all+by_week+{year}&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def parse_transactions(html: str, year: int) -> tuple[list[dict], int]:
    """
    Parse all transaction tables from a year's transaction page.

    Transaction tables are identified by having a <td> containing "Eff. Date"
    in their header row. Each table has:
      - Row 0: "Weekly Transactions" (colspan=6)
      - Row 1: Header row with 6 <td> cells (Eff. Date, League Team, ...)
      - Row 2+: Data rows with 6 <td> cells
    """
    soup = BeautifulSoup(html, "lxml")
    records = []
    trans_table_count = 0

    for table in soup.find_all("table"):
        # Identify transaction tables: look for a <td> containing "Eff. Date"
        # Header cells use class 'white_on_grey12', not <th> tags
        header_tds = table.find_all("td", class_="white_on_grey12")
        header_texts = [td.get_text(strip=True) for td in header_tds]
        if "Eff. Date" not in header_texts:
            continue

        trans_table_count += 1

        # Parse all data rows (non-header rows with 6 <td> cells)
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) != 6:
                continue

            # Skip the header row — its cells have class 'white_on_grey12'
            first_class = cells[0].get("class", [])
            if "white_on_grey12" in first_class:
                continue

            eff_date = cells[0].get_text(strip=True)
            team = cells[1].get_text(strip=True)
            player_name = cells[2].get_text(strip=True)
            mlb_team = cells[3].get_text(strip=True)
            transaction = cells[4].get_text(strip=True)
            submitted = cells[5].get_text(strip=True)

            # Skip empty rows (shouldn't happen, but be safe)
            if not eff_date and not player_name:
                continue

            records.append({
                "year": year,
                "eff_date": eff_date,
                "team": team,
                "player_name": player_name,
                "mlb_team": mlb_team,
                "transaction": transaction,
                "submitted": submitted,
            })

    return records, trans_table_count


def scrape_all_years():
    """Main scraping function."""
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    all_records = []

    for year in YEARS:
        print(f"\nFetching {year} transactions...")
        html = fetch_transactions_page(session, session_id, year)
        records, table_count = parse_transactions(html, year)
        all_records.extend(records)
        print(f"  Tables found: {table_count}, Transactions: {len(records)}")
        time.sleep(0.5)

    df = pd.DataFrame(all_records)

    # Ensure column order
    if not df.empty:
        df = df[["year", "eff_date", "team", "player_name", "mlb_team",
                  "transaction", "submitted"]]

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} rows to {OUTPUT_PATH}")

    # Summary: transactions per year
    print("\nTransactions per year:")
    if not df.empty:
        summary = df.groupby("year").size()
        for yr, count in summary.items():
            print(f"  {yr}: {count}")
    else:
        print("  (no transactions found)")

    return df


if __name__ == "__main__":
    scrape_all_years()

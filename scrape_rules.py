"""
Scrape OnRoto league rules for the Moonlight Graham league.
Logs in, visits each rules sub-page, extracts question/answer pairs,
and saves them to a readable text file.
"""

import re
import requests
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
from pathlib import Path

BASE_URL = "https://onroto.fangraphs.com"
LEAGUE_ID = "MoonGrahm"
LOGIN_URL = f"{BASE_URL}/index.pl"
LOGIN_DATA = {
    "user": "pete@srjsteel.com",
    "pass": "ASUuoa12",
    "submit": "Login",
    "postback": "1",
}

# Correct URL path includes baseball/webnew/ and correct page keys
RULES_PAGES = [
    ("basic", "Basic Setup"),
    ("line_ups", "Lineups and Rosters"),
    ("categories", "Scoring Categories"),
    ("aux_categories", "Display (Non-Scoring) Categories"),
    ("transactions", "Transaction Rules"),
    ("trades", "Trade Rules"),
    ("free_agents", "Free Agent Rules"),
    ("waivers", "Waiver Rules"),
    ("bid_meister", "Bid Meister / Blind Bidding Rules"),
    ("misc", "Miscellaneous Rules"),
]

OUTPUT_FILE = Path("/Users/jacobdennen/baseball-models/data/league_rules.txt")


def login(session: requests.Session) -> str:
    """Establish cookies and log in. Return the session_id."""
    print("Fetching homepage to establish cookies...")
    resp = session.get(BASE_URL, allow_redirects=True)
    resp.raise_for_status()
    print(f"  Homepage status: {resp.status_code}")

    print("Logging in...")
    resp = session.post(LOGIN_URL, data=LOGIN_DATA, allow_redirects=True)
    resp.raise_for_status()
    print(f"  Login status: {resp.status_code}")
    print(f"  Final URL: {resp.url}")

    session_id = None
    match = re.search(r"session_id=([A-Za-z0-9]+)", resp.url)
    if match:
        session_id = match.group(1)
    else:
        match = re.search(r"session_id=([A-Za-z0-9]+)", resp.text)
        if match:
            session_id = match.group(1)

    if session_id:
        print(f"  Session ID: {session_id}")
    else:
        print("  WARNING: Could not extract session_id.")

    return session_id


def get_question_text(cell):
    """
    Extract the question text from a cell. The question is typically the
    direct text content before any form elements (select, input, etc.).
    May also be inside a <div> wrapper.
    """
    # Try to collect text that comes before or around the form elements
    texts = []

    # Walk through the cell's contents
    def collect_text(element):
        for child in element.children:
            if isinstance(child, NavigableString):
                t = child.strip()
                if t:
                    texts.append(t)
            elif child.name in ("b", "strong", "em", "i", "u", "span", "font", "a"):
                t = child.get_text(strip=True)
                if t:
                    texts.append(t)
            elif child.name == "br":
                pass  # skip line breaks
            elif child.name == "div":
                collect_text(child)  # recurse into divs
            elif child.name in ("select", "input", "textarea"):
                break  # stop at form elements
            elif child.name == "table":
                break  # stop at nested tables

    collect_text(cell)
    return " ".join(texts).strip()


def get_answer(cell):
    """
    Extract the current answer/value from a cell's form elements.
    Handles: <select> (selected option), <input type=text> (value),
    <input type=radio/checkbox> (checked value + label), <textarea>.
    """
    answers = []

    # Check for <select> elements
    for select in cell.find_all("select"):
        selected_opt = select.find("option", selected=True)
        if not selected_opt:
            selected_opt = select.find("option", attrs={"selected": ""})
        if selected_opt:
            val = selected_opt.get_text(strip=True)
            if val:
                answers.append(val)

    # Check for checked radio buttons and checkboxes
    for inp in cell.find_all("input"):
        input_type = inp.get("type", "text").lower()
        if input_type in ("radio", "checkbox"):
            if inp.has_attr("checked"):
                # Get the label text - it's usually the next sibling text
                label_text = ""
                for sib in inp.next_siblings:
                    if isinstance(sib, NavigableString):
                        t = sib.strip()
                        if t:
                            label_text = t
                            break
                    elif sib.name == "br":
                        break
                    elif sib.name in ("b", "strong", "em", "i", "span", "font", "label"):
                        label_text = sib.get_text(strip=True)
                        break
                if label_text:
                    answers.append(label_text)
                else:
                    answers.append(inp.get("value", "checked"))
        elif input_type == "text":
            val = inp.get("value", "")
            if val:
                answers.append(val)
        elif input_type == "number":
            val = inp.get("value", "")
            if val:
                answers.append(val)

    # Check for <textarea>
    for ta in cell.find_all("textarea"):
        val = ta.get_text(strip=True)
        if val:
            answers.append(val)

    return "; ".join(answers) if answers else ""


def extract_categories(html: str) -> list[tuple[str, str]]:
    """
    Extract scoring/display categories from a categories page.
    These pages use checkboxes in a grid layout with stats_light_grey10 class.
    Checked checkboxes indicate which categories are enabled.
    Also extracts select elements and other settings on the page.
    """
    soup = BeautifulSoup(html, "html.parser")
    pairs = []

    # Extract checked checkbox categories grouped by name prefix
    checked = soup.find_all("input", {"type": "checkbox", "checked": True})

    hit_cats = []
    pitch_cats = []

    for cb in checked:
        name = cb.get("name", "")
        value = cb.get("value", "")
        if "hit" in name.lower() and "cat" in name.lower():
            hit_cats.append(value)
        elif "pit" in name.lower() and "cat" in name.lower():
            pitch_cats.append(value)

    if hit_cats:
        pairs.append(("Hitter scoring categories", ", ".join(hit_cats)))
    if pitch_cats:
        pairs.append(("Pitcher scoring categories", ", ".join(pitch_cats)))

    # Also extract any select elements and other settings on the page
    all_settings_classes = ["stats_dark_grey", "stats_light_grey", "stats_light_grey10", "stats_dark_grey10"]

    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 1:
            continue

        cell = cells[0]
        cell_class = cell.get("class", [])
        if not any(c in cell_class for c in all_settings_classes):
            continue

        # Look for select elements in this cell
        selects = cell.find_all("select")
        if not selects:
            continue

        question = get_question_text(cell)
        answer = get_answer(cell)
        question = re.sub(r"\s+", " ", question).strip()

        if question and answer:
            pairs.append((question, answer))

    return pairs


def extract_rules(html: str, is_categories_page: bool = False) -> list[tuple[str, str]]:
    """
    Parse a rules page and return list of (question, answer) pairs.
    Each row in the settings table has a single <td> cell containing
    both the question text and form elements with the answer.
    """
    if is_categories_page:
        return extract_categories(html)

    soup = BeautifulSoup(html, "html.parser")
    pairs = []

    # Supported cell classes across different page layouts
    all_settings_classes = ["stats_dark_grey", "stats_light_grey", "stats_light_grey10", "stats_dark_grey10"]

    # Find all table rows with a single td that has a settings class
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) != 1:
            continue

        cell = cells[0]
        cell_class = cell.get("class", [])
        if not any(c in cell_class for c in all_settings_classes):
            continue

        # Skip rows that are entirely hidden (display:none on the cell itself)
        style = cell.get("style", "")
        if "display:none" in style.replace(" ", "").lower() or "display: none" in style.lower():
            continue

        question = get_question_text(cell)
        answer = get_answer(cell)

        # Clean up question text
        question = re.sub(r"\s+", " ", question).strip()

        if question and answer:
            pairs.append((question, answer))

    # Also handle multi-cell rows (some pages use 2-column layout)
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 2:
            continue

        first_cell = cells[0]
        first_class = first_cell.get("class", [])
        if not any(c in first_class for c in all_settings_classes):
            continue

        question = first_cell.get_text(strip=True)
        answer_parts = []
        for cell in cells[1:]:
            a = get_answer(cell)
            if a:
                answer_parts.append(a)

        answer = "; ".join(answer_parts)
        question = re.sub(r"\s+", " ", question).strip()

        if question and answer:
            # Avoid duplicates
            if not any(q == question for q, _ in pairs):
                pairs.append((question, answer))

    return pairs


def scrape_all_rules(session: requests.Session, session_id: str | None) -> dict[str, list[tuple[str, str]]]:
    """Fetch each rules page and extract the settings."""
    all_rules = {}

    for page_key, page_title in RULES_PAGES:
        url = f"{BASE_URL}/baseball/webnew/display_specs.pl?{LEAGUE_ID}+0+{page_key}&session_id={session_id}"

        print(f"\nFetching: {page_title} ({page_key})...")
        print(f"  URL: {url}")

        try:
            resp = session.get(url, allow_redirects=True)
            resp.raise_for_status()
            print(f"  Status: {resp.status_code}, Length: {len(resp.text)} chars")

            is_cats = page_key in ("categories", "aux_categories")
            pairs = extract_rules(resp.text, is_categories_page=is_cats)
            print(f"  Extracted {len(pairs)} settings")

            if pairs:
                for q, a in pairs[:3]:
                    print(f"    Sample: {q[:60]:<60} => {a[:60]}")
                if len(pairs) > 3:
                    print(f"    ... and {len(pairs) - 3} more")

            all_rules[page_title] = pairs

        except requests.RequestException as e:
            print(f"  ERROR: {e}")
            all_rules[page_title] = []

    return all_rules


def save_rules(all_rules: dict[str, list[tuple[str, str]]], path: Path):
    """Write rules to a readable text file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("MOONLIGHT GRAHAM LEAGUE RULES\n")
        f.write(f"Scraped from OnRoto (FanGraphs) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        total_settings = 0
        for page_title, pairs in all_rules.items():
            f.write("-" * 80 + "\n")
            f.write(f"  {page_title.upper()}\n")
            f.write("-" * 80 + "\n\n")

            if not pairs:
                f.write("  (No settings found on this page)\n\n")
                continue

            for question, answer in pairs:
                # Wrap long questions nicely
                f.write(f"  Q: {question}\n")
                f.write(f"  A: {answer}\n")
                f.write("\n")
                total_settings += 1

            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write(f"Total settings extracted: {total_settings}\n")
        f.write("=" * 80 + "\n")

    print(f"\nSaved {total_settings} settings to {path}")


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    })

    session_id = login(session)
    all_rules = scrape_all_rules(session, session_id)
    save_rules(all_rules, OUTPUT_FILE)

    # Print the full output file
    print("\n" + "=" * 80)
    print("FULL OUTPUT FILE CONTENTS:")
    print("=" * 80)
    with open(OUTPUT_FILE) as f:
        print(f.read())


if __name__ == "__main__":
    main()

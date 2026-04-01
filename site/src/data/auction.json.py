#!/usr/bin/env python3
"""Data loader: extract the DATA object from the auction analysis HTML report.

Observable Framework runs this loader from the project root (site/).
The HTML report is at ../reports/auction_analysis_2026_d3.html.

When the HTML report is regenerated, re-running `npm run build` picks up fresh data
automatically (Observable invalidates the cache when this file changes).
"""
import sys
import json
from pathlib import Path

html_path = Path("../reports/auction_analysis_2026_d3.html")
if not html_path.exists():
    print(f"ERROR: HTML report not found at {html_path.absolute()}", file=sys.stderr)
    sys.exit(1)

html = html_path.read_text(encoding="utf-8")

# Use Python's JSON decoder to robustly extract the DATA object.
# The marker "const DATA = " precedes a JSON object literal in the <script> block.
marker = "const DATA = "
try:
    start = html.index(marker) + len(marker)
except ValueError:
    print("ERROR: Could not find 'const DATA = ' in HTML report", file=sys.stderr)
    sys.exit(1)

decoder = json.JSONDecoder()
try:
    data, _ = decoder.raw_decode(html, start)
except json.JSONDecodeError as e:
    print(f"ERROR: Failed to parse DATA JSON: {e}", file=sys.stderr)
    sys.exit(1)

# Write compact JSON to stdout (Observable reads this as auction.json)
json.dump(data, sys.stdout, ensure_ascii=False, separators=(",", ":"))

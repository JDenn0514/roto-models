#!/usr/bin/env python3
"""Data loader: historical league standings for the SGP calibration report.
Observable Framework runs loaders from the site/ directory.
"""
import sys
import json
import csv
from pathlib import Path

CATS = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]
PRIMARY_YEARS = {2019, 2021, 2022, 2023, 2024, 2025}

rows = []
with open(Path("../data/historical_standings.csv"), newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        yr = int(row["year"])
        if yr == 2020:
            continue  # COVID-shortened season, excluded from calibration

        record = {
            "year": yr,
            "team": row["team"],
            "era": "primary" if yr in PRIMARY_YEARS else "supplemental",
        }

        for cat in CATS:
            for suffix in ("", "_pts"):
                key = cat + suffix
                raw = row.get(key, "").strip()
                if raw and raw.lower() not in ("nan", "none", ""):
                    record[key] = round(float(raw), 5)
                else:
                    record[key] = None

        total = row.get("total_pts", "").strip()
        record["total_pts"] = (
            round(float(total), 1)
            if total and total.lower() not in ("nan", "")
            else None
        )

        rows.append(record)

json.dump(rows, sys.stdout, separators=(",", ":"), ensure_ascii=False)

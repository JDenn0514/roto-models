#!/usr/bin/env python3
"""Data loader: SGP calibration sweep results.
Observable Framework runs loaders from the site/ directory.
320 configurations tested via leave-one-year-out cross-validation.
"""
import sys
import json
import csv
from pathlib import Path
from collections import defaultdict

configs = []
with open(Path("../data/sweep_results.csv"), newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cats = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]
        c = {
            "method": row["method"],
            "supp": row["use_supplemental"] == "True",
            "decay": row["time_decay"] == "True",
            "punt": row["punt_detection"] == "True",
            "h_buf": int(float(row["replacement_hitter_buffer"])),
            "nrmse": round(float(row["sgp_cv_nrmse"]), 5),
            "rank_corr": round(float(row["rank_correlation"]), 5),
            "cat_nrmse": {
                cat: round(float(row[f"nrmse_{cat}"]), 5) for cat in cats
            },
        }
        configs.append(c)

# Aggregate per method: mean / min / max nRMSE and all values for strip plot
by_method_dict = defaultdict(list)
for c in configs:
    by_method_dict[c["method"]].append(c["nrmse"])

by_method = []
for method, nrmses in sorted(by_method_dict.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
    by_method.append(
        {
            "method": method,
            "mean": round(sum(nrmses) / len(nrmses), 5),
            "min": round(min(nrmses), 5),
            "max": round(max(nrmses), 5),
            "n": len(nrmses),
            "all": [round(v, 5) for v in sorted(nrmses)],
        }
    )

json.dump(
    {"configs": configs, "by_method": by_method},
    sys.stdout,
    separators=(",", ":"),
    ensure_ascii=False,
)

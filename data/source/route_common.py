"""Paths, CSV helpers and route selection shared by the preparation scripts."""

import csv
import hashlib
from collections import Counter
from pathlib import Path


DATA = Path(__file__).resolve().parents[1]
INTERIM = DATA / "interim/routes"
PROCESSED = DATA / "processed/routes"
TRAFFIC_SHA256 = "400e1b215682ded55d74168a8ef00d72016991d5c3f34ac8ca46eb555049b98e"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def select_top20():
    """Rank airport pairs by 2025 passengers, adding the two directions."""
    path = DATA / "raw/domestic_route_monthly.csv"
    if hashlib.sha256(path.read_bytes()).hexdigest() != TRAFFIC_SHA256:
        raise ValueError("The city-pair traffic snapshot has changed.")
    totals = Counter()
    months = set()
    keys = set()
    for row in read_csv(path):
        if row["year"] != "2025":
            continue
        key = (row["month"], row["origin"], row["destination"])
        if key in keys:
            raise ValueError(f"Duplicate directed traffic record: {key}")
        keys.add(key)
        months.add(int(row["month"]))
        pair = tuple(sorted((row["origin"], row["destination"])))
        totals[pair] += int(row["passengers"])
    if months != set(range(1, 13)):
        raise ValueError("Route selection requires all twelve months of 2025.")
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:20]
    return [{
        "rank_2025": rank, "route": "-".join(pair),
        "airport_a": pair[0], "airport_b": pair[1],
        "passengers_2025_both_directions": passengers,
    } for rank, (pair, passengers) in enumerate(ranked, 1)]

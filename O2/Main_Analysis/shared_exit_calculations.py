"""Shared data, exit windows and full-precision shares for O2 hypotheses."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

# Read repository data and write objective-specific outputs regardless of working directory.
O2 = Path(__file__).resolve().parents[1]
RAW = O2.parent / "data" / "raw" / "carrier_monthly.csv"
RESULTS = O2 / "output" / "tables"

# Tuple order: event, exiting group, pre-window start/end, post-window start/end.
# Exclude exit months; end Jet's post window before the COVID-19 disruption.
EXITS = [
    ("Jet Airways exit", "Jet Airways Group",
     date(2018, 4, 1), date(2019, 3, 1), date(2019, 5, 1), date(2020, 2, 1)),
    ("Go First exit", "Go First",
     date(2022, 5, 1), date(2023, 4, 1), date(2023, 6, 1), date(2024, 5, 1)),
]


def ownership_group(airline: str, when: date) -> str:
    """Group brands using the January 2022 Tata ownership cutoff."""
    if airline in {"Jet Airways", "JetLite"}:
        return "Jet Airways Group"
    if airline in {"Air India", "Air India Express"}:
        return "Air India Group"
    # Recognise common ownership from acquisition, not the later legal mergers.
    if when >= date(2022, 1, 1) and airline in {
        "Vistara", "AirAsia India", "AIX Connect",
    }:
        return "Air India Group"
    return airline


def read_data() -> list[dict]:
    """Load positive-passenger scheduled-domestic observations from the raw CSV."""
    observations = []
    with RAW.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            # Keep the scheduled-domestic sample, excluding non-operating rows.
            if row["service_type"] != "scheduled_domestic":
                continue
            passengers = int(float(row["passengers"] or 0))
            if passengers <= 0:
                continue
            observations.append({
                "date": date(int(row["year"]), int(row["month"]), 1),
                "airline": row["airline"],
                "passengers": passengers,
                "seat_km": float(row["seat_km"] or 0),
                "passenger_km": float(row["passenger_km"] or 0),
                "plf": float(row["passenger_load_factor"])
                if row["passenger_load_factor"] else math.nan,
            })
    return observations


def monthly_group_shares(observations: list[dict], field: str, by_brand: bool = False) -> dict[date, dict[str, float]]:
    # Passengers measure traffic; seat-km measure offered capacity.
    totals: dict[date, float] = defaultdict(float)
    by_group: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for observation in observations:
        value = observation[field]
        totals[observation["date"]] += value
        group = observation["airline"] if by_brand else ownership_group(
            observation["airline"], observation["date"]
        )
        by_group[observation["date"]][group] += value
    # Use each month's market total so shares are percentages, not fractions.
    return {
        month: {group: 100.0 * value / totals[month] for group, value in groups.items()}
        for month, groups in by_group.items()
        if totals[month] > 0
    }


def window_mean(shares: dict[date, dict[str, float]], start: date, end: date) -> dict[str, float]:
    months = [month for month in shares if start <= month <= end]
    # Weight observed months equally; an absent group's share in a month is zero.
    groups = {group for month in months for group in shares[month]}
    return {
        group: sum(shares[month].get(group, 0.0) for month in months) / len(months)
        for group in groups
    }


def exit_comparisons() -> list[dict]:
    """Keep shares unrounded so H3 and H4 use the same underlying values."""
    observations = read_data()
    series = {
        "passengers": monthly_group_shares(observations, "passengers"),
        "seat_km": monthly_group_shares(observations, "seat_km"),
    }
    comparisons = []
    for event, exiting, pre_start, pre_end, post_start, post_end in EXITS:
        for measure, shares in series.items():
            before = window_mean(shares, pre_start, pre_end)
            after = window_mean(shares, post_start, post_end)
            for group in sorted(set(before) | set(after)):
                comparisons.append({
                    "event": event,
                    "measure": f"{measure}_share",
                    "group": group,
                    "pre_share": before.get(group, 0.0),
                    "post_share": after.get(group, 0.0),
                    "change_pp": after.get(group, 0.0) - before.get(group, 0.0),
                    "exiting_pre_share": before.get(exiting, 0.0),
                    "is_exiting": group == exiting,
                })
    return comparisons


def write_results(filename: str, rows: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    destination = RESULTS / filename
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {destination}")
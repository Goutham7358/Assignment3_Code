"""Prepare the national airline-month CSV used by O4."""

import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path


DATA = Path(__file__).resolve().parents[1]
SOURCE = DATA / "raw/carrier_monthly.csv"
OUTPUT = DATA / "processed"
SOURCE_SHA256 = "30412b650b47b9d8ba50917365b29f120f2da458403533829d65fd11b64c09be"


def ownership_group(airline, month):
    """Use the grouping convention submitted in Assignment 2, Section 2."""
    if airline in {"Air India", "Air India Express"}:
        return "Air India Group"
    if airline in {"Jet Airways", "JetLite"}:
        return "Jet Airways Group"
    # The Tata joint ventures remain separate before the acquisition month.
    if month >= date(2022, 1, 1) and airline in {
        "Vistara", "AirAsia India", "AIX Connect"
    }:
        return "Air India Group"
    return airline


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise ValueError("The source snapshot has changed. Review its provenance first.")

    with SOURCE.open(newline="", encoding="utf-8") as handle:
        original = list(csv.DictReader(handle))

    prepared = []
    seen = set()
    excluded = Counter()
    for row in original:
        if row["service_type"] != "scheduled_domestic":
            excluded["other_service_types"] += 1
            continue
        # Missing or malformed counts should raise an error, not become zero.
        passengers = int(row["passengers"])
        if passengers < 0:
            raise ValueError(f"Negative passenger count: {row}")
        if passengers == 0:
            excluded["zero_passengers"] += 1
            continue

        month = date(int(row["year"]), int(row["month"]), 1)
        key = (month, row["airline"])
        if key in seen:
            raise ValueError(f"Duplicate airline-month: {key}")
        seen.add(key)
        prepared.append({
            "date": month.isoformat(),
            "airline": row["airline"],
            "ownership_group": ownership_group(row["airline"], month),
            "passengers": passengers,
        })

    prepared.sort(key=lambda row: (row["date"], row["airline"]))
    months = sorted({row["date"] for row in prepared})
    if not months:
        raise ValueError("No scheduled domestic passenger observations found.")

    # Record missing calendar months. Do not interpolate or add zero shares.
    calendar_months = set()
    month = date.fromisoformat(months[0])
    last = date.fromisoformat(months[-1])
    while month <= last:
        calendar_months.add(month.isoformat())
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "national_airline_monthly.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=prepared[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(prepared)

    audit = {
        "input": "data/raw/carrier_monthly.csv",
        "source_sha256": source_hash,
        "raw_rows": len(original),
        "excluded_rows": dict(excluded),
        "retained_airline_months": len(prepared),
        "observed_months": len(months),
        "first_month": months[0],
        "last_month": months[-1],
        "missing_months": sorted(calendar_months - set(months)),
        "duplicate_airline_months": 0,
        "passenger_unit": "passenger journeys",
        "ownership_convention": "Assignment 2, Section 2; see data/SOURCE.md",
    }
    (OUTPUT / "national_preparation.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared {len(prepared):,} airline-months across {len(months)} months.")
    print("Missing months:", ", ".join(audit["missing_months"]))


if __name__ == "__main__":
    main()

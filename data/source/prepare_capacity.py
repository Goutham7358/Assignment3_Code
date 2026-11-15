"""Prepare reported capacity and passenger-km without altering the passenger panel."""

import csv
import hashlib
import json
import math
from datetime import date

from prepare_national import SOURCE, SOURCE_SHA256, OUTPUT, ownership_group


def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("The national source snapshot has changed.")
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        original = list(csv.DictReader(handle))

    prepared, issues = [], []
    seen = set()
    for row in original:
        if row["service_type"] != "scheduled_domestic" or int(row["passengers"]) <= 0:
            continue
        month = date(int(row["year"]), int(row["month"]), 1)
        key = (month, row["airline"])
        if key in seen:
            raise ValueError(f"Duplicate capacity observation: {key}")
        seen.add(key)
        ask, rpk = float(row["seat_km"]), float(row["passenger_km"])
        if not math.isfinite(ask) or not math.isfinite(rpk):
            raise ValueError(f"Non-finite capacity value: {key}")
        if ask == 0 and rpk == 0:
            status = "zero_ask_and_rpk_with_positive_passengers"
        elif ask <= 0 or rpk < 0 or rpk > ask:
            status = "invalid_capacity_range"
        else:
            status = "valid"
        prepared.append({
            "date": month.isoformat(), "airline": row["airline"],
            "ownership_group": ownership_group(row["airline"], month),
            "passengers": int(row["passengers"]),
            # Preserve the source's decimal strings and thousand-km units.
            "ask_thousand_seat_km": row["seat_km"],
            "rpk_thousand_passenger_km": row["passenger_km"],
            "capacity_status": status,
        })
        if status != "valid":
            issues.append({"date": month.isoformat(), "airline": row["airline"], "status": status})

    prepared.sort(key=lambda row: (row["date"], row["airline"]))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "capacity_airline_monthly.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prepared[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(prepared)
    audit = {
        "source_sha256": SOURCE_SHA256,
        "retained_passenger_airline_months": len(prepared),
        "valid_capacity_observations": len(prepared) - len(issues),
        "flagged_observations": issues,
        "handling": "Flagged records remain in the CSV. Capacity analyses must handle them explicitly; they are not imputed.",
        "ask_unit": "thousand seat-km", "rpk_unit": "thousand passenger-km",
    }
    (OUTPUT / "capacity_preparation.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Prepared {len(prepared):,} capacity records; {len(issues)} flagged for review.")


if __name__ == "__main__":
    main()

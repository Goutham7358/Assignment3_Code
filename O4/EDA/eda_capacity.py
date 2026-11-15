"""Summarise the two December capacity inputs used by O4."""

import csv
from math import fsum
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/processed/capacity_airline_monthly.csv"
OUTPUT = ROOT / "O4/output/tables"
MONTHS = ["2024-12-01", "2025-12-01"]


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    with INPUT.open(newline="", encoding="utf-8") as handle:
        selected = [row for row in csv.DictReader(handle) if row["date"] in MONTHS]
    if any(row["capacity_status"] != "valid" for row in selected):
        raise ValueError("A comparison-month capacity record needs review; do not silently exclude it.")
    totals = []
    for month in MONTHS:
        observations = [row for row in selected if row["date"] == month]
        if sum(row["airline"] == "IndiGo" for row in observations) != 1:
            raise ValueError(f"Expected exactly one IndiGo record in {month}.")
        for scope in ["IndiGo", "Other airlines"]:
            airlines = [row for row in observations if (row["airline"] == "IndiGo") == (scope == "IndiGo")]
            if not airlines:
                raise ValueError(f"Missing input for {scope}, {month}.")
            ask = fsum(float(row["ask_thousand_seat_km"]) for row in airlines)
            rpk = fsum(float(row["rpk_thousand_passenger_km"]) for row in airlines)
            totals.append({
                "date": month, "scope": scope, "airline_brands": len(airlines),
                "ask_thousand_seat_km": ask, "rpk_thousand_passenger_km": rpk,
                "ask_billion_seat_km": ask / 1_000_000,
                "rpk_billion_passenger_km": rpk / 1_000_000,
            })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "capacity_airline_inputs.csv", selected)
    write_csv(OUTPUT / "capacity_inputs.csv", totals)

    lines = [
        r"\begin{tabular}{@{}llrr@{}}", r"\toprule",
        r"Month & Airlines & \shortstack[r]{Offered capacity\\(billion seat-km)} & \shortstack[r]{Passenger traffic\\(billion passenger-km)} \\",
        r"\midrule",
    ]
    for row in totals:
        month = "Dec " + row["date"][:4]
        lines.append(f"{month} & {row['scope']} & {row['ask_billion_seat_km']:.3f} & "
                     f"{row['rpk_billion_passenger_km']:.3f}" + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "capacity_inputs_table.tex").write_text("\n".join(lines) + "\n")
    print(f"Saved capacity inputs for {len(selected)} airline records in two December months.")


if __name__ == "__main__":
    main()

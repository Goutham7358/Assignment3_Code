"""Compare rivals' unused seat-km relative to IndiGo's passenger-km in December."""

import csv
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/processed/capacity_airline_monthly.csv"
OUTPUT = ROOT / "O4/output/tables"
MONTHS = ["2024-12-01", "2025-12-01"]
MILLION = Decimal(1_000_000)  # Thousands of km to billions of km.


def write_csv(name, rows):
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_inputs():
    selected, seen = [], set()
    with INPUT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["date"] not in MONTHS:
                continue
            key = (row["date"], row["airline"])
            if key in seen or row["capacity_status"] != "valid":
                raise ValueError(f"Duplicate or flagged capacity record: {key}")
            seen.add(key)
            # Read the reported decimal strings without binary floating-point rounding.
            ask = Decimal(row["ask_thousand_seat_km"])
            rpk = Decimal(row["rpk_thousand_passenger_km"])
            if not ask.is_finite() or not rpk.is_finite() or not 0 <= rpk <= ask or ask <= 0:
                raise ValueError(f"Invalid ASK/RPK: {key}")
            selected.append({
                "date": row["date"], "airline": row["airline"],
                "role": "IndiGo" if row["airline"] == "IndiGo" else "Rival",
                "ask_thousand_seat_km": ask, "rpk_thousand_passenger_km": rpk,
                "unused_thousand_seat_km": ask - rpk,
                "ask_billion_seat_km": ask / MILLION,
                "rpk_billion_passenger_km": rpk / MILLION,
                "unused_billion_seat_km": (ask - rpk) / MILLION,
            })
    return sorted(selected, key=lambda r: (r["date"], r["airline"]))


def calculate_buffer(selected):
    results = []
    for month in MONTHS:
        indigo = [r for r in selected if r["date"] == month and r["role"] == "IndiGo"]
        rivals = [r for r in selected if r["date"] == month and r["role"] == "Rival"]
        if len(indigo) != 1 or not rivals or indigo[0]["rpk_thousand_passenger_km"] <= 0:
            raise ValueError(f"Missing or invalid comparison inputs in {month}")
        ask = sum(r["ask_thousand_seat_km"] for r in rivals)
        rpk = sum(r["rpk_thousand_passenger_km"] for r in rivals)
        unused = sum(r["unused_thousand_seat_km"] for r in rivals)
        indigo_rpk = indigo[0]["rpk_thousand_passenger_km"]
        if unused != ask - rpk:
            raise ValueError("Airline-level and aggregate unused capacity do not agree")
        results.append({
            "date": month, "rival_airline_brands": len(rivals),
            "rivals_ask_thousand_seat_km": ask,
            "rivals_rpk_thousand_passenger_km": rpk,
            "rivals_unused_thousand_seat_km": unused,
            "indigo_rpk_thousand_passenger_km": indigo_rpk,
            "rivals_ask_billion_seat_km": ask / MILLION,
            "rivals_rpk_billion_passenger_km": rpk / MILLION,
            "rivals_unused_billion_seat_km": unused / MILLION,
            "indigo_rpk_billion_passenger_km": indigo_rpk / MILLION,
            "buffer_relative_to_indigo_pct": 100 * unused / indigo_rpk,
        })
    return results


def write_report_outputs(selected, results):
    first, last = results
    lines = [r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
             r"Measure & Dec 2024 & Dec 2025 & Change \\", r"\midrule"]
    fields = [
        ("rivals_ask_billion_seat_km", "Rivals' ASK (billion seat-km)"),
        ("rivals_rpk_billion_passenger_km", "Rivals' RPK (billion passenger-km)"),
        ("rivals_unused_billion_seat_km", "Rivals' unused capacity (billion seat-km)"),
        ("indigo_rpk_billion_passenger_km", "IndiGo RPK (billion passenger-km)"),
        ("buffer_relative_to_indigo_pct", r"Buffer relative to IndiGo (\%)"),
    ]
    for field, label in fields:
        places = 2 if field.endswith("pct") else 3
        unit = " pp" if field.endswith("pct") else ""
        lines.append(f"{label} & {first[field]:.{places}f} & {last[field]:.{places}f}"
                     f" & {last[field] - first[field]:+.{places}f}{unit}" + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "capacity_buffer_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    rivals = [r for r in selected if r["role"] == "Rival"]
    lookup = {(r["date"], r["airline"]): r["unused_billion_seat_km"] for r in rivals}
    lines = [r"\begin{tabular}{@{}lrr@{}}", r"\toprule",
             r"Rival airline & Dec 2024 & Dec 2025 \\", r"\midrule"]
    for airline in sorted({r["airline"] for r in rivals}):
        values = [f"{lookup[month, airline]:.6f}" if (month, airline) in lookup else "--"
                  for month in MONTHS]
        lines.append(airline + " & " + " & ".join(values) + r" \\")
    lines.extend([r"\midrule", "Total & " + " & ".join(
        f"{r['rivals_unused_billion_seat_km']:.6f}" for r in results) + r" \\",
        r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "capacity_buffer_airlines_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [r"\begin{align*}"]
    for row in results:
        year = row["date"][:4]
        lines.append(rf"U_{{{year}}} &= {row['rivals_ask_billion_seat_km']:.9f}"
                     rf"-{row['rivals_rpk_billion_passenger_km']:.9f}"
                     rf"={row['rivals_unused_billion_seat_km']:.9f}, \\")
    for row in results:
        year = row["date"][:4]
        lines.append(rf"B_{{{year}}} &=100\times\frac{{{row['rivals_unused_billion_seat_km']:.9f}}}"
                     rf"{{{row['indigo_rpk_billion_passenger_km']:.6f}}}"
                     rf"\approx {row['buffer_relative_to_indigo_pct']:.4f}\%, \\")
    delta = last["buffer_relative_to_indigo_pct"] - first["buffer_relative_to_indigo_pct"]
    unused_change = 100 * (last["rivals_unused_billion_seat_km"] / first["rivals_unused_billion_seat_km"] - 1)
    lines.extend([rf"\Delta B &= B_{{2025}}-B_{{2024}}\approx {delta:.4f}\ \mathrm{{pp}}, \\",
                  rf"\text{{Change in unused capacity}} &=100\left(\frac{{U_{{2025}}}}{{U_{{2024}}}}-1\right)"
                  rf"\approx {unused_change:.2f}\%.",
                  r"\end{align*}"])
    (OUTPUT / "capacity_buffer_workings.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    selected = read_inputs()
    results = calculate_buffer(selected)
    first, last = results
    change = {
        "comparison": "December 2025 minus December 2024",
        "unused_capacity_change_billion_seat_km": last["rivals_unused_billion_seat_km"] - first["rivals_unused_billion_seat_km"],
        "unused_capacity_change_pct": 100 * (last["rivals_unused_billion_seat_km"] / first["rivals_unused_billion_seat_km"] - 1),
        "buffer_change_pp": last["buffer_relative_to_indigo_pct"] - first["buffer_relative_to_indigo_pct"],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv("capacity_buffer_airline.csv", selected)
    write_csv("capacity_buffer_summary.csv", results)
    write_csv("capacity_buffer_change.csv", [change])
    write_report_outputs(selected, results)
    print("O4 rivals' capacity buffer: December 2024 versus December 2025")
    print("Input: data/processed/capacity_airline_monthly.csv")
    print("Buffer (%) = 100 x rivals' (ASK - RPK) / IndiGo RPK\n")
    print("Month       Rival brands   Unused (bn seat-km)   IndiGo RPK (bn pax-km)   Buffer (%)")
    for row in results:
        print(f"{row['date'][:7]} {row['rival_airline_brands']:>15}"
              f" {row['rivals_unused_billion_seat_km']:>21.9f}"
              f" {row['indigo_rpk_billion_passenger_km']:>25.6f}"
              f" {row['buffer_relative_to_indigo_pct']:>12.4f}")
    print(f"\nBuffer change: {change['buffer_change_pp']:+.4f} percentage points")
    print(f"Rivals' unused capacity change: {change['unused_capacity_change_pct']:+.2f}%")
    print(f"All {len(selected)} selected airline records have valid capacity inputs.")
    print("Saved three CSVs and three LaTeX files in O4/output/tables/.")


if __name__ == "__main__":
    main()

"""Calculate O4's national results and save the report table and worked example."""

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/processed/national_airline_monthly.csv"
OUTPUT = ROOT / "O4/output/tables"
START, END = "2024-12-01", "2026-07-01"

# These are the conditions submitted in Assignment 2, not fitted to the results.
CR2_MIN = 80
GAP_MIN = 20
HHI_MIN = 1800
FRINGE_MAX = 20
CONDITIONS = [
    ("specified_pair", "IndiGo and Air India Group lead", None),
    ("cr2_ge_80", "CR2 >= 80%", "cr2_pct"),
    ("gap_gt_20", "Share gap > 20 pp", "share_gap_pp"),
    ("fringe_le_20", "Fringe <= 20%", "fringe_share_pct"),
    ("hhi_gt_1800", "Ownership HHI > 1,800", "ownership_hhi"),
    ("h5_joint", "Specified pair, CR2 and gap jointly", None),
]


def write_csv(name, rows):
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def calculate_monthly():
    counts = defaultdict(Counter)
    seen = set()
    with INPUT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["date"], row["airline"])
            passengers = int(row["passengers"])
            if key in seen or passengers <= 0:
                raise ValueError(f"Duplicate or nonpositive input: {key}")
            seen.add(key)
            counts[row["date"]][row["ownership_group"]] += passengers

    monthly, group_rows = [], []
    for month, groups in sorted(counts.items()):
        ranked = sorted(groups.items(), key=lambda item: (-item[1], item[0]))
        if len(ranked) < 2:
            raise ValueError(f"Fewer than two groups in {month}")
        total = sum(groups.values())
        shares = [100 * passengers / total for group, passengers in ranked]
        row = {
            "date": month, "total_passengers": total,
            "largest_group": ranked[0][0], "second_largest_group": ranked[1][0],
            "largest_share_pct": shares[0], "second_largest_share_pct": shares[1],
            "cr2_pct": shares[0] + shares[1],
            "share_gap_pp": shares[0] - shares[1],
            "fringe_share_pct": 100 * sum(n for group, n in ranked[2:]) / total,
            "ownership_hhi": sum(share ** 2 for share in shares),
        }
        row.update({
            "specified_pair": {ranked[0][0], ranked[1][0]}
            == {"IndiGo", "Air India Group"},
            "cr2_ge_80": row["cr2_pct"] >= CR2_MIN,
            "gap_gt_20": row["share_gap_pp"] > GAP_MIN,
            "fringe_le_20": row["fringe_share_pct"] <= FRINGE_MAX,
            "hhi_gt_1800": row["ownership_hhi"] > HHI_MIN,
        })
        # H5 specifies these three conditions; HHI/fringe are supporting measures.
        row["h5_joint"] = row["specified_pair"] and row["cr2_ge_80"] and row["gap_gt_20"]
        monthly.append(row)
        for (group, passengers), share in zip(ranked, shares):
            group_rows.append({
                "date": month, "ownership_group": group, "passengers": passengers,
                "passenger_share_pct": share, "hhi_contribution": share ** 2,
            })
    if not monthly:
        raise ValueError("No observations found")
    return monthly, group_rows


def make_summary(monthly, focus):
    summary = []
    for period, rows in [("2015-01 to 2026-07", monthly), ("2024-12 to 2026-07", focus)]:
        for flag, label, metric in CONDITIONS:
            matching = [row for row in rows if row[flag]]
            summary.append({
                "period": period, "condition": flag, "description": label,
                "months_meeting": len(matching), "observed_months": len(rows),
                "percent_meeting": 100 * len(matching) / len(rows),
                "minimum": min(row[metric] for row in rows) if metric else "",
                "maximum": max(row[metric] for row in rows) if metric else "",
            })
    return summary


def write_report_table(summary, compact=False):
    labels = [
        "IndiGo and AI Group lead", r"CR2 $\geq 80\%$",
        r"Share gap $>20$ pp", r"Fringe $\leq 20\%$",
        r"Ownership HHI $>1{,}800$", "Pair, CR2 and gap jointly",
    ]
    columns = r">{\raggedright\arraybackslash}p{0.43\linewidth}rrr" if compact else "lrrr"
    lines = [
        r"\begin{tabular}{@{}" + columns + r"@{}}", r"\toprule",
        r" & \shortstack{Full series\\Months / 138}"
        r" & \shortstack{Focus period\\Months / 20}"
        r" & \shortstack{Focus period\\Range} \\",
        r"\midrule",
    ]
    for i, label in enumerate(labels):
        if compact:
            # HHI and fringe remain in the complete appendix table.
            if i in (3, 4):
                continue
            if i == 0:
                label = "IndiGo and AI Group are the two largest groups"
            elif i == 5:
                label = "All three conditions together"
        full, recent = summary[i], summary[i + len(CONDITIONS)]
        value_range = "--"
        if recent["minimum"] != "":
            value_range = f"{recent['minimum']:,.2f}--{recent['maximum']:,.2f}"
            if compact:
                value_range += r"\%" if i == 1 else " pp"
        lines.append(f"{label} & {full['months_meeting']}/138"
                     f" & {recent['months_meeting']}/20 & {value_range}" + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    name = "national_h5_table.tex" if compact else "national_results_table.tex"
    (OUTPUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_worked_example(monthly, group_rows):
    example = next(row for row in monthly if row["date"] == END)
    groups = [row for row in group_rows if row["date"] == END]
    write_csv("national_worked_example.csv", groups)
    lines = [
        r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
        r"Ownership group & Passengers & Share (\%) & HHI contribution \\",
        r"\midrule",
    ]
    for row in groups:
        lines.append(f"{row['ownership_group']} & {row['passengers']:,}"
                     f" & {row['passenger_share_pct']:.4f} & {row['hhi_contribution']:,.2f}"
                     + r" \\")
    lines.extend([
        r"\midrule",
        f"Total & {example['total_passengers']:,} & 100.0000 & {example['ownership_hhi']:,.2f}" + r" \\",
        r"\bottomrule", r"\end{tabular}",
    ])
    (OUTPUT / "national_worked_groups.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    s1, s2 = example["largest_share_pct"], example["second_largest_share_pct"]
    calculations = [
        r"\begin{align*}",
        rf"\mathrm{{CR2}} &\approx {s1:.4f}+{s2:.4f} \approx {example['cr2_pct']:.4f}\%, \\",
        rf"\mathrm{{Gap}} &\approx {s1:.4f}-{s2:.4f} \approx {example['share_gap_pp']:.4f}\ \mathrm{{pp}}, \\",
        rf"\mathrm{{Fringe}} &\approx 100-{example['cr2_pct']:.4f} \approx {example['fringe_share_pct']:.4f}\%, \\",
        rf"\mathrm{{HHI}} &= \sum_g s_g^2 \approx {example['ownership_hhi']:,.2f}.",
        r"\end{align*}",
    ]
    (OUTPUT / "national_worked_calculations.tex").write_text(
        "\n".join(calculations) + "\n", encoding="utf-8"
    )


def main():
    monthly, groups = calculate_monthly()
    expected_months = {
        date(year, month, 1).isoformat()
        for year in range(2015, 2027) for month in range(1, 13)
        if (year, month) <= (2026, 7) and (year, month) != (2020, 4)
    }
    if {row["date"] for row in monthly} != expected_months:
        raise ValueError("National coverage has changed; review the report periods first")
    focus = [row for row in monthly if START <= row["date"] <= END]
    first, last = date.fromisoformat(START), date.fromisoformat(END)
    expected = (last.year - first.year) * 12 + last.month - first.month + 1
    if len(focus) != expected:
        raise ValueError("The specified H5 period has missing months")
    summary = make_summary(monthly, focus)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv("national_results_monthly.csv", monthly)
    write_csv("national_results_summary.csv", summary)
    write_report_table(summary)
    write_report_table(summary, compact=True)
    write_worked_example(monthly, groups)

    print("O4 national concentration results")
    print(f"Input: {INPUT.relative_to(ROOT)}")
    print(f"Full series: {len(monthly)} observed months, Jan 2015-Jul 2026 (Apr 2020 missing)")
    print(f"Focus period: {len(focus)} months, Dec 2024-Jul 2026 (no missing months)\n")
    print(f"{'Condition':<39} {'Full series':>13} {'Focus period':>14}")
    for i, (flag, label, metric) in enumerate(CONDITIONS):
        full, recent = summary[i], summary[i + len(CONDITIONS)]
        print(f"{label:<39} {full['months_meeting']:>6}/{len(monthly):<6}"
              f" {recent['months_meeting']:>7}/{len(focus)}")
    print("\nFocus-period ranges (calculated before rounding):")
    for row in summary[len(CONDITIONS):]:
        if row["minimum"] != "":
            print(f"  {row['description']:<26} {row['minimum']:,.2f} to {row['maximum']:,.2f}")
    print("\nSaved 3 CSVs and 4 LaTeX files in O4/output/tables/.")
    print("Counts use unrounded monthly values; formal hypothesis review belongs in Section 6.")


if __name__ == "__main__":
    main()

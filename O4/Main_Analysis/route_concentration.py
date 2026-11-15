"""Calculate route concentration and IndiGo exposure from cleaned schedule CSVs."""

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/processed/routes"
OUTPUT = ROOT / "O4/output/tables"
HHI_CUTOFF = 1800
INDIGO_CUTOFF = 60  # Study-defined exposure flag, as submitted in Assignment 2.
FLAGS = ["hhi_gt_1800", "cr2_ge_80", "gap_gt_20", "fringe_le_20",
         "indigo_ge_60", "indigo_sole", "specified_pair_unique", "top_two_boundary_tie",
         "specified_pair_cr2_gap"]
METRICS = ["group_frequency_hhi", "group_cr2_pct", "share_gap_pp",
           "fringe_share_pct", "indigo_share_pct"]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows):
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def calculate_routes():
    prepared = read_csv(DATA / "route_monthly.csv")
    groups = defaultdict(dict)
    for row in read_csv(DATA / "group_route_monthly.csv"):
        key = (row["month"], row["route"])
        owner, flights = row["ownership_group"], int(row["scheduled_flights"])
        if owner in groups[key] or flights <= 0:
            raise ValueError(f"Duplicate group or nonpositive flight count: {key}, {owner}")
        groups[key][owner] = flights
    keys = {(row["month"], row["route"]) for row in prepared}
    if len(keys) != len(prepared) or keys != set(groups):
        raise ValueError("Route and group CSVs have duplicate or different observations")

    results = []
    for source in sorted(prepared, key=lambda r: (r["month"], int(r["rank_2025"]))):
        key = (source["month"], source["route"])
        ranked = sorted(groups[key].items(), key=lambda item: (-item[1], item[0]))
        total = sum(groups[key].values())
        if total != int(source["scheduled_flights_both_directions"]):
            raise ValueError(f"Flight totals disagree: {key}")
        first = ranked[0][1]
        second = ranked[1][1] if len(ranked) > 1 else 0
        indigo = groups[key].get("IndiGo", 0)
        hhi = 10000 * sum(n * n for owner, n in ranked) / total ** 2
        cr2 = 100 * (first + second) / total
        for field, value in [("group_frequency_hhi", hhi), ("group_cr2_pct", cr2)]:
            if not math.isclose(value, float(source[field]), abs_tol=1e-7, rel_tol=0):
                raise ValueError(f"Calculated {field} differs from prepared data: {key}")
        # A tie between ranks 2 and 3 means there is no unique top-two pair.
        boundary_tie = len(ranked) > 2 and second == ranked[2][1]
        pair = sorted(owner for owner, n in ranked[:2])
        category = "Tie at second place" if boundary_tie else " + ".join(pair)
        results.append({
            "month": key[0], "route": key[1], "rank_2025": int(source["rank_2025"]),
            "scheduled_flights": total, "group_count": len(ranked),
            "largest_group": ranked[0][0],
            "second_largest_group": ranked[1][0] if len(ranked) > 1 else "",
            "first_place_groups": "; ".join(owner for owner, n in ranked if n == first),
            "second_place_groups": "; ".join(owner for owner, n in ranked if n == second),
            "leading_pair_category": category,
            "group_frequency_hhi": hhi, "group_cr2_pct": cr2,
            "share_gap_pp": 100 * (first - second) / total,
            "fringe_share_pct": 100 * (total - first - second) / total,
            "indigo_flights": indigo, "indigo_share_pct": 100 * indigo / total,
            # Compare integer counts before any rounding of the displayed shares.
            "hhi_gt_1800": 10000 * sum(n * n for owner, n in ranked) > HHI_CUTOFF * total ** 2,
            "cr2_ge_80": 100 * (first + second) >= 80 * total,
            "gap_gt_20": 100 * (first - second) > 20 * total,
            "fringe_le_20": 100 * (total - first - second) <= 20 * total,
            "indigo_ge_60": 100 * indigo >= INDIGO_CUTOFF * total,
            "indigo_sole": indigo == total,
            "specified_pair_unique": not boundary_tie and pair == ["Air India Group", "IndiGo"],
            "top_two_boundary_tie": boundary_tie,
            "endpoint_counts_match": source["endpoint_counts_match"] == "True",
        })
    for row in results:
        row["specified_pair_cr2_gap"] = (
            row["specified_pair_unique"] and row["cr2_ge_80"] and row["gap_gt_20"]
        )
    return results, groups


def summarise(label, rows):
    if not rows:
        raise ValueError(f"No observations in {label}")
    result = {
        "sample": label, "observations": len(rows),
        "observed_months": len({r["month"] for r in rows}),
        "airport_pairs": len({r["route"] for r in rows}),
        "first_month": min(r["month"] for r in rows),
        "last_month": max(r["month"] for r in rows),
    }
    for flag in FLAGS:
        result[flag + "_count"] = sum(r[flag] for r in rows)
        result[flag + "_pct"] = 100 * result[flag + "_count"] / len(rows)
    for field in METRICS:
        result[field + "_median"] = median(r[field] for r in rows)
    return result


def write_tex_table(name, header, lines, columns):
    content = [rf"\begin{{tabular}}{{@{{}}{columns}@{{}}}}", r"\toprule",
               header + r" \\", r"\midrule"]
    content.extend(line if line == r"\midrule" else line + r" \\" for line in lines)
    content.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / name).write_text("\n".join(content) + "\n", encoding="utf-8")


def write_report_tables(summary, leaders):
    full = summary[0]
    conditions = [
        ("hhi_gt_1800", r"Ownership frequency HHI $>1{,}800$"),
        ("cr2_ge_80", r"Group CR2 $\geq80\%$"),
        ("gap_gt_20", r"Group share gap $>20$ pp"),
        ("indigo_ge_60", r"IndiGo frequency share $\geq60\%$"),
        ("indigo_sole", "IndiGo is the sole scheduled operator"),
        ("specified_pair_unique", "IndiGo and AI Group: unique top-two pair"),
        ("specified_pair_cr2_gap", "Unique pair, CR2 and gap conditions jointly"),
        ("top_two_boundary_tie", "Tie prevents a unique top-two pair"),
    ]
    lines = [f"{label} & {full[flag + '_count']:,}/{full['observations']:,}"
             f" & {full[flag + '_pct']:.2f}" for flag, label in conditions]
    write_tex_table("route_results_table.tex", r"Condition & Observations & Share (\%)", lines, "lrr")

    labels = ["Full sample", "Exact endpoint matches", "December 2025"]
    lines = []
    for label, row in zip(labels, summary):
        n = row["observations"]
        lines.append(f"{label} & {n:,} & {row['hhi_gt_1800_count']:,}"
                     f" ({row['hhi_gt_1800_pct']:.2f}\\%)"
                     f" & {row['indigo_ge_60_count']} ({row['indigo_ge_60_pct']:.2f}\\%)")
    write_tex_table("route_sensitivity_table.tex",
                    r"Sample & $N$ & HHI $>1{,}800$: $n$ (\%) & IndiGo $\geq60\%$: $n$ (\%)",
                    lines, "lrrr")
    lines = [f"{row['leading_pair_category']} & {row['observations']} & {row['percent']:.2f}"
             for row in leaders]
    write_tex_table("route_leading_pairs_table.tex",
                    r"Top-two ownership groups & Observations & Share (\%)", lines, "lrr")


def write_example(results, groups):
    key = ("2026-06", "DEL-PNQ")
    row = next(r for r in results if (r["month"], r["route"]) == key)
    counts = sorted(groups[key].items(), key=lambda item: (-item[1], item[0]))
    n = row["scheduled_flights"]
    example = [{"ownership_group": owner, "scheduled_flights": flights,
                "frequency_share_pct": 100 * flights / n,
                "hhi_contribution": (100 * flights / n) ** 2} for owner, flights in counts]
    write_csv("route_worked_example.csv", example)
    lines = [f"{r['ownership_group']} & {r['scheduled_flights']}"
             f" & {r['frequency_share_pct']:.4f} & {r['hhi_contribution']:,.2f}" for r in example]
    lines.extend([r"\midrule", f"Total & {n:,} & 100.0000 & {row['group_frequency_hhi']:,.2f}"])
    write_tex_table("route_worked_groups.tex", r"Group & Scheduled flights & Share (\%) & HHI contribution",
                    lines, "lrrr")
    s1, s2 = [r["frequency_share_pct"] for r in example[:2]]
    calculations = [
        r"\begin{align*}",
        rf"\mathrm{{CR2}} &\approx {s1:.4f}+{s2:.4f} \approx {row['group_cr2_pct']:.4f}\%, \\",
        rf"\mathrm{{Gap}} &\approx {s1:.4f}-{s2:.4f} \approx {row['share_gap_pp']:.4f}\ \mathrm{{pp}}, \\",
        rf"\mathrm{{Fringe}} &\approx 100-{row['group_cr2_pct']:.4f} \approx {row['fringe_share_pct']:.4f}\%, \\",
        rf"\mathrm{{HHI}} &= \sum_g s_g^2 \approx {row['group_frequency_hhi']:,.2f}, \\",
        rf"s_{{\mathrm{{IndiGo}}}} &= 100\times{row['indigo_flights']}/{n} \approx {row['indigo_share_pct']:.4f}\%.",
        r"\end{align*}",
    ]
    (OUTPUT / "route_worked_calculations.tex").write_text("\n".join(calculations) + "\n", encoding="utf-8")


def main():
    results, groups = calculate_routes()
    if len(results) != 1150 or len({r["route"] for r in results}) != 20:
        raise ValueError("Route coverage changed; review the report scope first")
    subsets = [("full_sample", results),
               ("exact_endpoint_matches", [r for r in results if r["endpoint_counts_match"]]),
               ("december_2025", [r for r in results if r["month"] == "2025-12"])]
    summary = [summarise(label, rows) for label, rows in subsets]
    monthly = [summarise(month, [r for r in results if r["month"] == month])
               for month in sorted({r["month"] for r in results})]
    by_pair = [summarise(route, [r for r in results if r["route"] == route])
               for route in sorted({r["route"] for r in results},
                                   key=lambda route: next(r["rank_2025"] for r in results if r["route"] == route))]
    counts = Counter(r["leading_pair_category"] for r in results)
    leaders = [{"leading_pair_category": pair, "observations": n, "percent": 100 * n / len(results)}
               for pair, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv("route_results_monthly.csv", results)
    write_csv("route_results_summary.csv", summary)
    write_csv("route_results_by_month.csv", monthly)
    write_csv("route_results_by_pair.csv", by_pair)
    write_csv("route_leading_pairs.csv", leaders)
    write_report_tables(summary, leaders)
    write_example(results, groups)

    print("O4 route concentration and IndiGo dependence")
    print("Input: data/processed/routes/{route_monthly,group_route_monthly}.csv")
    print(f"Sample: {len(results):,} airport-pair/month observations; 20 pairs; {len(monthly)} observed months")
    print("Period: April 2019-September 2026; unavailable observations are excluded.\n")
    print(f"{'Sample':<25} {'N':>6} {'HHI > 1800: n (%)':>23} {'IndiGo >= 60%: n (%)':>24}")
    for row in summary:
        print(f"{row['sample']:<25} {row['observations']:>6,}"
              f" {row['hhi_gt_1800_count']:>10,} ({row['hhi_gt_1800_pct']:>6.2f}%)"
              f" {row['indigo_ge_60_count']:>12} ({row['indigo_ge_60_pct']:>6.2f}%)")
    full = summary[0]
    print(f"\nIndiGo sole operator: {full['indigo_sole_count']}/{len(results):,}")
    print(f"Unique IndiGo-AI top-two pair: {full['specified_pair_unique_count']}/{len(results):,}"
          f" ({full['specified_pair_unique_pct']:.2f}%)")
    print(f"Ties prevent a unique pair: {full['top_two_boundary_tie_count']}/{len(results):,}")
    print(f"Unique pair + CR2 >=80% + gap >20 pp: {full['specified_pair_cr2_gap_count']}/{len(results):,}"
          f" ({full['specified_pair_cr2_gap_pct']:.2f}%)")
    print("Monthly percentage of available pairs with IndiGo >=60%:",
          f"{min(r['indigo_ge_60_pct'] for r in monthly):.2f}% to"
          f" {max(r['indigo_ge_60_pct'] for r in monthly):.2f}%")
    december = summary[-1]
    print(f"December 2025: {december['indigo_ge_60_count']} of {december['observations']} available pairs"
          f" flagged; IndiGo-only pairs: {december['indigo_sole_count']}.")
    print("\nSaved 6 CSVs and 5 LaTeX files in O4/output/tables/.")


if __name__ == "__main__":
    main()

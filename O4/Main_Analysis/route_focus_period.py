"""Compare national and route concentration during December 2024-July 2026."""

from statistics import median

from national_concentration import calculate_monthly
from route_concentration import OUTPUT, calculate_routes, summarise, write_csv, write_tex_table
from report_table import write_grid_table


FIRST, LAST = "2024-12", "2026-07"


def add_leadership(row, counts):
    total = sum(counts.values())
    highest = max(counts.values())
    leaders = [owner for owner, flights in counts.items() if flights == highest]
    row["indigo_unique_leader"] = leaders == ["IndiGo"]
    row["ai_unique_leader"] = leaders == ["Air India Group"]
    row["first_place_tie"] = len(leaders) > 1
    row["ai_share_pct"] = 100 * counts.get("Air India Group", 0) / total
    row["indigo_minus_ai_pp"] = row["indigo_share_pct"] - row["ai_share_pct"]
    # Require IndiGo to lead, rather than letting either group be the larger one.
    row["indigo_led_joint"] = row["specified_pair_cr2_gap"] and row["indigo_unique_leader"]


def focus_summary(label, rows):
    result = summarise(label, rows)
    for flag in ["indigo_unique_leader", "ai_unique_leader", "first_place_tie", "indigo_led_joint"]:
        result[flag + "_count"] = sum(r[flag] for r in rows)
        result[flag + "_pct"] = 100 * result[flag + "_count"] / len(rows)
    for field in ["ai_share_pct", "indigo_minus_ai_pp"]:
        result[field + "_median"] = median(r[field] for r in rows)
    return result


def write_report_tables(comparison, summary, monthly):
    samples = [comparison[0], comparison[2], comparison[1]]  # National, top 20, top 10.
    lines = []
    for field, label in [
        ("specified_pair_count", "IndiGo and AI Group are the unique top two"),
        ("cr2_median_pct", r"Median CR2 (\%)"),
        ("gap_median_pp", "Median share gap (pp)"),
        ("fringe_median_pct", r"Median fringe share (\%)"),
        ("indigo_led_joint_count", r"Leading pair, CR2 $\geq80\%$ and gap $>20$ pp, with IndiGo first"),
    ]:
        values = []
        for row in samples:
            value = (f"{row[field]}/{row['observations']}" if field.endswith("count")
                     else f"{row[field]:.2f}")
            values.append(value)
        lines.append(label + " & " + " & ".join(values))
    write_grid_table(OUTPUT / "national_route_focus_table.tex", [
        "Measure", r"\shortstack{National\\Passenger data}",
        r"\shortstack{Top 20\\airport pairs\\Scheduled flights}",
        r"\shortstack{Top 10\\airport pairs\\Scheduled flights}",
    ], lines)

    counts = {r["sample"]: r["observations"] for r in monthly}
    months = sorted(key.split(":")[1] for key in counts if key.startswith("top10:"))
    lines = [f"{month} & {counts['top10:' + month]}/10 & {counts['top20:' + month]}/20"
             for month in months]
    lines.extend([r"\midrule", f"Total pair-months & {summary[0]['observations']}/200"
                  f" & {summary[1]['observations']}/400"])
    write_tex_table("route_focus_coverage_table.tex", "Month & Top 10 retained & Top 20 retained",
                    lines, "lrr")

    top10, top20 = summary
    lines = [r"\begin{align*}"]
    for i, (row, label) in enumerate([(top10, "Top 10"), (top20, "Top 20")]):
        n, qualified = row["observations"], row["indigo_led_joint_count"]
        lines.append(rf"\text{{{label}, IndiGo-led joint share}}"
                     rf" &= 100\times{qualified}/{n} \approx {100 * qualified / n:.2f}\%"
                     + (r", \\" if i == 0 else "."))
    lines.append(r"\end{align*}")
    (OUTPUT / "route_focus_counts.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    all_routes, groups = calculate_routes()
    rows = [r for r in all_routes if FIRST <= r["month"] <= LAST]
    for row in rows:
        add_leadership(row, groups[row["month"], row["route"]])
    top10 = [r for r in rows if r["rank_2025"] <= 10]
    summary = [focus_summary("top10_focus", top10), focus_summary("top20_focus", rows)]
    monthly = [focus_summary(f"{label}:{month}", [r for r in data if r["month"] == month])
               for label, data in [("top10", top10), ("top20", rows)]
               for month in sorted({r["month"] for r in data})]
    by_pair = [focus_summary(route, [r for r in rows if r["route"] == route])
               for route in sorted({r["route"] for r in rows},
                                   key=lambda route: next(r["rank_2025"] for r in rows if r["route"] == route))]
    national, _ = calculate_monthly()
    national = [r for r in national if FIRST <= r["date"][:7] <= LAST]
    if len(national) != 20 or any(s["observed_months"] != 20 for s in summary):
        raise ValueError("An expected focus-period month is absent")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv("route_focus_observations.csv", rows)
    write_csv("route_focus_summary.csv", summary)
    write_csv("route_focus_by_month.csv", monthly)
    write_csv("route_focus_by_pair.csv", by_pair)
    comparison = [{
        "sample": "national_focus", "observations": len(national),
        "observation_unit": "national month; passenger shares",
        "specified_pair_count": sum(r["specified_pair"] for r in national),
        "cr2_median_pct": median(r["cr2_pct"] for r in national),
        "gap_median_pp": median(r["share_gap_pp"] for r in national),
        "fringe_median_pct": median(r["fringe_share_pct"] for r in national),
        "indigo_led_joint_count": sum(r["h5_joint"] and r["largest_group"] == "IndiGo"
                                      for r in national),
    }]
    for s in summary:
        comparison.append({
            "sample": s["sample"], "observations": s["observations"],
            "observation_unit": "airport pair/month; scheduled-frequency shares",
            "specified_pair_count": s["specified_pair_unique_count"],
            "cr2_median_pct": s["group_cr2_pct_median"],
            "gap_median_pp": s["share_gap_pp_median"],
            "fringe_median_pct": s["fringe_share_pct_median"],
            "indigo_led_joint_count": s["indigo_led_joint_count"],
        })
    write_csv("national_route_focus_comparison.csv", comparison)
    write_report_tables(comparison, summary, monthly)

    print("Matched focus period: December 2024-July 2026 (20 months)")
    for row in comparison:
        n = row["observations"]
        print(f"\n{row['sample']}: {n} observations ({row['observation_unit']})")
        print(f"  IndiGo-AI leading pair: {row['specified_pair_count']}/{n}")
        print(f"  Median CR2: {row['cr2_median_pct']:.2f}%")
        print(f"  Median leader-rival gap: {row['gap_median_pp']:.2f} pp")
        print(f"  Median fringe: {row['fringe_median_pct']:.2f}%")
        print(f"  Pair + CR2 >=80% + gap >20 pp, with IndiGo leading: {row['indigo_led_joint_count']}/{n}")
    for s in summary:
        print(f"\n{s['sample']} leadership: IndiGo {s['indigo_unique_leader_count']},"
              f" AI Group {s['ai_unique_leader_count']}, ties {s['first_place_tie_count']}")
    print(f"\nTop 10: {len(top10)}/200 possible pair-months retained;"
          f" top 20: {len(rows)}/400.")
    print("Pairs use their fixed 2025 passenger ranking; missing observations are excluded.")
    print("Saved five CSVs and three LaTeX files in O4/output/tables/.")


if __name__ == "__main__":
    main()

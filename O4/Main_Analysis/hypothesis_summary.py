"""Assess the three O4 hypotheses using the submitted conditions and periods."""

from capacity_buffer import calculate_buffer, read_inputs
from national_concentration import END, START, calculate_monthly
from report_table import write_grid_table
from route_concentration import OUTPUT, calculate_routes, write_csv


def outcome(condition):
    return "Supported" if condition else "Not supported"


def main():
    national, _ = calculate_monthly()
    focus = [r for r in national if START <= r["date"] <= END]
    if len(focus) != 20:
        raise ValueError("H5 requires all 20 months from December 2024 to July 2026")
    national_count = sum(r["h5_joint"] for r in focus)
    minimum_cr2 = min(r["cr2_pct"] for r in focus)
    minimum_gap = min(r["share_gap_pp"] for r in focus)

    routes, _ = calculate_routes()
    route_count = sum(r["hhi_gt_1800"] for r in routes)
    if not routes or len({r["route"] for r in routes}) != 20:
        raise ValueError("H6 requires the selected 20-pair sample")
    route_pct = 100 * route_count / len(routes)
    before, after = calculate_buffer(read_inputs())
    before_pct = before["buffer_relative_to_indigo_pct"]
    after_pct = after["buffer_relative_to_indigo_pct"]
    delta = after_pct - before_pct

    rows = [
        {
            "hypothesis": "H5",
            "expected_relationship": "IndiGo and AI Group are the two largest in every month, Dec 2024-Jul 2026, with CR2 >=80% and gap >20 pp",
            "outcome": outcome(national_count == len(focus)),
            "qualifying_observations": national_count, "observed_months_or_pair_months": len(focus),
            "before_buffer_pct": "", "after_buffer_pct": "", "buffer_change_pp": "",
            "evidence": f"{national_count}/{len(focus)} months; minimum CR2 {minimum_cr2:.2f}%; minimum gap {minimum_gap:.2f} pp",
        },
        {
            "hypothesis": "H6",
            "expected_relationship": "Ownership-adjusted frequency HHI >1,800 in more than half the available observations for the selected 20 pairs",
            # More than half is strict; exactly half would not meet H6.
            "outcome": outcome(2 * route_count > len(routes)),
            "qualifying_observations": route_count, "observed_months_or_pair_months": len(routes),
            "before_buffer_pct": "", "after_buffer_pct": "", "buffer_change_pp": "",
            "evidence": f"{route_count:,}/{len(routes):,} pair-months ({route_pct:.2f}%) exceed 1,800",
        },
        {
            "hypothesis": "H7",
            "expected_relationship": "Rivals' unused capacity relative to IndiGo RPK is lower in Dec 2025 than Dec 2024",
            "outcome": outcome(after_pct < before_pct),
            "qualifying_observations": "", "observed_months_or_pair_months": "",
            "before_buffer_pct": before_pct, "after_buffer_pct": after_pct, "buffer_change_pp": delta,
            "evidence": f"{before_pct:.4f}% to {after_pct:.4f}%; change {delta:+.4f} pp",
        },
    ]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv("hypothesis_results.csv", rows)
    references = [r"Table~\ref{tab:o4-national-results}.", r"Table~\ref{tab:o4-route-results}.",
                  r"Table~\ref{tab:o4-capacity-buffer}."]
    # The LaTeX table includes H1-H4 placeholders; CSV results cover H5-H7.
    pending = [("H1", "O1"), ("H2", "O1"), ("H3", "O2"), ("H4", "O2")]
    table_rows = [rf"\textbf{{{hypothesis}}} ({objective}) & &"
                  for hypothesis, objective in pending]
    for row, reference in zip(rows, references):
        evidence = row["evidence"].replace("%", r"\%")
        hypothesis = rf"\textbf{{{row['hypothesis']}}} (O4)"
        table_rows.append(f"{hypothesis} & {row['outcome']} & {evidence}. {reference}")
    columns = (r"|>{\raggedright\arraybackslash}p{0.19\linewidth}"
               r"|>{\raggedright\arraybackslash}p{0.16\linewidth}"
               r"|>{\raggedright\arraybackslash}X|")
    write_grid_table(OUTPUT / "hypothesis_results_table.tex",
                     ["Hypothesis (objective)", "Outcome", "Supporting evidence"],
                     table_rows, columns=columns)
    for row in rows:
        print(f"{row['hypothesis']}: {row['outcome']} - {row['evidence']}")
    print("Saved hypothesis_results.csv and hypothesis_results_table.tex in O4/output/tables/.")
    print("These are descriptive condition checks, not statistical significance tests.")


if __name__ == "__main__":
    main()

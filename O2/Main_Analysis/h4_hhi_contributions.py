#!/usr/bin/env python3
"""H4: Does IndiGo account for more than half of the net HHI rise after each exit?

Generate each group's contribution in h4_hhi_contributions.csv. Sum every
group, including the exiting airline, to obtain the net HHI change.
"""

from shared_exit_calculations import exit_comparisons, write_results


def build_hhi_rows(comparisons: list[dict]) -> list[dict]:
    rows = []
    # Decompose HHI of window-average shares, not the average of monthly HHIs.
    for comparison in comparisons:
        before = comparison["pre_share"]
        change = comparison["change_pp"]
        # Expand post_share^2 - pre_share^2; percentage shares give HHI points.
        # The exiting group has zero post-window share, hence its negative term.
        contribution = (
            -before ** 2 if comparison["is_exiting"]
            else 2 * before * change + change ** 2
        )
        rows.append({
            "event": comparison["event"],
            "measure": comparison["measure"],
            "group": comparison["group"],
            "hhi_contribution": round(contribution, 1),
        })
    return rows


def main() -> None:
    write_results("h4_hhi_contributions.csv", build_hhi_rows(exit_comparisons()))


if __name__ == "__main__":
    main()
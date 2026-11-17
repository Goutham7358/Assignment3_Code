#!/usr/bin/env python3
"""H3: Does IndiGo absorb the most share, and more after Go First than Jet?

Generate the passenger and capacity evidence in h3_exit_share_absorption.csv.
Ratios compare market shares; they do not track individual passengers.
"""

from shared_exit_calculations import exit_comparisons, write_results


def build_absorption_rows(comparisons: list[dict]) -> list[dict]:
    rows = []
    for comparison in comparisons:
        exiting_share = comparison["exiting_pre_share"]
        # Express a survivor's share gain as a percentage of the exiting share.
        # Blank means not applicable; negative ratios mean the survivor lost share.
        absorption = (
            round(100.0 * comparison["change_pp"] / exiting_share, 1)
            if not comparison["is_exiting"] and exiting_share else ""
        )
        # Round for export only; H4 uses the full-precision comparisons.
        rows.append({
            "event": comparison["event"],
            "measure": comparison["measure"],
            "group": comparison["group"],
            "pre_share": round(comparison["pre_share"], 3),
            "post_share": round(comparison["post_share"], 3),
            "change_pp": round(comparison["change_pp"], 3),
            "exiting_pre_share": round(exiting_share, 3),
            "pct_of_exiting_share": absorption,
        })
    return rows


def main() -> None:
    write_results("h3_exit_share_absorption.csv", build_absorption_rows(exit_comparisons()))


if __name__ == "__main__":
    main()
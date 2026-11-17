#!/usr/bin/env python3
"""Run the separate H3, H4 and supporting Tata calculations.

Export hypothesis-specific tables and a combined exit-share table.
"""

from h3_exit_share_absorption import build_absorption_rows
from h4_hhi_contributions import build_hhi_rows
from shared_exit_calculations import exit_comparisons, read_data, write_results
from supporting_tata_consolidation import write_tata


def main() -> None:
    # Build one unrounded comparison set so H3 and H4 use identical inputs.
    comparisons = exit_comparisons()
    print("H3: Who absorbed the exiting airlines' shares?")
    absorption_rows = build_absorption_rows(comparisons)
    write_results("h3_exit_share_absorption.csv", absorption_rows)

    print("H4: Who contributed to the rise in HHI?")
    hhi_rows = build_hhi_rows(comparisons)
    write_results("h4_hhi_contributions.csv", hhi_rows)

    # Both builders preserve row order; join matching rows for the combined table.
    combined_rows = [
        {**absorption, "hhi_contribution": concentration["hhi_contribution"]}
        for absorption, concentration in zip(absorption_rows, hhi_rows)
    ]
    write_results("exit_share_decomposition.csv", combined_rows)

    print("Supporting analysis: Tata consolidation (separate from H3 and H4)")
    write_tata(read_data())


if __name__ == "__main__":
    main()

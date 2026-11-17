#!/usr/bin/env python3
"""Supporting O2 analysis: fixed-share Tata effects versus observed HHI changes.

This comparison is separate from H3 and H4 and is not a causal merger estimate.
"""

from datetime import date

from shared_exit_calculations import monthly_group_shares, read_data, window_mean, write_results

TATA_BRANDS = {"Air India", "Air India Express", "Vistara", "AirAsia India", "AIX Connect"}
# Each step sets: label, HHI measure, fixed-share month,
# merger unit sets, pre window and post window. One unit may contain several brands.
TATA_STEPS = [
    ("Acquisition (Jan 2022)", "ownership_hhi",
     date(2021, 12, 1), [[["Air India", "Air India Express"], ["Vistara"], ["AirAsia India"]]],
     (date(2021, 1, 1), date(2021, 12, 1)), (date(2022, 1, 1), date(2022, 12, 1))),
    ("Mergers (Dec 2024)", "brand_hhi",
     date(2024, 9, 1), [[["Air India"], ["Vistara"]], [["Air India Express"], ["AIX Connect"]]],
     (date(2023, 10, 1), date(2024, 9, 1)), (date(2024, 12, 1), date(2025, 11, 1))),
]


def write_tata(observations: list[dict]) -> None:
    brand = monthly_group_shares(observations, "passengers", by_brand=True)
    ownership = monthly_group_shares(observations, "passengers")

    rows = []
    for step, measure, month, merges, pre_window, post_window in TATA_STEPS:
        mechanical = 0.0
        # Holding shares fixed, merging units adds 2*s_i*s_j for each unit pair.
        # Calculate separate merger sets independently before adding their effects.
        for units in merges:
            unit_shares = [sum(brand[month].get(airline, 0.0) for airline in unit) for unit in units]
            mechanical += sum(
                2 * first_share * second_share
                for position, first_share in enumerate(unit_shares)
                for second_share in unit_shares[position + 1:]
            )
        # Observed change compares mean monthly HHIs, not HHI of mean shares.
        hhi_shares = brand if measure == "brand_hhi" else ownership
        window_hhi = []
        for start, end in (pre_window, post_window):
            monthly_hhi = [
                sum(share ** 2 for share in hhi_shares[observed_month].values())
                for observed_month in sorted(hhi_shares)
                if start <= observed_month <= end
            ]
            window_hhi.append(sum(monthly_hhi) / len(monthly_hhi))
        rows.append({"step": step, "item": "mechanical", "points": round(mechanical, 1)})
        rows.append({"step": step, "item": "observed",
                     "points": round(window_hhi[1] - window_hhi[0], 1)})
        if measure != "brand_hhi":
            continue
        # This brand breakdown squares window-average shares. It need not exactly
        # match the observed change, which instead averages monthly brand HHIs.
        before = window_mean(brand, *pre_window)
        after = window_mean(brand, *post_window)
        squares = {
            airline: after.get(airline, 0.0) ** 2 - before.get(airline, 0.0) ** 2
            for airline in set(before) | set(after)
        }
        rows.append({"step": step, "item": "Tata brands combined",
                     "points": round(sum(value for airline, value in squares.items() if airline in TATA_BRANDS), 1)})
        # Show non-Tata brands only when their absolute contribution is >= 1 point.
        for airline, value in sorted(squares.items(), key=lambda item: -abs(item[1])):
            if airline not in TATA_BRANDS and abs(value) >= 1:
                rows.append({"step": step, "item": airline, "points": round(value, 1)})
    write_results("tata_consolidation.csv", rows)


def main() -> None:
    write_tata(read_data())


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""O3 route presence of the nine entrants over full IATA seasons.

Counts scheduled departures on each operating day, within every schedule row's
validity dates clipped to its IATA season, then measures each entrant's share
of departures on its airport pairs. Each entrant's selected season is its latest
season before closure or merger, or its latest available season. A separate
monthly check covers TruJet in November 2019.
"""

import calendar
from datetime import date, timedelta

import pandas as pd

from entrant_common import (
    DATA, ENTRANTS, O3, OUTCOMES, TABLES, VISTARA_MERGER, latex_row,
    load_national_shares, write_latex_rows,
)

ROWS = DATA / "interim" / "routes" / "o3_schedule_rows.csv"
CITY_PAIR_TRAFFIC = DATA / "raw" / "domestic_route_monthly.csv"

# Airline label in the schedule rows -> name used in the O3 tables.
ROUTE_LABELS = {
    "Vistara": "Vistara",
    "Akasa Air": "Akasa Air",
    "TruJet": "TruJet",
    "Star Air": "Star Air",
    "FLY91": "Fly91",
    "FlyBig": "Flybig",
    "Zoom Air": "Zoom Air",
    "IndiaOne Air": "India One Air",
    "Air Deccan": "Air Deccan",
}

# The other seven entrants are the regional entrants.
SCALE_ENTRANTS = {"Vistara", "Akasa Air"}
NUMBER_WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]

# Monthly check: airline (schedule label), month, and a pair shown as a worked example.
CHECK_AIRLINE, CHECK_YEAR, CHECK_MONTH, CHECK_PAIR = "TruJet", 2019, 11, "MAA-SXV"
# A pair is screened in when its directions' departures differ by at most this share.
DIRECTED_GAP_PCT = 3.0


def last_sunday(year: int, month: int) -> date:
    day = date(year, month, calendar.monthrange(year, month)[1])
    return day - timedelta(days=(day.weekday() + 1) % 7)


def season_window(year: int, season: str) -> tuple[date, date]:
    """Return the inclusive start and end dates of an IATA season."""
    if season == "summer":
        return last_sunday(year, 3), last_sunday(year, 10) - timedelta(days=1)
    return last_sunday(year, 10), last_sunday(year + 1, 3) - timedelta(days=1)


def count_operating_dates(operating_days: str, first: date, last: date) -> int:
    """Count dates from first to last whose ISO weekday is in operating_days."""
    span = (last - first).days + 1
    if span <= 0:
        return 0
    total = 0
    for weekday in {int(day) - 1 for day in operating_days}:
        offset = (weekday - first.weekday()) % 7
        if offset < span:
            total += (span - 1 - offset) // 7 + 1
    return total


def load_rows() -> pd.DataFrame:
    rows = pd.read_csv(ROWS, dtype={"operating_days": str})
    rows["pair"] = [
        "-".join(sorted(pair)) for pair in zip(rows["origin"], rows["destination"])
    ]
    rows["ef"] = pd.to_datetime(rows["effective_from"]).dt.date
    rows["et"] = pd.to_datetime(rows["effective_to"]).dt.date
    # Leading zeros differ between publications of the same flight.
    rows["flight"] = rows["flight_number"].str.replace(
        r"^([A-Z0-9]{2})0+(?=\d)", r"\1", regex=True
    )
    return rows.drop_duplicates(
        ["airline", "flight", "origin", "destination", "operating_days", "ef", "et"]
    )


def departures_in(rows: pd.DataFrame, start: date, end: date) -> pd.Series:
    """Departures of each row within [start, end], using validity dates and weekdays."""
    return pd.Series(
        [
            count_operating_dates(row.operating_days, max(row.ef, start), min(row.et, end))
            for row in rows.itertuples()
        ],
        index=rows.index,
    )


def season_label(year: int, season: str) -> str:
    return f"{season.capitalize()} {year}"


def selected_seasons(national: pd.DataFrame, summary: pd.DataFrame) -> dict:
    """Pick each entrant's latest recovered season before closure or merger, else latest."""
    chosen = {}
    for airline in ENTRANTS:
        last_month = national.loc[national["airline"] == airline, "date"].max()
        recovered = summary[summary["airline"] == airline]
        usable = []
        for year, season in zip(recovered["season_year"], recovered["season"]):
            start, end = season_window(year, season)
            if OUTCOMES[airline] == "Merged" and end >= VISTARA_MERGER:
                continue
            if OUTCOMES[airline] == "Ceased" and pd.Timestamp(start) > last_month + pd.offsets.MonthEnd(0):
                continue
            usable.append((start, year, season))
        chosen[airline] = max(usable)[1:]
    return chosen


def season_results(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows, detail_rows = [], []
    for (year, season), season_data in rows.groupby(["season_year", "season"]):
        start, end = season_window(year, season)
        # Only pairs an entrant serves contribute to the entrant measures.
        entrant_pairs = set(season_data.loc[season_data["airline"].isin(ROUTE_LABELS), "pair"])
        group = season_data[season_data["pair"].isin(entrant_pairs)].copy()
        group["dep"] = departures_in(group, start, end)

        pair_airline = group.groupby(["pair", "airline"])["dep"].sum().reset_index()
        pair_airline = pair_airline[pair_airline["dep"] > 0]
        if pair_airline.empty:
            continue

        route_totals = pair_airline.groupby("pair")["dep"].sum().rename("tot")
        pair_airline = pair_airline.join(route_totals, on="pair")
        pair_airline["sh"] = 100 * pair_airline["dep"] / pair_airline["tot"]
        recorded_airlines = season_data["airline"].nunique()

        for airline_code, airline_name in ROUTE_LABELS.items():
            entrant_routes = pair_airline[pair_airline["airline"] == airline_code]
            if entrant_routes.empty:
                continue

            summary_rows.append({
                "airline": airline_name,
                "season_year": year,
                "season": season,
                "window": f"{start}..{end}",
                "pairs": len(entrant_routes),
                "season_departures": int(entrant_routes["dep"].sum()),
                "pairs_half_or_more": int((entrant_routes["sh"] >= 50).sum()),
                "pairs_sole": int((entrant_routes["sh"] >= 99.9999).sum()),
                "median_share": round(entrant_routes["sh"].median(), 1),
                "n_recorded_airlines": recorded_airlines,
            })
            for route in entrant_routes.itertuples():
                detail_rows.append({
                    "airline": airline_name,
                    "season_year": year,
                    "season": season,
                    "pair": route.pair,
                    "entrant_deps": int(route.dep),
                    "route_deps": int(route.tot),
                    "share": round(route.sh, 1),
                })
    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def write_selected_tables(selected: pd.DataFrame) -> pd.DataFrame:
    """Write the route table rows for the report and return the regional totals."""
    write_latex_rows([
        latex_row(
            row.airline, season_label(row.season_year, row.season), row.pairs,
            row.pairs_sole, row.pairs_half_or_more,
        )
        for row in selected.itertuples()
    ], "o3_route_summary_rows.tex")

    write_latex_rows([
        latex_row(
            row.airline, season_label(row.season_year, row.season),
            f"{row.season_departures:,}", f"{row.median_share:.1f}", row.n_recorded_airlines,
        )
        for row in selected.itertuples()
    ], "o3_route_inputs_rows.tex")

    regional = selected[~selected["airline"].isin(SCALE_ENTRANTS)]
    ceased = regional[regional["airline"].map(OUTCOMES) == "Ceased"]
    totals = pd.DataFrame([
        {
            "group": name,
            "airlines": len(group),
            "records": int(group["pairs"].sum()),
            "pairs_sole": int(group["pairs_sole"].sum()),
            "pairs_half_or_more": int(group["pairs_half_or_more"].sum()),
        }
        for name, group in (
            ("Regional entrants", regional),
            ("Regional entrants that ceased", ceased),
        )
    ])
    write_latex_rows([
        latex_row(
            f"{NUMBER_WORDS[row.airlines]} {row.group.lower()}", row.records, row.pairs_sole,
            row.pairs_half_or_more,
        )
        for row in totals.itertuples()
    ], "o3_regional_rows.tex")
    return totals


def monthly_check(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """One airline's share of departures on its pairs in one month, with a worked pair."""
    first = date(CHECK_YEAR, CHECK_MONTH, 1)
    last = date(CHECK_YEAR, CHECK_MONTH, calendar.monthrange(CHECK_YEAR, CHECK_MONTH)[1])
    month_rows = rows[(rows["et"] >= first) & (rows["ef"] <= last)]
    airline_pairs = set(month_rows.loc[month_rows["airline"] == CHECK_AIRLINE, "pair"])
    month_rows = month_rows[month_rows["pair"].isin(airline_pairs)].copy()
    month_rows["dep"] = departures_in(month_rows, first, last)
    month_rows["forward"] = month_rows["origin"] < month_rows["destination"]

    by_direction = (
        month_rows.groupby(["pair", "airline", "forward"])["dep"].sum().unstack(fill_value=0)
    )
    by_direction["gap"] = (by_direction[True] - by_direction[False]).abs()
    pairs = pd.concat(
        [
            by_direction.groupby("pair")["gap"].sum().rename("direction_gap"),
            month_rows.groupby("pair")["dep"].sum().rename("route_deps"),
            month_rows[month_rows["airline"] == CHECK_AIRLINE]
            .groupby("pair")["dep"].sum().rename("airline_deps"),
        ],
        axis=1,
    )
    pairs["direction_gap_pct"] = 100 * pairs["direction_gap"] / pairs["route_deps"]
    pairs["share"] = 100 * pairs["airline_deps"] / pairs["route_deps"]
    pairs["screened"] = pairs["direction_gap_pct"] <= DIRECTED_GAP_PCT
    pairs = pairs.reset_index().sort_values("pair")

    example_deps = month_rows[month_rows["pair"] == CHECK_PAIR].groupby("airline")["dep"].sum()
    example_shares = 100 * example_deps / example_deps.sum()

    traffic = pd.read_csv(CITY_PAIR_TRAFFIC)
    origin, destination = CHECK_PAIR.split("-")
    on_pair = (
        ((traffic["origin"] == origin) & (traffic["destination"] == destination))
        | ((traffic["origin"] == destination) & (traffic["destination"] == origin))
    )
    in_month = (traffic["year"] == CHECK_YEAR) & (traffic["month"] == CHECK_MONTH)

    national = load_national_shares()
    national_share = national[
        (national["airline"] == ROUTE_LABELS[CHECK_AIRLINE])
        & (national["date"] == pd.Timestamp(first))
    ]["share"].iloc[0]

    example = {
        "flights": int(example_deps.sum()),
        "airline_share_pct": float(example_shares.get(CHECK_AIRLINE, 0.0)),
        "hhi": float((example_shares ** 2).sum()),
        "pair_passengers": int(traffic.loc[on_pair & in_month, "passengers"].sum()),
        "airline_national_share_pct": float(national_share),
    }
    return pairs, example


def main() -> None:
    rows = load_rows()
    summary, detail = season_results(rows)
    chosen = selected_seasons(load_national_shares(), summary)

    summary["selected"] = [
        chosen[airline] == (year, season)
        for airline, year, season in zip(summary["airline"], summary["season_year"], summary["season"])
    ]
    detail = detail.merge(
        summary[["airline", "season_year", "season", "selected"]],
        on=["airline", "season_year", "season"],
    )
    selected = summary[summary["selected"]].copy()
    selected["airline"] = pd.Categorical(selected["airline"], ENTRANTS, ordered=True)
    selected = selected.sort_values("airline").reset_index(drop=True)
    selected["airline"] = selected["airline"].astype(str)

    TABLES.mkdir(parents=True, exist_ok=True)
    summary.to_csv(TABLES / "route9_fullseason_summary.csv", index=False)
    detail.to_csv(TABLES / "route9_fullseason_detail.csv", index=False)
    selected.to_csv(TABLES / "route9_selected_season_summary.csv", index=False)
    totals = write_selected_tables(selected)

    pairs, example = monthly_check(rows)
    pairs.to_csv(TABLES / "route9_monthly_check.csv", index=False)
    pd.DataFrame([{"pair": CHECK_PAIR, **example}]).to_csv(
        TABLES / "route9_monthly_example.csv", index=False
    )
    screened = pairs[pairs["screened"]]

    print("O3 entrant route presence by IATA season")
    print(f"Input: {ROWS.relative_to(O3.parent)}")
    print("Share = entrant departures / all recorded departures on the airport pair (%).")
    print("Selected season = latest season before closure or merger, else latest available.\n")
    print(selected.drop(columns=["selected", "season_year"]).to_string(index=False))
    print(
        f"\nSelected-season airline-pair records: {int(selected['pairs'].sum())} "
        f"({len(summary)} airline-seasons and {len(detail)} airline-season-pair "
        "records across all seasons)."
    )
    print("\nRegional entrant totals (selected seasons):")
    print(totals.to_string(index=False))

    print(f"\nMonthly check: {CHECK_AIRLINE}, {date(CHECK_YEAR, CHECK_MONTH, 1):%B %Y}")
    print(
        f"Pairs served {len(pairs)}; screened (directions differ by at most "
        f"{DIRECTED_GAP_PCT:g}% of departures) {len(screened)}; {CHECK_AIRLINE} supplied "
        f"at least half the flights on {int((screened['share'] >= 50).sum())}."
    )
    print(
        f"Example {CHECK_PAIR}: {example['flights']} flights, {CHECK_AIRLINE} share "
        f"{example['airline_share_pct']:.1f}%, HHI {example['hhi']:,.0f}, "
        f"{example['pair_passengers']:,} passengers, {CHECK_AIRLINE} national share "
        f"{example['airline_national_share_pct']:.2f}%."
    )
    print(f"\nSaved 5 CSVs and 3 LaTeX files in {O3.name}/output/tables/.")


if __name__ == "__main__":
    main()

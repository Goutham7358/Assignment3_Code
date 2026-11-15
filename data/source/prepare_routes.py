"""Build monthly route CSVs from extracted DGCA schedule rows."""

import calendar
import json
import re
from collections import Counter, defaultdict
from datetime import date, timedelta

from prepare_national import ownership_group
from route_common import DATA, INTERIM, PROCESSED, read_csv, select_top20, write_csv


FIRST_MONTH = date(2019, 4, 1)
LAST_MONTH = date(2026, 9, 1)
MAX_ENDPOINT_DIFFERENCE_PCT = 5
MIN_ROUTES_PER_MONTH = 10


def calendar_months():
    month = FIRST_MONTH
    while month <= LAST_MONTH:
        yield month
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)


def flight_identity(airline, flight, day):
    """Apply the documented Jet, Go First and Vistara adjustments."""
    if airline in {"Jet Airways", "JetLite"} and day > date(2019, 4, 17):
        return None
    if airline == "Go First / GoAir" and day >= date(2023, 5, 3):
        return None
    if airline == "Vistara" and day >= date(2024, 11, 12):
        number = str(int(re.sub(r"^UK", "", flight)))
        airline, flight = "Air India", "AI2" + number.zfill(3)
    match = re.fullmatch(r"([A-Z0-9]{2})(\d+)([A-Z]?)", flight)
    if match:
        flight = match[1] + str(int(match[2])) + match[3]
    return airline, flight


def route_group(airline, month):
    # This combined source label refers to a renamed airline, not two rivals.
    if month >= date(2022, 1, 1) and airline == "AirAsia India / AIX Connect":
        return "Air India Group"
    return ownership_group(airline, month)


def prepare_source_rows(inventory):
    sources = {item["filename"]: item for item in inventory}
    rows = read_csv(INTERIM / "schedule_rows.csv")
    for row in rows:
        source = sources[row["source_file"]]
        row["route"] = "-".join(sorted((row["station_iata"], row["other_airport"])))
        row["first_day"] = max(date.fromisoformat(row["effective_from"]), date.fromisoformat(source["season_start"]))
        row["last_day"] = min(date.fromisoformat(row["effective_to"]), date.fromisoformat(source["season_end"]))
    return rows


def source_gaps(route, first, last, gaps, star_winter_2022):
    reasons = [gap["reason"] for gap in gaps if gap["route"] in {"ALL", route}
               and gap["first_day"] <= last and gap["last_day"] >= first]
    if route == "BLR-HYD" and not star_winter_2022:
        if first <= date(2023, 3, 25) and last >= date(2022, 10, 30):
            reasons.append("Star Air Winter 2022 filing unavailable")
    return reasons


def month_counts(rows, available_routes, first, last):
    """Expand weekdays into dates; count each flight-date-directed leg once."""
    events = {"departure": set(), "arrival": set()}
    references = defaultdict(set)
    duplicates = 0
    for row in rows:
        if row["route"] not in available_routes or row["last_day"] < first or row["first_day"] > last:
            continue
        if row["direction"] == "departure":
            origin, destination = row["station_iata"], row["other_airport"]
        else:
            origin, destination = row["other_airport"], row["station_iata"]
        day = max(first, row["first_day"])
        final_day = min(last, row["last_day"])
        while day <= final_day:
            if str(day.isoweekday()) in row["operating_days"]:
                identity = flight_identity(row["airline"], row["flight_number"], day)
                if identity:
                    airline, flight = identity
                    event = (row["route"], airline, flight, origin, destination, day)
                    if row["direction"] == "departure" and event in events["departure"]:
                        duplicates += 1
                    events[row["direction"]].add(event)
                    if row["direction"] == "departure":
                        references[row["route"]].add(row["source_file"])
            day += timedelta(days=1)

    counts = {direction: defaultdict(Counter) for direction in events}
    directions = defaultdict(Counter)
    for direction, dated_flights in events.items():
        for route, airline, flight, origin, destination, day in dated_flights:
            counts[direction][route][airline] += 1
            if direction == "departure":
                directions[(route, airline)][origin] += 1
    return counts, directions, duplicates, references


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    routes = select_top20()
    inventory = json.loads((INTERIM / "source_manifest.json").read_text())
    rows = prepare_source_rows(inventory)
    gaps = read_csv(DATA / "raw/route_coverage_gaps.csv")
    for gap in gaps:
        gap["first_day"] = date.fromisoformat(gap["first_date"])
        gap["last_day"] = date.fromisoformat(gap["last_date"])
    exclusions = {(row["month"], row["route"]): row["reason"]
                  for row in read_csv(DATA / "raw/route_month_exclusions.csv")}
    star_winter_2022 = any(item.get("year") == 2022 and item.get("season") == "winter"
                           and item.get("airline") == "Star Air" for item in inventory)
    monthly, airline_rows, group_rows, coverage, before_screen = [], [], [], [], []
    duplicate_days = 0
    used_sources = set()

    for first in calendar_months():
        last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
        month = first.strftime("%Y-%m")
        month_coverage = {}
        for route in routes:
            reasons = source_gaps(route["route"], first, last, gaps, star_winter_2022)
            month_coverage[route["route"]] = {
                "month": month, "route": route["route"], "rank_2025": route["rank_2025"],
                "full_month_source_coverage": not reasons, "retained": False,
                "reason": "; ".join(reasons),
            }
        available = {route for route, row in month_coverage.items() if row["full_month_source_coverage"]}
        counts, directions, duplicates, references = month_counts(rows, available, first, last)
        duplicate_days += duplicates
        candidates, month_airlines, month_groups = [], [], []
        for route in routes:
            name = route["route"]
            if name not in available:
                continue
            brands = counts["departure"][name]
            total = sum(brands.values())
            if not total:
                raise ValueError(f"No departure rows for source-covered pair {name}, {month}.")
            groups = Counter()
            for airline, flights in sorted(brands.items()):
                group = route_group(airline, first)
                groups[group] += flights
                month_airlines.append({
                    "month": month, "route": name, "airline": airline, "ownership_group": group,
                    "flights_a_to_b": directions[(name, airline)][route["airport_a"]],
                    "flights_b_to_a": directions[(name, airline)][route["airport_b"]],
                    "scheduled_flights": flights, "route_flights": total,
                    "frequency_share_pct": 100 * flights / total,
                })
            ranked = sorted(groups.items(), key=lambda item: (-item[1], item[0]))
            for rank, (group, flights) in enumerate(ranked, 1):
                month_groups.append({
                    "month": month, "route": name, "ownership_group": group, "rank": rank,
                    "scheduled_flights": flights, "route_flights": total,
                    "frequency_share_pct": 100 * flights / total,
                })
            arrivals = counts["arrival"][name]
            difference = sum(abs(brands[airline] - arrivals[airline]) for airline in set(brands) | set(arrivals))
            result = {
                "month": month, "route": name, "rank_2025": route["rank_2025"],
                "scheduled_flights_both_directions": total,
                "brand_frequency_hhi": 10000 * sum((brands[airline] / total) ** 2 for airline in sorted(brands)),
                "group_frequency_hhi": 10000 * sum((groups[group] / total) ** 2 for group in sorted(groups)),
                "group_cr2_pct": 100 * sum(flights for group, flights in ranked[:2]) / total,
                "largest_group": ranked[0][0], "group_count": len(groups),
                "endpoint_absolute_count_difference": difference,
                "endpoint_difference_pct": 100 * difference / total,
                "endpoint_counts_match": brands == arrivals,
            }
            before_screen.append(result)
            status = month_coverage[name]
            if (month, name) in exclusions:
                status["reason"] = exclusions[(month, name)]
            elif result["endpoint_difference_pct"] > MAX_ENDPOINT_DIFFERENCE_PCT:
                status["reason"] = "airline endpoint-count difference exceeds 5 percent"
            else:
                candidates.append(result)
        if len(candidates) < MIN_ROUTES_PER_MONTH:
            for row in candidates:
                month_coverage[row["route"]]["reason"] = "fewer than ten routes pass the monthly source-quality screen"
            candidates = []
        retained = {row["route"] for row in candidates}
        for name in retained:
            month_coverage[name]["retained"] = True
            used_sources.update(references[name])
        monthly.extend(candidates)
        airline_rows.extend(row for row in month_airlines if row["route"] in retained)
        group_rows.extend(row for row in month_groups if row["route"] in retained)
        coverage.extend(month_coverage.values())

    # Check that the two directional counts and the two aggregation levels agree.
    by_pair = defaultdict(list)
    for row in airline_rows:
        if row["flights_a_to_b"] + row["flights_b_to_a"] != row["scheduled_flights"]:
            raise ValueError("Directional flight totals do not agree.")
        by_pair[(row["month"], row["route"])].append(row)
    for row in monthly:
        components = by_pair[(row["month"], row["route"])]
        if sum(item["scheduled_flights"] for item in components) != row["scheduled_flights_both_directions"]:
            raise ValueError("Airline flight totals do not agree.")
        if abs(sum(item["frequency_share_pct"] for item in components) - 100) > 1e-8:
            raise ValueError("Frequency shares do not add to 100.")
        if not 0 < row["brand_frequency_hhi"] <= row["group_frequency_hhi"] + 1e-8 <= 10000 + 1e-8:
            raise ValueError("Concentration index outside its bounds.")

    write_csv(PROCESSED / "top20_routes.csv", routes)
    write_csv(PROCESSED / "route_monthly.csv", monthly)
    write_csv(PROCESSED / "airline_route_monthly.csv", airline_rows)
    write_csv(PROCESSED / "group_route_monthly.csv", group_rows)
    write_csv(PROCESSED / "route_coverage.csv", coverage)
    write_csv(PROCESSED / "route_monthly_before_screen.csv", before_screen)
    write_csv(PROCESSED / "source_pdfs_used.csv", [
        {key: item[key] for key in ["filename", "path", "airline", "year", "season", "sha256", "source_url"]}
        for item in inventory if item["filename"] in used_sources
    ])
    per_month = Counter(row["month"] for row in monthly)
    audit = {
        "first_month": min(per_month), "last_month": max(per_month),
        "candidate_calendar_months": len(list(calendar_months())),
        "observed_months": len(per_month), "route_months": len(monthly),
        "selected_pairs": len(routes), "minimum_routes_per_observed_month": min(per_month.values()),
        "source_pdfs_contributing_departure_rows": len(used_sources),
        "maximum_routes_per_observed_month": max(per_month.values()),
        "months_with_all20": sum(count == 20 for count in per_month.values()),
        "exact_endpoint_match_route_months": sum(row["endpoint_counts_match"] for row in monthly),
        "pre_screen_route_months": len(before_screen),
        "documented_route_month_exclusions": list(exclusions.keys()),
        "duplicate_departure_days_collapsed_before_screen": duplicate_days,
        "endpoint_tolerance_pct": MAX_ENDPOINT_DIFFERENCE_PCT,
        "minimum_routes_per_month_rule": MIN_ROUTES_PER_MONTH,
        "share_basis": "approved scheduled departure frequency; both directions combined",
    }
    (PROCESSED / "preparation_summary.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Prepared {len(monthly):,} route-months across {len(per_month)} months.")


if __name__ == "__main__":
    main()

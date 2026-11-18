"""Extract every airline's departure rows from the DGCA schedule PDFs for O3.

Rows for all airport pairs are kept so entrants' route shares can be measured.
The PDFs name each station by city, so station IATA codes are inferred from
matched departure/arrival pairs of the same flight.
"""

import json
import re
import shutil
from collections import Counter, defaultdict

from extract_route_schedules import CITIES, pdf_extract
from route_common import DATA, INTERIM, write_csv

# Flight, publication and validity dates identify one leg in both directions.
LEG_KEY = ("source_file", "flight_number", "effective_from", "effective_to")


def normalise_station(name):
    return re.sub(r"\s+", " ", name.upper()).strip()


def infer_station_codes(rows):
    """Map station names to IATA codes by voting over matched flight legs."""
    departures = defaultdict(list)
    arrivals = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in LEG_KEY)
        target = departures if row["direction"] == "departure" else arrivals
        target[key].append(row)

    votes = defaultdict(Counter)
    for key, departing in departures.items():
        arriving = arrivals.get(key)
        # Multi-leg flight numbers are ambiguous, so use only one-to-one matches.
        if len(departing) != 1 or not arriving or len(arriving) != 1:
            continue
        dep, arr = departing[0], arriving[0]
        votes[normalise_station(dep["station"])][arr["other_airport"]] += 1
        votes[normalise_station(arr["station"])][dep["other_airport"]] += 1

    codes = {}
    for station, counter in votes.items():
        ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        codes[station] = (ranked[0][0], ranked[0][1], sum(counter.values()))
    # Hard-coded city codes from the shared extractor take precedence.
    for city, code in CITIES.items():
        _, top, total = codes.get(city, (code, 0, 0))
        codes[city] = (code, top, total)
    return codes


def main():
    if shutil.which("pdftotext") is None:
        raise SystemExit("Install Poppler first; this script needs pdftotext.")
    manifest = json.loads((DATA / "raw/route_schedule_manifest.json").read_text())

    rows = []
    for number, original in enumerate(manifest, 1):
        extracted, _, _ = pdf_extract(dict(original))
        rows.extend(extracted)
        if number % 20 == 0 or number == len(manifest):
            print(f"Read {number}/{len(manifest)} PDFs; {len(rows):,} rows.", flush=True)

    codes = infer_station_codes(rows)
    write_csv(
        INTERIM / "o3_station_codes.csv",
        [
            {"station": station, "iata": code, "matched_votes": top, "all_votes": total}
            for station, (code, top, total) in sorted(codes.items())
        ],
    )

    departures, unmapped = [], 0
    for row in rows:
        if row["direction"] != "departure":
            continue
        origin = codes.get(normalise_station(row["station"]), ("",))[0]
        if not origin:
            unmapped += 1
            continue
        departures.append({
            "source_file": row["source_file"],
            "airline": row["airline"],
            "flight_number": row["flight_number"],
            "operating_days": row["operating_days"],
            "origin": origin,
            "destination": row["other_airport"],
            "effective_from": row["effective_from"],
            "effective_to": row["effective_to"],
            "season_year": row["season_year"],
            "season": row["season"],
        })
    departures.sort(key=lambda row: (
        row["source_file"], row["flight_number"], row["origin"], row["destination"],
        row["effective_from"],
    ))
    write_csv(INTERIM / "o3_schedule_rows.csv", departures)
    print(
        f"Saved {len(departures):,} departure rows; "
        f"{unmapped:,} had no station code and were dropped."
    )


if __name__ == "__main__":
    main()

"""Check source fingerprints, earlier results and independently recomputed HHI."""

import hashlib
import json
import math
import sqlite3

from route_common import DATA, PROCESSED, read_csv


def main():
    manifest = json.loads((DATA / "raw/route_schedule_manifest.json").read_text())
    for item in manifest:
        if hashlib.sha256((DATA / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("PDF fingerprint changed: " + item["filename"])
    evidence = json.loads((DATA / "raw/route_evidence_manifest.json").read_text())
    for item in evidence:
        if hashlib.sha256((DATA / "raw" / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Supporting document fingerprint changed: " + item["path"])

    monthly = read_csv(PROCESSED / "route_monthly.csv")
    by_pair = {(row["month"], row["route"]): row for row in monthly}
    if len(by_pair) != len(monthly):
        raise ValueError("Duplicate route-month in the prepared data.")
    reference = {(row["month"], row["route"]): row for row in read_csv(
        DATA / "reference/route_monthly_before_trujet_review.csv"
    )}
    excluded = {(row["month"], row["route"]) for row in read_csv(DATA / "raw/route_month_exclusions.csv")}
    if set(by_pair) != set(reference) - excluded:
        raise ValueError("Unexpected change in the earlier route sample.")
    for key, row in by_pair.items():
        old = reference[key]
        if row["scheduled_flights_both_directions"] != old["scheduled_flights_both_directions"]:
            raise ValueError(f"Flight total differs from earlier project: {key}")
        for measure in ["brand_frequency_hhi", "group_frequency_hhi", "group_cr2_pct"]:
            if not math.isclose(float(row[measure]), float(old[measure]), abs_tol=1e-7, rel_tol=0):
                raise ValueError(f"Earlier result differs: {key}, {measure}")

    # SQL aggregates the airline CSV separately from the preparation functions.
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE flights (month TEXT, route TEXT, owner TEXT, n INTEGER)")
    connection.executemany("INSERT INTO flights VALUES (?,?,?,?)", [
        (row["month"], row["route"], row["ownership_group"], int(row["scheduled_flights"]))
        for row in read_csv(PROCESSED / "airline_route_monthly.csv")
    ])
    query = """
        WITH groups AS (
            SELECT month, route, owner, SUM(n) AS n
            FROM flights GROUP BY month, route, owner
        ), totals AS (
            SELECT *, SUM(n) OVER (PARTITION BY month, route) AS total FROM groups
        )
        SELECT month, route, SUM(n), SUM(10000.0 * n * n / total / total)
        FROM totals GROUP BY month, route ORDER BY month, route
    """
    recomputed = connection.execute(query).fetchall()
    connection.close()
    if len(recomputed) != len(monthly):
        raise ValueError("SQL and prepared data cover different route-months.")
    for month, route, total, hhi in recomputed:
        row = by_pair[(month, route)]
        if total != int(row["scheduled_flights_both_directions"]):
            raise ValueError("Independent flight totals differ.")
        if not math.isclose(hhi, float(row["group_frequency_hhi"]), abs_tol=1e-7, rel_tol=0):
            raise ValueError("Independently calculated group HHI differs.")

    # The original Akasa filing lists daily flights in both directions; its
    # complementary weekday rows jointly give 120 Delhi-Pune flights in June.
    example = [row for row in read_csv(PROCESSED / "airline_route_monthly.csv")
               if row["month"] == "2026-06" and row["route"] == "DEL-PNQ"]
    akasa = next(row for row in example if row["airline"] == "Akasa Air")
    if int(akasa["scheduled_flights"]) != 120 or sum(int(row["scheduled_flights"]) for row in example) != 1430:
        raise ValueError("Delhi-Pune worked example differs from the checked original schedule.")

    result = {
        "passed": True, "pdf_fingerprints_checked": len(manifest),
        "supporting_document_fingerprints_checked": len(evidence),
        "route_months_compared_with_previous_project": len(monthly),
        "route_months_with_independent_sql_hhi_check": len(recomputed),
        "documented_exclusions": sorted(excluded),
        "worked_example": {"month": "2026-06", "route": "DEL-PNQ",
                           "akasa_flights": 120, "all_airline_flights": 1430},
    }
    (PROCESSED / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Verified {len(manifest)} PDF fingerprints and {len(monthly):,} route-months.")


if __name__ == "__main__":
    main()

# Data preparation

Prepared CSVs are included in [data/processed/](../processed/). The commands
below rebuild them from the national source CSV and the 228 original DGCA
schedule PDFs bundled with the repository.

The O4 runner prepares missing inputs automatically. To force a complete rebuild,
run `python O4/run_analysis.py --rebuild-data` from the repository root.

Complete the [shared Python setup](../../README.md#setup). PDF extraction also
requires Poppler's `pdftotext` on your PATH. Run these steps from the repository
root in the order shown.

| Command | Output |
|---|---|
| `python data/source/prepare_national.py` | [National airline-month CSV](../processed/national_airline_monthly.csv) and preparation audit |
| `python data/source/prepare_capacity.py` | [Capacity airline-month CSV](../processed/capacity_airline_monthly.csv) and validity flags |
| `python data/source/extract_route_schedules.py` | [Extracted schedule rows](../interim/routes/schedule_rows.csv), with PDF/page/row references, and extraction audit |
| `python data/source/prepare_routes.py` | [Route CSVs](../processed/routes/), including airline counts, ownership-group counts, concentration and coverage |
| `python data/source/verify_routes.py` | [Verification results](../processed/routes/verification.json) for PDF fingerprints, route totals and independent SQL HHI checks |

National preparation selects positive-passenger scheduled-domestic records.
Route preparation expands service dates and operating weekdays, deduplicates
flight/date/direction records, combines directions and applies the documented
coverage checks and exclusions. The resulting counts describe scheduled flights,
not actual operations or route-level airline passenger shares.

These preparation steps supply O4. O1 and O2 apply their own study filters to
the same national source CSV within their analysis workflows. Rerun the relevant
analysis commands after rebuilding its inputs.

Source versions, units and ownership conventions are in
[SOURCE.md](../SOURCE.md). Schedule sources, selection rules and exclusions are
in [ROUTE_SOURCES.md](../ROUTE_SOURCES.md).

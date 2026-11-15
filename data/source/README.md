# Preparing data before analysis

Data preparation lives here. O4's analysis scripts read prepared CSV files, rather than reading source PDFs or downloading data.

To generate all three figures from the included prepared data, run `python3 O4/EDA/generate_figures.py` from the repository root. The steps below are for rebuilding the prepared data itself.

## National data: implemented

Run from the repository root:

```sh
python3 data/source/prepare_national.py
```

Input: `data/raw/carrier_monthly.csv`, the unchanged DGCA-derived upstream snapshot.

Outputs:

- `data/processed/national_airline_monthly.csv`: positive scheduled-domestic airline-months, with ownership groups.
- `data/processed/national_preparation.json`: source fingerprint, exclusions, row counts and missing months.

The preparation script uses only Python's standard library. See `data/SOURCE.md` for the ownership convention, data dictionary and upstream attribution.

## Route data: implemented

The existing project's PDF table parser has been adapted for this repository. All inputs are included. The extraction step also needs Poppler's `pdftotext` on your PATH; no extra Python package is required for preparation.

Run from the repository root:

```sh
python3 data/source/extract_route_schedules.py
python3 data/source/prepare_routes.py
python3 data/source/verify_routes.py
python3 O4/EDA/eda_routes.py
```

The intermediate and prepared CSVs are already included. To redraw only the chart, run the last command. To rebuild the prepared CSVs without rereading PDFs, start at `prepare_routes.py`.

The preparation has two stages:

1. **Extract PDF tables into CSV.** Preserve airline, flight number, airport, arrival/departure direction, weekday mask, validity dates, source URL, PDF fingerprint, page and row. Poppler's `pdftotext` is required by the existing parser.
2. **Prepare monthly CSVs.** Expand validity dates and weekdays, deduplicate flight-date-leg records, apply documented operational adjustments, combine directions, and apply the submitted coverage and endpoint-consistency checks. Keep missing route-months missing.

The top-20 selection also needs the 2025 airport-pair passenger data. That file selects routes; it does not contain airline passenger shares. The schedule PDFs yield approved flight frequencies, not operated flights or route-level airline passenger counts.

The two affected HYD-MAA observations in February-March 2022 are excluded as whole route-months. The new panel has 1,150 route-months; the earlier panel had 1,152. Other retained flight totals and concentration indices agree with the earlier project. See `data/ROUTE_SOURCES.md` for the decisions, data dictionary and checks.

## Example of the prepared route data

Selected columns from `data/processed/routes/airline_route_monthly.csv`:

```csv
month,route,airline,scheduled_flights,route_flights
2026-06,DEL-PNQ,Air India,472,1430
2026-06,DEL-PNQ,Air India Express,146,1430
2026-06,DEL-PNQ,Akasa Air,120,1430
2026-06,DEL-PNQ,IndiGo,524,1430
2026-06,DEL-PNQ,SpiceJet,168,1430
```

These are both-direction scheduled-departure counts for Delhi-Pune. For example, Akasa has `120 / 1430 * 100 = 8.39%` of the recorded scheduled flights. The full CSV also contains ownership groups, counts in each direction and unrounded percentage shares. `route_monthly.csv` contains the corresponding pair-month HHI, CR2 and quality fields. Extracted PDF rows, including weekdays, validity dates and page references, are kept separately in `data/interim/routes/schedule_rows.csv`.

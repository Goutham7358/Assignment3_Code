# Preparing data before analysis

Data preparation lives here. O4's analysis scripts read prepared CSV files, rather than reading source PDFs or downloading data.

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
python3 O4/eda_routes.py
```

The intermediate and prepared CSVs are already included. To redraw only the chart, run the last command. To rebuild the prepared CSVs without rereading PDFs, start at `prepare_routes.py`.

The preparation has two stages:

1. **Extract PDF tables into CSV.** Preserve airline, flight number, airport, arrival/departure direction, weekday mask, validity dates, source URL, PDF fingerprint, page and row. Poppler's `pdftotext` is required by the existing parser.
2. **Prepare monthly CSVs.** Expand validity dates and weekdays, deduplicate flight-date-leg records, apply documented operational adjustments, combine directions, and apply the submitted coverage and endpoint-consistency checks. Keep missing route-months missing.

The top-20 selection also needs the 2025 airport-pair passenger data. That file selects routes; it does not contain airline passenger shares. The schedule PDFs yield approved flight frequencies, not operated flights or route-level airline passenger counts.

The two affected HYD-MAA observations in February-March 2022 are excluded as whole route-months. The new panel has 1,150 route-months; the earlier panel had 1,152. Other retained flight totals and concentration indices agree with the earlier project. See `data/ROUTE_SOURCES.md` for the decisions, data dictionary and checks.

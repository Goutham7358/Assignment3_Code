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

## Route data: next preparation task

Route EDA has not started. Its conversion code and inputs have not yet been migrated into this repository. The existing economics project already has a DGCA schedule parser; reuse and verify it here when starting that step.

The route workflow needs two distinct stages:

1. **Extract PDF tables into CSV.** Preserve airline, flight number, airport, arrival/departure direction, weekday mask, validity dates, source URL, PDF fingerprint, page and row. Poppler's `pdftotext` is required by the existing parser.
2. **Prepare monthly CSVs.** Expand validity dates and weekdays, deduplicate flight-date-leg records, apply documented operational adjustments, combine directions, and apply the submitted coverage and endpoint-consistency checks. Keep missing route-months missing.

The top-20 selection also needs the 2025 airport-pair passenger data. That file selects routes; it does not contain airline passenger shares. The schedule PDFs yield approved flight frequencies, not operated flights or route-level airline passenger counts.

Before using route outputs, resolve the existing TruJet observations for HYD-MAA in February-March 2022 and record any resulting sample changes. Do not treat the older route CSV as a newly verified Assignment 3 input.

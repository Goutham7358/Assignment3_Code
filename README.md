# From Fragmentation to Duopoly - Code

**Team Macro Matrix · DA241O: Managerial Economics**

Data preparation and analysis for the study of market concentration and major
consolidation events in Indian domestic aviation, 2015–2026.

## Setup

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use this environment for the commands in all guides below. Rebuilding route
CSVs from PDFs also requires Poppler's `pdftotext` on your PATH.

## Analyses and results

| Analysis | Run from the repository root | Results |
|---|---|---|
| [O1: Concentration and ownership](O1/README.md) | `python O1/export_results_tables.py` | [Numerical tables](O1/results/) and [chart](O1/figures/) |
| [O2: Airline exits and Tata consolidation](O2/README.md) | `python O2/run_analysis.py` | [Numerical tables](O2/output/tables/) and [share-path chart](O2/output/figures/exit_share_paths.png) |
| [O3: Entrant airlines](O3/README.md) | `python O3/run_analysis.py` | [Numerical tables](O3/output/tables/) and [figures](O3/output/figures/) |
| [O4: Concentration and rivals' capacity](O4/README.md) | `python O4/run_analysis.py` | [Numerical tables](O4/output/tables/) and [figures](O4/output/figures/) |

The guides identify the command and output files for each calculation.
Report values may be rounded further than the CSV outputs, producing small
differences in displayed entries and totals.

No cleanup is needed between runs. Commands overwrite their generated results.
The O4 runner creates missing prepared inputs and otherwise reuses them. After
changing source data or preparation rules, run
`python O4/run_analysis.py --rebuild-data` to rebuild those inputs as well.

## Data

The [national source CSV](data/raw/carrier_monthly.csv) preserves the
DGCA-derived data distributed by [Marek Kubicek](https://github.com/mkubicek/india-aviation-stats).
O1, O2 and O3 filter this file within their workflows. O4 reads the included
[prepared CSVs](data/processed/).

The 228 DGCA schedule PDFs in [data/raw/route_schedules/](data/raw/route_schedules/)
have been processed into [airline_route_monthly.csv](data/processed/routes/airline_route_monthly.csv)
for monthly flight counts by airline and airport pair, and
[route_monthly.csv](data/processed/routes/route_monthly.csv) for route-level
concentration measures. These CSVs use scheduled flights, rather than actual
flights operated or passengers carried.

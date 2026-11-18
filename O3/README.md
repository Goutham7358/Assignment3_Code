# O3: Entrant airlines

Follows the nine airlines that entered scheduled domestic service between 2015
and 2026: their national passenger share by months since entry, how long they
operated and how they ended, their share of scheduled departures on their
airport pairs over full IATA seasons, and the revenue growth and margins of the
two that reached national scale.

Complete the [shared setup](../README.md#setup), then run from the repository root:

```sh
python O3/run_analysis.py
```

The command prepares the route inputs if they are missing, applies the study
filters to the [national source CSV](../data/raw/carrier_monthly.csv), prints
every national, route and financial figure used in the report, and regenerates
all outputs below. Missing route inputs are extracted from the 228 bundled DGCA
PDFs, which requires Poppler's `pdftotext`. Results are overwritten, not
appended. To re-extract the route inputs, run
`python O3/run_analysis.py --rebuild-data`.

| Output | Contents |
|---|---|
| [Entrant summary](output/tables/o3_nine_table.csv) | First and last month, months operating, share at 12, 24 and 36 months, peak share, outcome and the meaningful and persistent flags |
| [All brands](output/tables/o3_all_brands_table.csv) | Operating months and peak share for every brand considered |
| [Financial ratios](output/tables/o3_financial_ratios.csv) | Revenue growth, net margins and latest profit after tax for Vistara and Akasa Air |
| [Season summary](output/tables/route9_fullseason_summary.csv) | Pairs served, departures, pairs with half or more of departures, sole-operator pairs and median share, by entrant and season; `selected` marks the season used in the report |
| [Selected seasons](output/tables/route9_selected_season_summary.csv) | The season summary for each entrant's selected season |
| [Route detail](output/tables/route9_fullseason_detail.csv) | Entrant and route departures and entrant share, by entrant, season and airport pair |
| [Monthly check](output/tables/route9_monthly_check.csv) | TruJet's share of departures on each of its pairs in November 2019, with the direction-balance screen, and the [worked example](output/tables/route9_monthly_example.csv) |
| [Report table rows](output/tables/) | LaTeX rows for the report: `o3_summary_rows.tex`, `o3_detail_rows.tex`, `o3_financial_rows.tex`, `o3_route_summary_rows.tex`, `o3_regional_rows.tex` and `o3_route_inputs_rows.tex` |
| [Event-time chart](output/figures/fig_o3_age.png) | Share by months since first service, one panel per entrant, log scale |
| [Lifespan chart](output/figures/fig_o3_lifespans.png) | Months of operation and peak share, coloured by outcome |

Individual steps can also be run separately:
`python O3/Main_Analysis/entrant_analysis.py`,
`python O3/Main_Analysis/route_fullseason.py` or
`python data/source/prepare_o3_routes.py`.

To compare the outputs with a LaTeX report, run
`python O3/check_report.py PATH_TO_main_combined.tex`. It follows the report's
`\input` files, confirms that each generated
table row and the quoted counts appear in the report, and exits with status 1 if
any do not.

## Inputs and interpretation

- [National input](../data/raw/carrier_monthly.csv) keeps scheduled-domestic
  records with positive passengers. A share is an airline's passengers divided by
  all passengers that month, without ownership grouping. `tau` is months since the
  airline's first passenger month, and `t12`, `t24` and `t36` are shares at those
  ages. An entrant is meaningful if its share reaches 1% in any month and
  persistent if it stays at or above 1% for 24 consecutive calendar months; a
  missing month ends a run. Outcomes are assigned in the script. Shares below
  0.0002% are drawn at the axis floor in the event-time chart.
- [Financial input](../data/raw/o3_financial_records.csv) gives operating income
  and profit after tax in Rs crore. Revenue growth is the change in operating
  income, and net margin is profit after tax divided by operating income.
- [Route input](../data/interim/routes/o3_schedule_rows.csv) holds departure
  rows for all airlines and airport pairs. Station codes are inferred from the
  PDFs, as recorded in [o3_station_codes.csv](../data/interim/routes/o3_station_codes.csv).
- Each row is clipped to its IATA season and counts the dates within its
  validity whose weekday it operates; exact duplicate rows are removed. An
  entrant's share is its departures divided by all recorded departures on the
  pair, both directions combined. Only pairs served by an entrant that season are
  measured.
- An entrant's selected season is its latest recovered season before closure or
  merger, or its latest recovered season if it still operates. The selected
  seasons give 229 airline-pair records, summed into the seven regional
  entrants and the four of them that ceased.
- Shares describe scheduled departures among recovered filings;
  `n_recorded_airlines` shows how many airlines appear in each season. A season
  with no recovered entrant filing has no row, and legacy-format publications are
  not used.
- The monthly check counts a pair when airlines' departures differ by direction
  by at most 3% of its departures. The tolerance is a study choice.

Definitions, extraction and station-code rules are in
[data/SOURCE.md](../data/SOURCE.md) and [data/ROUTE_SOURCES.md](../data/ROUTE_SOURCES.md).

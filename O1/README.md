# O1: Concentration and ownership

Calculates monthly brand HHI, ownership HHI and MHHI, then estimates event
regressions and checks changes around airline exits and consolidation.

Complete the [shared setup](../README.md#setup), then run from the repository root:

```sh
python O1/export_results_tables.py
```

This command cleans the [national source CSV](../data/raw/carrier_monthly.csv),
saves the prepared data, and regenerates the numerical tables and chart.

| Output | Contents |
|---|---|
| [Cleaned input](../data/processed/o1_airline_monthly_clean.csv) | Airline-month records and data-quality flags |
| [Monthly indices](results/o1_monthly_indices.csv) | HHI measures, CR2 and related concentration measures |
| [Regression results](results/o1_table_segmented_regression.csv) | Event coefficients, standard errors and model statistics |
| [Selected-window results](results/o1_table_drift_points.csv) | D1–D7 changes and passenger-share movements |
| [Ownership adjustment](results/o1_table_wedge_summary.csv) | MHHI adjustment and sensitivity summaries |
| [Chart](figures/Index-over-months.png) | Observed concentration and fitted trends |

The [table manifest](results/README_tables_manifest.csv) lists the remaining
period, ownership, cleaning and robustness outputs in [results/](results/).
Cleaning and index calculation can also be run separately with
`python O1/data_cleansing.py` and `python O1/HHI_Index_calculation.py`.

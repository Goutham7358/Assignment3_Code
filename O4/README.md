# O4 exploratory analysis

## Progress

- [x] Preserve and document the national source snapshot.
- [x] Prepare a separate national airline-month CSV with the submitted ownership groups.
- [x] Calculate monthly group shares, CR2, the leader-rival gap, ownership HHI and fringe share.
- [x] Save the numerical values behind the chart and summary statistics for all four concentration measures.
- [x] Draw the first two-panel trend figure and check its appearance.
- [x] Check all 138 monthly totals and CR2 values against the earlier project; independently check CR2 and gaps using a separate SQL aggregation of the source data.
- [x] Rerun from a standalone copy, with prepared files removed and a different working directory; reproduce all prepared files, numerical CSVs and the PNG byte-for-byte.
- [x] Add the figure and descriptive text to Section 4 of the report; compile and visually check the updated page.
- [x] Complete the national descriptive summary, including HHI and fringe share, for Appendix B. Coordinate overlap with O1 at team integration.
- [x] Migrate and verify the route PDF-to-CSV preparation workflow, including the TruJet issue.
- [x] Describe route coverage and the distribution of route concentration in a second two-panel figure, with numerical tables and local Section 4.2 text.
- [x] Describe capacity inputs for December 2024 and December 2025 in Section 4.3, with a generated table and airline-level inputs.

These are EDA tasks. The hypothesis criteria and support assessments will be reported in the main analysis and discussion later.

Code changes are committed and pushed after each completed EDA step. The Overleaf-linked report is currently updated locally; committing and pushing it is deferred until the EDA is ready for review as a whole.

## Generate all EDA figures and tables

The EDA scripts are in `O4/EDA/`. From the repository root, one command reads the included prepared CSVs and generates Figures 1-3, the national descriptive summary, and the capacity-input table:

```sh
python3 O4/EDA/generate_figures.py
```

`eda_national.py` makes Figure 1, the leading-pair summary and national descriptive statistics. `eda_routes.py` makes Figures 2-3. `eda_capacity.py` makes the December capacity-input table. The entry script calls all three. Outputs remain in `O4/output/`. EDA does not reread source PDFs or change the prepared data.

## Set up Python and run the national analysis

Use Python 3.10 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 data/source/prepare_national.py
python3 O4/EDA/eda_national.py
```

The scripts find data relative to their own location, so they can also be run from another working directory. No internet access is needed after the packages are installed. The exact Python, Matplotlib and NumPy versions used for the saved outputs are recorded in `output/software_versions.json`.

The EDA script saves files rather than opening a plotting window. Open `output/figures/national_cr2_share_gap.png` to see the chart; the PDF version is suitable for LaTeX.

The chart uses Computer Modern serif lettering bundled with Matplotlib, matching the report's Latin Modern style. Source attribution is given once below the report caption; the complete dataset provenance is in `data/SOURCE.md`.

## Outputs and definitions

| File under `output/` | Contents |
|---|---|
| `figures/national_cr2_share_gap.png` and `.pdf` | CR2 and share-gap trend panels |
| `tables/national_group_shares.csv` | Each ownership group's passengers, monthly total, rank and passenger share |
| `tables/national_concentration_monthly.csv` | Monthly total, group count, top-two names/shares, CR2 and gap |
| `tables/national_leading_pair_periods.csv` | Runs of the same leading pair, with first/last month and observed-month count |
| `tables/national_eda_summary.csv` | Count, mean, median, sample standard deviation, minimum and maximum of ownership HHI, CR2, gap and fringe |
| `tables/national_summary_table.tex` | Generated LaTeX table body for the Appendix B summary |

In the monthly table, `ownership_hhi` sums squared ownership-group percentage shares. `cr2_pct` adds the two largest shares (percent), `share_gap_pp` subtracts the second from the first (percentage points), and `fringe_share_pct` is 100 minus CR2. Other `_share_pct` fields are passenger percentages. `date` is the first day of each month. Names and ranks are determined each month. Values are saved without display rounding.

Summary statistics weight each observed month equally. They are not passenger-weighted averages or pooled-period passenger shares. April 2020 is absent from the numerical data and is displayed as a gap in the chart. No hypothesis threshold lines or pass/fail classifications are included in this EDA figure.

## First descriptive observations

The series contains 138 observed months from January 2015 to July 2026. CR2 rises from 60.7% to 91.3%, and the share gap rises from 12.5 to 43.4 percentage points. The leading pair is IndiGo and Jet Airways Group at the start, and IndiGo and Air India Group at the end. The two panels therefore track the leading groups in each month, rather than assuming an unchanged pair throughout.

IndiGo is first in all 138 observed months. Second place is Jet Airways Group (January 2015-January 2019, 49 months), SpiceJet (February 2019-April 2021, 26 observed months), Air India Group (May-August 2021, four months), Vistara (September 2021, one month), Go First (October-December 2021, three months), and Air India Group again (January 2022-July 2026, 55 months). These are five distinct pairs across six periods. April 2020 is unobserved, so its identity is not inferred. An independent SQL aggregation of the unchanged source confirms every month's top-two identities.

Across observed months, CR2 ranges from 56.1% to 92.3%; the gap ranges from 11.1 to 49.9 percentage points. The January 2022 movement includes the study's ownership regrouping and should not be attributed entirely to changes in airline passenger volumes.

The figure and a short descriptive paragraph belong in Section 4 of the report. The wider project checklist remains in `Assignment3/assignment3_checklist.md` in the parent economics workspace.

## Route EDA: Section 4.2

The full workflow, starting from the original PDFs, is:

```sh
python3 data/source/extract_route_schedules.py
python3 data/source/prepare_routes.py
python3 data/source/verify_routes.py
python3 O4/EDA/eda_routes.py
```

Poppler's `pdftotext` must be on the PATH for the first command. Python preparation and verification use the standard library. The plotting dependencies are the same as for the national figure. The included intermediate/prepared CSVs let you redraw the figure by running only the final command. See [route source notes](../data/ROUTE_SOURCES.md) for the source URLs, fingerprints, rules and data dictionary.

`output/figures/route_coverage_hhi.png` and `.pdf` contain two panels:

1. Retained airport pairs in each of the 90 calendar months from April 2019 through September 2026. Zero means no usable observation, not zero flights.
2. A histogram of ownership-group frequency HHI across 1,150 observations. One observation is one airport pair in one calendar month: the same pair in two different months counts twice. The horizontal axis contains HHI intervals of 500 points; the vertical axis counts observations in each interval. For example, 278 observations have HHI from 3,500 up to 4,000. The bar heights sum to 1,150. Every observation receives equal weight; unavailable HHIs are omitted rather than set to zero.

The same script also saves `output/figures/route_hhi_heatmap.png` and `.pdf` as a separate figure. The histogram is retained. Both use the same 1,150 HHI values: the histogram pools observations into ranges, while the heatmap preserves each airport pair and month. The histogram is a pooled frequency distribution, not a cumulative distribution.

Heatmap rows follow the fixed 2025 passenger ranking, with city names shown for readability. The 90 columns cover every calendar month from April 2019 through September 2026. Colour uses a shared 0-10,000 HHI scale. The 650 missing or excluded pair-months are grey, with no interpolation. `output/tables/route_hhi_heatmap.csv` saves the 20-by-90 matrix using airport-pair codes and blank cells for unavailable observations.

Read across a row to follow the same pair over time, or down a column to compare pairs in the same month. For example, Mumbai-Delhi's group frequency HHI changes from 2,071.31 in April 2019 to 4,145.95 in September 2026. This remains an approved-schedule measure under the study's ownership convention.

The chart values are in `output/tables/route_coverage_by_month.csv` and `route_hhi_histogram.csv`. `route_coverage_by_pair.csv` gives each pair's observation count and period, and `route_eda_summary.csv` reports the pooled descriptive statistics. The histogram bins have width 500; intervals include the left edge and exclude the right edge, except the last interval, which includes 10,000. Quartiles use linear interpolation.

There are 66 observed months with 12-20 retained pairs each; 14 months include all 20. The median group frequency HHI is 3,710.75 and the middle half lies between 3,179.60 and 4,244.17. These describe recovered approved schedules on selected major routes, not route passenger shares or the national market.

The preparation preserves the existing quality screen and excludes HYD-MAA in February-March 2022 consistently with O3. All 49,951 selected-route extracted rows match the earlier project's extraction, and all 1,150 retained observations agree with its flight totals and indices. A separate SQL aggregation checks every ownership-group HHI. The workflow also checks 228 schedule PDF fingerprints, two supporting parliamentary replies and the Delhi-Pune worked example. The sample change from 1,152 to 1,150 is fully explained by the two exclusions.

A standalone copy, run from a different working directory with the intermediate and prepared route data removed, reproduced the original 19 extraction, preparation, verification and figure/table outputs byte-for-byte from the PDFs. After adding the heatmap, a separate standalone plotting run from the three prepared input CSVs reproduced all nine route EDA figure/table files byte-for-byte, including the unchanged histogram.

## Capacity inputs: Section 4.3

To rebuild the capacity preparation and table:

```sh
python3 data/source/prepare_capacity.py
python3 O4/EDA/eda_capacity.py
```

The first command preserves the same 1,577 positive-passenger scheduled-domestic airline-months as the national panel, keeps source ASK/RPK values in their original thousand-km units, and flags invalid capacity observations. It saves `data/processed/capacity_airline_monthly.csv` and a preparation audit. The two zero-ASK/RPK records remain flagged; neither is in the December comparison.

The second command requires valid inputs for every selected airline and produces:

- `output/tables/capacity_airline_inputs.csv`: the 19 airline records used in December 2024 and December 2025.
- `output/tables/capacity_inputs.csv`: ASK and RPK summed for IndiGo and all other airlines, separately for each month, retaining both thousand-km source units and billion-km display units.
- `output/tables/capacity_inputs_table.tex`: the generated four-row LaTeX table body, displayed to three decimal places.

ASK measures offered seat-km; RPK measures passenger-km carried. Dividing source values by 1,000,000 converts thousands to billions. Other airlines means every retained airline except IndiGo; brands are counted once and totals are not averages. This table introduces the inputs only. The unused-capacity ratio and H7 assessment belong to the main analysis and discussion.

All 138 monthly ownership HHI/fringe values and the four capacity aggregates were independently checked against SQL calculations from the unchanged raw snapshot. A standalone run prepared capacity data from the raw CSV and reproduced all 22 EDA/capacity-preparation outputs byte-for-byte. Existing figure files and the original monthly concentration fields are unchanged.

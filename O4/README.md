# O4 analysis

The working report groups the main analysis under O4, with national results in 5.4.1, route results and the focus-period comparison in 5.4.2, and the capacity buffer in 5.4.3. Compact tables carry the main evidence. Complete condition tables, calculation examples and sampling details remain in Appendix C.

## Main analysis: national concentration

From the repository root, run:

```sh
python3 O4/Main_Analysis/national_concentration.py
```

This step uses only the Python standard library. It reads `data/processed/national_airline_monthly.csv`, aggregates passengers by ownership group and ranks the groups separately each month. It does not require the EDA scripts or their outputs. Run `python3 data/source/prepare_national.py` first if rebuilding the prepared input from the preserved raw CSV.

The script prints a results table in the terminal and saves seven files in `O4/output/tables/`:

| File | Contents |
|---|---|
| `national_results_monthly.csv` | All 138 monthly measures, leading-group identities and condition flags |
| `national_results_summary.csv` | Counts, denominators, percentages and ranges for the full series and December 2024-July 2026 |
| `national_h5_table.tex` | Four H5 condition rows for Section 5.4.1 |
| `national_results_table.tex` | Complete condition table, including HHI and fringe, for Appendix C |
| `national_worked_example.csv` | July 2026 group passenger counts, shares and HHI contributions |
| `national_worked_groups.tex` | Group-input table for the appendix worked example |
| `national_worked_calculations.tex` | Numerical calculations for that example |

Conditions are evaluated before display rounding. `specified_pair` means IndiGo and Air India Group occupy the top two ranks, in either order. `h5_joint` combines that pair with CR2 >=80% and gap >20 percentage points, as specified in Assignment 2. HHI >1,800 and fringe <=20% are supporting descriptions: CR2 and fringe are complements, and CR2 >=80% already implies HHI >=3,200. The gap threshold is study-defined. These are descriptive conditions, not statistical significance tests or a legal definition of duopoly.

Every observed month has equal weight. April 2020 is missing; December 2024-July 2026 has all 20 months. The script stops if the pinned national coverage changes. The January 2022 ownership regrouping remains part of the submitted convention. Counts describe the observed periods and do not establish permanent dominance.

The national result is complete: all three H5 conditions occur in 48/138 full-series months and 20/20 focus-period months. Route and capacity-buffer results are described below. The economic discussion and formal hypothesis review are now drafted in Section 6; the generated outcome table is documented below.

All 138 months' identities, six measures and six flags were checked independently using SQL aggregation of the unchanged raw snapshot, including integer-count comparisons for the CR2, gap and fringe cutoffs. All existing EDA measures agree. A standalone copy containing only this script and its prepared CSV reproduces all seven outputs byte-for-byte from a different working directory.

## Main analysis: route concentration and IndiGo dependence

```sh
python3 O4/Main_Analysis/route_concentration.py
```

This standard-library script reads `data/processed/routes/route_monthly.csv` and `group_route_monthly.csv`. It calculates shares from integer scheduled-flight counts; the first file supplies retained observations and endpoint-match flags. It does not re-extract PDFs or require EDA outputs. To rebuild those inputs from the original schedules, use the extraction, preparation and verification commands in the Route EDA section below.

The terminal output reports the full sample, exact endpoint matches and December 2025. The main result is 1,143/1,150 observations with HHI >1,800 (99.39%). IndiGo supplies >=60% of scheduled flights in 79 observations (6.87%); none has IndiGo as sole operator. These are selected major airport pairs, not India's entire network.

Generated files under `O4/output/tables/`:

| File | Contents |
|---|---|
| `route_results_monthly.csv` | 1,150 observations: group HHI, CR2, gap, fringe, IndiGo share, leading groups, ties and nine condition flags |
| `route_results_summary.csv` | Three sample definitions, their denominators, condition counts/percentages and medians |
| `route_results_by_month.csv` | 66 monthly summaries; `observations` is available pairs in that month |
| `route_results_by_pair.csv` | The same summaries for each of the 20 selected pairs |
| `route_leading_pairs.csv` | Frequencies of unique leading pairs, with boundary ties separate |
| `route_worked_example.csv` | Group flights, shares and HHI contributions for Delhi-Pune, June 2026 |
| `route_results_compact_table.tex` | Five concentration/dependence rows for Section 5.4.2 |
| `route_results_table.tex` | Complete eight-row condition table for Appendix C |
| `route_sensitivity_table.tex` | Subset and December 2025 comparison table body |
| `route_leading_pairs_table.tex` | Complete leading-pair frequency table body |
| `route_worked_groups.tex` | Input table for the worked example |
| `route_worked_calculations.tex` | Numerical calculations for the worked example |

Every retained airport-pair/month has equal weight in pooled percentages. Monthly route percentages instead use each month's available pairs; neither calculation weights by passengers or flights. `*_count` and `*_pct` fields count a condition and divide by `observations`. Medians use unrounded observation values. Missing observations are omitted, not filled with zero.

The flags are HHI >1,800; CR2 >=80%; gap >20 pp; fringe <=20%; IndiGo share >=60%; IndiGo sole operator; the unique IndiGo-AI leading pair; a tie across ranks two and three; and the unique pair jointly meeting CR2/gap conditions. The latter is a route-level descriptive comparison, not a new hypothesis. All thresholds use integer counts before display rounding. CR2 and fringe conditions are equivalent; the rows overlap and should not be added.

Leading groups are ranked separately for each observation. If ranks two and three have equal counts, there is no unique top-two pair: 58 such observations receive a separate category. The `largest_group`/`second_largest_group` fields use alphabetical order to break ties for display; `first_place_groups` and `second_place_groups` preserve all tied names. Unique-pair flags and counts do not use an arbitrary tie-break. There are 730 unique IndiGo-AI pairs, of which 95 also meet the CR2/gap conditions. A tie affects the names, not any numerical concentration measure.

The exact-match subset has 303 observations, and December 2025 has 19 available pairs. Subsets overlap. Endpoint agreement is a consistency check, not proof that every filing exists. In December 2025, Chennai-Hyderabad is the only pair above the 60% IndiGo flag (78.10%); this approved-schedule measure does not describe flights actually operated during disruption.

Independent SQL aggregation of the airline-level prepared CSV confirms all 1,150 totals, leading-group identities, five numerical measures and nine flags. All 66 monthly and 20 pair-level denominators and condition counts were checked against those observations. A standalone copy with only the script and two inputs reproduced all 12 outputs byte-for-byte from a different working directory.

## Matched focus-period comparison

```sh
python3 O4/Main_Analysis/route_focus_period.py
```

This additional calculation compares December 2024-July 2026 in both datasets. It keeps the original full-period H6 results intact. It reads the prepared CSVs through the national and route calculation functions above and uses only the standard library. It saves numerical CSVs and LaTeX table/calculation bodies; copying them into the report and building the PDF is a separate step.

The 20-pair sample is the submitted O4 sample; the busiest 10 are a supplementary check using the first ten ranks in the same fixed 2025 passenger ranking. The retained focus samples contain 350/400 possible observations for the top 20 and 184/200 for the top 10. All 20 months are represented, with missing pairs omitted separately each month. Each retained pair-month has equal weight.

Five CSVs are saved in `O4/output/tables/`: `route_focus_observations.csv` (350 observations with leading-group and signed IndiGo-minus-AI measures), `route_focus_summary.csv` (top 10 and top 20), `route_focus_by_month.csv` (40 monthly summaries), `route_focus_by_pair.csv` (20 pair summaries), and `national_route_focus_comparison.csv` (national and both route samples).

Three generated LaTeX files use those same calculated values: `national_route_focus_table.tex` contains the matched-period comparison for Section 5.4.2, with national, top-20 and top-ten columns clearly identifying passenger versus scheduled-flight data; `route_focus_coverage_table.tex` lists the retained pairs in every focus-period month; `route_focus_counts.tex` shows the joint-condition percentages for the appendix. The latter two are used in Appendix C.4. All five numerical CSVs are unchanged by adding the report outputs; a standalone run reproduces all eight focus-period files byte-for-byte.

The comparison separates shared dominance from asymmetry. In the top 10, IndiGo and AI are the leading pair in 184/184 observations; median CR2 is 89.37% and median gap is 7.69 pp. IndiGo leads uniquely in 86, AI in 94, with four first-place ties. Only 9/184 meet the unique-pair, CR2 >=80% and gap >20 pp conditions with IndiGo leading. Nationally, the corresponding conditions hold in 20/20 months, with median gap 37.35 pp. Matching periods therefore corroborates two-group concentration on the busiest pairs, while showing a more balanced division of scheduled frequency. National shares remain passenger-based and route shares frequency-based.

`indigo_led_joint` adds the requirement that IndiGo ranks first to the existing pair/CR2/gap conditions. `indigo_minus_ai_pp` is signed and can be negative; the usual `share_gap_pp` is largest minus second-largest and is nonnegative. These are different comparisons. Ties for first are recorded separately, never assigned to an airline for leadership counts. Focus results were checked against an independent SQL aggregation of airline counts. A standalone run reproduced all five CSVs byte-for-byte.

## Main analysis: rivals' capacity buffer

```sh
python3 O4/Main_Analysis/capacity_buffer.py
```

This standard-library script reads `data/processed/capacity_airline_monthly.csv` directly. If rebuilding the input, first run `python3 data/source/prepare_capacity.py`. It uses the same positive-passenger scheduled-domestic filter as the EDA, requires valid inputs for every selected airline and checks duplicate airline-months. It stops on invalid data instead of silently excluding or imputing it. Source decimal strings are read using `Decimal` so that ASK minus RPK and sums retain the reported precision.

For each December, it subtracts RPK from ASK for every rival airline brand, sums those differences and divides by IndiGo's total RPK, multiplying by 100. Air India and Air India Express are each counted once. IndiGo is excluded from the numerator. There are nine retained rival brands in December 2024 and eight in December 2025; all 19 selected records, including the two IndiGo records, have valid inputs.

Six outputs are saved in `O4/output/tables/`:

| File | Contents |
|---|---|
| `capacity_buffer_airline.csv` | All 19 selected airline ASK/RPK records, roles, unused amounts and unit conversions |
| `capacity_buffer_summary.csv` | Two monthly aggregates, rival-brand counts, IndiGo RPK and buffer percentages |
| `capacity_buffer_change.csv` | December 2025 minus December 2024: unused-capacity difference, relative change and buffer change in pp |
| `capacity_buffer_table.tex` | Section 5.3 table body with components, ratios and changes |
| `capacity_buffer_airlines_table.tex` | Rival-by-rival unused capacity for the appendix |
| `capacity_buffer_workings.tex` | Numerical substitutions and percentage-change calculations |

Source amounts are in thousands of seat-km or passenger-km. Dividing by 1,000,000 converts them to billions. The buffer is `100 * rivals_unused / indigo_rpk`; it is not unused capacity divided by rivals' ASK or by cancelled traffic. Ratios use unrounded amounts. The buffer falls from 9.7905% to 8.1865%, a change of -1.6040 pp. Rival unused capacity falls from 0.892215468 to 0.671937316 billion seat-km, or 24.69%.

The airline table uses a dash when a brand has no retained positive-passenger record in a comparison month; it does not insert an invented zero. Flagged earlier records remain outside these December samples. National monthly unused seat-km cannot establish route/date-specific spare seats or actual accommodation of disrupted passengers. The formal H7 assessment is included in the Section 6.2 summary below.

An independent SQL calculation from the unchanged raw snapshot checks both months' ASK, RPK, unused capacity, IndiGo denominators, airline counts and ratios. Every airline's difference was also checked against the source decimals. A standalone run with only this script and its prepared CSV reproduced all six outputs byte-for-byte.

## O4 hypothesis summary

```sh
python3 O4/Main_Analysis/hypothesis_summary.py
```

This standard-library script calls the national, route and capacity-buffer calculation functions directly on their prepared CSVs. It does not depend on saved EDA or main-results outputs. The source scripts' data checks remain active. It also requires all 20 H5 months and observations for the 20-pair route sample.

The script prints each outcome and saves `O4/output/tables/hypothesis_results.csv` and `hypothesis_results_table.tex`. The CSV records the original expected relationships, outcomes, H5/H6 qualifying counts and denominators, and H7's unrounded before/after ratios and pp change. Blank count fields for H7 are not missing route data; H7 compares two monthly ratios. The LaTeX body needs the report's `booktabs` and `array` packages.

- H5 requires the specified pair, CR2 >=80% and gap >20 pp in every month from December 2024 to July 2026: 20/20 meet the conditions.
- H6 requires HHI >1,800 in strictly more than half of the full retained route sample: 1,143/1,150 (99.39%). It does not require every route to have an asymmetric IndiGo-AI duopoly.
- H7 requires the December 2025 buffer ratio to be strictly lower than December 2024: 8.1865% versus 9.7905%, a change of -1.6040 pp.

All three are supported in the observed data. These are descriptive condition checks, not statistical significance tests or causal estimates. Their outcomes are checked against the existing independently verified monthly/route/capacity outputs. A standalone copy reproduces both files byte-for-byte.

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

These are EDA tasks. National condition counts are now reported by the separate main-analysis script above; formal hypothesis assessments are now drafted in the discussion.

Code changes are committed and pushed after each completed unit. The Overleaf-linked report is updated locally; committing and pushing it remains deferred until the user requests consolidation.

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

## Capacity inputs: national airline data in Section 4.1

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

ASK measures offered seat-km; RPK measures passenger-km carried. Dividing source values by 1,000,000 converts thousands to billions. Other airlines means every retained airline except IndiGo; brands are counted once and totals are not averages. The four-row input table is retained in Appendix B and described under national airline data in Section 4.1. It introduces the inputs only. The unused-capacity ratio and H7 assessment belong to the main analysis and discussion.

All 138 monthly ownership HHI/fringe values and the four capacity aggregates were independently checked against SQL calculations from the unchanged raw snapshot. A standalone run prepared capacity data from the raw CSV and reproduced all 22 EDA/capacity-preparation outputs byte-for-byte. Existing figure files and the original monthly concentration fields are unchanged.

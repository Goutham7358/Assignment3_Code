# O4: Concentration and rivals' capacity

Compares national passenger concentration with scheduled-flight concentration
on major airport pairs, and estimates rivals' unused capacity relative to
IndiGo's passenger traffic.

Complete the [shared setup](../README.md#setup), then run from the repository root:

```sh
python O4/run_analysis.py
```

This runs all EDA and main-analysis commands below. Existing prepared CSVs are
reused; missing national, capacity or route inputs are prepared automatically.
Missing route inputs trigger extraction from the 228 bundled DGCA PDFs, which
requires Poppler's `pdftotext`.

No cleanup is needed before rerunning. Results are overwritten, not appended.
To rebuild all prepared inputs after changing sources or preparation rules, run
`python O4/run_analysis.py --rebuild-data`. Existing CSVs are not automatically
checked for changes to their source data or preparation code.

Individual steps can also be run separately:

| Command | Main results |
|---|---|
| `python O4/EDA/generate_figures.py` | [Figures](output/figures/), [national measures](output/tables/national_concentration_monthly.csv), [route statistics](output/tables/route_eda_summary.csv) and [capacity inputs](output/tables/capacity_inputs.csv) |
| `python O4/Main_Analysis/national_concentration.py` | [Monthly results](output/tables/national_results_monthly.csv), [condition counts](output/tables/national_results_summary.csv) and [worked example](output/tables/national_worked_example.csv) |
| `python O4/Main_Analysis/route_concentration.py` | [Route results](output/tables/route_results_monthly.csv), [sample comparisons](output/tables/route_results_summary.csv) and [worked example](output/tables/route_worked_example.csv) |
| `python O4/Main_Analysis/route_focus_period.py` | [National/top-10/top-20 comparison](output/tables/national_route_focus_comparison.csv) and [route focus summary](output/tables/route_focus_summary.csv) for December 2024–July 2026 |
| `python O4/Main_Analysis/capacity_buffer.py` | [Airline inputs](output/tables/capacity_buffer_airline.csv), [monthly ratios](output/tables/capacity_buffer_summary.csv) and [changes](output/tables/capacity_buffer_change.csv) |
| `python O4/Main_Analysis/hypothesis_summary.py` | [H5–H7 outcomes and evidence](output/tables/hypothesis_results.csv) |

Additional CSVs and LaTeX table bodies are saved in [output/tables/](output/tables/).
The main-analysis commands calculate directly from prepared inputs and do not
require saved EDA results.

## Inputs and interpretation

- [National input](../data/processed/national_airline_monthly.csv) uses passenger
  counts grouped by ownership. April 2020 is missing.
- [Route inputs](../data/processed/routes/) use approved scheduled flights across
  both directions of 20 selected airport pairs. The top ten are a subset of
  the same 2025 passenger ranking. Missing observations are excluded.
- [Capacity input](../data/processed/capacity_airline_monthly.csv) preserves ASK
  and RPK. The buffer is `100 × rivals' combined (ASK − RPK) / IndiGo RPK`.
  It does not establish how many disrupted passengers could be accommodated
  on their required routes and dates.

CR2 is the combined share of the two largest groups. The gap is largest minus
second-largest. Groups are ranked for each observation, with second-place ties
kept separate when identifying a unique leading pair. National summaries weight
months equally; route summaries weight retained airport-pair/month observations
equally, without passenger or flight weighting.

To rebuild the inputs, follow the [preparation guide](../data/source/README.md).
Definitions, sample exclusions and source checks are documented in
[data/SOURCE.md](../data/SOURCE.md) and [data/ROUTE_SOURCES.md](../data/ROUTE_SOURCES.md).

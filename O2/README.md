# O2: Airline exits and Tata consolidation

Measures which groups gained passenger and capacity shares after the Jet
Airways and Go First exits, their contributions to the HHI change, and the
fixed-share and observed changes around Tata consolidation.

Complete the [shared setup](../README.md#setup), then run from the repository root:

```sh
python O2/run_analysis.py
```

The command reads the [national source CSV](../data/raw/carrier_monthly.csv),
applies the study filters and ownership grouping, and generates all outputs below.

| Output | Contents |
|---|---|
| [H3 share absorption](output/tables/h3_exit_share_absorption.csv) | Passenger and capacity share gains relative to the exiting airline's share |
| [H4 HHI contributions](output/tables/h4_hhi_contributions.csv) | Each group's contribution to the concentration change |
| [Combined exit results](output/tables/exit_share_decomposition.csv) | H3 and H4 results together |
| [Tata comparison](output/tables/tata_consolidation.csv) | Fixed-share ownership effects and observed changes |
| [Descriptive summary](output/tables/analysis_summary.txt) | Exit-window shares, market totals and pre-consolidation shares |
| [Share-path chart](output/figures/exit_share_paths.png) | Monthly group shares around both exits |

For individual calculations, run `python O2/Main_Analysis/h3_exit_share_absorption.py`,
`python O2/Main_Analysis/h4_hhi_contributions.py` or
`python O2/Main_Analysis/supporting_tata_consolidation.py`.

H3 and H4 share the same unrounded inputs. The net HHI change includes the
exiting airline's negative contribution. Capacity uses seat-kilometres;
these comparisons do not track aircraft transfers or individual passengers.
Supporting regulatory and company documents are in [reference_documents/](reference_documents/).

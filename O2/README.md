# Objective 2: Airline Exits and Tata Consolidation

Start with [run_analysis.py](run_analysis.py). It runs H3, H4, the supporting Tata
comparison, and the descriptive summary/chart.

O2 reads the repository's shared `data/raw/carrier_monthly.csv`. Input data are
not duplicated inside this folder; keep `O2` within the repository when running it.

## Code by Hypothesis

| Part | Question | Code | Results |
|---|---|---|---|
| H3 | Does IndiGo have the largest absorption ratio after both exits, and a larger ratio after Go First than Jet? | [H3 script](Main_Analysis/h3_exit_share_absorption.py) | [H3 share absorption](output/tables/h3_exit_share_absorption.csv) |
| H4 | Does IndiGo account for more than half of the net HHI rise after each exit? | [H4 script](Main_Analysis/h4_hhi_contributions.py) | [H4 HHI contributions](output/tables/h4_hhi_contributions.csv) |
| Supporting analysis | How much does Tata consolidation add at fixed shares, compared with observed changes? | [Tata script](Main_Analysis/supporting_tata_consolidation.py) | [Tata comparison](output/tables/tata_consolidation.csv) |

H3 uses share gains and absorption ratios. Compare IndiGo with the other surviving
groups for each exit, then compare its ratios between the two exits. H4 uses each
group's HHI contribution: sum **all** groups, including the exiting airline's
negative contribution, and compare IndiGo's contribution with half that net rise.
Both scripts include passenger and capacity measures. These are descriptive
comparisons, not causal effects.

The [shared calculation module](Main_Analysis/shared_exit_calculations.py) keeps inputs,
event windows and unrounded shares in one place. H4 does not recalculate HHI from
the rounded H3 output. Tata consolidation is assessed separately from H3 and H4.

## Run Everything

Use Python 3.10 or newer. From the repository root, set up an environment once
(macOS/Linux):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r O2/requirements.txt
python O2/run_analysis.py
```

After setup, run `python O2/run_analysis.py` again to regenerate every result.
Matplotlib is the only third-party dependency listed in
[requirements.txt](requirements.txt); H3, H4 and the Tata calculations themselves
use only Python's standard library. No data downloads are needed at run time.

The runner uses the same Python interpreter for its child scripts. It can also
be launched from another working directory by supplying its full path.

From the repository root, using an environment with the requirements installed:

```sh
python3 O2/run_analysis.py
```

## EDA

[EDA/create_charts_and_summary.py](EDA/create_charts_and_summary.py) reads the
shared raw CSV, retains the scheduled-domestic sample, and creates the share-path
chart and descriptive tables. It does not depend on the main-analysis outputs.

```sh
python3 O2/EDA/create_charts_and_summary.py
```

## Main Analysis

The scripts in `Main_Analysis` calculate H3 share absorption, H4 HHI contributions
and the supporting Tata comparison directly from the shared raw CSV. They do not
depend on the EDA outputs. Run all main calculations from the repository root:

```sh
python3 O2/Main_Analysis/calculate_exit_and_merger_effects.py
```

## Folder Map

```text
O2/
  run_analysis.py                         Start here
  requirements.txt                       Install the chart dependency
  EDA/
    create_charts_and_summary.py          Share-path chart and descriptive summary
  Main_Analysis/
    h3_exit_share_absorption.py           H3: who absorbed the exiting share?
    h4_hhi_contributions.py               H4: who drove the HHI rise?
    supporting_tata_consolidation.py      Supporting merger comparison
    shared_exit_calculations.py          Shared inputs, windows and shares
    calculate_exit_and_merger_effects.py  Coordinates H3/H4/Tata; combined export
  output/                                Generated files; do not edit by hand
    tables/
      h3_exit_share_absorption.csv
      h4_hhi_contributions.csv
      exit_share_decomposition.csv
      tata_consolidation.csv
      analysis_summary.txt
    figures/
      exit_share_paths.png
  reference_documents/                   CCI order, Go Airlines DRHP, SpiceJet report
  README.md                              This quick guide
```

## Results

- [Combined exit calculations](output/tables/exit_share_decomposition.csv): share changes,
  absorption ratios and HHI contributions for H3 and H4 in one table.
- [Tata calculations](output/tables/tata_consolidation.csv): fixed-share consolidation
  effects, observed changes and the late-2024 brand contribution breakdown.
- [Descriptive summary](output/tables/analysis_summary.txt): the supporting descriptive tables.
- [Share-path chart](output/figures/exit_share_paths.png): trends around Jet and Go First exits.

To run just one hypothesis from the repository root, using the environment above:

```sh
python O2/Main_Analysis/h3_exit_share_absorption.py
python O2/Main_Analysis/h4_hhi_contributions.py
```

Each command regenerates only its own hypothesis table. Use `run_analysis.py` to
refresh all tables, including the combined export, plus the summary and chart.

## Shared Input

- [Repository airline-month data](../data/raw/carrier_monthly.csv): read and filtered
  by [shared_exit_calculations.py](Main_Analysis/shared_exit_calculations.py), which
  also contains the ownership-group mapping.
- [Data source notes](../data/SOURCE.md): provenance, snapshot details and filtering
  conventions for the DGCA-derived dataset.

EDA, H3, H4 and the supporting Tata analysis use this single raw CSV. Tata's
observed changes are calculated from monthly brand and ownership-group HHIs;
no separate processed event-window CSV is required.

The runner regenerates O2 outputs without modifying the shared data. When
distributing the analysis, retain the repository's `O2/` and `data/raw/` layout.
Local `.venv` and `__pycache__` directories are not required.

Numerical tables and the descriptive summary are in `output/tables`; the chart
is in `output/figures`. Supporting source documents are in `reference_documents`.
# Assignment 3 - O4 analysis code

Code and data for Goutham P's O4 contribution to the DA241o Managerial Economics project on Indian domestic aviation.

The report is maintained separately in [Economics_Assignment3_Template](https://github.com/Goutham7358/Economics_Assignment3_Template), which is linked to Overleaf.

## Current status

The first O4 national EDA is complete: a reproducible data-preparation script, a plotting script, the prepared CSV, the numerical results and a two-panel figure are included. See [O4's instructions and checklist](O4/README.md) for run commands and the remaining EDA tasks. Route PDF conversion and route EDA are the next data-preparation/analysis work; they have not yet been migrated here.

The first figure has two panels:

1. **CR2:** the combined passenger share of the two largest airline ownership groups each month.
2. **Share gap:** the largest group's passenger share minus the second-largest group's share, in percentage points.

The figure and a short description belong in Section 4, Descriptive and Exploratory Analysis, of the report.

![National CR2 and the share gap, January 2015-July 2026](O4/output/figures/national_cr2_share_gap.png)

## Files

| File or folder | Contents |
|---|---|
| `data/raw/carrier_monthly.csv` | Unchanged DGCA-derived airline traffic snapshot |
| `data/source/` | Data preparation code and workflow notes |
| `data/processed/` | Prepared CSV and preparation audit |
| `data/SOURCE.md` | Source, version, fingerprint, variables and study filtering |
| `data/LICENSE.txt` | Upstream licence accompanying the dataset |
| `O4/eda_national.py` | Monthly group calculations, summary statistics and chart |
| `O4/output/` | Figure, numerical tables and software versions |
| `requirements.txt` | Python plotting dependency |

Run instructions and output definitions are in [O4/README.md](O4/README.md). Source data are preserved; analysis scripts consume the prepared CSV, not the upstream download or PDFs.

## How we will write the code

- Use descriptive names and ordinary steps that can be read from top to bottom.
- Give each script one clear purpose. Add functions only when they make the calculation easier to follow.
- Explain economic definitions and important choices, such as ownership grouping, beside the relevant code.
- Keep dependencies small. Avoid unnecessary frameworks, configuration files and command-line options.
- Include the inputs needed to run the script without the surrounding economics-project folder. Use paths relative to the script's location.
- Save the numerical table behind each figure, so the plotted values can be checked.
- Document missing observations, exclusions, units, grouping dates and formulas. Preserve the source data.
- Record the software versions and run instructions used to generate submitted results.
- Check calculations against the underlying data before using them in the report.

## AI assistance

OpenAI Codex assisted with repository setup, documentation, national data-preparation and EDA code, calculation checks, and the first descriptive report text. The analysis follows the method submitted in Assignment 2. The team must review the calculations and interpretations before submission and include the methods-and-tools disclosure required by the course.

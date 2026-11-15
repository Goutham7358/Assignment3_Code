# Assignment 3 - O4 analysis code

Code and data for Goutham P's O4 contribution to the DA241o Managerial Economics project on Indian domestic aviation.

The report is maintained separately in [Economics_Assignment3_Template](https://github.com/Goutham7358/Economics_Assignment3_Template), which is linked to Overleaf.

## Current status

This repository is set up for the analysis. The original data snapshot and its provenance are included. No new Assignment 3 EDA scripts or results have been added yet.

Our first analysis will produce one figure with two panels:

1. **CR2:** the combined passenger share of the two largest airline ownership groups each month.
2. **Share gap:** the largest group's passenger share minus the second-largest group's share, in percentage points.

The figure and a short description will go into Section 4, Descriptive and Exploratory Analysis, of the report.

## Files

| File or folder | Contents |
|---|---|
| `data/carrier_monthly.csv` | Unchanged DGCA-derived airline traffic snapshot |
| `data/SOURCE.md` | Source, version, fingerprint, variables and study filtering |
| `data/LICENSE.txt` | Upstream licence accompanying the dataset |

Each analysis script will be listed here with its exact run command and the files it produces. Any required Python packages will be recorded when the script is added.

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

OpenAI Codex assisted with the initial repository setup and documentation. Assistance with later analysis and coding will be recorded as that work is added. The team must review the calculations and interpretations before submission and include the methods-and-tools disclosure required by the course.

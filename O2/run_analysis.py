#!/usr/bin/env python3
"""Run O2 hypotheses H3 and H4, supporting Tata analysis, summary and chart."""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    objective_root = Path(__file__).resolve().parent
    # Locate shared repository inputs independently of the working directory.
    required_inputs = (
        objective_root.parent / "data" / "raw" / "carrier_monthly.csv",
    )
    missing_inputs = [path for path in required_inputs if not path.is_file()]
    if missing_inputs:
        missing_paths = "\n".join(str(path) for path in missing_inputs)
        raise FileNotFoundError(
            f"Required input files are missing:\n{missing_paths}\n"
            "Verify that the shared CSV is present under the repository's data/raw/."
        )

    steps = (
        ("Run H3, H4 and the supporting Tata comparison", "Main_Analysis/calculate_exit_and_merger_effects.py"),
        ("Create the chart and descriptive summary", "EDA/create_charts_and_summary.py"),
    )
    for step_number, (description, filename) in enumerate(steps, start=1):
        print(f"\n{step_number}/{len(steps)}: {description}", flush=True)
        # Reuse this interpreter so child scripts see the same installed packages.
        subprocess.run(
            [sys.executable, str(objective_root / filename)],
            check=True,
        )
    print(f"\nCompleted. All O2 outputs are in: {objective_root / 'output'}")


if __name__ == "__main__":
    main()
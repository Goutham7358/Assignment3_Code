#!/usr/bin/env python3
"""Run O4 data preparation when needed, followed by EDA and main analysis."""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_script(filename):
    print(f"\nRunning {filename}", flush=True)
    subprocess.run([sys.executable, str(ROOT / filename)], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-data", action="store_true",
        help="Rebuild national, capacity and route inputs from the included source files.",
    )
    args = parser.parse_args()

    preparations = [
        (
            "national",
            ["data/processed/national_airline_monthly.csv"],
            ["data/source/prepare_national.py"],
        ),
        (
            "capacity",
            ["data/processed/capacity_airline_monthly.csv"],
            ["data/source/prepare_capacity.py"],
        ),
        (
            "route",
            [
                "data/processed/routes/route_monthly.csv",
                "data/processed/routes/airline_route_monthly.csv",
                "data/processed/routes/group_route_monthly.csv",
                "data/processed/routes/route_coverage.csv",
                "data/processed/routes/top20_routes.csv",
            ],
            [
                "data/source/extract_route_schedules.py",
                "data/source/prepare_routes.py",
                "data/source/verify_routes.py",
            ],
        ),
    ]
    for name, inputs, scripts in preparations:
        missing = [filename for filename in inputs if not (ROOT / filename).is_file()]
        if args.rebuild_data or missing:
            reason = "--rebuild-data" if args.rebuild_data else "missing " + ", ".join(missing)
            print(f"\nPreparing {name} inputs ({reason}).", flush=True)
            for script in scripts:
                run_script(script)
        else:
            print(f"Using existing {name} CSV inputs.", flush=True)

    for script in [
        "O4/EDA/generate_figures.py",
        "O4/Main_Analysis/national_concentration.py",
        "O4/Main_Analysis/route_concentration.py",
        "O4/Main_Analysis/route_focus_period.py",
        "O4/Main_Analysis/capacity_buffer.py",
        "O4/Main_Analysis/hypothesis_summary.py",
    ]:
        run_script(script)

    print(f"\nCompleted. O4 results are in {ROOT / 'O4/output'}", flush=True)


if __name__ == "__main__":
    main()

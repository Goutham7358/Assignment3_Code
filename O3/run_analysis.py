#!/usr/bin/env python3
"""Run O3 data preparation when needed, followed by the entrant analyses."""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ROUTE_INPUT = "data/interim/routes/o3_schedule_rows.csv"


def run_script(filename):
    print(f"\nRunning {filename}", flush=True)
    subprocess.run([sys.executable, str(ROOT / filename)], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-data", action="store_true",
        help="Re-extract entrant route inputs from the bundled DGCA schedule PDFs.",
    )
    args = parser.parse_args()

    if args.rebuild_data or not (ROOT / ROUTE_INPUT).is_file():
        reason = "--rebuild-data" if args.rebuild_data else f"missing {ROUTE_INPUT}"
        print(f"\nPreparing O3 route inputs ({reason}).", flush=True)
        run_script("data/source/prepare_o3_routes.py")
    else:
        print("Using existing O3 route inputs.", flush=True)

    for script in [
        "O3/Main_Analysis/entrant_analysis.py",
        "O3/Main_Analysis/route_fullseason.py",
    ]:
        run_script(script)

    print(f"\nCompleted. O3 results are in {ROOT / 'O3/output'}", flush=True)


if __name__ == "__main__":
    main()

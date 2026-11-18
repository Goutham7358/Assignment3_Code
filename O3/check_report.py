#!/usr/bin/env python3
"""Check the report's O3 tables and quoted figures against the generated outputs.

Usage: python O3/check_report.py REPORT_DIR_OR_TEX_FILE [...]

Reads the given .tex files, or every .tex file under a given folder. Files named
by \input are read too, relative to the folder of the given file. Each generated
table row in output/tables/o3_*_rows.tex must appear in the report, and the quoted
counts below must match the generated CSVs. Exits with status 1 on any mismatch.
"""

import re
import sys
from pathlib import Path

import pandas as pd

TABLES = Path(__file__).resolve().parent / "output" / "tables"


def normalise(text: str) -> str:
    """Drop whitespace and treat \\\\* as \\\\ so rows compare across table styles."""
    return re.sub(r"\s+", "", text).replace("\\\\*", "\\\\")


def read_tex(file: Path, base: Path, seen: set, missing: list) -> str:
    """Return a file's text followed by the text of the files it \\inputs."""
    if file in seen:
        return ""
    seen.add(file)
    text = file.read_text(encoding="utf-8")
    code = re.sub(r"(?m)^\s*%.*$", "", text)
    for name in re.findall(r"\\input\{([^}]+)\}", code):
        target = base / name
        if target.suffix != ".tex":
            target = target.with_suffix(".tex")
        if target.is_file():
            text += read_tex(target, base, seen, missing)
        else:
            missing.append(str(target))
    return text


def read_report(paths: list[str]) -> str:
    seen, missing, texts = set(), [], []
    for path in map(Path, paths):
        if path.is_dir():
            texts.extend(read_tex(file, path, seen, missing) for file in sorted(path.rglob("*.tex")))
        else:
            texts.append(read_tex(path, path.parent, seen, missing))
    if not seen:
        raise SystemExit("No .tex files found.")
    for name in sorted(set(missing)):
        print(f"warning: input file not found: {name}")
    return normalise("".join(texts))


def quoted_figures() -> list[tuple[str, str]]:
    """Return (description, text that the report must contain) pairs."""
    selected = pd.read_csv(TABLES / "route9_selected_season_summary.csv")
    pairs = pd.read_csv(TABLES / "route9_monthly_check.csv")
    example = pd.read_csv(TABLES / "route9_monthly_example.csv").iloc[0]
    screened = pairs[pairs["screened"]]
    return [
        ("selected-season records", f"{int(selected['pairs'].sum())} records"),
        (
            "monthly check pairs",
            f"{int((screened['share'] >= 50).sum())} of {len(screened)} screened airport pairs",
        ),
        ("example flights", f"all {example['flights']} recorded scheduled flights"),
        ("example pair passengers", f"{example['pair_passengers']:,} passengers"),
        ("example national share", f"{example['airline_national_share_pct']:.2f}\\%"),
    ]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    report = read_report(sys.argv[1:])
    failures = 0

    for file in sorted(TABLES.glob("o3_*_rows.tex")):
        rows = [row for row in file.read_text(encoding="utf-8").split("\\hline") if row.strip()]
        missing = [row.strip() for row in rows if normalise(row) not in report]
        print(f"{file.name}: {len(rows) - len(missing)}/{len(rows)} rows found")
        for row in missing:
            print(f"  missing: {row}")
        failures += len(missing)

    for description, text in quoted_figures():
        found = normalise(text) in report
        print(f"{description}: {'found' if found else 'MISSING'} ({text})")
        failures += not found

    print("\nAll O3 figures match the report." if not failures else f"\n{failures} mismatch(es).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

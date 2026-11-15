"""Draw O4's first EDA figure from the prepared national passenger data."""

import csv
import json
import os
import platform
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[1]
# Keep the font cache in the repository's ignored local working folder.
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp/cache"))

import matplotlib

matplotlib.use("Agg")  # Save figures without requiring a desktop window.
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


INPUT = ROOT / "data/processed/national_airline_monthly.csv"
OUTPUT = Path(__file__).resolve().parent / "output"


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def calculate_monthly():
    counts_by_month = defaultdict(Counter)
    with INPUT.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            counts_by_month[row["date"]][row["ownership_group"]] += int(row["passengers"])

    monthly, group_shares = [], []
    for month, counts in sorted(counts_by_month.items()):
        total = sum(counts.values())
        # Rank groups again each month. Alphabetical order resolves any tie.
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if len(ranked) < 2:
            raise ValueError(f"Fewer than two groups in {month}")
        shares = [100 * passengers / total for group, passengers in ranked]
        if abs(sum(shares) - 100) > 1e-9:
            raise ValueError(f"Shares do not sum to 100 in {month}")
        for rank, ((group, passengers), share) in enumerate(zip(ranked, shares), 1):
            group_shares.append({
                "date": month, "ownership_group": group, "rank": rank,
                "passengers": passengers, "total_passengers": total,
                "passenger_share_pct": share,
            })
        monthly.append({
            "date": month, "total_passengers": total, "group_count": len(ranked),
            "largest_group": ranked[0][0], "second_largest_group": ranked[1][0],
            "largest_share_pct": shares[0], "second_largest_share_pct": shares[1],
            "cr2_pct": shares[0] + shares[1],
            "share_gap_pp": shares[0] - shares[1],
        })
    return monthly, group_shares


def draw_figure(monthly):
    by_month = {row["date"]: row for row in monthly}
    # A complete date axis with NaN at missing months breaks the plotted line.
    dates, cr2, gap = [], [], []
    month = date.fromisoformat(monthly[0]["date"])
    last = date.fromisoformat(monthly[-1]["date"])
    while month <= last:
        row = by_month.get(month.isoformat())
        dates.append(month)
        cr2.append(row["cr2_pct"] if row else np.nan)
        gap.append(row["share_gap_pp"] if row else np.nan)
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)
    fig.subplots_adjust(left=0.11, right=0.93, top=0.83, bottom=0.18, hspace=0.43)
    fig.suptitle("National concentration and size asymmetry", fontsize=15, x=0.11, ha="left", y=0.97)
    fig.text(0.11, 0.91, "India's scheduled domestic passengers, January 2015-July 2026", fontsize=10)

    series = [
        (cr2, "A. Top two groups' combined share (CR2)", "Passenger share (%)", "#23648a"),
        (gap, "B. Largest minus second-largest share", "Gap (percentage points)", "#ad591f"),
    ]
    for ax, (values, title, ylabel, color) in zip(axes, series):
        ax.plot(dates, values, color=color, linewidth=1.8)
        ax.set_title(title, loc="left", fontsize=11, pad=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
        ax.grid(axis="y", color="#e1e5e8", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axvspan(date(2020, 4, 1), date(2020, 5, 1), color="#c8cdd2", alpha=0.6, linewidth=0)
        ax.axvline(date(2022, 1, 1), color="#71777b", linestyle="--", linewidth=0.9)
        ax.plot(dates[-1], values[-1], "o", color=color, markersize=3)
        ax.annotate(f"{values[-1]:.1f}", (dates[-1], values[-1]),
                    xytext=(5, 0), textcoords="offset points", va="center", color=color, fontsize=9)
    axes[0].annotate("Grouping changes\nJan 2022", (date(2022, 1, 1), 25),
                     xytext=(5, 0), textcoords="offset points", fontsize=8, color="#555b60")
    axes[1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[1].set_xlim(dates[0], date(2027, 1, 1))
    axes[1].set_xlabel("Month", fontsize=9)
    fig.text(0.11, 0.075,
             "Source: DGCA monthly traffic via mkubicek/india-aviation-stats; authors' calculations.\n"
             "Groups follow Assignment 2. Dashed line: ownership regrouping in January 2022.\n"
             "Grey band and line break: April 2020 is missing; no value is imputed.",
             fontsize=8, linespacing=1.5, va="center")
    for extension in ["png", "pdf"]:
        fig.savefig(OUTPUT / f"figures/national_cr2_share_gap.{extension}", dpi=220,
                    metadata={"Creator": "O4/eda_national.py"})
    plt.close(fig)


def main():
    for folder in ["figures", "tables"]:
        (OUTPUT / folder).mkdir(parents=True, exist_ok=True)
    monthly, group_shares = calculate_monthly()
    write_csv(OUTPUT / "tables/national_concentration_monthly.csv", monthly)
    write_csv(OUTPUT / "tables/national_group_shares.csv", group_shares)
    summary = []
    for column, unit in [("cr2_pct", "percent"), ("share_gap_pp", "percentage points")]:
        values = [row[column] for row in monthly]
        summary.append({
            "measure": column, "unit": unit, "observed_months": len(values),
            "mean": mean(values), "median": median(values),
            "sample_standard_deviation": stdev(values), "minimum": min(values), "maximum": max(values),
        })
    write_csv(OUTPUT / "tables/national_eda_summary.csv", summary)
    draw_figure(monthly)
    versions = {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__}
    (OUTPUT / "software_versions.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    print(f"Saved the two-panel figure and its tables for {len(monthly)} observed months.")
    print("First observation:", monthly[0])
    print("Last observation:", monthly[-1])


if __name__ == "__main__":
    main()

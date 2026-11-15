"""Plot route-data coverage and the distribution of ownership-group HHI."""

import csv
import os
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp/cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


DATA = ROOT / "data/processed/routes"
OUTPUT = Path(__file__).resolve().parent / "output"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def draw_figure(coverage, hhi):
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["cmr10"], "font.size": 11,
        "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False, "pdf.fonttype": 42,
    })
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.8))
    fig.subplots_adjust(left=0.12, right=0.94, top=0.87, bottom=0.11, hspace=0.62)
    fig.suptitle("Top 20 airport pairs, April 2019-September 2026",
                 fontsize=12, x=0.12, ha="left", y=0.97)

    dates = [date.fromisoformat(row["month"] + "-01") for row in coverage]
    counts = [row["retained_pairs"] for row in coverage]
    axes[0].bar(dates, counts, width=25, color="#23648a")
    axes[0].set_title("A. Available airport pairs by month", loc="left", fontsize=12, pad=10)
    axes[0].set_ylabel("Retained pairs", fontsize=11)
    axes[0].set_ylim(0, 22)
    axes[0].set_yticks([0, 5, 10, 15, 20])
    axes[0].set_xlim(date(2019, 2, 1), date(2026, 11, 1))
    axes[0].xaxis.set_major_locator(mdates.YearLocator())
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[0].annotate("No usable\nobservations", (date(2020, 9, 1), 8.0),
                     ha="center", fontsize=9, color="#555b60")

    bins = np.arange(0, 10001, 500)
    axes[1].hist(hhi, bins=bins, color="#ad591f", edgecolor="white", linewidth=0.6)
    axes[1].set_title("B. Distribution of route-month concentration", loc="left", fontsize=12, pad=10)
    axes[1].set_xlabel("Ownership-group frequency HHI", fontsize=11)
    axes[1].set_ylabel("Route-months", fontsize=11)
    axes[1].set_xlim(0, 10000)
    axes[1].set_xticks(range(0, 10001, 2000))
    axes[1].annotate(f"{len(hhi):,} route-months", (0.98, 0.9),
                     xycoords="axes fraction", ha="right", fontsize=10, color="#555b60")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e1e5e8", linewidth=0.6)
        ax.set_axisbelow(True)
    for extension in ["png", "pdf"]:
        metadata = {"Creator": "O4/eda_routes.py"}
        if extension == "pdf":
            metadata.update({"CreationDate": None, "ModDate": None})
        fig.savefig(OUTPUT / f"figures/route_coverage_hhi.{extension}", dpi=220, metadata=metadata)
    plt.close(fig)


def main():
    for folder in ["figures", "tables"]:
        (OUTPUT / folder).mkdir(parents=True, exist_ok=True)
    routes = read_csv(DATA / "route_monthly.csv")
    coverage_rows = read_csv(DATA / "route_coverage.csv")
    per_month = Counter(row["month"] for row in routes)
    coverage = [{"month": month, "retained_pairs": per_month[month], "selected_pairs": 20}
                for month in sorted({row["month"] for row in coverage_rows})]
    hhi = [float(row["group_frequency_hhi"]) for row in routes]
    q25, q75 = np.quantile(hhi, [0.25, 0.75], method="linear")
    summary = [{
        "measure": "ownership_group_frequency_hhi", "route_months": len(routes),
        "observed_months": len(per_month), "selected_pairs": len({row["route"] for row in routes}),
        "first_month": min(per_month), "last_month": max(per_month),
        "mean": mean(hhi), "median": median(hhi), "sample_standard_deviation": stdev(hhi),
        "p25": float(q25), "p75": float(q75), "minimum": min(hhi), "maximum": max(hhi),
    }]
    frequencies, edges = np.histogram(hhi, bins=np.arange(0, 10001, 500))
    histogram = [{"bin_left_hhi": int(left), "bin_right_hhi": int(right), "route_months": int(count)}
                 for left, right, count in zip(edges[:-1], edges[1:], frequencies)]
    by_pair = defaultdict(list)
    for row in routes:
        by_pair[row["route"]].append(row)
    pair_coverage = [{
        "route": pair, "observed_months": len(rows),
        "first_month": min(row["month"] for row in rows), "last_month": max(row["month"] for row in rows),
        "median_group_frequency_hhi": median(float(row["group_frequency_hhi"]) for row in rows),
    } for pair, rows in sorted(by_pair.items())]
    write_csv(OUTPUT / "tables/route_coverage_by_month.csv", coverage)
    write_csv(OUTPUT / "tables/route_coverage_by_pair.csv", pair_coverage)
    write_csv(OUTPUT / "tables/route_hhi_histogram.csv", histogram)
    write_csv(OUTPUT / "tables/route_eda_summary.csv", summary)
    draw_figure(coverage, hhi)
    print(f"Saved route EDA for {len(routes):,} route-months across {len(per_month)} observed months.")
    print("HHI median:", round(median(hhi), 2), "interquartile range:", round(q25, 2), "to", round(q75, 2))


if __name__ == "__main__":
    main()

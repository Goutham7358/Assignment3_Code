"""Draw O4's first EDA figure from the prepared national passenger data."""

import csv
import json
import os
import platform
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[2]
# Keep the font cache in the repository's ignored local working folder.
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp/cache"))

import matplotlib

matplotlib.use("Agg")  # Save figures without requiring a desktop window.
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


INPUT = ROOT / "data/processed/national_airline_monthly.csv"
OUTPUT = ROOT / "O4/output"


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
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
            "ownership_hhi": sum(share ** 2 for share in shares),
            "fringe_share_pct": 100 - shares[0] - shares[1],
        })
    return monthly, group_shares


def leading_pair_periods(monthly):
    """Summarise runs of the same top two groups among observed months."""
    periods = []
    for row in monthly:
        pair = (row["largest_group"], row["second_largest_group"])
        if not periods or pair != (periods[-1]["largest_group"], periods[-1]["second_largest_group"]):
            periods.append({
                "first_month": row["date"][:7], "last_month": row["date"][:7],
                "largest_group": pair[0], "second_largest_group": pair[1],
                "observed_months": 0,
            })
        periods[-1]["last_month"] = row["date"][:7]
        periods[-1]["observed_months"] += 1
    # A period can span the missing April 2020; its identity is unknown then.
    return periods


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

    # Computer Modern is bundled with Matplotlib and matches the report's serif style.
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["cmr10"], "font.size": 11,
        "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False, "pdf.fonttype": 42,
    })
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.93, top=0.87, bottom=0.14, hspace=0.50)
    fig.suptitle("Scheduled domestic passengers, January 2015-July 2026",
                 fontsize=12, x=0.12, ha="left", y=0.97)

    series = [
        (cr2, "A. Top two groups' combined share (CR2)", "Passenger share (%)", "#23648a"),
        (gap, "B. Largest minus second-largest share", "Gap (percentage points)", "#ad591f"),
    ]
    for ax, (values, title, ylabel, color) in zip(axes, series):
        ax.plot(dates, values, color=color, linewidth=1.8)
        ax.set_title(title, loc="left", fontsize=12, pad=9)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
        ax.grid(axis="y", color="#e1e5e8", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axvspan(date(2020, 4, 1), date(2020, 5, 1), color="#c8cdd2", alpha=0.6, linewidth=0)
        ax.axvline(date(2022, 1, 1), color="#71777b", linestyle="--", linewidth=0.9)
        ax.plot(dates[-1], values[-1], "o", color=color, markersize=3)
        ax.annotate(f"{values[-1]:.1f}", (dates[-1], values[-1]),
                    xytext=(5, 0), textcoords="offset points", va="center", color=color, fontsize=10)
    axes[0].annotate("Ownership regrouping\nJanuary 2022", (date(2022, 1, 1), 20),
                     xytext=(5, 0), textcoords="offset points", fontsize=10, color="#555b60")
    axes[1].annotate("April 2020 missing", (date(2020, 4, 1), 85),
                     xytext=(-5, 0), textcoords="offset points", ha="right", fontsize=10, color="#555b60")
    axes[1].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[1].set_xlim(dates[0], date(2027, 1, 1))
    axes[1].set_xlabel("Month", fontsize=11)
    # Source attribution appears once in the report caption and in data/SOURCE.md.
    for extension in ["png", "pdf"]:
        metadata = {"Creator": "O4/EDA/eda_national.py"}
        if extension == "pdf":
            metadata.update({"CreationDate": None, "ModDate": None})
        fig.savefig(OUTPUT / f"figures/national_cr2_share_gap.{extension}", dpi=220,
                    metadata=metadata)
    plt.close(fig)


def main():
    for folder in ["figures", "tables"]:
        (OUTPUT / folder).mkdir(parents=True, exist_ok=True)
    monthly, group_shares = calculate_monthly()
    write_csv(OUTPUT / "tables/national_concentration_monthly.csv", monthly)
    write_csv(OUTPUT / "tables/national_group_shares.csv", group_shares)
    write_csv(OUTPUT / "tables/national_leading_pair_periods.csv", leading_pair_periods(monthly))
    summary = []
    for column, unit in [
        ("ownership_hhi", "HHI points"), ("cr2_pct", "percent"),
        ("share_gap_pp", "percentage points"), ("fringe_share_pct", "percent"),
    ]:
        values = [row[column] for row in monthly]
        summary.append({
            "measure": column, "unit": unit, "observed_months": len(values),
            "mean": mean(values), "median": median(values),
            "sample_standard_deviation": stdev(values), "minimum": min(values), "maximum": max(values),
        })
    write_csv(OUTPUT / "tables/national_eda_summary.csv", summary)
    labels = {
        "ownership_hhi": "Ownership HHI (points)", "cr2_pct": r"CR2 (\%)",
        "share_gap_pp": "Share gap (pp)", "fringe_share_pct": r"Fringe share (\%)",
    }
    lines = [
        r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
        r"Measure & Mean & Median & Std. dev. & Minimum & Maximum \\", r"\midrule",
    ]
    for row in summary:
        numbers = [f"{row[field]:,.2f}" for field in [
            "mean", "median", "sample_standard_deviation", "minimum", "maximum"
        ]]
        lines.append(labels[row["measure"]] + " & " + " & ".join(numbers) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (OUTPUT / "tables/national_summary_table.tex").write_text("\n".join(lines) + "\n")
    draw_figure(monthly)
    versions = {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__}
    (OUTPUT / "software_versions.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    print(f"Saved the two-panel figure and its tables for {len(monthly)} observed months.")
    print("First observation:", monthly[0])
    print("Last observation:", monthly[-1])


if __name__ == "__main__":
    main()

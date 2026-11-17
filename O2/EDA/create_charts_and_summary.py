"""Create the O2 share-path chart and descriptive summary.

Write the share-path chart to output/figures and the summary to output/tables.
Windows match the main analysis; exit months are excluded.
"""

import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

O2 = Path(__file__).resolve().parents[1]
# Share the main-analysis loader and ownership rules with the EDA.
sys.path.insert(0, str(O2.parent))
from O2.Main_Analysis.shared_exit_calculations import ownership_group, read_data  # noqa: E402

OUT = O2 / "output" / "tables"
FIGURES = O2 / "output" / "figures"

EXITS = [
    # name, exiting group, exit month, pre window, post window, plot range
    ("Jet Airways", "Jet Airways Group", date(2019, 4, 1),
     (date(2018, 4, 1), date(2019, 3, 1)), (date(2019, 5, 1), date(2020, 2, 1)),
     (date(2017, 4, 1), date(2020, 2, 1))),
    ("Go First", "Go First", date(2023, 5, 1),
     (date(2022, 5, 1), date(2023, 4, 1)), (date(2023, 6, 1), date(2024, 5, 1)),
     (date(2021, 5, 1), date(2024, 5, 1))),
]
TATA_STEPS = [("Jan 2022 acquisition", date(2021, 12, 1)), ("Dec 2024 mergers", date(2024, 9, 1))]
TATA_BRANDS = ["Air India", "Air India Express", "Vistara", "AirAsia India", "AIX Connect"]
PLOT_GROUPS = ["IndiGo", "Air India Group", "SpiceJet", "Go First", "Jet Airways Group",
               "Vistara", "AirAsia India", "Akasa Air"]
COLOURS = dict(zip(PLOT_GROUPS, plt.get_cmap("tab10").colors))


def month_back(d: date, k: int) -> date:
    m = d.year * 12 + d.month - 1 - k
    return date(m // 12, m % 12 + 1, 1)


def load():
    # Apply the same raw-data filters and ownership grouping as H3 and H4.
    return [
        {"date": observation["date"], "airline": observation["airline"],
         "group": ownership_group(observation["airline"], observation["date"]),
         "pax": float(observation["passengers"]), "skm": observation["seat_km"],
         "pkm": observation["passenger_km"]}
        for observation in read_data()
    ]


def shares(rows, key, field):
    totals, parts = defaultdict(float), defaultdict(lambda: defaultdict(float))
    for r in rows:
        totals[r["date"]] += r[field]
        parts[r["date"]][r[key]] += r[field]
    return {d: {k: 100 * v / totals[d] for k, v in p.items()} for d, p in parts.items()}


def in_window(d, w):
    return w[0] <= d <= w[1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    rows = load()
    # Exit comparisons use ownership groups; the Tata checks use operating brands.
    g_pax = shares(rows, "group", "pax")
    g_skm = shares(rows, "group", "skm")
    b_pax = shares(rows, "airline", "pax")
    months = sorted(g_pax)
    lines = []

    # Lead-up shares reveal whether each airline was already shrinking before exit.
    lines.append("Table A. Exiting airline's share before exit (%; passengers / seat-km)")
    for name, grp, exit_m, *_ in EXITS:
        cells = []
        for k in (12, 6, 3, 1, 0):
            d = month_back(exit_m, k)
            cells.append(f"t-{k}: {g_pax.get(d, {}).get(grp, 0):.2f} / {g_skm.get(d, {}).get(grp, 0):.2f}")
        lines.append(f"  {name} (t = {exit_m:%b %Y}): " + "; ".join(cells))

    lines.append("\nTable D. IndiGo's mean passenger share in pre vs post windows (%)")
    for name, grp, exit_m, pre, post, _ in EXITS:
        means = []
        for w in (pre, post):
            ms = [d for d in months if in_window(d, w)]
            means.append(sum(g_pax[d].get("IndiGo", 0) for d in ms) / len(ms))
        lines.append(f"  {name}: pre {pre[0]:%b %Y}-{pre[1]:%b %Y} {means[0]:.2f}, "
                     f"post {post[0]:%b %Y}-{post[1]:%b %Y} {means[1]:.2f}")

    # Market load factor uses total passenger-km / seat-km, not mean airline ratios.
    lines.append("\nTable B. Market in pre vs post windows (monthly means)")
    for name, grp, exit_m, pre, post, _ in EXITS:
        for label, w in (("pre", pre), ("post", post)):
            ms = [d for d in months if in_window(d, w)]
            pax = sum(r["pax"] for r in rows if in_window(r["date"], w)) / len(ms)
            skm = sum(r["skm"] for r in rows if in_window(r["date"], w)) / len(ms)
            pkm = sum(r["pkm"] for r in rows if in_window(r["date"], w)) / len(ms)
            groups = sum(sum(1 for v in g_pax[d].values() if v >= 1) for d in ms) / len(ms)
            lines.append(f"  {name} {label} {w[0]:%b %Y}-{w[1]:%b %Y} ({len(ms)} m): "
                         f"passengers {pax / 1e6:.2f} m, seat-km {skm / 1e6:.2f} bn, "
                         f"load factor {100 * pkm / skm:.1f}%, groups >=1% share {groups:.1f}")

    lines.append("\nTable C. Tata brands' passenger shares before each step (%)")
    for label, d in TATA_STEPS:
        cells = [f"{b} {b_pax[d].get(b, 0):.2f}" for b in TATA_BRANDS]
        lines.append(f"  {label} ({d:%b %Y}): " + ", ".join(cells))

    (OUT / "analysis_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, (name, grp, exit_m, pre, post, rng) in zip(axes, EXITS):
        ms = [d for d in months if in_window(d, rng)]
        for g in PLOT_GROUPS:
            ys = [g_pax[d].get(g) for d in ms]
            if any(y and y >= 1 for y in ys):
                ax.plot(ms, [y if y else float("nan") for y in ys], label=g, linewidth=1.4,
                        color=COLOURS[g])
            # Shade the comparison windows and mark the excluded exit month.
        ax.axvspan(pre[0], pre[1], color="0.9", zorder=0)
        ax.axvspan(post[0], post[1], color="0.8", zorder=0)
        ax.axvline(exit_m, color="black", linestyle="--", linewidth=1)
        ax.set_title(f"{name} exit ({exit_m:%B %Y})")
        ax.set_ylabel("Passenger share (%)")
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.grid(alpha=0.3)
    handles, labels = {}, []
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    fig.legend(handles.values(), handles.keys(), loc="lower center", ncol=8, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIGURES / "exit_share_paths.png", dpi=200)


if __name__ == "__main__":
    main()

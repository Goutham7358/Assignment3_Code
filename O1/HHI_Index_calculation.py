import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from data_cleansing import (
    CLEAN_PATH,
    COVID_END,
    COVID_START,
    ROOT,
    clean_airline_monthly,
    load_raw_traffic,
    save_clean_panel,
)

RESULTS_DIR = ROOT / "O1" / "results"
FIGURES_DIR = ROOT / "O1" / "figures"
INDEX_PATH = RESULTS_DIR / "o1_monthly_indices.csv"
FIGURE_PATH = FIGURES_DIR / "Index-over-months.png"

JET_EXIT = pd.Timestamp("2019-05-01")
TATA_ACQUISITION = pd.Timestamp("2022-01-01")
GO_FIRST_EXIT = pd.Timestamp("2023-06-01")
LEGAL_MERGERS = pd.Timestamp("2024-12-01")

EVENT_DATES = {
    "post_jet": JET_EXIT,
    "post_tata": TATA_ACQUISITION,
    "post_go": GO_FIRST_EXIT,
    "post_merge": LEGAL_MERGERS,
}
EVENT_LABELS = [
    ("post_jet", JET_EXIT, "T1"),
    ("post_tata", TATA_ACQUISITION, "T2"),
    ("post_go", GO_FIRST_EXIT, "T3"),
    ("post_merge", LEGAL_MERGERS, "T4"),
]
DRIFT_POINTS = [
    ("D1", "2019-03-01"),
    ("D2", "2020-07-01"),
    ("D3", "2021-05-01"),
    ("D4", "2022-01-01"),
    ("D5", "2023-05-01"),
    ("D6", "2024-12-01"),
    ("D7", "2025-12-01"),
]

AIR_INDIA_GROUP = ("Air India", "Air India Express")
JET_GROUP = ("Jet Airways", "JetLite")
TATA_ABSORBED = ("Vistara", "AirAsia India", "AIX Connect")

JUMP_Z_THRESHOLD = 3.5
JUMP_MATCH_DAYS = 40
NEWEY_WEST_LAGS = 12
HHI_HIGH_CONCENTRATION = 1800
HHI_SYMMETRIC_DUOPOLY = 5000

COLOR_BRAND = "#1f77b4"
COLOR_OWNERSHIP = "#ff7f0e"
COLOR_MHHI = "#d62728"
COLOR_WEDGE = "#7b2d8e"
COLOR_EVENT = "firebrick"


def map_ownership_group(airline, date):
    if airline in AIR_INDIA_GROUP:
        return "Air India Group"
    if airline in JET_GROUP:
        return "Jet Airways Group"
    if airline in TATA_ABSORBED and date >= TATA_ACQUISITION:
        return "Air India Group"
    return airline


def stake_schedule(date):
    if date < pd.Timestamp("2015-09-01"):
        airasia = {"Tata": 0.30, "AAIL": 0.49, "Telestra": 0.21}
    elif date < pd.Timestamp("2016-04-01"):
        airasia = {"Tata": 0.4106, "AAIL": 0.49, "Telestra": 0.0994}
    elif date < pd.Timestamp("2020-01-01"):
        airasia = {"Tata": 0.49, "AAIL": 0.49, "Directors": 0.02}
    elif date < pd.Timestamp("2021-01-01"):
        airasia = {"Tata": 0.51, "AAIL": 0.49}
    else:
        airasia = {"Tata": 0.8367, "AAIL": 0.1633}
    return {"Vistara": {"Tata": 0.51, "SIA": 0.49}, "AirAsia India": airasia}


def control_share(owner, firm, stakes, control):
    holdings = stakes[firm]
    if control == "proportional":
        return holdings[owner]
    largest = max(holdings, key=holdings.get)
    if holdings[largest] > 0.5:
        return 1.0 if owner == largest else 0.0
    return holdings[owner]


def profit_weight(firm_j, firm_k, stakes, control):
    numerator = sum(
        control_share(owner, firm_j, stakes, control) * stakes[firm_k].get(owner, 0.0)
        for owner in stakes[firm_j]
    )
    denominator = sum(
        control_share(owner, firm_j, stakes, control) * stakes[firm_j][owner]
        for owner in stakes[firm_j]
    )
    return numerator / denominator


def partial_ownership_wedge(date, group_shares, control="proportional"):
    if date >= TATA_ACQUISITION or "Vistara" not in group_shares or "AirAsia India" not in group_shares:
        return 0.0
    stakes = stake_schedule(date)
    vistara_share = group_shares["Vistara"]
    airasia_share = group_shares["AirAsia India"]
    weight_sum = profit_weight("Vistara", "AirAsia India", stakes, control) + profit_weight(
        "AirAsia India", "Vistara", stakes, control
    )
    return vistara_share * airasia_share * weight_sum


def pivot_shares(panel, column):
    return panel.pivot_table(index="date", columns=column, values="share", aggfunc="sum").fillna(0)


def top_two_total(shares):
    return np.sort(shares.values, axis=1)[:, -2:]


def compute_concentration_indices(panel):
    panel = panel.copy()
    panel["group"] = [map_ownership_group(a, d) for a, d in zip(panel.airline, panel.date)]
    brand_shares = pivot_shares(panel, "airline")
    group_shares = pivot_shares(panel, "group")
    indices = pd.DataFrame(index=group_shares.index)
    indices["brand_hhi"] = (brand_shares**2).sum(axis=1)
    indices["own_hhi"] = (group_shares**2).sum(axis=1)
    group_top_two = top_two_total(group_shares)
    indices["cr2"] = group_top_two.sum(axis=1)
    indices["cr2_brand"] = top_two_total(brand_shares).sum(axis=1)
    indices["share_gap"] = group_top_two[:, 1] - group_top_two[:, 0]
    indices["fringe"] = 100 - indices["cr2"]
    indices["eff_n"] = 10000 / indices["own_hhi"]
    largest_rival = group_shares.drop(columns="IndiGo").max(axis=1)
    indices["indigo_ratio"] = group_shares["IndiGo"] / largest_rival
    for control, column in [("proportional", "mhhi"), ("majority", "mhhi_major")]:
        wedge = [
            partial_ownership_wedge(date, row.to_dict(), control)
            for date, row in group_shares.iterrows()
        ]
        indices[column] = indices["own_hhi"].values + np.array(wedge)
    indices["gap_own_brand"] = indices.own_hhi - indices.brand_hhi
    indices["gap_mhhi_own"] = indices.mhhi - indices.own_hhi
    return indices


def build_design_matrix(index, include_covid=True):
    design = pd.DataFrame({"t": (index.year - 2015) * 12 + index.month}, index=index)
    for name, start in EVENT_DATES.items():
        design[name] = (index >= start).astype(int)
    if include_covid:
        design["covid"] = ((index >= COVID_START) & (index <= COVID_END)).astype(int)
    for month in range(2, 13):
        design[f"m{month}"] = (index.month == month).astype(int)
    return sm.add_constant(design)


def fit_event_regression(series, design=None, lags=NEWEY_WEST_LAGS):
    design = build_design_matrix(series.index) if design is None else design
    model = sm.OLS(series.values, design.values)
    robust = model.fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return robust, list(design.columns)


def fit_staircase(series):
    design = build_design_matrix(series.index)
    robust, columns = fit_event_regression(series, design)
    params = pd.Series(robust.params, index=columns)
    tvalues = pd.Series(robust.tvalues, index=columns)
    seasonal = [c for c in columns if c[0] == "m" and c[1:].isdigit()]
    retained = ["const", "t", "post_jet", "post_tata", "post_go", "post_merge"]
    fitted = design[retained].values @ params[retained].values + params[seasonal].sum() / 12.0
    steps = {name: (params[name], tvalues[name]) for name in retained[2:]}
    return pd.Series(fitted, index=series.index), steps


def detect_jump_months(series, threshold=JUMP_Z_THRESHOLD):
    changes = series.diff().dropna()
    median = changes.median()
    mad = (changes - median).abs().median()
    modified_z = 0.6745 * (changes - median) / mad
    return set(modified_z[modified_z.abs() > threshold].index)


def flag_jump_months(indices):
    flagged = set()
    for column in ("brand_hhi", "own_hhi", "mhhi"):
        flagged |= detect_jump_months(indices[column])
    return flagged


def load_indices_from_file(path=INDEX_PATH):
    return pd.read_csv(path, parse_dates=["date"], index_col="date")


def calculate_indices_from_raw():
    clean, _ = clean_airline_monthly(load_raw_traffic())
    save_clean_panel(clean, CLEAN_PATH)
    return compute_concentration_indices(clean)


def save_indices(indices, path=INDEX_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    indices.to_csv(path, index_label="date")


def step_label_box():
    return dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85)


def plot_hhi_panel(axis, indices, flagged):
    series_specs = [
        ("Brand-HHI", indices.brand_hhi, COLOR_BRAND, "-"),
        ("Ownership-HHI", indices.own_hhi, COLOR_OWNERSHIP, "--"),
        ("MHHI", indices.mhhi, COLOR_MHHI, "-"),
    ]
    fits = {}
    for name, series, color, style in series_specs:
        axis.plot(series.index, series, color=color, lw=0.9, alpha=0.35)
        fitted, steps = fit_staircase(series)
        fits[name] = (fitted, steps)
        axis.plot(fitted.index, fitted, color=color, lw=2.2, ls=style, label=f"{name} (fitted)", zorder=4)
    axis.axhline(HHI_HIGH_CONCENTRATION, color="grey", ls=":", lw=1.1)
    axis.axhline(HHI_SYMMETRIC_DUOPOLY, color="purple", ls="-.", lw=1.1)
    axis.text(indices.index[1], 1830, "1,800", fontsize=6.5, color="dimgrey")
    axis.text(indices.index[1], 5040, "5,000 symmetric duopoly", fontsize=6.5, color="purple", ha="left")
    axis.set_ylim(1500, 6500)
    axis.set_ylabel("HHI (index points)", fontweight="bold")
    axis.set_title("(a) HHI: observed (thin) and fitted (thick)", fontsize=9, fontweight="bold", pad=14)
    ownership_fit, ownership_steps = fits["Ownership-HHI"]
    for key, event_date, _ in EVENT_LABELS:
        before = ownership_fit[ownership_fit.index < event_date].iloc[-1]
        after = ownership_fit[ownership_fit.index >= event_date].iloc[0]
        axis.text(
            event_date - pd.DateOffset(months=2),
            (before + after) / 2,
            f"{ownership_steps[key][0]:+.0f}",
            fontsize=7,
            fontweight="bold",
            color=COLOR_OWNERSHIP,
            ha="right",
            va="center",
            zorder=9,
            bbox=step_label_box(),
        )
    mark_drift_points(axis, flagged)
    handles, labels = axis.get_legend_handles_labels()
    handles += [
        Line2D([], [], color="grey", lw=0.9, alpha=0.6),
        Line2D([], [], marker="v", ls="none", mfc="black", mec="black", ms=5),
        Line2D([], [], marker="v", ls="none", mfc="white", mec="black", ms=5),
        Patch(fc="grey", alpha=0.25),
    ]
    labels += ["observed", "drift: jump-flagged", "drift: trend break only", "COVID window"]
    axis.legend(
        handles, labels, loc="upper left", fontsize=6.3, ncol=2,
        framealpha=0.92, borderpad=0.4, columnspacing=0.8,
    )


def mark_drift_points(axis, flagged):
    baseline = 1500 + 0.05 * 5000
    for tag, date in DRIFT_POINTS:
        timestamp = pd.Timestamp(date)
        is_flagged = any(abs((timestamp - month).days) <= JUMP_MATCH_DAYS for month in flagged)
        axis.plot(
            timestamp, baseline, marker="v", ms=5.5,
            mfc="black" if is_flagged else "white", mec="black", mew=0.9, ls="none", zorder=6,
        )
        axis.annotate(
            tag, (timestamp, baseline), xytext=(0, 5), textcoords="offset points",
            ha="center", fontsize=6, fontweight="bold",
        )


def plot_cr2_panel(axis, indices):
    series_specs = [
        ("Ownership groups", indices.cr2, COLOR_OWNERSHIP, "--"),
        ("Brands", indices.cr2_brand, COLOR_BRAND, "-"),
    ]
    for name, series, color, style in series_specs:
        axis.plot(series.index, series, color=color, lw=0.9, alpha=0.35)
        fitted, steps = fit_staircase(series)
        axis.plot(
            fitted.index, fitted, color=color, lw=2.2, ls=style,
            label=f"CR2, {name.lower()} (fitted)", zorder=4,
        )
        if name.startswith("Own"):
            annotate_cr2_steps(axis, fitted, steps)
    axis.axhline(90, color="purple", ls="-.", lw=1.1)
    axis.text(indices.index[1], 90.7, "90% of passengers on two groups", fontsize=6.5, color="purple")
    axis.set_ylim(48, 97)
    axis.set_ylabel("CR2 (% of passengers)", fontweight="bold")
    axis.set_title("(b) Two-firm concentration ratio", fontsize=9, fontweight="bold", pad=14)
    axis.legend(loc="lower right", fontsize=6.5, framealpha=0.92)


def annotate_cr2_steps(axis, fitted, steps):
    for key, event_date, tag in EVENT_LABELS:
        before = fitted[fitted.index < event_date].iloc[-1]
        after = fitted[fitted.index >= event_date].iloc[0]
        height = (before + after) / 2 if tag != "T4" else after + 2.6
        axis.text(
            event_date - pd.DateOffset(months=2),
            height,
            f"{steps[key][0]:+.1f}",
            fontsize=7,
            fontweight="bold",
            color=COLOR_OWNERSHIP,
            ha="right",
            va="center",
            zorder=9,
            bbox=step_label_box(),
        )


def plot_wedge_panel(axis, indices):
    grouping = indices.own_hhi - indices.brand_hhi
    partial = indices.mhhi - indices.own_hhi
    total = indices.mhhi - indices.brand_hhi
    axis.plot(grouping.index, grouping, color=COLOR_OWNERSHIP, ls="--", lw=1.6, label="Grouping Effect (Own. - Brand)")
    axis.plot(partial.index, partial, color=COLOR_MHHI, ls=":", lw=1.9, label="Partial-Ownership Effect (MHHI - Own.)")
    axis.plot(total.index, total, color=COLOR_WEDGE, lw=2.0, label="Total concealed wedge (MHHI - Brand)")
    axis.fill_between(total.index, 0, total, color=COLOR_WEDGE, alpha=0.08)
    axis.set_ylim(-20, 760)
    axis.set_ylabel("Wedge (index points)", fontweight="bold")
    axis.set_title("(c) Concealed concentration", fontsize=9, fontweight="bold", pad=14)
    axis.legend(loc="upper left", fontsize=6.5, framealpha=0.92)


def decorate_time_axis(axis, indices):
    axis.axvspan(COVID_START, COVID_END, color="grey", alpha=0.12, lw=0, zorder=0)
    for _, event_date, _ in EVENT_LABELS:
        axis.axvline(event_date, color=COLOR_EVENT, ls="--", lw=0.9, alpha=0.7, zorder=1)
    for _, event_date, tag in EVENT_LABELS:
        axis.annotate(
            tag, xy=(event_date, 1.0), xycoords=("data", "axes fraction"), xytext=(0, 2),
            textcoords="offset points", ha="center", va="bottom", fontsize=7.5,
            fontweight="bold", color=COLOR_EVENT,
        )
    axis.grid(True, ls="--", alpha=0.3)
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axis.set_xlim(indices.index.min() - pd.Timedelta(days=60), indices.index.max() + pd.Timedelta(days=60))
    axis.tick_params(labelsize=7.5)


def plot_index_over_months(indices, flagged, output_path, dpi):
    plt.rcParams.update({"font.size": 8})
    figure, (hhi_axis, cr2_axis, wedge_axis) = plt.subplots(
        1, 3, figsize=(13.2, 4.3), gridspec_kw={"wspace": 0.22}
    )
    plot_hhi_panel(hhi_axis, indices, flagged)
    plot_cr2_panel(cr2_axis, indices)
    plot_wedge_panel(wedge_axis, indices)
    for axis in (hhi_axis, cr2_axis, wedge_axis):
        decorate_time_axis(axis, indices)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)
    print(f"saved {output_path}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Compute the O1 concentration indices and plot Index-over-months.")
    parser.add_argument("--from-indices", action="store_true")
    parser.add_argument("--out", type=Path, default=FIGURE_PATH)
    parser.add_argument("--dpi", type=int, default=250)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    if arguments.from_indices:
        indices = load_indices_from_file()
    else:
        indices = calculate_indices_from_raw()
        save_indices(indices)
        print(f"saved {INDEX_PATH}")
    plot_index_over_months(indices, flag_jump_months(indices), arguments.out, arguments.dpi)


if __name__ == "__main__":
    main()

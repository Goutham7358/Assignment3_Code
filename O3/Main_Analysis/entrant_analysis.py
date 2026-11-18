#!/usr/bin/env python3
"""O3 entrant outcomes: national event-time results and financial ratios.

Reads the DGCA national source CSV and the entrant financial records. Writes the
entrant summary, entry-criteria flags, report table rows and the event-time and
lifespan figures to output/.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from entrant_common import (  # noqa: E402
    ALL_BRANDS, DATA, ENTRANTS, FIGURES, MEANINGFUL_SHARE, O3, OUTCOMES, PERSISTENT_MONTHS,
    RAW, TABLES, get_airline_data, get_event_time_data, latex_row,
    load_national_shares, write_latex_rows,
)

FINANCIAL_RECORDS = DATA / "raw" / "o3_financial_records.csv"

COLORS = {
    "Vistara": "#1baf7a",
    "Akasa Air": "#2a78d6",
    "TruJet": "#eb6834",
    "Star Air": "#6250d6",
    "Fly91": "#e87ba4",
    "Flybig": "#e34948",
    "Zoom Air": "#c98500",
    "India One Air": "#008300",
    "Air Deccan": "#4d4c48",
}
OUTCOME_COLORS = {
    "Merged": COLORS["Vistara"],
    "Operating": COLORS["Akasa Air"],
    "Ceased": COLORS["TruJet"],
}
CONTEXT_COLOR = "#d3d2cb"

PLOT_STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#9a9994",
    "axes.labelcolor": "#52514e",
    "xtick.color": "#52514e",
    "ytick.color": "#52514e",
}


def format_share(value: float) -> str:
    """Format a share for LaTeX; tiny positive shares print as below 0.01."""
    if pd.isna(value):
        return "--"
    if 0 < value < 0.005:
        return "$<$0.01"
    return f"{value:.2f}"


def longest_run_at_or_above(share: pd.Series, threshold: float) -> int:
    """Longest run of consecutive calendar months at or above the threshold."""
    monthly = share.set_axis(share.index.to_period("M")).asfreq("M")
    above = (monthly >= threshold).astype(int)
    runs = above.groupby((above == 0).cumsum()).cumsum()
    return int(runs.max())


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    for airline in ENTRANTS:
        x = get_event_time_data(df, airline)
        if x.empty:
            continue
        peak_row = x.loc[x["share"].idxmax()]
        run = longest_run_at_or_above(x.set_index("date")["share"], MEANINGFUL_SHARE)
        meaningful = bool(x["share"].max() >= MEANINGFUL_SHARE)
        persistent = run >= PERSISTENT_MONTHS
        row = {
            "airline": airline,
            "first": x["date"].min().strftime("%b %Y"),
            "last": x["date"].max().strftime("%b %Y"),
            "months": len(x),
            "peak": x["share"].max(),
            "peak_month": peak_row["date"].strftime("%b %Y"),
            "outcome": OUTCOMES[airline],
            "longest_run_months_at_1pct": run,
            "meaningful": meaningful,
            "persistent": persistent,
            "meets_both": meaningful and persistent,
        }
        # Market share at 12, 24 and 36 months after first service.
        for tau in (12, 24, 36):
            row[f"t{tau}"] = x["share"].get(tau, float("nan"))
        summary_rows.append(row)
    return pd.DataFrame(summary_rows)


def build_brand_table(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise every brand considered, including those outside the nine."""
    rows = []
    for airline in ALL_BRANDS:
        x = get_airline_data(df, airline)
        if airline in ENTRANTS:
            note = "Nine entrants"
        elif airline == "AIX Connect":
            note = "Rebrand of AirAsia India"
        else:
            note = "Not an entrant studied"
        rows.append({
            "airline": airline,
            "first": "" if x.empty else x["date"].min().strftime("%b %Y"),
            "last": "" if x.empty else x["date"].max().strftime("%b %Y"),
            "months": len(x),
            "peak": float("nan") if x.empty else x["share"].max(),
            "note": note,
        })
    return pd.DataFrame(rows)


def build_financial_ratios() -> pd.DataFrame:
    """Revenue growth and net margin on operating income, by airline."""
    records = pd.read_csv(FINANCIAL_RECORDS)
    rows = []
    for airline, group in records.groupby("airline", sort=False):
        years = sorted(group["fiscal_year"].unique())
        first_year, last_year = years[0], years[-1]
        value = group.set_index(["measure", "fiscal_year"])["value_inr_crore"]
        income0 = value["operating_income", first_year]
        income1 = value["operating_income", last_year]
        profit0 = value["profit_after_tax", first_year]
        profit1 = value["profit_after_tax", last_year]
        rows.append({
            "airline": airline,
            "first_year": first_year,
            "last_year": last_year,
            "revenue_growth_pct": 100 * (income1 - income0) / income0,
            "net_margin_first_pct": 100 * profit0 / income0,
            "net_margin_last_pct": 100 * profit1 / income1,
            "latest_profit_after_tax": profit1,
        })
    return pd.DataFrame(rows)


def write_tables(summary: pd.DataFrame, brands: pd.DataFrame, finance: pd.DataFrame) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    summary.to_csv(TABLES / "o3_nine_table.csv", index=False)
    brands.to_csv(TABLES / "o3_all_brands_table.csv", index=False)
    finance.to_csv(TABLES / "o3_financial_ratios.csv", index=False)

    write_latex_rows([
        latex_row(
            row.airline, row.months, format_share(row.t36), f"{row.peak:.2f}",
            row.outcome, "Yes" if row.meets_both else "No",
        )
        for row in summary.itertuples()
    ], "o3_summary_rows.tex")

    write_latex_rows([
        latex_row(
            row.airline, row.first, row.last, format_share(row.t12),
            format_share(row.t24), row.outcome,
        )
        for row in summary.itertuples()
    ], "o3_detail_rows.tex")

    write_latex_rows([
        latex_row(
            f"{row.airline}, {row.first_year}--{row.last_year}",
            f"{row.revenue_growth_pct:.2f}",
            f"${row.net_margin_first_pct:.2f}\\to{row.net_margin_last_pct:.2f}$",
            "$" + f"{row.latest_profit_after_tax:,.1f}".replace(",", "{,}") + "$",
        )
        for row in finance.itertuples()
    ], "o3_financial_rows.tex")


def plot_event_time(df: pd.DataFrame) -> None:
    """One panel per entrant, with the other eight entrants shown in grey."""
    series = {}
    for airline in ENTRANTS:
        x = get_event_time_data(df, airline)
        full_range = range(int(x.index.min()), int(x.index.max()) + 1)
        # Reindex so months missing from the data break the line.
        series[airline] = x["share"].reindex(full_range).clip(lower=0.0002)

    fig, axes = plt.subplots(3, 3, figsize=(7.6, 7.0), dpi=200, sharex=True, sharey=True)
    for index, (ax, airline) in enumerate(zip(axes.flat, ENTRANTS)):
        for other, other_series in series.items():
            if other != airline:
                ax.plot(other_series.index, other_series, color=CONTEXT_COLOR, linewidth=1, zorder=1)

        own = series[airline]
        ax.plot(own.index, own, color=COLORS[airline], linewidth=2, zorder=3)
        # A month with missing neighbours has no line segment, so mark it.
        isolated = own.notna() & own.shift(1).isna() & own.shift(-1).isna()
        ax.plot(own.index[isolated], own[isolated], "o", color=COLORS[airline], markersize=2, zorder=3)
        last = own.dropna()
        ax.plot(last.index[-1], last.iloc[-1], "o", color=COLORS[airline], markersize=5, zorder=4)

        ax.axhline(1, color="#8d8c86", linewidth=0.8, linestyle="--", zorder=2)
        if index == 2:
            ax.text(124, 1.25, "1% line", fontsize=7, color="#52514e", ha="right")
        ax.set_title(airline, loc="left", fontweight="bold", fontsize=10)

    ax = axes[0, 0]
    ax.set_yscale("log")
    ax.set_ylim(0.00015, 15)
    ax.set_xlim(0, 126)
    ax.set_xticks([0, 36, 72, 108])
    ax.set_yticks([0.001, 0.01, 0.1, 1, 10])
    ax.set_yticklabels(["0.001", "0.01", "0.1", "1", "10"])

    fig.supxlabel("Months since first scheduled domestic service (τ)", fontsize=10)
    fig.supylabel("Share of domestic passengers (%, log scale)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_o3_age.png")
    plt.close(fig)


def plot_lifespans(summary: pd.DataFrame) -> None:
    # Earliest entrant at the top.
    order = sorted(
        ENTRANTS,
        key=lambda airline: pd.to_datetime(
            summary.loc[summary["airline"] == airline, "first"].iloc[0],
            format="%b %Y",
        ),
        reverse=True,
    )

    fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
    for index, airline in enumerate(order):
        row = summary.loc[summary["airline"] == airline].iloc[0]
        first_date = pd.to_datetime(row["first"], format="%b %Y")
        last_date = pd.to_datetime(row["last"], format="%b %Y") + pd.offsets.MonthEnd(0)

        ax.barh(
            index, (last_date - first_date).days,
            left=mdates.date2num(first_date), height=0.5,
            color=OUTCOME_COLORS[row["outcome"]],
        )
        ax.text(
            mdates.date2num(last_date) + 60, index,
            f"peak {row['peak']:.2f}%", va="center", fontsize=8,
        )

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(
        mdates.date2num(pd.Timestamp("2015-01-01")),
        mdates.date2num(pd.Timestamp("2027-09-01")),
    )
    ax.legend(
        handles=[
            Patch(color=OUTCOME_COLORS["Operating"], label="Operating (Jul 2026)"),
            Patch(color=OUTCOME_COLORS["Ceased"], label="Ceased"),
            Patch(color=OUTCOME_COLORS["Merged"], label="Merged"),
        ],
        frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9,
    )
    ax.set_xlabel("Months with scheduled domestic passenger traffic in the DGCA data")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    fig.tight_layout()
    fig.savefig(FIGURES / "fig_o3_lifespans.png")
    plt.close(fig)


def main() -> None:
    plt.rcParams.update(PLOT_STYLE)
    FIGURES.mkdir(parents=True, exist_ok=True)

    df = load_national_shares()
    summary = build_summary(df)
    brands = build_brand_table(df)
    finance = build_financial_ratios()
    write_tables(summary, brands, finance)
    plot_event_time(df)
    plot_lifespans(summary)

    print("O3 entrant outcomes")
    print(f"Input: {RAW.relative_to(O3.parent)}")
    print("Share = airline passengers / all scheduled-domestic passengers in the month (%).")
    print("t12, t24, t36 = share 12, 24 and 36 months after the first passenger month.")
    print(
        f"Meaningful = share reaches {MEANINGFUL_SHARE:g}% in any month; persistent = "
        f"{PERSISTENT_MONTHS} consecutive months at or above {MEANINGFUL_SHARE:g}%.\n"
    )
    print("Nine entrants:")
    print(summary.round(2).to_string(index=False))
    print("\nAll brands considered:")
    print(brands.round(3).to_string(index=False))
    print(f"\nFinancial ratios (input: {FINANCIAL_RECORDS.relative_to(O3.parent)}):")
    print("Revenue growth and net margin use operating income; amounts in Rs crore.")
    print(finance.round(2).to_string(index=False))
    print(f"\nSaved 3 CSVs, 3 LaTeX files and 2 figures in {O3.name}/output/.")


if __name__ == "__main__":
    main()

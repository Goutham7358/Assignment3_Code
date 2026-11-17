import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import adfuller

from data_cleansing import (
    COVID_END,
    COVID_START,
    IMMATERIAL_SHARE,
    clean_airline_monthly,
    find_internal_gaps,
    interpolate_material_gaps,
    load_raw_traffic,
    save_clean_panel,
)
from HHI_Index_calculation import (
    EVENT_DATES,
    FIGURE_PATH,
    GO_FIRST_EXIT,
    JET_EXIT,
    LEGAL_MERGERS,
    RESULTS_DIR,
    TATA_ACQUISITION,
    build_design_matrix,
    compute_concentration_indices,
    flag_jump_months,
    map_ownership_group,
    pivot_shares,
    plot_index_over_months,
    save_indices,
    stake_schedule,
)

EVENT_COLUMNS = list(EVENT_DATES)
EVENT_NAMES = {
    "post_jet": "Post-Jet exit (May 2019)",
    "post_tata": "Post-Tata acquisition (Jan 2022)",
    "post_go": "Post-Go First exit (Jun 2023)",
    "post_merge": "Post-legal mergers (Dec 2024)",
}
PERIOD_BOUNDS = [
    pd.Timestamp("2014-12-01"),
    JET_EXIT,
    TATA_ACQUISITION,
    LEGAL_MERGERS,
    pd.Timestamp("2026-08-01"),
]
PERIOD_LABELS = [
    "Pre-Jet exit (Jan 2015-Apr 2019)",
    "Jet exit to Tata (May 2019-Dec 2021)",
    "Tata to mergers (Jan 2022-Nov 2024)",
    "Post mergers (Dec 2024-Jul 2026)",
]
DRIFT_WINDOWS = [
    ("D1", "2019-02-01", "2019-04-01"),
    ("D2", "2020-06-01", "2020-07-01"),
    ("D3", "2021-04-01", "2021-05-01"),
    ("D4", "2021-12-01", "2022-01-01"),
    ("D5", "2023-04-01", "2023-06-01"),
    ("D6", "2024-11-01", "2024-12-01"),
    ("D7", "2025-11-01", "2025-12-01"),
]
SUMMARY_COLUMNS = [
    ("brand_hhi", "Brand-HHI", "points"),
    ("own_hhi", "Ownership-HHI", "points"),
    ("mhhi", "MHHI (proportional control)", "points"),
    ("cr2", "CR2", "%"),
    ("eff_n", "Effective number of firms", "firms"),
    ("share_gap", "Share gap", "pp"),
    ("fringe", "Fringe share", "%"),
    ("indigo_ratio", "IndiGo ratio", "ratio"),
]
WEDGE_WINDOWS = [
    ("Jan-Aug 2015 (Tata 30%)", "2015-01-01", "2015-08-01"),
    ("Sep 2015-Mar 2016 (Tata 41.06%)", "2015-09-01", "2016-03-01"),
    ("Apr-Dec 2016 (Tata 49%)", "2016-04-01", "2016-12-01"),
    ("2017 (source gap)", "2017-01-01", "2017-12-01"),
    ("2018-2019 (Tata 49%)", "2018-01-01", "2019-12-01"),
    ("2020 (Tata 51%)", "2020-01-01", "2020-12-01"),
    ("2021 (Tata 83.67%)", "2021-01-01", "2021-12-01"),
]
STAKE_SOURCES = {
    "Vistara": "sia2015annual; sia2022merger",
    "2015-01-01": "airasia2013jv",
    "2015-09-01": "tata2016airasia",
    "2016-04-01": "tata2016airasia; airasia2018q4",
    "2020-01-01": "airasia2021disposal",
    "2021-01-01": "airasia2021disposal; airasia2021results",
}
MANIFEST_ROWS = [
    ("o1_monthly_indices.csv", "Brand-HHI, Ownership-HHI, MHHI, CR2 and derived indices per market-month", "Figure O1 (o1_hhi.png); all tables"),
    ("o1_table_cleaning_log.csv", "Cleansing counts per rule", "tab:o1-cleansing, tab:o1-cleaning"),
    ("o1_table_period_means.csv", "Concentration measures by period", "tab:o1-periods"),
    ("o1_table_summary_statistics.csv", "Descriptive statistics of the index series", "tab:o1-summary"),
    ("o1_table_drift_points.csv", "Drift windows D1-D7 with index changes and share movers", "tab:o1-drift"),
    ("o1_table_segmented_regression.csv", "Equation O1.2 for Brand-HHI, Ownership-HHI and MHHI", "tab:o1-regression"),
    ("o1_table_cr2_regression.csv", "Equation O1.2 for CR2 (ownership and brand level)", "tab:o1-cr2reg"),
    ("o1_table_robustness.csv", "Robustness of the Ownership-HHI steps", "tab:o1-robust"),
    ("o1_table_grouping_gap.csv", "Grouping gap by period and regression", "tab:o1-gap"),
    ("o1_table_stake_schedule.csv", "Partial-ownership stake schedule used for MHHI", "tab:o1-stakes"),
    ("o1_table_wedge_summary.csv", "Partial-ownership wedge statistics", "tab:o1-hypotheses (H2), Section 4.2"),
    ("o1_table_data_quality_sensitivity.csv", "Sensitivity of the indices to flagged outliers and gaps", "Section 4.1 text, appendix C.4"),
]


def significance_stars(pvalue):
    if pvalue < 0.01:
        return "**"
    if pvalue < 0.05:
        return "*"
    return ""


def fit_with_diagnostics(series, design=None, lags=12):
    design = build_design_matrix(series.index) if design is None else design
    ols = sm.OLS(series.values, design.values).fit()
    robust = sm.OLS(series.values, design.values).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return ols, robust, list(design.columns)


def sum_of_steps(robust, columns):
    weights = np.zeros(len(columns))
    weights[[columns.index(name) for name in EVENT_COLUMNS]] = 1
    estimate = float(robust.params @ weights)
    standard_error = float(np.sqrt(weights @ robust.cov_params() @ weights))
    return estimate, standard_error


def regression_rows(series_name, ols, robust, columns, keys):
    rows = []
    for key in keys:
        position = columns.index(key)
        rows.append(
            dict(
                series=series_name,
                term=key,
                coefficient=robust.params[position],
                std_error=robust.bse[position],
                t_statistic=robust.tvalues[position],
                p_value=robust.pvalues[position],
                stars=significance_stars(robust.pvalues[position]),
            )
        )
    estimate, standard_error = sum_of_steps(robust, columns)
    rows.append(dict(series=series_name, term="sum_of_four_steps", coefficient=estimate, std_error=standard_error))
    rows.append(dict(series=series_name, term="r_squared", coefficient=robust.rsquared))
    rows.append(dict(series=series_name, term="durbin_watson", coefficient=durbin_watson(ols.resid)))
    rows.append(dict(series=series_name, term="breusch_godfrey_p_12_lags", coefficient=acorr_breusch_godfrey(ols, nlags=12)[1]))
    rows.append(dict(series=series_name, term="adf_residual_p", coefficient=adfuller(ols.resid, regression="n")[1]))
    rows.append(dict(series=series_name, term="n_observations", coefficient=int(robust.nobs)))
    return rows


def build_cleaning_log(clean, log, immaterial_effect):
    rows = [dict(rule=key.split(" ")[0], metric=key, value=str(value)) for key, value in log.items()]
    rows.append(dict(rule="C9", metric="C9 market-months with shares summing to 100", value=str(clean.date.nunique())))
    rows.append(dict(rule="summary", metric="clean airline-months", value=str(len(clean))))
    rows.append(dict(rule="summary", metric="market-months", value=str(clean.date.nunique())))
    rows.append(dict(rule="summary", metric="airlines", value=str(clean.airline.nunique())))
    rows.append(dict(rule="C7", metric="immaterial flags dropped in sensitivity run", value=str(immaterial_effect["rows_dropped"])))
    return pd.DataFrame(rows)


def build_period_means(indices):
    periods = pd.cut(indices.index, PERIOD_BOUNDS, labels=PERIOD_LABELS, right=False)
    columns = ["brand_hhi", "own_hhi", "mhhi", "cr2", "share_gap", "fringe", "gap_own_brand", "gap_mhhi_own"]
    table = indices.groupby(periods, observed=True)[columns].mean()
    table.index.name = "period"
    return table.reset_index()


def build_summary_statistics(indices):
    rows = []
    for column, label, unit in SUMMARY_COLUMNS:
        series = indices[column]
        rows.append(
            dict(series=label, mean=series.mean(), sd=series.std(), min=series.min(), max=series.max(), unit=unit, n=len(series))
        )
    return pd.DataFrame(rows)


def build_drift_table(clean, indices):
    panel = clean.copy()
    panel["group"] = [map_ownership_group(a, d) for a, d in zip(panel.airline, panel.date)]
    group_shares = pivot_shares(panel, "group")
    rows = []
    for tag, start, end in DRIFT_WINDOWS:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        movers = (group_shares.loc[end] - group_shares.loc[start]).sort_values(key=abs, ascending=False).head(3)
        rows.append(
            dict(
                drift=tag,
                window_start=start.strftime("%Y-%m"),
                window_end=end.strftime("%Y-%m"),
                delta_brand_hhi=indices.loc[end, "brand_hhi"] - indices.loc[start, "brand_hhi"],
                delta_own_hhi=indices.loc[end, "own_hhi"] - indices.loc[start, "own_hhi"],
                delta_mhhi=indices.loc[end, "mhhi"] - indices.loc[start, "mhhi"],
                delta_cr2=indices.loc[end, "cr2"] - indices.loc[start, "cr2"],
                own_hhi_level_start=indices.loc[start, "own_hhi"],
                own_hhi_level_end=indices.loc[end, "own_hhi"],
                largest_share_movers_pp="; ".join(f"{name} {value:+.1f}" for name, value in movers.items()),
                jump_flagged=any(abs((end - month).days) <= 40 for month in flag_jump_months(indices)),
            )
        )
    return pd.DataFrame(rows)


def build_segmented_regression(indices):
    rows = []
    keys = ["const", "t"] + EVENT_COLUMNS + ["covid"]
    for column, label in [("brand_hhi", "Brand HHI"), ("own_hhi", "Ownership HHI"), ("mhhi", "MHHI")]:
        ols, robust, columns = fit_with_diagnostics(indices[column])
        rows += regression_rows(label, ols, robust, columns, keys)
    return pd.DataFrame(rows)


def build_cr2_regression(indices):
    rows = []
    keys = ["const", "t"] + EVENT_COLUMNS + ["covid"]
    for column, label in [("cr2", "Ownership-group CR2"), ("cr2_brand", "Brand-level CR2")]:
        ols, robust, columns = fit_with_diagnostics(indices[column])
        rows += regression_rows(label, ols, robust, columns, keys)
    return pd.DataFrame(rows)


def event_steps_row(label, robust, columns):
    row = {"specification": label}
    for name in EVENT_COLUMNS:
        position = columns.index(name)
        row[f"{name}_coefficient"] = robust.params[position]
        row[f"{name}_t_statistic"] = robust.tvalues[position]
    return row


def build_robustness(clean, indices):
    series = indices["own_hhi"]
    rows = []
    for lags, label in [(12, "Baseline (Newey-West 12 lags)"), (6, "Newey-West 6 lags"), (18, "Newey-West 18 lags")]:
        _, robust, columns = fit_with_diagnostics(series, lags=lags)
        rows.append(event_steps_row(label, robust, columns))
    keep = ~((series.index >= COVID_START) & (series.index <= COVID_END))
    design = build_design_matrix(series.index, include_covid=False)[keep]
    _, robust, columns = fit_with_diagnostics(series[keep], design)
    rows.append(event_steps_row("COVID months dropped", robust, columns))
    interpolated, _ = interpolate_material_gaps(clean, find_internal_gaps(clean))
    interpolated_indices = compute_concentration_indices(interpolated)
    _, robust, columns = fit_with_diagnostics(interpolated_indices["own_hhi"])
    rows.append(event_steps_row("AirAsia India 2017 interpolated", robust, columns))
    return pd.DataFrame(rows)


def build_grouping_gap(indices):
    gap = indices["gap_own_brand"]
    periods = pd.cut(indices.index, PERIOD_BOUNDS, labels=PERIOD_LABELS, right=False)
    period_rows = gap.groupby(periods, observed=True).agg(["mean", "min", "max"]).reset_index()
    period_rows.columns = ["period", "mean", "min", "max"]
    period_rows.insert(0, "block", "period_summary")
    standard_design = build_design_matrix(gap.index)
    trend_design = standard_design.copy()
    first_post_t = trend_design.loc[gap.index >= TATA_ACQUISITION, "t"].min()
    trend_design["post_tata_trend"] = trend_design["post_tata"] * (trend_design["t"] - first_post_t)
    regression_rows_list = []
    for label, design in [("standard_model", standard_design), ("with_post_tata_trend", trend_design)]:
        ols, robust, columns = fit_with_diagnostics(gap, design)
        keys = [k for k in ["post_tata", "post_tata_trend", "post_go", "post_merge"] if k in columns]
        for key in keys:
            position = columns.index(key)
            regression_rows_list.append(
                dict(
                    block=label,
                    period=key,
                    coefficient=robust.params[position],
                    std_error=robust.bse[position],
                    t_statistic=robust.tvalues[position],
                    p_value=robust.pvalues[position],
                    stars=significance_stars(robust.pvalues[position]),
                )
            )
        regression_rows_list.append(dict(block=label, period="r_squared", coefficient=robust.rsquared))
    return pd.concat([period_rows, pd.DataFrame(regression_rows_list)], ignore_index=True)


def format_stakes(holdings):
    return "; ".join(f"{owner} {stake * 100:g}%" for owner, stake in holdings.items())


def build_stake_schedule():
    months = pd.date_range("2015-01-01", "2021-12-01", freq="MS")
    rows = []
    for firm in ["Vistara", "AirAsia India"]:
        current, first = None, None
        for month in list(months) + [None]:
            holdings = stake_schedule(month)[firm] if month is not None else None
            if holdings != current:
                if current is not None:
                    key = firm if firm == "Vistara" else first.strftime("%Y-%m-%d")
                    rows.append(
                        dict(
                            firm=firm,
                            owners_and_stakes=format_stakes(current),
                            first_month=first.strftime("%Y-%m"),
                            last_month=previous.strftime("%Y-%m"),
                            source_keys=STAKE_SOURCES.get(key, ""),
                        )
                    )
                current, first = holdings, month
            previous = month
    return pd.DataFrame(rows)


def build_wedge_summary(clean, indices):
    pre = indices[indices.index < TATA_ACQUISITION]
    rows = [
        dict(metric="pre_2022_mean_wedge_points", value=pre.gap_mhhi_own.mean()),
        dict(metric="pre_2022_max_wedge_points", value=pre.gap_mhhi_own.max()),
        dict(metric="pre_2022_max_wedge_month", value=pre.gap_mhhi_own.idxmax().strftime("%Y-%m")),
        dict(metric="pre_2022_mean_wedge_pct_of_own_hhi", value=(100 * pre.gap_mhhi_own / pre.own_hhi).mean()),
        dict(metric="pre_2022_max_wedge_pct_of_own_hhi", value=(100 * pre.gap_mhhi_own / pre.own_hhi).max()),
        dict(metric="pre_2022_months_with_positive_wedge_share", value=(pre.gap_mhhi_own > 0).mean()),
        dict(metric="pre_2022_months_with_zero_wedge", value=int((pre.gap_mhhi_own == 0).sum())),
        dict(metric="post_2022_max_abs_wedge", value=indices.loc[TATA_ACQUISITION:, "gap_mhhi_own"].abs().max()),
        dict(metric="majority_control_pre_2022_mean_wedge", value=(indices.mhhi_major - indices.own_hhi)[indices.index < TATA_ACQUISITION].mean()),
        dict(metric="majority_control_pre_2022_max_wedge", value=(indices.mhhi_major - indices.own_hhi)[indices.index < TATA_ACQUISITION].max()),
    ]
    for label, start, end in WEDGE_WINDOWS:
        rows.append(dict(metric=f"mean_wedge_points {label}", value=indices.loc[start:end, "gap_mhhi_own"].mean()))
    interpolated, _ = interpolate_material_gaps(clean, find_internal_gaps(clean))
    interpolated_indices = compute_concentration_indices(interpolated)
    rows.append(dict(metric="interpolated_2017_mean_wedge_points", value=interpolated_indices.loc["2017-01-01":"2017-12-01", "gap_mhhi_own"].mean()))
    rows.append(dict(metric="interpolated_pre_2022_mean_wedge_points", value=interpolated_indices[interpolated_indices.index < TATA_ACQUISITION].gap_mhhi_own.mean()))
    grouping = indices.gap_own_brand
    rows.append(dict(metric="grouping_gap_peak_points", value=grouping.max()))
    rows.append(dict(metric="grouping_gap_peak_month", value=grouping.idxmax().strftime("%Y-%m")))
    rows.append(dict(metric="grouping_gap_months_below_half_point", value=int((grouping < 0.5).sum())))
    return pd.DataFrame(rows)


def measure_immaterial_flag_effect(clean, indices):
    immaterial = clean[clean.flag_jump & clean.jump_class.str.startswith("unexplained, immaterial")]
    reduced = clean.drop(immaterial.index).copy()
    reduced["share"] = reduced.passengers / reduced.groupby("date").passengers.transform("sum") * 100
    reduced_indices = compute_concentration_indices(reduced)
    effect = {"rows_dropped": len(immaterial)}
    for column in ["brand_hhi", "own_hhi", "mhhi"]:
        difference = (reduced_indices[column] - indices[column]).abs()
        effect[f"{column}_max_abs_change"] = difference.max()
        effect[f"{column}_mean_abs_change"] = difference.mean()
    return effect


def build_data_quality_sensitivity(clean, indices, immaterial_effect):
    rows = [dict(check="drop_unexplained_immaterial_flags", metric=key, value=value) for key, value in immaterial_effect.items()]
    gaps = find_internal_gaps(clean)
    interpolated, added = interpolate_material_gaps(clean, gaps)
    interpolated_indices = compute_concentration_indices(interpolated)
    months = added.date.unique()
    difference = interpolated_indices[["brand_hhi", "own_hhi", "mhhi"]] - indices[["brand_hhi", "own_hhi", "mhhi"]]
    for column in ["brand_hhi", "own_hhi", "mhhi"]:
        rows.append(dict(check="interpolate_material_gaps", metric=f"{column}_mean_abs_change_in_imputed_months", value=difference.loc[months, column].abs().mean()))
        rows.append(dict(check="interpolate_material_gaps", metric=f"{column}_max_abs_change_in_imputed_months", value=difference.loc[months, column].abs().max()))
    rows.append(dict(check="interpolate_material_gaps", metric="imputed_months", value=len(added)))
    airasia = interpolated[(interpolated.airline == "AirAsia India") & (interpolated.date.dt.year == 2017)]
    rows.append(dict(check="interpolate_material_gaps", metric="imputed_airasia_india_2017_mean_share_pct", value=airasia.share.mean()))
    return pd.DataFrame(rows)


def write_table(table, name):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(RESULTS_DIR / name, index=False)
    print(f"saved {RESULTS_DIR / name}")


def write_manifest():
    manifest = pd.DataFrame(MANIFEST_ROWS, columns=["csv_file", "contents", "used_in_sowmya_tex"])
    write_table(manifest, "README_tables_manifest.csv")


def export_all_results():
    clean, log = clean_airline_monthly(load_raw_traffic())
    save_clean_panel(clean)
    indices = compute_concentration_indices(clean)
    save_indices(indices)
    immaterial_effect = measure_immaterial_flag_effect(clean, indices)
    write_table(build_cleaning_log(clean, log, immaterial_effect), "o1_table_cleaning_log.csv")
    write_table(build_period_means(indices), "o1_table_period_means.csv")
    write_table(build_summary_statistics(indices), "o1_table_summary_statistics.csv")
    write_table(build_drift_table(clean, indices), "o1_table_drift_points.csv")
    write_table(build_segmented_regression(indices), "o1_table_segmented_regression.csv")
    write_table(build_cr2_regression(indices), "o1_table_cr2_regression.csv")
    write_table(build_robustness(clean, indices), "o1_table_robustness.csv")
    write_table(build_grouping_gap(indices), "o1_table_grouping_gap.csv")
    write_table(build_stake_schedule(), "o1_table_stake_schedule.csv")
    write_table(build_wedge_summary(clean, indices), "o1_table_wedge_summary.csv")
    write_table(build_data_quality_sensitivity(clean, indices, immaterial_effect), "o1_table_data_quality_sensitivity.csv")
    write_manifest()
    plot_index_over_months(indices, flag_jump_months(indices), FIGURE_PATH, 250)


if __name__ == "__main__":
    export_all_results()

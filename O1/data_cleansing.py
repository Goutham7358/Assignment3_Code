"""Note on how the raw data is changed before the HHI calculation.
1. Rows are only removed when out of scope (non-scheduled-domestic, outside Jan 2015-Jul 2026) or zero-passenger; no observed passenger count is overwritten.
2. Market shares are recomputed from passengers each month, so they sum to 100; outliers and inconsistent rows are flagged, not altered or dropped.
3. April 2020 is missing for every airline and stays empty; it is not imputed.
4. Interpolation exists only in interpolate_material_gaps (log-linear, AirAsia India 2017) as a sensitivity run; the headline indices use the uninterpolated panel.
5. Everything else (Brand-, Ownership-HHI, MHHI, CR2) is computed from this panel in HHI_Index_calculation.py.
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "carrier_monthly.csv"
CLEAN_PATH = ROOT / "data" / "processed" / "o1_airline_monthly_clean.csv"
RAW_SHA256 = "30412b650b47b9d8ba50917365b29f120f2da458403533829d65fd11b64c09be"

STUDY_START = pd.Timestamp("2015-01-01")
STUDY_END = pd.Timestamp("2026-07-01")
COVID_START = pd.Timestamp("2020-03-01")
COVID_END = pd.Timestamp("2021-12-01")
MISSING_MARKET_MONTH = pd.Timestamp("2020-04-01")
MERGER_MONTHS = [pd.Timestamp("2024-10-01"), pd.Timestamp("2024-11-01")]

NUMERIC_COLUMNS = ["year", "month", "passengers", "passenger_km", "seat_km"]
KEY_COLUMNS = ["airline", "date"]
VOLUME_COLUMNS = ["passengers", "passenger_km", "seat_km"]

JUMP_LOG_THRESHOLD = 0.7
MARKET_SHOCK_THRESHOLD = 0.5
RAMP_WINDOW_DAYS = 70
IMMATERIAL_SHARE = 1.0


def load_raw_traffic(path=RAW_PATH):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != RAW_SHA256:
        raise ValueError(f"dataset checksum mismatch: {digest}")
    return pd.read_csv(path)


def coerce_numeric_columns(frame, log):
    frame = frame.copy()
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    log["C1 rows with NaN in key columns"] = int(frame[NUMERIC_COLUMNS].isna().any(axis=1).sum())
    return frame.dropna(subset=NUMERIC_COLUMNS)


def standardise_airline_names(frame):
    frame = frame.copy()
    frame["airline"] = frame["airline"].str.strip().str.replace(r"\s+", " ", regex=True)
    return frame


def restrict_to_study_scope(frame, log):
    frame = frame.copy()
    frame["date"] = pd.to_datetime(
        dict(year=frame.year.astype(int), month=frame.month.astype(int), day=1)
    )
    log["C3 rows outside scheduled-domestic scope"] = int((frame.service_type != "scheduled_domestic").sum())
    frame = frame[frame.service_type == "scheduled_domestic"]
    log["C3 rows after cut-off"] = int((frame.date > STUDY_END).sum())
    return frame[(frame.date >= STUDY_START) & (frame.date <= STUDY_END)]


def aggregate_duplicate_airline_months(frame, log):
    log["C4 duplicate airline-months"] = int(frame.duplicated(KEY_COLUMNS).sum())
    return frame.groupby(KEY_COLUMNS, as_index=False)[VOLUME_COLUMNS].sum()


def drop_structural_zeros(frame, log):
    log["C5 rows with passengers<=0 (dropped)"] = int((frame.passengers <= 0).sum())
    return frame[frame.passengers > 0].copy()


def flag_internal_inconsistencies(frame, log):
    frame = frame.copy()
    frame["load_factor_calc"] = frame.passenger_km / frame.seat_km.replace(0, np.nan) * 100
    frame["flag_zero_seat_km"] = frame.seat_km <= 0
    frame["flag_passenger_km_above_seat_km"] = frame.passenger_km > frame.seat_km * 1.0001
    log["C6 flagged: seat_km<=0 with passengers>0"] = int(frame.flag_zero_seat_km.sum())
    log["C6 flagged: passenger_km>seat_km"] = int(frame.flag_passenger_km_above_seat_km.sum())
    return frame


def classify_outlier_jumps(frame, log):
    frame = frame.sort_values(KEY_COLUMNS).copy()
    frame["dlog"] = frame.groupby("airline").passengers.transform(lambda s: np.log(s).diff())
    market_total = frame.groupby("date").passengers.sum()
    market_shock = np.log(market_total).diff().abs() > MARKET_SHOCK_THRESHOLD
    frame["share"] = frame.passengers / frame.date.map(market_total) * 100
    first_month = frame.groupby("airline").date.transform("min")
    last_month = frame.groupby("airline").date.transform("max")
    in_ramp = ((frame.date - first_month).dt.days < RAMP_WINDOW_DAYS) | (
        (last_month - frame.date).dt.days < RAMP_WINDOW_DAYS
    )
    month_before_rebound = frame.date.map(market_shock.shift(-1, fill_value=False)).astype(bool)
    frame["flag_jump"] = frame.dlog.abs() > JUMP_LOG_THRESHOLD
    in_covid = (frame.date >= COVID_START) & (frame.date <= COVID_END)
    in_merger_month = frame.date.isin(MERGER_MONTHS)
    frame["jump_class"] = np.select(
        [
            ~frame.flag_jump,
            in_covid | frame.date.map(market_shock).fillna(False) | month_before_rebound,
            in_ramp,
            in_merger_month,
            frame.share < IMMATERIAL_SHARE,
        ],
        [
            "",
            "explained: COVID / market-wide shock",
            "explained: entry/exit ramp",
            "explained: merger or rebrand month",
            "unexplained, immaterial (<1% share)",
        ],
        default="unexplained, material (>=1% share)",
    )
    for label, count in frame[frame.flag_jump].jump_class.value_counts().items():
        log[f"C7 jump flags - {label}"] = int(count)
    return frame


def record_missing_months(frame, log):
    observed = set(frame.date)
    expected = pd.date_range(STUDY_START, STUDY_END, freq="MS")
    log["C8 missing months"] = [str(month.date()) for month in expected if month not in observed]


def verify_share_closure(frame):
    if not np.allclose(frame.groupby("date").share.sum(), 100):
        raise ValueError("market shares do not sum to 100 in every month")


def clean_airline_monthly(raw):
    log = {}
    frame = coerce_numeric_columns(raw, log)
    frame = standardise_airline_names(frame)
    frame = restrict_to_study_scope(frame, log)
    frame = aggregate_duplicate_airline_months(frame, log)
    frame = drop_structural_zeros(frame, log)
    frame = flag_internal_inconsistencies(frame, log)
    frame = classify_outlier_jumps(frame, log)
    record_missing_months(frame, log)
    verify_share_closure(frame)
    return frame, log


def find_internal_gaps(frame):
    gaps = []
    for airline, group in frame.groupby("airline"):
        shares = group.set_index("date").share
        months = pd.date_range(shares.index.min(), shares.index.max(), freq="MS")
        run = []
        for month in list(months) + [None]:
            if month is not None and month not in shares.index and month != MISSING_MARKET_MONTH:
                run.append(month)
                continue
            if run:
                previous_share = shares[shares.index < run[0]].iloc[-1]
                next_share = shares[shares.index > run[-1]].iloc[0]
                gaps.append(
                    dict(
                        airline=airline,
                        first=run[0],
                        last=run[-1],
                        n=len(run),
                        bracket_share=(previous_share + next_share) / 2,
                    )
                )
                run = []
    return gaps


def interpolate_material_gaps(frame, gaps, max_gap=18, min_share=1.0):
    rows = []
    for gap in gaps:
        inside_covid = COVID_START <= gap["first"] <= COVID_END
        if gap["n"] > max_gap or gap["bracket_share"] < min_share or inside_covid:
            continue
        passengers = frame[frame.airline == gap["airline"]].set_index("date").passengers
        before = passengers[passengers.index < gap["first"]].iloc[-1]
        after = passengers[passengers.index > gap["last"]].iloc[0]
        months = pd.date_range(gap["first"], gap["last"], freq="MS")
        for position, month in enumerate(months, start=1):
            weight = position / (len(months) + 1)
            interpolated = np.exp((1 - weight) * np.log(before) + weight * np.log(after))
            rows.append(dict(airline=gap["airline"], date=month, passengers=float(interpolated)))
    added = pd.DataFrame(rows)
    combined = pd.concat([frame[["airline", "date", "passengers"]], added], ignore_index=True)
    combined["share"] = combined.passengers / combined.groupby("date").passengers.transform("sum") * 100
    return combined, added


def save_clean_panel(frame, path=CLEAN_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def load_clean_panel(path=CLEAN_PATH):
    return pd.read_csv(path, parse_dates=["date"])


def run_data_cleansing():
    raw = load_raw_traffic()
    clean, log = clean_airline_monthly(raw)
    save_clean_panel(clean)
    for key, value in log.items():
        print(f"{key}: {value}")
    print(
        f"clean airline-months: {len(clean)}  market-months: {clean.date.nunique()}  "
        f"airlines: {clean.airline.nunique()}"
    )
    print(f"saved {CLEAN_PATH}")
    return clean, log


if __name__ == "__main__":
    run_data_cleansing()

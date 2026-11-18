"""Shared paths, entrant definitions and national share loader for O3."""

from datetime import date
from pathlib import Path

import pandas as pd

O3 = Path(__file__).resolve().parents[1]
DATA = O3.parent / "data"
RAW = DATA / "raw" / "carrier_monthly.csv"
TABLES = O3 / "output" / "tables"
FIGURES = O3 / "output" / "figures"

ENTRANTS = [
    "Vistara", "Akasa Air", "TruJet", "Star Air", "Fly91",
    "Flybig", "Zoom Air", "India One Air", "Air Deccan",
]

# Operating status at the July 2026 data cutoff.
OUTCOMES = {
    "Vistara": "Merged",
    "Akasa Air": "Operating",
    "Star Air": "Operating",
    "Fly91": "Operating",
    "India One Air": "Operating",
    "TruJet": "Ceased",
    "Flybig": "Ceased",
    "Zoom Air": "Ceased",
    "Air Deccan": "Ceased",
}

ALL_BRANDS = ENTRANTS + [
    "Air Pegasus", "Air Carnival", "Air Odisha", "Air Heritage",
    "Pawan Hans", "Air Taxi", "AIX Connect",
]

# Vistara flights are relabelled as Air India flights from this date.
VISTARA_MERGER = date(2024, 11, 12)

# An entrant is meaningful at this national share, persistent if held this long.
MEANINGFUL_SHARE = 1.0
PERSISTENT_MONTHS = 24


def load_national_shares() -> pd.DataFrame:
    """Return scheduled-domestic airline-months with national passenger share."""
    df = pd.read_csv(RAW)
    df = df[
        (df["service_type"] == "scheduled_domestic") & (df["passengers"] > 0)
    ].copy()
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    monthly_total = df.groupby("date")["passengers"].sum().rename("tot")
    df = df.join(monthly_total, on="date")
    df["share"] = 100 * df["passengers"] / df["tot"]
    return df


def get_airline_data(df: pd.DataFrame, airline: str) -> pd.DataFrame:
    """Return an airline's passenger records ordered by month."""
    return df[df["airline"] == airline].sort_values("date").copy()


def get_event_time_data(df: pd.DataFrame, airline: str) -> pd.DataFrame:
    """Index an airline's months by tau, months since its first passenger month."""
    airline_data = get_airline_data(df, airline)
    if airline_data.empty:
        return airline_data
    first_date = airline_data["date"].min()
    airline_data["tau"] = (
        (airline_data["date"].dt.year - first_date.year) * 12
        + airline_data["date"].dt.month
        - first_date.month
    )
    return airline_data.set_index("tau")


def write_latex_rows(rows: list[str], filename: str) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / filename).write_text("\n".join(rows) + "\n", encoding="utf-8")


def latex_row(*cells) -> str:
    """Join cells into a table row followed by a horizontal rule."""
    return " & ".join(str(cell) for cell in cells) + " \\\\\n\\hline"

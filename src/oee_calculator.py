from __future__ import annotations

from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "planned_minutes",
    "downtime_minutes",
    "operating_minutes",
    "ideal_cycle_time_sec",
    "total_units",
    "good_units",
}


def add_oee_metrics(production: pd.DataFrame) -> pd.DataFrame:
    """Return production rows with row-level OEE components.

    Row-level metrics are useful for display, but aggregate OEE should be
    calculated from summed time and output values via `summarize_oee`.
    """
    missing = REQUIRED_COLUMNS.difference(production.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = production.copy()
    if df.empty:
        for column in ["availability", "performance", "quality", "oee", "scrap_rate"]:
            df[column] = pd.Series(dtype="float64")
        return df
    df["availability"] = safe_divide(
        df["planned_minutes"] - df["downtime_minutes"], df["planned_minutes"]
    )
    df["performance"] = safe_divide(
        (df["ideal_cycle_time_sec"] * df["total_units"]) / 60,
        df["operating_minutes"],
    ).clip(upper=1)
    df["quality"] = safe_divide(df["good_units"], df["total_units"])
    df["oee"] = df["availability"] * df["performance"] * df["quality"]
    df["scrap_rate"] = 1 - df["quality"]
    return df


def summarize_oee(production: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
    """Aggregate OEE correctly across lines, shifts, products or dates.

    Performance is weighted by ideal production time, so products with different
    ideal cycle times are not averaged incorrectly.
    """
    if production.empty:
        return empty_summary(group_by)

    df = add_oee_metrics(production)
    if "scrap_units" not in df.columns:
        df["scrap_units"] = df["total_units"] - df["good_units"]
    grouped = (
        df.groupby(group_by, as_index=False)
        .agg(
            planned_minutes=("planned_minutes", "sum"),
            downtime_minutes=("downtime_minutes", "sum"),
            operating_minutes=("operating_minutes", "sum"),
            total_units=("total_units", "sum"),
            good_units=("good_units", "sum"),
            scrap_units=("scrap_units", "sum"),
        )
    )
    grouped["availability"] = safe_divide(
        grouped["planned_minutes"] - grouped["downtime_minutes"],
        grouped["planned_minutes"],
    )
    grouped["quality"] = safe_divide(grouped["good_units"], grouped["total_units"])
    grouped["performance"] = safe_divide(
        ideal_production_minutes(df, group_by).to_numpy(),
        grouped["operating_minutes"],
    ).clip(upper=1)
    grouped["oee"] = grouped["availability"] * grouped["performance"] * grouped["quality"]
    grouped["scrap_rate"] = 1 - grouped["quality"]
    return grouped


def summarize_overall(production: pd.DataFrame) -> dict[str, float]:
    """Calculate overall manufacturing KPIs for a filtered production dataset."""
    if production.empty:
        return {
            "oee": 0.0,
            "availability": 0.0,
            "performance": 0.0,
            "quality": 0.0,
            "scrap_rate": 0.0,
            "planned_minutes": 0.0,
            "downtime_minutes": 0.0,
            "operating_minutes": 0.0,
            "total_units": 0.0,
            "good_units": 0.0,
            "scrap_units": 0.0,
        }

    df = production.copy()
    if "scrap_units" not in df.columns:
        df["scrap_units"] = df["total_units"] - df["good_units"]

    totals = df[
        [
            "planned_minutes",
            "downtime_minutes",
            "operating_minutes",
            "total_units",
            "good_units",
            "scrap_units",
        ]
    ].sum()
    availability = divide_scalar(
        totals["planned_minutes"] - totals["downtime_minutes"], totals["planned_minutes"]
    )
    performance = min(
        divide_scalar(
            ((df["ideal_cycle_time_sec"] * df["total_units"]) / 60).sum(),
            totals["operating_minutes"],
        ),
        1.0,
    )
    quality = divide_scalar(totals["good_units"], totals["total_units"])
    oee = availability * performance * quality
    return {
        "oee": oee,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "scrap_rate": 1 - quality if totals["total_units"] else 0.0,
        **{key: float(value) for key, value in totals.items()},
    }


def ideal_production_minutes(df: pd.DataFrame, group_by: Iterable[str]) -> pd.Series:
    return df.assign(
        ideal_minutes=(df["ideal_cycle_time_sec"] * df["total_units"]) / 60
    ).groupby(list(group_by))["ideal_minutes"].sum()


def empty_summary(group_by: list[str]) -> pd.DataFrame:
    columns = group_by + [
        "planned_minutes",
        "downtime_minutes",
        "operating_minutes",
        "total_units",
        "good_units",
        "scrap_units",
        "availability",
        "quality",
        "performance",
        "oee",
        "scrap_rate",
    ]
    return pd.DataFrame(columns=columns)


def safe_divide(numerator, denominator):
    result = numerator / denominator.replace(0, pd.NA) if hasattr(denominator, "replace") else divide_scalar(numerator, denominator)
    if hasattr(result, "fillna"):
        return result.fillna(0).astype(float)
    return result


def divide_scalar(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else float(numerator / denominator)

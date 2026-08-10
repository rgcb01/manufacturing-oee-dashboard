from __future__ import annotations

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
    missing = REQUIRED_COLUMNS.difference(production.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = production.copy()
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
    df = add_oee_metrics(production)
    grouped = (
        df.groupby(group_by, as_index=False)
        .agg(
            planned_minutes=("planned_minutes", "sum"),
            downtime_minutes=("downtime_minutes", "sum"),
            operating_minutes=("operating_minutes", "sum"),
            total_units=("total_units", "sum"),
            good_units=("good_units", "sum"),
        )
    )
    grouped["availability"] = safe_divide(
        grouped["planned_minutes"] - grouped["downtime_minutes"],
        grouped["planned_minutes"],
    )
    grouped["quality"] = safe_divide(grouped["good_units"], grouped["total_units"])
    grouped["performance"] = safe_divide(
        df.groupby(group_by)
        .apply(
            lambda part: ((part["ideal_cycle_time_sec"] * part["total_units"]) / 60).sum(),
            include_groups=False,
        )
        .to_numpy(),
        grouped["operating_minutes"],
    ).clip(upper=1)
    grouped["oee"] = grouped["availability"] * grouped["performance"] * grouped["quality"]
    grouped["scrap_rate"] = 1 - grouped["quality"]
    return grouped


def safe_divide(numerator, denominator):
    result = numerator / denominator.replace(0, pd.NA) if hasattr(denominator, "replace") else numerator / denominator
    if hasattr(result, "fillna"):
        return result.fillna(0)
    return 0 if denominator == 0 else result

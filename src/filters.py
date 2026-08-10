from __future__ import annotations

from datetime import date

import pandas as pd


def filter_scope(
    df: pd.DataFrame,
    lines: list[str],
    shifts: list[str],
    products: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Apply common line, shift, product and date filters to a dataset."""
    if df.empty or not lines or not shifts or not products:
        return df.iloc[0:0].copy()

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    return data[
        data["line"].isin(lines)
        & data["shift"].isin(shifts)
        & data["product"].isin(products)
        & (data["date"].dt.date >= start_date)
        & (data["date"].dt.date <= end_date)
    ].copy()


def previous_period_dates(start_date: date, end_date: date) -> tuple[date, date]:
    """Return the immediately preceding period with the same inclusive duration."""
    days = (end_date - start_date).days + 1
    previous_end = start_date - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=days - 1)
    return previous_start.date() if hasattr(previous_start, "date") else previous_start, previous_end.date() if hasattr(previous_end, "date") else previous_end

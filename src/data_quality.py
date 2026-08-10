from __future__ import annotations

import pandas as pd


KEYS = ["date", "line", "shift", "product"]


def validate_event_consistency(
    production: pd.DataFrame, downtime: pd.DataFrame, scrap: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Compare production totals against downtime and scrap event tables."""
    prod = production.copy()
    prod["date"] = pd.to_datetime(prod["date"]).dt.strftime("%Y-%m-%d")

    down = downtime.copy()
    scrap_df = scrap.copy()
    if not down.empty:
        down["date"] = pd.to_datetime(down["date"]).dt.strftime("%Y-%m-%d")
    if not scrap_df.empty:
        scrap_df["date"] = pd.to_datetime(scrap_df["date"]).dt.strftime("%Y-%m-%d")

    down_totals = (
        down.groupby(KEYS, as_index=False)["duration_minutes"].sum()
        if not down.empty
        else pd.DataFrame(columns=KEYS + ["duration_minutes"])
    )
    scrap_totals = (
        scrap_df.groupby(KEYS, as_index=False)["quantity"].sum()
        if not scrap_df.empty
        else pd.DataFrame(columns=KEYS + ["quantity"])
    )

    downtime_check = prod[KEYS + ["downtime_minutes"]].merge(down_totals, on=KEYS, how="left")
    downtime_check["duration_minutes"] = downtime_check["duration_minutes"].fillna(0)
    downtime_check["difference"] = downtime_check["downtime_minutes"] - downtime_check["duration_minutes"]

    scrap_check = prod[KEYS + ["scrap_units"]].merge(scrap_totals, on=KEYS, how="left")
    scrap_check["quantity"] = scrap_check["quantity"].fillna(0)
    scrap_check["difference"] = scrap_check["scrap_units"] - scrap_check["quantity"]

    return {
        "downtime": downtime_check[downtime_check["difference"] != 0],
        "scrap": scrap_check[scrap_check["difference"] != 0],
    }

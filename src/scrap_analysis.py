from __future__ import annotations

import pandas as pd


def scrap_by_reason(scrap: pd.DataFrame) -> pd.DataFrame:
    return (
        scrap.groupby("reason", as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
    )


def scrap_by_line(scrap: pd.DataFrame) -> pd.DataFrame:
    return (
        scrap.groupby("line", as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
    )

from __future__ import annotations

import pandas as pd


def downtime_by_reason(downtime: pd.DataFrame) -> pd.DataFrame:
    return (
        downtime.groupby("reason", as_index=False)["duration_minutes"]
        .sum()
        .sort_values("duration_minutes", ascending=False)
    )


def downtime_by_line_shift(downtime: pd.DataFrame) -> pd.DataFrame:
    return (
        downtime.groupby(["line", "shift"], as_index=False)["duration_minutes"]
        .sum()
        .sort_values("duration_minutes", ascending=False)
    )

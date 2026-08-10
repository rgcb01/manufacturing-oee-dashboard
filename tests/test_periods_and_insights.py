from datetime import date

import pandas as pd

from src.engineering_insights import ranked_insights
from src.filters import filter_scope, previous_period_dates


def test_previous_period_uses_same_inclusive_duration():
    start, end = previous_period_dates(date(2026, 7, 8), date(2026, 7, 14))

    assert start == date(2026, 7, 1)
    assert end == date(2026, 7, 7)


def test_filter_scope_applies_line_shift_product_and_dates():
    df = pd.DataFrame(
        [
            {"date": "2026-07-01", "line": "Line-A", "shift": "Shift-1", "product": "A"},
            {"date": "2026-07-02", "line": "Line-B", "shift": "Shift-1", "product": "A"},
        ]
    )

    result = filter_scope(df, ["Line-A"], ["Shift-1"], ["A"], date(2026, 7, 1), date(2026, 7, 1))

    assert len(result) == 1
    assert result.iloc[0]["line"] == "Line-A"


def test_ranked_insights_detects_poor_line_shift():
    production = pd.DataFrame(
        [
            good_row("Line-A", "Shift-1", 90, 89),
            good_row("Line-B", "Shift-2", 70, 60),
        ]
    )
    downtime = pd.DataFrame(
        [{"date": "2026-07-01", "line": "Line-B", "shift": "Shift-2", "product": "P", "reason": "Maintenance", "duration_minutes": 30}]
    )
    scrap = pd.DataFrame(
        [{"date": "2026-07-01", "line": "Line-B", "shift": "Shift-2", "product": "P", "reason": "Surface defect", "quantity": 10}]
    )

    insights = ranked_insights(production, downtime, scrap)

    assert any("Line-B / Shift-2" in insight.finding for insight in insights)


def test_ranked_insights_handles_empty_data():
    insights = ranked_insights(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    assert insights[0].title == "No Data Selected"


def test_ranked_insights_handles_healthy_data_without_crashing():
    production = pd.DataFrame([good_row("Line-A", "Shift-1", 98, 98)])

    insights = ranked_insights(production, pd.DataFrame(), pd.DataFrame())

    assert isinstance(insights, list)


def good_row(line, shift, total_units, good_units):
    return {
        "date": "2026-07-01",
        "line": line,
        "shift": shift,
        "product": "P",
        "planned_minutes": 100,
        "downtime_minutes": 5,
        "operating_minutes": 95,
        "ideal_cycle_time_sec": 55,
        "total_units": total_units,
        "good_units": good_units,
        "scrap_units": total_units - good_units,
    }

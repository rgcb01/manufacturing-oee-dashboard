import pandas as pd

from src.oee_calculator import add_oee_metrics, summarize_oee


def test_add_oee_metrics_calculates_expected_values():
    production = pd.DataFrame(
        [
            {
                "planned_minutes": 100,
                "downtime_minutes": 10,
                "operating_minutes": 90,
                "ideal_cycle_time_sec": 60,
                "total_units": 80,
                "good_units": 76,
            }
        ]
    )

    result = add_oee_metrics(production)

    assert result.loc[0, "availability"] == 0.9
    assert round(result.loc[0, "performance"], 4) == round(80 / 90, 4)
    assert result.loc[0, "quality"] == 0.95
    assert round(result.loc[0, "oee"], 4) == round(0.9 * (80 / 90) * 0.95, 4)


def test_summarize_oee_groups_by_line():
    production = pd.DataFrame(
        [
            {
                "line": "Line-A",
                "planned_minutes": 100,
                "downtime_minutes": 20,
                "operating_minutes": 80,
                "ideal_cycle_time_sec": 60,
                "total_units": 70,
                "good_units": 68,
            },
            {
                "line": "Line-A",
                "planned_minutes": 100,
                "downtime_minutes": 0,
                "operating_minutes": 100,
                "ideal_cycle_time_sec": 60,
                "total_units": 90,
                "good_units": 90,
            },
        ]
    )

    result = summarize_oee(production, ["line"])

    assert len(result) == 1
    assert result.loc[0, "line"] == "Line-A"
    assert result.loc[0, "total_units"] == 160

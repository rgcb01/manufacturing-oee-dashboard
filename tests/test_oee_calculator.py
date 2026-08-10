import pandas as pd

from src.oee_calculator import add_oee_metrics, summarize_oee, summarize_overall


def row(**overrides):
    data = {
        "line": "Line-A",
        "product": "Housing",
        "planned_minutes": 100,
        "downtime_minutes": 10,
        "operating_minutes": 90,
        "ideal_cycle_time_sec": 60,
        "total_units": 80,
        "good_units": 76,
        "scrap_units": 4,
    }
    data.update(overrides)
    return data


def test_add_oee_metrics_calculates_expected_values():
    result = add_oee_metrics(pd.DataFrame([row()]))

    assert result.loc[0, "availability"] == 0.9
    assert round(result.loc[0, "performance"], 4) == round(80 / 90, 4)
    assert result.loc[0, "quality"] == 0.95
    assert round(result.loc[0, "oee"], 4) == round(0.9 * (80 / 90) * 0.95, 4)


def test_zero_planned_time_returns_zero_availability_and_oee():
    result = add_oee_metrics(pd.DataFrame([row(planned_minutes=0, downtime_minutes=0)]))

    assert result.loc[0, "availability"] == 0
    assert result.loc[0, "oee"] == 0


def test_zero_production_returns_zero_quality():
    result = add_oee_metrics(pd.DataFrame([row(total_units=0, good_units=0, scrap_units=0)]))

    assert result.loc[0, "quality"] == 0
    assert result.loc[0, "scrap_rate"] == 1


def test_full_scrap_returns_zero_quality():
    result = add_oee_metrics(pd.DataFrame([row(total_units=80, good_units=0, scrap_units=80)]))

    assert result.loc[0, "quality"] == 0
    assert result.loc[0, "scrap_rate"] == 1


def test_performance_is_capped_at_100_percent():
    result = add_oee_metrics(pd.DataFrame([row(operating_minutes=40, total_units=80)]))

    assert result.loc[0, "performance"] == 1


def test_summarize_oee_groups_by_line():
    production = pd.DataFrame(
        [
            row(line="Line-A", planned_minutes=100, downtime_minutes=20, operating_minutes=80, total_units=70, good_units=68, scrap_units=2),
            row(line="Line-A", planned_minutes=100, downtime_minutes=0, operating_minutes=100, total_units=90, good_units=90, scrap_units=0),
        ]
    )

    result = summarize_oee(production, ["line"])

    assert len(result) == 1
    assert result.loc[0, "line"] == "Line-A"
    assert result.loc[0, "total_units"] == 160
    assert round(result.loc[0, "availability"], 4) == 0.9


def test_aggregation_across_products_uses_weighted_ideal_time():
    production = pd.DataFrame(
        [
            row(product="Fast", ideal_cycle_time_sec=30, operating_minutes=100, total_units=100, good_units=100, scrap_units=0),
            row(product="Slow", ideal_cycle_time_sec=60, operating_minutes=100, total_units=80, good_units=80, scrap_units=0),
        ]
    )

    result = summarize_overall(production)

    expected_performance = ((30 * 100 / 60) + (60 * 80 / 60)) / 200
    assert round(result["performance"], 4) == round(expected_performance, 4)

from pathlib import Path

import pandas as pd

from src.data_generator import generate_data
from src.data_quality import validate_event_consistency


def test_data_generator_is_deterministic(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate_data(first, days=5, seed=123)
    generate_data(second, days=5, seed=123)

    assert (first / "synthetic_production_data.csv").read_text() == (
        second / "synthetic_production_data.csv"
    ).read_text()
    assert (first / "downtime_events.csv").read_text() == (second / "downtime_events.csv").read_text()
    assert (first / "scrap_events.csv").read_text() == (second / "scrap_events.csv").read_text()


def test_generated_event_tables_match_production_totals(tmp_path: Path):
    generate_data(tmp_path, days=10, seed=42)
    production = pd.read_csv(tmp_path / "synthetic_production_data.csv")
    downtime = pd.read_csv(tmp_path / "downtime_events.csv")
    scrap = pd.read_csv(tmp_path / "scrap_events.csv")

    checks = validate_event_consistency(production, downtime, scrap)

    assert checks["downtime"].empty
    assert checks["scrap"].empty


def test_intentional_quality_issue_is_discoverable(tmp_path: Path):
    generate_data(tmp_path, days=30, seed=42)
    production = pd.read_csv(tmp_path / "synthetic_production_data.csv")
    grouped = production.groupby(["line", "shift"]).agg(
        total_units=("total_units", "sum"),
        good_units=("good_units", "sum"),
    )
    grouped["scrap_rate"] = 1 - grouped["good_units"] / grouped["total_units"]

    worst_quality_combo = grouped.sort_values("scrap_rate", ascending=False).index[0]

    assert worst_quality_combo == ("Line-B", "Shift-2")

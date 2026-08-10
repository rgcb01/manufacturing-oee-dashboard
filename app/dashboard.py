from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.downtime_analysis import downtime_by_reason
from src.oee_calculator import add_oee_metrics, summarize_oee
from src.scrap_analysis import scrap_by_reason


DATA_DIR = PROJECT_ROOT / "data"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    production = pd.read_csv(DATA_DIR / "synthetic_production_data.csv", parse_dates=["date"])
    downtime = pd.read_csv(DATA_DIR / "downtime_events.csv", parse_dates=["date"])
    scrap = pd.read_csv(DATA_DIR / "scrap_events.csv", parse_dates=["date"])
    return production, downtime, scrap


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    st.set_page_config(page_title="Manufacturing OEE Dashboard", layout="wide")
    st.title("Manufacturing Production Dashboard")
    st.caption(
        "Synthetic portfolio project for OEE, scrap, downtime and production monitoring."
    )

    production, downtime, scrap = load_data()

    line_options = sorted(production["line"].unique())
    shift_options = sorted(production["shift"].unique())

    with st.sidebar:
        st.header("Filters")
        selected_lines = st.multiselect("Line", line_options, default=line_options)
        selected_shifts = st.multiselect("Shift", shift_options, default=shift_options)
        date_range = st.date_input(
            "Date range",
            value=(production["date"].min().date(), production["date"].max().date()),
        )

    start_date, end_date = date_range
    production_filtered = production[
        production["line"].isin(selected_lines)
        & production["shift"].isin(selected_shifts)
        & (production["date"].dt.date >= start_date)
        & (production["date"].dt.date <= end_date)
    ]
    downtime_filtered = downtime[
        downtime["line"].isin(selected_lines)
        & downtime["shift"].isin(selected_shifts)
        & (downtime["date"].dt.date >= start_date)
        & (downtime["date"].dt.date <= end_date)
    ]
    scrap_filtered = scrap[
        scrap["line"].isin(selected_lines)
        & scrap["shift"].isin(selected_shifts)
        & (scrap["date"].dt.date >= start_date)
        & (scrap["date"].dt.date <= end_date)
    ]

    metrics = add_oee_metrics(production_filtered)
    summary = summarize_oee(production_filtered, ["line"])

    total_planned = metrics["planned_minutes"].sum()
    total_downtime = metrics["downtime_minutes"].sum()
    total_units = metrics["total_units"].sum()
    total_good = metrics["good_units"].sum()
    availability = (total_planned - total_downtime) / total_planned if total_planned else 0
    quality = total_good / total_units if total_units else 0
    performance = (
        ((metrics["ideal_cycle_time_sec"] * metrics["total_units"]) / 60).sum()
        / metrics["operating_minutes"].sum()
        if metrics["operating_minutes"].sum()
        else 0
    )
    performance = min(performance, 1)
    oee = availability * performance * quality

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("OEE", percent(oee))
    kpi_cols[1].metric("Availability", percent(availability))
    kpi_cols[2].metric("Performance", percent(performance))
    kpi_cols[3].metric("Quality", percent(quality))
    kpi_cols[4].metric("Scrap Rate", percent(1 - quality))

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("OEE by Line")
        st.plotly_chart(
            px.bar(summary, x="line", y="oee", text_auto=".1%", range_y=[0, 1]),
            use_container_width=True,
        )

    with chart_cols[1]:
        st.subheader("Daily OEE Trend")
        daily = summarize_oee(production_filtered, ["date"])
        st.plotly_chart(
            px.line(daily, x="date", y="oee", markers=True),
            use_container_width=True,
        )

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("Downtime Pareto")
        st.plotly_chart(
            px.bar(downtime_by_reason(downtime_filtered), x="reason", y="duration_minutes"),
            use_container_width=True,
        )

    with chart_cols[1]:
        st.subheader("Scrap Pareto")
        st.plotly_chart(
            px.bar(scrap_by_reason(scrap_filtered), x="reason", y="quantity"),
            use_container_width=True,
        )

    st.subheader("Filtered Production Records")
    st.dataframe(metrics.sort_values(["date", "line", "shift"]), use_container_width=True)


if __name__ == "__main__":
    main()

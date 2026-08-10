from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.config import TARGET_LABELS
from src.database import load_csv_data, load_manufacturing_data
from src.engineering_insights import (
    daily_monitoring,
    improvement_comparison,
    kpi_scorecard,
    line_shift_matrix,
    loss_breakdown,
    manufacturing_status,
    pareto_inputs,
    previous_scope,
    product_performance,
    ranked_insights,
)
from src.filters import filter_scope
from src.oee_calculator import add_oee_metrics, summarize_oee, summarize_overall
from src.pareto import pareto_sentence


DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "manufacturing.db"


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if DB_PATH.exists():
        return load_manufacturing_data(DB_PATH)
    return load_csv_data(DATA_DIR)


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def pp(value: float | None) -> str:
    if value is None:
        return "No previous period"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f} pp"


def metric_label(metric: str) -> str:
    labels = {
        "oee": "OEE",
        "availability": "Availability",
        "performance": "Performance",
        "quality": "Quality",
        "scrap_rate": "Scrap Rate",
        "downtime_minutes": "Downtime Minutes",
        "total_units": "Total Units",
        "good_units": "Good Units",
    }
    return labels.get(metric, metric.replace("_", " ").title())


def normalize_dates(date_range) -> tuple[date, date] | None:
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        return None
    start_date, end_date = date_range
    if start_date > end_date:
        return None
    return start_date, end_date


def pareto_figure(pareto: pd.DataFrame, category: str, value: str, title: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if pareto.empty:
        fig.update_layout(title=title)
        return fig
    fig.add_bar(x=pareto[category], y=pareto[value], name="Loss")
    fig.add_scatter(
        x=pareto[category],
        y=pareto["cumulative_pct"] * 100,
        name="Cumulative %",
        mode="lines+markers",
        secondary_y=True,
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#64748B", secondary_y=True)
    fig.update_yaxes(title_text=value.replace("_", " ").title(), secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
    fig.update_layout(title=title, hovermode="x unified", legend_orientation="h")
    return fig


def scorecard_card(column, label: str, data: dict[str, float | str | None], percentage: bool = True) -> None:
    current = data["current"]
    value_text = percent(float(current)) if percentage else f"{float(current):,.0f}"
    previous = data["previous_delta"]
    target = data["target"]
    target_delta = data["target_delta"]
    help_text = ""
    if percentage and target is not None:
        help_text = f"Target: {percent(float(target))} | Target delta: {pp(float(target_delta))}"
    column.metric(label, value_text, delta=pp(float(previous)) if percentage and previous is not None else None, help=help_text)
    column.caption(str(data["status"]))


def render_empty_state() -> None:
    st.warning("No production records match the selected filters. Adjust date range, line, shift or product selections.")


def main() -> None:
    st.set_page_config(page_title="Manufacturing OEE & Loss Analysis", layout="wide")
    st.title("Manufacturing OEE & Loss Analysis")
    st.caption("Production Data -> KPI Monitoring -> Loss Detection -> Root-Cause Exploration -> Engineering Insights")

    production, downtime, scrap = load_data()
    production["date"] = pd.to_datetime(production["date"])
    downtime["date"] = pd.to_datetime(downtime["date"])
    scrap["date"] = pd.to_datetime(scrap["date"])

    line_options = sorted(production["line"].unique())
    shift_options = sorted(production["shift"].unique())
    product_options = sorted(production["product"].unique())

    with st.sidebar:
        st.header("Active Scope")
        selected_lines = st.multiselect("Line", line_options, default=line_options)
        selected_shifts = st.multiselect("Shift", shift_options, default=shift_options)
        selected_products = st.multiselect("Product", product_options, default=product_options)
        date_range = st.date_input(
            "Date range",
            value=(production["date"].min().date(), production["date"].max().date()),
        )
        heatmap_metric = st.selectbox(
            "Heatmap metric",
            ["oee", "availability", "performance", "quality", "scrap_rate"],
            format_func=metric_label,
        )

    selected_dates = normalize_dates(date_range)
    if selected_dates is None:
        st.error("Select a valid start and end date.")
        return
    start_date, end_date = selected_dates

    production_filtered = filter_scope(production, selected_lines, selected_shifts, selected_products, start_date, end_date)
    downtime_filtered = filter_scope(downtime, selected_lines, selected_shifts, selected_products, start_date, end_date)
    scrap_filtered = filter_scope(scrap, selected_lines, selected_shifts, selected_products, start_date, end_date)
    previous_production, previous_downtime, previous_scrap, previous_dates = previous_scope(
        production,
        downtime,
        scrap,
        selected_lines,
        selected_shifts,
        selected_products,
        start_date,
        end_date,
    )

    st.markdown(
        f"**Selected period:** {start_date} to {end_date} | "
        f"**Previous comparison:** {previous_dates[0]} to {previous_dates[1]}"
    )

    if production_filtered.empty:
        render_empty_state()
        return

    st.subheader("Manufacturing Status")
    status_cols = st.columns(2)
    for index, message in enumerate(manufacturing_status(production_filtered, downtime_filtered, scrap_filtered)):
        status_cols[index % 2].info(message)

    st.subheader("KPI Scorecard")
    scorecard = kpi_scorecard(production_filtered, previous_production)
    cols = st.columns(4)
    for idx, kpi in enumerate(["oee", "availability", "performance", "quality"]):
        scorecard_card(cols[idx], TARGET_LABELS[kpi], scorecard[kpi], percentage=True)
    cols = st.columns(4)
    scorecard_card(cols[0], "Scrap Rate", scorecard["scrap_rate"], percentage=True)
    scorecard_card(cols[1], "Total Units", scorecard["total_units"], percentage=False)
    scorecard_card(cols[2], "Good Units", scorecard["good_units"], percentage=False)
    scorecard_card(cols[3], "Downtime Minutes", scorecard["downtime_minutes"], percentage=False)

    st.subheader("OEE Analysis")
    daily = daily_monitoring(production_filtered)
    loss_table, loss_explanation = loss_breakdown(production_filtered)
    analysis_cols = st.columns(2)
    with analysis_cols[0]:
        fig = px.line(daily, x="date", y="oee", markers=True, title="Daily OEE Trend")
        fig.add_hline(y=0.85, line_dash="dash", annotation_text="OEE Target 85%")
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)
    with analysis_cols[1]:
        fig = px.bar(
            loss_table,
            x="component",
            y=["value", "target"],
            barmode="group",
            title="OEE Loss Breakdown",
        )
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)
        st.info(loss_explanation)

    line_summary = summarize_oee(production_filtered, ["line"])
    fig = px.bar(line_summary, x="line", y="oee", text_auto=".1%", title="OEE by Line", range_y=[0, 1])
    fig.add_hline(y=0.85, line_dash="dash", annotation_text="Target")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Manufacturing Performance Matrix")
    matrix = line_shift_matrix(production_filtered, heatmap_metric)
    if matrix.empty:
        st.info("No line x shift matrix is available for the selected scope.")
    else:
        fig = px.imshow(
            matrix,
            text_auto=".1%" if heatmap_metric in {"oee", "availability", "performance", "quality", "scrap_rate"} else True,
            aspect="auto",
            color_continuous_scale="Blues_r" if heatmap_metric == "scrap_rate" else "Blues",
            title=f"Line x Shift {metric_label(heatmap_metric)}",
        )
        fig.update_coloraxes(colorbar_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Loss Analysis")
    downtime_pareto, scrap_pareto = pareto_inputs(downtime_filtered, scrap_filtered)
    pareto_cols = st.columns(2)
    with pareto_cols[0]:
        st.plotly_chart(
            pareto_figure(downtime_pareto, "reason", "duration_minutes", "Downtime Pareto"),
            use_container_width=True,
        )
        st.caption(pareto_sentence(downtime_pareto, "reason", "downtime"))
    with pareto_cols[1]:
        st.plotly_chart(
            pareto_figure(scrap_pareto, "reason", "quantity", "Scrap Pareto"),
            use_container_width=True,
        )
        st.caption(pareto_sentence(scrap_pareto, "reason", "scrap"))

    st.subheader("Product Performance")
    products = product_performance(production_filtered, downtime_filtered)
    if products.empty:
        st.info("No product data is available for the selected scope.")
    else:
        worst_product = products.sort_values("oee").iloc[0]
        st.info(f"Worst-performing product: {worst_product['product']} at {percent(worst_product['oee'])} OEE.")
        product_cols = st.columns(3)
        product_cols[0].plotly_chart(px.bar(products, x="product", y="oee", title="OEE by Product", text_auto=".1%"), use_container_width=True)
        product_cols[1].plotly_chart(px.bar(products, x="product", y="scrap_rate", title="Scrap Rate by Product", text_auto=".1%"), use_container_width=True)
        product_cols[2].plotly_chart(px.bar(products, x="product", y="total_units", title="Total Units by Product"), use_container_width=True)
        st.plotly_chart(px.bar(products, x="product", y="duration_minutes", title="Downtime Minutes by Product"), use_container_width=True)

    st.subheader("SPC / Process Monitoring")
    monitor_cols = st.columns(3)
    for column, metric in zip(monitor_cols, ["oee", "scrap_rate", "downtime_minutes"]):
        fig = px.line(daily, x="date", y=metric, markers=True, title=f"Daily {metric_label(metric)}")
        mean_value = daily[metric].mean() if not daily.empty else 0
        fig.add_hline(y=mean_value, line_dash="dash", annotation_text="Mean")
        if metric in {"oee", "scrap_rate"}:
            fig.update_yaxes(tickformat=".0%")
        column.plotly_chart(fig, use_container_width=True)

    st.subheader("Engineering Insights")
    insights = ranked_insights(production_filtered, downtime_filtered, scrap_filtered, previous_production)
    for insight in insights:
        with st.container(border=True):
            st.markdown(f"**{insight.title}**")
            st.write(f"Finding: {insight.finding}")
            st.write(f"Evidence: {insight.evidence}")
            st.write(f"Suggested investigation: {insight.suggested_investigation}")

    st.subheader("Improvement Analysis")
    min_date = production["date"].min().date()
    max_date = production["date"].max().date()
    comp_cols = st.columns(2)
    with comp_cols[0]:
        baseline_range = st.date_input("Baseline", value=(min_date, min_date + pd.Timedelta(days=6)), key="baseline")
    with comp_cols[1]:
        after_range = st.date_input("After Improvement", value=(max_date - pd.Timedelta(days=6), max_date), key="after")
    baseline_dates = normalize_dates(baseline_range)
    after_dates = normalize_dates(after_range)
    if baseline_dates and after_dates:
        baseline = filter_scope(production, selected_lines, selected_shifts, selected_products, *baseline_dates)
        after = filter_scope(production, selected_lines, selected_shifts, selected_products, *after_dates)
        comparison = improvement_comparison(baseline, after)
        display = comparison.copy()
        display["baseline"] = display.apply(lambda row: percent(row["baseline"]) if row["is_percent"] else f"{row['baseline']:,.0f}", axis=1)
        display["after"] = display.apply(lambda row: percent(row["after"]) if row["is_percent"] else f"{row['after']:,.0f}", axis=1)
        display["delta"] = display.apply(lambda row: pp(row["delta"]) if row["is_percent"] else f"{row['delta']:,.0f}", axis=1)
        st.dataframe(display[["metric", "baseline", "after", "delta"]], use_container_width=True)
    else:
        st.warning("Select valid baseline and after-improvement date ranges.")

    with st.expander("Production Records"):
        st.dataframe(add_oee_metrics(production_filtered).sort_values(["date", "line", "shift"]), use_container_width=True)


if __name__ == "__main__":
    main()

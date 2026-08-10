from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import TARGETS
from src.filters import filter_scope, previous_period_dates
from src.oee_calculator import summarize_oee, summarize_overall
from src.pareto import pareto_table
from src.targets import status_for


@dataclass(frozen=True)
class Insight:
    title: str
    finding: str
    evidence: str
    suggested_investigation: str
    priority: float


def pp(value: float) -> str:
    return f"{value * 100:.1f} pp"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def kpi_scorecard(
    current: pd.DataFrame,
    previous: pd.DataFrame,
) -> dict[str, dict[str, float | str | None]]:
    """Return current KPI values with target and previous-period deltas."""
    current_summary = summarize_overall(current)
    previous_summary = summarize_overall(previous)
    scorecard: dict[str, dict[str, float | str | None]] = {}
    target_map = {
        "oee": TARGETS.oee,
        "availability": TARGETS.availability,
        "performance": TARGETS.performance,
        "quality": TARGETS.quality,
        "scrap_rate": TARGETS.scrap_rate_max,
    }
    for kpi, target in target_map.items():
        current_value = current_summary[kpi]
        previous_value = previous_summary[kpi] if not previous.empty else None
        target_delta = target - current_value if kpi == "scrap_rate" else current_value - target
        previous_delta = (
            None
            if previous_value is None
            else (previous_value - current_value if kpi == "scrap_rate" else current_value - previous_value)
        )
        scorecard[kpi] = {
            "current": current_value,
            "target": target,
            "target_delta": target_delta,
            "previous_delta": previous_delta,
            "status": status_for(kpi, current_value),
        }
    for raw_kpi in ["total_units", "good_units", "downtime_minutes"]:
        scorecard[raw_kpi] = {
            "current": current_summary[raw_kpi],
            "target": None,
            "target_delta": None,
            "previous_delta": (
                None
                if previous.empty
                else current_summary[raw_kpi] - previous_summary[raw_kpi]
            ),
            "status": "Reference",
        }
    return scorecard


def previous_scope(
    production: pd.DataFrame,
    downtime: pd.DataFrame,
    scrap: pd.DataFrame,
    lines: list[str],
    shifts: list[str],
    products: list[str],
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, tuple[date, date]]:
    previous_start, previous_end = previous_period_dates(start_date, end_date)
    return (
        filter_scope(production, lines, shifts, products, previous_start, previous_end),
        filter_scope(downtime, lines, shifts, products, previous_start, previous_end),
        filter_scope(scrap, lines, shifts, products, previous_start, previous_end),
        (previous_start, previous_end),
    )


def manufacturing_status(
    production: pd.DataFrame, downtime: pd.DataFrame, scrap: pd.DataFrame
) -> list[str]:
    """Generate top deterministic status observations for the selected scope."""
    if production.empty:
        return ["No production records are available for the selected scope."]

    plant = summarize_overall(production)
    messages: list[str] = []
    line = worst_group_message(production, ["line"], "line", plant["oee"])
    shift = worst_group_message(production, ["shift"], "shift", plant["oee"])
    combo = worst_group_message(production, ["line", "shift"], "line / shift combination", plant["oee"])
    if combo:
        messages.append(f"Primary Loss Driver: {combo}")
    if line:
        messages.append(f"Worst Line: {line}")
    if shift:
        messages.append(f"Worst Shift: {shift}")

    if not scrap.empty:
        scrap_reason = scrap.groupby("reason")["quantity"].sum().sort_values(ascending=False)
        messages.append(
            f"Highest Scrap Contributor: {scrap_reason.index[0]} accounts for {scrap_reason.iloc[0]:.0f} rejected units."
        )
    if not downtime.empty:
        down_reason = downtime.groupby("reason")["duration_minutes"].sum().sort_values(ascending=False)
        messages.append(
            f"Largest Downtime Contributor: {down_reason.index[0]} accounts for {down_reason.iloc[0]:.0f} minutes."
        )

    loss = largest_oee_loss_component(production)
    messages.append(f"Largest OEE Loss Component: {loss['component']} is the weakest component at {pct(loss['value'])}.")
    return messages[:5]


def worst_group_message(
    production: pd.DataFrame, group_by: list[str], label: str, plant_oee: float
) -> str:
    summary = summarize_oee(production, group_by)
    if summary.empty:
        return ""
    worst = summary.sort_values("oee").iloc[0]
    group_label = " / ".join(str(worst[column]) for column in group_by)
    delta = plant_oee - worst["oee"]
    return f"{group_label} has the lowest OEE at {pct(worst['oee'])}, {pp(delta)} below the plant average."


def largest_oee_loss_component(production: pd.DataFrame) -> dict[str, float | str]:
    summary = summarize_overall(production)
    components = {
        "Availability": summary["availability"],
        "Performance": summary["performance"],
        "Quality": summary["quality"],
    }
    component, value = min(components.items(), key=lambda item: item[1])
    return {"component": component, "value": value}


def loss_breakdown(production: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    summary = summarize_overall(production)
    rows = [
        {"component": "Availability", "value": summary["availability"], "target": TARGETS.availability},
        {"component": "Performance", "value": summary["performance"], "target": TARGETS.performance},
        {"component": "Quality", "value": summary["quality"], "target": TARGETS.quality},
    ]
    table = pd.DataFrame(rows)
    table["gap_to_target"] = table["target"] - table["value"]
    weakest = table.sort_values("gap_to_target", ascending=False).iloc[0]
    explanation = (
        f"{weakest['component']} is currently the largest OEE constraint. "
        f"It is {pp(max(float(weakest['gap_to_target']), 0))} below its target during the selected period."
    )
    return table, explanation


def product_performance(production: pd.DataFrame, downtime: pd.DataFrame) -> pd.DataFrame:
    if production.empty:
        return summarize_oee(production, ["product"])
    product_summary = summarize_oee(production, ["product"])
    downtime_by_product = (
        downtime.groupby("product", as_index=False)["duration_minutes"].sum()
        if not downtime.empty
        else pd.DataFrame({"product": product_summary["product"], "duration_minutes": 0})
    )
    return product_summary.merge(downtime_by_product, on="product", how="left").fillna({"duration_minutes": 0})


def line_shift_matrix(production: pd.DataFrame, metric: str) -> pd.DataFrame:
    summary = summarize_oee(production, ["line", "shift"])
    if summary.empty:
        return pd.DataFrame()
    return summary.pivot(index="line", columns="shift", values=metric)


def daily_monitoring(production: pd.DataFrame) -> pd.DataFrame:
    if production.empty:
        return summarize_oee(production, ["date"])
    return summarize_oee(production, ["date"]).sort_values("date")


def improvement_comparison(baseline: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    baseline_summary = summarize_overall(baseline)
    after_summary = summarize_overall(after)
    rows = []
    for kpi in ["oee", "availability", "performance", "quality", "scrap_rate"]:
        delta = baseline_summary[kpi] - after_summary[kpi] if kpi == "scrap_rate" else after_summary[kpi] - baseline_summary[kpi]
        rows.append(
            {
                "metric": kpi,
                "baseline": baseline_summary[kpi],
                "after": after_summary[kpi],
                "delta": delta,
                "is_percent": True,
            }
        )
    for kpi in ["downtime_minutes", "total_units"]:
        rows.append(
            {
                "metric": kpi,
                "baseline": baseline_summary[kpi],
                "after": after_summary[kpi],
                "delta": after_summary[kpi] - baseline_summary[kpi],
                "is_percent": False,
            }
        )
    return pd.DataFrame(rows)


def ranked_insights(
    production: pd.DataFrame,
    downtime: pd.DataFrame,
    scrap: pd.DataFrame,
    previous_production: pd.DataFrame | None = None,
) -> list[Insight]:
    """Generate 3-5 deterministic engineering insights ranked by severity."""
    if production.empty:
        return [
            Insight(
                "No Data Selected",
                "No production records match the selected filters.",
                "The current scope has zero production rows.",
                "Review date, line, shift and product filters before drawing conclusions.",
                1.0,
            )
        ]

    insights: list[Insight] = []
    summary = summarize_overall(production)
    if summary["oee"] < TARGETS.oee:
        insights.append(
            Insight(
                "OEE Below Target",
                f"OEE is {pct(summary['oee'])}, below the {pct(TARGETS.oee)} target.",
                f"Gap to target: {pp(TARGETS.oee - summary['oee'])}.",
                "Review the weakest OEE component and focus on the largest line/shift losses first.",
                TARGETS.oee - summary["oee"],
            )
        )

    if previous_production is not None and not previous_production.empty:
        previous = summarize_overall(previous_production)
        decline = previous["oee"] - summary["oee"]
        if decline > 0.03:
            insights.append(
                Insight(
                    "OEE Decline Versus Previous Period",
                    f"OEE declined by {pp(decline)} versus the previous comparable period.",
                    f"Previous period: {pct(previous['oee'])}. Current period: {pct(summary['oee'])}.",
                    "Check whether the decline is concentrated by line, shift, product or loss category.",
                    decline,
                )
            )

    line_shift = summarize_oee(production, ["line", "shift"])
    if not line_shift.empty:
        worst = line_shift.sort_values("oee").iloc[0]
        avg = summary["oee"]
        gap = avg - worst["oee"]
        if gap > 0.02:
            insights.append(
                Insight(
                    "Low-Performing Line / Shift",
                    f"{worst['line']} / {worst['shift']} has the lowest OEE at {pct(worst['oee'])}.",
                    f"Plant average: {pct(avg)}. Difference: {pp(gap)}.",
                    "Review downtime events, scrap reasons, product mix and staffing conditions for this combination.",
                    gap,
                )
            )

    if not scrap.empty:
        scrap_combo = summarize_oee(production, ["line", "shift"]).sort_values("scrap_rate", ascending=False).iloc[0]
        avg_scrap = summary["scrap_rate"]
        gap = scrap_combo["scrap_rate"] - avg_scrap
        if gap > 0.01:
            insights.append(
                Insight(
                    "High Scrap Concentration",
                    f"{scrap_combo['line']} / {scrap_combo['shift']} has the highest scrap rate at {pct(scrap_combo['scrap_rate'])}.",
                    f"Plant average: {pct(avg_scrap)}. Difference: +{pp(gap)}.",
                    "Review defect distribution, product mix, tooling condition and process parameters for this line/shift combination.",
                    gap,
                )
            )

        scrap_reason = scrap.groupby("reason")["quantity"].sum().sort_values(ascending=False)
        insights.append(
            Insight(
                "Dominant Scrap Reason",
                f"{scrap_reason.index[0]} is the largest scrap reason.",
                f"Rejected units: {scrap_reason.iloc[0]:.0f}.",
                "Check inspection records and process settings associated with this defect category.",
                scrap_reason.iloc[0] / max(scrap_reason.sum(), 1),
            )
        )

    if not downtime.empty:
        down_reason = downtime.groupby("reason")["duration_minutes"].sum().sort_values(ascending=False)
        insights.append(
            Insight(
                "Dominant Downtime Reason",
                f"{down_reason.index[0]} is the largest downtime reason.",
                f"Downtime minutes: {down_reason.iloc[0]:.0f}.",
                "Review maintenance notes, changeover sequence, material availability and recurring stops for this category.",
                down_reason.iloc[0] / max(down_reason.sum(), 1),
            )
        )

    product = product_performance(production, downtime).sort_values("oee")
    if not product.empty and len(product) > 1:
        worst_product = product.iloc[0]
        gap = summary["oee"] - worst_product["oee"]
        if gap > 0.02:
            insights.append(
                Insight(
                    "Product Performance Difference",
                    f"{worst_product['product']} has the lowest product OEE at {pct(worst_product['oee'])}.",
                    f"Plant average: {pct(summary['oee'])}. Difference: {pp(gap)}.",
                    "Review ideal cycle time assumptions, product-specific defects and changeover impact.",
                    gap,
                )
            )

    return sorted(insights, key=lambda item: item.priority, reverse=True)[:5]


def pareto_inputs(downtime: pd.DataFrame, scrap: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pareto_table(downtime, "reason", "duration_minutes"),
        pareto_table(scrap, "reason", "quantity"),
    )

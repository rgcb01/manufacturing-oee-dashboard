from __future__ import annotations

import pandas as pd


def pareto_table(df: pd.DataFrame, category: str, value: str) -> pd.DataFrame:
    """Build a sorted Pareto table with cumulative contribution."""
    if df.empty:
        return pd.DataFrame(columns=[category, value, "cumulative_value", "cumulative_pct"])

    table = (
        df.groupby(category, as_index=False)[value]
        .sum()
        .sort_values(value, ascending=False)
        .reset_index(drop=True)
    )
    total = table[value].sum()
    table["cumulative_value"] = table[value].cumsum()
    table["cumulative_pct"] = table["cumulative_value"] / total if total else 0
    return table


def contributors_to_threshold(
    pareto: pd.DataFrame,
    category: str,
    threshold: float = 0.80,
) -> tuple[list[str], float]:
    """Return the categories required to reach approximately the threshold."""
    if pareto.empty:
        return [], 0.0

    selected = pareto[pareto["cumulative_pct"] <= threshold].copy()
    if selected.empty or selected["cumulative_pct"].max() < threshold:
        next_row = pareto.iloc[[len(selected)]]
        selected = pd.concat([selected, next_row])
    return selected[category].tolist(), float(selected["cumulative_pct"].iloc[-1])


def pareto_sentence(
    pareto: pd.DataFrame,
    category: str,
    loss_name: str,
    threshold: float = 0.80,
) -> str:
    contributors, cumulative = contributors_to_threshold(pareto, category, threshold)
    if not contributors:
        return f"No {loss_name} events are available for the selected scope."
    if len(contributors) == 1:
        joined = contributors[0]
    else:
        joined = ", ".join(contributors[:-1]) + f" and {contributors[-1]}"
    return f"{joined} account for {cumulative * 100:.1f}% of {loss_name}."

import pandas as pd

from src.pareto import contributors_to_threshold, pareto_sentence, pareto_table


def test_pareto_sorts_descending_and_calculates_cumulative_pct():
    df = pd.DataFrame(
        [
            {"reason": "A", "minutes": 30},
            {"reason": "B", "minutes": 50},
            {"reason": "C", "minutes": 20},
        ]
    )

    result = pareto_table(df, "reason", "minutes")

    assert result["reason"].tolist() == ["B", "A", "C"]
    assert result["cumulative_pct"].round(2).tolist() == [0.50, 0.80, 1.00]


def test_contributors_to_80_percent_include_threshold_crossing_row():
    df = pd.DataFrame({"reason": ["B", "A", "C"], "minutes": [50, 30, 20]})
    pareto = pareto_table(df, "reason", "minutes")

    contributors, cumulative = contributors_to_threshold(pareto, "reason", 0.8)

    assert contributors == ["B", "A"]
    assert cumulative == 0.8


def test_pareto_sentence_uses_actual_contributors():
    df = pd.DataFrame({"reason": ["B", "A", "C"], "minutes": [50, 30, 20]})
    pareto = pareto_table(df, "reason", "minutes")

    sentence = pareto_sentence(pareto, "reason", "downtime")

    assert "B and A account for 80.0% of downtime." == sentence

import pandas as pd
from src.checks.completeness import check_missing_values


def test_fully_missing_column_fails():
    df = pd.DataFrame({
        "a": [None, None, None],
        "b": [1, 2, 3],
    })

    result = check_missing_values(df, missing_warn_threshold=0.1)

    assert result["status"] == "fail"
    assert "a" in result["details"]["fully_missing"]


def test_partial_missing_warns():
    df = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": [1, 2, 3, 4],
    })

    result = check_missing_values(df, missing_warn_threshold=0.25)

    assert result["status"] == "warn"
    assert "a" in result["details"]

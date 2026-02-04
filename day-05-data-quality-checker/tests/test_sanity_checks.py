import pandas as pd
from src.checks.sanity import check_duplicate_rows


def test_duplicate_rows_warn():
    df = pd.DataFrame({
        "a": [1, 1, 2],
        "b": ["x", "x", "y"],
    })

    result = check_duplicate_rows(df, fail_threshold=0.5)

    assert result["status"] == "warn"
    assert result["details"]["count"] == 1

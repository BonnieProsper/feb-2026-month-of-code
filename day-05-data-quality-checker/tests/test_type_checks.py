import pandas as pd
from src.checks.types import check_mixed_type_columns


def test_mixed_type_column_warns():
    df = pd.DataFrame({
        "a": ["1", "2", "x"],
        "b": ["y", "z", "w"],
    })

    result = check_mixed_type_columns(df)

    assert result["status"] == "warn"
    assert "a" in result["details"]["columns"]

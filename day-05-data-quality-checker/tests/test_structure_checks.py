import pandas as pd
from checks.structure import check_missing_required_columns


def test_missing_required_columns_fails():
    df = pd.DataFrame({
        "id": [1, 2, 3]
    })

    result = check_missing_required_columns(
        df,
        required_columns=["id", "email"]
    )

    assert result["status"] == "fail"
    assert "email" in result["details"]["missing"]

from typing import Iterable, Dict, Any
import pandas as pd


def check_missing_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
) -> Dict[str, Any]:
    """
    Verify that all required columns are present.

    This is a hard gate: missing columns invalidate
    downstream assumptions immediately.
    """
    required = set(required_columns)
    present = set(df.columns)

    missing = sorted(required - present)

    if missing:
        return {
            "name": "missing_required_columns",
            "status": "fail",
            "details": {
                "missing": missing
            },
        }

    return {
        "name": "missing_required_columns",
        "status": "pass",
        "details": {},
    }

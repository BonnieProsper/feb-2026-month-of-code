from typing import Dict, Any
import pandas as pd


def check_missing_values(
    df: pd.DataFrame,
    missing_warn_threshold: float,
) -> Dict[str, Any]:
    """
    Measure missing value percentage per column.

    Fully missing columns are treated as hard failures.
    Partial missingness is surfaced for review.
    """
    total_rows = len(df)
    missing_percentages = {}

    fully_missing = []

    for col in df.columns:
        missing_count = df[col].isna().sum()

        if total_rows == 0:
            pct_missing = 0.0
        else:
            pct_missing = missing_count / total_rows

        if pct_missing == 1.0:
            fully_missing.append(col)
        elif pct_missing > missing_warn_threshold:
            missing_percentages[col] = round(pct_missing, 4)

    if fully_missing:
        return {
            "name": "missing_values",
            "status": "fail",
            "details": {
                "fully_missing": fully_missing
            },
        }

    if missing_percentages:
        return {
            "name": "missing_values",
            "status": "warn",
            "details": missing_percentages,
        }

    return {
        "name": "missing_values",
        "status": "pass",
        "details": {},
    }


def check_empty_rows(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect rows where all values are missing.
    """
    if df.empty:
        return {
            "name": "empty_rows",
            "status": "pass",
            "details": {},
        }

    empty_row_count = df.isna().all(axis=1).sum()

    if empty_row_count > 0:
        return {
            "name": "empty_rows",
            "status": "warn",
            "details": {
                "count": int(empty_row_count)
            },
        }

    return {
        "name": "empty_rows",
        "status": "pass",
        "details": {},
    }

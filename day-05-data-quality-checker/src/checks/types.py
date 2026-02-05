from typing import Dict, Any
import pandas as pd


def check_mixed_type_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect columns containing mixed numeric and non-numeric values.
    """
    if df.columns.empty:
        return {
            "name": "...",
            "category": "types",
            "status": "pass",
            "details": {},
        }

    mixed_columns = []

    for col in df.columns:
        series = df[col].dropna()

        if series.empty:
            continue

        numeric = pd.to_numeric(series, errors="coerce")
        numeric_count = numeric.notna().sum()
        total = len(series)

        if 0 < numeric_count < total:
            mixed_columns.append(col)

    if mixed_columns:
        return {
            "name": "mixed_type_columns",
            "category": "types",
            "status": "warn",
            "details": {
                "columns": mixed_columns
            },
        }

    return {
        "name": "mixed_type_columns",
        "category": "types",
        "status": "pass",
        "details": {},
    }


def check_numeric_like_strings(
    df: pd.DataFrame,
    numeric_ratio_threshold: float = 0.9,
) -> Dict[str, Any]:
    """
    Identify mostly-numeric columns that contain string values.
    """
    if df.columns.empty:
        return {
            "name": "...",
            "category": "types",
            "status": "pass",
            "details": {},
        }

    problematic = []

    for col in df.columns:
        series = df[col].dropna()

        if series.empty:
            continue

        numeric = pd.to_numeric(series, errors="coerce")
        ratio = numeric.notna().sum() / len(series)

        if ratio >= numeric_ratio_threshold and ratio < 1.0:
            problematic.append(col)

    if problematic:
        return {
            "name": "numeric_like_strings",
            "category": "types",
            "status": "warn",
            "details": {
                "columns": problematic
            },
        }

    return {
        "name": "numeric_like_strings",
        "category": "types",
        "status": "pass",
        "details": {},
    }

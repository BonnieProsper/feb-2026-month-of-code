from typing import Dict, Any
import pandas as pd


def check_duplicate_rows(
    df: pd.DataFrame,
    fail_threshold: float,
) -> Dict[str, Any]:
    """
    Detect duplicated rows in the dataset.
    """
    if df.empty:
        return {
            "name": "duplicate_rows",
            "category": "sanity",
            "status": "pass",
            "details": {},
        }

    duplicate_count = df.duplicated().sum()
    ratio = duplicate_count / len(df)

    if ratio > fail_threshold:
        return {
            "name": "duplicate_rows",
            "category": "sanity",
            "status": "fail",
            "details": {
                "count": int(duplicate_count),
                "ratio": round(ratio, 4),
            },
        }

    if duplicate_count > 0:
        return {
            "name": "duplicate_rows",
            "category": "sanity",
            "status": "warn",
            "details": {
                "count": int(duplicate_count),
                "ratio": round(ratio, 4),
            },
        }

    return {
        "name": "duplicate_rows",
        "category": "sanity",
        "status": "pass",
        "details": {},
    }


def check_constant_columns(
    df: pd.DataFrame,
    dominance_threshold: float,
) -> Dict[str, Any]:
    """
    Identify constant or near-constant columns.
    """
    if df.columns.empty:
        return {
            "name": "...",
            "category": "sanity",
            "status": "pass",
            "details": {},
        }

    constant_cols = []

    for col in df.columns:
        value_counts = df[col].value_counts(dropna=True)

        if value_counts.empty:
            continue

        dominance = value_counts.iloc[0] / value_counts.sum()

        if dominance >= dominance_threshold:
            constant_cols.append(col)

    if constant_cols:
        return {
            "name": "constant_columns",
            "category": "sanity",
            "status": "warn",
            "details": {
                "columns": constant_cols
            },
        }

    return {
        "name": "constant_columns",
        "category": "sanity",
        "status": "pass",
        "details": {},
    }


def check_numeric_ranges(
    df: pd.DataFrame,
    numeric_ranges: Dict[str, Dict[str, float]],
    fail_threshold: float,
) -> Dict[str, Any]:
    """
    Validate numeric columns against configured ranges.
    """
    violations = {}

    for col, bounds in numeric_ranges.items():
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        total = series.notna().sum()

        if total == 0:
            continue

        out_of_range = ((series < bounds["min"]) | (series > bounds["max"])).sum()
        ratio = out_of_range / total

        if out_of_range > 0:
            violations[col] = {
                "count": int(out_of_range),
                "ratio": round(ratio, 4),
            }

    if not violations:
        return {
            "name": "numeric_ranges",
            "category": "sanity",
            "status": "pass",
            "details": {},
        }

    max_ratio = max(v["ratio"] for v in violations.values())

    if max_ratio > fail_threshold:
        return {
            "name": "numeric_ranges",
            "category": "sanity",
            "status": "fail",
            "details": violations,
        }

    return {
        "name": "numeric_ranges",
        "category": "sanity",
        "status": "warn",
        "details": violations,
    }

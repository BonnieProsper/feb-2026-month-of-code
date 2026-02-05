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
            "category": "structure",
            "status": "fail",
            "details": {
                "missing": missing
            },
        }

    return {
        "name": "missing_required_columns",
        "category": "structure",
        "status": "pass",
        "details": {},
    }


def check_unexpected_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
) -> Dict[str, Any]:
    """
    Identify columns not declared in the expected schema.

    Extra columns often indicate upstream joins or schema drift.
    """
    required = set(required_columns)
    present = set(df.columns)

    unexpected = sorted(present - required)

    if unexpected:
        return {
            "name": "unexpected_columns",
            "category": "structure",
            "status": "warn",
            "details": {
                "unexpected": unexpected
            },
        }

    return {
        "name": "unexpected_columns",
        "category": "structure",
        "status": "pass",
        "details": {},
    }


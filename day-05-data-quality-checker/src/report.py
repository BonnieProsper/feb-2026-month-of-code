import json
from pathlib import Path
from typing import List, Dict
import pandas as pd


def generate_report(
    df: pd.DataFrame,
    results: List[Dict],
    output_path: str,
    strict: bool = False,
) -> int:
    """
    Generate a dataset-level report for console and JSON output.

    Exit codes:
        0 → pass
        1 → warnings present
        2 → failures present (or strict mode violation)
    """
    row_count = len(df)
    column_count = len(df.columns)

    passes = sum(1 for r in results if r["status"] == "pass")
    warns = sum(1 for r in results if r["status"] == "warn")
    fails = sum(1 for r in results if r["status"] == "fail")

    # ---- Health score ----
    health_score = max(
        0,
        100 - (warns * 5) - (fails * 20),
    )

    # ---- Dataset status ----
    if fails > 0 or (strict and warns > 0):
        dataset_status = "fail"
        exit_code = 2
    elif warns > 0:
        dataset_status = "warn"
        exit_code = 1
    else:
        dataset_status = "pass"
        exit_code = 0

    # ---- Aggregate column issues ----
    columns_summary: Dict[str, Dict] = {}
    for r in results:
        details = r.get("details")
        if not isinstance(details, dict):
            continue

        for col, val in details.items():
            if col not in columns_summary:
                columns_summary[col] = {
                    "issues": [],
                    "missing_pct": None,
                    "dtype": None,
                }

            columns_summary[col]["issues"].append(r["name"])

            if r["name"] == "missing_values":
                columns_summary[col]["missing_pct"] = val

            if r["name"] in {"mixed_type_columns", "numeric_like_strings"}:
                columns_summary[col]["dtype"] = (
                    "mixed"
                    if r["name"] == "mixed_type_columns"
                    else "numeric"
                )

    report = {
        "dataset": {
            "row_count": row_count,
            "column_count": column_count,
            "status": dataset_status,
            "health_score": health_score,
            "strict_mode": strict,
        },
        "summary": {
            "checks_run": len(results),
            "passes": passes,
            "warnings": warns,
            "failures": fails,
        },
        "checks": results,
        "columns": columns_summary,
    }

    output_file = Path(output_path)
    output_file.write_text(json.dumps(report, indent=4))

    # ---- Console output ----
    status_symbol = {"pass": "✔", "warn": "⚠", "fail": "✖"}

    print(f"\nData Quality Check — {dataset_status.upper()}")
    print(f"Health score: {health_score}/100\n")
    print(f"Rows: {row_count}")
    print(f"Columns: {column_count}\n")

    print("Checks:")
    for r in results:
        symbol = status_symbol.get(r["status"], "?")
        extra = ""
        if r["status"] != "pass" and isinstance(r.get("details"), dict):
            extra = f" ({len(r['details'])} columns affected)"
        print(f"{symbol} {r['name']}{extra}")

    if strict:
        print("\nStrict mode enabled: warnings are treated as failures")

    print(f"\nReport written to: {output_file}\n")

    return exit_code

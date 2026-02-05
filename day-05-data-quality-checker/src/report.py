import json
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


def _load_baseline(path: str) -> Dict:
    baseline_file = Path(path)
    if not baseline_file.exists():
        raise FileNotFoundError(f"Baseline report not found: {path}")
    return json.loads(baseline_file.read_text())


def _compare_to_baseline(current: Dict, baseline: Dict) -> Dict:
    comparison = {
        "health_score_delta": None,
        "warnings_delta": None,
        "failures_delta": None,
        "regression": False,
    }

    try:
        comparison["health_score_delta"] = (
            current["dataset"]["health_score"]
            - baseline["dataset"]["health_score"]
        )
        comparison["warnings_delta"] = (
            current["summary"]["warnings"]
            - baseline["summary"]["warnings"]
        )
        comparison["failures_delta"] = (
            current["summary"]["failures"]
            - baseline["summary"]["failures"]
        )

        if (
            comparison["health_score_delta"] < 0
            or comparison["failures_delta"] > 0
        ):
            comparison["regression"] = True

    except KeyError:
        raise ValueError("Baseline report structure is incompatible")

    return comparison


SEVERITY_ORDER = {"pass": 0, "warn": 1, "fail": 2}


def apply_severity_policy(
    results: List[Dict],
    severity_policy: Dict[str, str],
    category_severity: Dict[str, str],
    default_severity: str = "fail",
) -> List[Dict]:
    """
    Re-interpret check severity based on config.
    Severity may only be escalated, never downgraded.
    """
    adjusted = []

    for r in results:
        original = r["status"]

        if original == "pass":
            adjusted.append(r)
            continue

        category = r.get("category")
        category_level = (
            category_severity.get(category)
            if isinstance(category, str)
            else None
        )

        desired = severity_policy.get(
            r["name"],
            category_level or default_severity,
        )

        final = (
            desired
            if SEVERITY_ORDER[desired] > SEVERITY_ORDER[original]
            else original
        )

        adjusted.append({**r, "status": final})

    return adjusted


def generate_report(
    df: pd.DataFrame,
    results: List[Dict],
    output_path: str,
    strict: bool = False,
    baseline_path: Optional[str] = None,
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

    category_summary: Dict[str, Dict[str, int]] = {}

    for r in results:
        category = r.get("category", "unknown")
        category_summary.setdefault(
            category,
            {"pass": 0, "warn": 0, "fail": 0}
        )
        category_summary[category][r["status"]] += 1


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
        "categories": category_summary,
    }

    if baseline_path:
        baseline = _load_baseline(baseline_path)
        baseline_comparison = _compare_to_baseline(report, baseline)
        report["baseline_comparison"] = baseline_comparison

        if baseline_comparison["regression"]:
            if strict or baseline_comparison["failures_delta"] > 0:
                exit_code = 2

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

    print("\nCategory summary:")
    for cat, counts in category_summary.items():
        print(
            f"- {cat}: "
            f"{counts['pass']} pass, "
            f"{counts['warn']} warn, "
            f"{counts['fail']} fail"
        )

    if baseline_comparison:
        print("\nBaseline comparison:")
        print(
            f"Health score change: {baseline_comparison['health_score_delta']}"
        )
        print(
            f"Warnings change: {baseline_comparison['warnings_delta']}, "
            f"Failures change: {baseline_comparison['failures_delta']}"
        )
        if baseline_comparison["regression"]:
            print("Regression detected")

    if strict:
        print("\nStrict mode enabled: warnings are treated as failures")

    summary_path = output_file.with_name("run_summary.json")

    run_summary = {
        "status": dataset_status,
        "exit_code": exit_code,
        "health_score": health_score,
        "checks": {
            "total": len(results),
            "passed": passes,
            "warned": warns,
            "failed": fails,
        },
    }

    if baseline_comparison:
        run_summary["regression"] = baseline_comparison["regression"]
        run_summary["health_score_delta"] = baseline_comparison["health_score_delta"]

    summary_path.write_text(json.dumps(run_summary, indent=2))

    print(f"\nReport written to: {output_file}\n")
  
    return exit_code

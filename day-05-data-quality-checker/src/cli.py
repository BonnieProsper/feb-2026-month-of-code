import argparse
from loader import load_csv
from schema import load_schema
from checks.structure import check_missing_required_columns, check_unexpected_columns
from checks.completeness import check_missing_values, check_empty_rows
from checks.sanity import check_duplicate_rows, check_constant_columns, check_numeric_ranges
from checks.types import check_mixed_type_columns, check_numeric_like_strings
from report import generate_report, apply_severity_policy


def apply_column_ignores(df, check_name, schema):
    global_ignore = set(schema.get("ignore_columns", []))
    per_check_ignore = set(schema.get("ignore", {}).get(check_name, []))

    ignored = global_ignore | per_check_ignore
    if not ignored:
        return df

    remaining = [c for c in df.columns if c not in ignored]
    return df[remaining]


def main() -> int:
    parser = argparse.ArgumentParser(description="Dataset quality checker")
    parser.add_argument("csv_path", help="Path to the CSV file to check")
    parser.add_argument("--config", help="Optional JSON schema/config file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail the run if any warnings are detected",
    )
    parser.add_argument(
        "--baseline",
        help="Path to a previous JSON report to compare against",
    )
    parser.add_argument(
        "--only-category",
        action="append",
        help="Only run/report checks in these categories (can be repeated)",
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="List all available checks and their categories, then exit",
    )

    args = parser.parse_args()

    df = load_csv(args.csv_path)

    schema = load_schema(args.config) if args.config else {}
    required_columns = schema.get("required_columns", [])
    thresholds = schema.get("thresholds", {})

    missing_warn = thresholds.get("missing_warn", 0.05)
    duplicate_fail = thresholds.get("duplicate_fail", 0.05)
    dominance_warn = thresholds.get("dominance_warn", 0.99)
    range_fail = thresholds.get("range_fail", 0.01)

    results = []

    if required_columns:
        results.append(check_missing_required_columns(df, required_columns))
        results.append(check_unexpected_columns(df, required_columns))

    df_mv = apply_column_ignores(df, "missing_values", schema)
    results.append(check_missing_values(df_mv, missing_warn))

    results.append(check_empty_rows(df))

    results.append(check_duplicate_rows(df, duplicate_fail))
    results.append(check_constant_columns(df, dominance_warn))

    if "numeric_ranges" in schema:
        results.append(check_numeric_ranges(df, schema["numeric_ranges"], range_fail))

    results.append(check_mixed_type_columns(df))
    results.append(check_numeric_like_strings(df))

    if args.list_checks:
        seen = set()
        print("\nAvailable checks:\n")
        for r in results:
            key = (r["name"], r.get("category", "unknown"))
            if key in seen:
                continue
            seen.add(key)
            print(f"- {r['name']} ({r.get('category', 'unknown')})")
        print()
        return 0


    severity_policy = schema.get("severity", {})
    category_severity = schema.get("category_severity", {})
    default_severity = schema.get("default_severity", "fail")

    results = apply_severity_policy(
        results,
        severity_policy=severity_policy,
        category_severity=category_severity,
        default_severity=default_severity,
    )

    if args.only_category:
        allowed = set(args.only_category)
        results = [r for r in results if r.get("category") in allowed]

    return generate_report(
        df,
        results,
        output_path="report.json",
        strict=args.strict,
        baseline_path=args.baseline,
    )


if __name__ == "__main__":
    import sys
    sys.exit(main())

import argparse
import sys

from loader import load_csv
from schema import load_schema
from checks.structure import (
    check_missing_required_columns,
    check_unexpected_columns,
)
from checks.completeness import (
    check_missing_values,
    check_empty_rows,
)
from checks.sanity import (
    check_duplicate_rows,
    check_constant_columns,
    check_numeric_ranges,
)



def main() -> int:
    parser = argparse.ArgumentParser(description="Dataset quality checker")
    parser.add_argument("csv_path")
    parser.add_argument("--config", required=False)

    args = parser.parse_args()

    df = load_csv(args.csv_path)

    if args.config:
        schema = load_schema(args.config)
        required_columns = schema.get("required_columns", [])
    else:
        required_columns = []

    results = []

    if required_columns:
        results.append(
            check_missing_required_columns(df, required_columns)
        )
        results.append(
            check_unexpected_columns(df, required_columns)
        )

        missing_warn = 0.05
    if args.config:
        missing_warn = schema.get("thresholds", {}).get(
            "missing_warn", missing_warn
        )

    results.append(
        check_missing_values(df, missing_warn)
    )
    results.append(
        check_empty_rows(df)
    )

        thresholds = schema.get("thresholds", {}) if args.config else {}

    duplicate_fail = thresholds.get("duplicate_fail", 0.05)
    dominance_warn = thresholds.get("dominance_warn", 0.99)
    range_fail = thresholds.get("range_fail", 0.01)

    results.append(
        check_duplicate_rows(df, duplicate_fail)
    )
    results.append(
        check_constant_columns(df, dominance_warn)
    )

    if args.config and "numeric_ranges" in schema:
        results.append(
            check_numeric_ranges(
                df,
                schema["numeric_ranges"],
                range_fail,
            )
        )

    for r in results:
        print(r)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import sys

from loader import load_csv
from schema import load_schema
from checks.structure import (
    check_missing_required_columns,
    check_unexpected_columns,
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

    for r in results:
        print(r)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

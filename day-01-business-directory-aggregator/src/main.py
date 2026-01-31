from pathlib import Path
import argparse
from collections import Counter

from file_io import read_csv, read_json, write_csv
from normalize import normalize_record

MANDATORY_COLUMNS = ["name", "category", "city", "region", "country", "website"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize public business directory CSV/JSON datasets."
    )
    parser.add_argument("input_file", help="Path to input CSV or JSON file")
    parser.add_argument("output_file", help="Path to output CSV file")
    parser.add_argument(
        "--sort",
        choices=["name"],
        help="Optional: sort output by the given field (currently only 'name')",
    )
    parser.add_argument(
        "--min-fields",
        type=int,
        default=0,
        help="Optional: skip rows with fewer than N non-empty fields",
    )

    args = parser.parse_args()
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    # Read input
    if input_path.suffix.lower() == ".csv":
        raw_rows = read_csv(str(input_path))
    elif input_path.suffix.lower() == ".json":
        raw_rows = read_json(str(input_path))
    else:
        raise SystemExit("Input file must be a CSV or JSON file")

    # Normalize each row and apply min-fields filter
    normalized_rows = []
    skipped_rows = 0
    for row in raw_rows:
        if not isinstance(row, dict):
            skipped_rows += 1
            continue
        normalized = normalize_record(row)
        non_empty_count = sum(1 for c in MANDATORY_COLUMNS if normalized.get(c))
        if non_empty_count < args.min_fields:
            skipped_rows += 1
            continue
        normalized_rows.append(normalized)

    # Optional sorting
    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r["name"])

    # Write output
    write_csv(str(output_path), normalized_rows)

    # Data quality summary
    missing_counts = Counter()
    for row in normalized_rows:
        for col in MANDATORY_COLUMNS:
            if not row.get(col):
                missing_counts[col] += 1

    print(f"Normalized {len(normalized_rows)} rows → {output_path}")
    if skipped_rows:
        print(f"Skipped {skipped_rows} invalid or incomplete rows")
    if missing_counts:
        print("Missing fields summary:")
        for col, count in missing_counts.items():
            if count:
                print(f"  {col}: {count}")


if __name__ == "__main__":
    main()

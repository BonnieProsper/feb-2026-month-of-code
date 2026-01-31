from pathlib import Path
import argparse
import json
from collections import Counter
from typing import List, Dict, Optional

from file_io import read_csv, read_json, write_csv
from normalize import normalize_record, CATEGORY_MAP

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
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Optional: remove duplicate rows based on (name + website)",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Optional: output CSV or JSON summary of missing fields per column",
    )
    parser.add_argument(
        "--category-map",
        type=str,
        help="Optional: path to external JSON to extend category mapping",
    )

    args = parser.parse_args()
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    # Load external category mapping if provided
    if args.category_map:
        category_path = Path(args.category_map)
        if not category_path.exists():
            raise SystemExit(f"Category mapping file does not exist: {category_path}")
        try:
            with open(category_path, encoding="utf-8") as f:
                external_map = json.load(f)
            if isinstance(external_map, dict):
                CATEGORY_MAP.update({k.lower(): v.lower() for k, v in external_map.items()})
        except Exception as e:
            raise SystemExit(f"Failed to load category mapping: {e}")

    # Read input
    if input_path.suffix.lower() == ".csv":
        raw_rows = read_csv(str(input_path))
    elif input_path.suffix.lower() == ".json":
        raw_rows = read_json(str(input_path))
    else:
        raise SystemExit("Input file must be a CSV or JSON file")

    # Normalize rows
    normalized_rows: List[Dict[str, str]] = []
    skipped_rows = 0
    for row in raw_rows:
        if not isinstance(row, dict):
            skipped_rows += 1
            continue
        normalized = normalize_record(row)

        # Apply min-fields filter
        non_empty_count = sum(1 for c in MANDATORY_COLUMNS if normalized.get(c))
        if non_empty_count < args.min_fields:
            skipped_rows += 1
            continue

        normalized_rows.append(normalized)

    # Deduplicate if requested
    if args.deduplicate:
        seen = set()
        deduped_rows = []
        for row in normalized_rows:
            key = (row["name"].lower(), row["website"].lower())
            if key not in seen:
                seen.add(key)
                deduped_rows.append(row)
        normalized_rows = deduped_rows

    # Optional sorting
    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r["name"].lower())

    # Write output
    write_csv(str(output_path), normalized_rows, fieldnames=MANDATORY_COLUMNS)

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
    if args.deduplicate:
        print(f"Duplicates removed: {len(raw_rows) - len(normalized_rows) - skipped_rows}")

    # Interactive summary: top categories and cities
    categories_counter = Counter(row["category"] for row in normalized_rows if row["category"])
    cities_counter = Counter(row["city"] for row in normalized_rows if row["city"])

    if categories_counter:
        print("\nTop categories:")
        for cat, count in categories_counter.most_common(5):
            print(f"  {cat}: {count}")

    if cities_counter:
        print("\nTop cities:")
        for city, count in cities_counter.most_common(5):
            print(f"  {city}: {count}")

    # Optional report
    if args.report:
        report_path = Path(args.report)
        report_data = {col: missing_counts.get(col, 0) for col in MANDATORY_COLUMNS}
        try:
            if report_path.suffix.lower() == ".json":
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
            else:
                # Default to CSV
                with open(report_path, "w", encoding="utf-8", newline="") as f:
                    import csv

                    writer = csv.writer(f)
                    writer.writerow(["column", "missing_count"])
                    for col, count in report_data.items():
                        writer.writerow([col, count])
            print(f"\nData quality report written to {report_path}")
        except Exception as e:
            print(f"Failed to write report: {e}")


if __name__ == "__main__":
    main()

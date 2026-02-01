from pathlib import Path
import argparse
import json
import csv
import time
from collections import Counter
from typing import List, Dict, Optional

from file_io import read_csv_stream, read_json_stream, write_csv
from normalize import normalize_record, CATEGORY_MAP, is_duplicate
from enrich import geocode_address

MANDATORY_COLUMNS = ["name", "category", "city", "region", "country", "website", "lat", "lon"]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize public business directory CSV/JSON datasets with optional enrichment and deduplication."
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
        help="Skip rows with fewer than N non-empty mandatory fields",
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate rows based on exact website or fuzzy name match",
    )
    parser.add_argument(
        "--geocode",
        action="store_true",
        help="Optionally enrich rows with latitude and longitude using city, region, country",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Optional: output CSV or JSON summary of missing fields and skipped rows",
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

    # Load external category mapping
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

    # Choose streaming reader
    if input_path.suffix.lower() == ".csv":
        raw_rows_gen = read_csv_stream(str(input_path))
    elif input_path.suffix.lower() == ".json":
        raw_rows_gen = read_json_stream(str(input_path))
    else:
        raise SystemExit("Input file must be a CSV or JSON file")

    normalized_rows: List[Dict[str, str]] = []
    skipped_rows_info = []  # List of dicts with reason for skipping
    existing_rows: List[Dict[str, str]] = []

    invalid_website_count = 0
    geocode_success_count = 0

    for row in raw_rows_gen:
        reason = None
        if not isinstance(row, dict):
            reason = "invalid_row"
        else:
            normalized = normalize_record(row)
            # Apply min-fields filter
            non_empty_count = sum(1 for c in MANDATORY_COLUMNS if normalized.get(c))
            if non_empty_count < args.min_fields:
                reason = f"min_fields<{args.min_fields}"
            # Deduplication
            elif args.deduplicate and is_duplicate(existing_rows, normalized):
                reason = "duplicate"
            else:
                # Optional geocoding
                if args.geocode:
                    coords = geocode_address(normalized["city"], normalized["region"], normalized["country"])
                    if coords:
                        normalized.update(coords)
                        geocode_success_count += 1
                    else:
                        normalized.update({"lat": "", "lon": ""})
                        time.sleep(1)  # Respect rate limit

                # Track invalid website
                if not normalized.get("website"):
                    invalid_website_count += 1

                normalized_rows.append(normalized)
                existing_rows.append(normalized)

        if reason:
            skipped_rows_info.append({"row": row, "reason": reason})

    # Optional sorting
    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r["name"].lower())

    # Write output CSV
    write_csv(str(output_path), normalized_rows, fieldnames=MANDATORY_COLUMNS)

    # Data quality summary
    missing_counts = Counter()
    for row in normalized_rows:
        for col in MANDATORY_COLUMNS:
            if not row.get(col):
                missing_counts[col] += 1

    print(f"Normalized {len(normalized_rows)} rows → {output_path}")
    if skipped_rows_info:
        print(f"Skipped {len(skipped_rows_info)} rows:")
        reasons_counter = Counter(r["reason"] for r in skipped_rows_info)
        for reason, count in reasons_counter.items():
            print(f"  {reason}: {count}")

    if missing_counts:
        print("Missing fields summary:")
        for col, count in missing_counts.items():
            if count:
                print(f"  {col}: {count}")

    print(f"Invalid/missing websites: {invalid_website_count}")
    if args.geocode:
        print(f"Successfully geocoded rows: {geocode_success_count}")

    # Interactive top categories/cities
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

    # Optional report output
    if args.report:
        report_path = Path(args.report)
        report_data = {
            "missing_fields": {col: missing_counts.get(col, 0) for col in MANDATORY_COLUMNS},
            "skipped_rows": reasons_counter,
            "invalid_websites": invalid_website_count,
            "geocode_success": geocode_success_count,
        }
        try:
            if report_path.suffix.lower() == ".json":
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
            else:
                # Write CSV report
                with open(report_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["metric", "value"])
                    for key, val in report_data.items():
                        writer.writerow([key, val])
            print(f"\nData quality report written to {report_path}")
        except Exception as e:
            print(f"Failed to write report: {e}")


if __name__ == "__main__":
    main()

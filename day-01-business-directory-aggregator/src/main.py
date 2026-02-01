from pathlib import Path
import argparse
import json
import csv
import time
from collections import Counter
from typing import List, Dict, Optional, Callable

from file_io import read_csv_stream, read_json_stream, write_csv
from normalize import normalize_record, CATEGORY_MAP, is_duplicate
from enrich import geocode_address, scrape_website_title

# Mandatory fields + enrichment fields
MANDATORY_COLUMNS = [
    "name", "category", "city", "region", "country", "website", "lat", "lon", "title"
]

# Type for enrichment plugin
EnrichmentPlugin = Callable[[Dict[str, str]], Dict[str, str]]


def main() -> None:
    """
    Main entry point for normalizing business datasets.
    Features:
        - Streaming CSV/JSON input
        - Deduplication (exact + fuzzy)
        - Optional geocoding
        - Plugin-style enrichment (e.g., website scraping)
        - Full reporting and top category/city summaries
    """
    parser = argparse.ArgumentParser(
        description="Normalize public business directory datasets with optional enrichment."
    )
    parser.add_argument("input_file", help="Path to input CSV or JSON file")
    parser.add_argument("output_file", help="Path to output CSV file")
    parser.add_argument(
        "--sort", choices=["name"], help="Optional: sort output by the given field"
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
        help="Remove duplicate rows (exact website or fuzzy name match)",
    )
    parser.add_argument(
        "--geocode", action="store_true", help="Enrich rows with latitude/longitude"
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Enrich rows by scraping website titles",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Output CSV or JSON summary of missing fields and skipped rows",
    )
    parser.add_argument(
        "--category-map",
        type=str,
        help="Optional path to external JSON to extend category mapping",
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

    # Determine streaming reader
    if input_path.suffix.lower() == ".csv":
        raw_rows_gen = read_csv_stream(str(input_path))
    elif input_path.suffix.lower() == ".json":
        raw_rows_gen = read_json_stream(str(input_path))
    else:
        raise SystemExit("Input file must be CSV or JSON")

    # Enrichment plugins list
    enrichment_plugins: List[EnrichmentPlugin] = []
    if args.geocode:
        enrichment_plugins.append(lambda row: geocode_row(row))
    if args.scrape:
        enrichment_plugins.append(lambda row: scrape_row(row))

    normalized_rows: List[Dict[str, str]] = []
    skipped_rows_info = []
    existing_rows: List[Dict[str, str]] = []

    invalid_website_count = 0
    geocode_success_count = 0
    scrape_success_count = 0

    # Process each row
    for raw_row in raw_rows_gen:
        reason = None
        if not isinstance(raw_row, dict):
            reason = "invalid_row"
        else:
            normalized = normalize_record(raw_row)

            # Apply min-fields filter
            non_empty_count = sum(1 for c in MANDATORY_COLUMNS if normalized.get(c))
            if non_empty_count < args.min_fields:
                reason = f"min_fields<{args.min_fields}"

            # Deduplication
            elif args.deduplicate and is_duplicate(existing_rows, normalized):
                reason = "duplicate"
            else:
                # Apply enrichment plugins
                for plugin in enrichment_plugins:
                    result = plugin(normalized)
                    normalized.update(result)

                # Track enrichment counts
                if args.geocode and normalized.get("lat") and normalized.get("lon"):
                    geocode_success_count += 1
                if args.scrape and normalized.get("title"):
                    scrape_success_count += 1

                # Track invalid website
                if not normalized.get("website"):
                    invalid_website_count += 1

                normalized_rows.append(normalized)
                existing_rows.append(normalized)

        if reason:
            skipped_rows_info.append({"row": raw_row, "reason": reason})

    # Optional sorting
    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r["name"].lower())

    # Write normalized output
    write_csv(str(output_path), normalized_rows, fieldnames=MANDATORY_COLUMNS)

    # Generate data quality summary
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
    if args.scrape:
        print(f"Successfully scraped website titles: {scrape_success_count}")

    # Top categories / cities
    categories_counter = Counter(r["category"] for r in normalized_rows if r["category"])
    cities_counter = Counter(r["city"] for r in normalized_rows if r["city"])

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
        report_data = {
            "missing_fields": {col: missing_counts.get(col, 0) for col in MANDATORY_COLUMNS},
            "skipped_rows": Counter(r["reason"] for r in skipped_rows_info),
            "invalid_websites": invalid_website_count,
            "geocode_success": geocode_success_count,
            "scrape_success": scrape_success_count,
        }
        try:
            if report_path.suffix.lower() == ".json":
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2)
            else:
                with open(report_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["metric", "value"])
                    for key, val in report_data.items():
                        writer.writerow([key, val])
            print(f"\nData quality report written to {report_path}")
        except Exception as e:
            print(f"Failed to write report: {e}")


# --- Enrichment plugin implementations ---
def geocode_row(row: Dict[str, str]) -> Dict[str, str]:
    coords = geocode_address(row.get("city", ""), row.get("region", ""), row.get("country", ""))
    if coords:
        return {"lat": coords.get("lat", ""), "lon": coords.get("lon", "")}
    return {"lat": "", "lon": ""}


def scrape_row(row: Dict[str, str]) -> Dict[str, str]:
    url = row.get("website", "")
    if url:
        title = scrape_website_title(url)
        return {"title": title}
    return {"title": ""}


if __name__ == "__main__":
    main()

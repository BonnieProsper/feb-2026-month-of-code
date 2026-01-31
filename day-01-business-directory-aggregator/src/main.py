from pathlib import Path
import argparse

from file_io import read_csv, read_json, write_csv
from normalize import normalize_record

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

    # Normalize each row
    normalized_rows = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        normalized_rows.append(normalize_record(row))

    # Optional sorting
    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r["name"])

    # Write output
    write_csv(str(output_path), normalized_rows)
    print(f"Normalized {len(normalized_rows)} rows → {output_path}")


if __name__ == "__main__":
    main()

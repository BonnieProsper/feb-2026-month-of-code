import sys
from pathlib import Path

from file_io import read_csv, read_json, write_csv
from normalize import normalize_record


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python src/main.py <input_file.(csv|json)> <output_file.csv>"
        )

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    if input_path.suffix.lower() == ".csv":
        raw_rows = read_csv(str(input_path))
    elif input_path.suffix.lower() == ".json":
        raw_rows = read_json(str(input_path))
    else:
        raise SystemExit("Input file must be a CSV or JSON file")

    normalized_rows = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        normalized_rows.append(normalize_record(row))

    write_csv(str(output_path), normalized_rows)


if __name__ == "__main__":
    main()

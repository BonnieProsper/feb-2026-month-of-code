import csv
import json
from typing import List, Dict, Optional


def read_csv(path: str) -> List[Dict]:
    """
    Reads a CSV file and returns a list of dictionaries.
    Drops rows that are completely empty or whitespace-only.
    """
    rows: List[Dict] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if not row:
                continue
            # Drop rows where all values are empty or whitespace
            if all(value in (None, "", " ") or str(value).strip() == "" for value in row.values()):
                continue
            rows.append(row)

    return rows


def read_json(path: str) -> List[Dict]:
    """
    Reads a JSON file (must be a list of objects) and returns a list of dictionaries.
    Skips non-dict entries.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of objects")

    return [item for item in data if isinstance(item, dict)]


def write_csv(path: str, rows: List[Dict], fieldnames: Optional[List[str]] = None) -> None:
    """
    Writes a list of dictionaries to a CSV file.
    Uses the keys of the first row as fieldnames.
    Fills missing fields with empty strings.
    """
    default_columns = ["name", "category", "city", "region", "country", "website"]
    if fieldnames is None:
        # Use actual keys from the first row to preserve extra columns if any
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = default_columns

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

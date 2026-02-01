import csv
import json
from typing import List, Dict, Optional, Generator

def read_csv_stream(path: str) -> Generator[Dict, None, None]:
    """Generator to read CSV row by row."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row or all(v in (None, "", " ") or str(v).strip() == "" for v in row.values()):
                continue
            yield row

def read_json_stream(path: str) -> Generator[Dict, None, None]:
    """Generator to read JSON array elements one by one."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of objects")
        for item in data:
            if isinstance(item, dict):
                yield item

def write_csv(path: str, rows: List[Dict], fieldnames: Optional[List[str]] = None) -> None:
    """
    Writes a list of dictionaries to CSV.
    Uses provided fieldnames or defaults to common columns.
    """
    default_columns = ["name", "category", "city", "region", "country", "website", "lat", "lon"]
    if fieldnames is None:
        fieldnames = default_columns
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

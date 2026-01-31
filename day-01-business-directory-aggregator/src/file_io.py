import csv
import json
from typing import List, Dict


def read_csv(path: str) -> List[Dict]:
    rows: List[Dict] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if not row:
                continue

            # drop rows that are completely empty
            if all(value in (None, "", " ") for value in row.values()):
                continue

            rows.append(row)

    return rows


def read_json(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of objects")

    rows: List[Dict] = []

    for item in data:
        if not isinstance(item, dict):
            continue
        rows.append(item)

    return rows


def write_csv(path: str, rows: List[Dict]) -> None:
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

import csv
import json
from pathlib import Path
from typing import List, Dict

from src.errors import DataLoadError

def load_prospects(path: str) -> List[Dict[str, str]]:
    """
    Load prospect data from a CSV or JSON file.

    Returns a list of dictionaries where each dict represents one prospect.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise DataLoadError(f"Data file not found: {path}")

    if file_path.suffix == ".csv":
        prospects = _load_csv(file_path)
    elif file_path.suffix == ".json":
        prospects = _load_json(file_path)
    else:
        raise DataLoadError(
            f"Unsupported data format: {file_path.suffix}. Use CSV or JSON."
        )

    if not prospects:
        raise DataLoadError("No prospects found in data file.")

    duplicates = _detect_duplicates(prospects)
    if duplicates:
        raise DataLoadError("Duplicate prospects detected in data file.")


    return prospects

def _detect_duplicates(prospects: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []

    for prospect in prospects:
        key = (
            f'{prospect.get("first_name", "").lower()}::'
            f'{prospect.get("company", "").lower()}'
        )

        if key in seen:
            duplicates.append(key)
        else:
            seen.add(key)

    return duplicates


def _load_csv(path: Path) -> List[Dict[str, str]]:
    prospects: List[Dict[str, str]] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise DataLoadError("CSV file has no header row.")

        for row in reader:
            # Skip completely empty rows
            if not any(row.values()):
                continue

            cleaned = {
                key.strip(): (value.strip() if value is not None else "")
                for key, value in row.items()
            }

            prospects.append(cleaned)

    return prospects


def _load_json(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as exc:
            raise DataLoadError("Invalid JSON file.") from exc

    if not isinstance(data, list):
        raise DataLoadError("JSON data must be a list of objects.")

    prospects: List[Dict[str, str]] = []

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise DataLoadError(
                f"JSON item at index {idx} is not an object."
            )

        cleaned = {
            str(key).strip(): str(value).strip()
            for key, value in item.items()
        }

        prospects.append(cleaned)

    return prospects

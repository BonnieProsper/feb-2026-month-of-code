# tests/test_loader.py

import json
from pathlib import Path
import pytest

from src.loader import load_prospects
from src.errors import DataLoadError


def test_loads_csv_prospects(tmp_path: Path):
    csv_file = tmp_path / "prospects.csv"
    csv_file.write_text(
        "first_name,company,role\n"
        "Sam,Manning,CTO\n"
        "Jordan,Manning,Engineer\n"
    )

    prospects = load_prospects(str(csv_file))

    assert len(prospects) == 2
    assert prospects[0]["company"] == "Manning"


def test_loads_json_prospects(tmp_path: Path):
    json_file = tmp_path / "prospects.json"
    json_file.write_text(
        json.dumps(
            [
                {"first_name": "Sam", "company": "Manning"},
                {"first_name": "Jordan", "company": "Manning"},
            ]
        )
    )

    prospects = load_prospects(str(json_file))

    assert len(prospects) == 2
    assert prospects[1]["first_name"] == "Jordan"


def test_rejects_empty_data(tmp_path: Path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("first_name,company\n")

    with pytest.raises(DataLoadError):
        load_prospects(str(csv_file))


def test_rejects_unsupported_format(tmp_path: Path):
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("not valid")

    with pytest.raises(DataLoadError):
        load_prospects(str(txt_file))


def test_rejects_duplicate_prospects(tmp_path: Path):
    csv_file = tmp_path / "dupes.csv"
    csv_file.write_text(
        "first_name,company,email\n"
        "Sam,Manning,sam@manning.com\n"
        "Sam,Manning,sam@manning.com\n"
    )

    with pytest.raises(DataLoadError):
        load_prospects(str(csv_file))

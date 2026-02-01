from pathlib import Path
import json

from src.normalize import normalize_record, _normalize_website, extend_category_map, is_duplicate

def test_basic_record_normalization():
    raw = {
        "name": "  Acme   Corp ",
        "category": "Technology",
        "city": "Berlin",
        "country": "Germany",
        "website": "https://acme.com",
    }

    result = normalize_record(raw)
    assert result == {
        "name": "Acme Corp",
        "category": "technology",
        "city": "Berlin",
        "region": "",
        "country": "Germany",
        "website": "https://acme.com",
    }


def test_category_normalization_and_mapping():
    raw = {"business_name": "Pizza Place", "industry": "Restaurants"}
    result = normalize_record(raw)
    assert result["category"] == "restaurant"


def test_website_normalization():
    raw = {"name": "Example", "website": "example.com"}
    result = normalize_record(raw)
    assert result["website"] == "https://example.com"


def test_invalid_website_is_dropped():
    raw = {"name": "Bad Web", "url": "not a website"}
    result = normalize_record(raw)
    assert result["website"] == ""


def test_location_fallback_parsing():
    raw = {"name": "Some Shop", "location": "Paris, Île-de-France, France"}
    result = normalize_record(raw)
    assert result["city"] == "Paris"
    assert result["region"] == "Île-de-France"
    assert result["country"] == "France"


def test_structured_location_takes_precedence():
    raw = {"name": "Structured Co", "city": "London", "country": "UK", "location": "Paris, France"}
    result = normalize_record(raw)
    assert result["city"] == "London"
    assert result["country"] == "UK"


def test_empty_input_row():
    raw = {}
    result = normalize_record(raw)
    assert result == {"name": "", "category": "", "city": "", "region": "", "country": "", "website": ""}


def test_website_edge_cases():
    test_cases = [
        ("example.com", "https://example.com"),
        (" http://foo.org ", "http://foo.org"),
        ("www.bar.net/", "https://bar.net"),
        ("https://www.test.org/", "https://test.org"),
        ("bad website", ""),
        ("", ""),
    ]
    for input_url, expected in test_cases:
        result = _normalize_website(input_url)
        assert result == expected

def test_external_category_map_extension():
    extend_category_map({"Food Truck": "restaurant"})
    raw = {"name": "Tasty Truck", "category": "Food Truck"}
    result = normalize_record(raw)
    assert result["category"] == "restaurant"

def test_min_fields_filtering(monkeypatch):
    # simulate row with missing fields
    raw = {"name": "Partial Co"}
    result = normalize_record(raw)
    # count non-empty mandatory fields
    non_empty_count = sum(1 for c in ["name", "category", "city", "region", "country", "website"] if result.get(c))
    assert non_empty_count == 1


def test_deduplication_logic():
    rows = []

    row1 = {
        "name": "A",
        "website": "site.com",
        "category": "tech",
        "city": "X",
        "region": "",
        "country": "Y",
    }

    row2 = row1.copy()

    rows.append(row1)
    assert is_duplicate(rows, row2) is True

import re
from typing import Any, Dict, Iterable, Optional


# --- input key aliases ---

NAME_KEYS = [
    "name",
    "business_name",
    "company",
    "company_name",
    "organization",
]

CATEGORY_KEYS = [
    "category",
    "categories",
    "type",
    "industry",
    "sector",
]

CITY_KEYS = ["city"]
REGION_KEYS = ["region", "state", "province"]
COUNTRY_KEYS = ["country"]

LOCATION_FALLBACK_KEYS = ["location", "address"]

WEBSITE_KEYS = ["website", "url", "homepage", "site", "web"]


# --- category normalization ---

CATEGORY_MAP = {
    "restaurants": "restaurant",
    "restaurant": "restaurant",
    "tech": "technology",
    "it": "technology",
}


# --- public API ---

def normalize_record(raw: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalize a single raw business record into a flat, consistent schema.
    """
    name = _normalize_name(_pick_first_value(raw, NAME_KEYS))
    category = _normalize_category(_pick_first_value(raw, CATEGORY_KEYS))

    city = _clean_string(_pick_first_value(raw, CITY_KEYS))
    region = _clean_string(_pick_first_value(raw, REGION_KEYS))
    country = _clean_string(_pick_first_value(raw, COUNTRY_KEYS))

    if not (city or region or country):
        city, region, country = _parse_location_fallback(
            _pick_first_value(raw, LOCATION_FALLBACK_KEYS)
        )

    website = _normalize_website(_pick_first_value(raw, WEBSITE_KEYS))

    return {
        "name": name,
        "category": category,
        "city": city,
        "region": region,
        "country": country,
        "website": website,
    }


# --- helpers ---

def _pick_first_value(raw: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    """
    Return the first non-empty value found for the given keys.
    """
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def _clean_string(value: Optional[Any]) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return _collapse_whitespace(text)


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _normalize_name(value: Optional[Any]) -> str:
    return _clean_string(value)


def _normalize_category(value: Optional[Any]) -> str:
    if value is None:
        return ""

    if isinstance(value, list) and value:
        value = value[0]

    text = _clean_string(value).lower()
    if not text:
        return ""

    # light plural handling
    if text.endswith("s"):
        text = text[:-1]

    return CATEGORY_MAP.get(text, text)


def _parse_location_fallback(value: Optional[Any]) -> tuple[str, str, str]:
    """
    Best-effort parsing of a single location string.
    """
    if value is None:
        return "", "", ""

    text = _clean_string(value)
    if not text:
        return "", "", ""

    parts = [p.strip() for p in text.split(",") if p.strip()]

    if len(parts) == 2:
        return parts[0], "", parts[1]

    if len(parts) >= 3:
        return parts[0], parts[1], parts[-1]

    return "", "", ""


def _normalize_website(value: Optional[Any]) -> str:
    if value is None:
        return ""

    text = _clean_string(value).lower()
    if not text:
        return ""

    if " " in text:
        return ""

    if text.startswith("http://") or text.startswith("https://"):
        return text

    if "." in text:
        return f"https://{text}"

    return ""

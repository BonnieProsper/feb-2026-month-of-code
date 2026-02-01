import re
from typing import Any, Dict, Iterable, Optional, Tuple
from rapidfuzz import fuzz

# --- input key aliases ---
NAME_KEYS = ["name", "business_name", "company", "company_name", "organization"]
CATEGORY_KEYS = ["category", "categories", "type", "industry", "sector"]
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
    "technology": "technology",
    "it": "technology",
    "software": "technology",
    "cloud": "technology",
    "retail": "retail",
    "shop": "retail",
    "store": "retail",
    "market": "retail",
    "health": "health",
    "clinic": "health",
    "hospital": "health",
    "healthcare": "health",
    "doctor": "health",
    "dentist": "health",
    "pharmacy": "health",
    "education": "education",
    "school": "education",
    "university": "education",
    "finance": "finance",
    "bank": "finance",
    "insurance": "finance",
    "entertainment": "entertainment",
    "bar": "restaurant",
    "cafe": "restaurant",
    "pub": "restaurant",
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
def extend_category_map(new_map: Dict[str, str]) -> None:
    """
    Extend CATEGORY_MAP with a dict of lowercase key -> lowercase value.
    """
    CATEGORY_MAP.update({k.lower(): v.lower() for k, v in new_map.items()})

def _pick_first_value(raw: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None

def _clean_string(value: Optional[Any]) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return _collapse_whitespace(text) if text else ""

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
    if text.endswith("s") and text not in CATEGORY_MAP:
        text = text[:-1]
    return CATEGORY_MAP.get(text, text)

def _parse_location_fallback(value: Optional[Any]) -> Tuple[str, str, str]:
    if value is None:
        return "", "", ""
    text = _clean_string(value)
    if not text:
        return "", "", ""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) == 2:
        return parts[0], "", parts[1]
    elif len(parts) >= 3:
        return parts[0], parts[1], parts[-1]
    return "", "", ""

def _normalize_website(value: Optional[Any]) -> str:
    if value is None:
        return ""
    text = _clean_string(value).lower()
    if not text or " " in text:
        return ""
    if not text.startswith(("http://", "https://")):
        if "." in text:
            text = f"https://{text}"
        else:
            return ""
    text = text.rstrip("/")
    text = re.sub(r"^https?://www\.", lambda m: "https://", text)
    return text

def is_duplicate(existing_rows: list, new_row: dict, threshold=90) -> bool:
    """
    Determine if a new row is a duplicate of any existing row.
    Combines exact website match and fuzzy name similarity.
    """
    for row in existing_rows:
        if row.get("website") and new_row.get("website") and row["website"] == new_row["website"]:
            return True
        if fuzz.ratio(row.get("name", "").lower(), new_row.get("name", "").lower()) >= threshold:
            return True
    return False

import requests
import time
from typing import Dict, Optional
from bs4 import BeautifulSoup

def geocode_address(city: str, region: str, country: str) -> Dict[str, str]:
    """
    Return latitude/longitude for an address or empty dict if not found.
    Uses OpenStreetMap Nominatim API with rate-limiting.
    """
    if not (city or region or country):
        return {}
    query = ", ".join(filter(None, [city, region, country]))
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "DataNormalizer/1.0"})
        resp.raise_for_status()
        results = resp.json()
        if results:
            return {"lat": results[0]["lat"], "lon": results[0]["lon"]}
    except Exception:
        pass
    time.sleep(1)  # Respect rate limits
    return {}

def scrape_website_title(url: str) -> str:
    """
    Optionally fetch the <title> of a website.
    Minimal scraping logic, safe for portfolio purposes.
    """
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "DataNormalizer/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        title_tag = soup.find("title")
        return title_tag.text.strip() if title_tag else ""
    except Exception:
        return ""

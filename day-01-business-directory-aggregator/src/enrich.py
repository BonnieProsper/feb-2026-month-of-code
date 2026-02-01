import requests
import time
from typing import Dict

def geocode_address(city: str, region: str, country: str) -> Dict[str, str]:
    """
    Return latitude and longitude for an address using OpenStreetMap Nominatim API.
    Rate-limited to 1 request/sec for polite usage.
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
    time.sleep(1)
    return {}

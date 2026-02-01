import time
from typing import Dict

import requests


class GeocodePlugin:
    """
    Enrich a row with latitude / longitude using OpenStreetMap Nominatim.

    This plugin is intentionally conservative:
    - 1 request per row
    - hard timeout
    - silent failure on network errors
    """

    name = "geocode"

    def enrich(self, row: Dict[str, str]) -> Dict[str, str]:
        city = row.get("city")
        region = row.get("region")
        country = row.get("country")

        if not any([city, region, country]):
            return {}

        query = ", ".join(filter(None, [city, region, country]))

        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "BusinessDirectoryAggregator/1.0"},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
        except Exception:
            return {}

        time.sleep(1)  # Respect Nominatim rate limits

        if not results:
            return {}

        return {
            "lat": results[0].get("lat", ""),
            "lon": results[0].get("lon", ""),
        }

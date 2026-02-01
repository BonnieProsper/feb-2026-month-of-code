from typing import Dict

import requests
from bs4 import BeautifulSoup


class ScrapeTitlePlugin:
    """
    Enrich a row by fetching the <title> tag from the business website.

    This plugin is intentionally minimal:
    - no JS rendering
    - no retries
    - short timeout
    """

    name = "scrape_title"

    def enrich(self, row: Dict[str, str]) -> Dict[str, str]:
        url = row.get("website")
        if not url:
            return {}

        try:
            resp = requests.get(
                url,
                timeout=5,
                headers={"User-Agent": "BusinessDirectoryAggregator/1.0"},
            )
            resp.raise_for_status()
        except Exception:
            return {}

        soup = BeautifulSoup(resp.text, "lxml")
        title_tag = soup.find("title")

        if not title_tag or not title_tag.text:
            return {}

        return {"website_title": title_tag.text.strip()}

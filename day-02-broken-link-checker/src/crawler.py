import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Callable, List, Tuple, Optional


def crawl_site(
    base_url: str,
    max_depth: int = 2,
    max_pages: int = 100,
    timeout: int = 5,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[int, List[Tuple[str, str, str]]]:
    """
    Crawl a single domain and collect links.

    Returns:
        pages_scanned: int
        discovered_links: List of (source_page, url, link_type)
            link_type: 'internal', 'external', 'anchor'
    """
    headers = {"User-Agent": "BrokenLinkChecker/1.0"}
    to_visit: List[Tuple[str, int]] = [(base_url, 0)]
    visited: set[str] = set()
    pages_scanned = 0
    discovered_links: List[Tuple[str, str, str]] = []

    while to_visit:
        url, depth = to_visit.pop(0)
        if url in visited or pages_scanned >= max_pages:
            continue

        visited.add(url)
        pages_scanned += 1

        # Progress callback
        if progress_callback:
            progress_callback(pages_scanned, max_pages, url)

        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            content_type = resp.headers.get("Content-Type", "")
        except requests.RequestException:
            continue

        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup.find_all("a", href=True):
            href = str(tag.get("href", "")).strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue

            # Normalize URL
            normalized = urljoin(url, href)
            parsed = urlparse(normalized)

            # Classify link type
            if parsed.fragment:
                link_type = "anchor"
            elif parsed.netloc.lower() == urlparse(base_url).netloc.lower():
                link_type = "internal"
            else:
                link_type = "external"

            discovered_links.append((url, normalized, link_type))

            # Queue internal links for further crawling
            if link_type == "internal" and depth + 1 <= max_depth and normalized not in visited:
                to_visit.append((normalized, depth + 1))

    return pages_scanned, discovered_links

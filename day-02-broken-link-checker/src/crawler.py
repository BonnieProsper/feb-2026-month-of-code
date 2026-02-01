import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Callable, List, Tuple, Optional


def crawl_site(
    base_url: str,
    max_depth: int = 2,
    max_pages: int = 100,
    timeout: int = 5,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Crawl a single domain and collect internal links.

    Args:
        base_url: starting URL
        max_depth: max crawl depth
        max_pages: max pages to scan
        timeout: request timeout
        progress_callback: optional callback for progress reporting
            signature: (current_page_index, max_pages, url)

    Returns:
        Tuple[pages_scanned, discovered_links]
    """
    to_visit: List[Tuple[str, int]] = [(base_url, 0)]
    visited: set[str] = set()
    pages_scanned = 0
    discovered_links: List[Tuple[str, str]] = []

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
            response = requests.get(url, timeout=timeout)
            content_type = response.headers.get("Content-Type", "")
        except requests.RequestException:
            continue

        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            if not isinstance(href, str):
                continue

            normalized = normalize_url(href, url)
            if not normalized or not is_internal_url(normalized, base_url):
                continue

            discovered_links.append((url, normalized))

            if depth + 1 <= max_depth and normalized not in visited:
                to_visit.append((normalized, depth + 1))

    return pages_scanned, discovered_links


def normalize_url(href: str, base_url: str) -> Optional[str]:
    """Normalize URL: absolute, lowercase scheme/netloc, ensure path ends with /"""
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "tel:", "javascript:")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if not parsed.scheme or not parsed.netloc:
        return None

    scheme, netloc = parsed.scheme.lower(), parsed.netloc.lower()
    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"

    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def is_internal_url(url: str, base_url: str) -> bool:
    """Check if URL is internal to the base domain"""
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()

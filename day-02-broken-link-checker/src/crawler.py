import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse


def crawl_site(
    base_url: str,
    max_depth: int = 2,
    max_pages: int = 100,
    timeout: int = 5,
):
    to_visit: list[tuple[str, int]] = [(base_url, 0)]
    visited: set[str] = set()

    pages_scanned = 0
    discovered_links: list[tuple[str, str]] = []

    while to_visit:
        url, depth = to_visit.pop(0)

        if url in visited:
            continue

        if pages_scanned >= max_pages:
            break

        visited.add(url)
        pages_scanned += 1

        try:
            response = requests.get(url, timeout=timeout)
            content_type = response.headers.get("Content-Type", "")
        except requests.RequestException:
            continue

        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            raw_href = tag.get("href")
            normalized = normalize_url(raw_href, url)

            if not normalized:
                continue

            if not is_internal_url(normalized, base_url):
                continue

            discovered_links.append((url, normalized))

            if depth + 1 <= max_depth and normalized not in visited:
                to_visit.append((normalized, depth + 1))

    return pages_scanned, discovered_links


def normalize_url(href: str, base_url: str) -> str | None:
    if not href:
        return None

    href = href.strip()

    if href.startswith(("mailto:", "tel:", "javascript:")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)

    if not parsed.scheme or not parsed.netloc:
        return None

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"

    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",
        parsed.query,
        "",
    ))

    return normalized


def is_internal_url(url: str, base_url: str) -> bool:
    base_host = urlparse(base_url).netloc.lower()
    url_host = urlparse(url).netloc.lower()

    return url_host == base_host

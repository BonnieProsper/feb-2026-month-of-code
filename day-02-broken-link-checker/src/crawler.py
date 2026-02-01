from urllib.parse import urljoin, urlparse, urlunparse


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

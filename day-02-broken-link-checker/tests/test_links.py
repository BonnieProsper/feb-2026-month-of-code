from src.crawler import crawl_site
from src.checker import check_link


BASE = "https://example.com"


def test_crawl_returns_links_with_types():
    pages_scanned, links = crawl_site(BASE, max_depth=1, max_pages=5)
    assert isinstance(pages_scanned, int)
    for source, url, link_type in links:
        assert link_type in ("internal", "external", "anchor")
        assert source.startswith("https://")
        assert url.startswith("https://")


def test_check_link_timeout():
    status, error = check_link("http://10.255.255.1", timeout=1, retries=0)
    assert status is None
    assert error == "timeout"

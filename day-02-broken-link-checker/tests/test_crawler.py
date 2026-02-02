from src.crawler import crawl_site


def test_crawl_basic_internal_links():
    base_url = "https://example.com"
    pages_scanned, links = crawl_site(base_url, max_depth=1, max_pages=5)

    # All discovered links should have the expected structure
    for source, url, link_type in links:
        assert source.startswith("https://")
        assert url.startswith("https://")
        assert link_type in ("internal", "external", "anchor")


def test_internal_and_external_links_classification():
    base_url = "https://example.com"

    # Mock links manually using a small HTML snippet if needed
    pages_scanned, links = crawl_site(base_url, max_depth=1, max_pages=5)

    for source, url, link_type in links:
        if base_url in url:
            assert link_type in ("internal", "anchor")
        else:
            assert link_type == "external"

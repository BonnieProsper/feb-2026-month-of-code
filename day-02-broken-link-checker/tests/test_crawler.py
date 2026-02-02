from src.crawler import normalize_url, is_internal_url


def test_normalize_url_basic():
    url = normalize_url("/about", "https://example.com")
    assert url == "https://example.com/about/"


def test_ignore_mailto():
    assert normalize_url("mailto:test@example.com", "https://example.com") is None


def test_internal_url():
    assert is_internal_url(
        "https://example.com/page/",
        "https://example.com",
    )


def test_external_url():
    assert not is_internal_url(
        "https://other.com",
        "https://example.com",
    )

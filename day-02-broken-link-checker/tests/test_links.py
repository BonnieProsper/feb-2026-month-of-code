from src.crawler import normalize_url, is_internal_url


BASE = "https://example.com"


def test_normalize_resolves_relative_url():
    url = normalize_url("/about", BASE)
    assert url == "https://example.com/about/"


def test_normalize_strips_fragment():
    url = normalize_url("/about#team", BASE)
    assert url == "https://example.com/about/"


def test_normalize_lowercases_scheme_and_host():
    url = normalize_url("HTTPS://EXAMPLE.COM/Contact", BASE)
    assert url == "https://example.com/Contact/"


def test_normalize_ignores_mailto_links():
    assert normalize_url("mailto:test@example.com", BASE) is None


def test_internal_url_same_host():
    assert is_internal_url("https://example.com/about/", BASE) is True


def test_internal_url_different_subdomain_is_external():
    assert is_internal_url("https://blog.example.com/", BASE) is False


def test_internal_url_different_domain():
    assert is_internal_url("https://example.org/", BASE) is False

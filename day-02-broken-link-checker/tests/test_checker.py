import requests
from src.checker import check_link


def test_check_link_ok(mocker):
    mocker.patch("requests.head", return_value=mocker.Mock(status_code=200))
    status, error = check_link("https://example.com")
    assert status == 200
    assert error is None


def test_head_fallback_to_get(mocker):
    mocker.patch("requests.head", return_value=mocker.Mock(status_code=405))
    mocker.patch("requests.get", return_value=mocker.Mock(status_code=200))

    status, error = check_link("https://example.com")
    assert status == 200
    assert error is None


def test_timeout(mocker):
    mocker.patch("requests.head", side_effect=requests.Timeout)

    status, error = check_link("https://example.com", retries=0)
    assert status is None
    assert error == "timeout"

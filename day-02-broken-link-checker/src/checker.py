import requests


def check_link(url: str, timeout: int = 5) -> tuple[int | None, str | None]:
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code, None

    except requests.Timeout:
        return None, "timeout"

    except requests.ConnectionError:
        return None, "connection_error"

    except requests.RequestException:
        return None, "request_error"

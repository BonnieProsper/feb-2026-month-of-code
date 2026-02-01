import requests
from typing import Tuple, Optional


def check_link(
    url: str,
    timeout: int = 5,
    retries: int = 1,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Check a single link's HTTP status.

    Args:
        url: URL to check
        timeout: request timeout in seconds
        retries: number of retries on transient failures (timeouts, connection errors, 5xx)

    Returns:
        Tuple[status_code, error_str]:
            - status_code: int if request succeeded, else None
            - error_str: "timeout", "connection_error", "request_error" for failures
    """
    attempt = 0
    while attempt <= retries:
        try:
            response = requests.get(url, timeout=timeout)
            # Treat 5xx as transient error to allow retry
            if 500 <= response.status_code <= 599 and attempt < retries:
                attempt += 1
                continue
            return response.status_code, None

        except requests.Timeout:
            if attempt < retries:
                attempt += 1
                continue
            return None, "timeout"

        except requests.ConnectionError:
            if attempt < retries:
                attempt += 1
                continue
            return None, "connection_error"

        except requests.RequestException:
            # Non-transient errors
            return None, "request_error"

    # Should not reach here, but fallback
    return None, "request_error"

import requests
from typing import Tuple, Optional


def check_link(
    url: str,
    timeout: int = 5,
    retries: int = 1,
    use_head: bool = True,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Check a single link's HTTP status.

    Strategy:
        Try HEAD first (faster, lower bandwidth)
        Fallback to GET if HEAD is not allowed or unreliable
        Retry transient failures (timeouts, connection errors, 5xx)

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
            if use_head:
                response = requests.head(
                    url,
                    timeout=timeout,
                    allow_redirects=True,
                )

                # Some servers return 405 or bogus results for HEAD
                if response.status_code < 400:
                    return response.status_code, None

            # Fallback to GET
            
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
            )

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

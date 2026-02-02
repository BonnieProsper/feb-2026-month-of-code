import asyncio
from typing import Optional, Tuple

import aiohttp


async def check_link_async(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 5,
    retries: int = 1,
    use_head: bool = True,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Asynchronously check a single URL.

    Mirrors the synchronous checker contract:
    returns (status_code, error_str)

    - Retries on timeouts and transient 5xx responses
    - Optionally attempts HEAD before GET
    """
    attempt = 0

    client_timeout = aiohttp.ClientTimeout(total=timeout)

    while attempt <= retries:
        try:
            if use_head:
                async with session.head(
                    url,
                    timeout=client_timeout,
                    allow_redirects=True,
                ) as resp:
                    if resp.status < 400:
                        return resp.status, None

            async with session.get(
                url,
                timeout=client_timeout,
                allow_redirects=True,
            ) as resp:
                if 500 <= resp.status <= 599 and attempt < retries:
                    attempt += 1
                    continue

                return resp.status, None

        except asyncio.TimeoutError:
            if attempt < retries:
                attempt += 1
                continue
            return None, "timeout"

        except aiohttp.ClientConnectionError:
            if attempt < retries:
                attempt += 1
                continue
            return None, "connection_error"

        except aiohttp.ClientError:
            return None, "request_error"

    return None, "request_error"

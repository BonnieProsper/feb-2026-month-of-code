import dns.resolver
import dns.exception


DEFAULT_TIMEOUT = 3.0


def lookup_txt(name: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    Perform a single TXT lookup and return a structured result.

    DNS is treated as an unreliable external dependency. This function
    makes uncertainty explicit so callers do not confuse lookup failure
    with configuration failure.
    """
    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    resolver.timeout = timeout

    try:
        answers = resolver.resolve(name, "TXT")
    except dns.resolver.NXDOMAIN:
        return {
            "status": "not_found",
            "records": [],
        }
    except dns.resolver.NoAnswer:
        return {
            "status": "not_found",
            "records": [],
        }
    except dns.exception.Timeout:
        return {
            "status": "timeout",
            "records": [],
            "error": "DNS query timed out",
        }
    except Exception as exc:
        return {
            "status": "error",
            "records": [],
            "error": str(exc),
        }

    records = []
    for rdata in answers:
        # TXT records can be split across multiple strings
        value = "".join(part.decode("utf-8", errors="ignore") for part in rdata.strings)
        records.append(value)

    return {
        "status": "ok",
        "records": records,
    }

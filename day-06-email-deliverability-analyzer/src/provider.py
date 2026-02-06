import dns.resolver


def infer_email_provider(domain: str) -> str | None:
    try:
        answers = dns.resolver.resolve(domain, "MX")
    except Exception:
        return None

    hosts = [r.exchange.to_text().lower() for r in answers]

    if any("google.com" in h for h in hosts):
        return "google"

    if any("outlook.com" in h or "protection.outlook.com" in h for h in hosts):
        return "microsoft"

    return None

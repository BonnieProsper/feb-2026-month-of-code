from typing import Iterable, List

from dns_lookup import lookup_txt


COMMON_DKIM_SELECTORS = [
    "default",
    "selector1",
    "selector2",
    "google",
    "smtp",
    "dkim",
    "mail",
]


def _looks_like_dkim_record(txt_values: Iterable[str]) -> bool:
    """
    Heuristic check for a DKIM public key record.

    We deliberately do not fully validate DKIM syntax here.
    The goal is to detect likely presence, not enforce RFC compliance.
    """
    combined = " ".join(txt_values).lower()
    return "v=dkim1" in combined and "p=" in combined


def check_dkim(domain: str, selectors: Iterable[str] | None = None) -> List[dict]:
    """
    Check for presence of DKIM public keys using common selector names.

    DKIM selector discovery is inherently heuristic. We treat the presence
    of at least one valid-looking selector as a strong signal that DKIM
    signing is in use, and absence as high risk.
    """
    selectors = list(selectors) if selectors else COMMON_DKIM_SELECTORS

    checked = []
    valid_selectors = []
    invalid_records = []

    for selector in selectors:
        hostname = f"{selector}._domainkey.{domain}"
        checked.append(hostname)

        try:
            records = lookup_txt(hostname)
        except Exception:
            # DNS failures are treated as absence, not hard failure
            continue

        if not records:
            continue

        if _looks_like_dkim_record(records):
            valid_selectors.append(selector)
        else:
            invalid_records.append(
                {
                    "selector": selector,
                    "hostname": hostname,
                    "records": records,
                }
            )

    findings: List[dict] = []

    if valid_selectors:
        findings.append(
            {
                "check": "dkim",
                "signal": "dkim_selector_found",
                "summary": "DKIM signing appears to be configured",
                "explanation": (
                    "At least one DKIM public key was discovered using common selector names. "
                    "This suggests outgoing mail is DKIM-signed."
                ),
                "evidence": {
                    "valid_selectors": valid_selectors,
                    "selectors_checked": selectors,
                },
            }
        )

        if invalid_records:
            findings.append(
                {
                    "check": "dkim",
                    "signal": "dkim_invalid_record",
                    "summary": "Some DKIM selectors have invalid records",
                    "explanation": (
                        "One or more DKIM selector hostnames returned TXT records that do not "
                        "appear to be valid DKIM public keys. This may indicate stale or "
                        "misconfigured DNS entries."
                    ),
                    "evidence": {
                        "invalid_records": invalid_records,
                    },
                }
            )

        return findings

    findings.append(
        {
            "check": "dkim",
            "signal": "dkim_not_detected",
            "summary": "No DKIM configuration detected",
            "explanation": (
                "No valid DKIM public keys were discovered using common selector names. "
                "Mail from this domain is likely not DKIM-signed, which significantly "
                "increases the risk of spam filtering."
            ),
            "evidence": {
                "selectors_checked": selectors,
                "hostnames_checked": checked,
            },
        }
    )

    return findings

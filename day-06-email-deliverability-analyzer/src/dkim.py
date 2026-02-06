import base64
import re
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


def _extract_dkim_public_key(txt_values: Iterable[str]) -> str | None:
    combined = " ".join(txt_values)
    match = re.search(r"\bp=([A-Za-z0-9+/=]+)", combined)
    return match.group(1) if match else None


def _infer_dkim_key_strength(public_key_b64: str) -> dict | None:
    try:
        decoded = base64.b64decode(public_key_b64, validate=True)
    except Exception:
        return None

    key_bits = len(decoded) * 8

    if key_bits >= 2048:
        return {"strength": "strong", "bits": key_bits}
    if key_bits >= 1024:
        return {"strength": "marginal", "bits": key_bits}

    return {"strength": "weak", "bits": key_bits}


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
            public_key = _extract_dkim_public_key(records)
            strength = (
                _infer_dkim_key_strength(public_key)
                if public_key
                else None
            )

            valid_selectors.append(
                {
                    "selector": selector,
                    "key_strength": strength,
                }
            )
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

        weak = []
        marginal = []
        strong = []

        for entry in valid_selectors:
            strength = entry.get("key_strength")
            if not strength:
                continue

            if strength["strength"] == "weak":
                weak.append(entry)
            elif strength["strength"] == "marginal":
                marginal.append(entry)
            else:
                strong.append(entry)

        if weak:
            findings.append(
                {
                    "check": "dkim",
                    "signal": "dkim_weak_key",
                    "summary": "Weak DKIM key detected",
                    "explanation": (
                        "One or more DKIM selectors use cryptographically weak RSA keys. "
                        "Weak DKIM keys may be rejected or deprioritized by mailbox providers."
                    ),
                    "evidence": weak,
                }
            )

        if marginal:
            findings.append(
                {
                    "check": "dkim",
                    "signal": "dkim_marginal_key",
                    "summary": "Marginal DKIM key strength detected",
                    "explanation": (
                        "Some DKIM keys use 1024-bit RSA, which is considered marginal. "
                        "Upgrading to 2048-bit or ed25519 is recommended."
                    ),
                    "evidence": marginal,
                }
            )

        if strong:
            findings.append(
                {
                    "check": "dkim",
                    "signal": "dkim_strong_key",
                    "summary": "Strong DKIM key detected",
                    "explanation": (
                        "At least one DKIM selector uses a strong cryptographic key."
                    ),
                    "evidence": strong,
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


# TODO: future improvement
# Include ED25519 detection if heuristics expand 
# (currently all keys are treated by byte length). 
# Could add detection via v=DKIM1; 
# k=ed25519 if TXT contains k= parameter.
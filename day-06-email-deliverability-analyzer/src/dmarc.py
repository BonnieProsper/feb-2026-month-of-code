from typing import Dict, List

from src.dns_lookup import lookup_txt


DMARC_PREFIX = "v=DMARC1"


def analyze_dmarc(domain: str) -> List[dict]:
    """
    Analyze DMARC configuration for a domain and return findings.

    This inspects the published DMARC policy and related tags without
    attempting to infer runtime alignment outcomes.
    """
    findings = []

    dmarc_domain = f"_dmarc.{domain}"
    result = lookup_txt(dmarc_domain)

    if result["status"] == "timeout":
        findings.append(_finding(
            signal="dmarc_lookup_error",
            summary="DMARC lookup timed out",
            explanation=(
                "The DMARC record could not be retrieved due to a DNS timeout. "
                "This prevents receivers from applying a domain-level policy."
            ),
            evidence=result.get("error"),
        ))
        return findings

    if result["status"] == "error":
        findings.append(_finding(
            signal="dmarc_lookup_error",
            summary="DMARC lookup failed",
            explanation=(
                "An error occurred while retrieving the DMARC record. "
                "This prevents receivers from applying a domain-level policy."
            ),
            evidence=result.get("error"),
        ))
        return findings

    records = [
        r for r in result.get("records", [])
        if r.upper().startswith(DMARC_PREFIX)
    ]

    if not records:
        findings.append(_finding(
            signal="dmarc_missing",
            summary="No DMARC record found",
            explanation=(
                "Without a DMARC record, the domain provides no guidance to "
                "receiving servers on how to handle authentication failures."
            ),
        ))
        return findings

    if len(records) > 1:
        findings.append(_finding(
            signal="dmarc_parse_error",
            summary="Multiple DMARC records found",
            explanation=(
                "Multiple DMARC records were detected. Receivers may interpret "
                "this unpredictably, resulting in policy enforcement failure."
            ),
            evidence=records,
        ))
        return findings

    raw = records[0]
    tags = _parse_dmarc_tags(raw)

    if not tags:
        findings.append(_finding(
            signal="dmarc_parse_error",
            summary="DMARC record could not be parsed",
            explanation=(
                "The DMARC record exists but could not be parsed into valid tags."
            ),
            evidence=raw,
        ))
        return findings

    policy = tags.get("p")
    if not policy:
        findings.append(_finding(
            signal="dmarc_parse_error",
            summary="DMARC policy tag missing",
            explanation=(
                "The DMARC record does not contain a policy tag (`p`). "
                "Receivers require this to apply enforcement."
            ),
            evidence=raw,
        ))
        return findings

    if policy == "none":
        findings.append(_finding(
            signal="dmarc_policy_none",
            summary="DMARC policy is set to none",
            explanation=(
                "The domain is monitoring authentication results but does not "
                "request enforcement on failures."
            ),
        ))
    elif policy == "quarantine":
        findings.append(_finding(
            signal="dmarc_policy_quarantine",
            summary="DMARC policy is set to quarantine",
            explanation=(
                "The domain requests that failing messages be treated as "
                "suspicious by receiving servers."
            ),
        ))
    elif policy == "reject":
        findings.append(_finding(
            signal="dmarc_policy_reject",
            summary="DMARC policy is set to reject",
            explanation=(
                "The domain requests that failing messages be rejected outright."
            ),
        ))
    else:
        findings.append(_finding(
            signal="dmarc_parse_error",
            summary="Unknown DMARC policy value",
            explanation=(
                "The DMARC policy value is not recognized by common receivers."
            ),
            evidence=policy,
        ))
        return findings

    if "rua" not in tags:
        findings.append(_finding(
            signal="dmarc_no_reporting",
            summary="No DMARC aggregate reporting address configured",
            explanation=(
                "Without aggregate reports, the domain lacks visibility into "
                "authentication failures and abuse attempts."
            ),
        ))

    if tags.get("adkim") == "r" or tags.get("aspf") == "r":
        findings.append(_finding(
            signal="dmarc_relaxed_alignment",
            summary="DMARC alignment is relaxed",
            explanation=(
                "Relaxed alignment allows related domains to pass authentication, "
                "which may reduce spoofing resistance."
            ),
        ))

    return findings


def _parse_dmarc_tags(record: str) -> Dict[str, str]:
    tags = {}
    parts = [p.strip() for p in record.split(";") if p.strip()]

    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        tags[key.strip().lower()] = value.strip().lower()

    return tags


def _finding(signal: str, summary: str, explanation: str, evidence=None) -> dict:
    return {
        "check": "dmarc",
        "signal": signal,
        "summary": summary,
        "explanation": explanation,
        **({"evidence": evidence} if evidence is not None else {}),
    }

from typing import List

from .dns_lookup import lookup_txt


SPF_PREFIX = "v=spf1"


def analyze_spf(domain: str) -> List[dict]:
    """
    Analyze SPF configuration for a domain and return findings.

    This function reports observable SPF risks without attempting
    full RFC validation or recursive include resolution.
    """
    findings = []

    result = lookup_txt(domain)

    if result["status"] == "timeout":
        findings.append(_dns_warning(
            signal="spf_lookup_timeout",
            summary="SPF lookup timed out",
            explanation=(
                "The SPF record could not be retrieved due to a DNS timeout. "
                "This prevents verification of sender authorization."
            ),
            evidence=result.get("error"),
        ))
        return findings

    if result["status"] == "error":
        findings.append(_dns_warning(
            signal="spf_lookup_error",
            summary="SPF lookup failed",
            explanation=(
                "An error occurred while retrieving the SPF record. "
                "This prevents verification of sender authorization."
            ),
            evidence=result.get("error"),
        ))
        return findings

    spf_records = [
        record for record in result.get("records", [])
        if record.lower().startswith(SPF_PREFIX)
    ]

    if not spf_records:
        findings.append(_finding(
            signal="spf_missing",
            summary="No SPF record found",
            explanation=(
                "Without an SPF record, receiving servers cannot verify whether "
                "the sending IP is authorized to send on behalf of this domain."
            ),
        ))
        return findings

    if len(spf_records) > 1:
        findings.append(_finding(
            signal="spf_multiple_records",
            summary="Multiple SPF records found",
            explanation=(
                "Multiple SPF records were detected. Receiving servers may "
                "interpret this unpredictably, leading to authentication failure."
            ),
            evidence=spf_records,
        ))
        return findings

    spf = spf_records[0]
    tokens = spf.split()

    if _has_permissive_all(tokens):
        findings.append(_finding(
            signal="spf_permissive_all",
            summary="SPF record allows all senders",
            explanation=(
                "The SPF record ends with '+all', which explicitly authorizes "
                "any sending host. This removes SPF as a meaningful protection."
            ),
            evidence=spf,
        ))
        return findings

    if _is_complex(tokens):
        findings.append(_finding(
            signal="spf_complexity_risk",
            summary="SPF record is complex",
            explanation=(
                "The SPF record contains many mechanisms or includes. "
                "Complex SPF records increase the risk of DNS lookup limits "
                "and operational errors."
            ),
            evidence=spf,
        ))

    findings.append(_finding(
        signal="spf_present",
        summary="SPF record present",
        explanation=(
            "An SPF record with an explicit policy was found for this domain."
        ),
        evidence=spf,
    ))

    return findings


def _has_permissive_all(tokens: List[str]) -> bool:
    for token in tokens:
        if token.endswith("all"):
            return token.startswith("+") or token == "all"
    return False


def _is_complex(tokens: List[str]) -> bool:
    mechanisms = [
        t for t in tokens
        if t.startswith(("include:", "a", "mx", "ip4:", "ip6:", "exists:"))
    ]
    return len(mechanisms) > 8


def _finding(signal: str, summary: str, explanation: str, evidence=None) -> dict:
    return {
        "check": "spf",
        "signal": signal,
        "summary": summary,
        "explanation": explanation,
        **({"evidence": evidence} if evidence is not None else {}),
    }


def _dns_warning(signal: str, summary: str, explanation: str, evidence=None) -> dict:
    return {
        "check": "spf",
        "signal": signal,
        "summary": summary,
        "explanation": explanation,
        **({"evidence": evidence} if evidence is not None else {}),
    }

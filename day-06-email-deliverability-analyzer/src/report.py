import json
from typing import Any, Dict, Iterable, List, Literal


Severity = Literal["FAIL", "WARN", "PASS"]
Finding = Dict[str, Any]


SEVERITY_MAP: Dict[str, Severity] = {
    # SPF
    "spf_missing": "FAIL",
    "spf_multiple_records": "FAIL",
    "spf_permissive_all": "FAIL",
    "spf_parse_error": "FAIL",
    "spf_present": "PASS",
    "spf_complexity_risk": "WARN",
    "spf_lookup_timeout": "WARN",
    "spf_lookup_error": "WARN",

    # DKIM
    "dkim_not_detected": "FAIL",
    "dkim_selector_missing": "WARN",
    "dkim_lookup_error": "WARN",
    "dkim_invalid_record": "WARN",
    "dkim_selector_found": "PASS",

    # DMARC
    "dmarc_missing": "FAIL",
    "dmarc_parse_error": "FAIL",
    "dmarc_policy_none": "WARN",
    "dmarc_no_reporting": "WARN",
    "dmarc_relaxed_alignment": "WARN",
    "dmarc_policy_quarantine": "PASS",
    "dmarc_policy_reject": "PASS",

    # BIMI
    "bimi_missing": "WARN",
    "bimi_invalid_record": "WARN",
    "bimi_no_logo": "WARN",
    "bimi_svg_invalid": "WARN",
    "bimi_present": "PASS",
}


SEVERITY_ORDER = {
    "FAIL": 0,
    "WARN": 1,
    "PASS": 2,
}


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def normalize_findings(findings: Iterable[Finding]) -> List[Finding]:
    """
    Normalize raw analyzer findings into a strict, stable, JSON-safe schema.

    This function is intentionally tolerant:
    analyzers should never be able to crash the CLI.
    """
    normalized: List[Finding] = []

    for f in findings:
        signal = f.get("signal")
        if not isinstance(signal, str):
            signal = "unknown"

        severity: Severity = SEVERITY_MAP.get(signal, "WARN")

        entry: Finding = {
            "check": f.get("check", "unknown"),
            "signal": signal,
            "severity": severity,
            "summary": f.get("summary", ""),
            "explanation": f.get("explanation", ""),
        }

        if "evidence" in f:
            entry["evidence"] = _json_safe(f["evidence"])

        normalized.append(entry)

    normalized.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))
    return normalized


def format_console_report(findings: List[Finding]) -> str:
    sections: Dict[Severity, List[Finding]] = {
        "FAIL": [],
        "WARN": [],
        "PASS": [],
    }

    for f in findings:
        sections[f["severity"]].append(f)

    lines: List[str] = []

    for severity in ("FAIL", "WARN", "PASS"):
        items = sections[severity]
        if not items:
            continue

        lines.append(severity)
        lines.append("-" * len(severity))

        for f in items:
            lines.append(f"* {f['summary']}")
            if f["explanation"]:
                lines.append(f"  {f['explanation']}")
            if "evidence" in f:
                lines.append(f"  Evidence: {f['evidence']}")

        lines.append("")

    return "\n".join(lines).rstrip()


def format_json_report(findings: List[Finding]) -> str:
    report = {
        "summary": {
            "fail": sum(1 for f in findings if f["severity"] == "FAIL"),
            "warn": sum(1 for f in findings if f["severity"] == "WARN"),
            "pass": sum(1 for f in findings if f["severity"] == "PASS"),
        },
        "findings": findings,
    }

    return json.dumps(report, indent=2, sort_keys=True)


# ---- SARIF OUTPUT (YES, THIS BELONGS HERE) ----

_SARIF_LEVEL = {
    "FAIL": "error",
    "WARN": "warning",
    "PASS": "note",
}


def format_sarif_report(findings: List[Finding]) -> Dict[str, Any]:
    """
    Produce a SARIF v2.1.0 report compatible with GitHub Code Scanning.
    """
    results = []

    for f in findings:
        results.append({
            "ruleId": f["signal"],
            "level": _SARIF_LEVEL.get(f["severity"], "warning"),
            "message": {
                "text": f"{f['summary']} — {f['explanation']}"
            },
        })

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "email-deliverability-analyzer",
                        "informationUri": "https://github.com/yourname/email-deliverability-analyzer",
                        "rules": [],
                    }
                },
                "results": results,
            }
        ],
    }

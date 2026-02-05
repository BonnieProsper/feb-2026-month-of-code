import json


SEVERITY_MAP = {
    # SPF
    "spf_missing": "FAIL",
    "spf_multiple_records": "FAIL",
    "spf_permissive_all": "FAIL",
    "spf_parse_error": "FAIL",
    "spf_present": "PASS",
    "spf_complexity_risk": "WARN",
    "spf_lookup_timeout": "WARN",
    "spf_lookup_error": "WARN",

    # DKIM (future modules will emit these)
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

    # Content heuristics
    "content_spam_terms": "WARN",
    "content_excessive_caps": "WARN",
    "content_excessive_punctuation": "WARN",
    "content_high_link_ratio": "WARN",
}

def normalize_findings(findings):
    normalized = []

    for f in findings:
        signal = f.get("signal")
        severity = SEVERITY_MAP.get(signal, "WARN")

        normalized.append({
            "check": f["check"],
            "signal": signal,
            "severity": severity,
            "summary": f["summary"],
            "explanation": f["explanation"],
            **({"evidence": f["evidence"]} if "evidence" in f else {}),
        })

    return normalized

def format_console_report(findings):
    sections = {
        "FAIL": [],
        "WARN": [],
        "PASS": [],
    }

    for f in findings:
        sections[f["severity"]].append(f)

    lines = []

    for severity in ("FAIL", "WARN", "PASS"):
        items = sections[severity]
        if not items:
            continue

        lines.append(f"{severity}")
        lines.append("-" * len(severity))

        for f in items:
            lines.append(f"* {f['summary']}")
            lines.append(f"  {f['explanation']}")

        lines.append("")

    return "\n".join(lines).rstrip()


def format_json_report(findings):
    report = {
        "summary": {
            "fail": sum(1 for f in findings if f["severity"] == "FAIL"),
            "warn": sum(1 for f in findings if f["severity"] == "WARN"),
            "pass": sum(1 for f in findings if f["severity"] == "PASS"),
        },
        "findings": findings,
    }

    return json.dumps(report, indent=2)

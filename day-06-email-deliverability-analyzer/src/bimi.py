import dns.resolver


def analyze_bimi(domain: str):
    findings = []
    record_name = f"default._bimi.{domain}"

    try:
        answers = dns.resolver.resolve(record_name, "TXT")
    except dns.resolver.NXDOMAIN:
        findings.append({
            "check": "bimi",
            "signal": "bimi_missing",
            "summary": "No BIMI record found",
            "explanation": (
                "No BIMI TXT record was found. BIMI allows supported mailbox "
                "providers to display your brand logo in inboxes."
            ),
        })
        return findings
    except Exception as e:
        findings.append({
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Error retrieving BIMI record",
            "explanation": "An error occurred while querying the BIMI DNS record.",
            "evidence": str(e),
        })
        return findings

    records = [
        "".join(part.decode() for part in r.strings)
        for r in answers
    ]

    record = records[0]

    if not record.lower().startswith("v=bimi1"):
        findings.append({
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Invalid BIMI record version",
            "explanation": "The BIMI record does not start with v=BIMI1.",
            "evidence": record,
        })
        return findings

    if "l=" not in record:
        findings.append({
            "check": "bimi",
            "signal": "bimi_no_logo",
            "summary": "BIMI record missing logo URL",
            "explanation": (
                "The BIMI record does not specify a logo (l=). "
                "A valid SVG logo is required for BIMI to function."
            ),
            "evidence": record,
        })
        return findings

    findings.append({
        "check": "bimi",
        "signal": "bimi_present",
        "summary": "Valid BIMI record detected",
        "explanation": (
            "A BIMI record with a logo URL was found. "
            "Mailbox providers that support BIMI may display your logo."
        ),
        "evidence": record,
    })

    return findings

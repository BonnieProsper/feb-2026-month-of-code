import dns.resolver
import urllib.request
import xml.etree.ElementTree as ET

SVG_MAX_BYTES = 32 * 1024  # BIMI SVGs are intentionally small
SVG_FETCH_TIMEOUT = 5


def _fetch_svg(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "bimi-checker"},
    )
    with urllib.request.urlopen(req, timeout=SVG_FETCH_TIMEOUT) as resp:
        content_type = resp.headers.get("Content-Type", "")
        if "image/svg+xml" not in content_type:
            raise ValueError(f"Unexpected content type: {content_type}")

        data = resp.read(SVG_MAX_BYTES + 1)
        if len(data) > SVG_MAX_BYTES:
            raise ValueError("SVG exceeds size limit")

        return data


def _validate_svg(svg_bytes: bytes) -> None:
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError as e:
        raise ValueError(f"Invalid SVG XML: {e}")

    if root.tag.lower().endswith("svg") is False:
        raise ValueError("Root element is not <svg>")

    for elem in root.iter():
        tag = elem.tag.lower()
        if tag.endswith("script") or tag.endswith("foreignobject"):
            raise ValueError("Disallowed SVG element present")

    width = root.attrib.get("width")
    height = root.attrib.get("height")
    if not width or not height:
        raise ValueError("SVG missing explicit width/height")


def analyze_bimi(domain: str):
    findings = []
    record_name = f"default._bimi.{domain}"

    try:
        answers = dns.resolver.resolve(record_name, "TXT")
    except dns.resolver.NXDOMAIN:
        return [{
            "check": "bimi",
            "signal": "bimi_missing",
            "summary": "No BIMI record found",
            "explanation": (
                "No BIMI TXT record was found. Without BIMI, mailbox providers "
                "cannot display a verified brand logo in the inbox."
            ),
        }]
    except Exception as e:
        return [{
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Error retrieving BIMI record",
            "explanation": "The BIMI DNS record could not be retrieved.",
            "evidence": str(e),
        }]

    records = [
        "".join(part.decode() for part in r.strings)
        for r in answers
    ]

    if len(records) > 1:
        findings.append({
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Multiple BIMI records detected",
            "explanation": (
                "Multiple BIMI TXT records were found. Mailbox providers "
                "expect a single authoritative record."
            ),
            "evidence": records,
        })
        return findings

    record = records[0]
    lower = record.lower()

    if not lower.startswith("v=bimi1"):
        return [{
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Invalid BIMI record version",
            "explanation": "The BIMI record must begin with v=BIMI1.",
            "evidence": record,
        }]

    parts = dict(
        part.split("=", 1)
        for part in record.split(";")
        if "=" in part
    )

    logo_url = parts.get("l")
    authority_url = parts.get("a")

    if not logo_url:
        return [{
            "check": "bimi",
            "signal": "bimi_no_logo",
            "summary": "BIMI record missing logo URL",
            "explanation": (
                "The BIMI record does not include an l= parameter. "
                "A valid SVG logo is required for BIMI."
            ),
            "evidence": record,
        }]

    # SVG validation (fail-open)
    try:
        svg_bytes = _fetch_svg(logo_url)
        _validate_svg(svg_bytes)
    except Exception as e:
        findings.append({
            "check": "bimi",
            "signal": "bimi_svg_invalid",
            "summary": "BIMI logo SVG failed validation",
            "explanation": (
                "A BIMI logo was specified, but the SVG did not meet "
                "basic safety or format requirements."
            ),
            "evidence": str(e),
        })

    findings.append({
        "check": "bimi",
        "signal": "bimi_present",
        "summary": "Valid BIMI record detected",
        "explanation": (
            "A BIMI record with a valid SVG logo was found. "
            "Supporting mailbox providers may display your brand logo."
        ),
        "evidence": {
            "logo": logo_url,
            "authority": authority_url,
        },
    })

    return findings

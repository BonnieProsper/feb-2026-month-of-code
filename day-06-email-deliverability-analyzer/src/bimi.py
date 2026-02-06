import dns.resolver
import urllib.request
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

from src.dns_lookup import lookup_txt


SVG_MAX_BYTES = 32 * 1024
FETCH_TIMEOUT = 5
VALID_SVG_CT = ("image/svg+xml",)


def _fetch_svg(url: str) -> bytes:
    if not url.lower().startswith("https://"):
        raise ValueError("Logo URL must use HTTPS")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "email-deliverability-analyzer"},
    )

    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        content_type = (resp.headers.get("Content-Type") or "").lower()

        if content_type and not any(ct in content_type for ct in VALID_SVG_CT):
            raise ValueError(f"Unexpected Content-Type: {content_type}")

        data = resp.read(SVG_MAX_BYTES + 1)

        if len(data) > SVG_MAX_BYTES:
            raise ValueError("SVG exceeds maximum allowed size")

        return data


def _validate_svg(svg_bytes: bytes) -> None:
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError:
        raise ValueError("Invalid SVG XML")

    if not root.tag.lower().endswith("svg"):
        raise ValueError("Root element is not <svg>")

    for elem in root.iter():
        tag = elem.tag.lower()
        if "script" in tag or "foreignobject" in tag:
            raise ValueError("Disallowed SVG element present")

    if "width" not in root.attrib or "height" not in root.attrib:
        raise ValueError("SVG must declare width and height")


def _validate_vmc_certificate(url: str) -> None:
    if not url.lower().startswith("https://"):
        raise ValueError("VMC authority URL must use HTTPS")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "email-deliverability-analyzer"},
    )

    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        data = resp.read(64 * 1024)

    try:
        cert = x509.load_pem_x509_certificate(data, default_backend())
    except ValueError:
        try:
            cert = x509.load_der_x509_certificate(data, default_backend())
        except ValueError:
            raise ValueError("Authority file is not a valid X.509 certificate")

    now = datetime.datetime.utcnow()

    if cert.not_valid_after < now:
        raise ValueError("VMC certificate is expired")

    pubkey = cert.public_key()
    if isinstance(pubkey, rsa.RSAPublicKey):
        if pubkey.key_size < 2048:
            raise ValueError("VMC certificate RSA key is too small")

    if not cert.subject or not cert.issuer:
        raise ValueError("VMC certificate missing subject or issuer")


def analyze_bimi(domain: str, provider: str | None = None):
    findings = []

    # Provider inference (informational only)
    if provider:
        findings.append(
            {
                "check": "bimi",
                "signal": f"provider_{provider}_context",
                "summary": f"BIMI evaluated in {provider.title()} context",
                "explanation": (
                    "Mailbox providers apply different BIMI and VMC enforcement rules."
                ),
            }
        )

    record_name = f"default._bimi.{domain}"

    result = lookup_txt(record_name)

    if result["status"] == "timeout":
        return findings + [{
            "check": "bimi",
            "signal": "bimi_lookup_error",
            "summary": "BIMI lookup timed out",
            "explanation": (
                "The BIMI record could not be retrieved due to a DNS timeout."
            ),
            "evidence": result.get("error"),
        }]

    if result["status"] == "error":
        return findings + [{
            "check": "bimi",
            "signal": "bimi_lookup_error",
            "summary": "BIMI lookup failed",
            "explanation": (
                "An error occurred while retrieving the BIMI record."
            ),
            "evidence": result.get("error"),
        }]

    records = result.get("records", [])

    if not records:
        return findings + [{
            "check": "bimi",
            "signal": "bimi_missing",
            "summary": "No BIMI record found",
            "explanation": "No BIMI TXT record was found for this domain.",
        }]

    if len(records) != 1:
        return findings + [{
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Multiple BIMI records detected",
            "evidence": records,
        }]

    record = records[0]

    if len(records) != 1:
        return findings + [{
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Multiple BIMI records detected",
            "evidence": records,
        }]

    record = records[0]

    parts = {}
    for part in record.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            parts[k.strip().lower()] = v.strip()

    if parts.get("v", "").strip().upper() != "BIMI1":
        return findings + [{
            "check": "bimi",
            "signal": "bimi_invalid_record",
            "summary": "Invalid BIMI record version",
            "evidence": record,
        }]

    logo_url = parts.get("l")
    if not logo_url:
        return findings + [{
            "check": "bimi",
            "signal": "bimi_no_logo",
            "summary": "BIMI record missing logo URL",
            "evidence": record,
        }]

    try:
        svg_bytes = _fetch_svg(logo_url)
        _validate_svg(svg_bytes)
    except Exception as e:
        return findings + [{
            "check": "bimi",
            "signal": "bimi_svg_invalid",
            "summary": "BIMI SVG logo failed validation",
            "explanation": str(e),
            "evidence": logo_url,
        }]

    authority = parts.get("a")
    if authority:
        try:
            _validate_vmc_certificate(authority)
            findings.append({
                "check": "bimi",
                "signal": "bimi_vmc_valid",
                "summary": "Valid BIMI VMC authority certificate detected",
                "evidence": authority,
            })
        except Exception as e:
            findings.append({
                "check": "bimi",
                "signal": "bimi_vmc_invalid",
                "summary": "BIMI VMC authority certificate failed validation",
                "explanation": str(e),
                "evidence": authority,
            })

    findings.append({
        "check": "bimi",
        "signal": "bimi_present",
        "summary": "Valid BIMI configuration detected",
        "evidence": record,
    })

    return findings

from html.parser import HTMLParser
from typing import List, Dict, Any
from urllib.parse import urlparse


class _HTMLInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self.images = 0
        self.links = []
        self.has_unsubscribe = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "img":
            self.images += 1

        if tag == "a":
            href = attrs.get("href")

            if isinstance(href, str):
                self.links.append(href)

                if "unsubscribe" in href.lower():
                    self.has_unsubscribe = True

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text_chunks.append(text)


def analyze_content(html: str) -> List[Dict[str, Any]]:
    findings = []

    if not html or not html.strip():
        return [{
            "check": "content",
            "signal": "content_missing_html",
            "summary": "Email content is empty",
            "explanation": "No HTML content was provided for analysis.",
        }]

    parser = _HTMLInspector()
    parser.feed(html)

    text_length = sum(len(t) for t in parser.text_chunks)
    image_count = parser.images

    # Image-only email (very bad)
    if image_count > 0 and text_length < 20:
        return [{
            "check": "content",
            "signal": "content_image_only",
            "summary": "Email appears to be image-only",
            "explanation": (
                "Image-only emails are frequently flagged by spam filters "
                "and have poor accessibility and deliverability."
            ),
        }]

    # Low text-to-image ratio
    if image_count > 0 and text_length / max(image_count, 1) < 40:
        findings.append({
            "check": "content",
            "signal": "content_low_text_ratio",
            "summary": "Low text-to-image ratio detected",
            "explanation": (
                "Emails with little text relative to images may trigger "
                "spam filtering heuristics."
            ),
            "evidence": {
                "text_length": text_length,
                "images": image_count,
            },
        })

    # Missing unsubscribe
    if not parser.has_unsubscribe:
        findings.append({
            "check": "content",
            "signal": "content_missing_unsubscribe",
            "summary": "No unsubscribe link detected",
            "explanation": (
                "Commercial email should include a visible unsubscribe "
                "mechanism to comply with deliverability best practices."
            ),
        })

    # Suspicious links
    suspicious = []
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.netloc and parsed.netloc.count(".") >= 3:
            suspicious.append(parsed.netloc)

    if suspicious:
        findings.append({
            "check": "content",
            "signal": "content_suspicious_links",
            "summary": "Potentially suspicious links detected",
            "explanation": (
                "Some links appear to use URL shorteners or unusual domains, "
                "which may reduce trust with mailbox providers."
            ),
            "evidence": suspicious,
        })

    if not findings:
        findings.append({
            "check": "content",
            "signal": "content_ok",
            "summary": "No content-level deliverability issues detected",
            "explanation": (
                "The email content passed basic deliverability hygiene checks."
            ),
        })

    return findings

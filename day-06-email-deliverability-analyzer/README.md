# Email Deliverability Analyzer

A production-style CLI tool that analyzes email authentication and brand indicators
for a given domain.

This tool focuses on correctness, auditability, and safety rather than
auto-remediation.

## Checks Performed

- SPF (RFC 7208)
- DKIM (RFC 6376)
- DMARC (RFC 7489)
- BIMI (RFC  BIMI draft)
  - SVG logo validation
  - VMC authority awareness
  - Provider inference (Google / Microsoft)

## Output Formats

- Console
- JSON
- SARIF (GitHub Code Scanning compatible)

## CI Integration

This project supports SARIF upload to GitHub Code Scanning and can fail CI
based on strict deliverability policies.

## Non-Goals

- Email sending
- DNS modification
- Automatic remediation

## Threat Model

### Inputs
- DNS TXT records
- Remote SVG / certificate URLs

### Threats
- Malformed DNS records
- Malicious SVG payloads
- XML entity expansion
- Oversized remote resources

### Mitigations
- Strict size limits
- HTTPS enforcement
- XML parsing without entity resolution
- Disallowed SVG elements
- Timeouts on all network fetches

### Out of Scope
- Certificate chain validation
- Mailbox-provider-specific policy enforcement



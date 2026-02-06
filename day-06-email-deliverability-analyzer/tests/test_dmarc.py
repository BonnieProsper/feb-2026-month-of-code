from src.dmarc import analyze_dmarc

def test_dmarc_missing(monkeypatch):
    def fake_lookup(domain):
        return {"status": "ok", "records": []}

    monkeypatch.setattr("src.dmarc.lookup_txt", fake_lookup)

    findings = analyze_dmarc("example.com")
    signals = {f["signal"] for f in findings}

    assert "dmarc_missing" in signals


def test_dmarc_reject_policy(monkeypatch):
    def fake_lookup(domain):
        return {
            "status": "ok",
            "records": ["v=DMARC1; p=reject; rua=mailto:d@example.com"],
        }

    monkeypatch.setattr("src.dmarc.lookup_txt", fake_lookup)

    findings = analyze_dmarc("example.com")
    signals = {f["signal"] for f in findings}

    assert "dmarc_policy_reject" in signals

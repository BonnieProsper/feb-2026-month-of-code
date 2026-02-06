from src.spf import analyze_spf

def test_spf_missing(monkeypatch):
    def fake_lookup(domain):
        return {"status": "ok", "records": []}

    monkeypatch.setattr("src.spf.lookup_txt", fake_lookup)

    findings = analyze_spf("example.com")
    signals = {f["signal"] for f in findings}

    assert "spf_missing" in signals


def test_spf_present_basic(monkeypatch):
    def fake_lookup(domain):
        return {
            "status": "ok",
            "records": ["v=spf1 include:_spf.google.com -all"],
        }

    monkeypatch.setattr("src.spf.lookup_txt", fake_lookup)

    findings = analyze_spf("example.com")
    signals = {f["signal"] for f in findings}

    assert "spf_present" in signals

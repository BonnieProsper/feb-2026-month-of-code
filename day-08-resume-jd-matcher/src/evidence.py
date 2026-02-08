EVIDENCE_HINTS = {
    "aws": "Cloud provider usage, deployment, infrastructure work",
    "docker": "Containerization, build pipelines, runtime environments",
    "python": "Production code, automation, backend services",
}


def evidence_hint(term: str) -> str | None:
    return EVIDENCE_HINTS.get(term.lower())


# wire into cli
# tests

def test_evidence_hint_known():
    assert evidence_hint("aws") is not None


def test_evidence_hint_unknown():
    assert evidence_hint("kubernetes") is None

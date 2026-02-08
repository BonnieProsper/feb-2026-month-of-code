import pytest
from src.analysis import GapDetail, GapConfidence, group_gaps_by_category

@pytest.fixture
def sample_gaps():
    return [
        GapDetail(term="python", confidence=GapConfidence.STRONG_MATCH, score=0.9),
        GapDetail(term="docker", confidence=GapConfidence.MISSING, score=0.0),
        GapDetail(term="aws", confidence=GapConfidence.MISSING, score=0.0),
        GapDetail(term="react", confidence=GapConfidence.MISSING, score=0.0),
        GapDetail(term="communication", confidence=GapConfidence.PARTIAL_EVIDENCE, score=0.5),
    ]

def test_group_by_category(sample_gaps):
    grouped = group_gaps_by_category(sample_gaps)

    # Only missing items should be present
    for term in ["docker", "aws", "react"]:
        found = any(term in [g.term for g in v] for v in grouped.values())
        assert found

    # No strong or partial should appear
    assert "python" not in grouped.get("Languages", [])
    assert "communication" not in grouped.get("Other", [])

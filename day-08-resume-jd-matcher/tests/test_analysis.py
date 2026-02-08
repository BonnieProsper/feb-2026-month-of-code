from src.analysis import classify_gap, GapConfidence, analyze_gaps


def test_gap_confidence_classification():
    resume_tokens = {"python", "docker"}
    resume_text = "Built services in Python using Docker."

    assert classify_gap("python", resume_tokens, resume_text) == GapConfidence.STRONG_MATCH
    assert classify_gap("cloud platforms", resume_tokens, resume_text) == GapConfidence.PARTIAL_EVIDENCE
    assert classify_gap("kubernetes", resume_tokens, resume_text) == GapConfidence.MISSING


def test_gap_analysis_shapes():
    resume = {"python": 1.0}
    jd = {"python": 1.0, "kubernetes": 1.0}

    result = analyze_gaps(resume, jd)

    assert "kubernetes" in [t for t, _ in result.jd_emphasized_missing]

from src.analysis import classify_gap, GapConfidence, analyze_gaps


def test_gap_confidence_classification():
    resume_tokens = {"python", "docker"}
    resume_text = "Built services in Python using Docker."

    assert classify_gap("python", resume_tokens, resume_text) == GapConfidence.STRONG_MATCH
    assert (
        classify_gap("cloud platforms", resume_tokens, resume_text)
        == GapConfidence.PARTIAL_EVIDENCE
    )
    assert classify_gap("kubernetes", resume_tokens, resume_text) == GapConfidence.MISSING


def test_gap_analysis_shapes():
    resume_tfidf = {"python": 1.0}
    jd_tfidf = {"python": 1.0, "kubernetes": 1.0}

    result = analyze_gaps(
        resume_tfidf=resume_tfidf,
        jd_tfidf=jd_tfidf,
        resume_tokens={"python"},
        resume_text="Experienced Python developer",
    )

    terms = [g.term for g in result.gaps]
    assert "kubernetes" in terms

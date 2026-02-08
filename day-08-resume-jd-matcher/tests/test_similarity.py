from src.similarity import compute_cosine_similarity


def test_similarity_bounds():
    score = compute_cosine_similarity({"a": 1.0}, {"a": 1.0})
    assert 0.0 <= score <= 1.0


def test_similarity_directionality():
    jd = {"python": 1.0, "docker": 1.0}
    resume_good = {"python": 1.0, "docker": 0.8}
    resume_bad = {"excel": 1.0}

    assert compute_cosine_similarity(resume_good, jd) > compute_cosine_similarity(resume_bad, jd)


def test_empty_vectors():
    assert compute_cosine_similarity({}, {}) == 0.0

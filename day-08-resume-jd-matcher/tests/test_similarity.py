from src.similarity import compute_similarity


def test_similarity_bounds():
    result = compute_similarity(["a"], ["a"])
    assert 0.0 <= result.cosine_similarity <= 1.0


def test_similarity_directionality():
    jd = ["python", "docker"]
    resume_good = ["python", "docker"]
    resume_bad = ["excel"]

    good = compute_similarity(resume_good, jd)
    bad = compute_similarity(resume_bad, jd)

    assert good.cosine_similarity > bad.cosine_similarity


def test_empty_vectors():
    result = compute_similarity([], [])
    assert result.cosine_similarity == 0.0

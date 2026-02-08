from src.taxonomy import classify_skill


def test_known_skill_classification():
    assert classify_skill("python") == "Languages"
    assert classify_skill("docker") == "Tooling"
    assert classify_skill("aws") == "Cloud / Platforms"


def test_unknown_skill_fallback():
    assert classify_skill("kubernetes") == "Other"

import subprocess
import sys
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_cli_json_output_scores_and_categories():
    """
    Integration test: ensures CLI --json output includes
    scores, confidence, and category-ready gaps
    """
    resume_path = FIXTURES_DIR / "sample_resume.pdf"
    jd_path = FIXTURES_DIR / "sample_jd.txt"

    # Run CLI with --json and capture output
    result = subprocess.run(
        [sys.executable, "-m", "src.cli",
         "--resume", str(resume_path),
         "--job", str(jd_path),
         "--json",
         "--top-n", "10",
         "--deterministic"],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    # Check top-level keys
    assert "gaps" in data
    assert "resume_emphasized_extra" in data
    assert "shared_terms" in data
    assert "similarity" in data

    # Check gaps
    for g in data["gaps"]:
        assert "term" in g
        assert "confidence" in g
        assert g["confidence"] in {"strong_match", "partial_evidence", "missing"}
        assert "score" in g
        assert isinstance(g["score"], (float, int))
        assert "explanation" in g

    # Ensure missing skills categories exist
    missing_gaps = [g for g in data["gaps"] if g["confidence"] == "missing"]
    assert all(isinstance(g["term"], str) for g in missing_gaps)

    # Ensure resume_emphasized_extra and shared_terms are lists
    assert isinstance(data["resume_emphasized_extra"], list)
    assert isinstance(data["shared_terms"], list)

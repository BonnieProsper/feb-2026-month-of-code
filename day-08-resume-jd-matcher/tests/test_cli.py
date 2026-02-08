import subprocess
import sys


def test_cli_runs(fixtures_dir):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "--resume",
            str(fixtures_dir / "sample_resume.pdf"),
            "--job",
            str(fixtures_dir / "sample_jd.txt"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Similarity" in result.stdout
    assert "Gap Analysis" in result.stdout

import pytest
from pathlib import Path

from src.parse_resume import parse_resume


def test_extract_text_resume(tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("Software engineer with Python experience.")

    result = parse_resume(resume)
    assert "python" in result.text.lower()
    assert result.source_type == "text"


def test_extract_pdf_resume(fixtures_dir):
    pdf_path = fixtures_dir / "sample_resume.pdf"
    result = parse_resume(pdf_path)

    assert isinstance(result.text, str)
    assert len(result.text.strip()) > 200
    assert result.source_type == "pdf"


def test_unsupported_file_type(tmp_path):
    bad = tmp_path / "resume.docx"
    bad.write_text("nope")

    with pytest.raises(ValueError):
        parse_resume(bad)

import pytest
from pathlib import Path

from src.parse_resume import  parse_resume


def test_extract_text_resume(tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("Software engineer with Python experience.")

    text =  parse_resume(resume)
    assert "python" in text.lower()


def test_extract_pdf_resume(fixtures_dir):
    pdf_path = fixtures_dir / "sample_resume.pdf"
    text =  parse_resume(pdf_path)

    assert isinstance(text, str)
    assert len(text.strip()) > 200


def test_unsupported_file_type(tmp_path):
    bad = tmp_path / "resume.docx"
    bad.write_text("nope")

    with pytest.raises(ValueError):
         parse_resume(bad)

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError


@dataclass
class ResumeParseResult:
    text: str
    source_type: str
    warnings: List[str]
    char_count: int
    line_count: int
    page_count: Optional[int]


def parse_resume(path: Path) -> ResumeParseResult:
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    if path.suffix.lower() == ".txt":
        return _parse_text_resume(path)

    if path.suffix.lower() == ".pdf":
        return _parse_pdf_resume(path)

    raise ValueError(f"Unsupported resume format: {path.suffix}")


def _parse_text_resume(path: Path) -> ResumeParseResult:
    text = path.read_text(encoding="utf-8", errors="replace")

    warnings = []
    if not text.strip():
        warnings.append("Text resume is empty or whitespace only.")

    lines = text.splitlines()

    return ResumeParseResult(
        text=text,
        source_type="text",
        warnings=warnings,
        char_count=len(text),
        line_count=len(lines),
        page_count=None,
    )


def _parse_pdf_resume(path: Path) -> ResumeParseResult:
    warnings: List[str] = []

    try:
        text = extract_text(path)
    except PDFSyntaxError:
        raise ValueError("PDF appears to be malformed or unreadable.")
    except Exception as exc:
        raise ValueError(f"PDF extraction failed: {exc}")

    if not text or not text.strip():
        warnings.append(
            "No extractable text found in PDF. "
            "This may be a scanned document or image-based resume."
        )

    lines = text.splitlines()

    if len(lines) < 5:
        warnings.append(
            "Very little text extracted from PDF. "
            "Layout or encoding issues may be present."
        )

    return ResumeParseResult(
        text=text,
        source_type="pdf",
        warnings=warnings,
        char_count=len(text),
        line_count=len(lines),
        page_count=None,  # pdfminer does not reliably expose this
    )

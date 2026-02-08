from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class GapConfidence(Enum):
    STRONG_MATCH = "strong_match"
    PARTIAL_EVIDENCE = "partial_evidence"
    MISSING = "missing"


@dataclass
class GapDetail:
    term: str
    confidence: GapConfidence
    explanation: str


@dataclass
class GapAnalysisResult:
    gaps: List[GapDetail]
    resume_emphasized_extra: List[str]
    shared_terms: List[str]


def classify_gap(term: str, resume_tokens: set[str], resume_text: str) -> GapConfidence:
    normalized = term.lower()

    if normalized in resume_tokens or normalized in resume_text:
        return GapConfidence.STRONG_MATCH

    parts = normalized.split()
    if any(p in resume_tokens for p in parts):
        return GapConfidence.PARTIAL_EVIDENCE

    return GapConfidence.MISSING


def explain_gap(term: str, confidence: GapConfidence) -> str:
    if confidence == GapConfidence.STRONG_MATCH:
        return f"'{term}' is explicitly referenced in the resume."

    if confidence == GapConfidence.PARTIAL_EVIDENCE:
        return (
            f"'{term}' is not explicitly named, but related experience appears to be present."
        )

    return f"'{term}' is emphasized in the job description but not evidenced in the resume."


def analyze_gaps(
    resume_tfidf: Dict[str, float],
    jd_tfidf: Dict[str, float],
    resume_tokens: set[str],
    resume_text: str,
    top_n: int = 15,
    epsilon: float = 1e-6,
) -> GapAnalysisResult:
    gaps: List[GapDetail] = []

    jd_sorted = sorted(jd_tfidf.items(), key=lambda x: x[1], reverse=True)

    for term, weight in jd_sorted:
        if len(gaps) >= top_n:
            break
        if weight <= epsilon:
            continue

        confidence = classify_gap(term, resume_tokens, resume_text)
        gaps.append(
            GapDetail(
                term=term,
                confidence=confidence,
                explanation=explain_gap(term, confidence),
            )
        )

    resume_emphasized_extra = [
        term
        for term, w in resume_tfidf.items()
        if w > epsilon and jd_tfidf.get(term, 0.0) <= epsilon
    ][:top_n]

    shared_terms = [
        term
        for term, w in jd_tfidf.items()
        if w > epsilon and resume_tfidf.get(term, 0.0) > epsilon
    ][:top_n]

    return GapAnalysisResult(
        gaps=gaps,
        resume_emphasized_extra=resume_emphasized_extra,
        shared_terms=shared_terms,
    )

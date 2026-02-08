from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
from collections import defaultdict

from .taxonomy import classify_skill


class GapConfidence(Enum):
    STRONG_MATCH = "strong_match"
    PARTIAL_EVIDENCE = "partial_evidence"
    MISSING = "missing"


@dataclass
class GapDetail:
    term: str
    confidence: GapConfidence
    explanation: str | None = None
    score: float | None = None  # numeric confidence weighting


@dataclass
class GapAnalysisResult:
    gaps: List[GapDetail]
    resume_emphasized_extra: List[str]
    shared_terms: List[str]


def classify_gap(term: str, resume_tokens: set[str], resume_text: str) -> GapConfidence:
    """
    Classify term into categorical confidence (Tier-1)
    """
    normalized = term.lower()

    if normalized in resume_tokens or normalized in resume_text:
        return GapConfidence.STRONG_MATCH

    parts = normalized.split()
    if any(p in resume_tokens for p in parts):
        return GapConfidence.PARTIAL_EVIDENCE

    return GapConfidence.MISSING


def classify_gap_score(term: str, resume_tokens: set[str], resume_text: str) -> float:
    """
    Confidence-weighted numeric score (Tier-1 / Tier-3)
    """
    normalized = term.lower()
    if normalized in resume_tokens or normalized in resume_text:
        return 1.0
    parts = normalized.split()
    if any(p in resume_tokens for p in parts):
        return 0.5
    return 0.0


def analyze_gaps(
    resume_tfidf: Dict[str, float],
    jd_tfidf: Dict[str, float],
    resume_tokens: set[str],
    resume_text: str,
    top_n: int = 15,
    epsilon: float = 1e-6,
) -> GapAnalysisResult:
    """
    Analyze gaps between resume and job description
    Returns structured GapAnalysisResult
    """
    gaps: List[GapDetail] = []

    # Sort JD terms by importance (TF-IDF weight)
    jd_sorted = sorted(jd_tfidf.items(), key=lambda x: x[1], reverse=True)

    for term, weight in jd_sorted:
        if len(gaps) >= top_n:
            break
        if weight <= epsilon:
            continue

        confidence = classify_gap(term, resume_tokens, resume_text)
        score = classify_gap_score(term, resume_tokens, resume_text) * weight

        gaps.append(GapDetail(term=term, confidence=confidence, score=score))

    # Additional diagnostics
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


def group_gaps_by_category(gaps: List[GapDetail]) -> Dict[str, List[GapDetail]]:
    """
    Tier-2.2 / Tier-3: group missing gaps by taxonomy category
    """
    grouped = defaultdict(list)
    for g in gaps:
        if g.confidence == GapConfidence.MISSING:
            category = classify_skill(g.term)
            grouped[category].append(g)
    return dict(grouped)

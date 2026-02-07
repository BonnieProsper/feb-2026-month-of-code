from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class GapAnalysisResult:
    jd_emphasized_missing: List[Tuple[str, float]]
    resume_emphasized_extra: List[Tuple[str, float]]
    shared_emphasis: List[Tuple[str, float, float]]


def analyze_gaps(
    resume_tfidf: Dict[str, float],
    jd_tfidf: Dict[str, float],
    top_n: int = 15,
    epsilon: float = 1e-6,
) -> GapAnalysisResult:
    jd_sorted = sorted(
        jd_tfidf.items(), key=lambda x: x[1], reverse=True
    )
    resume_sorted = sorted(
        resume_tfidf.items(), key=lambda x: x[1], reverse=True
    )

    jd_emphasized_missing: List[Tuple[str, float]] = []
    resume_emphasized_extra: List[Tuple[str, float]] = []
    shared_emphasis: List[Tuple[str, float, float]] = []

    # JD terms not represented in resume
    for term, jd_weight in jd_sorted:
        if len(jd_emphasized_missing) >= top_n:
            break

        resume_weight = resume_tfidf.get(term, 0.0)
        if jd_weight > epsilon and resume_weight <= epsilon:
            jd_emphasized_missing.append((term, jd_weight))

    # Resume terms not represented in JD
    for term, resume_weight in resume_sorted:
        if len(resume_emphasized_extra) >= top_n:
            break

        jd_weight = jd_tfidf.get(term, 0.0)
        if resume_weight > epsilon and jd_weight <= epsilon:
            resume_emphasized_extra.append((term, resume_weight))

    # Shared emphasis
    for term, jd_weight in jd_sorted:
        if len(shared_emphasis) >= top_n:
            break

        resume_weight = resume_tfidf.get(term, 0.0)
        if jd_weight > epsilon and resume_weight > epsilon:
            shared_emphasis.append((term, jd_weight, resume_weight))

    return GapAnalysisResult(
        jd_emphasized_missing=jd_emphasized_missing,
        resume_emphasized_extra=resume_emphasized_extra,
        shared_emphasis=shared_emphasis,
    )

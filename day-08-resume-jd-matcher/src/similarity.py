from dataclasses import dataclass
from typing import Dict, List, Tuple
from collections import Counter

import math


@dataclass
class SimilarityResult:
    cosine_similarity: float
    jd_coverage_ratio: float
    resume_relevance_ratio: float
    resume_tfidf: Dict[str, float]
    jd_tfidf: Dict[str, float]


def compute_similarity(
    resume_tokens: List[str],
    jd_tokens: List[str],
) -> SimilarityResult:
    resume_counts = Counter(resume_tokens)
    jd_counts = Counter(jd_tokens)

    vocabulary = set(resume_counts) | set(jd_counts)

    tf_resume = _term_frequency(resume_counts)
    tf_jd = _term_frequency(jd_counts)

    idf = _inverse_document_frequency(vocabulary, resume_counts, jd_counts)

    resume_tfidf = {
        term: tf_resume.get(term, 0.0) * idf[term]
        for term in vocabulary
    }
    jd_tfidf = {
        term: tf_jd.get(term, 0.0) * idf[term]
        for term in vocabulary
    }

    cosine = _cosine_similarity(resume_tfidf, jd_tfidf)

    jd_coverage = _coverage_ratio(jd_counts, resume_counts)
    resume_relevance = _coverage_ratio(resume_counts, jd_counts)

    return SimilarityResult(
        cosine_similarity=cosine,
        jd_coverage_ratio=jd_coverage,
        resume_relevance_ratio=resume_relevance,
        resume_tfidf=resume_tfidf,
        jd_tfidf=jd_tfidf,
    )


def _term_frequency(counts: Counter) -> Dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {}

    return {term: count / total for term, count in counts.items()}


def _inverse_document_frequency(
    vocabulary: set,
    resume_counts: Counter,
    jd_counts: Counter,
) -> Dict[str, float]:
    idf = {}
    doc_count = 2  # resume + JD

    for term in vocabulary:
        docs_with_term = 0
        if term in resume_counts:
            docs_with_term += 1
        if term in jd_counts:
            docs_with_term += 1

        # Smoothed IDF to avoid division by zero
        idf[term] = math.log((doc_count + 1) / (docs_with_term + 1)) + 1

    return idf


def _cosine_similarity(
    vec_a: Dict[str, float],
    vec_b: Dict[str, float],
) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for term in vec_a:
        a = vec_a.get(term, 0.0)
        b = vec_b.get(term, 0.0)
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def _coverage_ratio(
    source: Counter,
    target: Counter,
) -> float:
    if not source:
        return 0.0

    covered = sum(1 for term in source if term in target)
    return covered / len(source)

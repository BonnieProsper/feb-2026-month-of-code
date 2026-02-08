import argparse
import json
from pathlib import Path
import random
from collections import defaultdict

from src.parse_resume import parse_resume
from src.preprocess import preprocess_text
from src.similarity import compute_similarity
from src.analysis import analyze_gaps, GapConfidence, group_gaps_by_category
from src.explain import explain_gap


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare resume text and job description text using explicit, interpretable similarity measures."
    )
    parser.add_argument("--resume", required=True, help="Path to resume file (.pdf or .txt)")
    parser.add_argument("--job", required=True, help="Path to job description text file")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Disable sources of randomness for reproducible output",
    )

    args = parser.parse_args()

    if args.deterministic:
        random.seed(0)

    # Load and preprocess
    resume_result = parse_resume(Path(args.resume))
    jd_text = Path(args.job).read_text(encoding="utf-8", errors="replace")

    resume_prep = preprocess_text(resume_result.text)
    jd_prep = preprocess_text(jd_text)

    similarity = compute_similarity(resume_prep.tokens, jd_prep.tokens)

    # Tier-1 & Tier-3: analyze gaps with confidence and scores
    gaps_result = analyze_gaps(
        resume_tfidf=similarity.resume_tfidf,
        jd_tfidf=similarity.jd_tfidf,
        resume_tokens=set(resume_prep.tokens),
        resume_text=resume_result.text.lower(),
        top_n=args.top_n,
    )

    # Add Tier-1 explanations
    for g in gaps_result.gaps:
        g.explanation = explain_gap(g.term, g.confidence)

    if args.json:
        print(
            json.dumps(
                {
                    "similarity": similarity.__dict__,
                    "gaps": [
                        {
                            "term": g.term,
                            "confidence": g.confidence.value,
                            "score": g.score,
                            "explanation": g.explanation,
                        }
                        for g in gaps_result.gaps
                    ],
                    "resume_emphasized_extra": gaps_result.resume_emphasized_extra,
                    "shared_terms": gaps_result.shared_terms,
                },
                indent=2,
            )
        )
        return

    _print_human(similarity, gaps_result)


def _print_human(similarity, gaps_result) -> None:
    print("\nResume <-> Job Description Text Comparison")
    print("----------------------------------------")
    print("This tool compares surface-level text usage only.\n")

    print("Similarity signals")
    print("------------------")
    print(f"TF-IDF cosine similarity: {similarity.cosine_similarity:.3f}")
    print(f"JD coverage ratio: {similarity.jd_coverage_ratio:.3f}")
    print(f"Resume relevance ratio: {similarity.resume_relevance_ratio:.3f}\n")

    # Tier-1: basic gap grouping
    grouped = defaultdict(list)
    for g in gaps_result.gaps:
        grouped[g.confidence].append(g)

    print("Gap Analysis")
    print("------------")
    for confidence in GapConfidence:
        print(confidence.value.replace("_", " ").title() + ":")
        items = grouped[confidence]
        if not items:
            print("  (no items detected)")
        else:
            for g in items:
                score_str = f" [score: {g.score:.2f}]" if g.score is not None else ""
                print(f"  - {g.term}: {g.explanation}{score_str}")
        print()

    # Tier-2.2 / Tier-3: category-aware diagnostics for missing items
    print("Missing Skills by Category")
    print("--------------------------")
    categorized = group_gaps_by_category(gaps_result.gaps)
    if not categorized:
        print("  (no missing items detected)\n")
    else:
        for category, items in categorized.items():
            print(f"{category}:")
            for g in items:
                score_str = f" [score: {g.score:.2f}]" if g.score is not None else ""
                print(f"  - {g.term}: {g.explanation}{score_str}")
            print()


if __name__ == "__main__":
    main()

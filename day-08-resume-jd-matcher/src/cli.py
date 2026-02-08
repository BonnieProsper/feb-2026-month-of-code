import argparse
import json
from pathlib import Path
import random

from parse_resume import parse_resume
from preprocess import preprocess_text
from similarity import compute_similarity
from analysis import analyze_gaps, GapConfidence


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

    resume_result = parse_resume(Path(args.resume))
    jd_text = Path(args.job).read_text(encoding="utf-8", errors="replace")

    resume_prep = preprocess_text(resume_result.text)
    jd_prep = preprocess_text(jd_text)

    similarity = compute_similarity(resume_prep.tokens, jd_prep.tokens)

    gaps = analyze_gaps(
        resume_tfidf=similarity.resume_tfidf,
        jd_tfidf=similarity.jd_tfidf,
        resume_tokens=set(resume_prep.tokens),
        resume_text=resume_result.text.lower(),
        top_n=args.top_n,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "similarity": similarity.__dict__,
                    "gaps": [
                        {
                            "term": g.term,
                            "confidence": g.confidence.value,
                            "explanation": g.explanation,
                        }
                        for g in gaps.gaps
                    ],
                },
                indent=2,
            )
        )
        return

    _print_human(resume_result, similarity, gaps)


def _print_human(resume, similarity, gaps) -> None:
    print()
    print("Resume ↔ Job Description Text Comparison")
    print("---------------------------------------")
    print("This tool compares surface-level text usage only.")
    print()

    print("Similarity signals")
    print("------------------")
    print(f"TF-IDF cosine similarity: {similarity.cosine_similarity:.3f}")
    print(f"JD coverage ratio: {similarity.jd_coverage_ratio:.3f}")
    print(f"Resume relevance ratio: {similarity.resume_relevance_ratio:.3f}")
    print()

    grouped = {
        GapConfidence.STRONG_MATCH: [],
        GapConfidence.PARTIAL_EVIDENCE: [],
        GapConfidence.MISSING: [],
    }

    for g in gaps.gaps:
        grouped[g.confidence].append(g)

    print("Gap analysis")
    print("------------")

    for confidence in GapConfidence:
        print(confidence.value.replace("_", " ").title() + ":")
        for g in grouped[confidence]:
            print(f"  - {g.term}: {g.explanation}")
        print()


if __name__ == "__main__":
    main()

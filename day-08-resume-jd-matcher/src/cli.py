import argparse
import json
from pathlib import Path

from parse_resume import parse_resume
from preprocess import preprocess_text
from similarity import compute_similarity
from analysis import analyze_gaps


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare resume text and job description text using explicit, interpretable similarity measures."
    )
    parser.add_argument("--resume", required=True, help="Path to resume file (.pdf or .txt)")
    parser.add_argument("--job", required=True, help="Path to job description text file")
    parser.add_argument("--top-n", type=int, default=10, help="Number of terms to display per section")
    parser.add_argument("--json", action="store_true", help="Output structured JSON only")

    args = parser.parse_args()

    resume_result = parse_resume(Path(args.resume))
    jd_text = Path(args.job).read_text(encoding="utf-8", errors="replace")

    resume_prep = preprocess_text(resume_result.text)
    jd_prep = preprocess_text(jd_text)

    similarity = compute_similarity(resume_prep.tokens, jd_prep.tokens)
    gaps = analyze_gaps(
        resume_tfidf=similarity.resume_tfidf,
        jd_tfidf=similarity.jd_tfidf,
        top_n=args.top_n,
    )

    if args.json:
        print(json.dumps({
            "resume": {
                "source_type": resume_result.source_type,
                "char_count": resume_result.char_count,
                "line_count": resume_result.line_count,
                "warnings": resume_result.warnings,
            },
            "similarity": {
                "cosine": similarity.cosine_similarity,
                "jd_coverage": similarity.jd_coverage_ratio,
                "resume_relevance": similarity.resume_relevance_ratio,
            },
            "gap_analysis": {
                "jd_emphasized_missing": gaps.jd_emphasized_missing,
                "resume_emphasized_extra": gaps.resume_emphasized_extra,
                "shared_emphasis": gaps.shared_emphasis,
            }
        }, indent=2))
        return

    _print_human_readable(resume_result, similarity, gaps, args.top_n)


def _print_human_readable(resume, similarity, gaps, top_n: int) -> None:
    print()
    print("Resume ↔ Job Description Text Comparison")
    print("---------------------------------------")
    print("This tool compares surface-level text usage only.")
    print("It does not assess candidate quality, skill proficiency, or hiring likelihood.")
    print()

    print("Input diagnostics")
    print("-----------------")
    print(f"Resume source type: {resume.source_type}")
    print(f"Extracted characters: {resume.char_count}")
    print(f"Extracted lines: {resume.line_count}")
    for w in resume.warnings:
        print(f"WARNING: {w}")
    print()

    print("Similarity signals")
    print("------------------")
    print(f"TF-IDF cosine similarity: {similarity.cosine_similarity:.3f}")
    print("  Measures weighted vocabulary overlap, not semantic equivalence.")
    print(f"JD coverage ratio: {similarity.jd_coverage_ratio:.3f}")
    print("  Fraction of job description terms appearing at least once in the resume.")
    print(f"Resume relevance ratio: {similarity.resume_relevance_ratio:.3f}")
    print("  Fraction of resume terms appearing at least once in the job description.")
    print()

    print("Gap analysis")
    print("------------")

    print("JD-emphasized terms weakly represented in resume:")
    for term, weight in gaps.jd_emphasized_missing[:top_n]:
        print(f"  - {term} (jd weight: {weight:.4f})")
    print()

    print("Resume-emphasized terms with low JD presence:")
    for term, weight in gaps.resume_emphasized_extra[:top_n]:
        print(f"  - {term} (resume weight: {weight:.4f})")
    print()

    print("Shared high-emphasis terms:")
    for term, jd_w, res_w in gaps.shared_emphasis[:top_n]:
        print(f"  - {term} (jd: {jd_w:.4f}, resume: {res_w:.4f})")
    print()

    print("Caveats")
    print("-------")
    print("- Absence of a term does not imply lack of experience.")
    print("- Different wording can reduce measured overlap.")
    print("- Short or templated job descriptions can distort weights.")
    print()


if __name__ == "__main__":
    main()

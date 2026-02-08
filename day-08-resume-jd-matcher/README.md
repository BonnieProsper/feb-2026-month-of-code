# Resume ↔ Job Description Matcher
A diagnostic text evaluation tool
________________________________________
## Overview
This tool compares a resume and a job description using explicit, surface-level text similarity measures.
Its purpose is not to predict hiring outcomes or evaluate candidate quality.
It exists to make resume-job alignment inspectable, auditable, and explainable.

The output answers a narrow but common question:
- Given the text that appears in this resume and this job description, where do they align, and where do they diverge?
________________________________________
## What this tool measures
This tool measures textual alignment, specifically:
-	Overlap in normalized terms between a resume and a job description
-	Relative emphasis of terms in each document
-	Directional coverage (what the JD mentions that the resume does not, and vice versa)
-	Statistically weighted similarity using TF-IDF and cosine similarity

All metrics are computed directly from visible text.
There is no inference beyond term frequency and weighting.
________________________________________
## What this tool explicitly does not measure
This tool does not:
-	Predict hiring decisions
-	Assess candidate quality or seniority
-	Infer skills or competencies
-	Evaluate “fit” of any kind
-	Emulate ATS ranking systems
-	Rewrite or recommend changes to resumes
-	Perform semantic matching or synonym expansion

A low similarity value does not mean a candidate is unqualified.
A high similarity value does not mean a candidate should be hired.
The output reflects text usage only.
________________________________________
## Why resume matching is hard (and why scope is limited)
Resumes and job descriptions are not neutral datasets:
-	Resumes are compressed narratives with implied experience
-	Job descriptions are often aspirational or templated
-	Important experience is frequently described indirectly
-	The same concept appears under many surface forms
Attempting to “solve” this holistically often leads to opaque heuristics and overconfident scoring. This tool intentionally avoids that.
It favors conservative, inspectable signals over speculative intelligence.
________________________________________
## Input handling
### Resume
-	Supported formats:
    - PDF (best-effort text extraction)
    - Plain text (.txt)
-	PDF extraction uses a text-first parser
-	Scanned or image-based PDFs will not extract reliably
Extraction warnings are surfaced explicitly.
If little or no text is extractable, the tool says so.
### Job description
-	Plain text input
-	No formatting or section assumptions
________________________________________
## Text preprocessing
Both documents go through the same preprocessing pipeline.
Steps (intentionally minimal and lossy):
1.	Lowercasing
2.	Punctuation replaced with whitespace
3.	Whitespace tokenization
4.	Removal of a small, explicit stopword list
5.	Dropping very short tokens

No stemming, lemmatization, synonym expansion, or phrase inference is performed.

Tradeoffs are deliberate:
-	Consistency and inspectability over semantic richness
-	Reduced noise at the cost of nuance
________________________________________
## Similarity metrics
The tool reports three complementary signals.
### 1. TF-IDF cosine similarity
Measures how similar the weighted term distributions of the resume and job description are.
-	Downweights boilerplate
-	Independent of document length
-	Bounded between 0 and 1
This reflects shared vocabulary emphasis, not semantic equivalence.
________________________________________
### 2. Job description coverage ratio
The fraction of unique job description terms that appear at least once in the resume.
This answers:
How much of the JD’s vocabulary is represented in the resume text?
________________________________________
### 3. Resume relevance ratio
The fraction of unique resume terms that appear at least once in the job description.
This answers:
How much of the resume’s vocabulary aligns with the JD’s vocabulary?
These ratios are directional and intentionally asymmetric.
________________________________________
## Gap analysis
Gap analysis is descriptive, not prescriptive.
The tool reports three ranked lists:
### Job-description-emphasized terms weakly represented in the resume
Terms that carry high weight in the JD but are absent or minimal in the resume text.
Each term is assigned:
     - **Categorical confidence**: STRONG_MATCH, PARTIAL_EVIDENCE, MISSING
     - **Numeric score**: confidence-weighted by JD TF-IDF importance
     - **Category**: e.g., Languages, Frameworks, Tooling
### Resume-emphasized terms with low JD presence
Terms heavily emphasized in the resume but barely present in the JD.
### Shared high-emphasis terms
Terms that are emphasized in both documents.
Ranking is based on TF-IDF weight.
All terms are directly traceable to the source text.

The tool also produces **category-aware diagnostics** for missing skills, grouping absent items by taxonomy for easy inspection (e.g., all missing cloud skills together).
________________________________________
## Output
### Human-readable CLI output
The default CLI output:
-	Leads with scope and limitations
-	Surfaces extraction warnings early
-	Explains each metric inline
-	Avoids judgmental language
### JSON output

Using the `--json` flag emits structured output suitable for downstream analysis:

```json
{
  "similarity": { ... },
  "gaps": [
    {
      "term": "docker",
      "confidence": "missing",
      "score": 0.0,
      "explanation": "Emphasized in the job description but not evidenced in the resume"
    }
  ],
  "resume_emphasized_extra": [ ... ],
  "shared_terms": [ ... ]
}
```
________________________________________
## Known limitations
This tool intentionally accepts the following limitations:
-	No semantic matching or synonym handling
-	Multi-word concepts are split into individual tokens
-	Certain technical terms degrade during normalization (c++, node.js)
-	TF-IDF is computed over only two documents
-	Short or templated job descriptions can distort weights
-	Absence of a term does not imply lack of experience
These are documented tradeoffs, not oversights.
________________________________________
## When this tool is useful
-	Understanding why a resume and job description appear misaligned
-	Auditing keyword-driven screening behavior
-	Explaining rejections or mismatches in concrete terms
-	Internal diagnostics for recruiting or career review
________________________________________
## When this tool is not appropriate
-	Hiring decisions
-	Candidate ranking
-	Resume rewriting
-	Skill inference
-	ATS simulation
________________________________________
## Project philosophy
This project prioritizes:
-	Transparency over cleverness
-	Inspectability over inference
-	Explicit limitations over optimistic claims

Every metric, transformation, and output can be traced back to visible text and simple math.

## Possible Next Steps

- Tiered weighting: prioritize skills vs responsibilities in gap scoring
- Section-aware analysis (skills, experience, certifications)
- Multi-job comparisons for benchmarking
from src.analysis import GapConfidence


def explain_gap(term: str, confidence: GapConfidence) -> str:
    if confidence == GapConfidence.STRONG_MATCH:
        return "Explicitly mentioned in the resume."

    if confidence == GapConfidence.PARTIAL_EVIDENCE:
        return "Related terms or experience detected, but not explicitly stated."

    if confidence == GapConfidence.MISSING:
        return "Emphasized in the job description but not evidenced in the resume."

    return ""

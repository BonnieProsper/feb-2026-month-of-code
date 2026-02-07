import re
from dataclasses import dataclass
from typing import List, Set


DEFAULT_STOPWORDS: Set[str] = {
    "the", "and", "or", "with", "to", "of", "in", "for", "on", "at", "by"
}


@dataclass
class PreprocessResult:
    tokens: List[str]
    token_count: int
    dropped_token_count: int


def preprocess_text(
    text: str,
    stopwords: Set[str] = DEFAULT_STOPWORDS,
) -> PreprocessResult:
    if not text:
        return PreprocessResult(tokens=[], token_count=0, dropped_token_count=0)

    # Normalize case
    lowered = text.lower()

    # Replace punctuation with whitespace
    # This is intentionally blunt and documented as lossy
    normalized = re.sub(r"[^a-z0-9\s]", " ", lowered)

    raw_tokens = normalized.split()

    tokens: List[str] = []
    dropped = 0

    for tok in raw_tokens:
        if len(tok) < 2:
            dropped += 1
            continue

        if tok in stopwords:
            dropped += 1
            continue

        tokens.append(tok)

    return PreprocessResult(
        tokens=tokens,
        token_count=len(tokens),
        dropped_token_count=dropped,
    )

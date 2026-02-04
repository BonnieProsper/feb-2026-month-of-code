# src/types.py

from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass(frozen=True)
class ParsedTemplate:
    headers: Dict[str, str]  # e.g., {"Subject": "...", "From": "..."}
    body: str
    placeholders: Set[str]


@dataclass(frozen=True)
class SkippedProspect:
    index: int
    prospect: Dict[str, str]
    reason: str


@dataclass(frozen=True)
class ValidationResult:
    valid_prospects: List[Dict[str, str]]
    skipped_prospects: List[SkippedProspect]

    @property
    def rendered_count(self) -> int:
        return len(self.valid_prospects)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_prospects)

    @property
    def total_count(self) -> int:
        return self.rendered_count + self.skipped_count

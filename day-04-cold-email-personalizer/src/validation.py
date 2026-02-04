# src/validation.py

from typing import List, Dict, Set
import difflib

from src.errors import ValidationError
from src.types import ValidationResult, SkippedProspect


def validate_prospects(
    prospects: List[Dict[str, str]],
    required_fields: Set[str],
) -> ValidationResult:
    """
    Validate prospects with partial success support.

    - Invalid rows are skipped with a reason.
    - do_not_contact=true rows are skipped automatically.
    - Validation is strict per row, but never aborts the entire run.

    Returns a ValidationResult containing valid and skipped prospects.
    """
    if not prospects:
        raise ValidationError("No prospects provided for validation.")

    valid: List[Dict[str, str]] = []
    skipped: List[SkippedProspect] = []

    for index, prospect in enumerate(prospects, start=1):
        # Compliance: do not contact
        if _is_do_not_contact(prospect):
            skipped.append(
                SkippedProspect(
                    index=index,
                    prospect=prospect,
                    reason="do_not_contact flag is set",
                )
            )
            continue

        try:
            _validate_required_fields(
                prospect=prospect,
                required_fields=required_fields,
                index=index,
            )
        except ValidationError as exc:
            skipped.append(
                SkippedProspect(
                    index=index,
                    prospect=prospect,
                    reason=str(exc),
                )
            )
            continue

        valid.append(prospect)

    return ValidationResult(
        valid_prospects=valid,
        skipped_prospects=skipped,
    )


def _validate_required_fields(
    prospect: Dict[str, str],
    required_fields: Set[str],
    index: int,
) -> None:
    for field in required_fields:
        value = prospect.get(field)

        if value is None or not value.strip():
            identifier = _describe_prospect(prospect, index)
            suggestion = _suggest_field_name(field, set(prospect.keys()))

            message = f'Missing required field "{field}" for {identifier}.'
            if suggestion:
                message += f' Did you mean "{suggestion}"?'

            raise ValidationError(message)


def _is_do_not_contact(prospect: Dict[str, str]) -> bool:
    value = prospect.get("do_not_contact", "")
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _suggest_field_name(
    missing_field: str,
    available_fields: Set[str],
) -> str | None:
    matches = difflib.get_close_matches(
        missing_field,
        available_fields,
        n=1,
        cutoff=0.8,
    )
    return matches[0] if matches else None


def _describe_prospect(prospect: Dict[str, str], index: int) -> str:
    if prospect.get("company", "").strip():
        return f'prospect #{index} (company={prospect["company"]})'

    if prospect.get("first_name", "").strip():
        return f'prospect #{index} (first_name={prospect["first_name"]})'

    return f"prospect #{index}"

from typing import List, Dict, Set

from src.errors import ValidationError

def validate_prospects(
    prospects: List[Dict[str, str]],
    required_fields: Set[str],
) -> None:
    """
    Ensure that each prospect contains all required fields
    with non-empty values.

    Raises ValidationError on the first failure encountered.
    """
    if not prospects:
        raise ValidationError("No prospects provided for validation.")

    for index, prospect in enumerate(prospects, start=1):
        for field in required_fields:
            value = prospect.get(field)

            if value is None or not value.strip():
                identifier = _describe_prospect(prospect, index)
                raise ValidationError(
                    f'Missing required field "{field}" for {identifier}.'
                )


def _describe_prospect(prospect: Dict[str, str], index: int) -> str:
    """
    Return a human-readable identifier for a prospect.
    """
    if "company" in prospect and prospect["company"].strip():
        return f'prospect #{index} (company={prospect["company"]})'

    if "first_name" in prospect and prospect["first_name"].strip():
        return f'prospect #{index} (first_name={prospect["first_name"]})'

    return f"prospect #{index}"

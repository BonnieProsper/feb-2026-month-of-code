import re
from typing import Set, Dict, Iterable

from src.errors import TemplateError

# Strict placeholder format: {{field_name}}
_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z0-9_]+)\}\}")


def extract_placeholders(template: str) -> Set[str]:
    """
    Return all unique placeholder names required by the template.

    Placeholders follow the format: {{field_name}}
    """
    if not template:
        return set()

    return set(_PLACEHOLDER_PATTERN.findall(template))


def lint_template(
    template: str,
    known_fields: Iterable[str],
) -> list[str]:
    """
    Return warnings about template issues.
    Does not raise.
    """
    warnings: list[str] = []

    placeholders = extract_placeholders(template)
    known = set(known_fields)

    unknown = placeholders - known
    if unknown:
        warnings.append(
            f"Template contains unknown placeholders: {sorted(unknown)}"
        )

    return warnings


def render_template(
    template: str,
    context: Dict[str, str],
    required_placeholders: Set[str],
) -> str:
    """
    Render a template with partial rendering support.

    Missing required placeholders raise TemplateError.
    Missing optional placeholders render as empty strings.
    """
    rendered = template

    for placeholder in required_placeholders:
        if not context.get(placeholder):
            raise TemplateError(
                f'Missing required placeholder "{placeholder}".'
            )

    for key in required_placeholders:
        rendered = rendered.replace(
            f"{{{{{key}}}}}",
            context.get(key, ""),
        )

    return rendered
import re
from typing import Set, Dict

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


def render_template(template: str, context: Dict[str, str]) -> str:
    """
    Render the template using values from context.

    Assumes all required placeholders exist in context.
    Validation is handled elsewhere.
    """
    rendered = template

    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    return rendered

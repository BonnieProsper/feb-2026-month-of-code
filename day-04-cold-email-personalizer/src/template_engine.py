import re
import difflib
from typing import Set, Dict

from src.errors import TemplateError
from src.types import ParsedTemplate

# Strict placeholder format: {{field_name}}
_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z0-9_]+)\}\}")

# Frontmatter format: Key: Value (top of file, before first blank line)
_FRONTMATTER_PATTERN = re.compile(r"^([A-Za-z-]+):\s*(.+)$")


def extract_placeholders(text: str) -> Set[str]:
    """
    Return all unique placeholder names found in text.
    """
    if not text:
        return set()

    return set(_PLACEHOLDER_PATTERN.findall(text))


def parse_template(template: str) -> ParsedTemplate:
    """
    Parse a template into headers, body, and placeholders.

    Frontmatter is optional and consists of `Key: Value` lines
    at the top of the file, terminated by the first blank line
    or first non-header line.
    """
    lines = template.splitlines()
    headers: Dict[str, str] = {}
    body_lines: list[str] = []

    in_frontmatter = True

    for line in lines:
        if in_frontmatter:
            if not line.strip():
                in_frontmatter = False
                continue

            match = _FRONTMATTER_PATTERN.match(line)
            if match:
                key, value = match.group(1), match.group(2).strip()
                headers[key] = value
                continue

            # Non-header line ends frontmatter
            in_frontmatter = False

        body_lines.append(line)

    body = "\n".join(body_lines).strip()
    placeholders = extract_placeholders(body)

    return ParsedTemplate(
        headers=headers,
        body=body,
        placeholders=placeholders,
    )


def render_template(
    template: str,
    context: Dict[str, str],
    required_placeholders: Set[str],
) -> str:
    """
    Render a template using the provided context.

    - Missing required placeholders raise TemplateError
    - Optional placeholders render as empty strings
    - Headers are re-attached above the rendered body
    """
    parsed = parse_template(template)
    rendered_body = parsed.body

    for placeholder in required_placeholders:
        if not context.get(placeholder):
            suggestion = _suggest_field_name(
                placeholder,
                set(context.keys()),
            )
            message = f'Missing required placeholder "{placeholder}".'
            if suggestion:
                message += f' Did you mean "{suggestion}"?'
            raise TemplateError(message)

    for placeholder in parsed.placeholders:
        rendered_body = rendered_body.replace(
            f"{{{{{placeholder}}}}}",
            context.get(placeholder, ""),
        )

    if parsed.headers:
        header_block = "\n".join(f"{k}: {v}" for k, v in parsed.headers.items())
        return f"{header_block}\n\n{rendered_body}"

    return rendered_body


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

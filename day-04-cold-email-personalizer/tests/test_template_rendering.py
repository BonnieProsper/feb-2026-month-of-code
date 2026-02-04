# tests/test_template_rendering.py

import pytest

from src.template_engine import extract_placeholders, render_template
from src.errors import TemplateError


def test_extracts_unique_placeholders():
    template = (
        "Hi {{first_name}},\n\n"
        "I saw that {{company}} recently {{recent_event}}.\n"
        "Best,\n"
        "{{first_name}}"
    )

    placeholders = extract_placeholders(template)

    assert placeholders == {"first_name", "company", "recent_event"}


def test_extracts_no_placeholders_from_static_template():
    template = "Hello,\nThis is a static email.\nRegards."

    placeholders = extract_placeholders(template)

    assert placeholders == set()


def test_renders_template_with_context():
    template = (
        "Hi {{first_name}},\n\n"
        "Congrats to {{company}} on {{recent_event}}."
    )

    context = {
        "first_name": "Sam",
        "company": "Manning",
        "recent_event": "launching a new platform",
    }

    placeholders = extract_placeholders(template)

    rendered = render_template(
        template,
        context,
        required_placeholders=placeholders,
    )

    assert rendered == (
        "Hi Sam,\n\n"
        "Congrats to Manning on launching a new platform."
    )


def test_renders_repeated_placeholders():
    template = "{{first_name}} from {{company}} — thanks {{first_name}}."

    context = {
        "first_name": "Jordan",
        "company": "Manning",
    }

    placeholders = extract_placeholders(template)

    rendered = render_template(
        template,
        context,
        required_placeholders=placeholders,
    )

    assert rendered == "Jordan from Manning — thanks Jordan."


def test_missing_required_placeholder_raises():
    template = "Hi {{first_name}} from {{company}}"

    context = {"first_name": "Sam"}

    placeholders = extract_placeholders(template)

    with pytest.raises(TemplateError):
        render_template(
            template,
            context,
            required_placeholders=placeholders,
        )

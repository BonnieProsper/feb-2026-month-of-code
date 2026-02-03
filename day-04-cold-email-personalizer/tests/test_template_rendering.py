# tests/test_template_rendering.py

from src.template_engine import extract_placeholders, render_template


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

    rendered = render_template(template, context)

    assert "Sam" in rendered
    assert "Manning" in rendered
    assert "launching a new platform" in rendered


def test_renders_repeated_placeholders():
    template = "{{first_name}} from {{company}} — thanks {{first_name}}."

    context = {
        "first_name": "Jordan",
        "company": "Manning",
    }

    rendered = render_template(template, context)

    assert rendered == "Jordan from Manning — thanks Jordan."

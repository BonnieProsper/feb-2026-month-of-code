# tests/test_renderer.py

from pathlib import Path

from src.renderer import render_outputs
from src.types import ParsedTemplate


def _get_run_dir(output_dir: Path) -> Path:
    runs = list(output_dir.iterdir())
    assert len(runs) == 1
    return runs[0]


def _template(body: str) -> ParsedTemplate:
    return ParsedTemplate(
        headers={},
        body=body,
        placeholders=set(),
    )


def test_renders_individual_files(tmp_path: Path):
    parsed_templates = [
        _template("Email for Sam"),
        _template("Email for Jordan"),
    ]

    prospects = [
        {"first_name": "Sam", "company": "Manning"},
        {"first_name": "Jordan", "company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"

    render_outputs(
        parsed_templates=parsed_templates,
        prospects=prospects,
        output_dir=str(output_dir),
    )

    run_dir = _get_run_dir(output_dir)
    filenames = sorted(f.name for f in run_dir.iterdir())

    assert filenames == [
        "jordan_manning.txt",
        "sam_manning.txt",
    ]


def test_handles_filename_collisions(tmp_path: Path):
    parsed_templates = [
        _template("Email one"),
        _template("Email two"),
    ]

    prospects = [
        {"first_name": "Sam", "company": "Manning"},
        {"first_name": "Sam", "company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"

    render_outputs(
        parsed_templates=parsed_templates,
        prospects=prospects,
        output_dir=str(output_dir),
    )

    run_dir = _get_run_dir(output_dir)
    filenames = sorted(f.name for f in run_dir.iterdir())

    assert filenames == [
        "sam_manning.txt",
        "sam_manning_2.txt",
    ]


def test_writes_combined_output(tmp_path: Path):
    parsed_templates = [
        _template("Email for Sam"),
        _template("Email for Jordan"),
    ]

    prospects = [
        {"company": "Manning"},
        {"company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"
    combined_file = tmp_path / "combined.txt"

    render_outputs(
        parsed_templates=parsed_templates,
        prospects=prospects,
        output_dir=str(output_dir),
        combined_output_path=str(combined_file),
    )

    content = combined_file.read_text()

    assert "prospect #1" in content
    assert "Email for Sam" in content
    assert "Email for Jordan" in content

# tests/test_renderer.py

from pathlib import Path

from src.renderer import render_outputs


def test_renders_individual_files(tmp_path: Path):
    rendered = [
        "Email for Sam",
        "Email for Jordan",
    ]

    prospects = [
        {"first_name": "Sam", "company": "Manning"},
        {"first_name": "Jordan", "company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"

    render_outputs(rendered, prospects, str(output_dir))

    files = list(output_dir.iterdir())
    filenames = sorted(f.name for f in files)

    assert filenames == [
        "jordan_manning.txt",
        "sam_manning.txt",
    ]


def test_handles_filename_collisions(tmp_path: Path):
    rendered = [
        "Email one",
        "Email two",
    ]

    prospects = [
        {"first_name": "Sam", "company": "Manning"},
        {"first_name": "Sam", "company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"

    render_outputs(rendered, prospects, str(output_dir))

    filenames = sorted(f.name for f in output_dir.iterdir())

    assert filenames == [
        "sam_manning.txt",
        "sam_manning_2.txt",
    ]


def test_writes_combined_output(tmp_path: Path):
    rendered = [
        "Email for Sam",
        "Email for Jordan",
    ]

    prospects = [
        {"company": "Manning"},
        {"company": "Manning"},
    ]

    output_dir = tmp_path / "outputs"
    combined_file = tmp_path / "combined.txt"

    render_outputs(
        rendered,
        prospects,
        str(output_dir),
        combined_output_path=str(combined_file),
    )

    content = combined_file.read_text()

    assert "prospect #1" in content
    assert "Email for Sam" in content
    assert "Email for Jordan" in content

"""Tests for project spec extraction."""

from pathlib import Path

from prisme.migration.project_extractor import extract_project_spec


def test_extract_basic() -> None:
    content = extract_project_spec({"database": '"postgresql"'}, project_name="my-app")
    assert "ProjectSpec" in content
    assert "my-app" in content
    assert "postgresql" in content


def test_extract_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "specs" / "project.py"
    extract_project_spec({}, project_name="test", write_path=out)
    assert out.exists()
    assert "ProjectSpec" in out.read_text()


def test_extract_empty_fields() -> None:
    content = extract_project_spec({})
    assert "ProjectSpec" in content

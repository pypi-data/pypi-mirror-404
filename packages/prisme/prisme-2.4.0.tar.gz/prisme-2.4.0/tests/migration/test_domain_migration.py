"""Tests for domain spec v1→v2 migration."""

from pathlib import Path

from prisme.migration.domain_v1_to_v2 import migrate_domain_v1_to_v2


def test_migrate_removes_infra_fields(tmp_path: Path) -> None:
    spec_file = tmp_path / "models.py"
    spec_file.write_text(
        """from prism.spec.stack import StackSpec

stack = StackSpec(
    name="test",
    database="postgresql",
    auth_enabled=True,
    models=[],
)
"""
    )

    result = migrate_domain_v1_to_v2(spec_file)

    assert (
        "database" not in result.new_domain_content or "database=" not in result.new_domain_content
    )
    assert "database" in result.extracted_project_fields
    assert any("database" in c for c in result.changes)


def test_migrate_updates_imports(tmp_path: Path) -> None:
    spec_file = tmp_path / "models.py"
    spec_file.write_text(
        """from prism.spec.stack import StackSpec

stack = StackSpec(
    name="test",
    models=[],
)
"""
    )

    result = migrate_domain_v1_to_v2(spec_file)
    assert "from prisme.spec.stack" in result.new_domain_content


def test_migrate_dry_run_does_not_write(tmp_path: Path) -> None:
    spec_file = tmp_path / "models.py"
    original = 'from prism.spec.stack import StackSpec\nstack = StackSpec(name="t", database="sqlite", models=[])\n'
    spec_file.write_text(original)

    migrate_domain_v1_to_v2(spec_file, write=False)
    assert spec_file.read_text() == original


def test_migrate_write_updates_file(tmp_path: Path) -> None:
    spec_file = tmp_path / "models.py"
    spec_file.write_text(
        'from prism.spec.stack import StackSpec\nstack = StackSpec(name="t", database="sqlite", models=[])\n'
    )

    migrate_domain_v1_to_v2(spec_file, write=True)
    content = spec_file.read_text()
    assert "from prisme" in content


def test_migrate_already_v2(tmp_path: Path) -> None:
    spec_file = tmp_path / "models.py"
    spec_file.write_text(
        'from prisme.spec.stack import StackSpec\nstack = StackSpec(name="t", models=[])\n'
    )

    result = migrate_domain_v1_to_v2(spec_file)
    assert any("already be v2" in w for w in result.warnings)

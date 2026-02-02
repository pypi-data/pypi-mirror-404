"""Tests for the prisme doctor command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from prisme.cli import main
from prisme.tracking.manifest import (
    FileManifest,
    ManifestManager,
    TrackedFile,
    hash_content,
)


def _write_minimal_project(root: Path) -> None:
    """Write the minimum files for a valid prisme project."""
    specs_dir = root / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    (specs_dir / "models.py").write_text('''"""Test spec."""
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.stack import StackSpec

stack = StackSpec(
    name="test-project",
    version="1.0.0",
    models=[
        ModelSpec(
            name="User",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        ),
    ],
)
''')

    (root / "prisme.toml").write_text(
        'prisme_version = "0.12.1"\nconfig_version = 1\n\n[project]\nspec_path = "specs/models.py"\n'
    )


class TestDoctorCommand:
    """Tests for the doctor command."""

    def test_doctor_healthy_project(self, tmp_path: Path) -> None:
        """Doctor passes for a healthy project."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            result = runner.invoke(main, ["doctor"])

            assert "Prism Doctor" in result.output
            assert "\u2713" in result.output  # checkmark
            assert "prisme.toml is valid" in result.output
            assert "Domain spec loaded" in result.output

    def test_doctor_missing_toml(self, tmp_path: Path) -> None:
        """Doctor reports missing prisme.toml."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["doctor"])

            assert result.exit_code != 0
            assert "prisme.toml not found" in result.output

    def test_doctor_missing_spec(self, tmp_path: Path) -> None:
        """Doctor reports missing domain spec."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            Path(td, "prisme.toml").write_text(
                'prisme_version = "0.12.1"\nconfig_version = 1\n\n[project]\nspec_path = "specs/models.py"\n'
            )

            result = runner.invoke(main, ["doctor"])

            assert result.exit_code != 0
            assert "not found" in result.output

    def test_doctor_detects_edited_always_overwrite(self, tmp_path: Path) -> None:
        """Doctor warns about manually edited ALWAYS_OVERWRITE files."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # Create a manifest with a tracked file
            content = "# generated content"
            file_path = td_path / "packages" / "backend" / "test.py"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content + "\n# user edit")

            manifest = FileManifest()
            manifest.track_file(
                TrackedFile(
                    path="packages/backend/test.py",
                    strategy="always_overwrite",
                    content_hash=hash_content(content),
                    generated_at="2026-01-01T00:00:00",
                )
            )
            ManifestManager.save(manifest, td_path)

            result = runner.invoke(main, ["doctor"])

            assert "manually edited" in result.output

    def test_doctor_no_manifest_warns(self, tmp_path: Path) -> None:
        """Doctor warns when no manifest exists."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            result = runner.invoke(main, ["doctor"])

            assert "No manifest found" in result.output

    def test_doctor_shows_summary(self, tmp_path: Path) -> None:
        """Doctor shows a summary of checks."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            result = runner.invoke(main, ["doctor"])

            assert "checks:" in result.output
            assert "passed" in result.output

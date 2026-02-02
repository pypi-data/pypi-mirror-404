"""Tests for manifest integration with the generate command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from prisme.cli import main
from prisme.tracking.manifest import ManifestManager


def _write_minimal_project(root: Path, spec_content: str | None = None) -> None:
    """Write the minimum files for a valid prisme project."""
    specs_dir = root / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    if spec_content is None:
        spec_content = '''"""Test spec."""
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
                FieldSpec(name="email", type=FieldType.STRING, unique=True),
            ],
        ),
    ],
)
'''
    (specs_dir / "models.py").write_text(spec_content)

    # Write prisme.toml
    (root / "prisme.toml").write_text(
        'prisme_version = "0.12.1"\nconfig_version = 1\n\n[project]\nspec_path = "specs/models.py"\n'
    )


class TestManifestIntegration:
    """Tests for manifest being written after generate."""

    def test_manifest_written_after_generate(self, tmp_path: Path) -> None:
        """Manifest file is created after successful generation."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            result = runner.invoke(main, ["generate"])

            assert result.exit_code == 0, f"Generate failed: {result.output}"

            manifest_path = Path(td) / ".prisme" / "manifest.json"
            assert manifest_path.exists(), "Manifest file should be created"

            data = json.loads(manifest_path.read_text())
            assert "files" in data
            assert "generated_at" in data
            assert "generators_enabled" in data
            assert len(data["generators_enabled"]) > 0

    def test_manifest_contains_v2_fields(self, tmp_path: Path) -> None:
        """Manifest includes v2 metadata fields."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            runner.invoke(main, ["generate"])

            manifest = ManifestManager.load(Path(td))
            assert manifest.domain_hash != ""
            assert manifest.domain_version is not None
            assert manifest.config_hash != ""

    def test_manifest_tracks_generated_files(self, tmp_path: Path) -> None:
        """Manifest tracks all generated files with hashes."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            runner.invoke(main, ["generate"])

            manifest = ManifestManager.load(Path(td))
            assert len(manifest.files) > 0

            # Each tracked file should have a content hash and strategy
            for path, tracked in manifest.files.items():
                assert tracked.content_hash, f"File {path} missing content_hash"
                assert tracked.strategy, f"File {path} missing strategy"

    def test_manifest_not_written_in_dry_run(self, tmp_path: Path) -> None:
        """Manifest is not written in dry-run mode."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            _write_minimal_project(Path(td))

            runner.invoke(main, ["generate", "--dry-run"])

            manifest_path = Path(td) / ".prisme" / "manifest.json"
            assert not manifest_path.exists()

    def test_always_overwrite_edit_warning(self, tmp_path: Path) -> None:
        """Warning is printed when overwriting a manually edited ALWAYS_OVERWRITE file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # First generate
            result1 = runner.invoke(main, ["generate"])
            assert result1.exit_code == 0

            # Find an ALWAYS_OVERWRITE file from the manifest
            manifest = ManifestManager.load(td_path)
            ao_file = None
            for path, tracked in manifest.files.items():
                if tracked.strategy == "always_overwrite":
                    full_path = td_path / path
                    if full_path.exists():
                        ao_file = full_path
                        break

            if ao_file is None:
                # Skip if no always_overwrite files were generated
                return

            # Manually edit it
            ao_file.write_text(ao_file.read_text() + "\n# manually edited")

            # Regenerate — should see warning
            result2 = runner.invoke(main, ["generate"])
            assert result2.exit_code == 0
            assert "manually edited" in result2.output or "overwriting" in result2.output

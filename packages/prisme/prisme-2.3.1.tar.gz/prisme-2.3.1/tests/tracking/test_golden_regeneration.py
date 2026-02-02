"""Golden regeneration tests for file strategy behavior and determinism."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from prisme.cli import main
from prisme.tracking.manifest import ManifestManager


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
                FieldSpec(name="email", type=FieldType.STRING, unique=True),
            ],
        ),
        ModelSpec(
            name="Post",
            fields=[
                FieldSpec(name="title", type=FieldType.STRING, required=True),
                FieldSpec(name="content", type=FieldType.TEXT),
            ],
        ),
    ],
)
''')

    (root / "prisme.toml").write_text(
        'prisme_version = "0.12.1"\nconfig_version = 1\n\n[project]\nspec_path = "specs/models.py"\n'
    )


def _snapshot_files(root: Path) -> dict[str, str]:
    """Snapshot all non-hidden, non-spec files in the project."""
    files = {}
    for p in root.rglob("*"):
        if (
            p.is_file()
            and ".prisme" not in p.parts
            and "specs" not in p.parts
            and p.name != "prisme.toml"
        ):
            rel = str(p.relative_to(root))
            files[rel] = p.read_text()
    return files


class TestGoldenRegeneration:
    """Golden tests for file strategy behavior."""

    def test_generate_once_file_preserved_on_regen(self, tmp_path: Path) -> None:
        """GENERATE_ONCE files are not overwritten on regeneration."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # First generate
            result1 = runner.invoke(main, ["generate"])
            assert result1.exit_code == 0

            # Find a GENERATE_ONCE file
            manifest = ManifestManager.load(td_path)
            go_file = None
            for path_str, tracked in manifest.files.items():
                if tracked.strategy == "generate_once":
                    full = td_path / path_str
                    if full.exists():
                        go_file = full
                        break

            if go_file is None:
                # No generate_once files, skip
                return

            # Edit the file
            original = go_file.read_text()
            edited = original + "\n# user customization"
            go_file.write_text(edited)

            # Regenerate
            result2 = runner.invoke(main, ["generate"])
            assert result2.exit_code == 0

            # File should still contain our edit
            assert go_file.read_text() == edited

    def test_always_overwrite_file_restored_on_regen(self, tmp_path: Path) -> None:
        """ALWAYS_OVERWRITE files are restored on regeneration."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # First generate
            result1 = runner.invoke(main, ["generate"])
            assert result1.exit_code == 0

            # Find an ALWAYS_OVERWRITE file
            manifest = ManifestManager.load(td_path)
            ao_file = None
            for path_str, tracked in manifest.files.items():
                if tracked.strategy == "always_overwrite":
                    full = td_path / path_str
                    if full.exists():
                        ao_file = full
                        break

            if ao_file is None:
                return

            # Edit the file
            original = ao_file.read_text()
            ao_file.write_text(original + "\n# should be removed")

            # Regenerate
            result2 = runner.invoke(main, ["generate"])
            assert result2.exit_code == 0

            # File should be restored to generated content
            assert ao_file.read_text() == original

    def test_deterministic_generation(self, tmp_path: Path) -> None:
        """Two consecutive generates produce identical file content."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # First generate
            result1 = runner.invoke(main, ["generate"])
            assert result1.exit_code == 0
            snapshot1 = _snapshot_files(td_path)

            # Second generate (should overwrite ALWAYS_OVERWRITE identically)
            result2 = runner.invoke(main, ["generate"])
            assert result2.exit_code == 0
            snapshot2 = _snapshot_files(td_path)

            # All files should be identical
            assert set(snapshot1.keys()) == set(snapshot2.keys()), (
                f"File sets differ: added={set(snapshot2) - set(snapshot1)}, "
                f"removed={set(snapshot1) - set(snapshot2)}"
            )
            for path in snapshot1:
                assert snapshot1[path] == snapshot2[path], (
                    f"File {path} differs between generations"
                )

    def test_spec_change_only_affects_always_overwrite(self, tmp_path: Path) -> None:
        """Changing domain spec only changes ALWAYS_OVERWRITE files."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)
            _write_minimal_project(td_path)

            # First generate
            result1 = runner.invoke(main, ["generate"])
            assert result1.exit_code == 0

            # Get GENERATE_ONCE files snapshot
            manifest = ManifestManager.load(td_path)
            go_files_before: dict[str, str] = {}
            for path_str, tracked in manifest.files.items():
                if tracked.strategy == "generate_once":
                    full = td_path / path_str
                    if full.exists():
                        go_files_before[path_str] = full.read_text()

            # Change the spec (add a field)
            (td_path / "specs" / "models.py").write_text('''"""Test spec."""
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
                FieldSpec(name="age", type=FieldType.INTEGER),
            ],
        ),
        ModelSpec(
            name="Post",
            fields=[
                FieldSpec(name="title", type=FieldType.STRING, required=True),
                FieldSpec(name="content", type=FieldType.TEXT),
            ],
        ),
    ],
)
''')

            # Regenerate
            result2 = runner.invoke(main, ["generate"])
            assert result2.exit_code == 0

            # GENERATE_ONCE files should be unchanged
            for path_str, content_before in go_files_before.items():
                full = td_path / path_str
                if full.exists():
                    assert full.read_text() == content_before, (
                        f"GENERATE_ONCE file {path_str} was changed after spec update"
                    )

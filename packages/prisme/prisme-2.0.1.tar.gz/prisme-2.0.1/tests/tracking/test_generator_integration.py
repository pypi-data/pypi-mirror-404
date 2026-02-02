"""Tests for generator integration with file tracking."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import (
    GeneratedFile,
    GeneratorBase,
    GeneratorContext,
)
from prisme.spec.stack import FileStrategy, StackSpec
from prisme.tracking.manifest import ManifestManager, hash_content


class SimpleGenerator(GeneratorBase):
    """Simple test generator."""

    def generate_files(self) -> list[GeneratedFile]:
        """Generate a test file."""
        return [
            GeneratedFile(
                path=Path("test_file.py"),
                content="# Generated content",
                strategy=FileStrategy.GENERATE_ONCE,
                description="Test file",
            )
        ]


def test_generator_tracks_new_file(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test that generator tracks newly generated files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    generator = SimpleGenerator(context)
    result = generator.generate()

    assert result.written == 1
    assert result.skipped == 0

    # Check manifest was created and file is tracked
    manifest = ManifestManager.load(output_dir)
    tracked = manifest.get_file("test_file.py")

    assert tracked is not None
    assert tracked.strategy == FileStrategy.GENERATE_ONCE.value
    assert tracked.content_hash == hash_content("# Generated content")


def test_generator_respects_user_modifications(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test that generator doesn't overwrite user-modified files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # First generation
    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    generator = SimpleGenerator(context)
    result1 = generator.generate()

    assert result1.written == 1
    file_path = output_dir / "test_file.py"
    assert file_path.exists()

    # User modifies the file
    user_content = "# User's custom code"
    file_path.write_text(user_content)

    # Second generation with different content
    class ModifiedGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("test_file.py"),
                    content="# New generated content",
                    strategy=FileStrategy.GENERATE_ONCE,
                )
            ]

    generator2 = ModifiedGenerator(context)
    result2 = generator2.generate()

    # File should be skipped (user modification detected)
    assert result2.written == 0
    assert result2.skipped == 1

    # User's content should be preserved
    assert file_path.read_text() == user_content


def test_generator_always_overwrite_ignores_modifications(
    tmp_path: Path,
    sample_stack_spec: StackSpec,
):
    """Test that ALWAYS_OVERWRITE strategy overwrites user changes."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # First generation
    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    class OverwriteGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("models.py"),
                    content="# Original models",
                    strategy=FileStrategy.ALWAYS_OVERWRITE,
                )
            ]

    generator1 = OverwriteGenerator(context)
    result1 = generator1.generate()

    assert result1.written == 1
    file_path = output_dir / "models.py"

    # User modifies the file
    file_path.write_text("# User's modified models")

    # Second generation with ALWAYS_OVERWRITE
    class UpdatedGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("models.py"),
                    content="# Updated models",
                    strategy=FileStrategy.ALWAYS_OVERWRITE,
                )
            ]

    generator2 = UpdatedGenerator(context)
    result2 = generator2.generate()

    # File should be overwritten
    assert result2.written == 1
    assert result2.skipped == 0
    assert file_path.read_text() == "# Updated models"


def test_generator_force_flag_overwrites_everything(
    tmp_path: Path,
    sample_stack_spec: StackSpec,
):
    """Test that force flag overwrites all files regardless of strategy."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # First generation
    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    generator1 = SimpleGenerator(context)
    result1 = generator1.generate()

    assert result1.written == 1
    file_path = output_dir / "test_file.py"

    # User modifies the file
    file_path.write_text("# User's code")

    # Second generation with force=True
    context_force = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
        force=True,
    )

    generator2 = SimpleGenerator(context_force)
    result2 = generator2.generate()

    # File should be overwritten due to force flag
    assert result2.written == 1
    assert result2.skipped == 0
    assert file_path.read_text() == "# Generated content"


def test_generator_tracks_file_metadata(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test that generator tracks extended file metadata."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    class ExtendedGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("services/user.py"),
                    content="class UserService:\n    pass",
                    strategy=FileStrategy.GENERATE_ONCE,
                    has_hooks=True,
                    extends=Path("services/_base/user_base.py"),
                )
            ]

    generator = ExtendedGenerator(context)
    result = generator.generate()

    assert result.written == 1

    # Check manifest includes extended metadata
    manifest = ManifestManager.load(output_dir)
    tracked = manifest.get_file("services/user.py")

    assert tracked is not None
    assert tracked.has_hooks is True
    assert tracked.extends == "services/_base/user_base.py"


def test_generator_dry_run_does_not_track(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test that dry_run mode doesn't track files in manifest."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
        dry_run=True,
    )

    generator = SimpleGenerator(context)
    result = generator.generate()

    # Files should be "written" (returned True) but not tracked
    assert result.written == 1

    # Manifest should be empty (no files tracked in dry_run)
    manifest = ManifestManager.load(output_dir)
    assert len(manifest.files) == 0


def test_generator_handles_unmodified_regeneration(
    tmp_path: Path,
    sample_stack_spec: StackSpec,
):
    """Test that regenerating without user changes works correctly."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    # First generation
    generator1 = SimpleGenerator(context)
    result1 = generator1.generate()

    assert result1.written == 1

    # Second generation without user changes (content unchanged)
    generator2 = SimpleGenerator(context)
    result2 = generator2.generate()

    # With GENERATE_ONCE, file should be skipped (already exists)
    # even though user hasn't modified it
    assert result2.written == 0
    assert result2.skipped == 1


def test_manifest_persists_across_generations(
    tmp_path: Path,
    sample_stack_spec: StackSpec,
):
    """Test that manifest data persists across multiple generation runs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    # First generation - file A
    class GeneratorA(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("file_a.py"),
                    content="# File A",
                    strategy=FileStrategy.GENERATE_ONCE,
                )
            ]

    gen_a = GeneratorA(context)
    gen_a.generate()

    # Check manifest has file A
    manifest1 = ManifestManager.load(output_dir)
    assert len(manifest1.files) == 1
    assert "file_a.py" in manifest1.files

    # Second generation - file B
    class GeneratorB(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("file_b.py"),
                    content="# File B",
                    strategy=FileStrategy.GENERATE_ONCE,
                )
            ]

    gen_b = GeneratorB(context)
    gen_b.generate()

    # Check manifest now has both files
    manifest2 = ManifestManager.load(output_dir)
    assert len(manifest2.files) == 2
    assert "file_a.py" in manifest2.files
    assert "file_b.py" in manifest2.files

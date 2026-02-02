"""End-to-end tests for the complete safe regeneration workflow."""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import (
    GeneratedFile,
    GeneratorBase,
    GeneratorContext,
)
from prisme.spec.stack import FileStrategy, StackSpec
from prisme.tracking.logger import OverrideLogger
from prisme.tracking.manifest import ManifestManager


class ServiceGenerator(GeneratorBase):
    """Generator that simulates service generation."""

    def generate_files(self) -> list[GeneratedFile]:
        """Generate test service files."""
        return [
            GeneratedFile(
                path=Path("backend/services/user.py"),
                content=self._get_service_content(),
                strategy=FileStrategy.GENERATE_ONCE,
                has_hooks=False,
                description="User service",
            )
        ]

    def _get_service_content(self) -> str:
        """Get the generated service content."""
        return """from models import User

class UserService:
    def create(self, data):
        return db.add(User(**data.dict()))

    def get(self, id):
        return db.get(User, id)
"""


class UpdatedServiceGenerator(GeneratorBase):
    """Generator that produces updated service content."""

    def generate_files(self) -> list[GeneratedFile]:
        """Generate updated service files."""
        return [
            GeneratedFile(
                path=Path("backend/services/user.py"),
                content=self._get_updated_content(),
                strategy=FileStrategy.GENERATE_ONCE,
                has_hooks=False,
            )
        ]

    def _get_updated_content(self) -> str:
        """Get updated service content (new method added)."""
        return """from models import User

class UserService:
    def create(self, data):
        return db.add(User(**data.model_dump()))

    def get(self, id):
        return db.get(User, id)

    def delete(self, id):
        # New method from spec
        return db.delete(User, id)
"""


def test_complete_safe_regeneration_workflow(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test the complete workflow: generate → modify → regenerate → review."""
    output_dir = tmp_path / "project"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    # === STEP 1: Initial Generation ===
    generator1 = ServiceGenerator(context)
    result1 = generator1.generate()

    assert result1.written == 1
    assert result1.skipped == 0
    assert result1.success

    service_file = output_dir / "backend/services/user.py"
    assert service_file.exists()

    # Verify manifest tracks the file
    manifest1 = ManifestManager.load(output_dir)
    assert len(manifest1.files) == 1
    assert "backend/services/user.py" in manifest1.files

    # No overrides yet
    override_log1 = OverrideLogger.load(output_dir)
    assert len(override_log1.overrides) == 0

    # === STEP 2: User Customizes the File ===
    user_custom_content = """from models import User
from notifications import send_welcome_email

class UserService:
    def create(self, data):
        user = User(**data.dict())
        # Custom: Send welcome email
        send_welcome_email(user.email)
        return db.add(user)

    def get(self, id):
        return db.get(User, id)

    # Custom: User added this method
    def validate_email(self, email):
        return "@" in email
"""

    service_file.write_text(user_custom_content)

    # === STEP 3: Regenerate with Updated Spec ===
    generator2 = UpdatedServiceGenerator(context)
    result2 = generator2.generate()

    # File should be skipped (user modified)
    assert result2.written == 0
    assert result2.skipped == 1

    # User's content should be preserved
    assert service_file.read_text() == user_custom_content

    # === STEP 4: Verify Override Was Logged ===
    override_log2 = OverrideLogger.load(output_dir)
    assert len(override_log2.overrides) == 1

    override = override_log2.get("backend/services/user.py")
    assert override is not None
    assert override.strategy == FileStrategy.GENERATE_ONCE.value
    assert override.reviewed is False
    assert override.diff_summary is not None

    # Check diff summary
    assert override.diff_summary["lines_added"] > 0  # User added lines

    # === STEP 5: Verify Override Files Were Created ===
    override_json = output_dir / ".prisme/overrides.json"
    override_md = output_dir / ".prisme/overrides.md"
    diff_cache = output_dir / ".prisme/diffs/backend_services_user.py.diff"

    assert override_json.exists()
    assert override_md.exists()
    assert diff_cache.exists()

    # === STEP 6: Verify Markdown Content ===
    md_content = override_md.read_text()
    assert "# Code Override Log" in md_content
    assert "backend/services/user.py" in md_content
    assert "⚠️" in md_content  # Unreviewed icon
    assert "**Unreviewed Overrides**: 1" in md_content
    assert "prisme review" in md_content

    # === STEP 7: Mark as Reviewed ===
    override_log2.mark_reviewed("backend/services/user.py")
    OverrideLogger.save(override_log2, output_dir)

    # Reload and verify
    override_log3 = OverrideLogger.load(output_dir)
    override3 = override_log3.get("backend/services/user.py")
    assert override3.reviewed is True

    # Check unreviewed count
    assert len(override_log3.get_unreviewed()) == 0

    # Markdown should now show as reviewed
    md_content2 = (output_dir / ".prisme/overrides.md").read_text()
    assert "✓" in md_content2  # Reviewed icon


def test_always_overwrite_ignores_user_changes_no_log(
    tmp_path: Path,
    sample_stack_spec: StackSpec,
):
    """Test that ALWAYS_OVERWRITE files don't log overrides."""
    output_dir = tmp_path / "project"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    # Generator with ALWAYS_OVERWRITE strategy
    class ModelsGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("backend/models/user.py"),
                    content="class User(Base):\n    pass",
                    strategy=FileStrategy.ALWAYS_OVERWRITE,
                )
            ]

    # Initial generation
    gen1 = ModelsGenerator(context)
    gen1.generate()

    model_file = output_dir / "backend/models/user.py"

    # User modifies (but shouldn't because it's ALWAYS_OVERWRITE)
    model_file.write_text("class User(Base):\n    # Custom modification\n    pass")

    # Regenerate
    gen2 = ModelsGenerator(context)
    result = gen2.generate()

    # File should be overwritten
    assert result.written == 1
    assert "# Custom modification" not in model_file.read_text()

    # No override should be logged (ALWAYS_OVERWRITE expected behavior)
    override_log = OverrideLogger.load(output_dir)
    assert len(override_log.overrides) == 0


def test_multiple_files_override_tracking(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test tracking overrides for multiple files."""
    output_dir = tmp_path / "project"
    output_dir.mkdir()

    context = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
    )

    # Generator for multiple files
    class MultiFileGenerator(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("services/user.py"),
                    content="# User service",
                    strategy=FileStrategy.GENERATE_ONCE,
                ),
                GeneratedFile(
                    path=Path("services/post.py"),
                    content="# Post service",
                    strategy=FileStrategy.GENERATE_ONCE,
                ),
                GeneratedFile(
                    path=Path("models/user.py"),
                    content="# User model",
                    strategy=FileStrategy.ALWAYS_OVERWRITE,
                ),
            ]

    # Initial generation
    gen1 = MultiFileGenerator(context)
    gen1.generate()

    # User modifies two GENERATE_ONCE files
    (output_dir / "services/user.py").write_text("# Custom user service")
    (output_dir / "services/post.py").write_text("# Custom post service")

    # User also modifies ALWAYS_OVERWRITE (will be overwritten)
    (output_dir / "models/user.py").write_text("# Custom user model")

    # Regenerate
    gen2 = MultiFileGenerator(context)
    result = gen2.generate()

    # Two files skipped (GENERATE_ONCE), one overwritten (ALWAYS_OVERWRITE)
    assert result.skipped == 2
    assert result.written == 1

    # Check override log
    override_log = OverrideLogger.load(output_dir)

    # Only the two GENERATE_ONCE files should be logged
    assert len(override_log.overrides) == 2
    assert "services/user.py" in override_log.overrides
    assert "services/post.py" in override_log.overrides
    assert "models/user.py" not in override_log.overrides


def test_dry_run_does_not_log_overrides(tmp_path: Path, sample_stack_spec: StackSpec):
    """Test that dry_run mode doesn't log overrides."""
    output_dir = tmp_path / "project"
    output_dir.mkdir()

    # Initial generation (not dry run)
    context1 = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
        dry_run=False,
    )

    class SimpleGen(GeneratorBase):
        def generate_files(self) -> list[GeneratedFile]:
            return [
                GeneratedFile(
                    path=Path("test.py"),
                    content="original",
                    strategy=FileStrategy.GENERATE_ONCE,
                )
            ]

    gen1 = SimpleGen(context1)
    gen1.generate()

    # User modifies
    (output_dir / "test.py").write_text("modified")

    # Dry run regeneration
    context2 = GeneratorContext(
        domain_spec=sample_stack_spec,
        output_dir=output_dir,
        dry_run=True,
    )

    gen2 = SimpleGen(context2)
    gen2.generate()

    # No override should be logged in dry run
    override_log = OverrideLogger.load(output_dir)
    assert len(override_log.overrides) == 0

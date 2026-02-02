"""Tests for the override logger."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prisme.spec.stack import FileStrategy
from prisme.tracking.logger import Override, OverrideLog, OverrideLogger
from prisme.tracking.manifest import hash_content

if TYPE_CHECKING:
    from pathlib import Path


def test_override_creation():
    """Test creating an Override."""
    override = Override(
        path="backend/services/user.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc123",
        user_hash="def456",
        reviewed=False,
        diff_summary={"lines_added": 5, "lines_removed": 2, "lines_changed": 3},
    )

    assert override.path == "backend/services/user.py"
    assert override.strategy == FileStrategy.GENERATE_ONCE.value
    assert override.reviewed is False
    assert override.diff_summary["lines_added"] == 5


def test_override_to_dict():
    """Test converting Override to dictionary."""
    override = Override(
        path="test.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=True,
    )

    data = override.to_dict()

    assert data["path"] == "test.py"
    assert data["strategy"] == FileStrategy.GENERATE_ONCE.value
    assert data["reviewed"] is True


def test_override_from_dict():
    """Test creating Override from dictionary."""
    data = {
        "path": "models.py",
        "strategy": FileStrategy.ALWAYS_OVERWRITE.value,
        "timestamp": "2026-01-23T10:00:00",
        "generated_hash": "ghi",
        "user_hash": "jkl",
        "reviewed": False,
        "diff_summary": {"lines_added": 1, "lines_removed": 0, "lines_changed": 0},
    }

    override = Override.from_dict(data)

    assert override.path == "models.py"
    assert override.strategy == FileStrategy.ALWAYS_OVERWRITE.value
    assert override.diff_summary["lines_added"] == 1


def test_override_log_add_override():
    """Test adding an override to the log."""
    log = OverrideLog()

    override = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
    )

    log.add_override(override)

    assert len(log.overrides) == 1
    assert "file1.py" in log.overrides


def test_override_log_mark_reviewed():
    """Test marking an override as reviewed."""
    log = OverrideLog()

    override = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=False,
    )

    log.add_override(override)
    assert not log.overrides["file1.py"].reviewed

    log.mark_reviewed("file1.py")
    assert log.overrides["file1.py"].reviewed


def test_override_log_get_unreviewed():
    """Test getting unreviewed overrides."""
    log = OverrideLog()

    override1 = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=False,
    )

    override2 = Override(
        path="file2.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="ghi",
        user_hash="jkl",
        reviewed=True,
    )

    log.add_override(override1)
    log.add_override(override2)

    unreviewed = log.get_unreviewed()

    assert len(unreviewed) == 1
    assert unreviewed[0].path == "file1.py"


def test_override_log_get_all():
    """Test getting all overrides."""
    log = OverrideLog()

    override1 = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
    )

    override2 = Override(
        path="file2.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="ghi",
        user_hash="jkl",
    )

    log.add_override(override1)
    log.add_override(override2)

    all_overrides = log.get_all()

    assert len(all_overrides) == 2


def test_override_log_remove():
    """Test removing an override from the log."""
    log = OverrideLog()

    override = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
    )

    log.add_override(override)
    assert len(log.overrides) == 1

    log.remove("file1.py")
    assert len(log.overrides) == 0


def test_override_log_clear_reviewed():
    """Test clearing reviewed overrides."""
    log = OverrideLog()

    override1 = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=True,
    )

    override2 = Override(
        path="file2.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="ghi",
        user_hash="jkl",
        reviewed=False,
    )

    log.add_override(override1)
    log.add_override(override2)

    log.clear_reviewed()

    assert len(log.overrides) == 1
    assert "file2.py" in log.overrides
    assert "file1.py" not in log.overrides


def test_override_log_to_dict():
    """Test converting override log to dictionary."""
    log = OverrideLog()

    override = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
    )

    log.add_override(override)

    data = log.to_dict()

    assert "last_updated" in data
    assert len(data["overrides"]) == 1
    assert data["overrides"][0]["path"] == "file1.py"


def test_override_log_from_dict():
    """Test creating override log from dictionary."""
    data = {
        "last_updated": "2026-01-23T12:00:00",
        "overrides": [
            {
                "path": "file1.py",
                "strategy": FileStrategy.GENERATE_ONCE.value,
                "timestamp": "2026-01-23T10:00:00",
                "generated_hash": "abc",
                "user_hash": "def",
                "reviewed": False,
                "diff_summary": None,
            }
        ],
    }

    log = OverrideLog.from_dict(data)

    assert log.last_updated == "2026-01-23T12:00:00"
    assert len(log.overrides) == 1
    assert "file1.py" in log.overrides


def test_override_logger_save_and_load(tmp_path: Path):
    """Test saving and loading override log."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    log = OverrideLog()

    override = Override(
        path="backend/services/user.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc123",
        user_hash="def456",
        diff_summary={"lines_added": 5, "lines_removed": 2, "lines_changed": 3},
    )

    log.add_override(override)

    # Save log
    OverrideLogger.save(log, project_dir)

    # Check files were created
    json_path = project_dir / ".prisme" / "overrides.json"
    md_path = project_dir / ".prisme" / "overrides.md"

    assert json_path.exists()
    assert md_path.exists()

    # Load log
    loaded = OverrideLogger.load(project_dir)

    assert len(loaded.overrides) == 1
    assert "backend/services/user.py" in loaded.overrides


def test_override_logger_load_nonexistent(tmp_path: Path):
    """Test loading override log when file doesn't exist."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()

    log = OverrideLogger.load(project_dir)

    assert isinstance(log, OverrideLog)
    assert len(log.overrides) == 0


def test_override_logger_log_override(tmp_path: Path):
    """Test logging an override."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    file_path = project_dir / "backend" / "services" / "user.py"
    file_path.parent.mkdir(parents=True)

    generated_content = "# Generated code\nprint('hello')"
    user_content = "# User's custom code\nprint('goodbye')"

    OverrideLogger.log_override(
        path=file_path,
        generated_content=generated_content,
        user_content=user_content,
        strategy=FileStrategy.GENERATE_ONCE,
        project_dir=project_dir,
    )

    # Check log was created
    log = OverrideLogger.load(project_dir)

    assert len(log.overrides) == 1

    override_path = "backend/services/user.py"
    assert override_path in log.overrides

    override = log.overrides[override_path]
    assert override.strategy == FileStrategy.GENERATE_ONCE.value
    assert override.reviewed is False
    assert override.diff_summary is not None

    # Check diff cache was created
    diff_cache = project_dir / ".prisme" / "diffs" / "backend_services_user.py.diff"
    assert diff_cache.exists()


def test_override_logger_generate_markdown(tmp_path: Path):
    """Test generating Markdown representation."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    log = OverrideLog()

    override = Override(
        path="backend/services/user.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=False,
        diff_summary={"lines_added": 5, "lines_removed": 2, "lines_changed": 3},
    )

    log.add_override(override)

    markdown = OverrideLogger.generate_markdown(log, project_dir)

    assert "# Code Override Log" in markdown
    assert "backend/services/user.py" in markdown
    assert "**Unreviewed Overrides**: 1" in markdown
    assert "+5 lines" in markdown
    assert "-2 lines" in markdown


def test_override_logger_markdown_with_reviewed(tmp_path: Path):
    """Test Markdown generation with both reviewed and unreviewed."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    log = OverrideLog()

    override1 = Override(
        path="file1.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T10:00:00",
        generated_hash="abc",
        user_hash="def",
        reviewed=False,
    )

    override2 = Override(
        path="file2.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        timestamp="2026-01-23T11:00:00",
        generated_hash="ghi",
        user_hash="jkl",
        reviewed=True,
    )

    log.add_override(override1)
    log.add_override(override2)

    markdown = OverrideLogger.generate_markdown(log, project_dir)

    assert "file1.py" in markdown
    assert "file2.py" in markdown
    assert "⚠️" in markdown  # Unreviewed icon
    assert "✓" in markdown  # Reviewed icon
    assert "Reviewed Overrides" in markdown


def test_override_logger_update_existing_override(tmp_path: Path):
    """Test that logging an override for same file updates it."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    file_path = project_dir / "test.py"

    # First override
    OverrideLogger.log_override(
        path=file_path,
        generated_content="version 1",
        user_content="user version 1",
        strategy=FileStrategy.GENERATE_ONCE,
        project_dir=project_dir,
    )

    log1 = OverrideLogger.load(project_dir)
    assert len(log1.overrides) == 1

    # Second override for same file
    OverrideLogger.log_override(
        path=file_path,
        generated_content="version 2",
        user_content="user version 2",
        strategy=FileStrategy.GENERATE_ONCE,
        project_dir=project_dir,
    )

    log2 = OverrideLogger.load(project_dir)

    # Should still be 1 override (updated, not added)
    assert len(log2.overrides) == 1

    # Hash should be updated
    override = log2.overrides["test.py"]
    assert override.generated_hash == hash_content("version 2")
    assert override.user_hash == hash_content("user version 2")

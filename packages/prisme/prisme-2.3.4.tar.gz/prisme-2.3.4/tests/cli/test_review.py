"""Tests for the prism review CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prisme.cli import main
from prisme.spec.stack import FileStrategy
from prisme.tracking.logger import OverrideLogger

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_project_with_overrides(tmp_path: Path):
    """Create a mock project with some overrides."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create override log with test data
    from prisme.tracking.logger import Override, OverrideLog

    log = OverrideLog()

    log.add_override(
        Override(
            path="backend/services/user.py",
            strategy=FileStrategy.GENERATE_ONCE.value,
            timestamp="2026-01-23T10:00:00",
            generated_hash="abc123",
            user_hash="def456",
            reviewed=False,
            diff_summary={"lines_added": 5, "lines_removed": 2, "lines_changed": 3},
        )
    )

    log.add_override(
        Override(
            path="backend/services/post.py",
            strategy=FileStrategy.GENERATE_ONCE.value,
            timestamp="2026-01-23T11:00:00",
            generated_hash="ghi789",
            user_hash="jkl012",
            reviewed=True,
            diff_summary={"lines_added": 2, "lines_removed": 1, "lines_changed": 0},
        )
    )

    OverrideLogger.save(log, project_dir)

    # Create a diff cache for testing
    diff_cache_dir = project_dir / ".prisme" / "diffs"
    diff_cache_dir.mkdir(parents=True, exist_ok=True)

    diff_content = """--- generated
+++ user
@@ -1,3 +1,5 @@
 def create(self, data):
-    return db.add(User(**data.dict()))
+    user = User(**data.model_dump())
+    send_welcome_email(user.email)
+    return db.add(user)
"""

    (diff_cache_dir / "backend_services_user.py.diff").write_text(diff_content)

    return project_dir


def test_review_summary_no_overrides(cli_runner: CliRunner, tmp_path: Path):
    """Test review summary with no overrides."""
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(main, ["review", "summary"])

        assert result.exit_code == 0
        assert "Override Log Summary" in result.output
        assert "Total Overrides: 0" in result.output


def test_review_summary_with_overrides(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test review summary with overrides."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "summary"])

        assert result.exit_code == 0
        assert "Override Log Summary" in result.output
        assert "Total Overrides: 2" in result.output
        assert "Unreviewed: 1" in result.output
        assert "Reviewed: 1" in result.output


def test_review_list_all(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test listing all overrides."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "list"])

        assert result.exit_code == 0
        assert "backend/services/user.py" in result.output
        assert "backend/services/post.py" in result.output


def test_review_list_unreviewed(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test listing only unreviewed overrides."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "list", "--unreviewed"])

        assert result.exit_code == 0
        assert "backend/services/user.py" in result.output
        assert "backend/services/post.py" not in result.output  # Reviewed, should be excluded


def test_review_list_empty(cli_runner: CliRunner, tmp_path: Path):
    """Test listing when no overrides exist."""
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(main, ["review", "list"])

        assert result.exit_code == 0
        assert "No overrides recorded" in result.output


def test_review_diff(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test showing diff for an override."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "diff", "backend/services/user.py"])

        assert result.exit_code == 0
        assert "Custom Code Preserved" in result.output
        assert "backend/services/user.py" in result.output
        assert "Diff:" in result.output
        assert "send_welcome_email" in result.output


def test_review_diff_not_found(cli_runner: CliRunner, tmp_path: Path):
    """Test showing diff for non-existent override."""
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(main, ["review", "diff", "nonexistent.py"])

        assert result.exit_code == 1
        assert "No override found" in result.output


def test_review_show(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test showing override details."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "show", "backend/services/user.py"])

        assert result.exit_code == 0
        assert "Override Details" in result.output
        assert "backend/services/user.py" in result.output
        assert "generate_once" in result.output
        assert "Lines Added" in result.output


def test_review_mark_reviewed(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test marking an override as reviewed."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "mark-reviewed", "backend/services/user.py"])

        assert result.exit_code == 0
        assert "Marked backend/services/user.py as reviewed" in result.output

        # Verify it was actually marked
        log = OverrideLogger.load(mock_project_with_overrides)
        override = log.get("backend/services/user.py")
        assert override.reviewed is True


def test_review_mark_reviewed_already_reviewed(
    cli_runner: CliRunner, mock_project_with_overrides: Path
):
    """Test marking an already-reviewed override."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "mark-reviewed", "backend/services/post.py"])

        assert result.exit_code == 0
        assert "already marked as reviewed" in result.output


def test_review_mark_all_reviewed_with_confirmation(
    cli_runner: CliRunner, mock_project_with_overrides: Path
):
    """Test marking all overrides as reviewed with confirmation."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        # Confirm with 'y'
        result = cli_runner.invoke(main, ["review", "mark-all-reviewed"], input="y\n")

        assert result.exit_code == 0
        assert "Marked 1 overrides as reviewed" in result.output  # Only 1 unreviewed


def test_review_mark_all_reviewed_cancel(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test cancelling mark all reviewed."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        # Cancel with 'n'
        result = cli_runner.invoke(main, ["review", "mark-all-reviewed"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output


def test_review_mark_all_reviewed_skip_confirm(
    cli_runner: CliRunner, mock_project_with_overrides: Path
):
    """Test marking all with --yes flag."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "mark-all-reviewed", "--yes"])

        assert result.exit_code == 0
        assert "Marked 1 overrides as reviewed" in result.output


def test_review_clear_reviewed(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test clearing reviewed overrides."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        # Confirm with 'y'
        result = cli_runner.invoke(main, ["review", "clear"], input="y\n")

        assert result.exit_code == 0
        assert "Cleared 1 reviewed overrides" in result.output

        # Verify only reviewed was cleared
        log = OverrideLogger.load(mock_project_with_overrides)
        assert len(log.overrides) == 1  # Only unreviewed remains
        assert "backend/services/user.py" in log.overrides


def test_review_clear_all(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test clearing all overrides."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        # Confirm with 'y'
        result = cli_runner.invoke(main, ["review", "clear", "--all"], input="y\n")

        assert result.exit_code == 0
        assert "Cleared 2 overrides" in result.output

        # Verify all were cleared
        log = OverrideLogger.load(mock_project_with_overrides)
        assert len(log.overrides) == 0


def test_review_clear_cancel(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test cancelling clear operation."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "clear"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify nothing was cleared
        log = OverrideLogger.load(mock_project_with_overrides)
        assert len(log.overrides) == 2


def test_review_clear_with_yes_flag(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test clearing with --yes flag to skip confirmation."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "clear", "--yes"])

        assert result.exit_code == 0
        assert "Cleared 1 reviewed overrides" in result.output


@pytest.fixture
def mock_project_with_generated_content(tmp_path: Path):
    """Create a mock project with override and cached generated content."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create the actual file with user content
    file_path = "backend/services/user.py"
    (project_dir / "backend" / "services").mkdir(parents=True)
    (project_dir / "backend" / "services" / "user.py").write_text("# User modified code")

    # Create override log with test data
    from prisme.tracking.logger import Override, OverrideLog

    log = OverrideLog()
    log.add_override(
        Override(
            path=file_path,
            strategy=FileStrategy.GENERATE_ONCE.value,
            timestamp="2026-01-23T10:00:00",
            generated_hash="abc123",
            user_hash="def456",
            reviewed=False,
        )
    )
    OverrideLogger.save(log, project_dir)

    # Cache generated content for restore
    generated_dir = project_dir / ".prisme" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    (generated_dir / "backend_services_user.py").write_text("# Original generated code")

    return project_dir


def test_review_restore_success(cli_runner: CliRunner, mock_project_with_generated_content: Path):
    """Test restoring generated code successfully."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_generated_content):
        result = cli_runner.invoke(main, ["review", "restore", "backend/services/user.py", "--yes"])

        assert result.exit_code == 0
        assert "Restored generated code" in result.output

        # Verify file was restored
        restored_file = mock_project_with_generated_content / "backend/services/user.py"
        assert restored_file.read_text() == "# Original generated code"

        # Verify override was removed from log
        log = OverrideLogger.load(mock_project_with_generated_content)
        assert log.get("backend/services/user.py") is None


def test_review_restore_not_found(cli_runner: CliRunner, tmp_path: Path):
    """Test restore when no override exists."""
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(main, ["review", "restore", "nonexistent.py"])

        assert result.exit_code == 1
        assert "No override found" in result.output


def test_review_restore_no_cached_content(cli_runner: CliRunner, mock_project_with_overrides: Path):
    """Test restore when no generated content is cached."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_overrides):
        result = cli_runner.invoke(main, ["review", "restore", "backend/services/user.py"])

        assert result.exit_code == 1
        assert "Generated content not cached" in result.output


def test_review_restore_cancel(cli_runner: CliRunner, mock_project_with_generated_content: Path):
    """Test cancelling restore operation."""
    with patch("prisme.cli.Path.cwd", return_value=mock_project_with_generated_content):
        result = cli_runner.invoke(
            main, ["review", "restore", "backend/services/user.py"], input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify file was NOT restored
        file_content = (
            mock_project_with_generated_content / "backend/services/user.py"
        ).read_text()
        assert file_content == "# User modified code"

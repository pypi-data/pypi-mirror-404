"""Tests for migration warning messages after generation (issues #55 and #57)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prisme.cli import _show_migration_warnings
from prisme.generators.base import GeneratorResult
from prisme.tracking.model_diff import ModelFieldChange


class _FakeGenConfig:
    backend_output = "backend"


@pytest.fixture
def mock_stack_spec() -> MagicMock:
    spec = MagicMock()
    spec.name = "TestProject"
    return spec


class TestMigrationWarnings:
    """Tests for _show_migration_warnings."""

    def test_no_migrations_shows_initial_warning(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """Issue #57: When no migration files exist, show initial migration warning."""
        # Create alembic/versions directory with no .py files
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=1)}

        with (
            patch("prisme.cli.console") as mock_console,
            patch("prisme.cli._load_generator_config", return_value=_FakeGenConfig()),
        ):
            _show_migration_warnings(mock_stack_spec, results, tmp_path)

            # Check that Panel was printed with initial migration message
            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert any("Initial Migration" in str(c.args[0].title) for c in panel_calls)

    def test_model_changes_shows_migration_warning(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """Issue #55: When models were written, show migration needed warning."""
        # Create alembic/versions directory WITH a migration file
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=3)}

        with (
            patch("prisme.cli.console") as mock_console,
            patch("prisme.cli._load_generator_config", return_value=_FakeGenConfig()),
        ):
            _show_migration_warnings(mock_stack_spec, results, tmp_path)

            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert any("Migration May Be Needed" in str(c.args[0].title) for c in panel_calls)

    def test_no_warning_when_no_model_changes(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """No warning when models weren't written."""
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=0)}

        with (
            patch("prisme.cli.console") as mock_console,
            patch("prisme.cli._load_generator_config", return_value=_FakeGenConfig()),
        ):
            _show_migration_warnings(mock_stack_spec, results, tmp_path)

            # No panel should be printed
            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert len(panel_calls) == 0

    def test_detailed_field_changes_shown(self, tmp_path: Path, mock_stack_spec: MagicMock) -> None:
        """Issue #55: When specific field changes detected, show them in the warning."""
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        changes = [ModelFieldChange(model_name="User", added=["token"], removed=["legacy"])]
        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=1)}

        with (
            patch("prisme.cli.console") as mock_console,
            patch("prisme.cli._load_generator_config", return_value=_FakeGenConfig()),
            patch("prisme.cli.detect_model_changes", return_value=changes),
        ):
            _show_migration_warnings(mock_stack_spec, results, tmp_path)

            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert len(panel_calls) == 1
            panel_body = str(panel_calls[0].args[0].renderable)
            assert "User" in panel_body
            assert "token" in panel_body

    def test_fallback_when_detection_fails(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """Falls back to generic message when detection raises."""
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=1)}

        with (
            patch("prisme.cli.console") as mock_console,
            patch("prisme.cli._load_generator_config", return_value=_FakeGenConfig()),
            patch("prisme.cli.detect_model_changes", side_effect=RuntimeError("boom")),
        ):
            _show_migration_warnings(mock_stack_spec, results, tmp_path)

            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert len(panel_calls) == 1
            panel_body = str(panel_calls[0].args[0].renderable)
            assert "Model files were updated" in panel_body

"""Tests for prism validate command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prisme.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_valid_spec(
        self,
        cli_runner: CliRunner,
        valid_spec_file: Path,
    ) -> None:
        """Valid spec returns success message."""
        result = cli_runner.invoke(main, ["validate", str(valid_spec_file)])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_shows_spec_name(
        self,
        cli_runner: CliRunner,
        valid_spec_file: Path,
    ) -> None:
        """Output includes the spec name."""
        result = cli_runner.invoke(main, ["validate", str(valid_spec_file)])

        assert result.exit_code == 0
        assert "test-project" in result.output

    def test_validate_shows_model_count(
        self,
        cli_runner: CliRunner,
        valid_spec_file: Path,
    ) -> None:
        """Output includes model count."""
        result = cli_runner.invoke(main, ["validate", str(valid_spec_file)])

        assert result.exit_code == 0
        assert "Models: 2" in result.output

    def test_validate_lists_model_names(
        self,
        cli_runner: CliRunner,
        valid_spec_file: Path,
    ) -> None:
        """Output lists individual model names."""
        result = cli_runner.invoke(main, ["validate", str(valid_spec_file)])

        assert result.exit_code == 0
        assert "User" in result.output
        assert "Post" in result.output

    def test_validate_shows_field_counts(
        self,
        cli_runner: CliRunner,
        valid_spec_file: Path,
    ) -> None:
        """Output shows field counts per model."""
        result = cli_runner.invoke(main, ["validate", str(valid_spec_file)])

        assert result.exit_code == 0
        assert "2 fields" in result.output

    def test_validate_spec_not_found(
        self,
        cli_runner: CliRunner,
    ) -> None:
        """Returns error when file doesn't exist."""
        result = cli_runner.invoke(main, ["validate", "nonexistent.py"])

        # Click handles missing file with its own error
        assert result.exit_code != 0

    def test_validate_invalid_python_syntax(
        self,
        cli_runner: CliRunner,
        invalid_spec_file: Path,
    ) -> None:
        """Reports load errors for unparseable files."""
        result = cli_runner.invoke(main, ["validate", str(invalid_spec_file)])

        assert result.exit_code == 1
        assert "error" in result.output.lower()

    def test_validate_missing_stack_variable(
        self,
        cli_runner: CliRunner,
        spec_missing_stack: Path,
    ) -> None:
        """Reports error when spec file has no stack variable."""
        result = cli_runner.invoke(main, ["validate", str(spec_missing_stack)])

        assert result.exit_code == 1
        assert "error" in result.output.lower()

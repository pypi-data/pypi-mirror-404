"""Tests for CI/CD CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from prisme.cli import main


class TestCICommands:
    """Test CI/CD CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            # Create prisme.toml config
            config_file = project_dir / "prisme.toml"
            config_file.write_text(
                'prisme_version = "0.12.1"\nconfig_version = 1\n\n'
                "[project]\n"
                'spec_path = "specs/models.py"\n'
            )
            yield project_dir

    def test_ci_group_exists(self, runner):
        """Test that ci command group exists."""
        result = runner.invoke(main, ["ci", "--help"])
        assert result.exit_code == 0
        assert "CI/CD management commands" in result.output

    def test_ci_init_command_exists(self, runner):
        """Test that ci init command exists."""
        result = runner.invoke(main, ["ci", "init", "--help"])
        assert result.exit_code == 0
        assert "Generate CI/CD workflows" in result.output

    def test_ci_status_command_exists(self, runner):
        """Test that ci status command exists."""
        result = runner.invoke(main, ["ci", "status", "--help"])
        assert result.exit_code == 0
        assert "Check CI/CD setup status" in result.output

    def test_ci_validate_command_exists(self, runner):
        """Test that ci validate command exists."""
        result = runner.invoke(main, ["ci", "validate", "--help"])
        assert result.exit_code == 0
        assert "Validate GitHub Actions workflows" in result.output

    def test_ci_status_shows_missing_files(self, runner, temp_project):
        """Test ci status shows missing files correctly."""
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(main, ["ci", "status"])
            assert result.exit_code == 0
            assert "Missing" in result.output
            assert "prisme ci init" in result.output

    def test_ci_status_shows_existing_files(self, runner):
        """Test ci status shows existing files correctly."""
        with runner.isolated_filesystem():
            # Create the CI files
            workflows_dir = Path(".github/workflows")
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "ci.yml").write_text("name: CI")
            (workflows_dir / "release.yml").write_text("name: Release")
            Path(".releaserc.json").write_text("{}")
            Path("commitlint.config.js").write_text("module.exports = {}")
            Path(".github/dependabot.yml").write_text("version: 2")
            Path("CHANGELOG.md").write_text("# Changelog")

            result = runner.invoke(main, ["ci", "status"])
            assert result.exit_code == 0
            assert "Configured" in result.output
            assert "All CI/CD components configured" in result.output

    # NOTE: ci init requires a .prism directory (project must be initialized).
    # Spec loading is now optional with graceful fallback to CLI flags.

    def test_ci_init_without_prism_dir(self, runner):
        """Test ci init fails without .prism directory."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["ci", "init"])
            assert result.exit_code == 0  # Command exits but shows error
            assert "Not a Prism project" in result.output

    def test_ci_init_without_spec_uses_defaults(self, runner):
        """Test ci init works without spec file when .prism exists."""
        with runner.isolated_filesystem():
            # Create .prism directory (project is initialized)
            Path(".prisme").mkdir()
            result = runner.invoke(main, ["ci", "init"])
            assert result.exit_code == 0
            assert "CI/CD workflows generated successfully" in result.output

    def test_ci_init_with_frontend_flag(self, runner):
        """Test ci init --frontend flag is recognized."""
        result = runner.invoke(main, ["ci", "init", "--help"])
        assert result.exit_code == 0
        assert "--frontend" in result.output
        assert "Include frontend workflows" in result.output

    def test_ci_init_with_redis_flag(self, runner):
        """Test ci init --redis flag is recognized."""
        result = runner.invoke(main, ["ci", "init", "--help"])
        assert result.exit_code == 0
        assert "--redis" in result.output
        assert "Include Redis in CI" in result.output

    def test_ci_validate_without_workflows(self, runner, temp_project):
        """Test ci validate without workflows."""
        with runner.isolated_filesystem(temp_dir=temp_project):
            result = runner.invoke(main, ["ci", "validate"])
            assert result.exit_code == 0
            assert "No workflows found" in result.output

    @patch("subprocess.run")
    def test_ci_validate_without_act(self, mock_run, runner):
        """Test ci validate without act installed."""
        mock_run.side_effect = FileNotFoundError()

        with runner.isolated_filesystem():
            # Create workflow directory
            workflows_dir = Path(".github/workflows")
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "ci.yml").write_text("name: CI")

            result = runner.invoke(main, ["ci", "validate"])
            assert result.exit_code == 0
            assert "'act' not found" in result.output

    @patch("subprocess.run")
    def test_ci_validate_with_act(self, mock_run, runner):
        """Test ci validate with act installed."""
        # Mock subprocess to simulate act being installed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Stage  Job ID  Job name  Workflow name  Workflow file"
        mock_run.return_value = mock_result

        with runner.isolated_filesystem():
            # Create workflow directory
            workflows_dir = Path(".github/workflows")
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "ci.yml").write_text("name: CI")

            result = runner.invoke(main, ["ci", "validate"])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

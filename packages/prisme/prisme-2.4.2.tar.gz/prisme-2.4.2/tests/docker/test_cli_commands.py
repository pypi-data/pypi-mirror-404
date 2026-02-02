"""Tests for Docker-related CLI commands."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prisme.cli import main


class TestDockerCommands:
    """Tests for prism docker:* commands."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    def test_docker_logs_without_compose_file(self, runner):
        """Test docker logs command fails without docker-compose file."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["docker", "logs"])

            assert result.exit_code == 0
            assert "docker-compose.dev.yml not found" in result.output

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_logs_all_services(self, mock_run, runner):
        """Test docker logs command for all services."""
        with runner.isolated_filesystem():
            # Create docker-compose file
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "logs"])

            assert result.exit_code == 0
            # Check that subprocess.run was called with docker compose logs
            call_args = mock_run.call_args[0][0]
            assert "docker" in call_args
            assert "compose" in call_args
            assert "logs" in call_args

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_logs_specific_service(self, mock_run, runner):
        """Test docker logs command for a specific service."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "logs", "backend"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "logs" in call_args
            assert "backend" in call_args

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_logs_with_follow(self, mock_run, runner):
        """Test docker logs command with follow flag."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "logs", "-f"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "-f" in call_args

    def test_docker_shell_invalid_service(self, runner):
        """Test docker shell command with invalid service name."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")
            result = runner.invoke(main, ["docker", "shell", "invalid"])

            # Click should reject invalid choice
            assert result.exit_code != 0
            assert "Invalid value" in result.output

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_shell(self, mock_run, runner):
        """Test docker shell command."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "shell", "backend"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "exec" in call_args
            assert "backend" in call_args
            assert "/bin/sh" in call_args

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_down(self, mock_run, runner):
        """Test docker down command."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "down"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "down" in call_args

    def test_docker_reset_db_cancelled(self, runner):
        """Test docker reset-db command cancelled."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")
            result = runner.invoke(main, ["docker", "reset-db"], input="n\n")

            assert result.exit_code == 1

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_backup_db(self, mock_run, runner):
        """Test docker backup-db command."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")

            result = runner.invoke(main, ["docker", "backup-db", "backup.sql"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "pg_dump" in call_args

    @patch("prisme.docker.manager.subprocess.run")
    def test_docker_restore_db(self, mock_run, runner):
        """Test docker restore-db command."""
        with runner.isolated_filesystem():
            Path("docker-compose.dev.yml").write_text("version: '3.8'\nservices:\n  backend: {}\n")
            Path("backup.sql").write_text("-- SQL backup")

            result = runner.invoke(main, ["docker", "restore-db", "backup.sql"])

            assert result.exit_code == 0
            call_args = mock_run.call_args[0][0]
            assert "psql" in call_args


class TestProjectsCommands:
    """Tests for prism projects:* commands."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @patch("prisme.docker.proxy.subprocess.run")
    def test_projects_list_with_running_projects(self, mock_run, runner):
        """Test projects list command with running projects."""
        # Mock docker ps to return running proxy
        mock_run.return_value.stdout = "prism-proxy\n"
        mock_run.return_value.returncode = 0

        result = runner.invoke(main, ["projects", "list"])

        assert result.exit_code == 0
        # When no containers on network, should show "No running projects"
        assert "No running projects" in result.output or "Reverse proxy" in result.output

    @patch("prisme.docker.proxy.subprocess.run")
    def test_projects_list_proxy_not_running(self, mock_run, runner):
        """Test projects list command when proxy is not running."""
        # Mock docker ps to return nothing (proxy not running)
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        result = runner.invoke(main, ["projects", "list"])

        assert result.exit_code == 0
        assert "Reverse proxy is not running" in result.output

    @patch("prisme.docker.proxy.subprocess.run")
    def test_projects_down_all_proxy_not_running(self, mock_run, runner):
        """Test projects down-all command when proxy is not running."""
        # Mock docker ps to return nothing (proxy not running)
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        result = runner.invoke(main, ["projects", "down-all"], input="y\n")

        assert result.exit_code == 0
        # The command now runs even if proxy isn't running to catch orphaned containers
        assert (
            "No running projects on proxy network" in result.output
            or "No containers to stop" in result.output
        )

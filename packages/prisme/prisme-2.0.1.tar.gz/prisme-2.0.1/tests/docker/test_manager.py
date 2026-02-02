"""Tests for Docker and Docker Compose management."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from prisme.docker import ComposeManager, DockerManager


class TestDockerManager:
    """Tests for DockerManager."""

    @patch("subprocess.run")
    def test_is_available_when_docker_running(self, mock_run):
        """Test is_available returns True when Docker is running."""
        mock_run.return_value = Mock(returncode=0)

        assert DockerManager.is_available() is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_is_available_when_docker_not_running(self, mock_run):
        """Test is_available returns False when Docker is not running."""
        mock_run.return_value = Mock(returncode=1)

        assert DockerManager.is_available() is False

    @patch("subprocess.run")
    def test_is_available_when_docker_not_installed(self, mock_run):
        """Test is_available returns False when Docker is not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert DockerManager.is_available() is False

    @patch("subprocess.run")
    def test_is_available_timeout(self, mock_run):
        """Test is_available returns False on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=5)

        assert DockerManager.is_available() is False

    @patch("subprocess.run")
    def test_get_version_success(self, mock_run):
        """Test get_version returns version string when Docker is available."""
        mock_run.return_value = Mock(returncode=0, stdout="Docker version 24.0.0, build abc123")

        version = DockerManager.get_version()

        assert version == "Docker version 24.0.0, build abc123"

    @patch("subprocess.run")
    def test_get_version_failure(self, mock_run):
        """Test get_version returns None when Docker is not available."""
        mock_run.return_value = Mock(returncode=1)

        version = DockerManager.get_version()

        assert version is None

    @patch("subprocess.run")
    def test_get_version_not_installed(self, mock_run):
        """Test get_version returns None when Docker is not installed."""
        mock_run.side_effect = FileNotFoundError()

        version = DockerManager.get_version()

        assert version is None


class TestComposeManager:
    """Tests for ComposeManager."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            # Create a dummy docker-compose.dev.yml
            (project_dir / "docker-compose.dev.yml").write_text(
                "version: '3.8'\nservices:\n  test: {}\n"
            )
            yield project_dir

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        return Mock(spec=Console)

    def test_initialization(self, temp_project_dir, mock_console):
        """Test ComposeManager initialization."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        assert manager.project_dir == temp_project_dir
        assert manager.compose_file == temp_project_dir / "docker-compose.dev.yml"
        assert manager.console == mock_console

    def test_initialization_without_console(self, temp_project_dir):
        """Test ComposeManager creates its own console if not provided."""
        manager = ComposeManager(temp_project_dir)

        assert manager.console is not None
        assert isinstance(manager.console, Console)

    @patch("prisme.docker.manager.ProxyManager.is_running")
    @patch("subprocess.run")
    @patch("prisme.docker.manager.ComposeManager._wait_for_health")
    @patch("prisme.docker.manager.ComposeManager._print_urls")
    def test_start_without_rebuild(
        self,
        mock_print_urls,
        mock_wait_health,
        mock_run,
        mock_proxy_running,
        temp_project_dir,
        mock_console,
    ):
        """Test start() without rebuild flag."""
        mock_run.return_value = Mock(returncode=0)
        mock_proxy_running.return_value = True  # Proxy already running
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.start(rebuild=False)

        # Check subprocess.run was called correctly
        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "up",
            "-d",
        ]
        mock_run.assert_called_once()
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

        # Check that health check and URL printing were called
        mock_wait_health.assert_called_once()
        mock_print_urls.assert_called_once()

    @patch("prisme.docker.manager.ProxyManager.is_running")
    @patch("subprocess.run")
    @patch("prisme.docker.manager.ComposeManager._wait_for_health")
    @patch("prisme.docker.manager.ComposeManager._print_urls")
    def test_start_with_rebuild(
        self,
        mock_print_urls,
        mock_wait_health,
        mock_run,
        mock_proxy_running,
        temp_project_dir,
        mock_console,
    ):
        """Test start() with rebuild flag."""
        mock_run.return_value = Mock(returncode=0)
        mock_proxy_running.return_value = True  # Proxy already running
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.start(rebuild=True)

        # Check subprocess.run was called with --build flag
        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "up",
            "-d",
            "--build",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_start_failure(self, mock_run, temp_project_dir, mock_console):
        """Test start() raises exception on failure."""
        mock_run.return_value = Mock(returncode=1)
        manager = ComposeManager(temp_project_dir, console=mock_console)

        with pytest.raises(RuntimeError, match="Failed to start services"):
            manager.start()

    @patch("subprocess.run")
    def test_stop(self, mock_run, temp_project_dir, mock_console):
        """Test stop() calls docker compose down."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.stop()

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "down",
        ]
        mock_run.assert_called_once()
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_stream_logs(self, mock_run, temp_project_dir, mock_console):
        """Test stream_logs() calls docker compose logs -f."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.stream_logs()

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "logs",
            "-f",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_logs_all_services(self, mock_run, temp_project_dir, mock_console):
        """Test logs() for all services."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.logs(service=None, follow=False)

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "logs",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_logs_specific_service(self, mock_run, temp_project_dir, mock_console):
        """Test logs() for a specific service."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.logs(service="backend", follow=False)

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "logs",
            "backend",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_logs_with_follow(self, mock_run, temp_project_dir, mock_console):
        """Test logs() with follow flag."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.logs(service="backend", follow=True)

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "logs",
            "-f",
            "backend",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_shell(self, mock_run, temp_project_dir, mock_console):
        """Test shell() opens shell in service container."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        manager.shell("backend")

        expected_cmd = [
            "docker",
            "compose",
            "-f",
            str(temp_project_dir / "docker-compose.dev.yml"),
            "exec",
            "backend",
            "/bin/sh",
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    def test_get_project_name(self, temp_project_dir, mock_console):
        """Test _get_project_name() returns directory name."""
        manager = ComposeManager(temp_project_dir, console=mock_console)

        project_name = manager._get_project_name()

        # Should be the directory name with dashes/spaces replaced by underscores
        expected = temp_project_dir.name.replace("-", "_").replace(" ", "_")
        assert project_name == expected

    @patch("subprocess.run")
    @patch("prisme.docker.manager.ComposeManager.stop")
    @patch("prisme.docker.manager.ComposeManager.start")
    def test_reset_database(self, mock_start, mock_stop, mock_run, temp_project_dir, mock_console):
        """Test reset_database() stops, removes volume, and restarts."""
        manager = ComposeManager(temp_project_dir, console=mock_console)
        project_name = manager._get_project_name()

        manager.reset_database()

        # Check stop was called
        mock_stop.assert_called_once()

        # Check docker volume rm was called
        mock_run.assert_called_once()
        expected_cmd = ["docker", "volume", "rm", f"{project_name}_postgres_data"]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

        # Check start was called
        mock_start.assert_called_once()

    @patch("subprocess.run")
    def test_backup_database(self, mock_run, temp_project_dir, mock_console):
        """Test backup_database() calls pg_dump."""
        manager = ComposeManager(temp_project_dir, console=mock_console)
        project_name = manager._get_project_name()
        output_file = temp_project_dir / "backup.sql"

        manager.backup_database(output_file)

        # Check docker exec pg_dump was called
        expected_cmd = [
            "docker",
            "exec",
            f"{project_name}_db",
            "pg_dump",
            "-U",
            "postgres",
            project_name,
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

    @patch("subprocess.run")
    def test_restore_database(self, mock_run, temp_project_dir, mock_console):
        """Test restore_database() calls psql."""
        manager = ComposeManager(temp_project_dir, console=mock_console)
        project_name = manager._get_project_name()
        input_file = temp_project_dir / "backup.sql"
        input_file.write_text("-- SQL backup")

        manager.restore_database(input_file)

        # Check docker exec psql was called
        expected_cmd = [
            "docker",
            "exec",
            "-i",
            f"{project_name}_db",
            "psql",
            "-U",
            "postgres",
            project_name,
        ]
        actual_call = mock_run.call_args
        assert actual_call[0][0] == expected_cmd

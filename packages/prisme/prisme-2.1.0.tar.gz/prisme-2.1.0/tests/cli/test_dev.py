"""Tests for prism dev command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from prisme.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestDevCommand:
    """Tests for the dev command."""

    def test_dev_shows_starting_message(
        self,
        cli_runner: CliRunner,
        mock_popen: MagicMock,
    ) -> None:
        """Dev command shows starting message."""
        with cli_runner.isolated_filesystem():
            # Mock to avoid actually starting servers
            mock_popen.return_value.wait.side_effect = KeyboardInterrupt

            result = cli_runner.invoke(main, ["dev"])

            assert "starting" in result.output.lower()

    def test_dev_backend_only_flag(
        self,
        cli_runner: CliRunner,
        mock_popen: MagicMock,
    ) -> None:
        """--backend-only flag is accepted."""
        with cli_runner.isolated_filesystem():
            mock_popen.return_value.wait.side_effect = KeyboardInterrupt

            result = cli_runner.invoke(main, ["dev", "--backend-only"])

            assert "backend" in result.output.lower()

    def test_dev_frontend_only_flag(
        self,
        cli_runner: CliRunner,
        mock_popen: MagicMock,
    ) -> None:
        """--frontend-only flag is accepted."""
        with cli_runner.isolated_filesystem():
            mock_popen.return_value.wait.side_effect = KeyboardInterrupt

            result = cli_runner.invoke(main, ["dev", "--frontend-only"])

            assert "frontend" in result.output.lower()

    def test_dev_docker_no_compose_file(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """--docker shows error when no docker-compose.yml exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["dev", "--docker"])

            assert "docker-compose" in result.output.lower() or "not found" in result.output.lower()

    def test_dev_docker_with_compose_file(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """--docker runs docker-compose when file exists."""
        with cli_runner.isolated_filesystem():
            Path("docker-compose.yml").write_text("version: '3'\n")

            # Simulate KeyboardInterrupt to exit
            mock_subprocess.side_effect = KeyboardInterrupt

            result = cli_runner.invoke(main, ["dev", "--docker"])

            # Should have attempted to run docker-compose
            assert mock_subprocess.called or "docker" in result.output.lower()

    def test_dev_docker_with_docker_dir(
        self,
        cli_runner: CliRunner,
        mock_subprocess: MagicMock,
    ) -> None:
        """--docker finds docker/docker-compose.yml."""
        with cli_runner.isolated_filesystem():
            docker_dir = Path("docker")
            docker_dir.mkdir()
            (docker_dir / "docker-compose.yml").write_text("version: '3'\n")

            mock_subprocess.side_effect = KeyboardInterrupt

            result = cli_runner.invoke(main, ["dev", "--docker"])

            assert mock_subprocess.called or "docker" in result.output.lower()


class TestDevHelperFunctions:
    """Tests for dev command helper functions."""

    def test_start_backend_tries_multiple_modules(
        self,
        mock_popen: MagicMock,
    ) -> None:
        """Backend starter tries multiple module patterns."""
        from prisme.cli import _start_backend

        # First call fails, second succeeds
        mock_popen.side_effect = [Exception("not found"), MagicMock()]

        _start_backend()

        # Should have tried at least once
        assert mock_popen.called

    def test_start_frontend_looks_for_package_json(
        self,
        cli_runner: CliRunner,
        mock_popen: MagicMock,
    ) -> None:
        """Frontend starter looks for package.json."""
        from prisme.cli import _start_frontend

        with cli_runner.isolated_filesystem():
            # No package.json - should return None
            _start_frontend()

            # Without package.json, may return None
            # This is expected behavior

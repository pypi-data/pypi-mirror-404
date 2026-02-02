"""Tests for WorkspaceManager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prisme.devcontainer.config import WorkspaceConfig
from prisme.devcontainer.manager import WorkspaceManager


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> WorkspaceManager:
        """Create a manager instance for testing."""
        return WorkspaceManager(project_dir=tmp_path)

    @pytest.fixture
    def config(self, tmp_path: Path) -> WorkspaceConfig:
        """Create a test configuration."""
        return WorkspaceConfig(
            project_name="testproject",
            project_dir=tmp_path,
            workspace_name="testproject-main",
        )

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_ensure_networks(self, mock_run: MagicMock, manager: WorkspaceManager) -> None:
        """Test network creation is attempted."""
        mock_run.return_value = MagicMock(returncode=0)
        manager.ensure_networks()
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "network" in call_args
        assert "create" in call_args
        assert "prism_proxy_network" in call_args

    def test_get_env_workspace_no_file(
        self, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test getting workspace from non-existent .env file."""
        result = manager._get_env_workspace(config)
        assert result is None

    def test_get_env_workspace_with_file(
        self, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test getting workspace from existing .env file."""
        config.devcontainer_dir.mkdir(parents=True)
        config.env_file.write_text("WORKSPACE_NAME=myworkspace\n")

        result = manager._get_env_workspace(config)
        assert result == "myworkspace"

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_list_workspaces_empty(self, mock_run: MagicMock, manager: WorkspaceManager) -> None:
        """Test listing workspaces when none exist."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        workspaces = manager.list_workspaces()
        assert workspaces == []

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_list_workspaces(self, mock_run: MagicMock, manager: WorkspaceManager) -> None:
        """Test listing workspaces."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="myproject-main-app\tUp 2 hours\nmyproject-main-db\tUp 2 hours\n",
        )
        workspaces = manager.list_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0].workspace_name == "myproject-main"
        assert workspaces[0].status == "running"
        assert "app" in workspaces[0].services
        assert "db" in workspaces[0].services

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_list_workspaces_stopped(self, mock_run: MagicMock, manager: WorkspaceManager) -> None:
        """Test listing stopped workspaces."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="myproject-main-app\tExited (0) 2 hours ago\n",
        )
        workspaces = manager.list_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0].status == "stopped"
        assert workspaces[0].url == ""

    @patch("prisme.devcontainer.manager.DevContainerGenerator")
    def test_ensure_devcontainer_generates_if_missing(
        self, mock_generator_class: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that .devcontainer is generated if missing."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        manager.ensure_devcontainer(config)

        mock_generator.generate.assert_called_once_with(config)

    @patch("prisme.devcontainer.manager.DevContainerGenerator")
    def test_ensure_devcontainer_skips_if_exists(
        self, mock_generator_class: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that .devcontainer is not regenerated if it exists."""
        config.devcontainer_dir.mkdir(parents=True)

        manager.ensure_devcontainer(config)

        mock_generator_class.assert_not_called()

    @patch("prisme.devcontainer.manager.DevContainerGenerator")
    def test_ensure_env_generates_if_missing(
        self, mock_generator_class: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that .env is generated if missing."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        config.devcontainer_dir.mkdir(parents=True)

        manager.ensure_env(config)

        mock_generator.generate_env.assert_called_once_with(config)

    @patch("prisme.devcontainer.manager.DevContainerGenerator")
    def test_ensure_env_regenerates_if_workspace_changed(
        self, mock_generator_class: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that .env is regenerated if workspace name changed."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        config.devcontainer_dir.mkdir(parents=True)
        config.env_file.write_text("WORKSPACE_NAME=old-workspace\n")

        manager.ensure_env(config)

        mock_generator.generate_env.assert_called_once_with(config)


class TestWorkspaceManagerDockerCompose:
    """Tests for WorkspaceManager docker compose commands."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> WorkspaceManager:
        """Create a manager instance for testing."""
        return WorkspaceManager(project_dir=tmp_path)

    @pytest.fixture
    def config(self, tmp_path: Path) -> WorkspaceConfig:
        """Create a test configuration with .devcontainer."""
        config = WorkspaceConfig(
            project_name="testproject",
            project_dir=tmp_path,
            workspace_name="testproject-main",
        )
        # Create .devcontainer directory and files
        config.devcontainer_dir.mkdir(parents=True)
        config.compose_file.write_text("version: '3'\n")
        config.env_file.write_text("WORKSPACE_NAME=testproject-main\n")
        return config

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_up_builds_command(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that up builds the correct docker compose command."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.up(config)

        # Get the docker compose up call (last call with 'up' in args)
        calls = mock_run.call_args_list
        up_call = None
        for call in calls:
            if "up" in call[0][0]:
                up_call = call
                break

        assert up_call is not None
        cmd = up_call[0][0]
        assert "docker" in cmd
        assert "compose" in cmd
        assert "-f" in cmd
        assert "--env-file" in cmd
        assert "up" in cmd
        assert "-d" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_up_with_build_flag(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that up includes --build when requested."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.up(config, build=True)

        calls = mock_run.call_args_list
        up_call = None
        for call in calls:
            if "up" in call[0][0]:
                up_call = call
                break

        assert up_call is not None
        assert "--build" in up_call[0][0]

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_down_builds_command(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that down builds the correct docker compose command."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.down(config)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "compose" in cmd
        assert "down" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_down_with_volumes(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that down includes --volumes when requested."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.down(config, volumes=True)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "--volumes" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_logs_builds_command(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that logs builds the correct command."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.logs(config)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "compose" in cmd
        assert "logs" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_logs_with_follow(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that logs includes -f when requested."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.logs(config, follow=True)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "-f" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_logs_with_service(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that logs includes service name when specified."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.logs(config, service="app")

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "app" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_status_builds_command(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that status builds the correct command."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.status(config)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "compose" in cmd
        assert "ps" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_shell_executes(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that shell executes docker exec."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.shell(config)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "exec" in cmd
        assert "-it" in cmd
        assert "bash" in cmd

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_shell_as_root(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that shell uses root user when requested."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.shell(config, root=True)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "-u" in cmd
        root_idx = cmd.index("-u")
        assert cmd[root_idx + 1] == "root"

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_shell_default_user(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that shell uses vscode user by default."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.shell(config, root=False)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "-u" in cmd
        user_idx = cmd.index("-u")
        assert cmd[user_idx + 1] == "vscode"

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_exec_runs_command(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that exec runs a command in the container."""
        mock_run.return_value = MagicMock(returncode=0)

        result = manager.exec(config, "echo hello")

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "docker" in cmd
        assert "exec" in cmd
        assert "-u" in cmd
        assert "bash" in cmd
        assert "-lc" in cmd
        assert "echo hello" in cmd
        assert result == 0

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_exec_as_root(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that exec uses root user when requested."""
        mock_run.return_value = MagicMock(returncode=0)

        manager.exec(config, "apt update", root=True)

        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "-u" in cmd
        user_idx = cmd.index("-u")
        assert cmd[user_idx + 1] == "root"

    @patch("prisme.devcontainer.manager.subprocess.run")
    def test_exec_returns_exit_code(
        self, mock_run: MagicMock, manager: WorkspaceManager, config: WorkspaceConfig
    ) -> None:
        """Test that exec returns the command exit code."""
        mock_run.return_value = MagicMock(returncode=42)

        result = manager.exec(config, "exit 42")

        assert result == 42

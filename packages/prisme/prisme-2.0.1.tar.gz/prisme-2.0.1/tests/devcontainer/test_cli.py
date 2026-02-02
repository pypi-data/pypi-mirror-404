"""Tests for devcontainer CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from prisme.cli import main


class TestDevContainerUpCommand:
    """Tests for 'prism devcontainer up' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.up")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_up_basic(self, mock_config: MagicMock, mock_up: MagicMock, runner: CliRunner) -> None:
        """Test basic up command."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "up"])

        mock_up.assert_called_once()

    @patch("prisme.devcontainer.manager.WorkspaceManager.up")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_up_with_build(
        self, mock_config: MagicMock, mock_up: MagicMock, runner: CliRunner
    ) -> None:
        """Test up command with --build flag."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "up", "--build"])

        mock_up.assert_called_once()
        call_kwargs = mock_up.call_args[1]
        assert call_kwargs.get("build") is True

    @patch("prisme.devcontainer.manager.WorkspaceManager.up")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_up_with_name(
        self, mock_config: MagicMock, mock_up: MagicMock, runner: CliRunner
    ) -> None:
        """Test up command with --name option."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "up", "--name", "myworkspace"])

        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs.get("workspace_name") == "myworkspace"

    @patch("prisme.devcontainer.manager.WorkspaceManager.up")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_up_with_redis(
        self, mock_config: MagicMock, mock_up: MagicMock, runner: CliRunner
    ) -> None:
        """Test up command with --redis flag."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "up", "--redis"])

        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs.get("include_redis") is True

    @patch("prisme.devcontainer.manager.WorkspaceManager.up")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_up_handles_error(
        self, mock_config: MagicMock, mock_up: MagicMock, runner: CliRunner
    ) -> None:
        """Test up handles errors gracefully."""
        mock_config.return_value = MagicMock()
        mock_up.side_effect = RuntimeError("Failed to start")

        result = runner.invoke(main, ["devcontainer", "up"])

        assert "Error" in result.output


class TestDevContainerDownCommand:
    """Tests for 'prism devcontainer down' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.down")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_down_basic(
        self, mock_config: MagicMock, mock_down: MagicMock, runner: CliRunner
    ) -> None:
        """Test basic down command."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "down"])

        mock_down.assert_called_once()

    @patch("prisme.devcontainer.manager.WorkspaceManager.down")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_down_with_volumes(
        self, mock_config: MagicMock, mock_down: MagicMock, runner: CliRunner
    ) -> None:
        """Test down command with --volumes flag."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "down", "--volumes"])

        mock_down.assert_called_once()
        call_kwargs = mock_down.call_args[1]
        assert call_kwargs.get("volumes") is True

    @patch("prisme.devcontainer.manager.WorkspaceManager.down")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_down_with_name(
        self, mock_config: MagicMock, mock_down: MagicMock, runner: CliRunner
    ) -> None:
        """Test down command with --name option."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "down", "--name", "myworkspace"])

        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs.get("workspace_name") == "myworkspace"


class TestDevContainerShellCommand:
    """Tests for 'prism devcontainer shell' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.shell")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_shell_basic(
        self, mock_config: MagicMock, mock_shell: MagicMock, runner: CliRunner
    ) -> None:
        """Test basic shell command."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "shell"])

        mock_shell.assert_called_once()

    @patch("prisme.devcontainer.manager.WorkspaceManager.shell")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_shell_as_root(
        self, mock_config: MagicMock, mock_shell: MagicMock, runner: CliRunner
    ) -> None:
        """Test shell command with --root flag."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "shell", "--root"])

        mock_shell.assert_called_once()
        call_kwargs = mock_shell.call_args[1]
        assert call_kwargs.get("root") is True


class TestDevContainerLogsCommand:
    """Tests for 'prism devcontainer logs' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.logs")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_logs_basic(
        self, mock_config: MagicMock, mock_logs: MagicMock, runner: CliRunner
    ) -> None:
        """Test basic logs command."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "logs"])

        mock_logs.assert_called_once()

    @patch("prisme.devcontainer.manager.WorkspaceManager.logs")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_logs_with_service(
        self, mock_config: MagicMock, mock_logs: MagicMock, runner: CliRunner
    ) -> None:
        """Test logs command with service argument."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "logs", "app"])

        mock_logs.assert_called_once()
        call_kwargs = mock_logs.call_args[1]
        assert call_kwargs.get("service") == "app"

    @patch("prisme.devcontainer.manager.WorkspaceManager.logs")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_logs_with_follow(
        self, mock_config: MagicMock, mock_logs: MagicMock, runner: CliRunner
    ) -> None:
        """Test logs command with -f flag."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "logs", "-f"])

        mock_logs.assert_called_once()
        call_kwargs = mock_logs.call_args[1]
        assert call_kwargs.get("follow") is True


class TestDevContainerStatusCommand:
    """Tests for 'prism devcontainer status' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.status")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_status_basic(
        self, mock_config: MagicMock, mock_status: MagicMock, runner: CliRunner
    ) -> None:
        """Test basic status command."""
        mock_config.return_value = MagicMock()

        runner.invoke(main, ["devcontainer", "status"])

        mock_status.assert_called_once()


class TestDevContainerListCommand:
    """Tests for 'prism devcontainer list' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.manager.WorkspaceManager.print_list")
    def test_list_calls_print_list(self, mock_print: MagicMock, runner: CliRunner) -> None:
        """Test list command calls print_list."""
        runner.invoke(main, ["devcontainer", "list"])

        mock_print.assert_called_once()


class TestDevContainerGenerateCommand:
    """Tests for 'prism devcontainer generate' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @patch("prisme.devcontainer.generator.DevContainerGenerator.generate")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_generate_basic(
        self, mock_config: MagicMock, mock_generate: MagicMock, runner: CliRunner
    ) -> None:
        """Test basic generate command."""
        config = MagicMock()
        config.devcontainer_dir.exists.return_value = False
        mock_config.return_value = config

        runner.invoke(main, ["devcontainer", "generate"])

        mock_generate.assert_called_once()

    @patch("prisme.devcontainer.generator.DevContainerGenerator.generate")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_generate_skips_existing(
        self, mock_config: MagicMock, mock_generate: MagicMock, runner: CliRunner
    ) -> None:
        """Test generate skips if .devcontainer exists."""
        config = MagicMock()
        config.devcontainer_dir.exists.return_value = True
        mock_config.return_value = config

        result = runner.invoke(main, ["devcontainer", "generate"])

        mock_generate.assert_not_called()
        assert ".devcontainer already exists" in result.output

    @patch("prisme.devcontainer.generator.DevContainerGenerator.generate")
    @patch("prisme.devcontainer.config.WorkspaceConfig.from_directory")
    def test_generate_force(
        self, mock_config: MagicMock, mock_generate: MagicMock, runner: CliRunner
    ) -> None:
        """Test generate with --force flag."""
        config = MagicMock()
        config.devcontainer_dir.exists.return_value = True
        mock_config.return_value = config

        runner.invoke(main, ["devcontainer", "generate", "--force"])

        mock_generate.assert_called_once()


class TestDevContainerGroup:
    """Tests for the devcontainer command group."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    def test_devcontainer_help(self, runner: CliRunner) -> None:
        """Test devcontainer group help text."""
        result = runner.invoke(main, ["devcontainer", "--help"])

        assert result.exit_code == 0
        assert "Workspace-isolated dev container commands" in result.output
        assert "up" in result.output
        assert "down" in result.output
        assert "shell" in result.output
        assert "logs" in result.output
        assert "status" in result.output
        assert "list" in result.output
        assert "generate" in result.output

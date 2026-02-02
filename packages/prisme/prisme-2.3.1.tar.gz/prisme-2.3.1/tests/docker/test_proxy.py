"""Tests for Traefik reverse proxy management."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from prisme.docker.proxy import ProjectInfo, ProxyManager


class TestProxyManager:
    """Test ProxyManager class."""

    def test_is_running_when_proxy_running(self):
        """Test is_running returns True when proxy is running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="abc123\n", returncode=0)

            result = ProxyManager.is_running()

            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "docker" in args
            assert "ps" in args
            assert "-q" in args

    def test_is_running_when_proxy_not_running(self):
        """Test is_running returns False when proxy is not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)

            result = ProxyManager.is_running()

            assert result is False

    def test_is_running_when_docker_not_available(self):
        """Test is_running returns False when Docker is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = ProxyManager.is_running()

            assert result is False

    def test_is_running_on_timeout(self):
        """Test is_running returns False on timeout."""
        with patch("subprocess.run", side_effect=TimeoutError):
            result = ProxyManager.is_running()

            assert result is False

    @patch("prisme.docker.proxy.ProxyManager._start_error_pages_container")
    @patch("prisme.docker.proxy.ProxyManager._get_error_pages_path")
    @patch("prisme.docker.proxy.ProxyManager._get_dynamic_config_path")
    @patch("prisme.docker.proxy.ProxyManager._get_config_path")
    @patch("prisme.docker.proxy.ProxyManager._ensure_network")
    @patch("prisme.docker.proxy.ProxyManager.is_running")
    @patch("subprocess.run")
    def test_start_when_not_running(
        self,
        mock_run,
        mock_is_running,
        mock_ensure_network,
        mock_get_config,
        mock_get_dynamic_config,
        mock_get_error_pages,
        mock_start_error_pages,
    ):
        """Test starting proxy when not already running."""
        mock_is_running.return_value = False
        mock_get_config.return_value = Path("/tmp/traefik.yml")
        mock_get_dynamic_config.return_value = Path("/tmp/traefik-dynamic.yml")
        mock_get_error_pages.return_value = Path("/tmp/error-pages")
        mock_run.return_value = Mock(returncode=0)

        proxy = ProxyManager()
        proxy.start()

        # Verify network creation was called
        mock_ensure_network.assert_called_once()

        # Verify docker run was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "run" in args
        assert "-d" in args
        assert ProxyManager.CONTAINER_NAME in args
        assert ProxyManager.IMAGE in args

        # Verify ports are exposed
        assert "-p" in args
        port_indices = [i for i, arg in enumerate(args) if arg == "-p"]
        ports = [args[i + 1] for i in port_indices]
        assert "80:80" in ports
        assert "8080:8080" in ports

    @patch("prisme.docker.proxy.ProxyManager.is_running")
    def test_start_when_already_running(self, mock_is_running):
        """Test starting proxy when already running does nothing."""
        mock_is_running.return_value = True

        proxy = ProxyManager()
        with patch("subprocess.run") as mock_run:
            proxy.start()

            # Should not call docker run
            mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("prisme.docker.proxy.ProxyManager._start_error_pages_container")
    @patch("prisme.docker.proxy.ProxyManager._get_error_pages_path")
    @patch("prisme.docker.proxy.ProxyManager._get_dynamic_config_path")
    @patch("prisme.docker.proxy.ProxyManager._get_config_path")
    @patch("prisme.docker.proxy.ProxyManager._ensure_network")
    @patch("prisme.docker.proxy.ProxyManager.is_running")
    def test_start_with_failure(
        self,
        mock_is_running,
        mock_ensure_network,
        mock_get_config,
        mock_get_dynamic_config,
        mock_get_error_pages,
        mock_start_error_pages,
        mock_run,
    ):
        """Test start raises exception on failure."""
        mock_is_running.return_value = False
        mock_get_config.return_value = Path("/tmp/traefik.yml")
        mock_get_dynamic_config.return_value = Path("/tmp/traefik-dynamic.yml")
        mock_get_error_pages.return_value = Path("/tmp/error-pages")
        mock_run.side_effect = Exception("Docker error")

        proxy = ProxyManager()
        with pytest.raises(Exception, match="Docker error"):
            proxy.start()

    @patch("subprocess.run")
    @patch("prisme.docker.proxy.ProxyManager.is_running")
    def test_stop_when_running(self, mock_is_running, mock_run):
        """Test stopping proxy when running."""
        mock_is_running.return_value = True
        mock_run.return_value = Mock(returncode=0)

        proxy = ProxyManager()
        proxy.stop()

        assert mock_run.call_count == 2
        # First call: remove proxy container
        args = mock_run.call_args_list[0][0][0]
        assert "docker" in args
        assert "rm" in args
        assert "-f" in args
        assert ProxyManager.CONTAINER_NAME in args
        # Second call: remove error pages container
        args = mock_run.call_args_list[1][0][0]
        assert "docker" in args
        assert "rm" in args
        assert "prism-error-pages" in args

    @patch("prisme.docker.proxy.ProxyManager.is_running")
    def test_stop_when_not_running(self, mock_is_running):
        """Test stopping proxy when not running does nothing gracefully."""
        mock_is_running.return_value = False

        proxy = ProxyManager()
        with patch("subprocess.run") as mock_run:
            proxy.stop()

            # Should not call docker rm
            mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_ensure_network_creates_network(self, mock_run):
        """Test _ensure_network creates the network."""
        mock_run.return_value = Mock(returncode=0)

        ProxyManager._ensure_network()

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "docker" in args
        assert "network" in args
        assert "create" in args
        assert ProxyManager.NETWORK_NAME in args

    @patch("subprocess.run")
    def test_ensure_network_handles_existing_network(self, mock_run):
        """Test _ensure_network handles already existing network."""
        mock_run.return_value = Mock(returncode=1, stderr=b"network already exists")

        # Should not raise exception
        ProxyManager._ensure_network()

    @patch("subprocess.run")
    def test_list_projects_with_running_projects(self, mock_run):
        """Test listing running projects."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="myapp_backend\nmyapp_frontend\nmyapp_db\nblog_backend\nblog_frontend\n",
        )

        proxy = ProxyManager()
        projects = proxy.list_projects()

        assert len(projects) == 2
        assert any(p.name == "myapp" and "backend" in p.services for p in projects)
        assert any(p.name == "blog" and "frontend" in p.services for p in projects)

    @patch("subprocess.run")
    def test_list_projects_with_no_projects(self, mock_run):
        """Test listing projects when none are running."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        proxy = ProxyManager()
        projects = proxy.list_projects()

        assert len(projects) == 0

    @patch("subprocess.run")
    def test_list_projects_excludes_proxy_container(self, mock_run):
        """Test listing projects excludes the proxy container itself."""
        mock_run.return_value = Mock(
            returncode=0, stdout=f"{ProxyManager.CONTAINER_NAME}\nmyapp_backend\n"
        )

        proxy = ProxyManager()
        projects = proxy.list_projects()

        # Should only have myapp, not the proxy
        assert len(projects) == 1
        assert projects[0].name == "myapp"

    @patch("subprocess.run")
    def test_list_projects_on_docker_error(self, mock_run):
        """Test listing projects returns empty list on Docker error."""
        mock_run.return_value = Mock(returncode=1, stdout="")

        proxy = ProxyManager()
        projects = proxy.list_projects()

        assert len(projects) == 0

    @patch("subprocess.run")
    def test_stop_all_projects_with_running_projects(self, mock_run):
        """Test stopping all projects."""
        # Calls sequence:
        # 1. list_projects: docker ps --filter network=...
        # 2. docker compose down for the project
        # 3-4. _find_orphaned_containers: 2x docker ps -a (labels and patterns)
        mock_run.side_effect = [
            Mock(returncode=0, stdout="myapp_backend\nmyapp_frontend\n"),  # list_projects
            Mock(returncode=0),  # docker compose down
            Mock(returncode=0, stdout=""),  # _find_orphaned_containers (labels)
            Mock(returncode=0, stdout=""),  # _find_orphaned_containers (patterns)
        ]

        proxy = ProxyManager()
        proxy.stop_all_projects()

        # Should have called: list_projects, compose down, and 2 orphan checks
        assert mock_run.call_count == 4

    @patch("subprocess.run")
    def test_stop_all_projects_with_no_projects(self, mock_run):
        """Test stopping all projects when none are running."""
        # list_projects returns empty, then orphan checks return empty
        mock_run.side_effect = [
            Mock(returncode=0, stdout=""),  # list_projects
            Mock(returncode=0, stdout=""),  # _find_orphaned_containers (labels)
            Mock(returncode=0, stdout=""),  # _find_orphaned_containers (patterns)
        ]

        proxy = ProxyManager()
        proxy.stop_all_projects()

        # Should call list_projects and 2 orphan checks
        assert mock_run.call_count == 3

    @patch("prisme.docker.proxy.Template")
    def test_get_config_path_creates_from_template(self, mock_template_class):
        """Test _get_config_path creates config from template."""
        mock_template = MagicMock()
        mock_template.render.return_value = "api:\n  dashboard: true"
        mock_template_class.return_value = mock_template

        with patch("prisme.docker.proxy.Path") as mock_path_class:
            mock_config_dir = MagicMock()
            mock_config_file = MagicMock()
            mock_config_dir.__truediv__ = lambda self, other: mock_config_file

            mock_home = MagicMock()
            mock_home.__truediv__ = lambda self, other: mock_config_dir

            mock_path_class.home.return_value = mock_home

            # Template path exists
            mock_template_path = MagicMock()
            mock_template_path.exists.return_value = True
            mock_template_path.read_text.return_value = "api:\n  dashboard: true"
            mock_path_class.return_value.__truediv__ = MagicMock(return_value=mock_template_path)

            config_path = ProxyManager._get_config_path()

            assert config_path is not None
            mock_template.render.assert_called_once()

    @patch("prisme.docker.proxy.Template")
    def test_get_config_path_returns_existing(self, mock_template_class):
        """Test _get_config_path returns existing config."""
        mock_template = MagicMock()
        mock_template.render.return_value = "api:\n  dashboard: true"
        mock_template_class.return_value = mock_template

        with patch("prisme.docker.proxy.Path") as mock_path_class:
            mock_config_dir = MagicMock()
            mock_config_file = MagicMock()
            mock_config_file.exists.return_value = True
            mock_config_dir.__truediv__ = lambda self, other: mock_config_file

            mock_home = MagicMock()
            mock_home.__truediv__ = lambda self, other: mock_config_dir

            mock_path_class.home.return_value = mock_home

            # Template path exists
            mock_template_path = MagicMock()
            mock_template_path.exists.return_value = True
            mock_template_path.read_text.return_value = "api:\n  dashboard: true"
            mock_path_class.return_value.__truediv__ = MagicMock(return_value=mock_template_path)

            config_path = ProxyManager._get_config_path()

            assert config_path is not None


class TestProjectInfo:
    """Test ProjectInfo dataclass."""

    def test_project_info_creation(self):
        """Test creating ProjectInfo."""
        project = ProjectInfo(name="myapp", services=["backend", "frontend", "db"])

        assert project.name == "myapp"
        assert len(project.services) == 3
        assert "backend" in project.services

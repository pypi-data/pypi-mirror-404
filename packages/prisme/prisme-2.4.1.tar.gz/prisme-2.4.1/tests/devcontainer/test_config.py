"""Tests for WorkspaceConfig."""

from pathlib import Path
from unittest.mock import patch

from prisme.devcontainer.config import (
    WorkspaceConfig,
    WorkspaceInfo,
    normalize_workspace_name,
)


class TestNormalizeWorkspaceName:
    """Tests for the normalize_workspace_name function."""

    def test_lowercase(self) -> None:
        """Test that names are lowercased."""
        assert normalize_workspace_name("MyProject") == "myproject"

    def test_slashes_to_hyphens(self) -> None:
        """Test that slashes are converted to hyphens."""
        assert normalize_workspace_name("feature/my-branch") == "feature-my-branch"

    def test_underscores_to_hyphens(self) -> None:
        """Test that underscores are converted to hyphens."""
        assert normalize_workspace_name("my_project_name") == "my-project-name"

    def test_removes_special_chars(self) -> None:
        """Test that special characters are removed."""
        assert normalize_workspace_name("my@project!") == "myproject"

    def test_collapses_multiple_hyphens(self) -> None:
        """Test that multiple hyphens are collapsed."""
        assert normalize_workspace_name("my--project---name") == "my-project-name"

    def test_strips_leading_trailing_hyphens(self) -> None:
        """Test that leading/trailing hyphens are stripped."""
        assert normalize_workspace_name("-my-project-") == "my-project"

    def test_max_length_63(self) -> None:
        """Test that names are truncated to 63 characters (DNS limit)."""
        long_name = "a" * 100
        result = normalize_workspace_name(long_name)
        assert len(result) == 63

    def test_complex_branch_name(self) -> None:
        """Test normalizing a complex branch name."""
        assert normalize_workspace_name("feature/JIRA-123_add-auth") == "feature-jira-123-add-auth"


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig dataclass."""

    def test_basic_creation(self, tmp_path: Path) -> None:
        """Test basic config creation with required fields."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.project_name == "myproject"
        assert config.project_dir == tmp_path
        # Workspace name is auto-generated
        assert config.workspace_name is not None

    @patch("prisme.devcontainer.config.get_current_branch")
    def test_auto_workspace_name_with_branch(self, mock_branch: patch, tmp_path: Path) -> None:
        """Test that workspace name includes branch when available."""
        mock_branch.return_value = "feature/add-auth"
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.workspace_name == "myproject-feature-add-auth"

    @patch("prisme.devcontainer.config.get_current_branch")
    def test_auto_workspace_name_without_branch(self, mock_branch: patch, tmp_path: Path) -> None:
        """Test that workspace name is just project name when no branch."""
        mock_branch.return_value = None
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.workspace_name == "myproject"

    def test_custom_workspace_name(self, tmp_path: Path) -> None:
        """Test custom workspace name is used and normalized."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
            workspace_name="my-custom-workspace",
        )
        assert config.workspace_name == "my-custom-workspace"

    def test_database_name_property(self, tmp_path: Path) -> None:
        """Test database name replaces hyphens with underscores."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
            workspace_name="my-project-main",
        )
        assert config.database_name == "my_project_main"

    def test_hostname_property(self, tmp_path: Path) -> None:
        """Test hostname is same as workspace name."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
            workspace_name="my-project-main",
        )
        assert config.hostname == "my-project-main"

    def test_devcontainer_dir_property(self, tmp_path: Path) -> None:
        """Test devcontainer_dir returns correct path."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.devcontainer_dir == tmp_path / ".devcontainer"

    def test_env_file_property(self, tmp_path: Path) -> None:
        """Test env_file returns correct path."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.env_file == tmp_path / ".devcontainer" / ".env"

    def test_compose_file_property(self, tmp_path: Path) -> None:
        """Test compose_file returns correct path."""
        config = WorkspaceConfig(
            project_name="myproject",
            project_dir=tmp_path,
        )
        assert config.compose_file == tmp_path / ".devcontainer" / "docker-compose.yml"

    def test_from_directory_basic(self, tmp_path: Path) -> None:
        """Test creating config from directory."""
        config = WorkspaceConfig.from_directory(project_dir=tmp_path)
        assert config.project_name == tmp_path.name
        assert config.project_dir == tmp_path

    def test_from_directory_detects_frontend(self, tmp_path: Path) -> None:
        """Test that frontend path is detected."""
        (tmp_path / "packages" / "frontend").mkdir(parents=True)
        (tmp_path / "packages" / "frontend" / "package.json").write_text("{}")

        config = WorkspaceConfig.from_directory(project_dir=tmp_path)
        assert config.frontend_path == "packages/frontend"

    def test_from_directory_detects_spec(self, tmp_path: Path) -> None:
        """Test that spec path is detected."""
        (tmp_path / "specs").mkdir()
        (tmp_path / "specs" / "models.py").write_text("# models")

        config = WorkspaceConfig.from_directory(project_dir=tmp_path)
        assert config.spec_path == "specs/models.py"

    def test_from_directory_custom_workspace_name(self, tmp_path: Path) -> None:
        """Test creating config with custom workspace name."""
        config = WorkspaceConfig.from_directory(
            project_dir=tmp_path,
            workspace_name="custom-workspace",
        )
        assert config.workspace_name == "custom-workspace"

    def test_from_directory_include_redis(self, tmp_path: Path) -> None:
        """Test creating config with Redis enabled."""
        config = WorkspaceConfig.from_directory(
            project_dir=tmp_path,
            include_redis=True,
        )
        assert config.include_redis is True


class TestWorkspaceInfo:
    """Tests for WorkspaceInfo dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic info creation."""
        info = WorkspaceInfo(
            workspace_name="myproject-main",
            status="running",
        )
        assert info.workspace_name == "myproject-main"
        assert info.status == "running"
        assert info.services == []
        assert info.url == ""

    def test_with_all_fields(self) -> None:
        """Test info creation with all fields."""
        info = WorkspaceInfo(
            workspace_name="myproject-main",
            status="running",
            services=["app", "db"],
            url="http://myproject-main.localhost",
            project_dir="/home/user/myproject",
        )
        assert info.services == ["app", "db"]
        assert info.url == "http://myproject-main.localhost"
        assert info.project_dir == "/home/user/myproject"

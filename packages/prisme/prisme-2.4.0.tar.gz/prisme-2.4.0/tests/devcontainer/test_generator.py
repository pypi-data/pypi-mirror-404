"""Tests for DevContainerGenerator."""

from pathlib import Path

import pytest

from prisme.devcontainer.config import WorkspaceConfig
from prisme.devcontainer.generator import DevContainerGenerator


class TestDevContainerGenerator:
    """Tests for DevContainerGenerator class."""

    @pytest.fixture
    def generator(self) -> DevContainerGenerator:
        """Create a generator instance for testing."""
        return DevContainerGenerator()

    @pytest.fixture
    def config(self, tmp_path: Path) -> WorkspaceConfig:
        """Create a test configuration."""
        return WorkspaceConfig(
            project_name="testproject",
            project_dir=tmp_path,
            workspace_name="testproject-main",
            frontend_path="packages/frontend",
            spec_path="specs/models.py",
        )

    def test_generate_creates_devcontainer_dir(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that generate creates .devcontainer directory."""
        generator.generate(config)

        assert config.devcontainer_dir.exists()
        assert config.devcontainer_dir.is_dir()

    def test_generate_creates_devcontainer_json(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that devcontainer.json is created."""
        generator.generate(config)

        devcontainer_json = config.devcontainer_dir / "devcontainer.json"
        assert devcontainer_json.exists()
        content = devcontainer_json.read_text()
        assert "dockerComposeFile" in content

    def test_generate_creates_docker_compose(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that docker-compose.yml is created."""
        generator.generate(config)

        compose_file = config.devcontainer_dir / "docker-compose.yml"
        assert compose_file.exists()
        content = compose_file.read_text()
        assert "app:" in content
        assert "db:" in content

    def test_generate_creates_dockerfile(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that Dockerfile.dev is created."""
        generator.generate(config)

        dockerfile = config.devcontainer_dir / "Dockerfile.dev"
        assert dockerfile.exists()
        content = dockerfile.read_text()
        assert "FROM mcr.microsoft.com/devcontainers/python" in content

    def test_generate_creates_env_template(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that .env.template is created."""
        generator.generate(config)

        env_template = config.devcontainer_dir / ".env.template"
        assert env_template.exists()
        content = env_template.read_text()
        assert "WORKSPACE_NAME" in content

    def test_generate_creates_setup_script(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that setup.sh is created with executable permissions."""
        generator.generate(config)

        setup_script = config.devcontainer_dir / "setup.sh"
        assert setup_script.exists()
        content = setup_script.read_text()
        assert "#!/bin/bash" in content
        # Check it's executable
        import stat

        mode = setup_script.stat().st_mode
        assert mode & stat.S_IXUSR  # User execute permission

    def test_generate_updates_gitignore(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that .gitignore is updated to exclude .devcontainer/.env."""
        generator.generate(config)

        gitignore = config.project_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".devcontainer/.env" in content

    def test_generate_appends_to_existing_gitignore(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that existing .gitignore is appended to, not overwritten."""
        gitignore = config.project_dir / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n")

        generator.generate(config)

        content = gitignore.read_text()
        assert "*.pyc" in content  # Original content preserved
        assert ".devcontainer/.env" in content  # New entry added

    def test_generate_env_creates_env_file(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that generate_env creates .env file."""
        config.devcontainer_dir.mkdir(parents=True)

        generator.generate_env(config)

        assert config.env_file.exists()
        content = config.env_file.read_text()
        assert f"WORKSPACE_NAME={config.workspace_name}" in content
        assert f"DATABASE_NAME={config.database_name}" in content

    def test_generate_env_uses_workspace_config(
        self, generator: DevContainerGenerator, config: WorkspaceConfig
    ) -> None:
        """Test that .env file uses values from config."""
        config.devcontainer_dir.mkdir(parents=True)

        generator.generate_env(config)

        content = config.env_file.read_text()
        assert "WORKSPACE_NAME=testproject-main" in content
        assert "COMPOSE_PROJECT_NAME=testproject-main" in content
        assert "DATABASE_NAME=testproject_main" in content


class TestDevContainerGeneratorWithRedis:
    """Tests for generator with Redis enabled."""

    @pytest.fixture
    def generator(self) -> DevContainerGenerator:
        """Create a generator instance for testing."""
        return DevContainerGenerator()

    @pytest.fixture
    def config_with_redis(self, tmp_path: Path) -> WorkspaceConfig:
        """Create a test configuration with Redis."""
        return WorkspaceConfig(
            project_name="testproject",
            project_dir=tmp_path,
            workspace_name="testproject-main",
            include_redis=True,
        )

    def test_generate_includes_redis_in_compose(
        self, generator: DevContainerGenerator, config_with_redis: WorkspaceConfig
    ) -> None:
        """Test that docker-compose includes Redis when enabled."""
        generator.generate(config_with_redis)

        compose_file = config_with_redis.devcontainer_dir / "docker-compose.yml"
        content = compose_file.read_text()
        assert "redis:" in content

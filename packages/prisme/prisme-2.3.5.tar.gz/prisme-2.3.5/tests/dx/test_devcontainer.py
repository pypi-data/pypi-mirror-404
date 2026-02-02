"""Tests for dev container configuration generation."""

import json
import tempfile
from pathlib import Path

import pytest

from prisme.dx.devcontainer import DevContainerConfig, DevContainerGenerator


class TestDevContainerConfig:
    """Test DevContainerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = DevContainerConfig(
            project_name="test_project",
            include_frontend=False,
        )
        assert config.python_version == "3.13"
        assert config.node_version == "22"
        assert config.include_postgres is True
        assert config.include_redis is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = DevContainerConfig(
            project_name="test_project",
            include_frontend=True,
            python_version="3.12",
            node_version="20",
            include_postgres=False,
            include_redis=True,
        )
        assert config.python_version == "3.12"
        assert config.node_version == "20"
        assert config.include_postgres is False
        assert config.include_redis is True


class TestDevContainerGenerator:
    """Test dev container configuration generation."""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self) -> DevContainerConfig:
        """Create a basic configuration for testing."""
        return DevContainerConfig(
            project_name="testproject",
            include_frontend=False,
            include_postgres=True,
        )

    @pytest.fixture
    def frontend_config(self) -> DevContainerConfig:
        """Create a configuration with frontend enabled."""
        return DevContainerConfig(
            project_name="testproject",
            include_frontend=True,
            include_postgres=True,
        )

    def test_generator_creates_devcontainer_dir(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that generator creates .devcontainer directory."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        devcontainer_dir = temp_project_dir / ".devcontainer"
        assert devcontainer_dir.exists()

    def test_generator_creates_devcontainer_json(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that generator creates devcontainer.json."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        json_file = temp_project_dir / ".devcontainer" / "devcontainer.json"
        assert json_file.exists()

        with json_file.open() as f:
            config = json.load(f)
            assert config["name"] == "testproject"

    def test_generator_creates_dockerfile(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that generator creates Dockerfile."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        dockerfile = temp_project_dir / ".devcontainer" / "Dockerfile"
        assert dockerfile.exists()

        content = dockerfile.read_text()
        assert "python" in content.lower()
        assert "uv" in content

    def test_devcontainer_includes_python_extensions(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that devcontainer.json includes Python extensions."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        json_file = temp_project_dir / ".devcontainer" / "devcontainer.json"
        with json_file.open() as f:
            config = json.load(f)
            extensions = config["customizations"]["vscode"]["extensions"]
            assert "ms-python.python" in extensions
            assert "ms-python.vscode-pylance" in extensions
            assert "charliermarsh.ruff" in extensions

    def test_devcontainer_includes_frontend_extensions_when_enabled(
        self,
        temp_project_dir: Path,
        frontend_config: DevContainerConfig,
    ) -> None:
        """Test that frontend extensions are included when frontend is enabled."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(frontend_config)

        json_file = temp_project_dir / ".devcontainer" / "devcontainer.json"
        with json_file.open() as f:
            config = json.load(f)
            extensions = config["customizations"]["vscode"]["extensions"]
            assert "dbaeumer.vscode-eslint" in extensions
            assert "esbenp.prettier-vscode" in extensions
            assert "bradlc.vscode-tailwindcss" in extensions

    def test_devcontainer_excludes_frontend_extensions_when_disabled(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that frontend extensions are excluded when frontend is disabled."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        json_file = temp_project_dir / ".devcontainer" / "devcontainer.json"
        with json_file.open() as f:
            config = json.load(f)
            extensions = config["customizations"]["vscode"]["extensions"]
            assert "dbaeumer.vscode-eslint" not in extensions
            assert "esbenp.prettier-vscode" not in extensions

    def test_devcontainer_forwards_correct_ports(
        self,
        temp_project_dir: Path,
        frontend_config: DevContainerConfig,
    ) -> None:
        """Test that correct ports are forwarded."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(frontend_config)

        json_file = temp_project_dir / ".devcontainer" / "devcontainer.json"
        with json_file.open() as f:
            config = json.load(f)
            ports = config["forwardPorts"]
            assert 8000 in ports  # Backend
            assert 5173 in ports  # Frontend (Vite)
            assert 5432 in ports  # PostgreSQL

    def test_dockerfile_includes_node_when_frontend_enabled(
        self,
        temp_project_dir: Path,
        frontend_config: DevContainerConfig,
    ) -> None:
        """Test that Dockerfile includes Node.js when frontend is enabled."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(frontend_config)

        dockerfile = temp_project_dir / ".devcontainer" / "Dockerfile"
        content = dockerfile.read_text()
        assert "nodejs" in content.lower() or "node" in content.lower()
        assert "pnpm" in content

    def test_dockerfile_excludes_node_when_frontend_disabled(
        self,
        temp_project_dir: Path,
        basic_config: DevContainerConfig,
    ) -> None:
        """Test that Dockerfile excludes Node.js when frontend is disabled."""
        generator = DevContainerGenerator(temp_project_dir)
        generator.generate(basic_config)

        dockerfile = temp_project_dir / ".devcontainer" / "Dockerfile"
        content = dockerfile.read_text()
        assert "pnpm" not in content

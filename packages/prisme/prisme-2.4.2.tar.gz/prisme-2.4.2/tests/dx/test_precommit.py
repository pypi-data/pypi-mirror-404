"""Tests for pre-commit hooks generation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from prisme.dx.precommit import PreCommitConfig, PreCommitGenerator


class TestPreCommitConfig:
    """Test PreCommitConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = PreCommitConfig(
            project_name="test_project",
            include_frontend=False,
        )
        assert config.python_manager == "uv"
        assert config.enable_mypy is True
        assert config.enable_pytest is True
        assert config.enable_ruff is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = PreCommitConfig(
            project_name="test_project",
            include_frontend=True,
            python_manager="poetry",
            enable_mypy=False,
            enable_pytest=False,
            enable_ruff=True,
        )
        assert config.python_manager == "poetry"
        assert config.enable_mypy is False
        assert config.enable_pytest is False


class TestPreCommitGenerator:
    """Test pre-commit hooks generation."""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self) -> PreCommitConfig:
        """Create a basic configuration for testing."""
        return PreCommitConfig(
            project_name="testproject",
            include_frontend=False,
            enable_mypy=True,
            enable_pytest=True,
            enable_ruff=True,
        )

    @pytest.fixture
    def frontend_config(self) -> PreCommitConfig:
        """Create a configuration with frontend enabled."""
        return PreCommitConfig(
            project_name="testproject",
            include_frontend=True,
            enable_mypy=True,
            enable_pytest=True,
            enable_ruff=True,
        )

    def test_generator_creates_precommit_config(
        self,
        temp_project_dir: Path,
        basic_config: PreCommitConfig,
    ) -> None:
        """Test that generator creates .pre-commit-config.yaml."""
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(basic_config)

        config_file = temp_project_dir / ".pre-commit-config.yaml"
        assert config_file.exists()

        with config_file.open() as f:
            config = yaml.safe_load(f)
            assert "repos" in config

    def test_precommit_includes_ruff_hooks(
        self,
        temp_project_dir: Path,
        basic_config: PreCommitConfig,
    ) -> None:
        """Test that pre-commit config includes ruff hooks."""
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(basic_config)

        content = (temp_project_dir / ".pre-commit-config.yaml").read_text()
        assert "ruff" in content
        assert "ruff-format" in content

    def test_precommit_includes_prepush_hooks(
        self,
        temp_project_dir: Path,
        basic_config: PreCommitConfig,
    ) -> None:
        """Test that pre-commit config includes pre-push hooks."""
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(basic_config)

        content = (temp_project_dir / ".pre-commit-config.yaml").read_text()
        assert "pre-push" in content
        assert "mypy" in content
        assert "pytest" in content

    def test_precommit_uses_python_manager(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test that pre-commit config uses the specified python manager."""
        config = PreCommitConfig(
            project_name="testproject",
            include_frontend=False,
            python_manager="poetry",
        )
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(config)

        content = (temp_project_dir / ".pre-commit-config.yaml").read_text()
        assert "poetry run" in content

    def test_precommit_includes_frontend_hooks_when_enabled(
        self,
        temp_project_dir: Path,
        frontend_config: PreCommitConfig,
    ) -> None:
        """Test that frontend hooks are included when frontend is enabled."""
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(frontend_config)

        content = (temp_project_dir / ".pre-commit-config.yaml").read_text()
        assert "eslint" in content

    def test_precommit_excludes_frontend_hooks_when_disabled(
        self,
        temp_project_dir: Path,
        basic_config: PreCommitConfig,
    ) -> None:
        """Test that frontend hooks are excluded when frontend is disabled."""
        generator = PreCommitGenerator(temp_project_dir)
        generator.generate(basic_config)

        content = (temp_project_dir / ".pre-commit-config.yaml").read_text()
        assert "eslint" not in content

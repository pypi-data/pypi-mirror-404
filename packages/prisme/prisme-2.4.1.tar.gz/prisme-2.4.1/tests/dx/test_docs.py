"""Tests for documentation setup generation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from prisme.dx.docs import DocsConfig, DocsGenerator


class TestDocsConfig:
    """Test DocsConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = DocsConfig(
            project_name="test_project",
            project_title="Test Project",
            description="A test project",
        )
        assert config.include_api_docs is True
        assert config.include_readthedocs is True
        assert config.theme == "material"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = DocsConfig(
            project_name="test_project",
            project_title="Test Project",
            description="A test project",
            include_api_docs=False,
            include_readthedocs=False,
            theme="readthedocs",
        )
        assert config.include_api_docs is False
        assert config.include_readthedocs is False
        assert config.theme == "readthedocs"


class TestDocsGenerator:
    """Test documentation setup generation."""

    @pytest.fixture
    def temp_project_dir(self) -> Path:
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self) -> DocsConfig:
        """Create a basic configuration for testing."""
        return DocsConfig(
            project_name="testproject",
            project_title="Test Project",
            description="A test project description",
            include_api_docs=True,
            include_readthedocs=True,
        )

    def test_generator_creates_mkdocs_config(
        self,
        temp_project_dir: Path,
        basic_config: DocsConfig,
    ) -> None:
        """Test that generator creates mkdocs.yml."""
        generator = DocsGenerator(temp_project_dir)
        generator.generate(basic_config)

        mkdocs_file = temp_project_dir / "mkdocs.yml"
        assert mkdocs_file.exists()

        with mkdocs_file.open() as f:
            config = yaml.safe_load(f)
            assert config["site_name"] == "Test Project"
            assert config["site_description"] == "A test project description"

    def test_generator_creates_docs_structure(
        self,
        temp_project_dir: Path,
        basic_config: DocsConfig,
    ) -> None:
        """Test that generator creates docs folder structure."""
        generator = DocsGenerator(temp_project_dir)
        generator.generate(basic_config)

        docs_dir = temp_project_dir / "docs"
        assert docs_dir.exists()
        assert (docs_dir / "index.md").exists()
        assert (docs_dir / "getting-started" / "index.md").exists()
        assert (docs_dir / "user-guide" / "index.md").exists()
        assert (docs_dir / "reference" / "index.md").exists()

    def test_generator_creates_readthedocs_config(
        self,
        temp_project_dir: Path,
        basic_config: DocsConfig,
    ) -> None:
        """Test that generator creates .readthedocs.yaml."""
        generator = DocsGenerator(temp_project_dir)
        generator.generate(basic_config)

        rtd_file = temp_project_dir / ".readthedocs.yaml"
        assert rtd_file.exists()

        with rtd_file.open() as f:
            config = yaml.safe_load(f)
            assert config["version"] == 2
            assert "mkdocs" in config

    def test_generator_creates_requirements_txt(
        self,
        temp_project_dir: Path,
        basic_config: DocsConfig,
    ) -> None:
        """Test that generator creates docs/requirements.txt."""
        generator = DocsGenerator(temp_project_dir)
        generator.generate(basic_config)

        requirements_file = temp_project_dir / "docs" / "requirements.txt"
        assert requirements_file.exists()

        content = requirements_file.read_text()
        assert "mkdocs" in content
        assert "mkdocs-material" in content

    def test_generator_skips_readthedocs_when_disabled(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test that .readthedocs.yaml is not created when disabled."""
        config = DocsConfig(
            project_name="testproject",
            project_title="Test Project",
            description="A test project",
            include_readthedocs=False,
        )
        generator = DocsGenerator(temp_project_dir)
        generator.generate(config)

        rtd_file = temp_project_dir / ".readthedocs.yaml"
        assert not rtd_file.exists()

    def test_mkdocs_includes_mkdocstrings_when_api_docs_enabled(
        self,
        temp_project_dir: Path,
        basic_config: DocsConfig,
    ) -> None:
        """Test that mkdocstrings is included when API docs are enabled."""
        generator = DocsGenerator(temp_project_dir)
        generator.generate(basic_config)

        content = (temp_project_dir / "mkdocs.yml").read_text()
        assert "mkdocstrings" in content

    def test_mkdocs_excludes_mkdocstrings_when_api_docs_disabled(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test that mkdocstrings is excluded when API docs are disabled."""
        config = DocsConfig(
            project_name="testproject",
            project_title="Test Project",
            description="A test project",
            include_api_docs=False,
        )
        generator = DocsGenerator(temp_project_dir)
        generator.generate(config)

        content = (temp_project_dir / "mkdocs.yml").read_text()
        assert "mkdocstrings" not in content

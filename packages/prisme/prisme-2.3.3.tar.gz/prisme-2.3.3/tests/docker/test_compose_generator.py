"""Tests for Docker Compose configuration generator."""

import tempfile
from pathlib import Path

import pytest

from prisme.docker import ComposeConfig, ComposeGenerator


class TestComposeConfig:
    """Tests for ComposeConfig dataclass."""

    def test_default_ports(self):
        """Test that default ports are set correctly."""
        config = ComposeConfig(
            project_name="test_project",
            backend_path="backend",
            frontend_path="frontend",
            backend_module="backend",
        )

        assert config.backend_port == 8000
        assert config.frontend_port == 5173
        assert config.db_port == 5432
        assert config.redis_port == 6379
        assert config.use_redis is False

    def test_custom_ports(self):
        """Test that custom ports can be set."""
        config = ComposeConfig(
            project_name="test_project",
            backend_path="backend",
            frontend_path="frontend",
            backend_module="backend",
            backend_port=9000,
            frontend_port=4000,
            db_port=5433,
            redis_port=6380,
            use_redis=True,
        )

        assert config.backend_port == 9000
        assert config.frontend_port == 4000
        assert config.db_port == 5433
        assert config.redis_port == 6380
        assert config.use_redis is True


class TestComposeGenerator:
    """Tests for ComposeGenerator."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        """Create a basic ComposeConfig for testing."""
        return ComposeConfig(
            project_name="test_app",
            backend_path="backend",
            frontend_path="frontend",
            backend_module="backend",
        )

    @pytest.fixture
    def config_with_redis(self):
        """Create a ComposeConfig with Redis enabled."""
        return ComposeConfig(
            project_name="test_app",
            backend_path="backend",
            frontend_path="frontend",
            backend_module="backend",
            use_redis=True,
        )

    def test_generator_initialization(self, temp_project_dir):
        """Test that ComposeGenerator initializes correctly."""
        generator = ComposeGenerator(temp_project_dir)

        assert generator.project_dir == temp_project_dir
        assert generator.templates_dir.exists()
        assert (generator.templates_dir / "docker-compose.dev.yml.jinja2").exists()

    def test_generate_creates_all_files(self, temp_project_dir, basic_config):
        """Test that generate() creates all required files."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(basic_config)

        assert (temp_project_dir / "docker-compose.dev.yml").exists()
        assert (temp_project_dir / "Dockerfile.backend").exists()
        assert (temp_project_dir / "Dockerfile.frontend").exists()
        assert (temp_project_dir / ".dockerignore").exists()

    def test_docker_compose_content_without_redis(self, temp_project_dir, basic_config):
        """Test docker-compose.yml content when Redis is not enabled."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(basic_config)

        compose_content = (temp_project_dir / "docker-compose.dev.yml").read_text()

        # Check that required services are present
        assert "backend:" in compose_content
        assert "frontend:" in compose_content
        assert "db:" in compose_content

        # Check that Redis is NOT present
        assert "redis:" not in compose_content

        # Check project name is used
        assert "test_app" in compose_content

        # Check health checks are present
        assert "healthcheck:" in compose_content

    def test_docker_compose_content_with_redis(self, temp_project_dir, config_with_redis):
        """Test docker-compose.yml content when Redis is enabled."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(config_with_redis)

        compose_content = (temp_project_dir / "docker-compose.dev.yml").read_text()

        # Check that all services including Redis are present
        assert "backend:" in compose_content
        assert "frontend:" in compose_content
        assert "db:" in compose_content
        assert "redis:" in compose_content

        # Check Redis environment variable is set
        assert "REDIS_URL" in compose_content

        # Check Redis volume is created
        assert "test_app_redis_data:" in compose_content

    def test_backend_dockerfile_content(self, temp_project_dir, basic_config):
        """Test Dockerfile.backend content."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(basic_config)

        dockerfile_content = (temp_project_dir / "Dockerfile.backend").read_text()

        # Check Python version
        assert "python:3.13" in dockerfile_content

        # Check working directory
        assert "WORKDIR /app" in dockerfile_content

        # Check that backend path is used
        assert "backend" in dockerfile_content

        # Check that backend module is used
        assert "backend.main:app" in dockerfile_content

        # Check uvicorn is used
        assert "uvicorn" in dockerfile_content

    def test_frontend_dockerfile_content(self, temp_project_dir, basic_config):
        """Test Dockerfile.frontend content."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(basic_config)

        dockerfile_content = (temp_project_dir / "Dockerfile.frontend").read_text()

        # Check Node version
        assert "node:22" in dockerfile_content

        # Check working directory
        assert "WORKDIR /app" in dockerfile_content

        # Check that frontend path is used
        assert "frontend" in dockerfile_content

        # Check npm is used
        assert "npm" in dockerfile_content

    def test_dockerignore_content(self, temp_project_dir, basic_config):
        """Test .dockerignore content."""
        generator = ComposeGenerator(temp_project_dir)
        generator.generate(basic_config)

        dockerignore_content = (temp_project_dir / ".dockerignore").read_text()

        # Check common ignore patterns
        assert "__pycache__" in dockerignore_content
        assert "node_modules" in dockerignore_content
        assert ".venv" in dockerignore_content
        assert ".git" in dockerignore_content
        assert ".prisme" in dockerignore_content
        assert ".env" in dockerignore_content

    def test_custom_ports_in_compose_file(self, temp_project_dir):
        """Test that custom ports are used in docker-compose.yml."""
        config = ComposeConfig(
            project_name="test_app",
            backend_path="backend",
            frontend_path="frontend",
            backend_module="backend",
            backend_port=9000,
            frontend_port=4000,
            db_port=5433,
        )

        generator = ComposeGenerator(temp_project_dir)
        generator.generate(config)

        compose_content = (temp_project_dir / "docker-compose.dev.yml").read_text()

        # Check custom ports (both host and container use the same port)
        assert "9000:9000" in compose_content
        assert "4000:4000" in compose_content
        # Database port is commented out by default (only needed for debugging)
        assert "${DB_PORT:-5433}:5432" in compose_content
        # Check port is used in commands and healthchecks
        assert "--port 9000" in compose_content
        assert "localhost:9000" in compose_content

    def test_custom_paths_in_files(self, temp_project_dir):
        """Test that custom backend/frontend paths are used."""
        config = ComposeConfig(
            project_name="test_app",
            backend_path="packages/backend",
            frontend_path="packages/frontend",
            backend_module="packages.backend.src",
        )

        generator = ComposeGenerator(temp_project_dir)
        generator.generate(config)

        # Check docker-compose.yml
        compose_content = (temp_project_dir / "docker-compose.dev.yml").read_text()
        assert "packages/backend" in compose_content
        assert "packages/frontend" in compose_content

        # Check Dockerfile.backend
        backend_dockerfile = (temp_project_dir / "Dockerfile.backend").read_text()
        assert "packages/backend" in backend_dockerfile
        assert "packages.backend.src.main:app" in backend_dockerfile

        # Check Dockerfile.frontend
        frontend_dockerfile = (temp_project_dir / "Dockerfile.frontend").read_text()
        assert "packages/frontend" in frontend_dockerfile

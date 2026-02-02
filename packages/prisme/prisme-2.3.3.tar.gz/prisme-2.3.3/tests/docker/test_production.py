"""Tests for production Docker configuration generation."""

import pytest

from prisme.docker import ProductionComposeGenerator, ProductionConfig


class TestProductionConfig:
    """Test ProductionConfig dataclass."""

    def test_default_values(self):
        """Test ProductionConfig with default values."""
        config = ProductionConfig(
            project_name="testapp",
            use_redis=False,
        )

        assert config.project_name == "testapp"
        assert config.use_redis is False
        assert config.domain == ""
        assert config.ssl_enabled is False
        assert config.backend_replicas == 2
        assert config.enable_monitoring is False

    def test_custom_values(self):
        """Test ProductionConfig with custom values."""
        config = ProductionConfig(
            project_name="myapp",
            use_redis=True,
            domain="myapp.com",
            ssl_enabled=True,
            backend_replicas=4,
            enable_monitoring=True,
        )

        assert config.project_name == "myapp"
        assert config.use_redis is True
        assert config.domain == "myapp.com"
        assert config.ssl_enabled is True
        assert config.backend_replicas == 4
        assert config.enable_monitoring is True


class TestProductionComposeGenerator:
    """Test ProductionComposeGenerator."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project directory."""
        project_dir = tmp_path / "testproject"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def config_no_redis(self):
        """Create config without Redis."""
        return ProductionConfig(
            project_name="testapp",
            use_redis=False,
        )

    @pytest.fixture
    def config_with_redis(self):
        """Create config with Redis."""
        return ProductionConfig(
            project_name="testapp",
            use_redis=True,
            domain="testapp.com",
            ssl_enabled=True,
            backend_replicas=3,
        )

    def test_generator_initialization(self, temp_project):
        """Test generator initialization."""
        generator = ProductionComposeGenerator(temp_project)
        assert generator.project_dir == temp_project

    def test_generate_backend_dockerfile(self, temp_project, config_no_redis):
        """Test backend Dockerfile generation."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_backend_dockerfile(config_no_redis)

        dockerfile = temp_project / "Dockerfile.backend.prod"
        assert dockerfile.exists()

        content = dockerfile.read_text()
        assert "FROM python:3.13-slim AS builder" in content
        assert "FROM python:3.13-slim" in content
        assert "groupadd -r appuser" in content
        assert "USER appuser" in content
        assert "HEALTHCHECK" in content
        assert "uvicorn" in content

    def test_generate_frontend_dockerfile(self, temp_project, config_no_redis):
        """Test frontend Dockerfile generation."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_frontend_dockerfile(config_no_redis)

        dockerfile = temp_project / "Dockerfile.frontend.prod"
        assert dockerfile.exists()

        content = dockerfile.read_text()
        assert "FROM node:22-alpine AS builder" in content
        assert "FROM nginx:alpine" in content
        assert "npm run build" in content
        assert "USER nginx" in content
        assert "HEALTHCHECK" in content

    def test_generate_nginx_config_without_ssl(self, temp_project, config_no_redis):
        """Test nginx config generation without SSL."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_nginx_config(config_no_redis)

        nginx_conf = temp_project / "nginx.conf"
        assert nginx_conf.exists()

        content = nginx_conf.read_text()
        assert "worker_processes auto" in content
        assert "gzip on" in content
        assert "X-Frame-Options" in content
        assert "try_files $uri $uri/ @frontend" in content
        assert "/health" in content

    def test_generate_nginx_config_with_ssl(self, temp_project, config_with_redis):
        """Test nginx config generation with SSL."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_nginx_config(config_with_redis)

        nginx_conf = temp_project / "nginx.conf"
        assert nginx_conf.exists()

        content = nginx_conf.read_text()
        assert "testapp.com" in content or "server_name" in content

    def test_generate_compose_file_no_redis(self, temp_project, config_no_redis):
        """Test compose file generation without Redis."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_compose_file(config_no_redis)

        compose_file = temp_project / "docker-compose.prod.yml"
        assert compose_file.exists()

        content = compose_file.read_text()
        assert "services:" in content
        assert "backend:" in content
        assert "frontend:" in content
        assert "db:" in content
        assert "nginx:" in content
        assert "Dockerfile.backend.prod" in content
        assert "Dockerfile.frontend.prod" in content
        assert "postgres:16-alpine" in content
        assert "nginx:alpine" in content
        assert "replicas: 2" in content
        assert "memory: 512M" in content

        # Redis should not be present
        assert "redis:" not in content

    def test_generate_compose_file_with_redis(self, temp_project, config_with_redis):
        """Test compose file generation with Redis."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_compose_file(config_with_redis)

        compose_file = temp_project / "docker-compose.prod.yml"
        assert compose_file.exists()

        content = compose_file.read_text()
        assert "redis:" in content
        assert "redis:7-alpine" in content
        assert "replicas: 3" in content

    def test_generate_env_example(self, temp_project, config_with_redis):
        """Test .env.prod.example generation."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_env_example(config_with_redis)

        env_file = temp_project / ".env.prod.example"
        assert env_file.exists()

        content = env_file.read_text()
        assert "PROJECT_NAME=testapp" in content
        assert "DB_USER=postgres" in content
        assert "SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE" in content
        assert "ALLOWED_HOSTS=" in content
        assert "REDIS_URL=redis://redis:6379/0" in content
        assert "HTTP_PORT=80" in content
        assert "HTTPS_PORT=443" in content

    def test_full_generation_no_redis(self, temp_project, config_no_redis):
        """Test full generation without Redis."""
        generator = ProductionComposeGenerator(temp_project)
        generator.generate(config_no_redis)

        # Check all files were created
        assert (temp_project / "Dockerfile.backend.prod").exists()
        assert (temp_project / "Dockerfile.frontend.prod").exists()
        assert (temp_project / "nginx.conf").exists()
        assert (temp_project / "docker-compose.prod.yml").exists()
        assert (temp_project / ".env.prod.example").exists()
        assert (temp_project / "nginx").exists()
        assert (temp_project / "nginx" / "static").exists()

    def test_full_generation_with_redis_and_ssl(self, temp_project, config_with_redis):
        """Test full generation with Redis and SSL."""
        generator = ProductionComposeGenerator(temp_project)
        generator.generate(config_with_redis)

        # Check all files were created
        assert (temp_project / "Dockerfile.backend.prod").exists()
        assert (temp_project / "Dockerfile.frontend.prod").exists()
        assert (temp_project / "nginx.conf").exists()
        assert (temp_project / "docker-compose.prod.yml").exists()
        assert (temp_project / ".env.prod.example").exists()
        assert (temp_project / "nginx" / "ssl").exists()

    def test_security_hardening_in_backend(self, temp_project, config_no_redis):
        """Test security hardening features in backend Dockerfile."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_backend_dockerfile(config_no_redis)

        content = (temp_project / "Dockerfile.backend.prod").read_text()

        # Check for security features
        assert "groupadd -r appuser" in content
        assert "useradd -r -g appuser appuser" in content
        assert "USER appuser" in content
        assert "HEALTHCHECK" in content
        assert "--no-cache-dir" in content
        assert "rm -rf /var/lib/apt/lists" in content

    def test_security_hardening_in_frontend(self, temp_project, config_no_redis):
        """Test security hardening features in frontend Dockerfile."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_frontend_dockerfile(config_no_redis)

        content = (temp_project / "Dockerfile.frontend.prod").read_text()

        # Check for security features
        assert "USER nginx" in content
        assert "HEALTHCHECK" in content
        assert "chown -R nginx:nginx" in content

    def test_multi_stage_builds(self, temp_project, config_no_redis):
        """Test multi-stage build features."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_backend_dockerfile(config_no_redis)
        generator._generate_frontend_dockerfile(config_no_redis)

        backend_content = (temp_project / "Dockerfile.backend.prod").read_text()
        frontend_content = (temp_project / "Dockerfile.frontend.prod").read_text()

        # Check multi-stage builds
        assert "AS builder" in backend_content
        assert "AS builder" in frontend_content
        assert "COPY --from=builder" in backend_content
        assert "COPY --from=builder" in frontend_content

    def test_resource_limits_in_compose(self, temp_project, config_with_redis):
        """Test resource limits in compose file."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_compose_file(config_with_redis)

        content = (temp_project / "docker-compose.prod.yml").read_text()

        # Check for resource limits
        assert "limits:" in content
        assert "cpus:" in content
        assert "memory:" in content
        assert "reservations:" in content

    def test_health_checks_in_compose(self, temp_project, config_no_redis):
        """Test health checks in compose file."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_compose_file(config_no_redis)

        content = (temp_project / "docker-compose.prod.yml").read_text()

        # Check for health checks
        assert "healthcheck:" in content
        assert "test:" in content
        assert "interval:" in content
        assert "timeout:" in content
        assert "retries:" in content

    def test_logging_configuration(self, temp_project, config_no_redis):
        """Test logging configuration in compose file."""
        generator = ProductionComposeGenerator(temp_project)
        generator._generate_compose_file(config_no_redis)

        content = (temp_project / "docker-compose.prod.yml").read_text()

        # Check for logging config
        assert "logging:" in content
        assert "driver:" in content
        assert "max-size:" in content
        assert "max-file:" in content

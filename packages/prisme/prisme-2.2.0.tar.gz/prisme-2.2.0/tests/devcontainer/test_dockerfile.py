"""Tests for the devcontainer templates."""

from jinja2 import Environment


class TestDockerfileDevTemplate:
    """Tests for Dockerfile.dev.jinja2 template."""

    def test_basic_render(self, template_env: Environment) -> None:
        """Test basic template rendering with default values."""
        template = template_env.get_template("devcontainer/Dockerfile.dev.jinja2")
        content = template.render(
            python_version="3.13",
            node_version="22",
        )

        assert "mcr.microsoft.com/devcontainers/python:3.13" in content
        assert "NODE_VERSION=22" in content
        assert "npm install -g pnpm" in content
        assert "pip install" in content and "uv" in content

    def test_different_python_version(self, template_env: Environment) -> None:
        """Test template with different Python version."""
        template = template_env.get_template("devcontainer/Dockerfile.dev.jinja2")
        content = template.render(
            python_version="3.12",
            node_version="22",
        )

        assert "mcr.microsoft.com/devcontainers/python:3.12" in content

    def test_different_node_version(self, template_env: Environment) -> None:
        """Test template with different Node.js version."""
        template = template_env.get_template("devcontainer/Dockerfile.dev.jinja2")
        content = template.render(
            python_version="3.13",
            node_version="20",
        )

        assert "NODE_VERSION=20" in content


class TestDevContainerJsonTemplate:
    """Tests for devcontainer.json.jinja2 template."""

    def test_basic_render(self, template_env: Environment) -> None:
        """Test basic template rendering."""
        template = template_env.get_template("devcontainer/devcontainer.json.jinja2")
        content = template.render(
            project_name="myproject",
            default_workspace="myproject-main",
        )

        assert "myproject" in content
        assert "docker-compose.yml" in content
        assert "dockerComposeFile" in content

    def test_includes_extensions(self, template_env: Environment) -> None:
        """Test that VS Code extensions are included."""
        template = template_env.get_template("devcontainer/devcontainer.json.jinja2")
        content = template.render(
            project_name="myproject",
            default_workspace="myproject-main",
        )

        # Should include Python extension
        assert "ms-python.python" in content


class TestDockerComposeTemplate:
    """Tests for docker-compose.yml.jinja2 template."""

    def test_basic_render(self, template_env: Environment) -> None:
        """Test basic template rendering."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path=None,
        )

        assert "${WORKSPACE_NAME}" in content
        assert "app:" in content
        assert "db:" in content
        assert "postgres:16" in content

    def test_traefik_labels(self, template_env: Environment) -> None:
        """Test that Traefik labels are included."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path=None,
        )

        assert "traefik.enable=true" in content
        assert "traefik.http.routers" in content
        assert "priority=5" in content

    def test_with_redis(self, template_env: Environment) -> None:
        """Test template with Redis enabled."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=True,
            frontend_path=None,
        )

        assert "redis:" in content
        assert "redis:7" in content

    def test_without_redis(self, template_env: Environment) -> None:
        """Test template without Redis."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path=None,
        )

        # Redis section should not be present
        assert "redis:" not in content or "include_redis" in content

    def test_with_frontend_path(self, template_env: Environment) -> None:
        """Test template renders the same with or without frontend path (volumes consolidated)."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path="packages/frontend",
        )

        # Frontend node_modules is now handled via symlinks in setup.sh,
        # not as a separate volume mount in compose
        assert "persist:/persist" in content

    def test_uses_workspace_variable(self, template_env: Environment) -> None:
        """Test that WORKSPACE_NAME variable is used for isolation."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path=None,
        )

        # Container names should use ${WORKSPACE_NAME}
        assert "${WORKSPACE_NAME}-app" in content
        assert "${WORKSPACE_NAME}-db" in content

    def test_volume_names_use_workspace(self, template_env: Environment) -> None:
        """Test that volume names are workspace-specific."""
        template = template_env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name="myproject",
            include_redis=False,
            frontend_path=None,
        )

        assert "${WORKSPACE_NAME}-persist" in content
        assert "${WORKSPACE_NAME}-pgdata" in content


class TestEnvTemplate:
    """Tests for env.template.jinja2 template."""

    def test_basic_render(self, template_env: Environment) -> None:
        """Test basic template rendering."""
        template = template_env.get_template("devcontainer/env.template.jinja2")
        content = template.render(
            workspace_name="myproject-main",
            database_name="myproject_main",
        )

        assert "WORKSPACE_NAME=myproject-main" in content
        assert "COMPOSE_PROJECT_NAME=myproject-main" in content
        assert "DATABASE_NAME=myproject_main" in content


class TestSetupShTemplate:
    """Tests for setup.sh.jinja2 template."""

    def test_basic_render(self, template_env: Environment) -> None:
        """Test basic template rendering."""
        template = template_env.get_template("devcontainer/setup.sh.jinja2")
        content = template.render(
            frontend_path=None,
            spec_path=None,
        )

        assert "#!/bin/bash" in content
        assert "uv sync" in content

    def test_with_frontend_path(self, template_env: Environment) -> None:
        """Test template with frontend path."""
        template = template_env.get_template("devcontainer/setup.sh.jinja2")
        content = template.render(
            frontend_path="packages/frontend",
            spec_path=None,
        )

        assert "packages/frontend" in content
        assert "pnpm install" in content

    def test_with_spec_path(self, template_env: Environment) -> None:
        """Test template with spec path."""
        template = template_env.get_template("devcontainer/setup.sh.jinja2")
        content = template.render(
            frontend_path=None,
            spec_path="specs/models.py",
        )

        assert "specs/models.py" in content
        assert "prisme generate" in content

    def test_without_frontend_or_spec(self, template_env: Environment) -> None:
        """Test template without frontend or spec paths."""
        template = template_env.get_template("devcontainer/setup.sh.jinja2")
        content = template.render(
            frontend_path=None,
            spec_path=None,
        )

        # Should not include frontend setup commands
        assert "pnpm install" not in content
        # Should not include prism generate
        assert "prisme generate" not in content

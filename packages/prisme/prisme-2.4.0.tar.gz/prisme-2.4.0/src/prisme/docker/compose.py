"""Docker Compose configuration generator for Prism projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template


def normalize_hostname(name: str) -> str:
    """Normalize a project name for use as a hostname.

    Converts underscores to hyphens since underscores in hostnames can cause
    issues with cookies, SSL certificates, and some browsers/tools.

    Args:
        name: Project name to normalize

    Returns:
        Hostname-safe version of the name
    """
    return name.replace("_", "-").lower()


@dataclass
class ComposeConfig:
    """Configuration for Docker Compose generation.

    Attributes:
        project_name: Name of the project (used for container names, volumes)
        backend_path: Path to backend source code (e.g., "backend" or "packages/backend/src")
        frontend_path: Path to frontend source code (e.g., "frontend" or "packages/frontend")
        backend_module: Python module name for backend (e.g., "backend" or "packages.backend.src")
        use_redis: Whether to include Redis service for background jobs
        use_mcp: Whether to include MCP server service
        backend_port: Port to expose backend on (default: 8000)
        frontend_port: Port to expose frontend on (default: 5173)
        db_port: Port to expose database on (default: 5432)
        redis_port: Port to expose Redis on (default: 6379)
        mcp_port: Port to expose MCP server on (default: 8765)
        system_packages: Additional system packages to install in backend Dockerfile
        health_check_path: Path for backend health check endpoint (default: /health)
        mcp_path: Subpath for MCP module (default: mcp_server)
    """

    project_name: str
    backend_path: str
    frontend_path: str
    backend_module: str
    use_redis: bool = False
    use_mcp: bool = False
    backend_port: int = 8000
    frontend_port: int = 5173
    db_port: int = 5432
    redis_port: int = 6379
    mcp_port: int = 8765
    system_packages: list[str] | None = None
    health_check_path: str = "/health"
    mcp_path: str = "mcp_server"

    @property
    def hostname(self) -> str:
        """Get hostname-safe version of project name."""
        return normalize_hostname(self.project_name)


class ComposeGenerator:
    """Generate Docker Compose configuration for development."""

    def __init__(self, project_dir: Path):
        """Initialize ComposeGenerator.

        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.templates_dir = Path(__file__).parent.parent / "templates" / "jinja2" / "docker"

    def generate(self, config: ComposeConfig) -> None:
        """Generate docker-compose.dev.yml and Dockerfiles.

        Args:
            config: Configuration for Docker Compose generation
        """
        # Render templates
        compose_content = self._render_compose_template(config)
        backend_dockerfile = self._render_backend_dockerfile(config)
        frontend_dockerfile = self._render_frontend_dockerfile(config)
        dockerignore = self._render_dockerignore()

        # Write files
        (self.project_dir / "docker-compose.dev.yml").write_text(compose_content)
        (self.project_dir / "Dockerfile.backend").write_text(backend_dockerfile)
        (self.project_dir / "Dockerfile.frontend").write_text(frontend_dockerfile)
        (self.project_dir / ".dockerignore").write_text(dockerignore)

    def _render_compose_template(self, config: ComposeConfig) -> str:
        """Render docker-compose.dev.yml template.

        Args:
            config: Configuration for template rendering

        Returns:
            Rendered docker-compose.dev.yml content
        """
        template_path = self.templates_dir / "docker-compose.dev.yml.jinja2"
        template = Template(template_path.read_text())
        return template.render(
            project_name=config.project_name,
            hostname=config.hostname,
            backend_path=config.backend_path,
            frontend_path=config.frontend_path,
            backend_module=config.backend_module,
            use_redis=config.use_redis,
            use_mcp=config.use_mcp,
            backend_port=config.backend_port,
            frontend_port=config.frontend_port,
            db_port=config.db_port,
            redis_port=config.redis_port,
            mcp_port=config.mcp_port,
            mcp_path=config.mcp_path,
            health_check_path=config.health_check_path,
        )

    def _render_backend_dockerfile(self, config: ComposeConfig) -> str:
        """Render Dockerfile.backend template.

        Args:
            config: Configuration for template rendering

        Returns:
            Rendered Dockerfile.backend content
        """
        template_path = self.templates_dir / "Dockerfile.backend.jinja2"
        template = Template(template_path.read_text())
        return template.render(
            backend_path=config.backend_path,
            backend_module=config.backend_module,
            system_packages=config.system_packages or [],
        )

    def _render_frontend_dockerfile(self, config: ComposeConfig) -> str:
        """Render Dockerfile.frontend template.

        Args:
            config: Configuration for template rendering

        Returns:
            Rendered Dockerfile.frontend content
        """
        template_path = self.templates_dir / "Dockerfile.frontend.jinja2"
        template = Template(template_path.read_text())
        return template.render(
            frontend_path=config.frontend_path,
        )

    def _render_dockerignore(self) -> str:
        """Render .dockerignore template.

        Returns:
            Rendered .dockerignore content
        """
        template_path = self.templates_dir / ".dockerignore.jinja2"
        template = Template(template_path.read_text())
        return template.render()

"""Production Docker configuration generator."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader
from rich.console import Console


@dataclass
class ProductionConfig:
    """Configuration for production Docker setup."""

    project_name: str
    use_redis: bool
    domain: str = ""
    backend_replicas: int = 2
    enable_monitoring: bool = False


class ProductionComposeGenerator:
    """Generate production Docker Compose configuration."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.env = Environment(loader=PackageLoader("prisme", "templates/jinja2"))
        self.console = Console()

    def generate(self, config: ProductionConfig) -> None:
        """Generate production Docker files."""
        # Generate production Dockerfiles
        self._generate_backend_dockerfile(config)
        self._generate_frontend_dockerfile(config)

        # Generate production compose file
        self._generate_compose_file(config)

        # Generate .env.example for production
        self._generate_env_example(config)

        self.console.print("[green]✓ Production Docker configuration generated[/green]")
        self.console.print(f"  Location: {self.project_dir}")
        self.console.print("\n[bold]Next steps:[/bold]")
        self.console.print("  1. Copy .env.prod.example to .env.prod and configure")
        self.console.print("  2. Run: docker compose -f docker-compose.prod.yml up -d")

    def _generate_backend_dockerfile(self, config: ProductionConfig) -> None:
        """Generate production backend Dockerfile."""
        template = self.env.get_template("docker/Dockerfile.backend.prod.jinja2")
        content = template.render(project_name=config.project_name)
        (self.project_dir / "Dockerfile.backend.prod").write_text(content)
        self.console.print("  ✓ Dockerfile.backend.prod")

    def _generate_frontend_dockerfile(self, config: ProductionConfig) -> None:
        """Generate production frontend Dockerfile."""
        template = self.env.get_template("docker/Dockerfile.frontend.prod.jinja2")
        content = template.render(project_name=config.project_name)
        (self.project_dir / "Dockerfile.frontend.prod").write_text(content)
        self.console.print("  ✓ Dockerfile.frontend.prod")

    def _generate_compose_file(self, config: ProductionConfig) -> None:
        """Generate production docker-compose.yml."""
        template = self.env.get_template("docker/docker-compose.prod.yml.jinja2")
        content = template.render(
            PROJECT_NAME=config.project_name,
            use_redis=config.use_redis,
            backend_replicas=config.backend_replicas,
        )
        (self.project_dir / "docker-compose.prod.yml").write_text(content)
        self.console.print("  ✓ docker-compose.prod.yml")

    def _generate_env_example(self, config: ProductionConfig) -> None:
        """Generate .env.example for production."""
        env_example = f"""# Production Environment Variables

# Project
PROJECT_NAME={config.project_name}

# Database
DB_USER=postgres
DB_PASSWORD=CHANGE_ME_IN_PRODUCTION
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION

# Backend
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
ALLOWED_HOSTS={config.domain + "," if config.domain else ""}localhost,127.0.0.1
ENVIRONMENT=production

# Redis (if used)
{"REDIS_URL=redis://redis:6379/0" if config.use_redis else "# REDIS_URL=redis://redis:6379/0"}
"""
        (self.project_dir / ".env.prod.example").write_text(env_example)
        self.console.print("  ✓ .env.prod.example")

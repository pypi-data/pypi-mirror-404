"""Development container configuration generation."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

console = Console()


@dataclass
class DevContainerConfig:
    """Configuration for dev container generation."""

    project_name: str
    include_frontend: bool
    python_version: str = "3.13"
    node_version: str = "22"
    include_postgres: bool = True
    include_redis: bool = False


class DevContainerGenerator:
    """Generate VS Code dev container configuration."""

    def __init__(self, project_dir: Path):
        """Initialize the generator.

        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.devcontainer_dir = project_dir / ".devcontainer"
        self.env = Environment(
            loader=PackageLoader("prisme", "templates/jinja2"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: DevContainerConfig) -> None:
        """Generate dev container configuration files.

        Args:
            config: Configuration for dev container generation
        """
        self.devcontainer_dir.mkdir(parents=True, exist_ok=True)

        self._generate_devcontainer_json(config)
        self._generate_dockerfile(config)

        console.print("[green]✓ Dev container configuration generated[/green]")
        console.print(f"  Location: {self.devcontainer_dir}")

    def _generate_devcontainer_json(self, config: DevContainerConfig) -> None:
        """Generate devcontainer.json.

        Args:
            config: Configuration for dev container generation
        """
        template = self.env.get_template("dx/devcontainer/devcontainer.json.jinja2")
        content = template.render(
            project_name=config.project_name,
            include_frontend=config.include_frontend,
            python_version=config.python_version,
            node_version=config.node_version,
            include_postgres=config.include_postgres,
            include_redis=config.include_redis,
        )
        (self.devcontainer_dir / "devcontainer.json").write_text(content)
        console.print("  [blue]✓[/blue] Generated devcontainer.json")

    def _generate_dockerfile(self, config: DevContainerConfig) -> None:
        """Generate Dockerfile for dev container.

        Args:
            config: Configuration for dev container generation
        """
        template = self.env.get_template("dx/devcontainer/Dockerfile.jinja2")
        content = template.render(
            python_version=config.python_version,
            node_version=config.node_version,
            include_frontend=config.include_frontend,
        )
        (self.devcontainer_dir / "Dockerfile").write_text(content)
        console.print("  [blue]✓[/blue] Generated Dockerfile")

"""Generate .devcontainer configuration files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader
from rich.console import Console

if TYPE_CHECKING:
    from prisme.devcontainer.config import WorkspaceConfig


class DevContainerGenerator:
    """Generate .devcontainer files for a workspace."""

    def __init__(self, console: Console | None = None):
        """Initialize the generator.

        Args:
            console: Rich console for output
        """
        self.console = console or Console()
        self.env = Environment(
            loader=PackageLoader("prisme", "templates/jinja2"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: WorkspaceConfig) -> None:
        """Generate all .devcontainer files.

        Args:
            config: Workspace configuration
        """
        devcontainer_dir = config.devcontainer_dir
        devcontainer_dir.mkdir(parents=True, exist_ok=True)

        self.console.print(f"[blue]Generating .devcontainer for {config.project_name}...[/blue]")

        # Generate each file
        self._generate_devcontainer_json(config)
        self._generate_docker_compose(config)
        self._generate_dockerfile(config)
        self._generate_env_template(config)
        self._generate_setup_script(config)
        self._update_gitignore(config)

        self.console.print("[green]✓ .devcontainer generated[/green]")
        self.console.print()
        self.console.print("Next steps:")
        self.console.print("  prisme devcontainer up")
        self.console.print("  prisme devcontainer shell")

    def _generate_devcontainer_json(self, config: WorkspaceConfig) -> None:
        """Generate devcontainer.json file."""
        template = self.env.get_template("devcontainer/devcontainer.json.jinja2")
        content = template.render(
            project_name=config.project_name,
            default_workspace=config.workspace_name,
        )
        (config.devcontainer_dir / "devcontainer.json").write_text(content)
        self.console.print("  [dim]✓ devcontainer.json[/dim]")

    def _generate_docker_compose(self, config: WorkspaceConfig) -> None:
        """Generate docker-compose.yml file."""
        template = self.env.get_template("devcontainer/docker-compose.yml.jinja2")
        content = template.render(
            project_name=config.project_name,
            include_redis=config.include_redis,
            frontend_path=config.frontend_path,
        )
        (config.devcontainer_dir / "docker-compose.yml").write_text(content)
        self.console.print("  [dim]✓ docker-compose.yml[/dim]")

    def _generate_dockerfile(self, config: WorkspaceConfig) -> None:
        """Generate Dockerfile.dev file."""
        template = self.env.get_template("devcontainer/Dockerfile.dev.jinja2")
        content = template.render(
            python_version=config.python_version,
            node_version=config.node_version,
        )
        (config.devcontainer_dir / "Dockerfile.dev").write_text(content)
        self.console.print("  [dim]✓ Dockerfile.dev[/dim]")

    def _generate_env_template(self, config: WorkspaceConfig) -> None:
        """Generate .env.template file."""
        template = self.env.get_template("devcontainer/env.template.jinja2")
        content = template.render(
            workspace_name=config.workspace_name,
            database_name=config.database_name,
            prisme_src=config.prisme_src,
        )
        (config.devcontainer_dir / ".env.template").write_text(content)
        self.console.print("  [dim]✓ .env.template[/dim]")

    def _generate_setup_script(self, config: WorkspaceConfig) -> None:
        """Generate setup.sh script."""
        template = self.env.get_template("devcontainer/setup.sh.jinja2")
        content = template.render(
            frontend_path=config.frontend_path,
            spec_path=config.spec_path,
        )
        setup_path = config.devcontainer_dir / "setup.sh"
        setup_path.write_text(content)
        setup_path.chmod(0o755)
        self.console.print("  [dim]✓ setup.sh[/dim]")

    def _update_gitignore(self, config: WorkspaceConfig) -> None:
        """Update .gitignore to exclude .devcontainer/.env."""
        gitignore = config.project_dir / ".gitignore"
        entry = ".devcontainer/.env"

        if gitignore.exists():
            content = gitignore.read_text()
            if entry not in content:
                with gitignore.open("a") as f:
                    f.write(f"\n# Dev container workspace env\n{entry}\n")
        else:
            gitignore.write_text(f"# Dev container workspace env\n{entry}\n")

    def generate_env(self, config: WorkspaceConfig) -> None:
        """Generate/update .env file for specific workspace.

        Args:
            config: Workspace configuration
        """
        template = self.env.get_template("devcontainer/env.template.jinja2")
        content = template.render(
            workspace_name=config.workspace_name,
            database_name=config.database_name,
            prisme_src=config.prisme_src,
        )
        config.env_file.write_text(content)
        self.console.print(f"[dim]Generated .env for workspace: {config.workspace_name}[/dim]")

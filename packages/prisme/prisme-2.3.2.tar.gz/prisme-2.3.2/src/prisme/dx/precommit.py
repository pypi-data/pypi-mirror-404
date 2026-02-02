"""Pre-commit and pre-push hooks generation."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

console = Console()


@dataclass
class PreCommitConfig:
    """Configuration for pre-commit hooks generation."""

    project_name: str
    include_frontend: bool
    python_manager: str = "uv"
    enable_mypy: bool = True
    enable_pytest: bool = True
    enable_ruff: bool = True


class PreCommitGenerator:
    """Generate pre-commit configuration files."""

    def __init__(self, project_dir: Path):
        """Initialize the generator.

        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.env = Environment(
            loader=PackageLoader("prisme", "templates/jinja2"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: PreCommitConfig) -> None:
        """Generate all pre-commit configuration files.

        Args:
            config: Configuration for pre-commit generation
        """
        self._generate_precommit_config(config)
        console.print("[green]✓ Pre-commit hooks generated[/green]")

    def _generate_precommit_config(self, config: PreCommitConfig) -> None:
        """Generate .pre-commit-config.yaml.

        Args:
            config: Configuration for pre-commit generation
        """
        template = self.env.get_template("dx/precommit/.pre-commit-config.yaml.jinja2")
        content = template.render(
            project_name=config.project_name,
            include_frontend=config.include_frontend,
            python_manager=config.python_manager,
            enable_mypy=config.enable_mypy,
            enable_pytest=config.enable_pytest,
            enable_ruff=config.enable_ruff,
        )
        (self.project_dir / ".pre-commit-config.yaml").write_text(content)
        console.print("  [blue]✓[/blue] Generated .pre-commit-config.yaml")

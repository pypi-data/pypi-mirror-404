"""Documentation setup generation."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

console = Console()


@dataclass
class DocsConfig:
    """Configuration for documentation generation."""

    project_name: str
    project_title: str
    description: str
    include_api_docs: bool = True
    include_readthedocs: bool = True
    theme: str = "material"


class DocsGenerator:
    """Generate documentation setup files."""

    def __init__(self, project_dir: Path):
        """Initialize the generator.

        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.docs_dir = project_dir / "docs"
        self.env = Environment(
            loader=PackageLoader("prisme", "templates/jinja2"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: DocsConfig) -> None:
        """Generate all documentation files.

        Args:
            config: Configuration for documentation generation
        """
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        self._generate_mkdocs_config(config)
        self._generate_docs_structure(config)
        self._generate_docs_requirements(config)

        if config.include_readthedocs:
            self._generate_readthedocs_config(config)

        console.print("[green]✓ Documentation setup generated[/green]")
        console.print(f"  Location: {self.docs_dir}")

    def _generate_mkdocs_config(self, config: DocsConfig) -> None:
        """Generate mkdocs.yml.

        Args:
            config: Configuration for documentation generation
        """
        template = self.env.get_template("dx/docs/mkdocs.yml.jinja2")
        content = template.render(
            project_name=config.project_name,
            project_title=config.project_title,
            description=config.description,
            include_api_docs=config.include_api_docs,
            theme=config.theme,
        )
        (self.project_dir / "mkdocs.yml").write_text(content)
        console.print("  [blue]✓[/blue] Generated mkdocs.yml")

    def _generate_docs_structure(self, config: DocsConfig) -> None:
        """Generate docs folder structure.

        Args:
            config: Configuration for documentation generation
        """
        # Create subdirectories
        (self.docs_dir / "getting-started").mkdir(exist_ok=True)
        (self.docs_dir / "user-guide").mkdir(exist_ok=True)
        (self.docs_dir / "reference").mkdir(exist_ok=True)

        # Generate index.md
        template = self.env.get_template("dx/docs/index.md.jinja2")
        content = template.render(
            project_title=config.project_title,
            description=config.description,
        )
        (self.docs_dir / "index.md").write_text(content)

        # Generate getting-started/index.md
        template = self.env.get_template("dx/docs/getting-started.md.jinja2")
        content = template.render(project_name=config.project_name)
        (self.docs_dir / "getting-started" / "index.md").write_text(content)

        # Generate user-guide/index.md
        template = self.env.get_template("dx/docs/user-guide.md.jinja2")
        content = template.render(project_name=config.project_name)
        (self.docs_dir / "user-guide" / "index.md").write_text(content)

        # Generate reference/index.md
        template = self.env.get_template("dx/docs/reference.md.jinja2")
        content = template.render(project_name=config.project_name)
        (self.docs_dir / "reference" / "index.md").write_text(content)

        console.print("  [blue]✓[/blue] Generated docs/ structure")

    def _generate_docs_requirements(self, config: DocsConfig) -> None:
        """Generate docs/requirements.txt for ReadTheDocs.

        Args:
            config: Configuration for documentation generation
        """
        template = self.env.get_template("dx/docs/requirements.txt.jinja2")
        content = template.render(include_api_docs=config.include_api_docs)
        (self.docs_dir / "requirements.txt").write_text(content)
        console.print("  [blue]✓[/blue] Generated docs/requirements.txt")

    def _generate_readthedocs_config(self, config: DocsConfig) -> None:
        """Generate .readthedocs.yaml.

        Args:
            config: Configuration for documentation generation
        """
        template = self.env.get_template("dx/docs/.readthedocs.yaml.jinja2")
        content = template.render()
        (self.project_dir / ".readthedocs.yaml").write_text(content)
        console.print("  [blue]✓[/blue] Generated .readthedocs.yaml")

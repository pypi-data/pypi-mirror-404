"""GitHub Actions CI/CD workflow generation."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

console = Console()


@dataclass
class CIConfig:
    """Configuration for CI/CD generation."""

    project_name: str
    include_frontend: bool
    use_redis: bool = False
    python_version: str = "3.13"
    node_version: str = "22"
    enable_codecov: bool = True
    enable_dependabot: bool = True
    enable_semantic_release: bool = True
    enable_commitlint: bool = True
    github_username: str | None = None


class GitHubCIGenerator:
    """Generate GitHub Actions workflows for CI/CD."""

    def __init__(self, project_dir: Path):
        """Initialize the generator.

        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = project_dir
        self.workflows_dir = project_dir / ".github" / "workflows"
        self.github_dir = project_dir / ".github"

        # Set up Jinja2 environment
        self.env = Environment(
            loader=PackageLoader("prisme", "templates/jinja2"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, config: CIConfig) -> None:
        """Generate all CI/CD files.

        Args:
            config: Configuration for CI/CD generation
        """
        # Create directories
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Generate CI workflow
        self._generate_ci_workflow(config)

        # Generate release workflow
        if config.enable_semantic_release:
            self._generate_release_workflow(config)
            self._generate_semantic_release_config(config)
            self._generate_changelog(config)

        # Generate commitlint config
        if config.enable_commitlint:
            self._generate_commitlint_config(config)

        # Generate Dependabot config
        if config.enable_dependabot:
            self._generate_dependabot_config(config)

        console.print("[green]✓ CI/CD workflows generated[/green]")
        console.print(f"  Location: {self.workflows_dir}")

    def _generate_ci_workflow(self, config: CIConfig) -> None:
        """Generate ci.yml workflow.

        Args:
            config: Configuration for CI/CD generation
        """
        template = self.env.get_template("ci/github/ci.yml.jinja2")
        content = template.render(
            project_name=config.project_name,
            include_frontend=config.include_frontend,
            use_redis=config.use_redis,
            python_version=config.python_version,
            node_version=config.node_version,
            enable_codecov=config.enable_codecov,
        )
        (self.workflows_dir / "ci.yml").write_text(content)
        console.print("  [blue]✓[/blue] Generated ci.yml")

    def _generate_dependabot_config(self, config: CIConfig) -> None:
        """Generate dependabot.yml configuration.

        Args:
            config: Configuration for CI/CD generation
        """
        template = self.env.get_template("ci/github/dependabot.yml.jinja2")
        content = template.render(
            include_frontend=config.include_frontend,
            github_username=config.github_username,
        )
        (self.github_dir / "dependabot.yml").write_text(content)
        console.print("  [blue]✓[/blue] Generated dependabot.yml")

    def _generate_release_workflow(self, config: CIConfig) -> None:
        """Generate release.yml workflow.

        Args:
            config: Configuration for CI/CD generation
        """
        template = self.env.get_template("ci/github/release.yml.jinja2")
        content = template.render(
            node_version=config.node_version,
        )
        (self.workflows_dir / "release.yml").write_text(content)
        console.print("  [blue]✓[/blue] Generated release.yml")

    def _generate_semantic_release_config(self, config: CIConfig) -> None:
        """Generate .releaserc.json configuration.

        Args:
            config: Configuration for CI/CD generation
        """
        template = self.env.get_template("ci/config/releaserc.json.jinja2")
        content = template.render()
        (self.project_dir / ".releaserc.json").write_text(content)
        console.print("  [blue]✓[/blue] Generated .releaserc.json")

    def _generate_commitlint_config(self, config: CIConfig) -> None:
        """Generate commitlint.config.js configuration.

        Args:
            config: Configuration for CI/CD generation
        """
        template = self.env.get_template("ci/config/commitlint.config.js.jinja2")
        content = template.render()
        (self.project_dir / "commitlint.config.js").write_text(content)
        console.print("  [blue]✓[/blue] Generated commitlint.config.js")

    def _generate_changelog(self, config: CIConfig) -> None:
        """Generate initial CHANGELOG.md.

        Args:
            config: Configuration for CI/CD generation
        """
        changelog_path = self.project_dir / "CHANGELOG.md"
        # Only generate if it doesn't exist
        if not changelog_path.exists():
            template = self.env.get_template("ci/CHANGELOG.md.jinja2")
            content = template.render()
            changelog_path.write_text(content)
            console.print("  [blue]✓[/blue] Generated CHANGELOG.md")

"""Docker CI/CD workflow generation."""

from pathlib import Path

from jinja2 import Environment, PackageLoader
from rich.console import Console


class DockerCIGenerator:
    """Generate Docker-specific CI workflows."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.workflows_dir = project_dir / ".github" / "workflows"
        self.env = Environment(loader=PackageLoader("prisme", "templates/jinja2"))
        self.console = Console()

    def generate_docker_build_workflow(self) -> None:
        """Generate docker-build.yml workflow."""
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        template = self.env.get_template("ci/github/docker-build.yml.jinja2")
        content = template.render()
        (self.workflows_dir / "docker-build.yml").write_text(content)

        self.console.print("[green]✓ Docker build workflow generated[/green]")
        self.console.print("  Location: .github/workflows/docker-build.yml")
        self.console.print("\n[bold]Docker images will be pushed to:[/bold]")
        self.console.print("  ghcr.io/<your-org>/<your-repo>-backend")
        self.console.print("  ghcr.io/<your-org>/<your-repo>-frontend")

    def extend_ci_with_docker_tests(self) -> None:
        """Add Docker-based testing to CI workflow."""
        ci_file = self.workflows_dir / "ci.yml"

        if not ci_file.exists():
            self.console.print(
                "[yellow]Warning: ci.yml not found. Run 'prisme ci init' first.[/yellow]"
            )
            return

        # Check if Docker tests are already added
        ci_content = ci_file.read_text()
        if "test-in-docker:" in ci_content:
            self.console.print(
                "[yellow]Docker integration tests already present in CI workflow[/yellow]"
            )
            return

        # Append Docker test job to existing CI workflow
        template = self.env.get_template("ci/github/ci-docker-tests.yml.jinja2")
        docker_tests = template.render()

        # Insert before the final line of the CI workflow
        ci_file.write_text(ci_content + "\n" + docker_tests)

        self.console.print("[green]✓ Docker integration tests added to CI workflow[/green]")
        self.console.print("  Location: .github/workflows/ci.yml")

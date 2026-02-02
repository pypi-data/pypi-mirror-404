"""Hetzner Cloud deployment generator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - used at runtime
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader
from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    from prisme.deploy.config import DeploymentConfig


@dataclass
class HetznerDeployGenerator:
    """Generate Hetzner Cloud deployment infrastructure."""

    project_dir: Path
    config: DeploymentConfig

    def __post_init__(self) -> None:
        self.env = Environment(loader=PackageLoader("prisme", "templates/jinja2/deploy"))
        self.console = Console()
        self.deploy_dir = self.project_dir / "deploy"

    def generate(self) -> None:
        """Generate all deployment files."""
        self.console.print("[blue]Generating Hetzner deployment infrastructure...[/blue]")

        self._create_directory_structure()
        self._generate_terraform_files()
        self._generate_terraform_modules()
        self._generate_cloud_init()
        self._generate_env_templates()
        self._generate_scripts()
        self._generate_readme()
        self._generate_github_workflow()
        self._generate_traefik_config()

        self._show_next_steps()

    def _create_directory_structure(self) -> None:
        """Create deployment directory structure."""
        dirs = [
            self.deploy_dir / "terraform",
            self.deploy_dir / "terraform" / "modules" / "server",
            self.deploy_dir / "terraform" / "modules" / "volume",
            self.deploy_dir / "terraform" / "cloud-init",
            self.deploy_dir / "scripts",
            self.deploy_dir / "env",
            self.deploy_dir / "traefik",
            self.deploy_dir / "traefik" / "dynamic",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _get_template_context(self) -> dict:
        """Get common template context."""
        # Compute S3 bucket name default if not provided
        s3_bucket_name = self.config.hetzner.s3_bucket_name
        if not s3_bucket_name:
            s3_bucket_name = f"{self.config.project_name}-terraform-state"

        return {
            "project_name": self.config.project_name,
            "project_name_snake": self.config.project_name.replace("-", "_"),
            "domain": self.config.domain,
            "ssl_email": self.config.ssl_email,
            "hetzner": self.config.hetzner,
            "use_redis": self.config.use_redis,
            "postgres_version": self.config.postgres_version,
            "postgres_user": self.config.postgres_user,
            "postgres_db": self.config.postgres_db,
            "enable_swap": self.config.enable_swap,
            "swap_size_mb": self.config.swap_size_mb,
            "docker_registry": self.config.docker_registry,
            # Remote state (Hetzner Object Storage)
            "enable_remote_state": self.config.hetzner.enable_remote_state,
            "s3_bucket_name": s3_bucket_name,
            "s3_endpoint": self.config.hetzner.s3_endpoint,
        }

    def _render_template(self, template_name: str, output_path: Path) -> None:
        """Render a template to a file."""
        template = self.env.get_template(template_name)
        content = template.render(**self._get_template_context())
        output_path.write_text(content)

    def _generate_terraform_files(self) -> None:
        """Generate Terraform configuration files."""
        terraform_dir = self.deploy_dir / "terraform"

        files = [
            ("hetzner/terraform/main.tf.jinja2", "main.tf"),
            ("hetzner/terraform/variables.tf.jinja2", "variables.tf"),
            ("hetzner/terraform/outputs.tf.jinja2", "outputs.tf"),
            ("hetzner/terraform/versions.tf.jinja2", "versions.tf"),
            ("hetzner/terraform/staging.tfvars.jinja2", "staging.tfvars"),
            ("hetzner/terraform/production.tfvars.jinja2", "production.tfvars"),
        ]

        for template_name, output_name in files:
            self._render_template(template_name, terraform_dir / output_name)
            self.console.print(f"  [green]✓[/green] terraform/{output_name}")

    def _generate_terraform_modules(self) -> None:
        """Generate Terraform module files."""
        terraform_dir = self.deploy_dir / "terraform"

        modules = {
            "server": ["main.tf", "variables.tf", "outputs.tf"],
            "volume": ["main.tf", "variables.tf", "outputs.tf"],
        }

        for module, files in modules.items():
            module_dir = terraform_dir / "modules" / module
            for filename in files:
                template = f"hetzner/terraform/modules/{module}/{filename}.jinja2"
                self._render_template(template, module_dir / filename)
            self.console.print(f"  [green]✓[/green] terraform/modules/{module}/")

    def _generate_cloud_init(self) -> None:
        """Generate cloud-init configuration."""
        cloud_init_dir = self.deploy_dir / "terraform" / "cloud-init"
        self._render_template(
            "hetzner/cloud-init/user-data.yml.jinja2", cloud_init_dir / "user-data.yml"
        )
        self.console.print("  [green]✓[/green] terraform/cloud-init/user-data.yml")

    def _generate_env_templates(self) -> None:
        """Generate environment file templates."""
        env_dir = self.deploy_dir / "env"

        self._render_template("env/.env.staging.template.jinja2", env_dir / ".env.staging.template")
        self._render_template(
            "env/.env.production.template.jinja2", env_dir / ".env.production.template"
        )
        self.console.print("  [green]✓[/green] env/.env.staging.template")
        self.console.print("  [green]✓[/green] env/.env.production.template")

    def _generate_scripts(self) -> None:
        """Generate deployment scripts."""
        scripts_dir = self.deploy_dir / "scripts"

        self._render_template("hetzner/scripts/deploy.sh.jinja2", scripts_dir / "deploy.sh")
        self._render_template("hetzner/scripts/rollback.sh.jinja2", scripts_dir / "rollback.sh")

        # Make scripts executable
        for script in scripts_dir.glob("*.sh"):
            script.chmod(0o755)

        self.console.print("  [green]✓[/green] scripts/deploy.sh")
        self.console.print("  [green]✓[/green] scripts/rollback.sh")

    def _generate_readme(self) -> None:
        """Generate deployment README."""
        self._render_template("README.md.jinja2", self.deploy_dir / "README.md")
        self.console.print("  [green]✓[/green] README.md")

    def _generate_github_workflow(self) -> None:
        """Generate GitHub Actions deployment workflows."""
        workflows_dir = self.project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        self._render_template("github/deploy.yml.jinja2", workflows_dir / "deploy.yml")
        self._render_template("github/terraform.yml.jinja2", workflows_dir / "terraform.yml")
        self.console.print("  [green]✓[/green] .github/workflows/deploy.yml")
        self.console.print("  [green]✓[/green] .github/workflows/terraform.yml")

    def _generate_traefik_config(self) -> None:
        """Generate Traefik configuration files."""
        traefik_dir = self.deploy_dir / "traefik"
        dynamic_dir = traefik_dir / "dynamic"

        self._render_template("traefik/traefik.yml.jinja2", traefik_dir / "traefik.yml")
        self.console.print("  [green]✓[/green] deploy/traefik/traefik.yml")

        self._render_template(
            "traefik/dynamic/infrastructure.yml.jinja2", dynamic_dir / "infrastructure.yml"
        )
        self.console.print("  [green]✓[/green] deploy/traefik/dynamic/infrastructure.yml")

        self._render_template(
            "traefik/dynamic/middlewares.yml.jinja2", dynamic_dir / "middlewares.yml"
        )
        self.console.print("  [green]✓[/green] deploy/traefik/dynamic/middlewares.yml")

    def _show_next_steps(self) -> None:
        """Display next steps after generation."""
        self.console.print()

        next_steps = f"""[bold]Next steps to deploy to Hetzner Cloud:[/bold]

1. [cyan]Set up Hetzner API token:[/cyan]
   export HETZNER_API_TOKEN="your-api-token"

2. [cyan]Configure SSH key:[/cyan]
   - Add your SSH public key to Hetzner Cloud console, or
   - Set SSH_PUBLIC_KEY environment variable

3. [cyan]Initialize Terraform:[/cyan]
   cd {self.deploy_dir / "terraform"}
   terraform init

4. [cyan]Deploy staging environment:[/cyan]
   terraform plan -var-file=staging.tfvars
   terraform apply -var-file=staging.tfvars

5. [cyan]Configure application:[/cyan]
   - Copy deploy/env/.env.staging.template to server
   - Update with your secrets

6. [cyan]Deploy production (when ready):[/cyan]
   terraform plan -var-file=production.tfvars
   terraform apply -var-file=production.tfvars

[dim]See deploy/README.md for detailed documentation[/dim]"""

        self.console.print(
            Panel(next_steps, title="[green]Deployment Infrastructure Generated[/green]")
        )

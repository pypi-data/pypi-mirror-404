"""Prism CLI - Command line interface for the Prism code generation framework."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from prisme import PrismConfig
    from prisme.config.schema import PrismeConfig
    from prisme.spec.project import ProjectSpec

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from prisme.generators import GeneratorContext, GeneratorResult
from prisme.generators.backend import (
    AdminGenerator,
    AlembicGenerator,
    APIKeyAuthGenerator,
    AuthGenerator,
    GraphQLGenerator,
    MCPGenerator,
    ModelsGenerator,
    RESTGenerator,
    SchemasGenerator,
    ServicesGenerator,
)
from prisme.generators.ci import CIGenerator
from prisme.generators.deploy import DeployGenerator
from prisme.generators.docker import DockerGenerator
from prisme.generators.frontend import (
    ComponentsGenerator,
    DashboardGenerator,
    DesignSystemGenerator,
    ErrorPagesGenerator,
    FrontendAdminGenerator,
    FrontendAuthGenerator,
    GraphQLOpsGenerator,
    HeadlessGenerator,
    HooksGenerator,
    PagesGenerator,
    ProfilePagesGenerator,
    RouterGenerator,
    SearchPageGenerator,
    TypeScriptGenerator,
    WidgetSystemGenerator,
)
from prisme.generators.testing import BackendTestGenerator, FrontendTestGenerator
from prisme.templates.base import template_registry
from prisme.tracking.model_diff import detect_model_changes
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.spec_loader import (
    SpecLoadError,
    SpecValidationError,
    load_spec_from_file,
    validate_spec,
)
from prisme.utils.template_engine import TemplateRenderer

console = Console()


def _resolve_spec_file(fallback: str = "specs/models.py") -> Path:
    """Resolve the spec file path from prisme.toml, prism.config.py, or defaults."""
    # Try prisme.toml first
    toml_path = Path("prisme.toml")
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config

            config = load_prisme_config(toml_path)
            spec_path = Path(config.project.spec_path)
            if spec_path.exists():
                return spec_path
        except Exception:
            pass

    # Fall back to prism.config.py
    legacy_path = Path("prism.config.py")
    if legacy_path.exists():
        try:
            from prisme import PrismConfig

            legacy_config = PrismConfig.load_from_file(legacy_path)
            spec_path = Path(legacy_config.spec_path)
            if spec_path.exists():
                return spec_path
        except Exception:
            pass

    # Fall back to default locations
    for candidate in [Path(fallback), Path("spec.py")]:
        if candidate.exists():
            return candidate

    return Path(fallback)


def _load_generator_config() -> Any:
    """Load generator config from project spec or return defaults."""
    from prisme.spec.project import GeneratorConfig

    toml_path = Path("prisme.toml")
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config
            from prisme.utils.spec_loader import load_project_spec

            config = load_prisme_config(toml_path)
            project_path = Path(config.project.project_path)
            if project_path.exists():
                project_spec = load_project_spec(project_path)
                return project_spec.generator
        except Exception:
            pass
    return GeneratorConfig()


def _get_project_paths() -> tuple[Path | None, Path | None, str | None]:
    """Get backend and frontend paths from spec or defaults.

    Returns:
        Tuple of (backend_path, frontend_path, package_name)
        Paths are the parent directories containing pyproject.toml/package.json.
        package_name is the Python package name for the backend.
    """
    # Try to load spec to get generator config
    spec_file = _resolve_spec_file()

    backend_path: Path | None = None
    frontend_path: Path | None = None
    package_name: str | None = None

    if spec_file:
        try:
            from prisme.utils.spec_loader import load_spec_from_file

            spec = load_spec_from_file(spec_file)
            gen_config = _load_generator_config()

            # Get paths from generator config
            backend_output = Path(gen_config.backend_output)
            frontend_output = Path(gen_config.frontend_output)

            # Backend path is the parent that contains pyproject.toml
            # e.g., if backend_output is "apps/api/src/pkg", find "apps/api"
            backend_candidate = backend_output
            while backend_candidate != Path(".") and backend_candidate.parent != backend_candidate:
                if (backend_candidate / "pyproject.toml").exists():
                    backend_path = backend_candidate
                    break
                backend_candidate = backend_candidate.parent

            # Frontend path is similar - find parent with package.json
            frontend_candidate = frontend_output
            while (
                frontend_candidate != Path(".") and frontend_candidate.parent != frontend_candidate
            ):
                if (frontend_candidate / "package.json").exists():
                    frontend_path = frontend_candidate
                    break
                frontend_candidate = frontend_candidate.parent

            # Package name from spec
            from prisme.utils.case_conversion import to_snake_case

            package_name = to_snake_case(spec.name)

        except Exception:
            pass  # Fall back to defaults

    # Fall back to standard monorepo structure
    if backend_path is None and Path("packages/backend").exists():
        backend_path = Path("packages/backend")

    if frontend_path is None and Path("packages/frontend").exists():
        frontend_path = Path("packages/frontend")

    # Detect package name from backend if not from spec
    if package_name is None and backend_path:
        src_path = backend_path / "src"
        if src_path.exists():
            excluded_dirs = ("api", "models", "schemas", "services", "mcp", "mcp_server", "tests")
            for pkg in src_path.iterdir():
                if pkg.is_dir() and not pkg.name.startswith("_") and pkg.name not in excluded_dirs:
                    package_name = pkg.name
                    break

    return backend_path, frontend_path, package_name


@click.group()
@click.version_option(package_name="prisme")
def main() -> None:
    """Prism - Code generation framework for full-stack applications.

    "One spec, full spectrum."
    """


# =============================================================================
# CREATE COMMAND
# =============================================================================


@main.command()
@click.argument("project_name")
@click.option("--spec", "-s", type=click.Path(exists=True), help="Path to initial StackSpec file")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["minimal", "full", "saas", "api-only"]),
    default="full",
    help="Project template",
)
@click.option(
    "--package-manager",
    type=click.Choice(["npm", "pnpm", "yarn", "bun"]),
    default="npm",
    help="Node.js package manager",
)
@click.option(
    "--python-manager",
    type=click.Choice(["pip", "poetry", "uv", "pdm"]),
    default="uv",
    help="Python package manager",
)
@click.option(
    "--database",
    type=click.Choice(["postgresql", "sqlite"]),
    default="postgresql",
    help="Database backend",
)
@click.option("--no-install", is_flag=True, help="Skip dependency installation")
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--docker", is_flag=True, help="Generate Docker configuration files")
@click.option("--no-ci", is_flag=True, help="Skip CI/CD workflows generation")
@click.option("--pre-commit", is_flag=True, help="Generate pre-commit/pre-push hooks configuration")
@click.option("--docs", is_flag=True, help="Generate MkDocs documentation setup")
@click.option("--devcontainer", is_flag=True, help="Generate VS Code dev container configuration")
@click.option(
    "--full-dx", is_flag=True, help="Enable all DX features (--pre-commit --docs --devcontainer)"
)
@click.option("--yes", "-y", is_flag=True, help="Skip interactive prompts, use defaults")
def create(
    project_name: str,
    spec: str | None,
    template: str,
    package_manager: str,
    python_manager: str,
    database: str,
    no_install: bool,
    no_git: bool,
    docker: bool,
    no_ci: bool,
    pre_commit: bool,
    docs: bool,
    devcontainer: bool,
    full_dx: bool,
    yes: bool,
) -> None:
    """Create a new Prism project.

    PROJECT_NAME is the name of the project directory to create.
    """
    console.print(
        Panel.fit(
            f"[bold blue]🔮 Creating Prism project:[/] {project_name}",
            border_style="blue",
        )
    )

    # Get template
    project_template = template_registry.get(template)
    if project_template is None:
        console.print(f"[red]Template not found: {template}[/]")
        sys.exit(1)

    # Resolve project path - handle "." as current directory and normalize absolute paths
    cwd = Path.cwd().resolve()
    if project_name == ".":
        project_path = cwd
        # Use the directory name as the actual project name for templates
        actual_project_name = cwd.name
    elif os.path.isabs(project_name):
        # Extract only the final directory name from absolute paths
        project_path = Path(project_name)
        actual_project_name = project_path.name
    else:
        project_path = cwd / project_name
        actual_project_name = project_name

    # Sanitize project name for use in paths and package names
    # Remove any path separators and invalid characters
    actual_project_name = re.sub(r"[^\w\-]", "_", actual_project_name)

    # Preserve the entire specs folder if it exists
    specs_folder_backup: dict[str, str] = {}
    specs_folder = project_path / "specs"

    if project_path.exists():
        if not yes and not click.confirm(f"Directory {project_name} already exists. Overwrite?"):
            console.print("[yellow]Aborted.[/]")
            return

        # Backup specs folder contents if it exists
        if specs_folder.exists():
            for spec_file_path in specs_folder.rglob("*"):
                if spec_file_path.is_file():
                    rel_path = spec_file_path.relative_to(project_path)
                    specs_folder_backup[str(rel_path)] = spec_file_path.read_text()

        # For "." we can't delete the current directory, so we'll overlay files
        # For named directories, we delete and recreate
        if project_name != ".":
            shutil.rmtree(project_path)
            project_path.mkdir(parents=True)
    else:
        project_path.mkdir(parents=True)

    # Restore specs folder contents
    for spec_rel_path, spec_content in specs_folder_backup.items():
        restored_file = project_path / spec_rel_path
        restored_file.parent.mkdir(parents=True, exist_ok=True)
        restored_file.write_text(spec_content)

    # Prepare template context
    # Create a human-readable title from the project name
    project_title = actual_project_name.replace("-", " ").replace("_", " ").title()
    context = {
        "project_name": actual_project_name,
        "project_name_snake": to_snake_case(actual_project_name),
        "project_title": project_title,
        "description": f"{project_title} - Built with Prism",
        "database": database,
        "package_manager": package_manager,
        "python_manager": python_manager,
        "include_docker": docker,
        "include_redis": "False",
        "include_ci": not no_ci,
    }

    # Render and write template files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)

        for file_path, content in project_template.render(context):
            # Skip generating specs/models.py if user provided their own spec
            if spec and file_path == Path("specs/models.py"):
                continue

            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Restore any backed up specs folder files (may have been overwritten by template)
        for backup_path, backup_content in specs_folder_backup.items():
            restored_file = project_path / backup_path
            restored_file.parent.mkdir(parents=True, exist_ok=True)
            restored_file.write_text(backup_content)

        progress.update(task, description="Project structure created")

        # Scaffold frontend for full/saas templates using create-vite
        if template in ("full", "saas"):
            progress.update(task, description="Scaffolding frontend with Vite...")
            if _scaffold_frontend(project_path, package_manager):
                progress.update(task, description="Frontend scaffolded")
                # Configure frontend with Prism-specific settings
                progress.update(task, description="Configuring frontend for Prism...")
                _configure_frontend_for_prism(project_path, context)
                progress.update(task, description="Frontend configured")
            else:
                console.print("[yellow]Warning: Could not scaffold frontend with Vite[/]")

        # Link spec file in prisme.toml if provided
        if spec:
            spec_source = Path(spec)
            # Resolve to absolute path for comparison (use saved cwd, not current)
            if spec_source.is_absolute():
                spec_abs = spec_source.resolve()
            else:
                spec_abs = (cwd / spec_source).resolve()

            # Validate spec is within project folder
            try:
                spec_path_rel = spec_abs.relative_to(project_path.resolve())
            except ValueError:
                console.print(
                    f"[red]Error: Spec file must be within the project folder.[/]\n"
                    f"  Spec: {spec_abs}\n"
                    f"  Project: {project_path.resolve()}"
                )
                sys.exit(1)

            # Verify the spec file exists
            if not spec_abs.exists():
                console.print(f"[red]Error: Spec file not found: {spec_abs}[/]")
                sys.exit(1)

            # Update prisme.toml with the relative spec path
            config_file = project_path / "prisme.toml"
            if config_file.exists():
                config_content = config_file.read_text()
                config_content = config_content.replace(
                    'spec_path = "specs/models.py"',
                    f'spec_path = "{spec_path_rel}"',
                )
                config_file.write_text(config_content)
            progress.update(task, description="Spec path configured")

        # Initialize git
        if not no_git:
            progress.update(task, description="Initializing git...")
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=project_path,
                    capture_output=True,
                    check=True,
                )
            except Exception:
                console.print("[yellow]Warning: Could not initialize git[/]")

        # Generate Docker configuration if requested
        if docker:
            progress.update(task, description="Generating Docker configuration...")
            _generate_docker_config(project_path, actual_project_name, template)
            progress.update(task, description="Docker configuration generated")

        # Generate CI/CD workflows if requested
        if not no_ci:
            progress.update(task, description="Generating CI/CD workflows...")
            _generate_ci_config(project_path, actual_project_name, template)
            progress.update(task, description="CI/CD workflows generated")

        # Handle --full-dx convenience flag
        if full_dx:
            pre_commit = True
            docs = True
            devcontainer = True

        # Generate pre-commit hooks if requested
        if pre_commit:
            progress.update(task, description="Generating pre-commit hooks...")
            _generate_precommit_config(project_path, actual_project_name, template, python_manager)
            progress.update(task, description="Pre-commit hooks generated")

        # Generate documentation setup if requested
        if docs:
            progress.update(task, description="Generating documentation setup...")
            _generate_docs_config(project_path, actual_project_name, context)
            progress.update(task, description="Documentation setup generated")

        # Generate dev container if requested
        if devcontainer:
            progress.update(task, description="Generating dev container configuration...")
            _generate_devcontainer_config(project_path, actual_project_name, template)
            progress.update(task, description="Dev container configuration generated")

        # Install dependencies
        if not no_install:
            progress.update(task, description="Installing dependencies...")
            _install_dependencies(project_path, python_manager, package_manager, template)

    # Success message
    console.print()

    # Build next steps based on what was generated
    if project_name == ".":
        next_steps = "Next steps:\n"
        next_steps += "  prisme generate    # Generate code from spec\n"
        if docker:
            next_steps += "  prisme dev --docker # Start Docker development environment\n"
        else:
            next_steps += "  prisme dev         # Start development servers\n"
        if not docker:
            next_steps += "  prisme docker init # (Optional) Generate Docker config"
    else:
        next_steps = "Next steps:\n"
        next_steps += f"  cd {project_name}\n"
        next_steps += "  prisme generate    # Generate code from spec\n"
        if docker:
            next_steps += "  prisme dev --docker # Start Docker development environment\n"
        else:
            next_steps += "  prisme dev         # Start development servers\n"
        if not docker:
            next_steps += "  prisme docker init # (Optional) Generate Docker config"

    console.print(
        Panel.fit(
            f"[green]✅ Project created successfully![/]\n\n{next_steps}",
            title="Success",
            border_style="green",
        )
    )


def _generate_docker_config(
    project_path: Path,
    project_name: str,
    template: str,
) -> None:
    """Generate Docker configuration files for the project.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        template: Template type (full, saas, minimal, api-only)
    """
    from prisme.docker import ComposeConfig, ComposeGenerator

    # Determine paths based on template
    if template in ("full", "saas"):
        backend_path = "packages/backend"
        frontend_path = "packages/frontend"
        backend_module = to_snake_case(project_name)
    else:  # minimal or api-only
        backend_path = "."
        frontend_path = None  # No frontend for API-only
        backend_module = to_snake_case(project_name)

    # Create configuration
    config = ComposeConfig(
        project_name=project_name.replace("-", "_"),
        backend_path=backend_path,
        frontend_path=frontend_path or "frontend",  # Fallback
        backend_module=backend_module,
        use_redis=False,  # Can be enabled later with --redis flag
    )

    # Generate files
    generator = ComposeGenerator(project_path)
    generator.generate(config)


def _generate_ci_config(
    project_path: Path,
    project_name: str,
    template: str,
) -> None:
    """Generate CI/CD workflows for the project.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        template: Template type (full, saas, minimal, api-only)
    """
    from prisme.ci import CIConfig, GitHubCIGenerator

    # Determine if frontend is included
    include_frontend = template in ("full", "saas")

    # Create configuration
    config = CIConfig(
        project_name=project_name,
        include_frontend=include_frontend,
        use_redis=False,  # Can be detected later from spec
        enable_codecov=True,
        enable_dependabot=True,
        enable_semantic_release=True,
        enable_commitlint=True,
    )

    # Generate files
    generator = GitHubCIGenerator(project_path)
    generator.generate(config)


def _generate_precommit_config(
    project_path: Path,
    project_name: str,
    template: str,
    python_manager: str,
) -> None:
    """Generate pre-commit hooks configuration.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        template: Template type (full, saas, minimal, api-only)
        python_manager: Python package manager (uv, poetry, pip)
    """
    from prisme.dx import PreCommitConfig, PreCommitGenerator

    include_frontend = template in ("full", "saas")

    config = PreCommitConfig(
        project_name=project_name,
        include_frontend=include_frontend,
        python_manager=python_manager,
        enable_mypy=True,
        enable_pytest=True,
        enable_ruff=True,
    )

    generator = PreCommitGenerator(project_path)
    generator.generate(config)


def _generate_docs_config(
    project_path: Path,
    project_name: str,
    context: dict[str, Any],
) -> None:
    """Generate documentation setup.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        context: Template context with project_title and description
    """
    from prisme.dx import DocsConfig, DocsGenerator

    config = DocsConfig(
        project_name=project_name,
        project_title=context.get("project_title", project_name),
        description=context.get("description", f"{project_name} documentation"),
        include_api_docs=True,
        include_readthedocs=True,
    )

    generator = DocsGenerator(project_path)
    generator.generate(config)


def _generate_devcontainer_config(
    project_path: Path,
    project_name: str,
    template: str,
) -> None:
    """Generate VS Code dev container configuration.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        template: Template type (full, saas, minimal, api-only)
    """
    from prisme.dx import DevContainerConfig, DevContainerGenerator

    include_frontend = template in ("full", "saas")

    config = DevContainerConfig(
        project_name=project_name,
        include_frontend=include_frontend,
        include_postgres=True,
        include_redis=False,
    )

    generator = DevContainerGenerator(project_path)
    generator.generate(config)


def _install_dependencies(
    project_path: Path,
    python_manager: str,
    package_manager: str,
    template: str,
) -> None:
    """Install project dependencies."""
    try:
        if template in ("full", "saas"):
            # Backend dependencies
            backend_path = project_path / "packages" / "backend"
            if backend_path.exists():
                if python_manager == "uv":
                    subprocess.run(["uv", "sync"], cwd=backend_path, capture_output=True)
                elif python_manager == "poetry":
                    subprocess.run(["poetry", "install"], cwd=backend_path, capture_output=True)

            # Frontend dependencies
            frontend_path = project_path / "packages" / "frontend"
            if frontend_path.exists():
                subprocess.run([package_manager, "install"], cwd=frontend_path, capture_output=True)
        else:
            # Single package project
            if python_manager == "uv":
                subprocess.run(["uv", "sync"], cwd=project_path, capture_output=True)
            elif python_manager == "poetry":
                subprocess.run(["poetry", "install"], cwd=project_path, capture_output=True)
    except Exception:
        console.print("[yellow]Warning: Could not install all dependencies[/]")


def _scaffold_frontend(
    project_path: Path,
    package_manager: str,
) -> bool:
    """Scaffold frontend using create-vite.

    Args:
        project_path: Path to the project directory.
        package_manager: Node.js package manager to use.

    Returns:
        True if scaffolding succeeded, False otherwise.
    """
    # Build the create-vite command based on package manager
    # All commands use --template react-ts and skip prompts with -y/--yes
    # npm: npm create vite@latest packages/frontend -- --template react-ts
    # pnpm: pnpm create vite packages/frontend --template react-ts
    # yarn: yarn create vite packages/frontend --template react-ts
    # bun: bun create vite packages/frontend --template react-ts

    if package_manager == "npm":
        cmd = [
            "npm",
            "create",
            "vite@latest",
            "packages/frontend",
            "--yes",  # Skip npm prompts
            "--",
            "--template",
            "react-ts",
        ]
    elif package_manager == "pnpm":
        cmd = [
            "pnpm",
            "create",
            "vite",
            "packages/frontend",
            "--template",
            "react-ts",
        ]
    elif package_manager == "yarn":
        cmd = [
            "yarn",
            "create",
            "vite",
            "packages/frontend",
            "--template",
            "react-ts",
        ]
    else:  # bun
        cmd = [
            "bun",
            "create",
            "vite",
            "packages/frontend",
            "--template",
            "react-ts",
        ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            stdin=subprocess.DEVNULL,  # Prevent interactive prompts
        )
        if result.returncode != 0:
            console.print(f"[yellow]  Vite scaffold failed: {result.stderr or result.stdout}[/]")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        console.print("[yellow]  Vite scaffolding timed out after 2 minutes[/]")
        return False
    except Exception as e:
        console.print(f"[yellow]  Vite scaffolding error: {e}[/]")
        return False


def _configure_frontend_for_prism(
    project_path: Path,
    context: dict[str, Any],
) -> None:
    """Add Prism-specific configuration to Vite-generated frontend.

    This enhances the Vite-scaffolded frontend with:
    - Tailwind CSS configuration
    - PostCSS configuration
    - Additional dependencies (urql, graphql, react-router-dom, etc.)
    - Prism-specific CSS styles

    Args:
        project_path: Path to the project directory.
        context: Template context with project variables.
    """
    import json

    frontend_path = project_path / "packages" / "frontend"

    # Ensure frontend directories exist (in case Vite didn't create them or was mocked)
    frontend_path.mkdir(parents=True, exist_ok=True)
    (frontend_path / "src").mkdir(parents=True, exist_ok=True)

    # Initialize template renderer
    renderer = TemplateRenderer()

    # Add tailwind.config.js with Nordic design palette
    tailwind_config = renderer.render_file("cli/tailwind.config.js.jinja2", context={})
    (frontend_path / "tailwind.config.js").write_text(tailwind_config)

    # Add postcss.config.js
    postcss_config = renderer.render_file("cli/postcss.config.js.jinja2", context={})
    (frontend_path / "postcss.config.js").write_text(postcss_config)

    # Add design system tokens (always regenerated - base tokens)
    design_tokens_css = renderer.render_file("cli/design-tokens.css.jinja2", context={"design": {}})
    (frontend_path / "src" / "design-tokens.css").write_text(design_tokens_css)

    # Add custom tokens file (only if doesn't exist - user customizations preserved)
    custom_tokens_path = frontend_path / "src" / "custom-tokens.css"
    if not custom_tokens_path.exists():
        custom_tokens_css = renderer.render_file("cli/custom-tokens.css.jinja2", context={})
        custom_tokens_path.write_text(custom_tokens_css)

    # Add Tailwind directives with Nordic styling to src/index.css
    index_css = renderer.render_file("cli/index.css.jinja2", context={})
    (frontend_path / "src" / "index.css").write_text(index_css)

    # Update or create package.json with Prism dependencies
    package_json_path = frontend_path / "package.json"
    if package_json_path.exists():
        package_data = json.loads(package_json_path.read_text())
    else:
        # Create a base package.json if Vite didn't create one (e.g., during tests)
        project_name_snake = context.get("project_name_snake", "frontend")
        package_data = {
            "name": f"{project_name_snake}-frontend",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "lint": "eslint .",
                "preview": "vite preview",
            },
            "dependencies": {
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
            },
            "devDependencies": {
                "@types/react": "^19.0.0",
                "@types/react-dom": "^19.0.0",
                "@vitejs/plugin-react": "^4.3.0",
                "typescript": "~5.6.0",
                "vite": "^6.0.0",
            },
        }

    # Add Prism-specific dependencies
    prism_dependencies = {
        "react-router-dom": "^6.22.0",
        "react-hook-form": "^7.50.0",
        "urql": "^4.0.0",
        "graphql": "^16.8.0",
        "graphql-ws": "^5.16.0",
        "lucide-react": "^0.460.0",  # Icon library for design system
    }
    package_data.setdefault("dependencies", {}).update(prism_dependencies)

    # Add Prism-specific dev dependencies
    prism_dev_dependencies = {
        "tailwindcss": "^3.4.0",
        "postcss": "^8.4.0",
        "autoprefixer": "^10.4.0",
        "@testing-library/react": "^16.0.0",
        "vitest": "^2.1.0",
        "@vitest/coverage-v8": "^2.1.0",
        "@testing-library/jest-dom": "^6.6.0",
        "jsdom": "^25.0.0",
    }
    package_data.setdefault("devDependencies", {}).update(prism_dev_dependencies)

    # Add test script if not present
    scripts = package_data.setdefault("scripts", {})
    if "test" not in scripts:
        scripts["test"] = "vitest"
    if "test:coverage" not in scripts:
        scripts["test:coverage"] = "vitest --coverage"

    package_json_path.write_text(json.dumps(package_data, indent=2) + "\n")

    # Update tsconfig.json to exclude test files and add vite/client types
    tsconfig_path = frontend_path / "tsconfig.json"
    if tsconfig_path.exists():
        tsconfig_data = json.loads(tsconfig_path.read_text())

        # Add __tests__ to exclude (prevents test files in production build)
        exclude = tsconfig_data.setdefault("exclude", [])
        if "**/__tests__/**" not in exclude:
            exclude.append("**/__tests__/**")

        # Add vite/client to compilerOptions.types (provides Vite type definitions)
        compiler_options = tsconfig_data.setdefault("compilerOptions", {})
        types = compiler_options.setdefault("types", [])
        if "vite/client" not in types:
            types.append("vite/client")

        tsconfig_path.write_text(json.dumps(tsconfig_data, indent=2) + "\n")

    # Create vitest config if it doesn't exist
    # Note: setupFiles points to where FrontendTestGenerator creates the setup file
    vitest_config = frontend_path / "vitest.config.ts"
    if not vitest_config.exists():
        vitest_config_content = renderer.render_file("cli/vitest.config.ts.jinja2", context={})
        vitest_config.write_text(vitest_config_content)

    # Create vite config with proxy settings for local development
    # This enables /graphql and /api requests to be proxied to the backend
    vite_config = frontend_path / "vite.config.ts"
    vite_config_content = renderer.render_file("cli/vite.config.ts.jinja2", context={})
    vite_config.write_text(vite_config_content)

    # Test setup file is created by FrontendTestGenerator to ensure single source of truth

    # Update index.html with project name and custom favicon
    project_name = context.get("project_name", "My Project")
    project_title = context.get(
        "project_title", project_name.replace("-", " ").replace("_", " ").title()
    )
    project_description = context.get("description", f"{project_title} - Built with Prism")

    index_html = renderer.render_file(
        "cli/index.html.jinja2",
        context={
            "project_title": project_title,
            "project_description": project_description,
            "dark_mode": True,
        },
    )
    (frontend_path / "index.html").write_text(index_html)

    # Create a modern SVG favicon with the project initial
    project_initial = project_name[0].upper() if project_name else "P"
    favicon_svg = renderer.render_file(
        "cli/favicon.svg.jinja2", context={"project_initial": project_initial}
    )
    (frontend_path / "public").mkdir(parents=True, exist_ok=True)
    (frontend_path / "public" / "favicon.svg").write_text(favicon_svg)
    # Also copy to root for Vite
    (frontend_path / "favicon.svg").write_text(favicon_svg)

    # Update App.tsx with Prism welcome content
    app_tsx = renderer.render_file(
        "cli/App.tsx.jinja2",
        context={
            "project_initial": project_initial,
            "project_title": project_title,
        },
    )
    (frontend_path / "src" / "App.tsx").write_text(app_tsx)


# =============================================================================
# GENERATE COMMAND
# =============================================================================


@main.command()
@click.argument("spec_path", type=click.Path(exists=True), required=False)
@click.option("--only", help="Comma-separated list of layers to generate")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files")
@click.option("--force", is_flag=True, help="Force overwrite all files")
@click.option("--diff", is_flag=True, help="Show diff of changes")
@click.option("--typecheck", is_flag=True, help="Run tsc --noEmit after generating frontend code")
def generate(
    spec_path: str | None,
    only: str | None,
    dry_run: bool,
    force: bool,
    diff: bool,
    typecheck: bool,
) -> None:
    """Generate code from a Prism specification.

    SPEC_PATH is the path to the specification file.
    If not provided, reads from prisme.config.py or defaults to specs/models.py.
    """
    # Check for evidence of 'prisme create' having been run (only when no spec provided)
    toml_path = Path("prisme.toml")
    legacy_config_path = Path("prism.config.py")
    if not spec_path and not toml_path.exists() and not legacy_config_path.exists() and not force:
        console.print()
        console.print("[yellow]⚠️  Warning: No prisme.toml found.[/]")
        console.print("[yellow]It looks like 'prisme create' has not been run for this project.[/]")
        console.print()
        console.print("To initialize a new project, run:")
        console.print("  [bold]prisme create <project-name>[/]")
        console.print()
        console.print("Or to generate in an existing project directory:")
        console.print("  [bold]cd <project-dir> && prisme generate[/]")
        console.print()
        console.print("[dim]Use --force to bypass this warning.[/]")
        console.print()
        sys.exit(1)

    spec_file: Path | None = None
    prism_config: PrismConfig | None = None
    prisme_config: PrismeConfig | None = None
    project_spec: ProjectSpec | None = None

    if spec_path:
        spec_file = Path(spec_path)
    else:
        # Try v2 config (prisme.toml) first
        if toml_path.exists():
            try:
                from prisme.config.loader import load_prisme_config

                prisme_config = load_prisme_config(toml_path)
                spec_file = Path(prisme_config.project.spec_path)

                # Load project spec if available
                project_path = Path(prisme_config.project.project_path)
                if project_path.exists():
                    try:
                        from prisme.utils.spec_loader import load_project_spec

                        project_spec = load_project_spec(project_path)
                    except Exception:
                        pass
            except Exception:
                pass

        # Fall back to legacy v1 config (prism.config.py)
        if spec_file is None and legacy_config_path.exists():
            try:
                from prisme import PrismConfig

                prism_config = PrismConfig.load_from_file(legacy_config_path)
                spec_file = Path(prism_config.spec_path)
            except Exception:
                pass

        # Fall back to default locations if not found in config
        if spec_file is None or not spec_file.exists():
            for candidate in [
                Path("specs/models.py"),
                Path("spec.py"),
            ]:
                if candidate.exists():
                    spec_file = candidate
                    break

    if spec_file is None:
        spec_file = Path("specs/models.py")

    if not spec_file.exists():
        console.print(f"[red]Specification file not found: {spec_file}[/]")
        console.print("Run [bold]prisme create[/] to create a new project or specify a spec file.")
        sys.exit(1)

    console.print(f"[bold blue]🔮 Generating code from:[/] {spec_file}")

    if dry_run:
        console.print("[yellow]Dry run mode - no files will be written[/]")
    if force:
        console.print("[yellow]Force mode - all files will be overwritten[/]")

    # Load spec
    try:
        stack_spec = load_spec_from_file(spec_file)
    except (SpecLoadError, SpecValidationError) as e:
        console.print(f"[red]Error loading specification: {e}[/]")
        sys.exit(1)

    # Ensure project_spec exists (required for generator config)
    if project_spec is None:
        from prisme.spec.project import ProjectSpec

        project_spec = ProjectSpec(name=stack_spec.name)

    # Override generator paths from config if specified
    backend_module_name = prism_config.backend_module_name if prism_config else None
    if prism_config:
        if prism_config.backend_path:
            project_spec.generator.backend_output = prism_config.backend_path
        if prism_config.frontend_path:
            project_spec.generator.frontend_output = prism_config.frontend_path

    # Use project_spec backend module name if available
    if project_spec and project_spec.backend.module_name:
        backend_module_name = project_spec.backend.module_name

    output_dir = Path.cwd()

    # Parse --only option
    layers = _parse_layers(only) if only else None

    # Create generator context
    context = GeneratorContext(
        domain_spec=stack_spec,
        output_dir=output_dir,
        dry_run=dry_run,
        force=force,
        backend_module_name=backend_module_name,
        project_spec=project_spec,
        config=prisme_config,
    )

    # Run generators
    results = _run_generators(context, layers)

    # Save consolidated manifest with v2 metadata
    if not dry_run:
        _save_generation_manifest(
            results=results,
            output_dir=output_dir,
            spec_file=spec_file,
            prisme_config=prisme_config,
            project_spec=project_spec,
        )

    # Validate backend structure and warn about missing core files
    if not layers or "models" in layers:
        _validate_backend_structure(stack_spec, output_dir)

    # Show summary
    _show_generation_summary(results)

    # Show migration warnings (issues #55 and #57)
    if not dry_run:
        _show_migration_warnings(stack_spec, results, output_dir)

    # Run TypeScript type-check if requested
    if typecheck and not dry_run:
        frontend_path = None
        if project_spec.generator.frontend_output:
            frontend_path = output_dir / project_spec.generator.frontend_output
        if not _run_frontend_typecheck(frontend_path):
            sys.exit(1)


def _parse_layers(only: str) -> set[str]:
    """Parse the --only option into a set of layers."""
    return {layer.strip().lower() for layer in only.split(",")}


def _run_generators(
    context: GeneratorContext,
    layers: set[str] | None,
) -> dict[str, GeneratorResult]:
    """Run all generators and return results."""
    results: dict[str, GeneratorResult] = {}

    generators: list[tuple[str, type]] = [
        # Backend
        ("models", ModelsGenerator),
        ("alembic", AlembicGenerator),
        ("schemas", SchemasGenerator),
        ("services", ServicesGenerator),
        ("auth", AuthGenerator),
        ("admin", AdminGenerator),
        ("api-key-auth", APIKeyAuthGenerator),
        ("rest", RESTGenerator),
        ("graphql", GraphQLGenerator),
        ("mcp", MCPGenerator),
        # Frontend
        ("types", TypeScriptGenerator),
        ("graphql-ops", GraphQLOpsGenerator),
        ("headless", HeadlessGenerator),
        ("design-system", DesignSystemGenerator),
        ("widgets", WidgetSystemGenerator),
        ("components", ComponentsGenerator),
        ("hooks", HooksGenerator),
        ("pages", PagesGenerator),
        ("frontend-auth", FrontendAuthGenerator),
        ("frontend-admin", FrontendAdminGenerator),
        ("profile", ProfilePagesGenerator),
        ("error-pages", ErrorPagesGenerator),
        ("search", SearchPageGenerator),
        ("dashboard", DashboardGenerator),
        ("router", RouterGenerator),
        # Testing
        ("backend-tests", BackendTestGenerator),
        ("frontend-tests", FrontendTestGenerator),
        # Infrastructure (from ProjectSpec)
        ("deploy", DeployGenerator),
        ("ci", CIGenerator),
        ("docker", DockerGenerator),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for name, generator_class in generators:
            # Skip if not in --only list
            if layers and name not in layers:
                continue

            task = progress.add_task(f"Generating {name}...", total=None)

            try:
                generator = generator_class(context)
                result = generator.generate()
                results[name] = result

                if result.errors:
                    progress.update(
                        task, description=f"[red]{name}: {len(result.errors)} errors[/]"
                    )
                else:
                    progress.update(task, description=f"[green]{name}: {result.written} files[/]")
            except Exception as e:
                results[name] = GeneratorResult(errors=[str(e)])
                progress.update(task, description=f"[red]{name}: error[/]")

    return results


def _save_generation_manifest(
    results: dict[str, GeneratorResult],
    output_dir: Path,
    spec_file: Path,
    prisme_config: PrismeConfig | None,
    project_spec: ProjectSpec | None,
) -> None:
    """Save a consolidated manifest with v2 metadata after generation."""
    from prisme.tracking.manifest import ManifestManager, TrackedFile, hash_content

    # Load existing manifest to preserve any existing tracking data
    manifest = ManifestManager.load(output_dir)

    # Populate v2 metadata fields
    try:
        from prisme import __version__

        manifest.prisme_version = __version__
    except Exception:
        pass

    # Hash the spec file
    if spec_file.exists():
        manifest.domain_hash = hash_content(spec_file.read_text())

    # Hash project spec if available
    if prisme_config:
        project_path = Path(prisme_config.project.project_path)
        if project_path.exists():
            manifest.project_hash = hash_content(project_path.read_text())
        manifest.config_version = prisme_config.config_version

    # Hash prisme.toml
    toml_path = Path("prisme.toml")
    if toml_path.exists():
        manifest.config_hash = hash_content(toml_path.read_text())

    # Set domain/project versions
    from prisme.spec.stack import PRISME_DOMAIN_VERSION

    manifest.domain_version = PRISME_DOMAIN_VERSION
    if project_spec:
        from prisme.spec.project import PRISME_PROJECT_VERSION

        manifest.project_version = PRISME_PROJECT_VERSION

    # Record which generators ran
    manifest.generators_enabled = list(results.keys())

    # Track all generated files from results
    from datetime import datetime

    for _name, result in results.items():
        for generated_file in result.files:
            manifest.track_file(
                TrackedFile(
                    path=str(generated_file.path),
                    strategy=generated_file.strategy.value,
                    content_hash=hash_content(generated_file.content),
                    generated_at=datetime.now().isoformat(),
                    has_hooks=generated_file.has_hooks,
                    extends=str(generated_file.extends) if generated_file.extends else None,
                )
            )

    ManifestManager.save(manifest, output_dir)


def _validate_backend_structure(stack_spec: Any, output_dir: Path) -> None:
    """Validate that required backend files exist and warn if missing."""
    # The package directory is backend_output / snake_case(project_name)
    package_name = to_snake_case(stack_spec.name)
    gen_config = _load_generator_config()
    backend_path = output_dir / gen_config.backend_output / package_name

    # Skip validation if the backend path doesn't exist (e.g., fresh project)
    if not backend_path.exists():
        return

    required_files = {
        "__init__.py": "Package initialization",
        "main.py": "FastAPI application entry point",
        "config.py": "Application configuration",
        "database.py": "Database connection and session management",
    }

    missing = []
    for filename, description in required_files.items():
        if not (backend_path / filename).exists():
            missing.append((filename, description))

    if missing:
        console.print()
        console.print("[yellow]⚠️  Warning: Core backend files are missing:[/]")
        for filename, description in missing:
            console.print(f"  [yellow]• {filename}[/] - {description}")
        console.print()
        console.print("[yellow]These files are typically created by 'prisme create'.[/]")
        console.print("[yellow]To fix this issue, run:[/]")
        console.print("  [bold]prisme create <project-name>[/]")
        console.print()


def _show_generation_summary(results: dict[str, GeneratorResult]) -> None:
    """Display generation summary."""
    console.print()

    table = Table(title="Generation Summary")
    table.add_column("Generator", style="cyan")
    table.add_column("Written", justify="right", style="green")
    table.add_column("Skipped", justify="right", style="yellow")
    table.add_column("Errors", justify="right", style="red")

    total_written = 0
    total_skipped = 0
    total_errors = 0

    for name, result in results.items():
        table.add_row(
            name,
            str(result.written),
            str(result.skipped),
            str(len(result.errors)),
        )
        total_written += result.written
        total_skipped += result.skipped
        total_errors += len(result.errors)

    table.add_section()
    table.add_row(
        "[bold]Total[/]",
        f"[bold]{total_written}[/]",
        f"[bold]{total_skipped}[/]",
        f"[bold]{total_errors}[/]",
    )

    console.print(table)

    if total_errors > 0:
        console.print()
        console.print("[red]Errors occurred during generation:[/]")
        for name, result in results.items():
            for error in result.errors:
                console.print(f"  [{name}] {error}")

    # Show override warnings
    _show_override_warnings()


def _show_override_warnings() -> None:
    """Show warnings about code overrides after generation."""
    from prisme.tracking.logger import OverrideLogger

    try:
        log = OverrideLogger.load(Path.cwd())
        unreviewed = log.get_unreviewed()

        if not unreviewed:
            return

        console.print()
        console.print(
            Panel(
                f"""[green]✓ {len(unreviewed)} file(s) with custom code were PRESERVED[/]

Your modifications were kept - the new generated code was not applied.
Review to ensure your custom code is compatible with any template changes.

[bold]What to do next:[/]
1. Run [bold cyan]prisme review list[/] to see preserved files
2. Run [bold cyan]prisme review diff <file>[/] to compare your code vs generated
3. Run [bold cyan]prisme test[/] to verify everything still works
4. Run [bold cyan]prisme review mark-reviewed <file>[/] when done
5. Or run [bold cyan]prisme review restore <file>[/] to replace with generated code

[dim]Tip: Use 'prisme review summary' to see an overview of all preserved files[/]""",
                title="🔒 Custom Code Preserved",
                border_style="green",
            )
        )
        console.print()

        # Show first few preserved files
        for override in unreviewed[:3]:
            console.print(f"  [green]✓ {override.path}[/] [dim](kept)[/]")
            if override.diff_summary:
                added = override.diff_summary.get("lines_added", 0)
                removed = override.diff_summary.get("lines_removed", 0)
                console.print(f"     [dim]Your code differs by +{added}, -{removed} lines[/]")

        if len(unreviewed) > 3:
            console.print(f"  [dim]... and {len(unreviewed) - 3} more[/]")

        console.print()

    except Exception:
        # Don't fail generation if override warnings fail
        pass


def _show_migration_warnings(
    stack_spec: Any, results: dict[str, GeneratorResult], output_dir: Path
) -> None:
    """Show warnings about missing or needed migrations after generation."""
    try:
        package_name = to_snake_case(stack_spec.name)
        gen_config = _load_generator_config()
        backend_path = output_dir / gen_config.backend_output / package_name
        alembic_versions = backend_path / "alembic" / "versions"

        # Issue #57: Check if no migrations exist at all
        if alembic_versions.exists():
            has_migrations = any(alembic_versions.glob("*.py"))
            if not has_migrations:
                console.print()
                console.print(
                    Panel(
                        "[yellow]No migrations found.[/]\n\n"
                        "Run the following command to create the initial migration:\n\n"
                        '  [bold cyan]uv run prisme db migrate -m "initial schema"[/]',
                        title="⚠ Initial Migration Required",
                        border_style="yellow",
                    )
                )
                return  # No need to check for model changes if no migrations exist

        # Issue #55: Check if model files were written (changed)
        models_result = results.get("models")
        if models_result and models_result.written > 0:
            # Try to detect specific field-level changes
            detail_lines: list[str] = []
            try:
                changes = detect_model_changes(models_result)
                for change in changes:
                    parts: list[str] = []
                    if change.added:
                        parts.append(f"added {', '.join(change.added)}")
                    if change.removed:
                        parts.append(f"removed {', '.join(change.removed)}")
                    if parts:
                        detail_lines.append(f"  - {change.model_name}: {'; '.join(parts)}")
            except Exception:
                pass

            if detail_lines:
                body = (
                    "[yellow]Model changes detected that may require a migration:[/]\n\n"
                    + "\n".join(detail_lines)
                    + "\n\n"
                    + '  Run: [bold cyan]uv run prisme db migrate -m "describe your changes"[/]'
                )
            else:
                body = (
                    "[yellow]Model files were updated during generation.[/]\n\n"
                    "If you changed your spec models, you may need a new migration:\n\n"
                    '  [bold cyan]uv run prisme db migrate -m "describe your changes"[/]'
                )

            console.print()
            console.print(
                Panel(
                    body,
                    title="⚠ Migration May Be Needed",
                    border_style="yellow",
                )
            )
    except Exception:
        # Don't fail generation if migration warnings fail
        pass


# =============================================================================
# DOCTOR COMMAND
# =============================================================================


@main.command()
def doctor() -> None:
    """Check project health and configuration.

    Validates the project setup, configuration files, and generated file integrity.
    """
    from prisme.tracking.manifest import ManifestManager, hash_content

    checks_passed = 0
    checks_failed = 0
    checks_warned = 0

    def _pass(msg: str) -> None:
        nonlocal checks_passed
        checks_passed += 1
        console.print(f"  [green]\u2713[/] {msg}")

    def _fail(msg: str) -> None:
        nonlocal checks_failed
        checks_failed += 1
        console.print(f"  [red]\u2717[/] {msg}")

    def _warn(msg: str) -> None:
        nonlocal checks_warned
        checks_warned += 1
        console.print(f"  [yellow]\u26a0[/] {msg}")

    console.print("[bold blue]Prism Doctor[/]")
    console.print()

    # 1. Check prisme.toml
    toml_path = Path("prisme.toml")
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config

            prisme_config = load_prisme_config(toml_path)
            _pass(f"prisme.toml is valid (config_version={prisme_config.config_version})")
        except Exception as e:
            _fail(f"prisme.toml is invalid: {e}")
            prisme_config = None
    else:
        _fail("prisme.toml not found")
        prisme_config = None

    # 2. Check domain spec (specs/models.py)
    spec_path = Path("specs/models.py")
    if prisme_config:
        spec_path = Path(prisme_config.project.spec_path)

    if spec_path.exists():
        try:
            stack_spec = load_spec_from_file(spec_path)
            _pass(f"Domain spec loaded ({len(stack_spec.models)} models)")
        except Exception as e:
            _fail(f"Domain spec error: {e}")
    else:
        _fail(f"Domain spec not found: {spec_path}")

    # 3. Check project spec (specs/project.py)
    project_path = Path("specs/project.py")
    if prisme_config:
        project_path = Path(prisme_config.project.project_path)

    if project_path.exists():
        try:
            from prisme.utils.spec_loader import load_project_spec

            load_project_spec(project_path)
            _pass("Project spec loaded")
        except Exception as e:
            _fail(f"Project spec error: {e}")
    else:
        _warn(f"Project spec not found: {project_path} (optional)")

    # 4. Check manifest and file integrity
    output_dir = Path.cwd()
    manifest = ManifestManager.load(output_dir)

    if manifest.files:
        _pass(f"Manifest found ({len(manifest.files)} tracked files)")

        # Check ALWAYS_OVERWRITE files for manual edits
        edited_files = []
        for path_str, tracked in manifest.files.items():
            if tracked.strategy == "always_overwrite":
                file_path = output_dir / path_str
                if file_path.exists():
                    current_hash = hash_content(file_path.read_text())
                    if current_hash != tracked.content_hash:
                        edited_files.append(path_str)

        if edited_files:
            _warn(f"{len(edited_files)} ALWAYS_OVERWRITE file(s) manually edited:")
            for f in edited_files[:5]:
                console.print(f"      {f}")
            if len(edited_files) > 5:
                console.print(f"      ... and {len(edited_files) - 5} more")
        else:
            _pass("No ALWAYS_OVERWRITE files manually edited")
    else:
        _warn("No manifest found — run 'prisme generate' first")

    # 5. Check required directories
    required_dirs = ["specs"]
    if prisme_config:
        required_dirs.append(
            prisme_config.project.spec_path.rsplit("/", 1)[0]
            if "/" in prisme_config.project.spec_path
            else "specs"
        )

    for dir_name in set(required_dirs):
        dir_path = Path(dir_name)
        if dir_path.exists():
            _pass(f"Directory exists: {dir_name}/")
        else:
            _fail(f"Directory missing: {dir_name}/")

    # Summary
    console.print()
    total = checks_passed + checks_failed + checks_warned
    console.print(f"[bold]{total} checks:[/] [green]{checks_passed} passed[/]", end="")
    if checks_warned:
        console.print(f", [yellow]{checks_warned} warnings[/]", end="")
    if checks_failed:
        console.print(f", [red]{checks_failed} failed[/]", end="")
    console.print()

    if checks_failed > 0:
        sys.exit(1)


# =============================================================================
# MIGRATE COMMAND
# =============================================================================


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would change without writing")
@click.option("--write", "do_write", is_flag=True, help="Write migration changes")
def migrate(dry_run: bool, do_write: bool) -> None:
    """Migrate spec and config to the latest schema version.

    Without flags, auto-migrates if safe. Use --dry-run to preview
    or --write to explicitly write changes.
    """
    from prisme.migration.detector import detect_versions

    project_dir = Path.cwd()
    info = detect_versions(project_dir)

    console.print("[bold blue]🔮 Prisme Migration[/]")
    console.print()

    if not any(
        [info.needs_config_migration, info.needs_domain_migration, info.needs_project_extraction]
    ):
        console.print("[green]✓ Project is up to date — no migrations needed.[/]")
        return

    changes: list[str] = []

    # Domain spec v1→v2
    if info.needs_domain_migration:
        spec_path_candidates = [
            project_dir / "specs" / "models.py",
            project_dir / "spec.py",
        ]
        for sp in spec_path_candidates:
            if sp.exists():
                from prisme.migration.domain_v1_to_v2 import migrate_domain_v1_to_v2

                should_write = do_write or (not dry_run)
                result = migrate_domain_v1_to_v2(sp, write=should_write)
                for change in result.changes:
                    changes.append(change)
                    console.print(f"  {'[dim](dry)[/] ' if dry_run else ''}[yellow]→[/] {change}")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠ {warning}[/]")

                # Extract project spec if needed
                if info.needs_project_extraction and result.extracted_project_fields:
                    from prisme.migration.project_extractor import extract_project_spec

                    project_out = project_dir / "specs" / "project.py"
                    if should_write:
                        extract_project_spec(
                            result.extracted_project_fields,
                            project_name=project_dir.name,
                            write_path=project_out,
                        )
                    changes.append(f"Created {project_out.relative_to(project_dir)}")
                    console.print(
                        f"  {'[dim](dry)[/] ' if dry_run else ''}[green]+[/] Created specs/project.py"
                    )
                break

    # Legacy config → prisme.toml
    if info.needs_config_migration:
        changes.append(
            "Legacy prism.config.py detected — manual migration to prisme.toml recommended"
        )
        console.print("  [yellow]⚠ Legacy prism.config.py found.[/]")
        console.print("    Run [bold]prisme create <name>[/] to generate a new prisme.toml,")
        console.print("    then move your settings over.")

    console.print()
    if dry_run:
        console.print(f"[dim]{len(changes)} change(s) would be applied. Use --write to apply.[/]")
    elif changes:
        console.print(f"[green]✓ {len(changes)} change(s) applied.[/]")
    else:
        console.print("[green]✓ No changes needed.[/]")


# =============================================================================
# PLAN / APPLY COMMANDS
# =============================================================================


@main.command()
@click.option("--spec", "spec_path", default=None, help="Path to spec file")
def plan(spec_path: str | None) -> None:
    """Preview what prisme generate would do and save a plan file.

    Runs generation in dry-run mode, collects all files that would be
    created or modified, and writes the plan to .prisme/plan.json.
    """
    from prisme.planning.planner import save_plan

    console.print("[bold blue]🔮 Prisme Plan[/]")
    console.print()

    # Resolve spec file
    resolved_spec = _resolve_spec_file() if not spec_path else Path(spec_path)
    if not resolved_spec.exists():
        console.print(f"[red]✗ Spec file not found: {resolved_spec}[/]")
        sys.exit(1)

    # Load spec
    try:
        domain_spec = load_spec_from_file(resolved_spec)
    except (SpecLoadError, SpecValidationError) as e:
        console.print(f"[red]✗ {e}[/]")
        sys.exit(1)

    # Load project spec + config
    toml_path = Path("prisme.toml")
    prisme_config = None
    project_spec_obj = None
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config
            from prisme.utils.spec_loader import load_project_spec

            prisme_config = load_prisme_config(toml_path)
            project_path = Path(prisme_config.project.project_path)
            if project_path.exists():
                project_spec_obj = load_project_spec(project_path)
        except Exception:
            pass

    # Create context with dry_run=True
    output_dir = Path.cwd()
    ctx = GeneratorContext(
        domain_spec=domain_spec,
        output_dir=output_dir,
        dry_run=True,
        project_spec=project_spec_obj,
        config=prisme_config,
    )

    # Run all generators to collect files
    all_files = []
    generators = _get_generators(ctx, project_spec_obj)
    for gen_cls in generators:
        try:
            gen = gen_cls(ctx)
            result = gen.generate()
            all_files.extend(result.files)
        except Exception:
            pass

    # Create and save plan
    from prisme.planning.planner import create_plan as _create_plan

    generation_plan = _create_plan(
        output_dir=output_dir,
        generated_files=all_files,
        spec_path=str(resolved_spec),
    )
    plan_path = save_plan(generation_plan, output_dir)

    # Display summary
    console.print(f"  Files to create: [green]{len(generation_plan.creates)}[/]")
    console.print(f"  Files to modify: [yellow]{len(generation_plan.modifies)}[/]")
    console.print(f"  Files to skip:   [dim]{len(generation_plan.skips)}[/]")
    console.print()
    console.print(f"  Plan saved to: [bold]{plan_path}[/]")
    console.print("  Run [bold]prisme apply[/] to execute this plan.")


@main.command()
def apply() -> None:
    """Execute the last saved generation plan.

    Reads .prisme/plan.json and runs generation for the planned files.
    """
    from prisme.planning.executor import PlanExecutionError, apply_plan

    console.print("[bold blue]🔮 Prisme Apply[/]")
    console.print()

    output_dir = Path.cwd()
    try:
        generation_plan = apply_plan(output_dir)
    except PlanExecutionError as e:
        console.print(f"[red]✗ {e}[/]")
        sys.exit(1)

    # Load the spec from the plan
    spec_path = Path(generation_plan.spec_path)
    if not spec_path.exists():
        console.print(f"[red]✗ Spec file from plan not found: {spec_path}[/]")
        sys.exit(1)

    try:
        domain_spec = load_spec_from_file(spec_path)
    except (SpecLoadError, SpecValidationError) as e:
        console.print(f"[red]✗ {e}[/]")
        sys.exit(1)

    # Load config
    toml_path = Path("prisme.toml")
    prisme_config = None
    project_spec_obj = None
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config
            from prisme.utils.spec_loader import load_project_spec

            prisme_config = load_prisme_config(toml_path)
            project_path = Path(prisme_config.project.project_path)
            if project_path.exists():
                project_spec_obj = load_project_spec(project_path)
        except Exception:
            pass

    # Filter generation to only planned files
    planned_paths = {f.path for f in generation_plan.files if f.action != "skip"}

    ctx = GeneratorContext(
        domain_spec=domain_spec,
        output_dir=output_dir,
        project_spec=project_spec_obj,
        config=prisme_config,
    )

    total_written = 0
    generators = _get_generators(ctx, project_spec_obj)
    for gen_cls in generators:
        try:
            gen = gen_cls(ctx)
            result = gen.generate()
            for f in result.files:
                if str(f.path) in planned_paths:
                    total_written += 1
        except Exception:
            pass

    console.print(f"  [green]✓ Applied plan: {total_written} file(s) written.[/]")

    # Remove plan file
    plan_file = output_dir / ".prisme" / "plan.json"
    if plan_file.exists():
        plan_file.unlink()
        console.print("  [dim]Plan file removed.[/]")


def _get_generators(
    ctx: GeneratorContext,
    project_spec_obj: Any | None,
) -> list[type]:
    """Get the list of generator classes to run."""
    generators: list[type] = [
        ModelsGenerator,
        SchemasGenerator,
        ServicesGenerator,
        RESTGenerator,
        TypeScriptGenerator,
        ComponentsGenerator,
        HooksGenerator,
        PagesGenerator,
        RouterGenerator,
    ]

    if project_spec_obj:
        if getattr(project_spec_obj, "auth", None) and project_spec_obj.auth.enabled:
            generators.append(AuthGenerator)
            generators.append(FrontendAuthGenerator)
        if (
            getattr(project_spec_obj.auth, "admin_panel", None)
            and project_spec_obj.auth.admin_panel.enabled
        ):
            generators.append(AdminGenerator)
            generators.append(FrontendAdminGenerator)
        if (
            getattr(project_spec_obj.exposure, "graphql", None)
            and project_spec_obj.exposure.graphql.enabled
        ):
            generators.append(GraphQLGenerator)
            generators.append(GraphQLOpsGenerator)
        if (
            getattr(project_spec_obj.exposure, "mcp", None)
            and project_spec_obj.exposure.mcp.enabled
        ):
            generators.append(MCPGenerator)
        if getattr(project_spec_obj, "testing", None) and project_spec_obj.testing.enabled:
            generators.append(BackendTestGenerator)
            generators.append(FrontendTestGenerator)

    generators.extend(
        [
            AlembicGenerator,
            DockerGenerator,
            CIGenerator,
            DeployGenerator,
            DesignSystemGenerator,
            ErrorPagesGenerator,
            ProfilePagesGenerator,
            SearchPageGenerator,
            DashboardGenerator,
            HeadlessGenerator,
            WidgetSystemGenerator,
        ]
    )

    return generators


# =============================================================================
# VALIDATE COMMAND
# =============================================================================


@main.command()
@click.argument("spec_path", type=click.Path(exists=True))
def validate(spec_path: str) -> None:
    """Validate a Prism specification file.

    SPEC_PATH is the path to the specification file to validate.
    """
    console.print(f"[bold blue]🔮 Validating specification:[/] {spec_path}")

    try:
        spec = load_spec_from_file(Path(spec_path))
        validate_spec(spec)

        console.print()
        console.print("[green]✅ Specification is valid![/]")
        console.print()

        # Show summary
        console.print(f"  Name: {spec.name}")
        console.print(f"  Version: {spec.version}")
        console.print(f"  Models: {len(spec.models)}")

        if spec.models:
            console.print()
            console.print("  Models defined:")
            for model in spec.models:
                console.print(f"    - {model.name} ({len(model.fields)} fields)")

    except SpecLoadError as e:
        console.print(f"[red]✗ Load error: {e}[/]")
        sys.exit(1)
    except SpecValidationError as e:
        console.print(f"[red]✗ Validation error: {e}[/]")
        if e.errors:
            for error in e.errors:
                console.print(f"  - {error['msg']}")
                if error.get("fix"):
                    console.print(f"    [cyan]fix:[/] {error['fix']}")
        sys.exit(1)


# =============================================================================
# DATABASE COMMANDS
# =============================================================================


@main.group()
def db() -> None:
    """Database operations."""


@db.command()
def init() -> None:
    """Initialize Alembic for database migrations.

    Note: Alembic is now automatically initialized during `prisme generate`.
    This command is kept for backwards compatibility and manual initialization.
    """
    console.print("[bold blue]🔮 Initializing Alembic...[/]")

    # Check if alembic is already initialized
    alembic_ini = Path("alembic.ini")
    if alembic_ini.exists():
        console.print("[yellow]Alembic already initialized (alembic.ini exists)[/]")
        console.print("  Run [bold]prisme db migrate -m 'initial'[/] to create first migration")
        return

    # Recommend using prisme generate instead
    console.print(
        "[yellow]Note: Alembic is now automatically configured during 'prisme generate'[/]"
    )
    console.print("  If you have a spec file, run: [bold]prisme generate <spec_file>[/]")
    console.print()

    try:
        # Run alembic init via uv
        console.print("  Running alembic init...")
        result = subprocess.run(
            ["uv", "run", "alembic", "init", "alembic"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Try without uv as fallback
            result = subprocess.run(
                ["alembic", "init", "alembic"],
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            console.print(f"[red]Error initializing Alembic:[/]\n{result.stderr}")
            return

        console.print("[green]  ✓ Alembic initialized[/]")

        # Try to detect the project structure and configure alembic
        _configure_alembic()

        console.print()
        console.print("[green]✅ Alembic initialization complete![/]")
        console.print()
        console.print("Next steps:")
        console.print("  1. Review alembic/env.py and update model imports if needed")
        console.print("  2. Run [bold]prisme db migrate -m 'initial'[/] to create first migration")

    except FileNotFoundError:
        console.print("[red]Alembic not found. Install with: uv add alembic[/]")


def _configure_alembic() -> None:
    """Configure alembic with project-specific settings."""
    env_py = Path("alembic/env.py")
    if not env_py.exists():
        return

    # Read the current env.py
    content = env_py.read_text()

    # Try to detect project structure
    # Look for a models module in common locations
    model_import = None

    # Check for monorepo structure
    if Path("packages/backend/src").exists():
        # Find the package name
        for pkg in Path("packages/backend/src").iterdir():
            if pkg.is_dir() and not pkg.name.startswith("_"):
                model_import = f"from {pkg.name}.models import Base"
                break
    # Check for standard src layout
    elif Path("src").exists():
        for pkg in Path("src").iterdir():
            if pkg.is_dir() and not pkg.name.startswith("_"):
                model_import = f"from {pkg.name}.models import Base"
                break

    if model_import:
        # Add import after existing imports
        import_marker = "from alembic import context"
        if import_marker in content:
            content = content.replace(
                import_marker,
                f"{import_marker}\n\n# Import your models here\n# {model_import}  # Uncomment after running prisme generate",
            )

        # Update target_metadata
        old_metadata = "target_metadata = None"
        new_metadata = "# target_metadata = Base.metadata  # Uncomment after running prisme generate\ntarget_metadata = None"
        content = content.replace(old_metadata, new_metadata)

        env_py.write_text(content)
        console.print("[green]  ✓ Configured alembic/env.py[/]")


@db.command(name="migrate")
@click.option("--message", "-m", help="Migration message")
def db_migrate(message: str | None) -> None:
    """Create and apply database migrations."""
    console.print("[bold blue]🔮 Running migrations...[/]")

    # Check for alembic
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        console.print("[yellow]Alembic not initialized.[/]")
        console.print("  Run [bold]prisme generate <spec_file>[/] to set up Alembic automatically")
        console.print("  Or run [bold]prisme db init[/] for manual initialization")
        return

    try:
        # Generate migration
        if message:
            console.print(f"  Creating migration: {message}")
            result = subprocess.run(
                ["uv", "run", "alembic", "revision", "--autogenerate", "-m", message],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(f"[red]Error creating migration:[/]\n{result.stderr}")
                return
            console.print("[green]  ✓ Migration created[/]")

        # Apply migrations
        console.print("  Applying migrations...")
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ Migrations applied successfully![/]")
        else:
            console.print(f"[red]Error applying migrations:[/]\n{result.stderr}")

    except FileNotFoundError:
        console.print("[red]Alembic not found. Install with: uv add alembic[/]")


@db.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def reset(yes: bool) -> None:
    """Reset the database."""
    if not yes and not click.confirm("This will delete all data. Are you sure?"):
        console.print("[yellow]Aborted.[/]")
        return

    console.print("[bold blue]🔮 Resetting database...[/]")

    try:
        # Downgrade to base
        result = subprocess.run(
            ["uv", "run", "alembic", "downgrade", "base"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print(f"[red]Error resetting:[/]\n{result.stderr}")
            return

        # Upgrade to head
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✅ Database reset complete![/]")
        else:
            console.print(f"[red]Error upgrading:[/]\n{result.stderr}")

    except FileNotFoundError:
        console.print("[red]Alembic not found. Install with: uv add alembic[/]")


@db.command()
def seed() -> None:
    """Seed the database with initial data."""
    console.print("[bold blue]🔮 Seeding database...[/]")

    # Look for seed file
    seed_file = Path("scripts/seed.py")
    if not seed_file.exists():
        seed_file = Path("seed.py")

    if seed_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(seed_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.print("[green]✅ Database seeded![/]")
                if result.stdout:
                    console.print(result.stdout)
            else:
                console.print(f"[red]Error seeding:[/]\n{result.stderr}")
        except Exception as e:
            console.print(f"[red]Error running seed script: {e}[/]")
    else:
        console.print("[yellow]No seed file found (scripts/seed.py or seed.py)[/]")
        console.print("Create a seed script to populate initial data.")


# =============================================================================
# DEV COMMAND
# =============================================================================


def _stream_output(
    process: subprocess.Popen,
    prefix: str,
    color: str,
    stop_event: threading.Event,
) -> None:
    """Stream output from a process with a colored prefix."""
    # Combine stdout and stderr for the process
    streams = []
    if process.stdout:
        streams.append(("stdout", process.stdout))
    if process.stderr:
        streams.append(("stderr", process.stderr))

    for _stream_name, stream in streams:
        try:
            for line in iter(stream.readline, ""):
                if stop_event.is_set():
                    break
                if line:
                    # Strip ANSI codes for cleaner output, or keep them
                    line = line.rstrip()
                    if line:
                        console.print(f"[{color}]{prefix}[/] {line}")
        except Exception:
            pass


def _create_output_reader(
    process: subprocess.Popen,
    prefix: str,
    color: str,
    stop_event: threading.Event,
) -> tuple[threading.Thread, threading.Thread]:
    """Create threads to read process output with color-coded prefixes.

    Color scheme:
    - API (backend): cyan prefix with dim cyan text
    - FRONTEND: magenta prefix with dim magenta text
    - MCP: green prefix with dim green text

    Args:
        process: The subprocess to read from.
        prefix: Pre-formatted prefix string (can include Rich markup).
        color: Base color for the output text.
        stop_event: Event to signal when to stop reading.

    Returns:
        Tuple of (stdout_thread, stderr_thread).
    """
    text_style = f"dim {color}"

    def format_line(line: str, is_stderr: bool = False) -> str:
        """Format a line with the appropriate prefix and color."""
        # Detect error patterns in the line content
        line_lower = line.lower()
        has_error = any(kw in line_lower for kw in ["error", "exception", "failed", "traceback"])
        has_warning = "warning" in line_lower

        if has_error:
            return f"{prefix} [bold red]{line}[/]"
        elif has_warning:
            return f"{prefix} [yellow]{line}[/]"
        elif is_stderr:
            return f"{prefix} [dim red]{line}[/]"
        else:
            return f"{prefix} [{text_style}]{line}[/]"

    def reader() -> None:
        try:
            # Read from stdout
            while not stop_event.is_set() and process.poll() is None:
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        line = line.rstrip()
                        if line:
                            console.print(format_line(line))

            # Drain remaining output
            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        console.print(format_line(line))
        except Exception:
            pass

    def stderr_reader() -> None:
        try:
            while not stop_event.is_set() and process.poll() is None:
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        line = line.rstrip()
                        if line:
                            console.print(format_line(line, is_stderr=True))

            # Drain remaining output
            if process.stderr:
                for line in process.stderr:
                    line = line.rstrip()
                    if line:
                        console.print(format_line(line, is_stderr=True))
        except Exception:
            pass

    stdout_thread = threading.Thread(target=reader, daemon=True)
    stderr_thread = threading.Thread(target=stderr_reader, daemon=True)
    return stdout_thread, stderr_thread


@main.command()
@click.option("--backend-only", is_flag=True, help="Start only the backend")
@click.option("--frontend-only", is_flag=True, help="Start only the frontend")
@click.option("--mcp", is_flag=True, help="Also start the MCP server")
@click.option("--docker", is_flag=True, help="Run in Docker")
@click.option("--watch", is_flag=True, help="Watch for spec changes and regenerate")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output from servers")
def dev(
    backend_only: bool,
    frontend_only: bool,
    mcp: bool,
    docker: bool,
    watch: bool,
    quiet: bool,
) -> None:
    """Start development servers."""
    console.print("[bold blue]🔮 Starting development servers...[/]")

    if docker:
        click.echo("⚠️  --docker is deprecated. Use 'prisme devcontainer up' instead.", err=True)
        _run_docker_dev()
        return

    # Determine what to run
    run_backend = not frontend_only
    run_frontend = not backend_only
    run_mcp = mcp

    processes: list[tuple[subprocess.Popen, str, str]] = []
    threads: list[threading.Thread] = []
    stop_event = threading.Event()

    try:
        if run_backend:
            console.print("  Starting backend...")
            backend_process = _start_backend(quiet=quiet)
            if backend_process:
                processes.append((backend_process, "[API]     ", "cyan"))
                console.print("[green]  ✓ Backend running at http://localhost:8000[/]")

                if not quiet:
                    stdout_t, stderr_t = _create_output_reader(
                        backend_process, "[bold cyan]API[/]      │", "cyan", stop_event
                    )
                    stdout_t.start()
                    stderr_t.start()
                    threads.extend([stdout_t, stderr_t])

        if run_frontend:
            console.print("  Starting frontend...")
            frontend_process = _start_frontend(quiet=quiet)
            if frontend_process:
                processes.append((frontend_process, "[FRONTEND]", "magenta"))
                console.print("[green]  ✓ Frontend running at http://localhost:5173[/]")

                if not quiet:
                    stdout_t, stderr_t = _create_output_reader(
                        frontend_process, "[bold magenta]FRONTEND[/] │", "magenta", stop_event
                    )
                    stdout_t.start()
                    stderr_t.start()
                    threads.extend([stdout_t, stderr_t])

        if run_mcp:
            console.print("  Starting MCP server...")
            mcp_process = _start_mcp(quiet=quiet)
            if mcp_process:
                processes.append((mcp_process, "[MCP]     ", "green"))
                console.print("[green]  ✓ MCP server running at http://localhost:8765/sse[/]")

                if not quiet:
                    stdout_t, stderr_t = _create_output_reader(
                        mcp_process, "[bold green]MCP[/]      │", "green", stop_event
                    )
                    stdout_t.start()
                    stderr_t.start()
                    threads.extend([stdout_t, stderr_t])

        if processes:
            console.print()
            console.print("Press Ctrl+C to stop all servers.")
            console.print()

            # Wait for any process to exit
            while True:
                for proc, prefix, _color in processes:
                    if proc.poll() is not None:
                        console.print(
                            f"[yellow]{prefix} Process exited with code {proc.returncode}[/]"
                        )
                        raise KeyboardInterrupt
                time.sleep(0.1)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Stopping servers...[/]")
        stop_event.set()
        for proc, _prefix, _color in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        console.print("[green]Servers stopped.[/]")


def _start_backend(quiet: bool = False) -> subprocess.Popen | None:
    """Start the backend development server."""
    import os

    # Get paths from spec or defaults
    backend_path, _, package_name = _get_project_paths()

    if backend_path is None:
        # Fall back to cwd if no backend found
        backend_path = Path.cwd()
        is_monorepo = False
    else:
        is_monorepo = True

    # Determine main module
    main_module = f"{package_name}.main:app" if package_name else None

    # Detect Python manager to use the right runner
    python_manager = _detect_python_manager(backend_path)

    # Build the uvicorn command
    if python_manager == "uv":
        base_cmd = ["uv", "run", "uvicorn"]
    elif python_manager == "poetry":
        base_cmd = ["poetry", "run", "uvicorn"]
    elif python_manager == "pdm":
        base_cmd = ["pdm", "run", "uvicorn"]
    else:
        base_cmd = ["uvicorn"]

    # Set up environment with PYTHONPATH for src layout
    env = os.environ.copy()
    # Remove VIRTUAL_ENV to let uv use the project's own venv
    # This prevents the "VIRTUAL_ENV does not match" warning
    env.pop("VIRTUAL_ENV", None)
    src_path = backend_path / "src"
    if src_path.exists():
        env["PYTHONPATH"] = str(src_path.resolve())

    # Try to start the backend
    modules_to_try = (
        [main_module]
        if main_module
        else [
            "src.main:app",
            "main:app",
            "app.main:app",
        ]
    )

    for module in modules_to_try:
        if module is None:
            continue
        try:
            cmd = [*base_cmd, module, "--reload", "--host", "0.0.0.0", "--port", "8000"]
            # For monorepo with src layout, add --app-dir to set the Python path
            if is_monorepo and src_path.exists():
                cmd.extend(["--app-dir", str(src_path.resolve())])
            if quiet:
                return subprocess.Popen(
                    cmd,
                    cwd=backend_path,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                return subprocess.Popen(
                    cmd,
                    cwd=backend_path,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
        except Exception:
            continue

    console.print("[yellow]Could not start backend. Check your project structure.[/]")
    return None


def _start_frontend(quiet: bool = False) -> subprocess.Popen | None:
    """Start the frontend development server."""
    # Get paths from spec or defaults
    _, frontend_path, _ = _get_project_paths()

    # Build list of paths to try
    frontend_paths = []
    if frontend_path:
        frontend_paths.append(frontend_path)
    # Add fallbacks
    frontend_paths.extend(
        [
            Path("packages/frontend"),
            Path("frontend"),
            Path.cwd(),
        ]
    )

    for fpath in frontend_paths:
        package_json = fpath / "package.json"
        if package_json.exists():
            # Determine package manager
            for pm in ["pnpm", "npm", "yarn", "bun"]:
                if shutil.which(pm):
                    try:
                        if quiet:
                            return subprocess.Popen(
                                [pm, "run", "dev"],
                                cwd=fpath,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        else:
                            return subprocess.Popen(
                                [pm, "run", "dev"],
                                cwd=fpath,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                bufsize=1,
                            )
                    except Exception:
                        continue

    console.print("[yellow]Could not start frontend. Check your project structure.[/]")
    return None


def _start_mcp(quiet: bool = False) -> subprocess.Popen | None:
    """Start the MCP server."""
    import os

    # Get paths from spec or defaults
    backend_path, _, package_name = _get_project_paths()

    if backend_path is None:
        backend_path = Path.cwd()

    # Determine package name for module path
    if package_name is None:
        # Try to infer from directory structure
        src_path = backend_path / "src"
        if src_path.exists():
            # Look for package directories in src
            for item in src_path.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    package_name = item.name
                    break

    if package_name is None:
        console.print("[yellow]Could not determine package name for MCP server.[/]")
        return None

    # Build MCP module path - get mcp_path from spec if available
    mcp_subdir = "mcp_server"  # Default
    try:
        gen_config = _load_generator_config()
        mcp_subdir = gen_config.mcp_path
    except Exception:
        pass

    mcp_module = f"{package_name}.{mcp_subdir}.server"

    # Set up environment with PYTHONPATH for src layout
    env = os.environ.copy()
    # Remove VIRTUAL_ENV to let uv use the project's own venv
    # This prevents the "VIRTUAL_ENV does not match" warning
    env.pop("VIRTUAL_ENV", None)
    src_path = backend_path / "src"
    if src_path.exists():
        env["PYTHONPATH"] = str(src_path.resolve())

    # Detect Python manager to use the right runner
    python_manager = _detect_python_manager(backend_path)

    # Use -c to avoid double-import warning when __init__.py imports from server
    run_code = f"from {mcp_module} import run_server; run_server(transport='sse')"

    # Build the python command
    if python_manager == "uv":
        python_cmd = ["uv", "run", "python", "-c", run_code]
    elif python_manager == "poetry":
        python_cmd = ["poetry", "run", "python", "-c", run_code]
    elif python_manager == "pdm":
        python_cmd = ["pdm", "run", "python", "-c", run_code]
    else:
        python_cmd = ["python", "-c", run_code]

    try:
        if quiet:
            return subprocess.Popen(
                python_cmd,
                cwd=backend_path,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            return subprocess.Popen(
                python_cmd,
                cwd=backend_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
    except Exception as e:
        console.print(f"[yellow]Could not start MCP server: {e}[/]")
        return None


def _run_docker_dev() -> None:
    """Run development servers using Docker Compose."""
    from prisme.docker import ComposeManager, DockerManager

    # Check if Docker is available
    if not DockerManager.is_available():
        console.print(
            "[yellow]Docker not found. Install Docker or use 'prisme dev' without --docker flag.[/yellow]"
        )
        console.print("Install: https://docs.docker.com/get-docker/")
        return

    # Check if docker-compose.dev.yml exists
    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        console.print("Run 'prisme generate' to create Docker configuration files.")
        return

    try:
        compose_mgr = ComposeManager(Path.cwd(), console=console)
        compose_mgr.start(rebuild=False)

        # Stream logs
        compose_mgr.stream_logs()
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Stopping services...[/yellow]")
        compose_mgr.stop()


# =============================================================================
# INSTALL COMMAND
# =============================================================================


@main.command()
@click.option("--backend-only", is_flag=True, help="Install only backend dependencies")
@click.option("--frontend-only", is_flag=True, help="Install only frontend dependencies")
def install(backend_only: bool, frontend_only: bool) -> None:
    """Install project dependencies."""
    console.print("[bold blue]🔮 Installing dependencies...[/]")

    run_backend = not frontend_only
    run_frontend = not backend_only

    if run_backend:
        _install_backend_deps()

    if run_frontend:
        _install_frontend_deps()

    console.print()
    console.print("[green]✅ Dependencies installed![/]")


def _install_backend_deps() -> None:
    """Install backend dependencies."""
    # Get paths from spec or defaults
    backend_path, _, _ = _get_project_paths()

    if backend_path is None:
        backend_path = Path.cwd()

    if not backend_path.exists():
        console.print(f"[yellow]  No backend package found at {backend_path}[/]")
        return

    # Detect Python package manager
    python_manager = _detect_python_manager(backend_path)

    console.print(f"  Installing backend dependencies with {python_manager}...")

    try:
        if python_manager == "uv":
            # Use --all-extras to install dev dependencies
            result = subprocess.run(
                ["uv", "sync", "--all-extras"],
                cwd=backend_path,
                capture_output=True,
                text=True,
            )
        elif python_manager == "poetry":
            result = subprocess.run(
                ["poetry", "install"],
                cwd=backend_path,
                capture_output=True,
                text=True,
            )
        elif python_manager == "pdm":
            result = subprocess.run(
                ["pdm", "install"],
                cwd=backend_path,
                capture_output=True,
                text=True,
            )
        else:  # pip
            # Install with dev dependencies for testing
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
                cwd=backend_path,
                capture_output=True,
                text=True,
            )

        if result.returncode == 0:
            console.print("[green]  ✓ Backend dependencies installed[/]")
        else:
            console.print(f"[red]  Error installing backend: {result.stderr}[/]")

    except FileNotFoundError as e:
        console.print(f"[yellow]  Warning: {e}[/]")


def _install_frontend_deps() -> None:
    """Install frontend dependencies."""
    # Get paths from spec or defaults
    _, frontend_path, _ = _get_project_paths()

    if frontend_path is None:
        # Try fallbacks
        for candidate in [Path("packages/frontend"), Path("frontend")]:
            if candidate.exists():
                frontend_path = candidate
                break

    if frontend_path is None or not frontend_path.exists():
        # Try current directory
        if not Path("package.json").exists():
            console.print("[yellow]  No frontend package found[/]")
            return
        frontend_path = Path.cwd()

    # Detect Node package manager
    node_manager = _detect_node_manager(frontend_path)

    console.print(f"  Installing frontend dependencies with {node_manager}...")

    try:
        result = subprocess.run(
            [node_manager, "install"],
            cwd=frontend_path,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]  ✓ Frontend dependencies installed[/]")
        else:
            console.print(f"[red]  Error installing frontend: {result.stderr}[/]")

    except FileNotFoundError as e:
        console.print(f"[yellow]  Warning: {e}[/]")


def _detect_python_manager(path: Path) -> str:
    """Detect the Python package manager used in a directory.

    Prefers uv when available as it's faster and handles pyproject.toml natively.
    """
    # Check for specific lock files first
    if (path / "poetry.lock").exists() and shutil.which("poetry"):
        return "poetry"
    if (path / "pdm.lock").exists() and shutil.which("pdm"):
        return "pdm"
    # Prefer uv if available and there's a pyproject.toml
    if ((path / "pyproject.toml").exists() or (path / "uv.lock").exists()) and shutil.which("uv"):
        return "uv"
    return "pip"


def _detect_node_manager(path: Path) -> str:
    """Detect the Node package manager used in a directory."""
    if (path / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
        return "pnpm"
    if (path / "yarn.lock").exists() and shutil.which("yarn"):
        return "yarn"
    if (path / "bun.lockb").exists() and shutil.which("bun"):
        return "bun"
    return "npm"


def _run_frontend_typecheck(frontend_path: Path | None = None) -> bool:
    """Run TypeScript type-check on frontend code.

    Args:
        frontend_path: Path to frontend directory. If None, tries common locations.

    Returns:
        True on success, False on failure.
    """
    if frontend_path is None:
        for candidate in [Path("packages/frontend"), Path("frontend")]:
            if candidate.exists():
                frontend_path = candidate
                break

    if frontend_path is None or not frontend_path.exists():
        if Path("package.json").exists():
            frontend_path = Path.cwd()
        else:
            console.print("[yellow]  No frontend directory found for type-check[/]")
            return True

    tsconfig = frontend_path / "tsconfig.json"
    if not tsconfig.exists():
        console.print("[yellow]  No tsconfig.json found, skipping type-check[/]")
        return True

    # Check if there's a typecheck script in package.json
    import json

    package_json = frontend_path / "package.json"
    use_script = False
    if package_json.exists():
        try:
            pkg_data = json.loads(package_json.read_text())
            if "typecheck" in pkg_data.get("scripts", {}):
                use_script = True
        except Exception:
            pass

    node_manager = _detect_node_manager(frontend_path)

    console.print("  Running TypeScript type-check...")

    cmd = [node_manager, "run", "typecheck"] if use_script else ["npx", "tsc", "--noEmit"]

    try:
        result = subprocess.run(cmd, cwd=frontend_path)
        if result.returncode == 0:
            console.print("[green]  ✓ TypeScript type-check passed[/]")
            return True
        else:
            console.print("[red]  ✗ TypeScript type-check failed[/]")
            return False
    except FileNotFoundError as e:
        console.print(f"[red]  Error: {e}[/]")
        return False


# =============================================================================
# TEST COMMAND
# =============================================================================


@main.command()
@click.option("--backend-only", is_flag=True, help="Run only backend tests")
@click.option("--frontend-only", is_flag=True, help="Run only frontend tests")
@click.option("--coverage", is_flag=True, help="Run with coverage")
@click.option("--typecheck/--no-typecheck", default=True, help="Run TypeScript type-check")
@click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
def test(
    backend_only: bool,
    frontend_only: bool,
    coverage: bool,
    typecheck: bool,
    pytest_args: tuple,
) -> None:
    """Run the test suite."""
    console.print("[bold blue]🔮 Running tests...[/]")

    run_backend = not frontend_only
    run_frontend = not backend_only

    backend_success = True
    frontend_success = True
    typecheck_success = True

    if run_backend:
        backend_success = _run_backend_tests(coverage, pytest_args)

    if run_frontend:
        if typecheck:
            typecheck_success = _run_frontend_typecheck()
        frontend_success = _run_frontend_tests(coverage)

    console.print()
    if backend_success and frontend_success and typecheck_success:
        console.print("[green]✅ All tests passed![/]")
    else:
        console.print("[red]❌ Some tests failed[/]")
        sys.exit(1)


def _run_backend_tests(coverage: bool, extra_args: tuple) -> bool:
    """Run backend tests with pytest."""
    # Get paths from spec or defaults
    backend_path, _, _ = _get_project_paths()

    if backend_path is None:
        backend_path = Path.cwd()

    if not backend_path.exists():
        console.print(f"[yellow]  No backend package found at {backend_path}[/]")
        return True

    # Check if there are tests
    tests_path = backend_path / "tests"
    if not tests_path.exists():
        console.print("[yellow]  No tests directory found in backend[/]")
        return True

    # Detect Python package manager
    python_manager = _detect_python_manager(backend_path)

    console.print("  Running backend tests...")

    # Build command
    if python_manager == "uv":
        cmd = ["uv", "run", "pytest"]
    elif python_manager == "poetry":
        cmd = ["poetry", "run", "pytest"]
    elif python_manager == "pdm":
        cmd = ["pdm", "run", "pytest"]
    else:
        cmd = [sys.executable, "-m", "pytest"]

    if coverage:
        cmd.append("--cov")

    cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            cwd=backend_path,
        )

        if result.returncode == 0:
            console.print("[green]  ✓ Backend tests passed[/]")
            return True
        else:
            console.print("[red]  ✗ Backend tests failed[/]")
            return False

    except FileNotFoundError as e:
        console.print(f"[red]  Error: {e}[/]")
        return False


def _run_frontend_tests(coverage: bool) -> bool:
    """Run frontend tests with vitest."""
    # Get paths from spec or defaults
    _, frontend_path, _ = _get_project_paths()

    if frontend_path is None:
        # Try fallbacks
        for candidate in [Path("packages/frontend"), Path("frontend")]:
            if candidate.exists():
                frontend_path = candidate
                break

    if frontend_path is None or not frontend_path.exists():
        # Try current directory
        if not Path("package.json").exists():
            console.print("[yellow]  No frontend package found[/]")
            return True
        frontend_path = Path.cwd()

    # Check if vitest is configured
    package_json = frontend_path / "package.json"
    if not package_json.exists():
        return True

    import json

    try:
        pkg_data = json.loads(package_json.read_text())
        scripts = pkg_data.get("scripts", {})
        if "test" not in scripts:
            console.print("[yellow]  No test script found in frontend package.json[/]")
            return True
    except Exception:
        return True

    # Check if test files exist before running vitest
    # Tests are generated to src/__tests__/ by FrontendTestGenerator
    tests_dir = frontend_path / "src" / "__tests__"
    if not tests_dir.exists():
        console.print("[yellow]  No test files found (src/__tests__/ not found)[/]")
        console.print("[yellow]  Run 'prisme generate' to generate tests[/]")
        return True

    # Check if there are actual test files (not just setup files)
    test_files = list(tests_dir.rglob("*.test.tsx")) + list(tests_dir.rglob("*.test.ts"))
    if not test_files:
        console.print("[yellow]  No test files found in src/__tests__/[/]")
        console.print("[yellow]  Run 'prisme generate' to generate tests[/]")
        return True

    # Detect Node package manager
    node_manager = _detect_node_manager(frontend_path)

    console.print("  Running frontend tests...")

    # Build command - always use --run to avoid watch mode
    cmd = [node_manager, "run", "test", "--", "--run"]
    if coverage:
        cmd.append("--coverage")

    try:
        result = subprocess.run(
            cmd,
            cwd=frontend_path,
        )

        if result.returncode == 0:
            console.print("[green]  ✓ Frontend tests passed[/]")
            return True
        else:
            console.print("[red]  ✗ Frontend tests failed[/]")
            return False

    except FileNotFoundError as e:
        console.print(f"[red]  Error: {e}[/]")
        return False


# =============================================================================
# ADDITIONAL UTILITY COMMANDS
# =============================================================================


@main.command()
@click.argument("spec_path", type=click.Path(exists=True), required=False)
@click.option("--output", "-o", type=click.Path(), help="Output file for GraphQL schema")
def schema(spec_path: str | None, output: str | None) -> None:
    """Generate GraphQL schema SDL from specification."""
    spec_file = Path(spec_path) if spec_path else Path("specs/models.py")

    if not spec_file.exists():
        console.print(f"[red]Specification file not found: {spec_file}[/]")
        sys.exit(1)

    try:
        stack_spec = load_spec_from_file(spec_file)
    except (SpecLoadError, SpecValidationError) as e:
        console.print(f"[red]Error loading specification: {e}[/]")
        sys.exit(1)

    # Generate basic SDL from spec
    sdl_lines = ["# GraphQL Schema generated by Prism", ""]

    for model in stack_spec.models:
        if not model.expose:
            continue

        sdl_lines.append(f"type {model.name}Type {{")
        sdl_lines.append("  id: Int!")

        for field in model.fields:
            gql_type = _get_graphql_sdl_type(field)
            sdl_lines.append(f"  {field.name}: {gql_type}")

        sdl_lines.append("}")
        sdl_lines.append("")

    sdl = "\n".join(sdl_lines)

    if output:
        Path(output).write_text(sdl)
        console.print(f"[green]Schema written to {output}[/]")
    else:
        console.print(sdl)


def _get_graphql_sdl_type(field: Any) -> str:
    """Get GraphQL SDL type for a field."""
    from prisme.spec.fields import FieldType

    type_map = {
        FieldType.STRING: "String",
        FieldType.TEXT: "String",
        FieldType.INTEGER: "Int",
        FieldType.FLOAT: "Float",
        FieldType.DECIMAL: "Float",
        FieldType.BOOLEAN: "Boolean",
        FieldType.DATETIME: "DateTime",
        FieldType.DATE: "Date",
        FieldType.TIME: "Time",
        FieldType.UUID: "ID",
        FieldType.JSON: "JSON",
        FieldType.ENUM: "String",
        FieldType.FOREIGN_KEY: "Int",
    }

    base_type = type_map.get(field.type, "String")
    return f"{base_type}!" if field.required else base_type


# =============================================================================
# REVIEW COMMAND GROUP
# =============================================================================


@main.group()
def review() -> None:
    """Review code overrides and regeneration conflicts.

    When Prism detects that you've modified generated files, it logs these
    overrides instead of overwriting your changes. Use these commands to
    review what was overridden and verify your customizations still work.
    """


@review.command(name="list")
@click.option("--unreviewed", is_flag=True, help="Show only unreviewed overrides")
def review_list(unreviewed: bool) -> None:
    """List all overridden files."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())

    overrides = log.get_unreviewed() if unreviewed else log.get_all()

    if not overrides:
        if unreviewed:
            console.print("[green]✓ No unreviewed overrides[/]")
        else:
            console.print("[green]✓ No overrides recorded[/]")
        return

    console.print()
    console.print(f"[bold]{'Unreviewed ' if unreviewed else ''}Overrides:[/]")
    console.print()

    for override in sorted(overrides, key=lambda o: o.timestamp, reverse=True):
        icon = "✓" if override.reviewed else "⚠️ "
        status_color = "green" if override.reviewed else "yellow"

        console.print(f"  {icon} [{status_color}]{override.path}[/]")

        if override.diff_summary:
            added = override.diff_summary.get("lines_added", 0)
            removed = override.diff_summary.get("lines_removed", 0)
            changed = override.diff_summary.get("lines_changed", 0)
            console.print(f"     [dim]+{added}, -{removed}, ~{changed} lines[/]")

        console.print(f"     [dim]{override.strategy} • {override.timestamp}[/]")
        console.print()

    if unreviewed:
        console.print("[yellow]Run 'prisme review diff <file>' to see changes[/]")
        console.print("[yellow]Run 'prisme test' to verify your code works[/]")


@review.command()
def summary() -> None:
    """Show a summary of override status."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())

    all_overrides = log.get_all()
    unreviewed = log.get_unreviewed()
    reviewed = [o for o in all_overrides if o.reviewed]

    console.print()
    console.print(
        Panel(
            f"""[bold]Override Log Summary[/]

Total Overrides: {len(all_overrides)}
Unreviewed: [yellow]{len(unreviewed)}[/]
Reviewed: [green]{len(reviewed)}[/]

[dim]Last Updated: {log.last_updated}[/]""",
            title="📋 Code Overrides",
            border_style="blue",
        )
    )

    if unreviewed:
        console.print()
        console.print("[yellow]⚠️  You have unreviewed overrides:[/]")
        for override in unreviewed[:5]:  # Show first 5
            console.print(f"   • {override.path}")

        if len(unreviewed) > 5:
            console.print(f"   [dim]... and {len(unreviewed) - 5} more[/]")

        console.print()
        console.print("[yellow]Run 'prisme review list --unreviewed' to see all[/]")
        console.print("[yellow]Run 'prisme review diff <file>' to see changes[/]")


@review.command()
@click.argument("file_path")
def diff(file_path: str) -> None:
    """Show diff for a specific overridden file."""
    from prisme.tracking.differ import DiffGenerator
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())
    override = log.get(file_path)

    if not override:
        console.print(f"[red]No override found for: {file_path}[/]")
        console.print("[dim]Run 'prisme review list' to see all overrides[/]")
        sys.exit(1)

    console.print()
    console.print(
        Panel(
            f"""[bold]{override.path}[/]

Strategy: {override.strategy}
Status: {"[green]Reviewed[/]" if override.reviewed else "[yellow]Not Reviewed[/]"}
Last Modified: {override.timestamp}

[dim]Your custom code was preserved - generated code was not applied[/]""",
            title=f"{'✓' if override.reviewed else '🔒'} Custom Code Preserved",
            border_style="green" if override.reviewed else "blue",
        )
    )

    # Load cached diff
    diff_content = OverrideLogger._load_diff_cache(Path.cwd(), file_path)

    if diff_content:
        console.print()
        console.print("[bold]Diff:[/]")
        console.print()

        # Show colored diff
        colored_diff = DiffGenerator.format_diff_colored(diff_content)
        console.print(colored_diff)
    else:
        console.print()
        console.print("[yellow]Diff not available (run 'prisme generate' to regenerate)[/]")

    console.print()
    if not override.reviewed:
        console.print("[dim]Actions:[/]")
        console.print("  • Review the changes above")
        console.print("  • Run [bold]prisme test[/] to verify functionality")
        console.print(f"  • Run [bold]prisme review mark-reviewed {file_path}[/] when done")


@review.command()
@click.argument("file_path")
def show(file_path: str) -> None:
    """Show full override details for a file."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())
    override = log.get(file_path)

    if not override:
        console.print(f"[red]No override found for: {file_path}[/]")
        sys.exit(1)

    # Create detailed table
    table = Table(title=f"Override Details: {override.path}")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("File Path", override.path)
    table.add_row("Strategy", override.strategy)
    table.add_row("Status", "[green]Reviewed" if override.reviewed else "[yellow]Not Reviewed")
    table.add_row("Timestamp", override.timestamp)
    table.add_row("Generated Hash", override.generated_hash[:16] + "...")
    table.add_row("User Hash", override.user_hash[:16] + "...")

    if override.diff_summary:
        table.add_row("Lines Added", f"[green]+{override.diff_summary.get('lines_added', 0)}[/]")
        table.add_row("Lines Removed", f"[red]-{override.diff_summary.get('lines_removed', 0)}[/]")
        table.add_row(
            "Lines Changed", f"[yellow]~{override.diff_summary.get('lines_changed', 0)}[/]"
        )

    console.print()
    console.print(table)
    console.print()

    if not override.reviewed:
        console.print(f"[dim]Run 'prisme review diff {file_path}' to see the changes[/]")


@review.command(name="mark-reviewed")
@click.argument("file_path")
def mark_reviewed(file_path: str) -> None:
    """Mark an override as reviewed."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())
    override = log.get(file_path)

    if not override:
        console.print(f"[red]No override found for: {file_path}[/]")
        sys.exit(1)

    if override.reviewed:
        console.print(f"[dim]{file_path} is already marked as reviewed[/]")
        return

    log.mark_reviewed(file_path)
    OverrideLogger.save(log, Path.cwd())

    console.print(f"[green]✓ Marked {file_path} as reviewed[/]")

    # Show remaining unreviewed
    unreviewed = log.get_unreviewed()
    if unreviewed:
        console.print()
        console.print(f"[dim]Remaining unreviewed: {len(unreviewed)}[/]")
    else:
        console.print()
        console.print("[green]✓ All overrides reviewed![/]")


@review.command(name="mark-all-reviewed")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def mark_all_reviewed(yes: bool) -> None:
    """Mark all overrides as reviewed."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())
    unreviewed = log.get_unreviewed()

    if not unreviewed:
        console.print("[green]✓ No unreviewed overrides[/]")
        return

    if not yes:
        console.print(f"[yellow]This will mark {len(unreviewed)} overrides as reviewed.[/]")
        console.print()
        for override in unreviewed[:5]:
            console.print(f"  • {override.path}")
        if len(unreviewed) > 5:
            console.print(f"  [dim]... and {len(unreviewed) - 5} more[/]")
        console.print()

        if not click.confirm("Mark all as reviewed?"):
            console.print("[dim]Cancelled[/]")
            return

    for override in unreviewed:
        log.mark_reviewed(override.path)

    OverrideLogger.save(log, Path.cwd())

    console.print(f"[green]✓ Marked {len(unreviewed)} overrides as reviewed[/]")


@review.command()
@click.option("--all", "clear_all", is_flag=True, help="Clear entire log (including unreviewed)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def clear(clear_all: bool, yes: bool) -> None:
    """Clear reviewed overrides from the log."""
    from prisme.tracking.logger import OverrideLogger

    log = OverrideLogger.load(Path.cwd())

    if clear_all:
        all_overrides = log.get_all()
        if not all_overrides:
            console.print("[dim]Override log is already empty[/]")
            return

        if not yes:
            console.print(
                f"[red]⚠️  This will DELETE all {len(all_overrides)} overrides from the log![/]"
            )
            console.print("[red]This action cannot be undone.[/]")
            console.print()

            if not click.confirm("Clear entire log?"):
                console.print("[dim]Cancelled[/]")
                return

        # Clear all
        log.overrides.clear()
        OverrideLogger.save(log, Path.cwd())

        console.print(f"[green]✓ Cleared {len(all_overrides)} overrides[/]")
    else:
        reviewed = [o for o in log.get_all() if o.reviewed]

        if not reviewed:
            console.print("[dim]No reviewed overrides to clear[/]")
            return

        if not yes:
            console.print(
                f"[yellow]This will remove {len(reviewed)} reviewed overrides from the log.[/]"
            )
            console.print()

            if not click.confirm("Clear reviewed overrides?"):
                console.print("[dim]Cancelled[/]")
                return

        log.clear_reviewed()
        OverrideLogger.save(log, Path.cwd())

        console.print(f"[green]✓ Cleared {len(reviewed)} reviewed overrides[/]")


@review.command()
@click.argument("file_path")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def restore(file_path: str, yes: bool) -> None:
    """Restore generated code, discarding your override.

    This replaces your customized code with the originally generated code,
    effectively rejecting your override.
    """
    from prisme.tracking.logger import OverrideLogger

    project_dir = Path.cwd()
    log = OverrideLogger.load(project_dir)
    override = log.get(file_path)

    if not override:
        console.print(f"[red]No override found for: {file_path}[/]")
        console.print("[dim]Run 'prisme review list' to see all overrides[/]")
        sys.exit(1)

    # Load the generated content
    generated_content = OverrideLogger.load_generated_content(project_dir, file_path)

    if not generated_content:
        console.print(f"[red]Generated content not cached for: {file_path}[/]")
        console.print("[dim]Run 'prisme generate' first to cache the generated content[/]")
        sys.exit(1)

    # Show what we're about to do
    console.print()
    console.print(
        Panel(
            f"""[bold]Restore Generated Code[/]

File: {file_path}

[yellow]⚠️  This will REPLACE your customized code with the generated code.[/]
[dim]Your current code will be lost unless you have it backed up.[/]""",
            title="⚠️  Restore Override",
            border_style="yellow",
        )
    )

    if not yes:
        console.print()
        if not click.confirm("Restore generated code?"):
            console.print("[dim]Cancelled[/]")
            return

    # Write the generated content to the file
    target_path = project_dir / file_path
    target_path.write_text(generated_content)

    # Remove the override from the log
    log.remove(file_path)
    OverrideLogger.save(log, project_dir)

    console.print()
    console.print(f"[green]✓ Restored generated code to {file_path}[/]")
    console.print("[dim]Override has been removed from the log[/]")


# =============================================================================
# DOCKER COMMANDS
# =============================================================================


@main.group(name="docker")
def docker_group() -> None:
    """Docker development environment commands."""
    pass


@docker_group.command(name="init")
@click.option("--redis", is_flag=True, help="Include Redis service")
@click.option("--mcp", is_flag=True, help="Include MCP server service")
def docker_init(redis: bool, mcp: bool) -> None:
    """Generate Docker configuration files for development.

    .. deprecated::
        Use ``ProjectSpec.docker`` in ``specs/project.py`` and run ``prisme generate``.
    """
    console.print(
        "[yellow]⚠ Deprecated: 'prisme docker init' will be removed in the next minor version.[/]"
    )
    console.print(
        "[yellow]  Set Docker config in specs/project.py (ProjectSpec.docker) "
        "and run 'prisme generate' instead.[/]"
    )
    console.print()
    from prisme.docker import ComposeConfig, ComposeGenerator

    # Load spec to get project configuration
    spec_file = _resolve_spec_file()

    if not spec_file.exists():
        console.print("[red]No spec file found. Run this command in a Prism project.[/red]")
        sys.exit(1)

    try:
        spec = load_spec_from_file(spec_file)
    except Exception as e:
        console.print(f"[red]Failed to load spec: {e}[/red]")
        sys.exit(1)

    # Get paths from spec
    backend_path, _, package_name = _get_project_paths()

    # Determine backend and frontend paths
    gen_config = _load_generator_config()
    backend_output = Path(gen_config.backend_output)
    frontend_output = Path(gen_config.frontend_output)

    # For backend, get the parent directory that contains the source
    # e.g., "packages/backend/src" -> backend_path_relative = "packages/backend"
    backend_path_relative = str(backend_path) if backend_path else str(backend_output.parent)

    # For frontend, similar logic
    frontend_path_relative = str(
        frontend_output.parent
        if (Path.cwd() / frontend_output.parent / "package.json").exists()
        else frontend_output
    )

    # Determine backend module name
    backend_module = package_name or backend_output.name

    # Get MCP path from spec
    mcp_path = gen_config.mcp_path

    config = ComposeConfig(
        project_name=spec.name.replace("-", "_"),
        backend_path=backend_path_relative,
        frontend_path=frontend_path_relative,
        backend_module=backend_module,
        use_redis=redis,
        use_mcp=mcp,
        mcp_path=mcp_path,
    )

    generator = ComposeGenerator(Path.cwd())

    console.print("[blue]Generating Docker configuration files...[/blue]")
    generator.generate(config)

    console.print("[green]✓ Docker configuration generated successfully[/green]")
    console.print("\nGenerated files:")
    console.print("  • docker-compose.dev.yml")
    console.print("  • Dockerfile.backend")
    console.print("  • Dockerfile.frontend")
    console.print("  • .dockerignore")
    services = "backend, frontend, db"
    if redis:
        services += ", redis"
    if mcp:
        services += ", mcp"
    console.print(f"\n[dim]Services: {services}[/dim]")
    console.print("[dim]Run 'prisme dev --docker' to start the development environment[/dim]")


# =============================================================================
# DEV SUBCOMMANDS (dev:*)
# =============================================================================


@docker_group.command(name="logs")
@click.argument("service", required=False)
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def docker_logs(service: str | None, follow: bool) -> None:
    """View logs for Docker services.

    SERVICE is the service name (backend, frontend, db, redis).
    If not specified, shows logs for all services.
    """
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        console.print("Run 'prisme docker init' to create Docker configuration files.")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.logs(service=service, follow=follow)


@docker_group.command(name="shell")
@click.argument("service", type=click.Choice(["backend", "frontend", "db", "redis"]))
def docker_shell(service: str) -> None:
    """Open shell in service container.

    SERVICE is the service name (backend, frontend, db, redis).
    """
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        console.print("Run 'prisme docker init' to create Docker configuration files.")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.shell(service)


@docker_group.command(name="down")
def docker_down() -> None:
    """Stop all Docker services."""
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.stop()


@docker_group.command(name="reset-db")
@click.confirmation_option(prompt="This will delete all database data. Continue?")
def docker_reset_db() -> None:
    """Reset database (delete and recreate)."""
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.reset_database()


@docker_group.command(name="backup-db")
@click.argument("output", type=click.Path())
def docker_backup_db(output: str) -> None:
    """Backup database to SQL file.

    OUTPUT is the path to save the backup file.
    """
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.backup_database(Path(output))


@docker_group.command(name="restore-db")
@click.argument("input", type=click.Path(exists=True))
def docker_restore_db(input: str) -> None:
    """Restore database from SQL file.

    INPUT is the path to the backup file.
    """
    from prisme.docker import ComposeManager

    compose_file = Path("docker-compose.dev.yml")
    if not compose_file.exists():
        console.print("[red]docker-compose.dev.yml not found[/red]")
        return

    compose = ComposeManager(Path.cwd(), console=console)
    compose.restore_database(Path(input))


@docker_group.command(name="init-prod")
@click.option("--domain", help="Production domain name")
@click.option("--replicas", default=2, help="Number of backend replicas")
def docker_init_prod(domain: str | None, replicas: int) -> None:
    """Generate production Docker configuration.

    .. deprecated::
        Use ``ProjectSpec.docker.production`` in ``specs/project.py`` and run ``prisme generate``.
    """
    console.print(
        "[yellow]⚠ Deprecated: 'prisme docker init-prod' will be removed in the next minor version.[/]"
    )
    console.print(
        "[yellow]  Set production Docker config in specs/project.py "
        "(ProjectSpec.docker.production) and run 'prisme generate' instead.[/]"
    )
    console.print()
    from prisme.docker import ProductionComposeGenerator, ProductionConfig

    project_dir = Path.cwd()

    # Check if project has been initialized
    prism_dir = project_dir / ".prisme"
    if not prism_dir.exists():
        console.print("[red]Not a Prism project[/red]")
        console.print("Run 'prisme generate' first")
        return

    # Determine project name and redis usage
    project_name = project_dir.name
    use_redis = False

    # Check if docker-compose.dev.yml exists to detect redis
    dev_compose = project_dir / "docker-compose.dev.yml"
    if dev_compose.exists():
        use_redis = "redis" in dev_compose.read_text()

    config = ProductionConfig(
        project_name=project_name,
        use_redis=use_redis,
        domain=domain or "",
        backend_replicas=replicas,
    )

    generator = ProductionComposeGenerator(project_dir)
    generator.generate(config)


@docker_group.command(name="build-prod")
@click.option("--push", is_flag=True, help="Push images to registry")
@click.option("--registry", help="Docker registry URL")
def docker_build_prod(push: bool, registry: str | None) -> None:
    """Build production Docker images."""
    import subprocess

    project_dir = Path.cwd()
    project_name = project_dir.name

    # Check if production Dockerfiles exist
    if not (project_dir / "Dockerfile.backend.prod").exists():
        console.print("[red]Production Dockerfiles not found[/red]")
        console.print("Run 'prisme docker init-prod' first")
        return

    console.print("[blue]Building production images...[/blue]")

    # Build backend
    backend_tag = (
        f"{registry}/{project_name}-backend:latest"
        if registry
        else f"{project_name}-backend:latest"
    )
    try:
        subprocess.run(
            ["docker", "build", "-f", "Dockerfile.backend.prod", "-t", backend_tag, "."],
            cwd=project_dir,
            check=True,
        )
        console.print(f"[green]✓ Backend image built: {backend_tag}[/green]")
    except subprocess.CalledProcessError:
        console.print("[red]Failed to build backend image[/red]")
        return

    # Build frontend
    frontend_tag = (
        f"{registry}/{project_name}-frontend:latest"
        if registry
        else f"{project_name}-frontend:latest"
    )
    try:
        subprocess.run(
            ["docker", "build", "-f", "Dockerfile.frontend.prod", "-t", frontend_tag, "."],
            cwd=project_dir,
            check=True,
        )
        console.print(f"[green]✓ Frontend image built: {frontend_tag}[/green]")
    except subprocess.CalledProcessError:
        console.print("[red]Failed to build frontend image[/red]")
        return

    console.print("[green]✓ All images built successfully[/green]")

    if push and registry:
        console.print(f"[blue]Pushing images to {registry}...[/blue]")
        try:
            subprocess.run(["docker", "push", backend_tag], check=True)
            console.print(f"[green]✓ Pushed {backend_tag}[/green]")
            subprocess.run(["docker", "push", frontend_tag], check=True)
            console.print(f"[green]✓ Pushed {frontend_tag}[/green]")
        except subprocess.CalledProcessError:
            console.print("[red]Failed to push images[/red]")
            return


# =============================================================================
# PROJECTS COMMANDS
# =============================================================================


@main.group(name="projects")
def projects_group() -> None:
    """Manage multiple Prism projects."""
    pass


@projects_group.command(name="list")
def projects_list() -> None:
    """List all running Prism projects."""
    from prisme.docker import ProxyManager

    proxy = ProxyManager()

    # Check if proxy is running
    if not proxy.is_running():
        console.print("[yellow]Reverse proxy is not running[/yellow]")
        console.print("[dim]Start a project with 'prisme dev --docker' to launch the proxy[/dim]")
        return

    projects = proxy.list_projects()

    if not projects:
        console.print("[yellow]No running projects[/yellow]")
        return

    table = Table(title="Running Prism Projects")
    table.add_column("Project", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Services", style="blue")

    for project in projects:
        table.add_row(
            project.name,
            f"http://{project.name}.localhost",
            ", ".join(project.services),
        )

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Traefik Dashboard: http://traefik.localhost:8080[/dim]")


@projects_group.command(name="down-all")
@click.confirmation_option(prompt="Stop all running Prism projects?")
@click.option("--volumes", "-v", is_flag=True, help="Also remove volumes")
@click.option("--quiet", "-q", is_flag=True, help="Suppress detailed output")
def projects_down_all(volumes: bool, quiet: bool) -> None:
    """Stop all Prism projects.

    Stops all running Prism projects by:
    1. Using docker compose down for each project (cleanest method)
    2. Falling back to docker stop/rm for individual containers
    3. Finding and stopping orphaned containers not on proxy network
    """
    from prisme.docker import ProxyManager

    proxy = ProxyManager()

    # Even if proxy isn't running, there might be orphaned containers
    proxy.stop_all_projects(remove_volumes=volumes, verbose=not quiet)


# ============================================================================
# PROXY Commands
# ============================================================================


@main.group(name="proxy")
def proxy_group() -> None:
    """Proxy management and diagnostics."""
    pass


@proxy_group.command(name="status")
def proxy_status() -> None:
    """Show proxy status and configured routes."""
    from prisme.docker import ProxyManager

    proxy = ProxyManager()

    # Check if proxy is running
    if not proxy.is_running():
        console.print("[yellow]Reverse proxy is not running[/yellow]")
        console.print(
            "[dim]Start a project with 'prisme devcontainer up' to launch the proxy[/dim]"
        )
        return

    console.print("[green]✓ Proxy is running[/green]")
    console.print(
        "  Dashboard: [link=http://traefik.localhost:8080]http://traefik.localhost:8080[/link]"
    )
    console.print()

    # Get routes
    routes = proxy.get_routes()
    if routes:
        routes_table = Table(title="Configured Routes")
        routes_table.add_column("Router", style="cyan")
        routes_table.add_column("Rule", style="green")
        routes_table.add_column("Service", style="blue")
        routes_table.add_column("Status", style="yellow")

        for route in routes:
            # Skip internal routers
            if route.name.endswith("@internal"):
                continue
            routes_table.add_row(
                route.name,
                route.rule,
                route.service,
                route.status,
            )

        console.print(routes_table)
        console.print()

    # Get services
    services = proxy.get_services_status()
    if services:
        services_table = Table(title="Services")
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Status", style="yellow")
        services_table.add_column("Servers", style="blue")

        for svc in services:
            # Skip internal services
            if svc.name.endswith("@internal"):
                continue
            status_color = "green" if svc.status == "enabled" else "red"
            services_table.add_row(
                svc.name,
                f"[{status_color}]{svc.status}[/{status_color}]",
                ", ".join(svc.servers) if svc.servers else "[dim]none[/dim]",
            )

        console.print(services_table)


@proxy_group.command(name="diagnose")
@click.argument("url")
def proxy_diagnose(url: str) -> None:
    """Diagnose connectivity issues for a URL.

    URL can be a full URL (http://myproject.localhost/api) or just a hostname
    (myproject.localhost).
    """
    from urllib.parse import urlparse

    from prisme.docker import ProxyManager

    # Parse the URL to extract hostname
    if not url.startswith("http"):
        url = f"http://{url}"
    parsed = urlparse(url)
    hostname = parsed.netloc or parsed.path

    console.print(f"[blue]Diagnosing: {hostname}[/blue]")
    console.print()

    proxy = ProxyManager()
    result = proxy.diagnose(hostname)

    # Display results
    if result.route_exists:
        console.print(f"[green]✓ Route found:[/green] {result.route_name}")
        console.print(f"  Service: {result.service_name}")
    else:
        console.print(f"[red]✗ No route found for {hostname}[/red]")

    if result.route_exists and result.service_healthy:
        console.print("[green]✓ Service is healthy[/green]")
    elif result.route_exists and not result.service_healthy:
        console.print("[red]✗ Service is not healthy[/red]")

    # Display suggestions
    if result.suggested_actions:
        console.print()
        console.print("[yellow]Suggested actions:[/yellow]")
        for action in result.suggested_actions:
            console.print(f"  • {action}")


@proxy_group.command(name="restart")
def proxy_restart() -> None:
    """Restart the proxy container."""
    from prisme.docker import ProxyManager

    proxy = ProxyManager()
    console.print("[yellow]Restarting proxy...[/yellow]")
    proxy.stop()
    proxy.start()


# ============================================================================
# CI/CD Commands
# ============================================================================


@main.group(name="ci")
def ci_group() -> None:
    """CI/CD management commands."""
    pass


@ci_group.command(name="init")
@click.option("--no-codecov", is_flag=True, help="Skip Codecov integration")
@click.option("--no-dependabot", is_flag=True, help="Skip Dependabot config")
@click.option("--no-release", is_flag=True, help="Skip semantic-release setup")
@click.option("--no-commitlint", is_flag=True, help="Skip commitlint config")
@click.option("--frontend", is_flag=True, help="Include frontend workflows")
@click.option("--redis", is_flag=True, help="Include Redis in CI")
def ci_init(
    no_codecov: bool,
    no_dependabot: bool,
    no_release: bool,
    no_commitlint: bool,
    frontend: bool,
    redis: bool,
) -> None:
    """Generate CI/CD workflows for existing project.

    .. deprecated::
        Use ``ProjectSpec.ci`` in ``specs/project.py`` and run ``prisme generate``.
    """
    console.print(
        "[yellow]⚠ Deprecated: 'prisme ci init' will be removed in the next minor version.[/]"
    )
    console.print(
        "[yellow]  Set CI config in specs/project.py (ProjectSpec.ci) "
        "and run 'prisme generate' instead.[/]"
    )
    console.print()
    from prisme.ci import CIConfig, GitHubCIGenerator

    project_dir = Path.cwd()

    # Check if project is initialized
    prism_dir = project_dir / ".prisme"
    if not prism_dir.exists():
        console.print("[red]Not a Prism project[/red]")
        console.print("Run 'prisme generate' first")
        return

    # Try to detect project configuration from spec (optional)
    spec = None
    spec_file = _resolve_spec_file()

    if spec_file.exists():
        try:
            spec = load_spec_from_file(spec_file)
        except Exception as e:
            console.print(f"[yellow]Note: Could not load spec ({e})[/yellow]")
            console.print("[yellow]Using CLI flags and defaults instead[/yellow]")
            console.print()

    # Determine project configuration (CLI flags override spec-detected values)
    project_name = project_dir.name
    if spec and hasattr(spec, "project"):
        project_name = spec.project.name

    # Frontend: CLI flag overrides, otherwise detect from spec
    include_frontend = frontend
    if not include_frontend and spec:
        gen_config = _load_generator_config()
        include_frontend = gen_config.frontend_output != ""

    # Redis: CLI flag overrides, otherwise detect from spec
    use_redis = redis
    if not use_redis and spec and hasattr(spec, "models"):
        for model in spec.models:
            if hasattr(model, "background_jobs") and model.background_jobs:
                use_redis = True
                break

    config = CIConfig(
        project_name=project_name,
        include_frontend=include_frontend,
        use_redis=use_redis,
        enable_codecov=not no_codecov,
        enable_dependabot=not no_dependabot,
        enable_semantic_release=not no_release,
        enable_commitlint=not no_commitlint,
    )

    generator = GitHubCIGenerator(project_dir)
    generator.generate(config)

    console.print()
    console.print("[green]✓ CI/CD workflows generated successfully[/green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review the generated workflows:")
    console.print("     [cyan]git diff .github/[/cyan]")
    console.print("  2. Commit the workflows:")
    console.print(
        "     [cyan]git add .github/ .releaserc.json commitlint.config.js CHANGELOG.md[/cyan]"
    )
    console.print("     [cyan]git commit -m 'ci: add GitHub Actions workflows'[/cyan]")
    console.print("  3. Push to GitHub:")
    console.print("     [cyan]git push[/cyan]")
    if config.enable_codecov:
        console.print("  4. [Optional] Add CODECOV_TOKEN secret to repository settings")


@ci_group.command(name="status")
def ci_status() -> None:
    """Check CI/CD setup status."""
    project_dir = Path.cwd()

    checks = {
        "CI workflow": (project_dir / ".github" / "workflows" / "ci.yml").exists(),
        "Release workflow": (project_dir / ".github" / "workflows" / "release.yml").exists(),
        "Semantic-release config": (project_dir / ".releaserc.json").exists(),
        "Commitlint config": (project_dir / "commitlint.config.js").exists(),
        "Dependabot config": (project_dir / ".github" / "dependabot.yml").exists(),
        "CHANGELOG": (project_dir / "CHANGELOG.md").exists(),
    }

    table = Table(title="CI/CD Setup Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")

    for component, exists in checks.items():
        status = "[green]✓ Configured[/green]" if exists else "[red]✗ Missing[/red]"
        table.add_row(component, status)

    console.print()
    console.print(table)
    console.print()

    if not all(checks.values()):
        console.print("[yellow]Run 'prisme ci init' to generate missing files[/yellow]")
    else:
        console.print("[green]✓ All CI/CD components configured[/green]")


@ci_group.command(name="validate")
def ci_validate() -> None:
    """Validate GitHub Actions workflows locally."""
    project_dir = Path.cwd()
    workflows_dir = project_dir / ".github" / "workflows"

    if not workflows_dir.exists():
        console.print("[red]No workflows found. Run 'prisme ci init' first.[/red]")
        return

    # Check if 'act' is installed
    try:
        subprocess.run(["act", "--version"], capture_output=True, check=True, timeout=5)
    except FileNotFoundError:
        console.print(
            "[yellow]'act' not found. Install from: https://github.com/nektos/act[/yellow]"
        )
        console.print()
        console.print("Installation:")
        console.print("  macOS:   [cyan]brew install act[/cyan]")
        console.print(
            "  Linux:   [cyan]curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash[/cyan]"
        )
        console.print("  Windows: [cyan]choco install act-cli[/cyan] or download from GitHub")
        return
    except subprocess.CalledProcessError:
        console.print("[red]'act' command failed[/red]")
        return

    # Run act in list mode to validate workflows
    console.print("[blue]Validating workflows with act...[/blue]")
    console.print()

    try:
        result = subprocess.run(
            ["act", "--list"], cwd=project_dir, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            console.print("[green]✓ Workflows are valid[/green]")
            console.print()
            console.print(result.stdout)
        else:
            console.print("[red]✗ Workflow validation failed[/red]")
            console.print()
            console.print(result.stderr)
    except subprocess.TimeoutExpired:
        console.print("[red]✗ Validation timed out[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error validating workflows: {e}[/red]")


@ci_group.command(name="add-docker")
def ci_add_docker() -> None:
    """Add Docker build and test workflows to CI/CD."""
    from prisme.ci import DockerCIGenerator

    project_dir = Path.cwd()

    # Check if Docker files exist
    if not (project_dir / "docker-compose.dev.yml").exists():
        console.print("[red]Docker not initialized. Run 'prisme docker init' first.[/red]")
        return

    # Check if production Docker files exist
    if not (project_dir / "Dockerfile.backend.prod").exists():
        console.print("[yellow]Production Docker files not found.[/yellow]")
        console.print("Run 'prisme docker init-prod --domain yourdomain.com' first")
        return

    # Generate Docker CI workflows
    docker_ci = DockerCIGenerator(project_dir)
    docker_ci.generate_docker_build_workflow()
    docker_ci.extend_ci_with_docker_tests()

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review the workflows:")
    console.print("     [cyan]git diff .github/workflows/[/cyan]")
    console.print("  2. Commit the workflows:")
    console.print("     [cyan]git add .github/workflows/[/cyan]")
    console.print("     [cyan]git commit -m 'ci: add Docker build workflows'[/cyan]")
    console.print("  3. Push to GitHub:")
    console.print("     [cyan]git push[/cyan]")
    console.print()
    console.print("[dim]Docker images will be available at:[/dim]")
    console.print("  [dim]ghcr.io/<your-org>/<your-repo>-backend[/dim]")
    console.print("  [dim]ghcr.io/<your-org>/<your-repo>-frontend[/dim]")


# =============================================================================
# DEPLOY COMMANDS
# =============================================================================


@main.group(name="deploy")
def deploy_group() -> None:
    """Deployment infrastructure commands.

    Generate and manage infrastructure-as-code for cloud deployment.
    """
    pass


@deploy_group.command(name="init")
@click.option(
    "--provider",
    type=click.Choice(["hetzner"]),
    default="hetzner",
    help="Cloud provider",
)
@click.option("--domain", help="Base domain for deployment (e.g., example.com)")
@click.option(
    "--location",
    type=click.Choice(["nbg1", "fsn1", "hel1", "ash", "hil"]),
    default="fsn1",
    help="Datacenter location",
)
@click.option(
    "--staging-type",
    type=click.Choice(["cx22", "cx23", "cx32", "cax11"]),
    default="cx23",
    help="Staging server type",
)
@click.option(
    "--production-type",
    type=click.Choice(["cx22", "cx23", "cx32", "cx42", "cx52"]),
    default="cx23",
    help="Production server type",
)
@click.option("--ssl-email", help="Email for Let's Encrypt certificates")
@click.option("--no-floating-ip", is_flag=True, help="Disable floating IP for production")
@click.option("--redis", is_flag=True, help="Include Redis in deployment")
def deploy_init(
    provider: str,
    domain: str | None,
    location: str,
    staging_type: str,
    production_type: str,
    ssl_email: str | None,
    no_floating_ip: bool,
    redis: bool,
) -> None:
    """Initialize deployment configuration for Hetzner Cloud.

    .. deprecated::
        Use ``ProjectSpec.deploy`` in ``specs/project.py`` and run ``prisme generate``.

    Generates Terraform templates, cloud-init configuration, and
    deployment workflows.
    """
    console.print(
        "[yellow]⚠ Deprecated: 'prisme deploy init' will be removed in the next minor version.[/]"
    )
    console.print(
        "[yellow]  Set deploy config in specs/project.py (ProjectSpec.deploy) "
        "and run 'prisme generate' instead.[/]"
    )
    console.print()
    from prisme.deploy import DeploymentConfig, HetznerConfig, HetznerDeployGenerator
    from prisme.deploy.config import HetznerLocation, HetznerServerType

    project_dir = Path.cwd()

    # Check if project is initialized
    prism_dir = project_dir / ".prisme"
    if not prism_dir.exists():
        console.print("[red]Not a Prism project[/red]")
        console.print("Run 'prisme generate' first")
        return

    # Determine project name
    project_name = project_dir.name

    # Map location string to enum
    location_map = {
        "nbg1": HetznerLocation.NUREMBERG,
        "fsn1": HetznerLocation.FALKENSTEIN,
        "hel1": HetznerLocation.HELSINKI,
        "ash": HetznerLocation.ASHBURN,
        "hil": HetznerLocation.HILLSBORO,
    }

    # Map server types to enums
    staging_type_map = {
        "cx22": HetznerServerType.CX22,
        "cx23": HetznerServerType.CX23,
        "cx32": HetznerServerType.CX32,
        "cax11": HetznerServerType.CAX11,
    }
    production_type_map = {
        "cx22": HetznerServerType.CX22,
        "cx23": HetznerServerType.CX23,
        "cx32": HetznerServerType.CX32,
        "cx42": HetznerServerType.CX42,
        "cx52": HetznerServerType.CX52,
    }

    hetzner_config = HetznerConfig(
        location=location_map[location],
        staging_server_type=staging_type_map[staging_type],
        production_server_type=production_type_map[production_type],
        production_floating_ip=not no_floating_ip,
    )

    config = DeploymentConfig(
        project_name=project_name,
        domain=domain or "",
        ssl_email=ssl_email or "",
        use_redis=redis,
        hetzner=hetzner_config,
    )

    generator = HetznerDeployGenerator(project_dir, config)
    generator.generate()


@deploy_group.command(name="plan")
@click.option(
    "--env",
    "-e",
    type=click.Choice(["staging", "production", "all"]),
    default="all",
    help="Environment to plan",
)
def deploy_plan(env: str) -> None:
    """Run terraform plan to preview infrastructure changes.

    Shows what resources will be created, modified, or destroyed.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        console.print("Run 'prisme deploy init --provider hetzner' first")
        return

    # Determine which tfvars to use
    tfvars_files = ["staging.tfvars", "production.tfvars"] if env == "all" else [f"{env}.tfvars"]

    for tfvars in tfvars_files:
        tfvars_path = terraform_dir / tfvars
        if not tfvars_path.exists():
            console.print(f"[yellow]Skipping {tfvars} (not found)[/yellow]")
            continue

        console.print(f"\n[blue]Planning with {tfvars}...[/blue]\n")

        try:
            subprocess.run(
                ["terraform", "plan", f"-var-file={tfvars}"],
                cwd=terraform_dir,
                check=True,
            )
        except FileNotFoundError:
            console.print("[red]Terraform not found. Install from https://terraform.io[/red]")
            return
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Terraform plan failed: {e}[/red]")
            return


@deploy_group.command(name="apply")
@click.option(
    "--env",
    "-e",
    type=click.Choice(["staging", "production"]),
    required=True,
    help="Environment to deploy",
)
@click.option("--auto-approve", is_flag=True, help="Skip confirmation")
def deploy_apply(env: str, auto_approve: bool) -> None:
    """Apply Terraform configuration to provision infrastructure.

    Creates or updates VMs, networks, volumes, and firewall rules.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        console.print("Run 'prisme deploy init --provider hetzner' first")
        return

    tfvars = f"{env}.tfvars"
    tfvars_path = terraform_dir / tfvars

    if not tfvars_path.exists():
        console.print(f"[red]{tfvars} not found[/red]")
        return

    console.print(f"\n[blue]Applying {env} configuration...[/blue]\n")

    cmd = ["terraform", "apply", f"-var-file={tfvars}"]
    if auto_approve:
        cmd.append("-auto-approve")

    try:
        subprocess.run(cmd, cwd=terraform_dir, check=True)
        console.print(f"\n[green]✓ {env.title()} infrastructure deployed[/green]")
    except FileNotFoundError:
        console.print("[red]Terraform not found. Install from https://terraform.io[/red]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Terraform apply failed: {e}[/red]")


@deploy_group.command(name="destroy")
@click.option(
    "--env",
    "-e",
    type=click.Choice(["staging", "production"]),
    required=True,
    help="Environment to destroy",
)
@click.confirmation_option(prompt="This will destroy all infrastructure. Continue?")
def deploy_destroy(env: str) -> None:
    """Destroy infrastructure for an environment.

    WARNING: This will delete all VMs, volumes, and data.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        return

    tfvars = f"{env}.tfvars"

    console.print(f"\n[red]Destroying {env} infrastructure...[/red]\n")

    try:
        subprocess.run(
            ["terraform", "destroy", f"-var-file={tfvars}"],
            cwd=terraform_dir,
            check=True,
        )
        console.print(f"\n[yellow]✓ {env.title()} infrastructure destroyed[/yellow]")
    except FileNotFoundError:
        console.print("[red]Terraform not found. Install from https://terraform.io[/red]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Terraform destroy failed: {e}[/red]")


@deploy_group.command(name="ssh")
@click.argument("environment", type=click.Choice(["staging", "production"]))
def deploy_ssh(environment: str) -> None:
    """SSH into a deployment server.

    Opens an interactive SSH session to the specified environment.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        return

    # Get server IP from Terraform output
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", f"{environment}_server_ip"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        server_ip = result.stdout.strip()

        if not server_ip or server_ip == "null":
            console.print(f"[red]{environment.title()} server not deployed[/red]")
            console.print(f"Run 'prisme deploy apply -e {environment}' first")
            return

        console.print(f"[blue]Connecting to {environment} ({server_ip})...[/blue]")

        # Start SSH session
        subprocess.run(["ssh", f"deploy@{server_ip}"])

    except FileNotFoundError:
        console.print("[red]Terraform not found. Install from https://terraform.io[/red]")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to get {environment} server IP[/red]")
        console.print("Make sure the infrastructure is deployed")


@deploy_group.command(name="logs")
@click.argument("environment", type=click.Choice(["staging", "production"]))
@click.option("--service", "-s", help="Service name (backend, frontend, db)")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", "-n", default=100, help="Number of lines to show")
def deploy_logs(environment: str, service: str | None, follow: bool, tail: int) -> None:
    """View logs from deployment server.

    Shows Docker container logs from the specified environment.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"
    project_name = project_dir.name

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        return

    # Get server IP from Terraform output
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", f"{environment}_server_ip"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        server_ip = result.stdout.strip()

        if not server_ip or server_ip == "null":
            console.print(f"[red]{environment.title()} server not deployed[/red]")
            return

        # Build docker compose logs command
        docker_cmd = f"cd /opt/{project_name} && docker compose -f docker-compose.prod.yml logs"
        if follow:
            docker_cmd += " -f"
        docker_cmd += f" --tail={tail}"
        if service:
            docker_cmd += f" {service}"

        console.print(f"[blue]Fetching logs from {environment}...[/blue]\n")

        subprocess.run(["ssh", f"deploy@{server_ip}", docker_cmd])

    except FileNotFoundError:
        console.print("[red]Terraform not found[/red]")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to get {environment} server IP[/red]")


@deploy_group.command(name="status")
def deploy_status() -> None:
    """Show deployment status and configuration."""
    project_dir = Path.cwd()
    deploy_dir = project_dir / "deploy"
    terraform_dir = deploy_dir / "terraform"

    if not deploy_dir.exists():
        console.print("[yellow]Deployment not initialized[/yellow]")
        console.print("Run 'prisme deploy init --provider hetzner' to get started")
        return

    table = Table(title="Deployment Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")

    # Check what's configured
    checks = {
        "Terraform config": (terraform_dir / "main.tf").exists(),
        "Staging tfvars": (terraform_dir / "staging.tfvars").exists(),
        "Production tfvars": (terraform_dir / "production.tfvars").exists(),
        "Cloud-init": (terraform_dir / "cloud-init" / "user-data.yml").exists(),
        "Deploy workflow": (project_dir / ".github" / "workflows" / "deploy.yml").exists(),
        "Deploy script": (deploy_dir / "scripts" / "deploy.sh").exists(),
    }

    for component, exists in checks.items():
        status = "[green]✓ Ready[/green]" if exists else "[red]✗ Missing[/red]"
        table.add_row(component, status)

    console.print()
    console.print(table)

    # Try to get Terraform state
    if (terraform_dir / "terraform.tfstate").exists():
        console.print("\n[bold]Infrastructure State:[/bold]")
        try:
            for env in ["staging", "production"]:
                result = subprocess.run(
                    ["terraform", "output", "-raw", f"{env}_server_ip"],
                    cwd=terraform_dir,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip() not in ["", "null"]:
                    console.print(f"  {env.title()}: [green]{result.stdout.strip()}[/green]")
                else:
                    console.print(f"  {env.title()}: [dim]Not deployed[/dim]")
        except FileNotFoundError:
            console.print("  [yellow]Terraform not found[/yellow]")
    else:
        console.print("\n[dim]Infrastructure not yet provisioned[/dim]")
        console.print("[dim]Run 'prisme deploy apply -e staging' to provision[/dim]")


@deploy_group.command(name="ssl")
@click.argument("environment", type=click.Choice(["staging", "production"]))
@click.option("--domain", required=True, help="Domain for certificate")
def deploy_ssl(environment: str, domain: str) -> None:
    """Setup Let's Encrypt SSL certificate.

    Runs certbot on the server to obtain and configure SSL.
    """
    project_dir = Path.cwd()
    terraform_dir = project_dir / "deploy" / "terraform"

    if not terraform_dir.exists():
        console.print("[red]Deployment not initialized[/red]")
        return

    # Get server IP from Terraform output
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", f"{environment}_server_ip"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        server_ip = result.stdout.strip()

        if not server_ip or server_ip == "null":
            console.print(f"[red]{environment.title()} server not deployed[/red]")
            return

        console.print(f"[blue]Setting up SSL for {domain} on {environment}...[/blue]")

        # Run certbot on server
        certbot_cmd = f"sudo certbot --nginx -d {domain} --non-interactive --agree-tos"

        subprocess.run(["ssh", f"deploy@{server_ip}", certbot_cmd])

        console.print(f"\n[green]✓ SSL certificate configured for {domain}[/green]")

    except FileNotFoundError:
        console.print("[red]SSH not found[/red]")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to get {environment} server IP[/red]")


# =============================================================================
# AUTH COMMANDS (prisme.dev integration)
# =============================================================================


@main.group(name="auth")
def auth_group() -> None:
    """Authentication commands for prisme.dev.

    Manage API keys and authentication for prisme.dev services.
    """
    pass


def _get_config_path() -> Path:
    """Get the path to the prisme config directory."""
    config_dir = Path.home() / ".config" / "prisme"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_credentials_path() -> Path:
    """Get the path to the credentials file."""
    return _get_config_path() / "credentials.json"


def _load_credentials() -> dict:
    """Load credentials from config file."""
    creds_path = _get_credentials_path()
    if creds_path.exists():
        import json

        return json.loads(creds_path.read_text())
    return {}


def _save_credentials(credentials: dict) -> None:
    """Save credentials to config file."""
    import json

    creds_path = _get_credentials_path()
    creds_path.write_text(json.dumps(credentials, indent=2))
    # Set restrictive permissions
    creds_path.chmod(0o600)


@auth_group.command(name="login")
@click.option("--api-key", prompt="API Key", hide_input=True, help="prisme.dev API key")
@click.option(
    "--api-url",
    default="https://api.prisme.dev",
    help="prisme.dev API URL",
)
def auth_login(api_key: str, api_url: str) -> None:
    """Login to prisme.dev with an API key.

    Stores the API key securely in ~/.config/prisme/credentials.json
    """
    import httpx

    # Validate the API key by making a test request
    console.print("[blue]Validating API key...[/blue]")

    try:
        response = httpx.get(
            f"{api_url}/subdomains",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
            params={"limit": 1},
        )
        if response.status_code == 401:
            console.print("[red]Invalid API key[/red]")
            return
        if response.status_code != 200:
            console.print(
                f"[yellow]Warning: Could not validate API key (status {response.status_code})[/yellow]"
            )
    except httpx.RequestError as e:
        console.print(f"[yellow]Warning: Could not connect to {api_url}: {e}[/yellow]")
        console.print("[yellow]Saving credentials anyway...[/yellow]")

    # Save credentials
    credentials = _load_credentials()
    credentials["prisme"] = {
        "api_key": api_key,
        "api_url": api_url,
    }
    _save_credentials(credentials)

    console.print("[green]✓ Logged in to prisme.dev[/green]")
    console.print(f"  Credentials saved to: {_get_credentials_path()}")


@auth_group.command(name="logout")
def auth_logout() -> None:
    """Logout from prisme.dev.

    Removes stored API key from the credentials file.
    """
    credentials = _load_credentials()
    if "prisme" in credentials:
        del credentials["prisme"]
        _save_credentials(credentials)
        console.print("[green]✓ Logged out from prisme.dev[/green]")
    else:
        console.print("[yellow]Not logged in[/yellow]")


@auth_group.command(name="status")
def auth_status() -> None:
    """Show current authentication status."""
    credentials = _load_credentials()

    if "prisme" not in credentials:
        console.print("[yellow]Not logged in to prisme.dev[/yellow]")
        console.print("Run 'prisme auth login' to authenticate")
        return

    api_url = credentials["prisme"].get("api_url", "https://api.prisme.dev")
    api_key = credentials["prisme"].get("api_key", "")

    # Mask the API key
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"

    console.print("[green]✓ Logged in to prisme.dev[/green]")
    console.print(f"  API URL: {api_url}")
    console.print(f"  API Key: {masked_key}")


# =============================================================================
# SUBDOMAIN COMMANDS (prisme.dev integration)
# =============================================================================


@main.group(name="subdomain")
def subdomain_group() -> None:
    """Manage prisme.dev subdomains.

    Claim, release, and manage *.prisme.dev subdomains for your projects.
    """
    pass


def _get_prisme_client():
    """Get an authenticated httpx client for prisme.dev API."""
    import httpx

    credentials = _load_credentials()
    if "prisme" not in credentials:
        console.print("[red]Not logged in to prisme.dev[/red]")
        console.print("Run 'prisme auth login' first")
        sys.exit(1)

    api_url = credentials["prisme"].get("api_url", "https://api.prisme.dev")
    api_key = credentials["prisme"].get("api_key")

    return httpx.Client(
        base_url=api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )


@subdomain_group.command(name="list")
def subdomain_list() -> None:
    """List your claimed subdomains."""
    client = _get_prisme_client()

    try:
        response = client.get("/subdomains")
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            console.print("[yellow]No subdomains found[/yellow]")
            return

        table = Table(title="Your Subdomains")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("IP Address")
        table.add_column("Created")

        for item in data["items"]:
            status_color = {
                "active": "green",
                "reserved": "yellow",
                "suspended": "red",
            }.get(item["status"], "white")

            table.add_row(
                f"{item['name']}.prisme.dev",
                f"[{status_color}]{item['status']}[/{status_color}]",
                item.get("ip_address") or "-",
                item.get("created_at", "-")[:10] if item.get("created_at") else "-",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list subdomains: {e}[/red]")
    finally:
        client.close()


@subdomain_group.command(name="claim")
@click.argument("name")
def subdomain_claim(name: str) -> None:
    """Claim a subdomain name.

    NAME is the subdomain to claim (e.g., 'myapp' for myapp.prisme.dev)
    """
    client = _get_prisme_client()

    try:
        response = client.post("/subdomains/claim", json={"name": name})

        if response.status_code == 409:
            console.print(f"[red]Subdomain '{name}' is already claimed[/red]")
            return
        if response.status_code == 400:
            error = response.json().get("detail", "Invalid subdomain name")
            console.print(f"[red]{error}[/red]")
            return

        response.raise_for_status()
        data = response.json()

        console.print(f"[green]✓ Subdomain claimed: {data['name']}.prisme.dev[/green]")
        console.print(f"  Status: {data['status']}")
        console.print()
        console.print("Next steps:")
        console.print("  1. Deploy your server")
        console.print(f"  2. Run: prisme subdomain activate {name} --ip <server-ip>")

    except Exception as e:
        console.print(f"[red]Failed to claim subdomain: {e}[/red]")
    finally:
        client.close()


@subdomain_group.command(name="activate")
@click.argument("name")
@click.option("--ip", required=True, help="IP address to point the subdomain to")
def subdomain_activate(name: str, ip: str) -> None:
    """Activate a subdomain with an IP address.

    NAME is the subdomain name (e.g., 'myapp')
    """
    client = _get_prisme_client()

    try:
        response = client.post(
            f"/subdomains/{name}/activate",
            json={"ip_address": ip},
        )

        if response.status_code == 404:
            console.print(f"[red]Subdomain '{name}' not found[/red]")
            console.print("Run 'prisme subdomain claim' first")
            return

        response.raise_for_status()
        data = response.json()

        console.print(f"[green]✓ Subdomain activated: {data['name']}.prisme.dev[/green]")
        console.print(f"  IP Address: {data['ip_address']}")
        console.print(f"  Status: {data['status']}")
        console.print()
        console.print("DNS propagation may take a few minutes.")
        console.print(f"Check status with: prisme subdomain status {name}")

    except Exception as e:
        console.print(f"[red]Failed to activate subdomain: {e}[/red]")
    finally:
        client.close()


@subdomain_group.command(name="status")
@click.argument("name")
def subdomain_status(name: str) -> None:
    """Check DNS propagation status for a subdomain.

    NAME is the subdomain name (e.g., 'myapp')
    """
    client = _get_prisme_client()

    try:
        response = client.get(f"/subdomains/{name}/status")

        if response.status_code == 404:
            console.print(f"[red]Subdomain '{name}' not found[/red]")
            return

        response.raise_for_status()
        data = response.json()

        console.print(f"[bold]Subdomain: {data['subdomain']}.prisme.dev[/bold]")
        console.print(f"  Status: {data['status']}")
        console.print(f"  IP Address: {data.get('ip_address') or 'Not set'}")

        if data.get("propagation"):
            console.print()
            console.print("DNS Propagation:")
            for resolver, propagated in data["propagation"].items():
                status = "[green]✓[/green]" if propagated else "[red]✗[/red]"
                console.print(f"  {resolver}: {status}")

    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")
    finally:
        client.close()


@subdomain_group.command(name="release")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to release this subdomain?")
def subdomain_release(name: str) -> None:
    """Release a subdomain.

    NAME is the subdomain name (e.g., 'myapp')

    This will delete the DNS record and release the subdomain name.
    """
    client = _get_prisme_client()

    try:
        response = client.post(f"/subdomains/{name}/release")

        if response.status_code == 404:
            console.print(f"[red]Subdomain '{name}' not found[/red]")
            return

        # 204 No Content is success
        if response.status_code in (200, 204):
            console.print(f"[green]✓ Subdomain released: {name}.prisme.dev[/green]")
        else:
            response.raise_for_status()

    except Exception as e:
        console.print(f"[red]Failed to release subdomain: {e}[/red]")
    finally:
        client.close()


# =============================================================================
# DEVCONTAINER COMMANDS
# =============================================================================


@main.group(name="devcontainer")
def devcontainer_group() -> None:
    """Workspace-isolated dev container commands.

    Manage dev containers that are isolated per workspace (project + branch).
    Each workspace gets its own containers, database, and Traefik URL.
    """
    pass


@devcontainer_group.command(name="up")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("--build", is_flag=True, help="Rebuild containers")
@click.option("--redis", is_flag=True, help="Include Redis service")
def devcontainer_up(name: str | None, build: bool, redis: bool) -> None:
    """Start the dev container workspace.

    Starts the dev container stack for the current project and branch.
    If .devcontainer doesn't exist, it will be generated first.

    The workspace is named {project}-{branch} by default.

    Examples:
        prisme devcontainer up
        prisme devcontainer up --build
        prisme devcontainer up --name custom-workspace
        prisme devcontainer up --redis
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
        include_redis=redis,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)

    try:
        manager.up(config, build=build)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")


@devcontainer_group.command(name="down")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("--volumes", "-v", is_flag=True, help="Remove volumes (database, etc.)")
def devcontainer_down(name: str | None, volumes: bool) -> None:
    """Stop the dev container workspace.

    Stops the dev container stack for the current workspace.

    Examples:
        prisme devcontainer down
        prisme devcontainer down --volumes
        prisme devcontainer down --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    manager.down(config, volumes=volumes)


@devcontainer_group.command(name="shell")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("--root", is_flag=True, help="Open shell as root user")
def devcontainer_shell(name: str | None, root: bool) -> None:
    """Open a shell in the dev container.

    Opens an interactive bash shell in the app container.

    Examples:
        prisme devcontainer shell
        prisme devcontainer shell --root
        prisme devcontainer shell --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    manager.shell(config, root=root)


@devcontainer_group.command(name="logs")
@click.argument("service", required=False)
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
def devcontainer_logs(service: str | None, name: str | None, follow: bool) -> None:
    """View dev container logs.

    Shows logs from the dev container services.

    Examples:
        prisme devcontainer logs
        prisme devcontainer logs app
        prisme devcontainer logs db -f
        prisme devcontainer logs --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    manager.logs(config, service=service, follow=follow)


@devcontainer_group.command(name="status")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
def devcontainer_status(name: str | None) -> None:
    """Show dev container status.

    Shows the status of all services in the workspace.

    Examples:
        prisme devcontainer status
        prisme devcontainer status --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    manager.status(config)


@devcontainer_group.command(name="list")
def devcontainer_list() -> None:
    """List all dev container workspaces.

    Shows all Prism dev container workspaces with their status.

    Examples:
        prisme devcontainer list
    """
    from prisme.devcontainer import WorkspaceManager

    manager = WorkspaceManager(console=console)
    manager.print_list()


@devcontainer_group.command(name="exec")
@click.argument("command", nargs=-1, required=True)
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("--root", is_flag=True, help="Run as root user")
def devcontainer_exec(command: tuple[str, ...], name: str | None, root: bool) -> None:
    """Execute a command in the dev container.

    Runs a command inside the dev container workspace.

    Examples:
        prisme devcontainer exec "echo hello"
        prisme devcontainer exec "uv sync"
        prisme devcontainer exec "uv run python -c 'print(1)'"
        prisme devcontainer exec --root "apt update"
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    cmd_str = " ".join(command)
    exit_code = manager.exec(config, cmd_str, root=root)
    raise SystemExit(exit_code)


@devcontainer_group.command(name="test")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.argument("args", nargs=-1)
def devcontainer_test(name: str | None, args: tuple[str, ...]) -> None:
    """Run tests in the dev container.

    Runs 'prisme test' inside the dev container workspace.

    Examples:
        prisme devcontainer test
        prisme devcontainer test -k "auth"
        prisme devcontainer test --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    cmd = "prisme test"
    if args:
        cmd += " " + " ".join(args)
    exit_code = manager.exec(config, cmd)
    raise SystemExit(exit_code)


@devcontainer_group.command(name="migrate")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
def devcontainer_migrate(name: str | None) -> None:
    """Run database migrations in the dev container.

    Runs 'prisme db migrate' inside the dev container workspace.

    Examples:
        prisme devcontainer migrate
        prisme devcontainer migrate --name custom-workspace
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig, WorkspaceManager

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    manager = WorkspaceManager(project_dir=config.project_dir, console=console)
    exit_code = manager.exec(config, "prisme db migrate")
    raise SystemExit(exit_code)


@devcontainer_group.command(name="url")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
def devcontainer_url(name: str | None) -> None:
    """Print the workspace URL for browser/curl access.

    Outputs just the URL, useful for scripting.

    Examples:
        prisme devcontainer url
        curl $(prisme devcontainer url)/api/health
    """
    from pathlib import Path

    from prisme.devcontainer import WorkspaceConfig

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
    )
    click.echo(f"http://{config.hostname}.localhost")


@devcontainer_group.command(name="generate")
@click.option("--name", "-n", help="Workspace name (defaults to project-branch)")
@click.option("--redis", is_flag=True, help="Include Redis service")
@click.option("--force", is_flag=True, help="Overwrite existing .devcontainer")
def devcontainer_generate(name: str | None, redis: bool, force: bool) -> None:
    """Generate .devcontainer configuration.

    Creates .devcontainer/ directory with all necessary files:
    - devcontainer.json (VS Code compatible)
    - docker-compose.yml (full stack)
    - Dockerfile.dev (development image)
    - setup.sh (post-create script)

    Examples:
        prisme devcontainer generate
        prisme devcontainer generate --redis
        prisme devcontainer generate --force
    """
    from pathlib import Path

    from prisme.devcontainer import DevContainerGenerator, WorkspaceConfig

    config = WorkspaceConfig.from_directory(
        project_dir=Path.cwd(),
        workspace_name=name,
        include_redis=redis,
    )

    if config.devcontainer_dir.exists() and not force:
        console.print("[yellow].devcontainer already exists[/yellow]")
        console.print("Use --force to overwrite")
        return

    generator = DevContainerGenerator(console=console)
    generator.generate(config)


# =============================================================================
# ADMIN COMMAND GROUP
# =============================================================================


@main.group()
def admin() -> None:
    """Admin panel management commands."""


@admin.command("bootstrap")
@click.option("--email", required=True, help="Email address for the admin user")
@click.option("--spec", "spec_path", default=None, help="Path to spec file")
def admin_bootstrap(email: str, spec_path: str | None) -> None:
    """Generate a one-time bootstrap token for the first admin account.

    Creates an admin user (if not existing) and prints a one-time URL
    that can be used to set the password.
    """
    from prisme.spec.project import ProjectSpec

    # Try to load project spec for auth config
    toml_path = Path("prisme.toml")
    project_spec: ProjectSpec | None = None
    if toml_path.exists():
        try:
            from prisme.config.loader import load_prisme_config
            from prisme.utils.spec_loader import load_project_spec

            prisme_cfg = load_prisme_config(toml_path)
            project_path = Path(prisme_cfg.project.project_path)
            if project_path.exists():
                project_spec = load_project_spec(project_path)
        except Exception:
            pass

    if project_spec is None:
        project_spec = ProjectSpec(name="unknown")

    if not project_spec.auth.enabled or not project_spec.auth.admin_panel.enabled:
        console.print("[red]Admin panel is not enabled in the spec.[/]")
        console.print("Set auth.admin_panel.enabled = True in your spec.")
        sys.exit(1)

    # Generate token
    import hashlib
    import secrets
    from datetime import UTC, datetime

    plain_token = secrets.token_urlsafe(48)
    hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()

    console.print()
    console.print(f"[bold green]Bootstrap token generated for:[/] {email}")
    console.print()
    console.print("[bold]One-time bootstrap URL:[/]")
    console.print(f"  [cyan]http://localhost:5173/bootstrap?token={plain_token}[/]")
    console.print()
    console.print("[bold]Hashed token (store in DB):[/]")
    console.print(f"  {hashed_token}")
    console.print()
    console.print("[dim]The token expires in 24 hours.[/]")
    console.print("[dim]Create the user in the database with:[/]")
    console.print(
        f'  [dim]roles=["admin"], is_active=False, bootstrap_token="{hashed_token}", '
        f'bootstrap_token_created_at="{datetime.now(UTC).isoformat()}"[/]'
    )
    console.print()


if __name__ == "__main__":
    main()

"""Base template classes for project scaffolding.

Provides the foundation for creating project templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from prisme.utils.template_engine import TemplateRenderer


@dataclass
class TemplateFile:
    """A file to be created in the project."""

    path: str  # Relative path in the project
    content: str  # File content (can be a template)
    is_template: bool = True  # Whether to process as Jinja2 template
    executable: bool = False  # Whether file should be executable


@dataclass
class ProjectTemplate:
    """Template for creating a new project."""

    name: str
    description: str
    files: list[TemplateFile] = field(default_factory=list)

    def render(self, context: dict[str, Any]) -> list[tuple[Path, str]]:
        """Render all template files with the given context.

        Args:
            context: Template variables.

        Returns:
            List of (path, content) tuples.
        """
        renderer = TemplateRenderer()
        results = []

        for template_file in self.files:
            # Render the path (for folder/file names with template variables)
            rendered_path = renderer.render_string(template_file.path, context)

            if template_file.is_template:
                content = renderer.render_string(template_file.content, context)
            else:
                content = template_file.content

            results.append((Path(rendered_path), content))

        return results

    def add_file(
        self,
        path: str,
        content: str,
        is_template: bool = True,
        executable: bool = False,
    ) -> None:
        """Add a file to the template.

        Args:
            path: Relative file path.
            content: File content.
            is_template: Whether to process as Jinja2 template.
            executable: Whether file should be executable.
        """
        self.files.append(
            TemplateFile(
                path=path,
                content=content,
                is_template=is_template,
                executable=executable,
            )
        )


class TemplateRegistry:
    """Registry for project templates."""

    def __init__(self) -> None:
        self._templates: dict[str, ProjectTemplate] = {}
        self._register_builtin_templates()

    def _register_builtin_templates(self) -> None:
        """Register built-in templates."""
        self.register(self._create_minimal_template())
        self.register(self._create_full_template())
        self.register(self._create_api_only_template())

    def register(self, template: ProjectTemplate) -> None:
        """Register a template."""
        self._templates[template.name] = template

    def get(self, name: str) -> ProjectTemplate | None:
        """Get a template by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """List available template names."""
        return list(self._templates.keys())

    def _load_template(self, template_name: str) -> str:
        """Load a template file from the package templates directory.

        Args:
            template_name: Name of the template file (e.g., 'README.minimal.md.jinja2')

        Returns:
            Template content as a string
        """
        template_path = (
            Path(__file__).parent.parent / "templates" / "jinja2" / "project" / template_name
        )
        return template_path.read_text()

    def _add_extension_stubs(self, template: ProjectTemplate) -> None:
        """Add app/backend/extensions/ stub files to a template."""
        ext = "app/backend/extensions"
        template.add_file(
            f"{ext}/__init__.py",
            self._load_template("app/backend/extensions/__init__.py.jinja2"),
        )
        template.add_file(
            f"{ext}/dependencies.py",
            self._load_template("app/backend/extensions/dependencies.py.jinja2"),
        )
        template.add_file(
            f"{ext}/routers.py",
            self._load_template("app/backend/extensions/routers.py.jinja2"),
        )
        template.add_file(
            f"{ext}/events.py",
            self._load_template("app/backend/extensions/events.py.jinja2"),
        )
        template.add_file(
            f"{ext}/policies.py",
            self._load_template("app/backend/extensions/policies.py.jinja2"),
        )

    def _create_minimal_template(self) -> ProjectTemplate:
        """Create the minimal project template."""
        template = ProjectTemplate(
            name="minimal",
            description="Minimal project with SQLite and REST API only",
        )

        # Root files
        template.add_file("README.md", self._load_template("README.minimal.md.jinja2"))
        template.add_file(".gitignore", self._load_template(".gitignore.jinja2"))
        template.add_file(".env.example", self._load_template(".env.example.minimal.jinja2"))

        # Python project
        template.add_file("pyproject.toml", self._load_template("pyproject.minimal.toml.jinja2"))

        # Prisme config + specs
        template.add_file("prisme.toml", self._load_template("prisme.toml.jinja2"))
        template.add_file("specs/models.py", self._load_template("specs/models.py.jinja2"))
        template.add_file("specs/project.py", self._load_template("specs/project_spec.py.jinja2"))

        # Main application
        template.add_file(
            "src/{{ project_name_snake }}/main.py", self._load_template("main_minimal.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/__init__.py", self._load_template("__init__.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/config.py", self._load_template("config.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/database.py", self._load_template("database.py.jinja2")
        )

        # App extension stubs
        self._add_extension_stubs(template)

        # Tests
        template.add_file("tests/__init__.py", self._load_template("tests/__init__.py.jinja2"))
        template.add_file("tests/conftest.py", self._load_template("tests/conftest.py.jinja2"))
        template.add_file(
            "tests/test_health.py", self._load_template("tests/test_health.py.jinja2")
        )

        return template

    def _create_full_template(self) -> ProjectTemplate:
        """Create the full project template."""
        template = ProjectTemplate(
            name="full",
            description="Full stack with PostgreSQL, REST + GraphQL + MCP, and React frontend",
        )

        # Root files
        template.add_file("README.md", self._load_template("README.full.md.jinja2"))
        template.add_file(".gitignore", self._load_template(".gitignore.jinja2"))
        template.add_file(".env.example", self._load_template(".env.example.full.jinja2"))

        # Monorepo structure
        template.add_file("pnpm-workspace.yaml", self._load_template("pnpm-workspace.yaml.jinja2"))

        # Backend
        template.add_file(
            "packages/backend/pyproject.toml", self._load_template("pyproject.full.toml.jinja2")
        )
        template.add_file(
            "packages/backend/src/{{ project_name_snake }}/__init__.py",
            self._load_template("__init__.py.jinja2"),
        )
        template.add_file(
            "packages/backend/src/{{ project_name_snake }}/main.py",
            self._load_template("main_full.py.jinja2"),
        )
        template.add_file(
            "packages/backend/src/{{ project_name_snake }}/config.py",
            self._load_template("config.py.jinja2"),
        )
        template.add_file(
            "packages/backend/src/{{ project_name_snake }}/database.py",
            self._load_template("database_async.py.jinja2"),
        )

        # App extension stubs
        self._add_extension_stubs(template)

        # Backend tests
        template.add_file(
            "packages/backend/tests/__init__.py", self._load_template("tests/__init__.py.jinja2")
        )
        template.add_file(
            "packages/backend/tests/conftest.py", self._load_template("tests/conftest.py.jinja2")
        )
        template.add_file(
            "packages/backend/tests/test_health.py",
            self._load_template("tests/test_health.py.jinja2"),
        )

        # Frontend files are now scaffolded using create-vite and configured
        # by _configure_frontend_for_prism() in cli.py
        # This includes: package.json, vite.config.ts, tsconfig.json,
        # tailwind.config.js, postcss.config.js, index.html, src/main.tsx, src/App.tsx

        # Spec file
        template.add_file("specs/models.py", self._load_template("specs/models.py.jinja2"))

        # Docker
        template.add_file(
            "docker/docker-compose.yml", self._load_template("docker-compose.yml.jinja2")
        )
        template.add_file(
            "docker/Dockerfile.backend", self._load_template("Dockerfile.backend.jinja2")
        )

        # Prism config
        template.add_file("prisme.toml", self._load_template("prisme.toml.jinja2"))
        template.add_file("specs/project.py", self._load_template("specs/project_spec.py.jinja2"))

        return template

    def _create_api_only_template(self) -> ProjectTemplate:
        """Create the API-only template."""
        template = ProjectTemplate(
            name="api-only",
            description="Full backend with REST + GraphQL + MCP, no frontend",
        )

        # Root files
        template.add_file("README.md", self._load_template("README.api-only.md.jinja2"))
        template.add_file(".gitignore", self._load_template(".gitignore.jinja2"))
        template.add_file(".env.example", self._load_template(".env.example.full.jinja2"))

        # Python project
        template.add_file("pyproject.toml", self._load_template("pyproject.full.toml.jinja2"))

        # Main application
        template.add_file(
            "src/{{ project_name_snake }}/__init__.py", self._load_template("__init__.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/main.py", self._load_template("main_full.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/config.py", self._load_template("config.py.jinja2")
        )
        template.add_file(
            "src/{{ project_name_snake }}/database.py",
            self._load_template("database_async.py.jinja2"),
        )

        # App extension stubs
        self._add_extension_stubs(template)

        # Tests
        template.add_file("tests/__init__.py", self._load_template("tests/__init__.py.jinja2"))
        template.add_file("tests/conftest.py", self._load_template("tests/conftest.py.jinja2"))
        template.add_file(
            "tests/test_health.py", self._load_template("tests/test_health.py.jinja2")
        )

        # Spec file
        template.add_file("specs/models.py", self._load_template("specs/models.py.jinja2"))

        # Docker
        template.add_file(
            "docker/docker-compose.yml", self._load_template("docker-compose.api-only.yml.jinja2")
        )
        template.add_file("docker/Dockerfile", self._load_template("Dockerfile.backend.jinja2"))

        # Prism config
        template.add_file("prisme.toml", self._load_template("prisme.toml.jinja2"))
        template.add_file("specs/project.py", self._load_template("specs/project_spec.py.jinja2"))

        return template


# All template content has been externalized to .jinja2 files
# in src/prism/templates/jinja2/project/
# See TemplateRegistry._load_template() for loading mechanism
# Global template registry
template_registry = TemplateRegistry()


__all__ = [
    "ProjectTemplate",
    "TemplateFile",
    "TemplateRegistry",
    "template_registry",
]

"""API key authentication generator for Prism.

This generator creates simple API key-based authentication infrastructure including:
- API key service (verification against environment variable)
- Authentication middleware (FastAPI dependencies)
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class APIKeyAuthGenerator(GeneratorBase):
    """Generates API key authentication system for backend."""

    REQUIRED_TEMPLATES = [
        "backend/auth/api_key/api_key_service.py.jinja2",
        "backend/auth/api_key/middleware_api_key.py.jinja2",
        "backend/auth/api_key/api_key_init.py.jinja2",
        "backend/auth/api_key/middleware_init.py.jinja2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Skip generation if auth is not enabled or preset is not api_key
        if not self.auth_config.enabled or self.auth_config.preset != "api_key":
            self.skip_generation = True
            return

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

        # Setup paths for generated auth files
        backend_base = Path(self.generator_config.backend_output)
        package_name = self.get_package_name()
        package_base = backend_base / package_name

        self.auth_base = package_base / "auth"
        self.middleware_path = package_base / "middleware"

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all API key authentication-related files.

        Returns:
            List of generated files with content and strategies
        """
        if getattr(self, "skip_generation", False):
            return []

        files = []

        # Core service
        files.append(self._generate_api_key_service())

        # Middleware
        files.append(self._generate_api_key_middleware())

        # Init files
        files.append(self._generate_auth_init())
        files.append(self._generate_middleware_init())

        return files

    def _generate_api_key_service(self) -> GeneratedFile:
        """Generate API key verification service.

        Returns:
            GeneratedFile for api_key_service.py
        """
        config = self.auth_config.api_key

        content = self.renderer.render_file(
            "backend/auth/api_key/api_key_service.py.jinja2",
            context={
                "env_var": config.env_var,
                "allow_multiple_keys": config.allow_multiple_keys,
            },
        )

        return GeneratedFile(
            path=self.auth_base / "api_key_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="API key verification service",
        )

    def _generate_api_key_middleware(self) -> GeneratedFile:
        """Generate FastAPI API key authentication middleware and dependencies.

        Returns:
            GeneratedFile for middleware/api_key.py
        """
        project_name = self.get_package_name()
        config = self.auth_config.api_key

        content = self.renderer.render_file(
            "backend/auth/api_key/middleware_api_key.py.jinja2",
            context={
                "project_name": project_name,
                "header": config.header,
                "scheme": config.scheme,
            },
        )

        return GeneratedFile(
            path=self.middleware_path / "api_key.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="API key authentication middleware",
        )

    def _generate_auth_init(self) -> GeneratedFile:
        """Generate __init__.py for auth module.

        Returns:
            GeneratedFile for auth/__init__.py
        """
        project_name = self.get_package_name()

        content = self.renderer.render_file(
            "backend/auth/api_key/api_key_init.py.jinja2",
            context={
                "project_name": project_name,
            },
        )

        return GeneratedFile(
            path=self.auth_base / "__init__.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth module init (API key)",
        )

    def _generate_middleware_init(self) -> GeneratedFile:
        """Generate __init__.py for middleware module.

        Returns:
            GeneratedFile for middleware/__init__.py
        """
        project_name = self.get_package_name()

        content = self.renderer.render_file(
            "backend/auth/api_key/middleware_init.py.jinja2",
            context={
                "project_name": project_name,
            },
        )

        return GeneratedFile(
            path=self.middleware_path / "__init__.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Middleware module init (API key)",
        )

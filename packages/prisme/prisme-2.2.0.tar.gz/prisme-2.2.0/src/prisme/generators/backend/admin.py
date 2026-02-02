"""Admin panel generator for Prism.

Generates admin API routes, services, schemas, and whitelist model
for managing users and signup access control.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.template_engine import TemplateRenderer


class AdminGenerator(GeneratorBase):
    """Generates admin panel backend infrastructure."""

    REQUIRED_TEMPLATES = [
        "backend/admin/admin_init.py.jinja2",
        "backend/admin/admin_service.py.jinja2",
        "backend/admin/bootstrap_service.py.jinja2",
        "backend/admin/whitelist_model.py.jinja2",
        "backend/admin/schemas_admin.py.jinja2",
        "backend/admin/routes_admin.py.jinja2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Skip if auth or admin panel is not enabled
        if not self.auth_config.enabled or not self.auth_config.admin_panel.enabled:
            self.skip_generation = True
            return

        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

        backend_base = Path(self.generator_config.backend_output)
        package_name = self.get_package_name()
        package_base = backend_base / package_name

        self.admin_base = package_base / "admin"
        self.schemas_path = package_base / "schemas"
        self.routes_base = package_base / "api" / "rest"

    def _get_common_context(self) -> dict:
        """Build template context."""
        config = self.auth_config
        project_name = self.get_package_name()
        user_model = config.user_model
        user_model_snake = to_snake_case(user_model)

        return {
            "project_name": project_name,
            "user_model": user_model,
            "user_model_snake": user_model_snake,
            "username_field": config.username_field,
            "email_verification": config.email_verification,
            "signup_access_mode": config.signup_access.mode,
        }

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all admin-related files."""
        if getattr(self, "skip_generation", False):
            return []

        return [
            self._generate_admin_service(),
            self._generate_bootstrap_service(),
            self._generate_whitelist_model(),
            self._generate_admin_schemas(),
            self._generate_admin_routes(),
            self._generate_admin_init(),
        ]

    def _generate_admin_service(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/admin_service.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.admin_base / "admin_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Admin service",
        )

    def _generate_bootstrap_service(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/bootstrap_service.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.admin_base / "bootstrap_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Bootstrap service",
        )

    def _generate_whitelist_model(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/whitelist_model.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.admin_base / "whitelist_model.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Signup whitelist model",
        )

    def _generate_admin_schemas(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/schemas_admin.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.schemas_path / "admin.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Admin API schemas",
        )

    def _generate_admin_routes(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/routes_admin.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.routes_base / "admin.py",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description="Admin API routes",
        )

    def _generate_admin_init(self) -> GeneratedFile:
        content = self.renderer.render_file(
            "backend/admin/admin_init.py.jinja2",
            context=self._get_common_context(),
        )
        return GeneratedFile(
            path=self.admin_base / "__init__.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Admin module init",
        )

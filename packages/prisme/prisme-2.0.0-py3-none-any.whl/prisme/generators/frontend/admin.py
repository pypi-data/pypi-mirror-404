"""Frontend admin panel generator for Prism.

Generates React admin pages, layout, and API client for the admin panel.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class FrontendAdminGenerator(GeneratorBase):
    """Generates React admin panel components for frontend."""

    REQUIRED_TEMPLATES = [
        "frontend/admin/adminApi.ts.jinja2",
        "frontend/admin/AdminLayout.tsx.jinja2",
        "frontend/admin/AdminDashboard.tsx.jinja2",
        "frontend/admin/AdminUsers.tsx.jinja2",
        "frontend/admin/AdminUserDetail.tsx.jinja2",
        "frontend/admin/AdminWhitelist.tsx.jinja2",
        "frontend/admin/BootstrapPage.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.auth_config.enabled or not self.auth_config.admin_panel.enabled:
            self.skip_generation = True
            return

        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / "pages"
        self.components_path = frontend_base / "components"
        self.lib_path = frontend_base / "lib"

    def _get_common_context(self) -> dict:
        """Build template context."""
        config = self.auth_config
        return {
            "username_field": config.username_field,
            "email_verification": config.email_verification,
            "admin_path": config.admin_panel.path,
        }

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all frontend admin files."""
        if getattr(self, "skip_generation", False):
            return []

        ctx = self._get_common_context()
        return [
            self._generate_file(
                "frontend/admin/adminApi.ts.jinja2",
                self.lib_path / "adminApi.ts",
                FileStrategy.ALWAYS_OVERWRITE,
                "Admin API client",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/AdminLayout.tsx.jinja2",
                self.components_path / "admin" / "AdminLayout.tsx",
                FileStrategy.ALWAYS_OVERWRITE,
                "Admin layout",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/AdminDashboard.tsx.jinja2",
                self.pages_path / "admin" / "AdminDashboard.tsx",
                FileStrategy.GENERATE_ONCE,
                "Admin dashboard page",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/AdminUsers.tsx.jinja2",
                self.pages_path / "admin" / "AdminUsers.tsx",
                FileStrategy.GENERATE_ONCE,
                "Admin users page",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/AdminUserDetail.tsx.jinja2",
                self.pages_path / "admin" / "AdminUserDetail.tsx",
                FileStrategy.GENERATE_ONCE,
                "Admin user detail page",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/AdminWhitelist.tsx.jinja2",
                self.pages_path / "admin" / "AdminWhitelist.tsx",
                FileStrategy.GENERATE_ONCE,
                "Admin whitelist page",
                ctx,
            ),
            self._generate_file(
                "frontend/admin/BootstrapPage.tsx.jinja2",
                self.pages_path / "auth" / "BootstrapPage.tsx",
                FileStrategy.GENERATE_ONCE,
                "Bootstrap page",
                ctx,
            ),
        ]

    def _generate_file(
        self,
        template: str,
        path: Path,
        strategy: FileStrategy,
        description: str,
        context: dict,
    ) -> GeneratedFile:
        content = self.renderer.render_file(template, context=context)
        return GeneratedFile(
            path=path,
            content=content,
            strategy=strategy,
            description=description,
        )

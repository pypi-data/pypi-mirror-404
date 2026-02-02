"""Profile and settings pages generator for Prism.

Generates user profile and settings page components when auth is enabled.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class ProfilePagesGenerator(GeneratorBase):
    """Generator for profile and settings page components."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/profile.tsx.jinja2",
        "frontend/pages/settings.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        if not self.auth_config.enabled:
            self.skip_generation = True
            return

        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / self.generator_config.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate profile and settings pages."""
        if getattr(self, "skip_generation", False):
            return []

        config = self.auth_config
        context = {
            "username_field": config.username_field,
            "mfa_enabled": config.mfa_enabled,
            "password_reset": config.password_reset,
            "email_verification": config.email_verification,
            "oauth_providers": [p.provider for p in config.oauth_providers],
        }

        return [
            GeneratedFile(
                path=self.pages_path / "ProfilePage.tsx",
                content=self.renderer.render_file(
                    "frontend/pages/profile.tsx.jinja2", context=context
                ),
                strategy=FileStrategy.GENERATE_ONCE,
                description="User profile page",
            ),
            GeneratedFile(
                path=self.pages_path / "SettingsPage.tsx",
                content=self.renderer.render_file(
                    "frontend/pages/settings.tsx.jinja2", context=context
                ),
                strategy=FileStrategy.GENERATE_ONCE,
                description="User settings page",
            ),
        ]


__all__ = ["ProfilePagesGenerator"]

"""Dashboard page generator for Prism.

Generates a dashboard page with model counts and quick links.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer


class DashboardGenerator(GeneratorBase):
    """Generator for the dashboard page."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/dashboard.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / self.generator_config.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate the dashboard page."""
        frontend_models = [m for m in self.spec.models if m.expose]
        if not frontend_models:
            return []

        models_info = []
        for model in frontend_models:
            snake_name = to_snake_case(model.name)
            kebab_name = to_kebab_case(snake_name)
            models_info.append(
                {
                    "name": model.name,
                    "plural_name": pluralize(model.name),
                    "plural_kebab": pluralize(kebab_name),
                    "has_list": model.has_operation("list"),
                    "has_create": model.has_operation("create"),
                }
            )

        project_title = self.spec.effective_title
        auth_enabled = self.auth_config.enabled

        content = self.renderer.render_file(
            "frontend/pages/dashboard.tsx.jinja2",
            context={
                "models": models_info,
                "project_title": project_title,
                "auth_enabled": auth_enabled,
            },
        )

        return [
            GeneratedFile(
                path=self.pages_path / "DashboardPage.tsx",
                content=content,
                strategy=FileStrategy.GENERATE_ONCE,
                description="Dashboard page",
            ),
        ]


__all__ = ["DashboardGenerator"]

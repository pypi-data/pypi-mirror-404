"""Global search page generator for Prism.

Generates a search page that queries across all exposed models.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer


class SearchPageGenerator(GeneratorBase):
    """Generator for the global search page."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/search.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / self.generator_config.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate the global search page."""
        frontend_models = [m for m in self.spec.models if m.expose]
        if not frontend_models:
            return []

        searchable_models = []
        for model in frontend_models:
            if model.has_operation("list"):
                snake_name = to_snake_case(model.name)
                kebab_name = to_kebab_case(snake_name)
                searchable_models.append(
                    {
                        "name": model.name,
                        "plural_name": pluralize(model.name),
                        "kebab_name": kebab_name,
                        "plural_kebab": pluralize(kebab_name),
                        "fields": [f.name for f in model.fields if not f.hidden],
                    }
                )

        content = self.renderer.render_file(
            "frontend/pages/search.tsx.jinja2",
            context={
                "models": searchable_models,
            },
        )

        return [
            GeneratedFile(
                path=self.pages_path / "SearchPage.tsx",
                content=content,
                strategy=FileStrategy.GENERATE_ONCE,
                description="Global search page",
            ),
        ]


__all__ = ["SearchPageGenerator"]

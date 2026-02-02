"""Error pages generator for Prism.

Generates 404, 403, and 500 error page components.
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class ErrorPagesGenerator(GeneratorBase):
    """Generator for error page components (404, 403, 500)."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/error_404.tsx.jinja2",
        "frontend/pages/error_403.tsx.jinja2",
        "frontend/pages/error_500.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / self.generator_config.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_files(self) -> list[GeneratedFile]:
        """Generate error page components."""
        project_title = self.spec.effective_title

        files = []
        for template, filename, description in [
            ("frontend/pages/error_404.tsx.jinja2", "NotFoundPage.tsx", "404 Not Found page"),
            ("frontend/pages/error_403.tsx.jinja2", "ForbiddenPage.tsx", "403 Forbidden page"),
            ("frontend/pages/error_500.tsx.jinja2", "ServerErrorPage.tsx", "500 Server Error page"),
        ]:
            content = self.renderer.render_file(
                template,
                context={"project_title": project_title},
            )
            files.append(
                GeneratedFile(
                    path=self.pages_path / filename,
                    content=content,
                    strategy=FileStrategy.GENERATE_ONCE,
                    description=description,
                )
            )

        return files


__all__ = ["ErrorPagesGenerator"]

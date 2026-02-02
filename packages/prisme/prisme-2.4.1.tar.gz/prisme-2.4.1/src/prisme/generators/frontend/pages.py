"""Page components generator for Prism.

Generates page components for list, detail, and create views
for each model.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.model import ModelSpec


class PagesGenerator(ModelGenerator):
    """Generator for page components."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/list_page.tsx.jinja2",
        "frontend/pages/detail_page.tsx.jinja2",
        "frontend/pages/create_page.tsx.jinja2",
        "frontend/pages/edit_page.tsx.jinja2",
        "frontend/pages/import_page.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.pages_path = frontend_base / self.generator_config.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """No shared files for pages."""
        return []

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate pages for a single model."""
        if not model.expose:
            return []

        files = []
        has_form = model.get_frontend_override("generate_form", True)
        has_detail = model.get_frontend_override("generate_detail_view", True)

        if model.has_operation("list"):
            files.append(self._generate_list_page(model))

        # Only generate detail page if both operation is enabled AND detail component exists
        if model.has_operation("read") and has_detail:
            files.append(self._generate_detail_page(model))

        # Only generate create/edit pages if BOTH operation is enabled AND form exists
        if model.has_operation("create") and has_form:
            files.append(self._generate_create_page(model))

        if model.has_operation("update") and has_form:
            files.append(self._generate_edit_page(model))

        # Import page when enabled
        enable_import = model.get_frontend_override("enable_import", False)
        if enable_import and model.has_operation("create"):
            files.append(self._generate_import_page(model))

        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """No index file for pages."""
        return []

    def _generate_list_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate list page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_name = pluralize(model.name)
        plural_kebab = pluralize(kebab_name)

        # Check if create operation and form exist
        has_form = model.get_frontend_override("generate_form", True)
        show_create_button = model.has_operation("create") and has_form

        # Export is always available on list pages
        enable_bulk_actions = model.get_frontend_override("enable_bulk_actions", False)
        filterable_fields = model.get_frontend_override("filterable_fields") or []
        enable_import = model.get_frontend_override("enable_import", False)

        content = self.renderer.render_file(
            "frontend/pages/list_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "plural_name": plural_name,
                "plural_name_lower": plural_name.lower(),
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
                "show_create_button": show_create_button,
                "ops_update": model.has_operation("update"),
                "ops_delete": model.has_operation("delete"),
                "has_mutations": model.has_operation("create")
                or model.has_operation("update")
                or model.has_operation("delete"),
                "enable_export": True,
                "enable_bulk_actions": enable_bulk_actions,
                "filterable_fields": filterable_fields,
                "enable_import": enable_import and model.has_operation("create"),
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "index.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"List page for {plural_name}",
        )

    def _generate_detail_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate detail page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)

        # Collect relationships for tab display
        related_models = []
        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                rel_kebab = to_kebab_case(to_snake_case(rel.target_model))
                related_models.append(
                    {
                        "name": rel.name,
                        "target_model": rel.target_model,
                        "plural_name": pluralize(rel.target_model),
                        "plural_kebab": pluralize(rel_kebab),
                        "type": rel.type,
                    }
                )

        content = self.renderer.render_file(
            "frontend/pages/detail_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
                "ops_update": model.has_operation("update"),
                "ops_delete": model.has_operation("delete"),
                "has_mutations": model.has_operation("create")
                or model.has_operation("update")
                or model.has_operation("delete"),
                "related_models": related_models,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "[id].tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Detail page for {model.name}",
        )

    def _generate_create_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate create page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)

        content = self.renderer.render_file(
            "frontend/pages/create_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "new.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Create page for {model.name}",
        )

    def _generate_edit_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate edit page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)

        content = self.renderer.render_file(
            "frontend/pages/edit_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "[id]/edit.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Edit page for {model.name}",
        )

    def _generate_import_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate import page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_name = pluralize(model.name)
        plural_kebab = pluralize(kebab_name)

        content = self.renderer.render_file(
            "frontend/pages/import_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "plural_name": plural_name,
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "import.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Import page for {plural_name}",
        )


__all__ = ["PagesGenerator"]

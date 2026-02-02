"""React hooks generator for Prism.

Generates custom React hooks for data fetching and mutations
for each model, plus headless UI state hooks (form state, table state).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_camel_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.model import ModelSpec


class HooksGenerator(ModelGenerator):
    """Generator for React hooks."""

    REQUIRED_TEMPLATES = [
        "frontend/hooks/urql_hooks.ts.jinja2",
        "frontend/hooks/apollo_hooks.ts.jinja2",
        "frontend/hooks/rest_hooks.ts.jinja2",
        "frontend/hooks/index.ts.jinja2",
        "frontend/hooks/form_state.ts.jinja2",
        "frontend/hooks/table_state.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.hooks_path = frontend_base / self.generator_config.hooks_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """No shared files for hooks."""
        return []

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate hooks for a single model."""
        if not model.expose:
            return []

        files: list[GeneratedFile] = []
        api_style = self.exposure_config.frontend.api_style if self.exposure_config else "graphql"
        graphql_client = (
            self.exposure_config.frontend.graphql_client if self.exposure_config else "urql"
        )

        # Data hooks (existing)
        if api_style == "graphql":
            if graphql_client == "urql":
                files.append(self._generate_urql_hooks(model))
            else:
                files.append(self._generate_apollo_hooks(model))
        else:
            files.append(self._generate_rest_hooks(model))

        # Headless UI state hooks (new)
        if model.get_frontend_override("generate_form", True):
            files.append(self._generate_form_state_hook(model))

        if model.get_frontend_override("generate_table", True):
            files.append(self._generate_table_state_hook(model))

        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate index file for hooks."""
        return [self._generate_hooks_index()]

    def _generate_urql_hooks(self, model: ModelSpec) -> GeneratedFile:
        """Generate hooks using urql."""
        snake_name = to_snake_case(model.name)
        camel_name = to_camel_case(model.name)
        plural_name = pluralize(model.name)
        plural_camel = to_camel_case(pluralize(snake_name))
        ops_create = model.has_operation("create")
        ops_update = model.has_operation("update")
        ops_delete = model.has_operation("delete")

        # Build loading and error expressions
        loading_parts = []
        if ops_create:
            loading_parts.append("createResult.fetching")
        if ops_update:
            loading_parts.append("updateResult.fetching")
        if ops_delete:
            loading_parts.append("deleteResult.fetching")

        error_parts = []
        if ops_create:
            error_parts.append("createResult.error")
        if ops_update:
            error_parts.append("updateResult.error")
        if ops_delete:
            error_parts.append("deleteResult.error")

        loading_expr = " || ".join(loading_parts) if loading_parts else "false"
        error_expr = (" ?? ".join(error_parts) + " ?? null") if error_parts else "null"

        content = self.renderer.render_file(
            "frontend/hooks/urql_hooks.ts.jinja2",
            context={
                "model_name": model.name,
                "camel_name": camel_name,
                "plural_name": plural_name,
                "plural_camel": plural_camel,
                "ops_create": ops_create,
                "ops_update": ops_update,
                "ops_delete": ops_delete,
                "loading_expr": loading_expr,
                "error_expr": error_expr,
            },
        )

        return GeneratedFile(
            path=self.hooks_path / f"use{model.name}.ts",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Hooks for {model.name}",
        )

    def _generate_apollo_hooks(self, model: ModelSpec) -> GeneratedFile:
        """Generate hooks using Apollo Client."""
        snake_name = to_snake_case(model.name)
        camel_name = to_camel_case(model.name)
        plural_name = pluralize(model.name)
        plural_camel = to_camel_case(pluralize(snake_name))
        ops_create = model.has_operation("create")
        ops_update = model.has_operation("update")
        ops_delete = model.has_operation("delete")

        # Build loading and error expressions
        loading_parts = []
        if ops_create:
            loading_parts.append("createState.loading")
        if ops_update:
            loading_parts.append("updateState.loading")
        if ops_delete:
            loading_parts.append("deleteState.loading")

        error_parts = []
        if ops_create:
            error_parts.append("createState.error")
        if ops_update:
            error_parts.append("updateState.error")
        if ops_delete:
            error_parts.append("deleteState.error")

        loading_expr = " || ".join(loading_parts) if loading_parts else "false"
        error_expr = (" ?? ".join(error_parts) + " ?? null") if error_parts else "null"

        content = self.renderer.render_file(
            "frontend/hooks/apollo_hooks.ts.jinja2",
            context={
                "model_name": model.name,
                "camel_name": camel_name,
                "plural_name": plural_name,
                "plural_camel": plural_camel,
                "ops_create": ops_create,
                "ops_update": ops_update,
                "ops_delete": ops_delete,
                "loading_expr": loading_expr,
                "error_expr": error_expr,
            },
        )

        return GeneratedFile(
            path=self.hooks_path / f"use{model.name}.ts",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Hooks for {model.name}",
        )

    def _generate_rest_hooks(self, model: ModelSpec) -> GeneratedFile:
        """Generate hooks using REST API (fetch/SWR pattern)."""
        snake_name = to_snake_case(model.name)
        plural_name = pluralize(model.name)
        kebab_name = pluralize(snake_name).replace("_", "-")
        content = self.renderer.render_file(
            "frontend/hooks/rest_hooks.ts.jinja2",
            context={
                "model_name": model.name,
                "plural_name": plural_name,
                "kebab_name": kebab_name,
                "ops_create": model.has_operation("create"),
                "ops_update": model.has_operation("update"),
                "ops_delete": model.has_operation("delete"),
            },
        )

        return GeneratedFile(
            path=self.hooks_path / f"use{model.name}.ts",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Hooks for {model.name}",
        )

    def _generate_hooks_index(self) -> GeneratedFile:
        """Generate index file for hooks."""
        model_names = [model.name for model in self.spec.models if model.expose]
        form_state_models = [
            model.name
            for model in self.spec.models
            if model.expose and model.get_frontend_override("generate_form", True)
        ]
        table_state_models = [
            model.name
            for model in self.spec.models
            if model.expose and model.get_frontend_override("generate_table", True)
        ]

        content = self.renderer.render_file(
            "frontend/hooks/index.ts.jinja2",
            context={
                "model_names": model_names,
                "form_state_models": form_state_models,
                "table_state_models": table_state_models,
            },
        )

        return GeneratedFile(
            path=self.hooks_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Hooks index",
        )

    def _generate_form_state_hook(self, model: ModelSpec) -> GeneratedFile:
        """Generate form state hook for a model."""
        camel_name = to_camel_case(model.name)

        # Build form field specifications
        form_fields = self._build_form_fields(model)

        content = self.renderer.render_file(
            "frontend/hooks/form_state.ts.jinja2",
            context={
                "model_name": model.name,
                "camel_name": camel_name,
                "form_fields": form_fields,
            },
        )

        return GeneratedFile(
            path=self.hooks_path / f"use{model.name}FormState.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Form state hook for {model.name}",
        )

    def _generate_table_state_hook(self, model: ModelSpec) -> GeneratedFile:
        """Generate table state hook for a model."""
        # Build sort fields type (union of field names)
        sortable_fields = self._get_sortable_fields(model)
        if sortable_fields:
            sort_fields_type = " | ".join(f"'{f}'" for f in sortable_fields)
        else:
            sort_fields_type = "string"

        # Build default search fields (string fields that are likely searchable)
        search_fields = self._get_search_fields(model)
        default_search_fields = (
            "[" + ", ".join(f"'{f}'" for f in search_fields) + "]" if search_fields else "[]"
        )

        # Get operations for mutation awareness
        ops_create = model.has_operation("create")
        ops_update = model.has_operation("update")
        ops_delete = model.has_operation("delete")

        content = self.renderer.render_file(
            "frontend/hooks/table_state.ts.jinja2",
            context={
                "model_name": model.name,
                "sort_fields_type": sort_fields_type,
                "default_search_fields": default_search_fields,
                "ops_delete": ops_delete,
                "has_mutations": ops_create or ops_update or ops_delete,
            },
        )

        return GeneratedFile(
            path=self.hooks_path / f"use{model.name}TableState.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Table state hook for {model.name}",
        )

    def _build_form_fields(self, model: ModelSpec) -> list[dict]:
        """Build form field specifications for template."""
        fields = []

        for field in model.fields:
            if field.hidden:
                continue

            # A field is only required for user input if it's required AND has no default
            user_required = field.required and field.default is None

            fields.append(
                {
                    "name": field.name,
                    "camel_name": to_camel_case(field.name),
                    "type": field.type.value,
                    "required": user_required,
                    "label": field.effective_label,
                    "max_length": getattr(field, "max_length", None),
                    "min_length": getattr(field, "min_length", None),
                    "min": getattr(field, "min", None),
                    "max": getattr(field, "max", None),
                }
            )

        return fields

    def _get_sortable_fields(self, model: ModelSpec) -> list[str]:
        """Get list of sortable field names (camelCase)."""
        sortable_types = {"string", "text", "integer", "float", "decimal", "datetime", "date"}
        fields = []

        for field in model.fields:
            if field.hidden:
                continue
            if field.type.value in sortable_types:
                fields.append(to_camel_case(field.name))

        # Add common fields
        if model.timestamps:
            fields.extend(["createdAt", "updatedAt"])

        return fields

    def _get_search_fields(self, model: ModelSpec) -> list[str]:
        """Get list of searchable field names (camelCase)."""
        searchable_types = {"string", "text"}
        fields = []

        for field in model.fields:
            if field.hidden:
                continue
            if field.type.value in searchable_types:
                fields.append(to_camel_case(field.name))

        return fields[:5]  # Limit to first 5 searchable fields


__all__ = ["HooksGenerator"]

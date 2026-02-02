"""React components generator for Prism.

Generates React form, table, and detail view components
for each model using the widget system.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_camel_case, to_kebab_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.model import ModelSpec


class ComponentsGenerator(ModelGenerator):
    """Generator for React components."""

    REQUIRED_TEMPLATES = [
        "frontend/components/form_base.tsx.jinja2",
        "frontend/components/form_extension.tsx.jinja2",
        "frontend/components/table_base.tsx.jinja2",
        "frontend/components/table_extension.tsx.jinja2",
        "frontend/components/detail_base.tsx.jinja2",
        "frontend/components/detail_extension.tsx.jinja2",
        "frontend/components/generated_index.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.components_path = frontend_base / self.generator_config.components_path
        self.generated_path = frontend_base / self.generator_config.components_generated_path

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared component utilities."""
        return []

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate components for a single model."""
        if not model.expose:
            return []

        files = []

        if model.get_frontend_override("generate_form", True):
            files.append(self._generate_form_base(model))
            files.append(self._generate_form_extension(model))

        if model.get_frontend_override("generate_table", True):
            files.append(self._generate_table_base(model))
            files.append(self._generate_table_extension(model))

        if model.get_frontend_override("generate_detail_view", True):
            files.append(self._generate_detail_base(model))
            files.append(self._generate_detail_extension(model))

        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate index files for components."""
        return [
            self._generate_generated_index(),
        ]

    def _generate_form_base(self, model: ModelSpec) -> GeneratedFile:
        """Generate base form component."""
        kebab_name = to_kebab_case(model.name)

        # Build field specs for the form
        field_specs = self._build_field_specs(model)

        content = self.renderer.render_file(
            "frontend/components/form_base.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_upper": model.name.upper(),
                "kebab_name": kebab_name,
                "field_specs": field_specs,
            },
        )

        return GeneratedFile(
            path=self.generated_path / f"{model.name}FormBase.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Base form for {model.name}",
        )

    def _generate_form_extension(self, model: ModelSpec) -> GeneratedFile:
        """Generate user-extensible form component."""
        kebab_name = to_kebab_case(model.name)

        content = self.renderer.render_file(
            "frontend/components/form_extension.tsx.jinja2",
            context={
                "model_name": model.name,
                "kebab_name": kebab_name,
            },
        )

        return GeneratedFile(
            path=self.components_path / kebab_name / f"{model.name}Form.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Form extension for {model.name}",
        )

    def _generate_table_base(self, model: ModelSpec) -> GeneratedFile:
        """Generate base table component."""
        kebab_name = to_kebab_case(model.name)
        plural_name = pluralize(model.name)

        # Build column definitions
        columns = self._build_table_columns(model)

        content = self.renderer.render_file(
            "frontend/components/table_base.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_upper": model.name.upper(),
                "kebab_name": kebab_name,
                "plural_name": plural_name,
                "plural_name_lower": plural_name.lower(),
                "columns": columns,
            },
        )

        return GeneratedFile(
            path=self.generated_path / f"{model.name}TableBase.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Base table for {model.name}",
        )

    def _generate_table_extension(self, model: ModelSpec) -> GeneratedFile:
        """Generate user-extensible table component."""
        kebab_name = to_kebab_case(model.name)

        content = self.renderer.render_file(
            "frontend/components/table_extension.tsx.jinja2",
            context={
                "model_name": model.name,
                "kebab_name": kebab_name,
            },
        )

        return GeneratedFile(
            path=self.components_path / kebab_name / f"{model.name}Table.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Table extension for {model.name}",
        )

    def _generate_detail_base(self, model: ModelSpec) -> GeneratedFile:
        """Generate base detail view component."""
        kebab_name = to_kebab_case(model.name)

        # Build detail fields
        detail_fields = self._build_detail_fields(model)

        content = self.renderer.render_file(
            "frontend/components/detail_base.tsx.jinja2",
            context={
                "model_name": model.name,
                "kebab_name": kebab_name,
                "detail_fields": detail_fields,
            },
        )

        return GeneratedFile(
            path=self.generated_path / f"{model.name}DetailBase.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Base detail view for {model.name}",
        )

    def _generate_detail_extension(self, model: ModelSpec) -> GeneratedFile:
        """Generate user-extensible detail component."""
        kebab_name = to_kebab_case(model.name)

        content = self.renderer.render_file(
            "frontend/components/detail_extension.tsx.jinja2",
            context={
                "model_name": model.name,
                "kebab_name": kebab_name,
            },
        )

        return GeneratedFile(
            path=self.components_path / kebab_name / f"{model.name}Detail.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Detail extension for {model.name}",
        )

    def _generate_generated_index(self) -> GeneratedFile:
        """Generate index file for generated components."""
        exports = []

        for model in self.spec.models:
            if model.expose:
                if model.get_frontend_override("generate_form", True):
                    exports.append(
                        f"export {{ {model.name}FormBase, {model.name.upper()}_FIELD_SPECS }} from './{model.name}FormBase';"
                    )
                if model.get_frontend_override("generate_table", True):
                    exports.append(
                        f"export {{ {model.name}TableBase, {model.name.upper()}_COLUMNS }} from './{model.name}TableBase';"
                    )
                if model.get_frontend_override("generate_detail_view", True):
                    exports.append(
                        f"export {{ {model.name}DetailBase }} from './{model.name}DetailBase';"
                    )

        content = self.renderer.render_file(
            "frontend/components/generated_index.ts.jinja2",
            context={
                "exports": exports,
            },
        )

        return GeneratedFile(
            path=self.generated_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Generated components index",
        )

    def _build_field_specs(self, model: ModelSpec) -> str:
        """Build field specifications array for form generation."""
        specs = []

        for field in model.fields:
            if field.hidden:
                continue

            # A field is only required for user input if it's required AND has no default
            user_required = field.required and field.default is None

            # Use camelCase for field names to match TypeScript types and GraphQL schema
            camel_name = to_camel_case(field.name)

            spec_parts = [
                f"name: '{camel_name}'",
                f"type: '{field.type.value}'",
                f"required: {str(user_required).lower()}",
            ]

            # Use effective_label for the display name
            label = field.effective_label
            spec_parts.append(f"displayName: '{label}'")

            # Use effective_tooltip for the description/tooltip
            tooltip = field.effective_tooltip
            if tooltip:
                # Escape single quotes in tooltip
                tooltip_escaped = tooltip.replace("'", "\\'")
                spec_parts.append(f"description: '{tooltip_escaped}'")

            if field.ui_placeholder:
                spec_parts.append(f"placeholder: '{field.ui_placeholder}'")
            if field.ui_widget:
                spec_parts.append(f"uiWidget: '{field.ui_widget}'")
            if field.ui_widget_props:
                props_str = str(field.ui_widget_props).replace("'", '"')
                spec_parts.append(f"widgetProps: {props_str}")
            if field.enum_values:
                values = ", ".join(f"'{v}'" for v in field.enum_values)
                spec_parts.append(f"enumValues: [{values}]")

            # Add references for foreign_key fields
            if field.references:
                spec_parts.append(f"references: '{field.references}'")

            specs.append("  { " + ", ".join(spec_parts) + " }")

        return "[\n" + ",\n".join(specs) + "\n]"

    def _build_table_columns(self, model: ModelSpec) -> str:
        """Build column definitions for table."""
        columns = []

        # Use table_columns from frontend exposure if specified
        table_columns = model.get_frontend_override("table_columns")

        for field in model.fields:
            if field.hidden:
                continue
            if table_columns and field.name not in table_columns:
                continue

            col = {
                "key": to_camel_case(field.name),
                "label": field.effective_label,
            }
            # Add tooltip if available
            tooltip = field.effective_tooltip
            if tooltip:
                tooltip_escaped = tooltip.replace("'", "\\'")
                columns.append(
                    f"  {{ key: '{col['key']}', label: '{col['label']}', tooltip: '{tooltip_escaped}' }}"
                )
            else:
                columns.append(f"  {{ key: '{col['key']}', label: '{col['label']}' }}")

        return "[\n" + ",\n".join(columns) + "\n]"

    def _build_detail_fields(self, model: ModelSpec) -> str:
        """Build detail view field display with Nordic styling."""
        lines = []

        for field in model.fields:
            if field.hidden:
                continue

            camel_name = to_camel_case(field.name)
            label = field.effective_label
            tooltip = field.effective_tooltip

            lines.append("          <div>")
            if tooltip:
                # Add title attribute for tooltip on hover
                # Escape quotes for JSX attribute - use HTML entities for double quotes
                tooltip_escaped = tooltip.replace('"', "&quot;")
                lines.append(
                    f'            <dt className="text-sm font-medium text-nordic-500 mb-1" title="{tooltip_escaped}">{label}</dt>'
                )
            else:
                lines.append(
                    f'            <dt className="text-sm font-medium text-nordic-500 mb-1">{label}</dt>'
                )
            lines.append(
                f"            <dd className=\"text-nordic-900\">{{String(data.{camel_name} ?? '-')}}</dd>"
            )
            lines.append("          </div>")

        if model.timestamps:
            lines.extend(
                [
                    "          <div>",
                    '            <dt className="text-sm font-medium text-nordic-500 mb-1">Created</dt>',
                    '            <dd className="text-nordic-900">{new Date(data.createdAt).toLocaleString()}</dd>',
                    "          </div>",
                    "          <div>",
                    '            <dt className="text-sm font-medium text-nordic-500 mb-1">Updated</dt>',
                    '            <dd className="text-nordic-900">{new Date(data.updatedAt).toLocaleString()}</dd>',
                    "          </div>",
                ]
            )

        return "\n".join(lines)


__all__ = ["ComponentsGenerator"]

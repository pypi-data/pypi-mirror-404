"""GraphQL operations generator for Prism.

Generates GraphQL fragments, queries, mutations, and subscriptions
for frontend use.
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


class GraphQLOpsGenerator(ModelGenerator):
    """Generator for GraphQL operations (queries, mutations, fragments)."""

    REQUIRED_TEMPLATES = [
        "frontend/graphql/gql.ts.jinja2",
        "frontend/graphql/client_urql.ts.jinja2",
        "frontend/graphql/client_apollo.ts.jinja2",
        "frontend/graphql/fragment.ts.jinja2",
        "frontend/graphql/queries.ts.jinja2",
        "frontend/graphql/mutations.ts.jinja2",
        "frontend/graphql/subscriptions.ts.jinja2",
        "frontend/graphql/index.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.generator_config.frontend_output)
        self.graphql_path = frontend_base / self.generator_config.graphql_operations_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared GraphQL files."""
        return [
            self._generate_client(),
            self._generate_gql_module(),
        ]

    def _generate_gql_module(self) -> GeneratedFile:
        """Generate the gql module for tagged template literals."""
        content = self.renderer.render_file(
            "frontend/graphql/gql.ts.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.graphql_path / "gql.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL tagged template literal helper",
        )

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate GraphQL operations for a single model."""
        if not model.expose:
            return []

        files = [
            self._generate_fragment(model),
            self._generate_queries(model),
        ]

        if (
            model.has_operation("create")
            or model.has_operation("update")
            or model.has_operation("delete")
        ):
            files.append(self._generate_mutations(model))

        if model.get_delivery_override("subscriptions", False):
            files.append(self._generate_subscriptions(model))

        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate index file that exports all operations."""
        return [
            self._generate_index(),
        ]

    def _generate_client(self) -> GeneratedFile:
        """Generate the GraphQL client setup."""
        graphql_client = (
            self.exposure_config.frontend.graphql_client if self.exposure_config else "urql"
        )

        template_name = (
            "frontend/graphql/client_urql.ts.jinja2"
            if graphql_client == "urql"
            else "frontend/graphql/client_apollo.ts.jinja2"
        )
        content = self.renderer.render_file(
            template_name,
            context={},
        )

        return GeneratedFile(
            path=self.graphql_path / "client.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL client",
        )

    def _generate_fragment(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL fragment for a model."""
        snake_name = to_snake_case(model.name)

        # Build fragment fields
        fields = ["    id"]

        for field in model.fields:
            field_name = to_camel_case(field.name)
            fields.append(f"    {field_name}")

        if model.timestamps:
            fields.append("    createdAt")
            fields.append("    updatedAt")

        if model.soft_delete:
            fields.append("    deletedAt")

        # Add relationship fields
        for rel in model.relationships:
            rel_field_name = to_camel_case(rel.name)
            # Include basic fields of the related type (id and commonly used fields)
            # Full nested fragments could be added for more complex scenarios
            fields.append(f"    {rel_field_name} {{")
            fields.append("      id")
            fields.append("    }")

        fields_str = "\n".join(fields)

        content = self.renderer.render_file(
            "frontend/graphql/fragment.ts.jinja2",
            context={
                "model_name": model.name,
                "fields_str": fields_str,
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "fragments" / f"{snake_name}.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL fragment for {model.name}",
        )

    def _generate_queries(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL queries for a model."""
        snake_name = to_snake_case(model.name)
        camel_name = to_camel_case(model.name)
        plural_camel = to_camel_case(pluralize(snake_name))

        content = self.renderer.render_file(
            "frontend/graphql/queries.ts.jinja2",
            context={
                "model_name": model.name,
                "camel_name": camel_name,
                "plural_camel": plural_camel,
                "fields_indent_6": self._indent_fields(model, 6),
                "fields_indent_10": self._indent_fields(model, 10),
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "queries" / f"{snake_name}.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL queries for {model.name}",
        )

    def _generate_mutations(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL mutations for a model."""
        snake_name = to_snake_case(model.name)
        content = self.renderer.render_file(
            "frontend/graphql/mutations.ts.jinja2",
            context={
                "model_name": model.name,
                "fields_indent_6": self._indent_fields(model, 6),
                "create_mutation": model.has_operation("create"),
                "update_mutation": model.has_operation("update"),
                "delete_mutation": model.has_operation("delete"),
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "mutations" / f"{snake_name}.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL mutations for {model.name}",
        )

    def _generate_subscriptions(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL subscriptions for a model."""
        snake_name = to_snake_case(model.name)
        camel_name = to_camel_case(model.name)

        content = self.renderer.render_file(
            "frontend/graphql/subscriptions.ts.jinja2",
            context={
                "model_name": model.name,
                "camel_name": camel_name,
                "fields_indent_6": self._indent_fields(model, 6),
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "subscriptions" / f"{snake_name}.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL subscriptions for {model.name}",
        )

    def _generate_index(self) -> GeneratedFile:
        """Generate index file for all GraphQL operations."""
        models_data = []
        for model in self.spec.models:
            if model.expose:
                snake_name = to_snake_case(model.name)
                models_data.append(
                    {
                        "model_name": model.name,
                        "snake_name": snake_name,
                        "has_mutations": model.has_operation("create")
                        or model.has_operation("update")
                        or model.has_operation("delete"),
                        "has_subscriptions": model.get_delivery_override("subscriptions", False),
                    }
                )

        content = self.renderer.render_file(
            "frontend/graphql/index.ts.jinja2",
            context={
                "models": models_data,
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL operations index",
        )

    def _indent_fields(self, model: ModelSpec, indent: int) -> str:
        """Generate indented field list."""
        spaces = " " * indent
        nested_spaces = " " * (indent + 2)
        fields = []

        for field in model.fields:
            field_name = to_camel_case(field.name)
            fields.append(f"{spaces}{field_name}")

        if model.timestamps:
            fields.append(f"{spaces}createdAt")
            fields.append(f"{spaces}updatedAt")

        if model.soft_delete:
            fields.append(f"{spaces}deletedAt")

        # Add relationship fields with basic nested query
        for rel in model.relationships:
            rel_field_name = to_camel_case(rel.name)
            fields.append(f"{spaces}{rel_field_name} {{")
            fields.append(f"{nested_spaces}id")
            fields.append(f"{spaces}}}")

        return "\n".join(fields)


__all__ = ["GraphQLOpsGenerator"]

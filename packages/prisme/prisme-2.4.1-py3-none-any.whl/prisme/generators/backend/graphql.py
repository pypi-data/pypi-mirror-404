"""Strawberry GraphQL generator for Prism.

Generates GraphQL types, queries, mutations, and subscriptions
using Strawberry GraphQL.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prisme.spec.fields import FieldType
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_camel_case, to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.fields import FieldSpec
    from prisme.spec.model import ModelSpec


# Strawberry type mapping
STRAWBERRY_TYPE_MAP: dict[FieldType, str] = {
    FieldType.STRING: "str",
    FieldType.TEXT: "str",
    FieldType.INTEGER: "int",
    FieldType.FLOAT: "float",
    FieldType.DECIMAL: "decimal.Decimal",
    FieldType.BOOLEAN: "bool",
    FieldType.DATETIME: "datetime.datetime",
    FieldType.DATE: "datetime.date",
    FieldType.TIME: "datetime.time",
    FieldType.UUID: "uuid.UUID",
    FieldType.JSON: "strawberry.scalars.JSON",
    FieldType.ENUM: "str",
    FieldType.FOREIGN_KEY: "int",
}


class GraphQLGenerator(ModelGenerator):
    """Generator for Strawberry GraphQL types and operations."""

    REQUIRED_TEMPLATES = [
        "backend/graphql/context.py.jinja2",
        "backend/graphql/scalars.py.jinja2",
        "backend/graphql/pagination.py.jinja2",
        "backend/graphql/type.py.jinja2",
        "backend/graphql/queries.py.jinja2",
        "backend/graphql/mutations.py.jinja2",
        "backend/graphql/subscriptions.py.jinja2",
        "backend/graphql/schema.py.jinja2",
        "backend/graphql/filters.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.generator_config.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        package_base = backend_base / package_name
        self.graphql_path = package_base / self.generator_config.graphql_path
        self.generated_path = package_base / self.generator_config.graphql_generated_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared types and utilities."""
        return [
            self._generate_context(),
            self._generate_scalars(),
            self._generate_pagination(),
            self._generate_common_filters(),
            self._generate_generated_types_init(),
            self._generate_generated_queries_init(),
            self._generate_generated_mutations_init(),
            self._generate_generated_filters_init(),
        ]

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate GraphQL components for a single model."""
        if not model.expose:
            return []

        files = [
            self._generate_type(model),
            self._generate_filters(model),
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
        """Generate schema.py that combines all types."""
        return [
            self._generate_schema(),
            self._generate_graphql_init(),
        ]

    def _generate_context(self) -> GeneratedFile:
        """Generate GraphQL context."""
        project_name = self.get_package_name()
        content = self.renderer.render_file(
            "backend/graphql/context.py.jinja2",
            context={
                "project_name": project_name,
            },
        )
        return GeneratedFile(
            path=self.generated_path / "context.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL context",
        )

    def _generate_scalars(self) -> GeneratedFile:
        """Generate custom scalars."""
        content = self.renderer.render_file(
            "backend/graphql/scalars.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.generated_path / "scalars.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL scalars",
        )

    def _generate_pagination(self) -> GeneratedFile:
        """Generate pagination types."""
        content = self.renderer.render_file(
            "backend/graphql/pagination.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.generated_path / "pagination.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL pagination types",
        )

    def _generate_common_filters(self) -> GeneratedFile:
        """Generate common filter types (StringFilter, IntFilter, etc.)."""
        content = self.renderer.render_file(
            "backend/graphql/common_filters.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.generated_path / "filters" / "common.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Common GraphQL filter types",
        )

    def _generate_generated_types_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated/types folder."""
        imports = []
        exports = []

        for model in self.spec.models:
            if model.expose:
                snake_name = to_snake_case(model.name)
                imports.append(
                    f"from .{snake_name} import {model.name}Type, {model.name}Input, {model.name}UpdateInput"
                )
                exports.extend(
                    [f"{model.name}Type", f"{model.name}Input", f"{model.name}UpdateInput"]
                )

        return create_init_file(
            self.generated_path / "types",
            imports,
            exports,
            "Generated GraphQL types.",
            use_future_annotations=False,  # Strawberry resolves types at runtime; PEP 563 causes recursion
        )

    def _generate_generated_queries_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated/queries folder."""
        imports = []
        exports = []

        for model in self.spec.models:
            if model.expose:
                snake_name = to_snake_case(model.name)
                imports.append(f"from .{snake_name} import {model.name}Queries")
                exports.append(f"{model.name}Queries")

        return create_init_file(
            self.generated_path / "queries",
            imports,
            exports,
            "Generated GraphQL queries.",
        )

    def _generate_generated_mutations_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated/mutations folder."""
        imports = []
        exports = []

        for model in self.spec.models:
            if model.expose and (
                model.has_operation("create")
                or model.has_operation("update")
                or model.has_operation("delete")
            ):
                snake_name = to_snake_case(model.name)
                imports.append(f"from .{snake_name} import {model.name}Mutations")
                exports.append(f"{model.name}Mutations")

        return create_init_file(
            self.generated_path / "mutations",
            imports,
            exports,
            "Generated GraphQL mutations.",
        )

    def _generate_generated_filters_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated/filters folder."""
        # Import common filter types
        imports = [
            "from .common import StringFilter, IntFilter, FloatFilter, BoolFilter, DateTimeFilter, DateFilter"
        ]
        exports = [
            "StringFilter",
            "IntFilter",
            "FloatFilter",
            "BoolFilter",
            "DateTimeFilter",
            "DateFilter",
        ]

        # First pass: determine which models have incoming relations
        models_with_incoming = set()
        for model in self.spec.models:
            if not model.expose:
                continue
            for rel in model.relationships:
                if rel.type in ("one_to_many", "many_to_many"):
                    models_with_incoming.add(rel.target_model)

        # Second pass: build imports and exports
        for model in self.spec.models:
            if model.expose:
                snake_name = to_snake_case(model.name)
                # WhereInput is always exported
                import_items = [f"{model.name}WhereInput"]
                export_items = [f"{model.name}WhereInput"]

                # ListRelationFilter is only exported if this model has incoming relations
                if model.name in models_with_incoming:
                    import_items.append(f"{model.name}ListRelationFilter")
                    export_items.append(f"{model.name}ListRelationFilter")

                imports.append(f"from .{snake_name} import {', '.join(import_items)}")
                exports.extend(export_items)

        return create_init_file(
            self.generated_path / "filters",
            imports,
            exports,
            "Generated GraphQL filter input types.",
        )

    def _generate_type(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL types for a model."""
        snake_name = to_snake_case(model.name)
        package_name = self.get_package_name()

        # Build imports
        imports = self._build_type_imports(model)

        # Build type fields
        type_fields = self._build_type_fields(model)
        input_fields = self._build_input_fields(model)
        update_fields = self._build_update_fields(model)
        conversion_fields = self._build_conversion_fields(model)

        # Build relationship fields
        relationship_fields = self._build_relationship_fields(model)
        relationship_resolvers = self._build_relationship_resolvers(model, package_name)

        content = self.renderer.render_file(
            "backend/graphql/type.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "package_name": package_name,
                "description": model.description or f"{model.name} type",
                "imports": imports,
                "type_fields": type_fields,
                "input_fields": input_fields,
                "update_fields": update_fields,
                "conversion_fields": conversion_fields,
                "relationship_fields": relationship_fields,
                "relationship_resolvers": relationship_resolvers,
                "has_relationships": bool(model.relationships),
            },
        )
        return GeneratedFile(
            path=self.generated_path / "types" / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL type for {model.name}",
        )

    def _generate_filters(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL filter input types for a model."""
        snake_name = to_snake_case(model.name)
        package_name = self.get_package_name()

        # Build the base module path for filters
        graphql_generated_path = self.generator_config.graphql_generated_path
        graphql_module_path = graphql_generated_path.replace("/", ".").replace("\\", ".")
        filters_module_base = f"{package_name}.{graphql_module_path}.filters"

        # Build filter field info for filterable fields
        filter_fields = []
        for field in model.fields:
            if field.filterable:
                filter_fields.append(
                    {
                        "name": field.name,
                        "camel_name": to_camel_case(field.name),
                        "filter_type": self._get_filter_input_type(field),
                    }
                )

        # Build relationship info for to-many relationships (outgoing)
        relationships = [
            {
                "name": rel.name,
                "camel_name": to_camel_case(rel.name),
                "target_model": rel.target_model,
                "target_snake": to_snake_case(rel.target_model),
                "type": rel.type,
                "lazy_module": f"{filters_module_base}.{to_snake_case(rel.target_model)}",
            }
            for rel in model.relationships
            if rel.type in ("one_to_many", "many_to_many")
        ]

        # Check if this model has incoming to-many relations from other models
        # (i.e., other models have this model as a target of one_to_many or many_to_many)
        has_incoming_relations = False
        for other_model in self.spec.models:
            if other_model.name == model.name:
                continue
            for rel in other_model.relationships:
                if rel.target_model == model.name and rel.type in (
                    "one_to_many",
                    "many_to_many",
                ):
                    has_incoming_relations = True
                    break
            if has_incoming_relations:
                break

        # Module path for self-referencing in ListRelationFilter
        self_lazy_module = f"{filters_module_base}.{snake_name}"

        content = self.renderer.render_file(
            "backend/graphql/filters.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "filter_fields": filter_fields,
                "relationships": relationships,
                "has_incoming_relations": has_incoming_relations,
                "self_lazy_module": self_lazy_module,
            },
        )

        return GeneratedFile(
            path=self.generated_path / "filters" / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL filters for {model.name}",
        )

    def _get_filter_input_type(self, field: FieldSpec) -> str:
        """Get the GraphQL filter input type for a field."""
        filter_type_map = {
            FieldType.STRING: "StringFilter",
            FieldType.TEXT: "StringFilter",
            FieldType.INTEGER: "IntFilter",
            FieldType.FLOAT: "FloatFilter",
            FieldType.DECIMAL: "FloatFilter",
            FieldType.BOOLEAN: "BoolFilter",
            FieldType.DATETIME: "DateTimeFilter",
            FieldType.DATE: "DateFilter",
            FieldType.UUID: "StringFilter",
        }
        return filter_type_map.get(field.type, "StringFilter")

    def _build_type_imports(self, model: ModelSpec) -> str:
        """Build import statements for type file."""
        lines = ["import datetime", "import decimal", "import uuid"]

        # Add typing imports - Annotated required for strawberry.lazy()
        if model.relationships:
            lines.append("from typing import TYPE_CHECKING, Annotated, Any")
        else:
            lines.append("from typing import Any")

        lines.append("")
        lines.append("import strawberry")

        # Add Info import if there are relationships (for resolvers)
        if model.relationships:
            lines.append("from strawberry.types import Info")

        lines.append("from strawberry.scalars import JSON")

        # TYPE_CHECKING imports for type checkers (not available at runtime)
        if model.relationships:
            lines.append("")
            lines.append("if TYPE_CHECKING:")
            for rel in model.relationships:
                target_snake = to_snake_case(rel.target_model)
                lines.append(f"    from .{target_snake} import {rel.target_model}Type")

        return "\n".join(lines)

    def _build_type_fields(self, model: ModelSpec) -> str:
        """Build GraphQL type field definitions."""
        lines = ["    id: int"]

        for field in model.fields:
            gql_type = self._get_graphql_type(field)
            field_name = to_camel_case(field.name)

            # Use effective_tooltip (tooltip or description) for GraphQL description
            field_desc = field.effective_tooltip
            if field_desc:
                # Escape quotes in description
                field_desc = field_desc.replace('"', '\\"')
                lines.append(
                    f'    {field_name}: {gql_type} = strawberry.field(description="{field_desc}")'
                )
            else:
                lines.append(f"    {field_name}: {gql_type}")

        if model.timestamps:
            lines.append("    createdAt: datetime.datetime")
            lines.append("    updatedAt: datetime.datetime")

        if model.soft_delete:
            lines.append("    deletedAt: datetime.datetime | None = None")

        return "\n".join(lines)

    def _build_input_fields(self, model: ModelSpec) -> str:
        """Build GraphQL input field definitions."""
        lines = []

        for field in model.fields:
            gql_type = self._get_graphql_type(field, for_input=True)
            field_name = to_camel_case(field.name)

            if not field.required or field.default is not None:
                default_value = self._get_default_value(field)
                lines.append(f"    {field_name}: {gql_type} = {default_value}")
            else:
                lines.append(f"    {field_name}: {gql_type}")

        # Add relationship ID fields for to-many relationships
        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                rel_field_name = f"{to_camel_case(rel.name)}Ids"
                lines.append(f"    {rel_field_name}: list[int] | None = None")

        if not lines:
            lines.append("    pass")

        return "\n".join(lines)

    def _build_update_fields(self, model: ModelSpec) -> str:
        """Build GraphQL update input field definitions (all optional)."""
        lines = []

        for field in model.fields:
            base_type = STRAWBERRY_TYPE_MAP.get(field.type, "str")
            field_name = to_camel_case(field.name)
            lines.append(f"    {field_name}: {base_type} | None = None")

        # Add relationship ID fields for to-many relationships
        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                rel_field_name = f"{to_camel_case(rel.name)}Ids"
                lines.append(f"    {rel_field_name}: list[int] | None = None")

        if not lines:
            lines.append("    pass")

        return "\n".join(lines)

    def _build_conversion_fields(self, model: ModelSpec) -> str:
        """Build field assignments for model-to-type conversion."""
        lines = []

        for field in model.fields:
            snake_name = field.name
            camel_name = to_camel_case(field.name)
            lines.append(f"        {camel_name}=obj.{snake_name},")

        if model.timestamps:
            lines.append("        createdAt=obj.created_at,")
            lines.append("        updatedAt=obj.updated_at,")

        if model.soft_delete:
            lines.append("        deletedAt=obj.deleted_at,")

        # Add relationship fields for lazy resolution
        # Use __dict__.get() to avoid triggering SQLAlchemy lazy loading
        for rel in model.relationships:
            # Pass the relationship data to the type for lazy resolution (only if already loaded)
            lines.append(f"        _db_{rel.name}=obj.__dict__.get('{rel.name}'),")

        return "\n".join(lines)

    def _build_relationship_fields(self, model: ModelSpec) -> str:
        """Build GraphQL relationship field definitions.

        These are private fields that store the model ID for lazy resolution.
        """
        if not model.relationships:
            return ""

        lines = []
        for rel in model.relationships:
            # Store the model object for lazy resolution by the resolver
            lines.append(f"    _db_{rel.name}: strawberry.Private[Any] = None")

        return "\n".join(lines)

    def _build_relationship_resolvers(self, model: ModelSpec, package_name: str = "") -> str:
        """Build GraphQL relationship resolver methods.

        These async methods fetch related entities when the field is queried.
        Uses Annotated with strawberry.lazy() for forward references.

        NOTE: The type template must NOT have 'from __future__ import annotations'
        for strawberry.lazy() to work correctly.
        """
        if not model.relationships:
            return ""

        lines = []

        for rel in model.relationships:
            target_snake = to_snake_case(rel.target_model)
            target_type = f"{rel.target_model}Type"
            field_name = to_camel_case(rel.name)

            # Use Annotated with strawberry.lazy() for forward references
            # The lazy loader tells Strawberry where to find the type
            lazy_type = f'Annotated["{target_type}", strawberry.lazy(".{target_snake}")]'
            if rel.type in ("one_to_many", "many_to_many"):
                return_type = f"list[{lazy_type}]"
            else:
                return_type = f"{lazy_type} | None"

            lines.append("")
            lines.append("    @strawberry.field")
            lines.append(f"    async def {field_name}(self, info: Info) -> {return_type}:")
            lines.append(f'        """Fetch related {rel.target_model} entities."""')
            lines.append(f"        from .{target_snake} import {target_snake}_from_model")
            lines.append(f"        if self._db_{rel.name} is None:")

            if rel.type in ("one_to_many", "many_to_many"):
                lines.append("            return []")
            else:
                lines.append("            return None")

            if rel.type in ("one_to_many", "many_to_many"):
                lines.append(
                    f"        return [{target_snake}_from_model(item) for item in self._db_{rel.name}]"
                )
            else:
                lines.append(f"        return {target_snake}_from_model(self._db_{rel.name})")

        return "\n".join(lines)

    def _get_graphql_type(self, field: FieldSpec, for_input: bool = False) -> str:
        """Get the GraphQL type for a field."""
        base_type = STRAWBERRY_TYPE_MAP.get(field.type, "str")

        # Handle typed JSON arrays
        if field.type == FieldType.JSON and field.json_item_type:
            item_type_map = {
                "str": "str",
                "string": "str",
                "int": "int",
                "integer": "int",
                "float": "float",
                "number": "float",
                "bool": "bool",
                "boolean": "bool",
            }
            gql_item_type = item_type_map.get(field.json_item_type, "str")
            base_type = f"list[{gql_item_type}]"

        if not field.required:
            return f"{base_type} | None"
        return base_type

    def _get_default_value(self, field: FieldSpec) -> str:
        """Get the default value representation.

        For mutable defaults (list/dict), returns a strawberry.field() with
        default_factory to avoid dataclass mutable default errors.
        """
        if field.default is not None:
            if isinstance(field.default, list | dict):
                return f"strawberry.field(default_factory=lambda: {field.default!r})"
            if isinstance(field.default, str):
                return f'"{field.default}"'
            return str(field.default)
        return "None"

    def _generate_queries(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL queries for a model."""
        snake_name = to_snake_case(model.name)
        plural_name = pluralize(snake_name)
        camel_name = to_camel_case(model.name)
        camel_plural = to_camel_case(plural_name)
        package_name = self.get_package_name()

        # Build relationship info for filter conversion
        relationships = [
            {
                "name": rel.name,
                "camel_name": to_camel_case(rel.name),
                "target_model": rel.target_model,
            }
            for rel in model.relationships
            if rel.type in ("one_to_many", "many_to_many")
        ]

        content = self.renderer.render_file(
            "backend/graphql/queries.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "plural_name": plural_name,
                "camel_name": camel_name,
                "camel_plural": camel_plural,
                "package_name": package_name,
                "relationships": relationships,
                "has_relationships": bool(relationships),
            },
        )
        return GeneratedFile(
            path=self.generated_path / "queries" / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL queries for {model.name}",
        )

    def _generate_mutations(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL mutations for a model."""
        snake_name = to_snake_case(model.name)
        package_name = self.get_package_name()
        plural_name = pluralize(snake_name)
        content = self.renderer.render_file(
            "backend/graphql/mutations.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "plural_name": plural_name,
                "plural_model_name": pluralize(model.name),
                "package_name": package_name,
                "create_mutation": model.has_operation("create"),
                "update_mutation": model.has_operation("update"),
                "delete_mutation": model.has_operation("delete"),
            },
        )

        return GeneratedFile(
            path=self.generated_path / "mutations" / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL mutations for {model.name}",
        )

    def _generate_subscriptions(self, model: ModelSpec) -> GeneratedFile:
        """Generate GraphQL subscriptions for a model."""
        snake_name = to_snake_case(model.name)
        camel_name = to_camel_case(model.name)

        content = self.renderer.render_file(
            "backend/graphql/subscriptions.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "camel_name": camel_name,
            },
        )
        return GeneratedFile(
            path=self.generated_path / "subscriptions" / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"GraphQL subscriptions for {model.name}",
        )

    def _generate_schema(self) -> GeneratedFile:
        """Generate the main schema.py file.

        Uses flat query structure where model queries are exposed directly
        on the root Query type (e.g., Query.todo, Query.todos) rather than
        nested under a model namespace.
        """
        enabled_models = [m for m in self.spec.models if m.expose]

        # Build imports for query classes
        query_imports = ", ".join(f"{m.name}Queries" for m in enabled_models)
        mutation_imports = ", ".join(
            f"{m.name}Mutations"
            for m in enabled_models
            if m.has_operation("create") or m.has_operation("update") or m.has_operation("delete")
        )

        # Build the Query class that extends all model query classes
        query_bases = ", ".join(f"{m.name}Queries" for m in enabled_models)

        # Build mutations
        has_mutations = any(
            m.has_operation("create") or m.has_operation("update") or m.has_operation("delete")
            for m in enabled_models
        )

        mutation_bases = ", ".join(
            f"{m.name}Mutations"
            for m in enabled_models
            if m.has_operation("create") or m.has_operation("update") or m.has_operation("delete")
        )

        # Build type imports for schema (helps with forward reference resolution)
        type_imports = ", ".join(f"{m.name}Type" for m in enabled_models)

        content = self.renderer.render_file(
            "backend/graphql/schema.py.jinja2",
            context={
                "spec_title": self.spec.effective_title,
                "spec_description": self.spec.description
                or f"{self.spec.effective_title} GraphQL queries.",
                "query_imports": query_imports,
                "mutation_imports": mutation_imports,
                "query_bases": query_bases,
                "mutation_bases": mutation_bases,
                "has_mutations": has_mutations,
                "type_imports": type_imports,
            },
        )

        return GeneratedFile(
            path=self.graphql_path / "schema.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="GraphQL schema",
        )

    def _generate_graphql_init(self) -> GeneratedFile:
        """Generate __init__.py for graphql folder."""
        return create_init_file(
            self.graphql_path,
            ["from .schema import schema, get_graphql_router"],
            ["schema", "get_graphql_router"],
            "GraphQL API.",
        )


__all__ = ["GraphQLGenerator"]

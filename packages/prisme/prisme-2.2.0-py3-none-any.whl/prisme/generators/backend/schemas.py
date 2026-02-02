"""Pydantic schemas generator for Prism.

Generates Pydantic schema classes from ModelSpec definitions
for API request/response validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prisme.spec.fields import FieldType, FilterOperator
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.fields import FieldSpec
    from prisme.spec.model import ModelSpec


# Pydantic type mapping
PYDANTIC_TYPE_MAP: dict[FieldType, str] = {
    FieldType.STRING: "str",
    FieldType.TEXT: "str",
    FieldType.INTEGER: "int",
    FieldType.FLOAT: "float",
    FieldType.DECIMAL: "Decimal",
    FieldType.BOOLEAN: "bool",
    FieldType.DATETIME: "datetime",
    FieldType.DATE: "date",
    FieldType.TIME: "time",
    FieldType.UUID: "UUID",
    FieldType.JSON: "dict[str, Any] | list[Any]",
    FieldType.ENUM: "str",
    FieldType.FOREIGN_KEY: "int",
}


class SchemasGenerator(ModelGenerator):
    """Generator for Pydantic schema classes."""

    REQUIRED_TEMPLATES = [
        "backend/schemas/base.py.jinja2",
        "backend/schemas/schemas.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.generator_config.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        self.schemas_path = backend_base / package_name / self.generator_config.schemas_path

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared base schema and utilities."""
        return [
            self._generate_base_schema(),
        ]

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate Pydantic schemas for a single model."""
        return [
            self._generate_schemas(model),
        ]

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate __init__.py that exports all schemas."""
        imports = []
        exports = []

        for model in self.spec.models:
            snake_name = to_snake_case(model.name)
            schema_names = [
                f"{model.name}Base",
                f"{model.name}Create",
                f"{model.name}Update",
                f"{model.name}Read",
                f"{model.name}Filter",
            ]
            # Add nested create schema if model has nested_create configured
            if model.nested_create:
                schema_names.append(f"{model.name}CreateNested")
            imports.append(f"from .{snake_name} import {', '.join(schema_names)}")
            exports.extend(schema_names)

        return [
            create_init_file(
                self.schemas_path,
                imports,
                exports,
                "Pydantic schemas for API validation.",
            ),
        ]

    def _generate_base_schema(self) -> GeneratedFile:
        """Generate the base schema class."""
        content = self.renderer.render_file(
            "backend/schemas/base.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.schemas_path / "base.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Base schema class",
        )

    def _generate_schemas(self, model: ModelSpec) -> GeneratedFile:
        """Generate Pydantic schemas for a model."""
        snake_name = to_snake_case(model.name)

        # Build imports
        imports = self._build_imports(model)

        # Build schema classes
        base_schema = self._build_base_schema(model)
        create_schema = self._build_create_schema(model)
        update_schema = self._build_update_schema(model)
        read_schema = self._build_read_schema(model)
        filter_schema = self._build_filter_schema(model)

        # Build optional schemas
        nested_schema = None
        if model.nested_create:
            nested_schema = self._build_nested_create_schema(model)

        conditional_validators = self._build_conditional_validators(model) or None

        content = self.renderer.render_file(
            "backend/schemas/schemas.py.jinja2",
            context={
                "model_name": model.name,
                "imports": imports,
                "base_schema": base_schema,
                "create_schema": create_schema,
                "update_schema": update_schema,
                "read_schema": read_schema,
                "filter_schema": filter_schema,
                "nested_schema": nested_schema,
                "conditional_validators": conditional_validators,
            },
        )

        return GeneratedFile(
            path=self.schemas_path / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Schemas for {model.name}",
        )

    def _build_imports(self, model: ModelSpec) -> str:
        """Build import statements for schemas."""
        lines = []
        typing_imports: set[str] = {"Any"}

        # Check for enum types (need Literal)
        has_enum = any(f.type == FieldType.ENUM for f in model.fields)
        if has_enum:
            typing_imports.add("Literal")

        # Check for date/time types
        datetime_types = set()
        for field in model.fields:
            if field.type == FieldType.DATETIME:
                datetime_types.add("datetime")
            elif field.type == FieldType.DATE:
                datetime_types.add("date")
            elif field.type == FieldType.TIME:
                datetime_types.add("time")

        # timestamps and soft_delete need datetime
        if model.timestamps or model.soft_delete:
            datetime_types.add("datetime")

        if datetime_types:
            lines.append(f"from datetime import {', '.join(sorted(datetime_types))}")

        # Check for Decimal
        has_decimal = any(f.type == FieldType.DECIMAL for f in model.fields)
        if has_decimal:
            lines.append("from decimal import Decimal")

        # Check for UUID
        has_uuid = any(f.type == FieldType.UUID for f in model.fields)
        if has_uuid:
            lines.append("from uuid import UUID")

        # Typing imports
        lines.append(f"from typing import {', '.join(sorted(typing_imports))}")
        lines.append("")

        # Pydantic imports
        pydantic_imports = ["BaseModel", "ConfigDict", "Field"]

        # Check for validators needed
        validators_needed = []
        for field in model.fields:
            if field.pattern:
                validators_needed.append("field_validator")
                break

        # Check for conditional validation
        has_conditional = any(f.conditional_required or f.conditional_enum for f in model.fields)
        if has_conditional:
            validators_needed.append("model_validator")
            typing_imports.add("Self")

        if validators_needed:
            pydantic_imports.extend(validators_needed)

        lines.append(f"from pydantic import {', '.join(sorted(pydantic_imports))}")
        lines.append("")
        lines.append("from .base import SchemaBase")

        return "\n".join(lines)

    def _build_base_schema(self, model: ModelSpec) -> str:
        """Build the base schema with shared fields."""
        lines = [
            f"class {model.name}Base(SchemaBase):",
            f'    """{model.description or f"Base schema for {model.name}."}"""',
            "",
        ]

        for field in model.fields:
            field_def = self._build_field_definition(field, optional=False)
            lines.append(f"    {field_def}")

        if not model.fields:
            lines.append("    pass")

        return "\n".join(lines)

    def _build_create_schema(self, model: ModelSpec) -> str:
        """Build the create input schema."""
        # Get fields allowed for creation (from REST exposure if specified)
        create_fields = model.create_fields

        lines = [
            f"class {model.name}Create({model.name}Base):",
            f'    """Schema for creating a {model.name}."""',
            "",
        ]

        has_override = False
        for field in model.fields:
            # Skip if not in create_fields (when specified)
            if create_fields and field.name not in create_fields:
                continue

            # Fields with defaults can be optional in create
            if field.default is not None or field.default_factory:
                field_def = self._build_field_definition(field, optional=True)
                lines.append(f"    {field_def}")
                has_override = True

        # Add M2M relationship ID fields
        for rel in model.relationships:
            if rel.type == "many_to_many":
                lines.append(f"    {rel.name}_ids: list[int] | None = None")
                has_override = True

        if not has_override:
            lines.append("    pass")

        return "\n".join(lines)

    def _build_update_schema(self, model: ModelSpec) -> str:
        """Build the update input schema (all fields optional)."""
        update_fields = model.update_fields

        lines = [
            f"class {model.name}Update(SchemaBase):",
            f'    """Schema for updating a {model.name}. All fields are optional."""',
            "",
        ]

        for field in model.fields:
            # Skip if not in update_fields (when specified)
            if update_fields and field.name not in update_fields:
                continue

            field_def = self._build_field_definition(field, optional=True)
            lines.append(f"    {field_def}")

        # Add M2M relationship ID fields
        for rel in model.relationships:
            if rel.type == "many_to_many":
                lines.append(f"    {rel.name}_ids: list[int] | None = None")

        if not model.fields and not any(rel.type == "many_to_many" for rel in model.relationships):
            lines.append("    pass")

        return "\n".join(lines)

    def _build_read_schema(self, model: ModelSpec) -> str:
        """Build the read/response schema with ID and timestamps."""
        lines = [
            f"class {model.name}Read({model.name}Base):",
            f'    """Schema for reading a {model.name}."""',
            "",
            "    id: int",
        ]

        if model.timestamps:
            lines.append("    created_at: datetime")
            lines.append("    updated_at: datetime")

        if model.soft_delete:
            lines.append("    deleted_at: datetime | None = None")

        # Add model_config for from_attributes
        lines.append("")
        lines.append("    model_config = ConfigDict(from_attributes=True)")

        return "\n".join(lines)

    def _build_filter_schema(self, model: ModelSpec) -> str:
        """Build the filter schema for list operations."""
        lines = [
            f"class {model.name}Filter(SchemaBase):",
            f'    """Filter schema for listing {model.name}s."""',
            "",
        ]

        for field in model.fields:
            if not field.filterable:
                continue

            # Add filter fields based on operators
            for op in field.filter_operators:
                filter_field = self._build_filter_field(field, op)
                if filter_field:
                    lines.append(f"    {filter_field}")

        # Add relationship filter fields
        rel_filters = self._build_relationship_filter_fields(model)
        if rel_filters:
            lines.append("")
            lines.append("    # Relationship filters")
            lines.extend(rel_filters)

        # Add common filters
        if model.timestamps:
            lines.append("    created_after: datetime | None = None")
            lines.append("    created_before: datetime | None = None")

        if model.soft_delete:
            lines.append("    include_deleted: bool = False")

        if len(lines) == 3:  # Only class definition and docstring
            lines.append("    pass")

        return "\n".join(lines)

    def _build_relationship_filter_fields(self, model: ModelSpec) -> list[str]:
        """Build relationship filter fields for the filter schema.

        Adds filter fields for to-many relationships (one_to_many, many_to_many)
        to enable filtering entities by their related entities.
        """
        lines = []

        for rel in model.relationships:
            # Only add filters for to-many relationships
            if rel.type in ("one_to_many", "many_to_many"):
                # Add filter by single related ID
                lines.append(f"    {rel.name}_id: int | None = None")
                # Add filter by multiple related IDs
                lines.append(f"    {rel.name}_ids: list[int] | None = None")

        return lines

    def _build_nested_create_schema(self, model: ModelSpec) -> str:
        """Build the nested create schema with related entities."""
        if not model.nested_create:
            return ""

        lines = [
            f"class {model.name}CreateNested({model.name}Create):",
            f'    """Schema for creating a {model.name} with nested related entities."""',
            "",
        ]

        # Add nested fields for each relationship in nested_create
        for rel_name in model.nested_create:
            # Find the relationship spec
            rel_spec = next(
                (r for r in model.relationships if r.name == rel_name),
                None,
            )
            if rel_spec:
                target = rel_spec.target_model
                # Use list for one_to_many, single for one_to_one/many_to_one
                if rel_spec.type == "one_to_many":
                    lines.append(
                        f"    {rel_name}: list[{target}Create] = Field(default_factory=list)"
                    )
                elif rel_spec.type in ("one_to_one", "many_to_one"):
                    lines.append(f"    {rel_name}: {target}Create | None = None")
                else:
                    # many_to_many - list of IDs or create schemas
                    lines.append(
                        f"    {rel_name}: list[{target}Create] = Field(default_factory=list)"
                    )

        if len(lines) == 3:  # Only class definition and docstring
            lines.append("    pass")

        return "\n".join(lines)

    def _build_conditional_validators(self, model: ModelSpec) -> str:
        """Build Pydantic validators for conditional validation rules."""

        # Check for conditional_required fields
        required_fields = [f for f in model.fields if f.conditional_required]
        # Check for conditional_enum fields
        enum_fields = [f for f in model.fields if f.conditional_enum]

        if not required_fields and not enum_fields:
            return ""

        # Generate a validator class that extends the base
        lines = [
            f"class {model.name}Validated({model.name}Base):",
            '    """Validated schema with conditional validation rules."""',
            "",
        ]

        # Add model_validator for conditional required
        if required_fields:
            lines.append('    @model_validator(mode="after")')
            lines.append("    def validate_conditional_required(self) -> Self:")
            lines.append('        """Validate conditionally required fields."""')

            for field in required_fields:
                condition = field.conditional_required
                if condition is None:
                    continue
                # Parse condition like "sector == mining"
                parts = condition.split()
                if len(parts) >= 3:
                    cond_field = parts[0]
                    operator = parts[1]
                    cond_value = " ".join(parts[2:]).strip("'\"")

                    if operator == "==":
                        lines.append(
                            f'        if getattr(self, "{cond_field}", None) == "{cond_value}":'
                        )
                        lines.append(f'            if getattr(self, "{field.name}", None) is None:')
                        lines.append(
                            f'                raise ValueError("{field.name} is required when {cond_field} is {cond_value}")'
                        )
                    elif operator == "!=":
                        lines.append(
                            f'        if getattr(self, "{cond_field}", None) != "{cond_value}":'
                        )
                        lines.append(f'            if getattr(self, "{field.name}", None) is None:')
                        lines.append(
                            f'                raise ValueError("{field.name} is required when {cond_field} is not {cond_value}")'
                        )

            lines.append("        return self")
            lines.append("")

        # Add model_validator for conditional enums
        if enum_fields:
            lines.append('    @model_validator(mode="after")')
            lines.append("    def validate_conditional_enums(self) -> Self:")
            lines.append('        """Validate conditionally allowed enum values."""')

            for field in enum_fields:
                if field.conditional_enum is None:
                    continue
                for condition, allowed_values in field.conditional_enum.items():
                    # Parse condition like "sector:mining"
                    if ":" in condition:
                        cond_field, cond_value = condition.split(":", 1)
                        # Use double quotes for the list check (Python code)
                        allowed_str = ", ".join(f'"{v}"' for v in allowed_values)
                        # Use single quotes for error message to avoid escaping issues
                        allowed_str_display = ", ".join(f"'{v}'" for v in allowed_values)
                        lines.append(
                            f'        if getattr(self, "{cond_field}", None) == "{cond_value}":'
                        )
                        lines.append(
                            f"            if self.{field.name} is not None and self.{field.name} not in [{allowed_str}]:"
                        )
                        lines.append(
                            f'                raise ValueError("{field.name} must be one of [{allowed_str_display}] when {cond_field} is {cond_value}")'
                        )

            lines.append("        return self")

        return "\n".join(lines)

    def _build_field_definition(
        self,
        field: FieldSpec,
        optional: bool = False,
    ) -> str:
        """Build a Pydantic field definition."""
        python_type = PYDANTIC_TYPE_MAP.get(field.type, "str")

        # Handle enums
        if field.type == FieldType.ENUM and field.enum_values:
            # Could use Literal type for better validation
            values = ", ".join(f'"{v}"' for v in field.enum_values)
            python_type = f"Literal[{values}]"

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
            py_item_type = item_type_map.get(field.json_item_type, "Any")
            python_type = f"list[{py_item_type}]"

        # Make optional if needed
        if optional or not field.required:
            python_type = f"{python_type} | None"

        # Build Field() arguments
        field_args: list[str] = []

        # Default value
        if optional or not field.required:
            if field.default is not None:
                if isinstance(field.default, str):
                    field_args.append(f'default="{field.default}"')
                else:
                    field_args.append(f"default={field.default}")
            else:
                field_args.append("default=None")

        # Validation constraints
        if field.min_length is not None:
            field_args.append(f"min_length={field.min_length}")
        if field.max_length is not None:
            field_args.append(f"max_length={field.max_length}")
        if field.min_value is not None:
            field_args.append(f"ge={field.min_value}")
        if field.max_value is not None:
            field_args.append(f"le={field.max_value}")
        if field.pattern:
            field_args.append(f'pattern=r"{field.pattern}"')

        # Description - use effective_tooltip (tooltip or description)
        field_desc = field.effective_tooltip
        if field_desc:
            # Escape quotes in description
            field_desc = field_desc.replace('"', '\\"')
            field_args.append(f'description="{field_desc}"')

        # Build the field string
        if field_args:
            return f"{field.name}: {python_type} = Field({', '.join(field_args)})"
        elif optional or not field.required:
            return f"{field.name}: {python_type} = None"
        else:
            return f"{field.name}: {python_type}"

    def _build_filter_field(
        self,
        field: FieldSpec,
        operator: FilterOperator,
    ) -> str | None:
        """Build a filter field for a specific operator."""
        python_type = PYDANTIC_TYPE_MAP.get(field.type, "str")
        name = field.name

        op_suffixes = {
            FilterOperator.EQ: "",
            FilterOperator.NE: "_ne",
            FilterOperator.GT: "_gt",
            FilterOperator.GTE: "_gte",
            FilterOperator.LT: "_lt",
            FilterOperator.LTE: "_lte",
            FilterOperator.LIKE: "_like",
            FilterOperator.ILIKE: "_ilike",
            FilterOperator.IN: "_in",
            FilterOperator.NOT_IN: "_not_in",
            FilterOperator.IS_NULL: "_is_null",
            FilterOperator.CONTAINS: "_contains",
            FilterOperator.STARTS_WITH: "_starts_with",
            FilterOperator.ENDS_WITH: "_ends_with",
        }

        suffix = op_suffixes.get(operator, "")
        field_name = f"{name}{suffix}"

        # Special handling for certain operators
        if operator == FilterOperator.IS_NULL:
            return f"{field_name}: bool | None = None"
        elif operator in (FilterOperator.IN, FilterOperator.NOT_IN):
            return f"{field_name}: list[{python_type}] | None = None"
        elif operator == FilterOperator.BETWEEN:
            # Between needs two values, skip for now
            return None
        else:
            return f"{field_name}: {python_type} | None = None"


__all__ = ["SchemasGenerator"]

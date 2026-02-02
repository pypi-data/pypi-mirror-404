"""SQLAlchemy models generator for Prism.

Generates SQLAlchemy model classes from ModelSpec definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prisme.spec.fields import FieldType
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.fields import FieldSpec
    from prisme.spec.model import ModelSpec, RelationshipSpec


# SQLAlchemy type mapping
SQLALCHEMY_TYPE_MAP: dict[FieldType, str] = {
    FieldType.STRING: "String",
    FieldType.TEXT: "Text",
    FieldType.INTEGER: "Integer",
    FieldType.FLOAT: "Float",
    FieldType.DECIMAL: "Numeric",
    FieldType.BOOLEAN: "Boolean",
    FieldType.DATETIME: "DateTime",
    FieldType.DATE: "Date",
    FieldType.TIME: "Time",
    FieldType.UUID: "UUID",
    FieldType.JSON: "JSON",
    FieldType.ENUM: "Enum",
    FieldType.FOREIGN_KEY: "Integer",  # FK uses the referenced type
}


class ModelsGenerator(ModelGenerator):
    """Generator for SQLAlchemy model classes."""

    REQUIRED_TEMPLATES = [
        "backend/models/base.py.jinja2",
        "backend/models/model.py.jinja2",
        "backend/models/associations.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.generator_config.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        self.models_path = backend_base / package_name / self.generator_config.models_path

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared base model and utilities."""
        files = [
            self._generate_base_model(),
        ]

        # Generate association tables for many-to-many relationships
        association_tables = self._collect_association_tables()
        if association_tables:
            files.append(self._generate_associations(association_tables))

        return files

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate SQLAlchemy model file for a single model."""
        return [
            self._generate_model(model),
        ]

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate __init__.py that exports all models."""
        imports = ["from .base import Base"]
        exports = ["Base"]

        # Add association tables export
        association_tables = self._collect_association_tables()
        if association_tables:
            table_names = [t["name"] for t in association_tables]
            imports.append(f"from .associations import {', '.join(table_names)}")
            exports.extend(table_names)

        for model in self.spec.models:
            snake_name = to_snake_case(model.name)
            imports.append(f"from .{snake_name} import {model.name}")
            exports.append(model.name)

        return [
            create_init_file(
                self.models_path,
                imports,
                exports,
                "SQLAlchemy models.",
            ),
        ]

    def _generate_base_model(self) -> GeneratedFile:
        """Generate the base model class."""
        content = self.renderer.render_file(
            "backend/models/base.py.jinja2",
            context={},
        )
        return GeneratedFile(
            path=self.models_path / "base.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Base model class",
        )

    def _collect_association_tables(self) -> list[dict[str, str]]:
        """Collect all association tables needed for many-to-many relationships.

        Returns a list of dicts with table metadata, deduplicating by table name.
        """
        tables: dict[str, dict[str, str]] = {}

        for model in self.spec.models:
            model_table = model.table_name or to_snake_case(model.name) + "s"

            for rel in model.relationships:
                # Only add if M2M with association table and not already seen
                if (
                    rel.type == "many_to_many"
                    and rel.association_table
                    and rel.association_table not in tables
                ):
                    target_table = self._get_table_name_for_model(rel.target_model)

                    # Determine column names from table names
                    # e.g., "signals" -> "signal_id", "instruments" -> "instrument_id"
                    left_column = model_table.rstrip("s") + "_id"
                    right_column = target_table.rstrip("s") + "_id"

                    tables[rel.association_table] = {
                        "name": rel.association_table,
                        "left_table": model_table,
                        "right_table": target_table,
                        "left_column": left_column,
                        "right_column": right_column,
                    }

        return list(tables.values())

    def _generate_associations(self, association_tables: list[dict[str, str]]) -> GeneratedFile:
        """Generate the associations.py file with many-to-many tables."""
        content = self.renderer.render_file(
            "backend/models/associations.py.jinja2",
            context={"association_tables": association_tables},
        )
        return GeneratedFile(
            path=self.models_path / "associations.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Association tables for many-to-many relationships",
        )

    def _generate_model(self, model: ModelSpec) -> GeneratedFile:
        """Generate a SQLAlchemy model for a single ModelSpec."""
        snake_name = to_snake_case(model.name)
        table_name = model.table_name or to_snake_case(model.name) + "s"

        # Build imports
        imports = self._build_imports(model)

        # Build column definitions
        columns = self._build_columns(model)

        # Build relationships
        relationships = self._build_relationships(model)

        # Build class definition
        mixins = self._build_mixins(model)
        base_classes = ["Base", *mixins]

        content = self.renderer.render_file(
            "backend/models/model.py.jinja2",
            context={
                "model_name": model.name,
                "description": model.description,
                "table_name": table_name,
                "imports": imports,
                "base_classes": base_classes,
                "columns": columns,
                "relationships": relationships,
            },
        )
        return GeneratedFile(
            path=self.models_path / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"Model for {model.name}",
        )

    def _build_imports(self, model: ModelSpec) -> str:
        """Build import statements for a model."""
        sqlalchemy_imports: set[str] = set()  # mapped_column comes from sqlalchemy.orm
        typing_imports: set[str] = set()

        # Collect base imports - always include Base, conditionally add mixins
        base_imports = ["Base"]
        if model.timestamps:
            base_imports.append("TimestampMixin")
        if model.soft_delete:
            base_imports.append("SoftDeleteMixin")

        # Analyze fields for required imports
        for field in model.fields:
            sa_type = SQLALCHEMY_TYPE_MAP.get(field.type, "String")
            sqlalchemy_imports.add(sa_type)

            # Note: UUID is imported from uuid module, not typing
            if field.type == FieldType.ENUM:
                sqlalchemy_imports.add("Enum")
            if field.type == FieldType.FOREIGN_KEY:
                sqlalchemy_imports.add("ForeignKey")

        # Check for many_to_one relationships that need ForeignKey
        for rel in model.relationships:
            if rel.type == "many_to_one":
                sqlalchemy_imports.add("ForeignKey")
            if field.unique or field.indexed:
                sqlalchemy_imports.add("Index")
            if not field.required:
                typing_imports.add("Optional")

        # Check for relationships
        if model.relationships:
            sqlalchemy_imports.add("relationship")
            typing_imports.add("TYPE_CHECKING")

        # Build import lines
        lines = []

        if typing_imports:
            lines.append(f"from typing import {', '.join(sorted(typing_imports))}")

        # UUID import
        has_uuid = any(f.type == FieldType.UUID for f in model.fields)
        if has_uuid:
            lines.append("from uuid import UUID as PyUUID")

        # Datetime imports
        has_datetime = any(
            f.type in (FieldType.DATETIME, FieldType.DATE, FieldType.TIME) for f in model.fields
        )
        if has_datetime:
            datetime_types = []
            if any(f.type == FieldType.DATETIME for f in model.fields):
                datetime_types.append("datetime")
            if any(f.type == FieldType.DATE for f in model.fields):
                datetime_types.append("date")
            if any(f.type == FieldType.TIME for f in model.fields):
                datetime_types.append("time")
            lines.append(f"from datetime import {', '.join(datetime_types)}")

        # Decimal import
        has_decimal = any(f.type == FieldType.DECIMAL for f in model.fields)
        if has_decimal:
            lines.append("from decimal import Decimal")

        # SQLAlchemy imports (mapped_column comes from sqlalchemy.orm)
        sa_imports = sorted(sqlalchemy_imports - {"relationship", "mapped_column"})
        if sa_imports:
            lines.append(f"from sqlalchemy import {', '.join(sa_imports)}")
        if "relationship" in sqlalchemy_imports:
            lines.append("from sqlalchemy.orm import Mapped, mapped_column, relationship")
        else:
            lines.append("from sqlalchemy.orm import Mapped, mapped_column")

        lines.append("")
        lines.append(f"from .base import {', '.join(base_imports)}")

        # Import association tables for many-to-many relationships
        m2m_tables = [
            rel.association_table
            for rel in model.relationships
            if rel.type == "many_to_many" and rel.association_table
        ]
        if m2m_tables:
            tables_import = ", ".join(m2m_tables)
            lines.append(f"from .associations import {tables_import}")

        # TYPE_CHECKING imports for relationships
        if model.relationships:
            lines.append("")
            lines.append("if TYPE_CHECKING:")
            for rel in model.relationships:
                rel_snake = to_snake_case(rel.target_model)
                lines.append(f"    from .{rel_snake} import {rel.target_model}")

        return "\n".join(lines)

    def _build_columns(self, model: ModelSpec) -> str:
        """Build column definitions for a model."""
        lines = []

        # Always add ID column first
        lines.append("    id: Mapped[int] = mapped_column(primary_key=True)")

        # Get table name for enum naming (to avoid conflicts between models)
        table_name = model.table_name or to_snake_case(model.name) + "s"

        # Collect existing field names to avoid duplicates
        existing_field_names = {field.name for field in model.fields}

        for field in model.fields:
            column_def = self._build_column(field, table_name=table_name)
            lines.append(f"    {column_def}")

        # Auto-generate FK columns for many_to_one relationships
        # Skip if field already exists (user defined explicit FK field)
        for rel in model.relationships:
            if rel.type == "many_to_one":
                fk_column_name = f"{rel.name}_id"
                if fk_column_name not in existing_field_names:
                    fk_column = self._build_fk_column_for_relationship(rel)
                    lines.append(f"    {fk_column}")

        return "\n".join(lines)

    def _get_table_name_for_model(self, model_name: str) -> str:
        """Get the table name for a model by looking it up in the spec."""
        for model in self.spec.models:
            if model.name == model_name:
                return model.table_name or to_snake_case(model.name) + "s"
        # Fallback to default naming if model not found
        return to_snake_case(model_name) + "s"

    def _build_fk_column_for_relationship(self, rel: RelationshipSpec) -> str:
        """Build a foreign key column for a many_to_one relationship.

        For many_to_one relationships, we need to generate a FK column like:
            instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)

        For optional relationships:
            instrument_id: Mapped[int | None] = mapped_column(ForeignKey("instruments.id"), index=True, nullable=True)
        """
        # Column name: {relationship_name}_id
        column_name = f"{rel.name}_id"

        # Get the target table name
        target_table = self._get_table_name_for_model(rel.target_model)

        # Handle optional/nullable FK
        if rel.optional:
            python_type = "int | None"
            nullable_arg = ", nullable=True"
        else:
            python_type = "int"
            nullable_arg = ""

        # Build the column definition
        return (
            f"{column_name}: Mapped[{python_type}] = mapped_column("
            f'ForeignKey("{target_table}.id"), index=True{nullable_arg})'
        )

    def _build_column(self, field: FieldSpec, table_name: str | None = None) -> str:
        """Build a single column definition."""
        name = field.name
        sa_type = SQLALCHEMY_TYPE_MAP.get(field.type, "String")
        python_type = self._get_python_type(field)

        # Build mapped_column arguments
        args: list[str] = []

        # Type with length/precision
        if field.type == FieldType.STRING and field.max_length:
            args.append(f"String({field.max_length})")
        elif field.type == FieldType.DECIMAL and field.precision:
            scale = field.scale or 2
            args.append(f"Numeric({field.precision}, {scale})")
        elif field.type == FieldType.ENUM and field.enum_values:
            enum_values = ", ".join(f'"{v}"' for v in field.enum_values)
            # Only prefix common field names that are likely to conflict between models
            # (e.g., "status", "type", "category" -> "position_status_enum")
            # More specific field names (e.g., "asset_type", "price_source") use field name only
            common_field_names = {"status", "type", "category", "state", "kind", "level"}
            snake_name = to_snake_case(name)
            if snake_name in common_field_names and table_name:
                table_prefix = table_name.rstrip("s")
                enum_name = f"{table_prefix}_{snake_name}_enum"
            else:
                enum_name = f"{snake_name}_enum"
            args.append(f"Enum({enum_values}, name='{enum_name}')")
        elif field.type == FieldType.DATETIME:
            args.append("DateTime(timezone=True)")
        elif field.type == FieldType.FOREIGN_KEY and field.references:
            ref_table = self._get_table_name_for_model(field.references)
            args.append(f'ForeignKey("{ref_table}.id", ondelete="{field.on_delete}")')
        elif sa_type != "String":
            args.append(sa_type)

        # Constraints
        if field.unique:
            args.append("unique=True")
        if field.indexed:
            args.append("index=True")
        if not field.required:
            args.append("nullable=True")
        if field.default is not None:
            if isinstance(field.default, str):
                args.append(f'default="{field.default}"')
            else:
                args.append(f"default={field.default}")

        args_str = ", ".join(args)
        return f"{name}: Mapped[{python_type}] = mapped_column({args_str})"

    def _get_python_type(self, field: FieldSpec) -> str:
        """Get the Python type annotation for a field."""
        type_map = {
            FieldType.STRING: "str",
            FieldType.TEXT: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.DECIMAL: "Decimal",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "datetime",
            FieldType.DATE: "date",
            FieldType.TIME: "time",
            FieldType.UUID: "PyUUID",
            FieldType.JSON: "dict | list",
            FieldType.ENUM: "str",
            FieldType.FOREIGN_KEY: "int",
        }

        base_type = type_map.get(field.type, "str")

        if not field.required:
            return f"{base_type} | None"
        return base_type

    def _build_relationships(self, model: ModelSpec) -> str:
        """Build relationship definitions for a model."""
        if not model.relationships:
            return ""

        lines = ["", "    # Relationships"]

        for rel in model.relationships:
            rel_def = self._build_relationship(rel)
            lines.append(f"    {rel_def}")

        return "\n".join(lines)

    def _build_relationship(self, rel: RelationshipSpec) -> str:
        """Build a single relationship definition."""
        args: list[str] = [f'"{rel.target_model}"']

        # Add secondary table for many-to-many relationships
        if rel.type == "many_to_many" and rel.association_table:
            args.append(f"secondary={rel.association_table}")

        if rel.back_populates:
            args.append(f'back_populates="{rel.back_populates}"')

        if rel.lazy != "select":
            args.append(f'lazy="{rel.lazy}"')

        # Only add cascade for non-many-to-many relationships
        # Many-to-many relationships should not use cascade="all, delete-orphan"
        if rel.type != "many_to_many" and rel.cascade != "all, delete-orphan":
            args.append(f'cascade="{rel.cascade}"')

        # Determine the type based on relationship type
        if rel.type in ("one_to_many", "many_to_many"):
            python_type = f'list["{rel.target_model}"]'
        else:
            # For forward references with Optional, the | None must be inside the string
            python_type = f'"{rel.target_model} | None"'

        args_str = ", ".join(args)
        return f"{rel.name}: Mapped[{python_type}] = relationship({args_str})"

    def _build_mixins(self, model: ModelSpec) -> list[str]:
        """Get the list of mixins to use for a model."""
        mixins = []
        if model.timestamps:
            mixins.append("TimestampMixin")
        if model.soft_delete:
            mixins.append("SoftDeleteMixin")
        return mixins


__all__ = ["ModelsGenerator"]

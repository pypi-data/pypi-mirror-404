"""FastMCP tools generator for Prism.

Generates MCP tools for AI assistant integration using FastMCP.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prisme.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prisme.spec.fields import FieldType
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import pluralize, to_snake_case
from prisme.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prisme.spec.fields import FieldSpec
    from prisme.spec.model import ModelSpec


class MCPGenerator(ModelGenerator):
    """Generator for FastMCP tools."""

    REQUIRED_TEMPLATES = [
        "backend/mcp/server.py.jinja2",
        "backend/mcp/tools.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.generator_config.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        self.mcp_path = backend_base / package_name / self.generator_config.mcp_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared MCP server setup."""
        return [
            self._generate_server(),
        ]

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate MCP tools for a single model."""
        if not model.expose:
            return []

        return [
            self._generate_tools(model),
        ]

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate __init__.py for MCP module."""
        imports = ["from .server import mcp, run_server"]
        exports = ["mcp", "run_server"]

        for model in self.spec.models:
            if model.expose:
                snake_name = to_snake_case(model.name)
                imports.append(f"from .{snake_name}_tools import register_{snake_name}_tools")
                exports.append(f"register_{snake_name}_tools")

        return [
            create_init_file(
                self.mcp_path,
                imports,
                exports,
                "MCP tools for AI assistant integration.",
            ),
        ]

    def _generate_server(self) -> GeneratedFile:
        """Generate the main MCP server."""
        # Get all enabled models
        enabled_models = [m for m in self.spec.models if m.expose]

        # Get project name for imports
        project_name_snake = self.get_package_name().replace("-", "_")

        register_calls = []
        imports = []

        for model in enabled_models:
            snake_name = to_snake_case(model.name)
            imports.append(f"from .{snake_name}_tools import register_{snake_name}_tools")
            register_calls.append(f"    register_{snake_name}_tools(mcp)")

        register_imports = "\n".join(imports)
        register_block = "\n".join(register_calls) if register_calls else "    pass"

        content = self.renderer.render_file(
            "backend/mcp/server.py.jinja2",
            context={
                "project_name_snake": project_name_snake,
                "title": self.spec.effective_title,
                "instructions": self.spec.description
                or f"{self.spec.effective_title} - MCP server for AI assistant integration",
                "register_imports": register_imports,
                "register_block": register_block,
            },
        )

        return GeneratedFile(
            path=self.mcp_path / "server.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="MCP server",
        )

    def _generate_tools(self, model: ModelSpec) -> GeneratedFile:
        """Generate MCP tools for a model."""
        snake_name = to_snake_case(model.name)
        plural_name = pluralize(snake_name)
        tool_prefix = model.get_mcp_override("tool_prefix") or snake_name

        # Get tool descriptions with defaults
        descriptions = model.get_mcp_override("tool_descriptions", {})
        list_desc = descriptions.get(
            "list", f"List {plural_name} with optional filtering and pagination"
        )
        read_desc = descriptions.get("read", f"Get a {snake_name} by ID")
        create_desc = descriptions.get("create", f"Create a new {snake_name}")
        update_desc = descriptions.get("update", f"Update an existing {snake_name}")
        delete_desc = descriptions.get("delete", f"Delete a {snake_name}")

        # Build field parameters for create/update
        create_params = self._build_tool_params(model, for_update=False)
        update_params = self._build_tool_params(model, for_update=True)
        create_field_names = ", ".join(f"{f.name}={f.name}" for f in model.fields)
        update_field_dict = self._build_update_dict(model)

        # Build relationship parameters
        relationship_params = self._build_relationship_params(model)
        relationship_args_doc = self._build_relationship_args_doc(model)

        # Get project name for imports
        project_name_snake = self.get_package_name().replace("-", "_")

        # Build Args documentation for create/update
        create_args_doc = self._build_field_args_doc(model)
        update_args_doc = self._build_field_args_doc(model)

        # Build list filter parameters and dict construction
        list_filter_params = self._build_list_filter_params(model)
        list_filter_dict = self._build_list_filter_dict(model)
        list_filter_args_doc = self._build_list_filter_args_doc(model)

        content = self.renderer.render_file(
            "backend/mcp/tools.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "plural_name": plural_name,
                "project_name_snake": project_name_snake,
                "tool_prefix": tool_prefix,
                "ops_list": model.has_operation("list"),
                "ops_read": model.has_operation("read"),
                "ops_create": model.has_operation("create"),
                "ops_update": model.has_operation("update"),
                "ops_delete": model.has_operation("delete"),
                "list_desc": list_desc,
                "read_desc": read_desc,
                "create_desc": create_desc,
                "update_desc": update_desc,
                "delete_desc": delete_desc,
                "create_params": create_params,
                "update_params": update_params,
                "create_field_names": create_field_names,
                "create_args_doc": create_args_doc,
                "update_args_doc": update_args_doc,
                "update_field_dict": update_field_dict,
                "relationship_params": relationship_params,
                "relationship_args_doc": relationship_args_doc,
                "has_relationships": bool(model.relationships),
                "relationships": [
                    {
                        "name": rel.name,
                        "target_model": rel.target_model,
                        "type": rel.type,
                        "ids_param": f"{rel.name}_ids",
                    }
                    for rel in model.relationships
                    if rel.type in ("one_to_many", "many_to_many")
                ],
                "list_filter_params": list_filter_params,
                "list_filter_dict": list_filter_dict,
                "list_filter_args_doc": list_filter_args_doc,
                "has_list_filters": bool(list_filter_params),
            },
        )

        return GeneratedFile(
            path=self.mcp_path / f"{snake_name}_tools.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"MCP tools for {model.name}",
        )

    def _build_update_dict(self, model: ModelSpec) -> str:
        """Build update dictionary assignment for tool."""
        lines = []
        for field in model.fields:
            lines.append(f"            if {field.name} is not None:")
            lines.append(f'                update_fields["{field.name}"] = {field.name}')
        return "\n".join(lines)

    def _build_field_args_doc(self, model: ModelSpec) -> str:
        """Build Args documentation for fields (required first, then optional)."""
        required_lines = []
        optional_lines = []
        for field in model.fields:
            # Get the best description for the field
            desc = field.effective_tooltip or field.effective_label
            if field.required and field.default is None:
                required_lines.append(f"            {field.name}: {desc}")
            else:
                optional_lines.append(f"            {field.name}: {desc} (optional)")
        return "\n".join(required_lines + optional_lines)

    def _build_tool_params(self, model: ModelSpec, for_update: bool) -> str:
        """Build function parameters for tool with field descriptions."""
        required_lines = []
        optional_lines = []

        for field in model.fields:
            python_type = self._get_python_type(field)
            # Get field description for documentation
            field_desc = field.effective_tooltip or field.effective_label

            if for_update:
                # All fields optional for update
                optional_lines.append(
                    f"        {field.name}: {python_type} | None = None,  # {field_desc}"
                )
            else:
                # Respect required for create
                if not field.required or field.default is not None:
                    default = self._get_default_str(field)
                    optional_lines.append(
                        f"        {field.name}: {python_type} | None = {default},  # {field_desc}"
                    )
                else:
                    required_lines.append(f"        {field.name}: {python_type},  # {field_desc}")

        # Python requires required parameters before optional ones
        return "\n".join(required_lines + optional_lines)

    def _get_python_type(self, field: FieldSpec) -> str:
        """Get Python type for a field."""
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
            return f"list[{py_item_type}]"

        type_map = {
            FieldType.STRING: "str",
            FieldType.TEXT: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.DECIMAL: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "str",  # ISO format string for MCP
            FieldType.DATE: "str",
            FieldType.TIME: "str",
            FieldType.UUID: "str",
            FieldType.JSON: "dict | list",
            FieldType.ENUM: "str",
            FieldType.FOREIGN_KEY: "int",
        }
        return type_map.get(field.type, "str")

    def _get_default_str(self, field: FieldSpec) -> str:
        """Get default value as string."""
        if field.default is not None:
            # Avoid mutable default arguments (B006) for list/dict defaults
            if isinstance(field.default, list | dict):
                return "None"
            if isinstance(field.default, str):
                return f'"{field.default}"'
            return str(field.default)
        return "None"

    def _build_relationship_params(self, model: ModelSpec) -> str:
        """Build function parameters for relationship fields."""
        lines = []

        for rel in model.relationships:
            # Only add params for to-many relationships that can be managed via IDs
            if rel.type in ("one_to_many", "many_to_many"):
                param_name = f"{rel.name}_ids"
                desc = f"IDs of related {rel.target_model} entities"
                lines.append(f"        {param_name}: list[int] | None = None,  # {desc}")

        return "\n".join(lines)

    def _build_relationship_args_doc(self, model: ModelSpec) -> str:
        """Build Args documentation for relationship fields."""
        lines = []

        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                param_name = f"{rel.name}_ids"
                desc = f"List of {rel.target_model} IDs to link (optional)"
                lines.append(f"            {param_name}: {desc}")

        return "\n".join(lines)

    def _build_list_filter_params(self, model: ModelSpec) -> str:
        """Build filter parameters for the list tool."""
        lines = []

        # Add relationship ID filters
        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                # Single ID filter
                lines.append(
                    f"        {rel.name}_id: int | None = None,  "
                    f"# Filter by related {rel.target_model} ID"
                )

        return "\n".join(lines)

    def _build_list_filter_dict(self, model: ModelSpec) -> str:
        """Build filter dictionary construction for list tool.

        Note: Uses 12-space indentation to align with code inside
        the async with block in the function body.
        """
        lines = ["            filters = {}"]

        # Add relationship filter dict entries
        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                param_name = f"{rel.name}_id"
                lines.append(f"            if {param_name} is not None:")
                lines.append(f'                filters["{param_name}"] = {param_name}')

        return "\n".join(lines)

    def _build_list_filter_args_doc(self, model: ModelSpec) -> str:
        """Build Args documentation for list filter parameters."""
        lines = []

        for rel in model.relationships:
            if rel.type in ("one_to_many", "many_to_many"):
                param_name = f"{rel.name}_id"
                desc = f"Filter by related {rel.target_model} ID (optional)"
                lines.append(f"            {param_name}: {desc}")

        return "\n".join(lines)


__all__ = ["MCPGenerator"]

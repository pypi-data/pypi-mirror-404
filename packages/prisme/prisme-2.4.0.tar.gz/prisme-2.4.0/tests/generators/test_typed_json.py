"""Tests for typed JSON fields feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.graphql import GraphQLGenerator
from prisme.generators.backend.mcp import MCPGenerator
from prisme.generators.backend.schemas import SchemasGenerator
from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.types import TypeScriptGenerator
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def typed_json_model() -> ModelSpec:
    """Create a model with typed JSON fields."""
    return ModelSpec(
        name="Document",
        fields=[
            FieldSpec(name="title", type=FieldType.STRING, required=True),
            FieldSpec(
                name="tags",
                type=FieldType.JSON,
                json_item_type="str",
                description="List of tags",
            ),
            FieldSpec(
                name="scores",
                type=FieldType.JSON,
                json_item_type="int",
                description="List of scores",
            ),
            FieldSpec(
                name="weights",
                type=FieldType.JSON,
                json_item_type="float",
                description="List of weights",
            ),
            FieldSpec(
                name="metadata",
                type=FieldType.JSON,
                description="Arbitrary metadata (untyped)",
            ),
        ],
    )


@pytest.fixture
def typed_json_stack(typed_json_model: ModelSpec) -> StackSpec:
    """Create a stack with typed JSON model."""
    return StackSpec(
        name="test-typed-json",
        version="1.0.0",
        models=[typed_json_model],
    )


@pytest.fixture
def typed_json_context(typed_json_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for typed JSON tests."""
    return GeneratorContext(
        domain_spec=typed_json_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-typed-json"),
    )


class TestTypedJsonFieldSpec:
    """Tests for json_item_type field in FieldSpec."""

    def test_field_with_json_item_type(self) -> None:
        """FieldSpec accepts json_item_type parameter."""
        field = FieldSpec(
            name="tags",
            type=FieldType.JSON,
            json_item_type="str",
        )
        assert field.json_item_type == "str"

    def test_field_without_json_item_type(self) -> None:
        """FieldSpec defaults json_item_type to None."""
        field = FieldSpec(
            name="data",
            type=FieldType.JSON,
        )
        assert field.json_item_type is None


class TestTypedJsonTypeScript:
    """Tests for TypeScript generator with typed JSON."""

    def test_generates_string_array(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with str item type generates string[]."""
        generator = TypeScriptGenerator(typed_json_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # tags field should be string[]
        assert "tags?: string[]" in content or "tags: string[]" in content

    def test_generates_number_array_for_int(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with int item type generates number[]."""
        generator = TypeScriptGenerator(typed_json_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # scores field should be number[]
        assert "scores?: number[]" in content or "scores: number[]" in content

    def test_generates_number_array_for_float(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with float item type generates number[]."""
        generator = TypeScriptGenerator(typed_json_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # weights field should be number[]
        assert "weights?: number[]" in content or "weights: number[]" in content

    def test_untyped_json_remains_record(self, typed_json_context: GeneratorContext) -> None:
        """Untyped JSON field uses Record<string, unknown>."""
        generator = TypeScriptGenerator(typed_json_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # metadata field should be Record<string, unknown>
        assert "Record<string, unknown>" in content


class TestTypedJsonPydantic:
    """Tests for Pydantic schema generator with typed JSON."""

    def test_generates_list_str(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with str generates list[str]."""
        generator = SchemasGenerator(typed_json_context)
        files = generator.generate_files()

        schema_file = next(f for f in files if "document.py" in str(f.path))
        content = schema_file.content

        assert "list[str]" in content

    def test_generates_list_int(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with int generates list[int]."""
        generator = SchemasGenerator(typed_json_context)
        files = generator.generate_files()

        schema_file = next(f for f in files if "document.py" in str(f.path))
        content = schema_file.content

        assert "list[int]" in content

    def test_generates_list_float(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with float generates list[float]."""
        generator = SchemasGenerator(typed_json_context)
        files = generator.generate_files()

        schema_file = next(f for f in files if "document.py" in str(f.path))
        content = schema_file.content

        assert "list[float]" in content

    def test_untyped_json_remains_dict(self, typed_json_context: GeneratorContext) -> None:
        """Untyped JSON uses dict[str, Any]."""
        generator = SchemasGenerator(typed_json_context)
        files = generator.generate_files()

        schema_file = next(f for f in files if "document.py" in str(f.path))
        content = schema_file.content

        assert "dict[str, Any]" in content


class TestTypedJsonGraphQL:
    """Tests for GraphQL generator with typed JSON."""

    def test_generates_list_type(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON generates list[type] in GraphQL."""
        generator = GraphQLGenerator(typed_json_context)
        files = generator.generate_files()

        # Find the type file
        type_file = next(
            (f for f in files if "types" in str(f.path) and "document" in str(f.path)),
            None,
        )
        if type_file:
            content = type_file.content
            # Should have list types for typed JSON fields
            assert "list[str]" in content or "list[int]" in content


class TestTypedJsonMCP:
    """Tests for MCP generator with typed JSON."""

    def test_generates_list_str(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with str generates list[str] in MCP tools."""
        generator = MCPGenerator(typed_json_context)
        files = generator.generate_files()

        # Find the document tools file
        tools_file = next(
            (f for f in files if "document_tools.py" in str(f.path)),
            None,
        )
        assert tools_file is not None
        content = tools_file.content

        # tags field should be list[str]
        assert "list[str]" in content

    def test_generates_list_int(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with int generates list[int] in MCP tools."""
        generator = MCPGenerator(typed_json_context)
        files = generator.generate_files()

        tools_file = next(
            (f for f in files if "document_tools.py" in str(f.path)),
            None,
        )
        assert tools_file is not None
        content = tools_file.content

        # scores field should be list[int]
        assert "list[int]" in content

    def test_generates_list_float(self, typed_json_context: GeneratorContext) -> None:
        """Typed JSON with float generates list[float] in MCP tools."""
        generator = MCPGenerator(typed_json_context)
        files = generator.generate_files()

        tools_file = next(
            (f for f in files if "document_tools.py" in str(f.path)),
            None,
        )
        assert tools_file is not None
        content = tools_file.content

        # weights field should be list[float]
        assert "list[float]" in content

    def test_untyped_json_remains_dict(self, typed_json_context: GeneratorContext) -> None:
        """Untyped JSON uses dict in MCP tools."""
        generator = MCPGenerator(typed_json_context)
        files = generator.generate_files()

        tools_file = next(
            (f for f in files if "document_tools.py" in str(f.path)),
            None,
        )
        assert tools_file is not None
        content = tools_file.content

        # metadata field should remain dict
        assert "metadata: dict" in content

"""Tests for nested create feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.schemas import SchemasGenerator
from prisme.generators.backend.services import ServicesGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec, RelationshipSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def nested_create_models() -> list[ModelSpec]:
    """Create models with nested create relationships."""
    return [
        ModelSpec(
            name="Order",
            fields=[
                FieldSpec(name="order_number", type=FieldType.STRING, required=True),
                FieldSpec(name="total", type=FieldType.DECIMAL, required=True),
            ],
            relationships=[
                RelationshipSpec(
                    name="items",
                    target_model="OrderItem",
                    type="one_to_many",
                    back_populates="order",
                ),
            ],
            nested_create=["items"],  # Enable nested create for items
        ),
        ModelSpec(
            name="OrderItem",
            fields=[
                FieldSpec(name="product_name", type=FieldType.STRING, required=True),
                FieldSpec(name="quantity", type=FieldType.INTEGER, required=True),
                FieldSpec(name="price", type=FieldType.DECIMAL, required=True),
                FieldSpec(
                    name="order_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Order",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="order",
                    target_model="Order",
                    type="many_to_one",
                    back_populates="items",
                ),
            ],
        ),
    ]


@pytest.fixture
def nested_create_stack(nested_create_models: list[ModelSpec]) -> StackSpec:
    """Create a stack with nested create models."""
    return StackSpec(
        name="test-nested-create",
        version="1.0.0",
        models=nested_create_models,
    )


@pytest.fixture
def nested_create_context(nested_create_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for nested create tests."""
    return GeneratorContext(
        domain_spec=nested_create_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-nested-create"),
    )


class TestNestedCreateModelSpec:
    """Tests for nested_create field in ModelSpec."""

    def test_model_with_nested_create(self) -> None:
        """ModelSpec accepts nested_create parameter."""
        model = ModelSpec(
            name="Parent",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
            relationships=[
                RelationshipSpec(
                    name="children",
                    target_model="Child",
                    type="one_to_many",
                ),
            ],
            nested_create=["children"],
        )
        assert model.nested_create == ["children"]

    def test_model_without_nested_create(self) -> None:
        """ModelSpec defaults nested_create to None."""
        model = ModelSpec(
            name="Simple",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        )
        assert model.nested_create is None


class TestNestedCreateSchema:
    """Tests for nested create schema generation."""

    def test_generates_nested_create_schema(self, nested_create_context: GeneratorContext) -> None:
        """Generates CreateNested schema when nested_create is set."""
        generator = SchemasGenerator(nested_create_context)
        files = generator.generate_files()

        order_schema = next(
            f for f in files if "order.py" in str(f.path) and "schemas" in str(f.path)
        )
        content = order_schema.content

        assert "class OrderCreateNested" in content
        assert "OrderCreate" in content

    def test_nested_schema_has_relationship_field(
        self, nested_create_context: GeneratorContext
    ) -> None:
        """Nested schema includes relationship field."""
        generator = SchemasGenerator(nested_create_context)
        files = generator.generate_files()

        order_schema = next(
            f for f in files if "order.py" in str(f.path) and "schemas" in str(f.path)
        )
        content = order_schema.content

        # Should have items field as list
        assert "items:" in content
        assert "list[OrderItemCreate]" in content

    def test_nested_schema_exported_in_init(self, nested_create_context: GeneratorContext) -> None:
        """Nested schema is exported in __init__.py."""
        generator = SchemasGenerator(nested_create_context)
        files = generator.generate_files()

        init_file = next(
            f for f in files if "__init__.py" in str(f.path) and "schemas" in str(f.path)
        )
        content = init_file.content

        assert "OrderCreateNested" in content


class TestNestedCreateService:
    """Tests for nested create service generation."""

    def test_generates_create_with_nested_method(
        self, nested_create_context: GeneratorContext
    ) -> None:
        """Generates create_with_nested method when nested_create is set."""
        generator = ServicesGenerator(nested_create_context)
        files = generator.generate_files()

        order_service = next(
            f for f in files if "order_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = order_service.content

        assert "async def create_with_nested(" in content
        assert "OrderCreateNested" in content

    def test_create_with_nested_creates_children(
        self, nested_create_context: GeneratorContext
    ) -> None:
        """create_with_nested method creates child entities."""
        generator = ServicesGenerator(nested_create_context)
        files = generator.generate_files()

        order_service = next(
            f for f in files if "order_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = order_service.content

        # Should iterate over items and create them
        assert "for child_data in data.items" in content
        assert "OrderItem" in content

    def test_model_without_nested_create_no_method(
        self, nested_create_context: GeneratorContext
    ) -> None:
        """Models without nested_create don't get create_with_nested."""
        generator = ServicesGenerator(nested_create_context)
        files = generator.generate_files()

        # OrderItem doesn't have nested_create
        item_service = next(
            f for f in files if "order_item_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = item_service.content

        assert "create_with_nested" not in content

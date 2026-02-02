"""Tests for bulk operations feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.graphql import GraphQLGenerator
from prisme.generators.backend.rest import RESTGenerator
from prisme.generators.backend.services import ServicesGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def bulk_ops_model() -> ModelSpec:
    """Create a model for bulk operations testing."""
    return ModelSpec(
        name="Product",
        soft_delete=True,
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="price", type=FieldType.DECIMAL, required=True),
            FieldSpec(name="active", type=FieldType.BOOLEAN, default=True),
        ],
    )


@pytest.fixture
def bulk_ops_stack(bulk_ops_model: ModelSpec) -> StackSpec:
    """Create a stack with bulk operations model."""
    return StackSpec(
        name="test-bulk-ops",
        version="1.0.0",
        models=[bulk_ops_model],
    )


@pytest.fixture
def bulk_ops_context(bulk_ops_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for bulk operations tests."""
    return GeneratorContext(
        domain_spec=bulk_ops_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-bulk-ops"),
    )


class TestBulkOperationsServiceBase:
    """Tests for bulk operations in ServiceBase."""

    def test_service_base_has_create_many(self, bulk_ops_context: GeneratorContext) -> None:
        """ServiceBase includes create_many method."""
        generator = ServicesGenerator(bulk_ops_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "_generated" in str(f.path) and "base.py" in str(f.path)
        )
        content = base_file.content

        assert "async def create_many(" in content
        assert "data: list[CreateSchemaT]" in content
        assert "list[ModelT]" in content

    def test_service_base_has_update_many(self, bulk_ops_context: GeneratorContext) -> None:
        """ServiceBase includes update_many method."""
        generator = ServicesGenerator(bulk_ops_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "_generated" in str(f.path) and "base.py" in str(f.path)
        )
        content = base_file.content

        assert "async def update_many(" in content
        assert "ids: list[int]" in content
        assert "data: UpdateSchemaT" in content

    def test_service_base_has_delete_many(self, bulk_ops_context: GeneratorContext) -> None:
        """ServiceBase includes delete_many method."""
        generator = ServicesGenerator(bulk_ops_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "_generated" in str(f.path) and "base.py" in str(f.path)
        )
        content = base_file.content

        assert "async def delete_many(" in content
        assert "ids: list[int]" in content
        assert "soft: bool = True" in content


class TestBulkOperationsREST:
    """Tests for bulk REST endpoints."""

    def test_rest_has_bulk_create_endpoint(self, bulk_ops_context: GeneratorContext) -> None:
        """REST router includes bulk create endpoint."""
        generator = RESTGenerator(bulk_ops_context)
        files = generator.generate_files()

        routes_file = next(
            f for f in files if "_generated" in str(f.path) and "product_routes" in str(f.path)
        )
        content = routes_file.content

        assert '@router.post(\n    "/bulk"' in content
        assert "bulk_create_products" in content
        assert "list[ProductCreate]" in content

    def test_rest_has_bulk_update_endpoint(self, bulk_ops_context: GeneratorContext) -> None:
        """REST router includes bulk update endpoint."""
        generator = RESTGenerator(bulk_ops_context)
        files = generator.generate_files()

        routes_file = next(
            f for f in files if "_generated" in str(f.path) and "product_routes" in str(f.path)
        )
        content = routes_file.content

        assert '@router.patch(\n    "/bulk"' in content
        assert "bulk_update_products" in content
        assert "update_many" in content

    def test_rest_has_bulk_delete_endpoint(self, bulk_ops_context: GeneratorContext) -> None:
        """REST router includes bulk delete endpoint."""
        generator = RESTGenerator(bulk_ops_context)
        files = generator.generate_files()

        routes_file = next(
            f for f in files if "_generated" in str(f.path) and "product_routes" in str(f.path)
        )
        content = routes_file.content

        assert '@router.delete(\n    "/bulk"' in content
        assert "bulk_delete_products" in content
        assert "delete_many" in content


class TestBulkOperationsGraphQL:
    """Tests for bulk GraphQL mutations."""

    def test_graphql_has_bulk_create_mutation(self, bulk_ops_context: GeneratorContext) -> None:
        """GraphQL includes bulk create mutation."""
        generator = GraphQLGenerator(bulk_ops_context)
        files = generator.generate_files()

        mutations_file = next(
            f for f in files if "mutations" in str(f.path) and "product" in str(f.path)
        )
        content = mutations_file.content

        assert "createProducts" in content
        assert "list[ProductInput]" in content
        assert "create_many" in content

    def test_graphql_has_bulk_update_mutation(self, bulk_ops_context: GeneratorContext) -> None:
        """GraphQL includes bulk update mutation."""
        generator = GraphQLGenerator(bulk_ops_context)
        files = generator.generate_files()

        mutations_file = next(
            f for f in files if "mutations" in str(f.path) and "product" in str(f.path)
        )
        content = mutations_file.content

        assert "updateProducts" in content
        assert "ids: list[int]" in content
        assert "update_many" in content

    def test_graphql_has_bulk_delete_mutation(self, bulk_ops_context: GeneratorContext) -> None:
        """GraphQL includes bulk delete mutation."""
        generator = GraphQLGenerator(bulk_ops_context)
        files = generator.generate_files()

        mutations_file = next(
            f for f in files if "mutations" in str(f.path) and "product" in str(f.path)
        )
        content = mutations_file.content

        assert "deleteProducts" in content
        assert "ids: list[int]" in content
        assert "delete_many" in content

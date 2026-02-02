"""Smoke tests for the services generator.

These tests verify that the ServicesGenerator produces valid, syntactically correct
Python code with the expected structure and methods.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.services import ServicesGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec, RelationshipSpec, TemporalConfig
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def basic_model() -> ModelSpec:
    """Create a basic model for smoke testing."""
    return ModelSpec(
        name="Customer",
        description="Customer entity",
        soft_delete=True,
        timestamps=True,
        fields=[
            FieldSpec(
                name="name",
                type=FieldType.STRING,
                max_length=255,
                required=True,
            ),
            FieldSpec(
                name="email",
                type=FieldType.STRING,
                max_length=255,
                required=True,
                unique=True,
            ),
            FieldSpec(
                name="status",
                type=FieldType.ENUM,
                enum_values=["active", "inactive"],
                default="active",
            ),
        ],
    )


@pytest.fixture
def model_with_relationships() -> list[ModelSpec]:
    """Create models with relationships."""
    return [
        ModelSpec(
            name="Order",
            fields=[
                FieldSpec(name="order_number", type=FieldType.STRING, required=True),
                FieldSpec(name="total", type=FieldType.DECIMAL, required=True),
                FieldSpec(
                    name="customer_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Customer",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="items",
                    target_model="OrderItem",
                    type="one_to_many",
                    back_populates="order",
                ),
            ],
            nested_create=["items"],
        ),
        ModelSpec(
            name="OrderItem",
            fields=[
                FieldSpec(name="product_name", type=FieldType.STRING, required=True),
                FieldSpec(name="quantity", type=FieldType.INTEGER, required=True),
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
def temporal_model() -> ModelSpec:
    """Create a model with temporal configuration."""
    return ModelSpec(
        name="PriceHistory",
        fields=[
            FieldSpec(name="symbol", type=FieldType.STRING, required=True),
            FieldSpec(name="price", type=FieldType.DECIMAL, required=True),
            FieldSpec(name="recorded_at", type=FieldType.DATETIME, required=True),
        ],
        temporal=TemporalConfig(
            timestamp_field="recorded_at",
            group_by_field="symbol",
            generate_latest_query=True,
            generate_history_query=True,
        ),
    )


@pytest.fixture
def basic_stack(basic_model: ModelSpec) -> StackSpec:
    """Create a basic stack for testing."""
    return StackSpec(
        name="test-smoke",
        version="1.0.0",
        models=[basic_model],
    )


@pytest.fixture
def full_stack(
    basic_model: ModelSpec,
    model_with_relationships: list[ModelSpec],
    temporal_model: ModelSpec,
) -> StackSpec:
    """Create a comprehensive stack for testing."""
    return StackSpec(
        name="test-full-smoke",
        version="1.0.0",
        models=[basic_model, *model_with_relationships, temporal_model],
    )


@pytest.fixture
def basic_context(basic_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for basic tests."""
    return GeneratorContext(
        domain_spec=basic_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-smoke"),
    )


@pytest.fixture
def full_context(full_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for full tests."""
    return GeneratorContext(
        domain_spec=full_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-full-smoke"),
    )


class TestServicesGeneratorSmoke:
    """Smoke tests for basic service generation."""

    def test_generates_files(self, basic_context: GeneratorContext) -> None:
        """Generator produces files."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        assert len(files) > 0

    def test_generates_base_service_file(self, basic_context: GeneratorContext) -> None:
        """Generator produces base.py with ServiceBase class."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            (f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)),
            None,
        )

        assert base_file is not None
        assert "class ServiceBase" in base_file.content
        assert "async def get(" in base_file.content
        assert "async def create(" in base_file.content
        assert "async def update(" in base_file.content
        assert "async def delete(" in base_file.content

    def test_generates_model_base_service(self, basic_context: GeneratorContext) -> None:
        """Generator produces base service for each model."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(
            (f for f in files if "customer_base.py" in str(f.path)),
            None,
        )

        assert customer_base is not None
        assert "class CustomerServiceBase" in customer_base.content
        assert "ServiceBase[Customer, CustomerCreate, CustomerUpdate]" in customer_base.content

    def test_generates_extension_service(self, basic_context: GeneratorContext) -> None:
        """Generator produces extension service for customization."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_ext = next(
            (f for f in files if f.path.name == "customer.py" and "_generated" not in str(f.path)),
            None,
        )

        assert customer_ext is not None
        assert "class CustomerService(CustomerServiceBase)" in customer_ext.content
        assert "YOUR CODE" in customer_ext.content

    def test_generates_init_files(self, basic_context: GeneratorContext) -> None:
        """Generator produces __init__.py files."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        init_files = [f for f in files if "__init__.py" in str(f.path)]

        assert len(init_files) >= 2  # services/ and services/_generated/


class TestServicesGeneratorValidPython:
    """Tests that generated code is valid Python syntax."""

    def test_base_service_valid_python(self, basic_context: GeneratorContext) -> None:
        """Base service file is valid Python."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        # Should parse without errors
        ast.parse(base_file.content)

    def test_model_base_service_valid_python(self, basic_context: GeneratorContext) -> None:
        """Model base service file is valid Python."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        # Should parse without errors
        ast.parse(customer_base.content)

    def test_extension_service_valid_python(self, basic_context: GeneratorContext) -> None:
        """Extension service file is valid Python."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_ext = next(
            f for f in files if f.path.name == "customer.py" and "_generated" not in str(f.path)
        )

        # Should parse without errors
        ast.parse(customer_ext.content)

    def test_all_generated_files_valid_python(self, full_context: GeneratorContext) -> None:
        """All generated Python files are valid syntax."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        python_files = [f for f in files if str(f.path).endswith(".py")]

        for file in python_files:
            try:
                ast.parse(file.content)
            except SyntaxError as e:
                pytest.fail(f"Invalid Python in {file.path}: {e}")


class TestServicesGeneratorCRUDMethods:
    """Tests for CRUD method generation."""

    def test_list_method_generated(self, basic_context: GeneratorContext) -> None:
        """Model service has list method with filters."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "async def list(" in customer_base.content
        assert "filters:" in customer_base.content
        assert "sort_by:" in customer_base.content
        assert "sort_order:" in customer_base.content

    def test_count_filtered_method_generated(self, basic_context: GeneratorContext) -> None:
        """Model service has count_filtered method."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "async def count_filtered(" in customer_base.content

    def test_apply_filters_method_generated(self, basic_context: GeneratorContext) -> None:
        """Model service has _apply_filters method."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "def _apply_filters(" in customer_base.content


class TestServicesGeneratorBulkOperations:
    """Tests for bulk operation generation."""

    def test_create_many_in_base_service(self, basic_context: GeneratorContext) -> None:
        """ServiceBase includes create_many method."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def create_many(" in base_file.content
        assert "list[CreateSchemaT]" in base_file.content

    def test_update_many_in_base_service(self, basic_context: GeneratorContext) -> None:
        """ServiceBase includes update_many method."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def update_many(" in base_file.content
        assert "ids: list[int]" in base_file.content

    def test_delete_many_in_base_service(self, basic_context: GeneratorContext) -> None:
        """ServiceBase includes delete_many method."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def delete_many(" in base_file.content


class TestServicesGeneratorLifecycleHooks:
    """Tests for lifecycle hook generation."""

    def test_lifecycle_hooks_in_base_service(self, basic_context: GeneratorContext) -> None:
        """ServiceBase includes all lifecycle hooks."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def before_create(" in base_file.content
        assert "async def after_create(" in base_file.content
        assert "async def before_update(" in base_file.content
        assert "async def after_update(" in base_file.content
        assert "async def before_delete(" in base_file.content
        assert "async def after_delete(" in base_file.content


class TestServicesGeneratorNestedCreate:
    """Tests for nested create functionality."""

    def test_nested_create_method_generated(self, full_context: GeneratorContext) -> None:
        """Models with nested_create have create_with_nested method."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        order_base = next(
            f for f in files if "order_base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def create_with_nested(" in order_base.content
        assert "OrderCreateNested" in order_base.content

    def test_nested_create_valid_python(self, full_context: GeneratorContext) -> None:
        """create_with_nested method is valid Python."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        order_base = next(
            f for f in files if "order_base.py" in str(f.path) and "_generated" in str(f.path)
        )

        # Should parse without errors
        ast.parse(order_base.content)


class TestServicesGeneratorTemporal:
    """Tests for temporal query generation."""

    def test_get_latest_generated(self, full_context: GeneratorContext) -> None:
        """Models with temporal config have get_latest method."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        price_history_base = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def get_latest(" in price_history_base.content

    def test_get_history_generated(self, full_context: GeneratorContext) -> None:
        """Models with temporal config have get_history method."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        price_history_base = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "async def get_history(" in price_history_base.content
        assert "start_date:" in price_history_base.content
        assert "end_date:" in price_history_base.content

    def test_temporal_methods_valid_python(self, full_context: GeneratorContext) -> None:
        """Temporal methods are valid Python."""
        generator = ServicesGenerator(full_context)
        files = generator.generate_files()

        price_history_base = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )

        # Should parse without errors
        ast.parse(price_history_base.content)


class TestServicesGeneratorSoftDelete:
    """Tests for soft delete support."""

    def test_soft_delete_in_get_method(self, basic_context: GeneratorContext) -> None:
        """Get method supports include_deleted parameter."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "include_deleted: bool = False" in base_file.content
        assert "deleted_at" in base_file.content

    def test_soft_delete_in_list_method(self, basic_context: GeneratorContext) -> None:
        """List method filters deleted records by default."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "include_deleted" in customer_base.content
        assert "deleted_at.is_(None)" in customer_base.content


class TestServicesGeneratorImports:
    """Tests for correct imports in generated code."""

    def test_base_service_imports(self, basic_context: GeneratorContext) -> None:
        """Base service has correct imports."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert "from sqlalchemy" in base_file.content
        assert "from pydantic import BaseModel" in base_file.content
        assert "AsyncSession" in base_file.content

    def test_model_service_imports(self, basic_context: GeneratorContext) -> None:
        """Model service imports model and schemas."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "from .base import ServiceBase" in customer_base.content
        # Imports now use package namespace (e.g., test_smoke.models.customer)
        assert ".models.customer import Customer" in customer_base.content
        assert ".schemas.customer import" in customer_base.content


class TestServicesGeneratorDocstrings:
    """Tests for documentation in generated code."""

    def test_base_service_has_docstrings(self, basic_context: GeneratorContext) -> None:
        """Base service class has docstrings."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        # Check for docstrings
        assert (
            '"""Base service class' in base_file.content
            or '"""Abstract base class' in base_file.content
        )
        assert "Args:" in base_file.content
        assert "Returns:" in base_file.content

    def test_model_service_has_docstrings(self, basic_context: GeneratorContext) -> None:
        """Model service methods have docstrings."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert '"""' in customer_base.content
        assert "Generated base service for Customer" in customer_base.content


class TestServicesGeneratorAllExports:
    """Tests for __all__ exports."""

    def test_base_service_exports(self, basic_context: GeneratorContext) -> None:
        """Base service file has __all__ export."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        base_file = next(
            f for f in files if "base.py" in str(f.path) and "_generated" in str(f.path)
        )

        assert '__all__ = ["ServiceBase", "ModelProtocol"]' in base_file.content

    def test_model_service_exports(self, basic_context: GeneratorContext) -> None:
        """Model service files have __all__ exports."""
        generator = ServicesGenerator(basic_context)
        files = generator.generate_files()

        customer_base = next(f for f in files if "customer_base.py" in str(f.path))

        assert "__all__" in customer_base.content
        assert "CustomerServiceBase" in customer_base.content

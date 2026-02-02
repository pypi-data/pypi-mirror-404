"""Tests for Prism specification models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from prisme.spec.exposure import (
    CRUDOperations,
    FrontendExposure,
    GraphQLExposure,
    MCPExposure,
    PaginationConfig,
    PaginationStyle,
    RESTExposure,
)
from prisme.spec.fields import FieldSpec, FieldType, FilterOperator
from prisme.spec.model import ModelSpec, RelationshipSpec
from prisme.spec.project import (
    DatabaseConfig,
    ExtensionConfig,
    GeneratorConfig,
    GraphQLConfig,
    TestingConfig,
    WidgetConfig,
)
from prisme.spec.stack import (
    FileStrategy,
    StackSpec,
)


class TestFieldType:
    """Tests for FieldType enum."""

    def test_all_field_types_exist(self) -> None:
        """Verify all expected field types are defined."""
        expected = [
            "string",
            "text",
            "integer",
            "float",
            "decimal",
            "boolean",
            "datetime",
            "date",
            "time",
            "uuid",
            "json",
            "enum",
            "foreign_key",
        ]
        actual = [ft.value for ft in FieldType]
        assert sorted(actual) == sorted(expected)


class TestFilterOperator:
    """Tests for FilterOperator enum."""

    def test_all_operators_exist(self) -> None:
        """Verify all expected filter operators are defined."""
        expected = [
            "eq",
            "ne",
            "gt",
            "gte",
            "lt",
            "lte",
            "like",
            "ilike",
            "in",
            "not_in",
            "is_null",
            "between",
            "contains",
            "starts_with",
            "ends_with",
        ]
        actual = [op.value for op in FilterOperator]
        assert sorted(actual) == sorted(expected)


class TestFieldSpec:
    """Tests for FieldSpec model."""

    def test_minimal_field_spec(self) -> None:
        """Create a minimal field spec with required fields only."""
        field = FieldSpec(name="id", type=FieldType.INTEGER)
        assert field.name == "id"
        assert field.type == FieldType.INTEGER
        assert field.required is True
        assert field.unique is False
        assert field.indexed is False

    def test_string_field_with_constraints(self) -> None:
        """Create a string field with validation constraints."""
        field = FieldSpec(
            name="username",
            type=FieldType.STRING,
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        )
        assert field.min_length == 3
        assert field.max_length == 50
        assert field.pattern is not None

    def test_enum_field(self) -> None:
        """Create an enum field with allowed values."""
        field = FieldSpec(
            name="status",
            type=FieldType.ENUM,
            enum_values=["pending", "active", "suspended"],
            default="pending",
        )
        assert field.enum_values == ["pending", "active", "suspended"]
        assert field.default == "pending"

    def test_foreign_key_field(self) -> None:
        """Create a foreign key field."""
        field = FieldSpec(
            name="customer_id",
            type=FieldType.FOREIGN_KEY,
            references="Customer",
            on_delete="CASCADE",
        )
        assert field.references == "Customer"
        assert field.on_delete == "CASCADE"

    def test_decimal_field(self) -> None:
        """Create a decimal field with precision and scale."""
        field = FieldSpec(
            name="price",
            type=FieldType.DECIMAL,
            precision=10,
            scale=2,
        )
        assert field.precision == 10
        assert field.scale == 2

    def test_ui_widget_configuration(self) -> None:
        """Create a field with UI widget configuration."""
        field = FieldSpec(
            name="address",
            type=FieldType.STRING,
            ui_widget="address",
            ui_widget_props={"enableMap": True, "country": "US"},
        )
        assert field.ui_widget == "address"
        assert field.ui_widget_props["enableMap"] is True

    def test_filter_operators(self) -> None:
        """Create a field with custom filter operators."""
        field = FieldSpec(
            name="name",
            type=FieldType.STRING,
            filter_operators=[
                FilterOperator.EQ,
                FilterOperator.ILIKE,
                FilterOperator.STARTS_WITH,
            ],
        )
        assert FilterOperator.ILIKE in field.filter_operators

    def test_field_spec_forbids_extra(self) -> None:
        """Verify extra fields are forbidden."""
        with pytest.raises(ValidationError):
            FieldSpec(
                name="test",
                type=FieldType.STRING,
                unknown_field="value",  # type: ignore[call-arg]
            )


class TestCRUDOperations:
    """Tests for CRUDOperations model."""

    def test_defaults_all_enabled(self) -> None:
        """All operations are enabled by default."""
        ops = CRUDOperations()
        assert ops.create is True
        assert ops.read is True
        assert ops.update is True
        assert ops.delete is True
        assert ops.list is True

    def test_read_only(self) -> None:
        """Create read-only operations."""
        ops = CRUDOperations(create=False, update=False, delete=False)
        assert ops.read is True
        assert ops.list is True
        assert ops.create is False


class TestPaginationConfig:
    """Tests for PaginationConfig model."""

    def test_defaults(self) -> None:
        """Verify default pagination settings."""
        config = PaginationConfig()
        assert config.style == PaginationStyle.OFFSET
        assert config.default_page_size == 20
        assert config.max_page_size == 100

    def test_cursor_pagination(self) -> None:
        """Create cursor-based pagination config."""
        config = PaginationConfig(
            style=PaginationStyle.CURSOR,
            default_page_size=25,
        )
        assert config.style == PaginationStyle.CURSOR


class TestRESTExposure:
    """Tests for RESTExposure model."""

    def test_defaults(self) -> None:
        """Verify default REST exposure settings."""
        exposure = RESTExposure()
        assert exposure.enabled is True
        assert exposure.auth_required is True
        assert exposure.tags == []

    def test_custom_configuration(self) -> None:
        """Create custom REST exposure configuration."""
        exposure = RESTExposure(
            enabled=True,
            prefix="/api/v2",
            tags=["customers"],
            create_fields=["name", "email"],
            permissions={"delete": ["admin"]},
        )
        assert exposure.prefix == "/api/v2"
        assert "customers" in exposure.tags


class TestGraphQLExposure:
    """Tests for GraphQLExposure model."""

    def test_defaults(self) -> None:
        """Verify default GraphQL exposure settings."""
        exposure = GraphQLExposure()
        assert exposure.enabled is True
        assert exposure.use_connection is True
        assert exposure.use_dataloader is True

    def test_subscriptions_enabled(self) -> None:
        """Create GraphQL exposure with subscriptions."""
        exposure = GraphQLExposure(
            enable_subscriptions=True,
            subscription_events=["created", "updated"],
        )
        assert exposure.enable_subscriptions is True
        assert "created" in exposure.subscription_events


class TestMCPExposure:
    """Tests for MCPExposure model."""

    def test_defaults(self) -> None:
        """Verify default MCP exposure settings."""
        exposure = MCPExposure()
        assert exposure.enabled is True
        assert exposure.expose_as_resource is False

    def test_tool_descriptions(self) -> None:
        """Create MCP exposure with tool descriptions."""
        exposure = MCPExposure(
            tool_prefix="customer",
            tool_descriptions={
                "list": "Search and list customers",
                "read": "Get customer by ID",
            },
        )
        assert exposure.tool_prefix == "customer"
        assert "list" in exposure.tool_descriptions


class TestFrontendExposure:
    """Tests for FrontendExposure model."""

    def test_defaults(self) -> None:
        """Verify default frontend exposure settings."""
        exposure = FrontendExposure()
        assert exposure.enabled is True
        assert exposure.api_style == "graphql"
        assert exposure.generate_form is True

    def test_navigation_config(self) -> None:
        """Create frontend exposure with navigation config."""
        exposure = FrontendExposure(
            include_in_nav=True,
            nav_label="Customers",
            nav_icon="users",
        )
        assert exposure.nav_label == "Customers"
        assert exposure.nav_icon == "users"


class TestRelationshipSpec:
    """Tests for RelationshipSpec model."""

    def test_one_to_many(self) -> None:
        """Create a one-to-many relationship."""
        rel = RelationshipSpec(
            name="orders",
            target_model="Order",
            type="one_to_many",
            back_populates="customer",
        )
        assert rel.name == "orders"
        assert rel.type == "one_to_many"
        assert rel.use_dataloader is True

    def test_many_to_many(self) -> None:
        """Create a many-to-many relationship."""
        rel = RelationshipSpec(
            name="tags",
            target_model="Tag",
            type="many_to_many",
            association_table="customer_tags",
        )
        assert rel.association_table == "customer_tags"


class TestModelSpec:
    """Tests for ModelSpec model."""

    def test_minimal_model(self) -> None:
        """Create a minimal model spec."""
        model = ModelSpec(
            name="User",
            fields=[
                FieldSpec(name="id", type=FieldType.INTEGER),
                FieldSpec(name="username", type=FieldType.STRING),
            ],
        )
        assert model.name == "User"
        assert len(model.fields) == 2
        assert model.timestamps is True  # default

    def test_model_with_all_options(self, sample_model_spec: ModelSpec) -> None:
        """Create a model spec with all options using fixture."""
        assert sample_model_spec.name == "Customer"
        assert sample_model_spec.soft_delete is True
        assert len(sample_model_spec.relationships) == 1


class TestFileStrategy:
    """Tests for FileStrategy enum."""

    def test_all_strategies_exist(self) -> None:
        """Verify all expected file strategies are defined."""
        expected = [
            "always_overwrite",
            "generate_once",
        ]
        actual = [fs.value for fs in FileStrategy]
        assert sorted(actual) == sorted(expected)


class TestExtensionConfig:
    """Tests for ExtensionConfig model."""

    def test_defaults(self) -> None:
        """Verify default extension configuration."""
        config = ExtensionConfig()
        assert config.use_protected_regions is True


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_defaults(self) -> None:
        """Verify default database configuration."""
        config = DatabaseConfig()
        assert config.engine == "postgresql"
        assert config.async_driver is True


class TestGraphQLConfig:
    """Tests for GraphQLConfig model."""

    def test_defaults(self) -> None:
        """Verify default GraphQL configuration."""
        config = GraphQLConfig()
        assert config.enabled is True
        assert config.path == "/graphql"
        assert config.graphiql is True


class TestWidgetConfig:
    """Tests for WidgetConfig model."""

    def test_defaults(self) -> None:
        """Verify default widget configuration."""
        config = WidgetConfig()
        assert config.type_widgets == {}
        assert config.ui_widgets == {}
        assert config.field_widgets == {}

    def test_custom_widgets(self) -> None:
        """Create custom widget configuration."""
        config = WidgetConfig(
            type_widgets={"string": "CustomTextInput"},
            field_widgets={"Customer.email": "EmailWidget"},
        )
        assert config.type_widgets["string"] == "CustomTextInput"


class TestGeneratorConfig:
    """Tests for GeneratorConfig model."""

    def test_defaults(self) -> None:
        """Verify default generator configuration."""
        config = GeneratorConfig()
        assert config.backend_output == "packages/backend/src"
        assert config.frontend_output == "packages/frontend/src"
        assert config.generate_migrations is True


class TestTestingConfig:
    """Tests for TestingConfig model."""

    def test_defaults(self) -> None:
        """Verify default testing configuration."""
        config = TestingConfig()
        assert config.generate_unit_tests is True
        assert config.generate_factories is True
        assert config.test_database == "sqlite"


class TestStackSpec:
    """Tests for StackSpec model."""

    def test_minimal_stack(self) -> None:
        """Create a minimal stack spec."""
        stack = StackSpec(
            name="my-project",
            models=[
                ModelSpec(
                    name="Item",
                    fields=[FieldSpec(name="name", type=FieldType.STRING)],
                ),
            ],
        )
        assert stack.name == "my-project"
        assert stack.version == "1.0.0"  # default
        assert len(stack.models) == 1

    def test_full_stack(self, sample_stack_spec: StackSpec) -> None:
        """Create a full stack spec using fixture."""
        assert sample_stack_spec.name == "test-project"
        assert len(sample_stack_spec.models) == 1

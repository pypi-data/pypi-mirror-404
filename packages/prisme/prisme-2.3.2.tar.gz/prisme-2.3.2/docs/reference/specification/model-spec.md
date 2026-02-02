# ModelSpec Reference

Defines a data model with fields, relationships, and exposure settings.

## Basic Usage

```python
from prism import ModelSpec, FieldSpec, FieldType

model = ModelSpec(
    name="Customer",
    fields=[
        FieldSpec(name="name", type=FieldType.STRING, required=True),
        FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
    ],
)
```

## Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Model name (PascalCase) |
| `fields` | `list[FieldSpec]` | List of field specifications |

### Optional Metadata

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `table_name` | `str` | snake_case of name | Database table name |
| `description` | `str` | `None` | Documentation |

### Relationships

| Parameter | Type | Description |
|-----------|------|-------------|
| `relationships` | `list[RelationshipSpec]` | Model relationships |

### Behaviors

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `soft_delete` | `bool` | `False` | Add `deleted_at` field |
| `timestamps` | `bool` | `False` | Add `created_at`, `updated_at` |

### Lifecycle Hooks

| Parameter | Type | Description |
|-----------|------|-------------|
| `before_create` | `str` | Function name to call before create |
| `after_create` | `str` | Function name to call after create |
| `before_update` | `str` | Function name to call before update |
| `after_update` | `str` | Function name to call after update |
| `before_delete` | `str` | Function name to call before delete |
| `after_delete` | `str` | Function name to call after delete |

### Testing

| Parameter | Type | Description |
|-----------|------|-------------|
| `test_factory` | `str` | Factory class name for tests |

### Advanced Features

| Parameter | Type | Description |
|-----------|------|-------------|
| `nested_create` | `list[str]` | Relationships supporting nested creation |
| `temporal` | `TemporalConfig` | Time-series query configuration |

### Exposure Settings

| Parameter | Type | Description |
|-----------|------|-------------|
| `rest` | `RESTExposure` | REST API settings |
| `graphql` | `GraphQLExposure` | GraphQL settings |
| `mcp` | `MCPExposure` | MCP tool settings |
| `frontend` | `FrontendExposure` | Frontend component settings |

## RelationshipSpec

```python
from prism import RelationshipSpec

relationship = RelationshipSpec(
    # Required
    name="orders",                    # Relationship field name
    target_model="Order",             # Target model name
    type="one_to_many",               # Relationship type

    # SQLAlchemy options
    back_populates="customer",        # Back-reference field
    lazy="select",                    # Loading strategy
    cascade="all, delete-orphan",     # Cascade behavior
    association_table="order_tags",   # For many-to-many

    # GraphQL options
    graphql_field_name="customerOrders",
    use_dataloader=True,
)
```

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `one_to_many` | One parent, many children | Customer -> Orders |
| `many_to_one` | Many children, one parent | Order -> Customer |
| `many_to_many` | Many to many | Order <-> Tags |
| `one_to_one` | Exclusive relationship | User -> Profile |

## TemporalConfig

For time-series data with specialized queries:

```python
from prism import TemporalConfig

temporal = TemporalConfig(
    timestamp_field="as_of_date",     # Timestamp field
    group_by_field="symbol",          # Grouping field
    generate_latest_query=True,       # Generate get_latest()
    generate_history_query=True,      # Generate get_history()
)
```

## Complete Example

```python
from prism import (
    ModelSpec, FieldSpec, FieldType, FilterOperator,
    RelationshipSpec,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
)

model = ModelSpec(
    name="Customer",
    table_name="customers",
    description="Customer entity in the CRM system",

    # Behaviors
    soft_delete=True,
    timestamps=True,

    # Fields
    fields=[
        FieldSpec(
            name="name",
            type=FieldType.STRING,
            max_length=255,
            required=True,
            searchable=True,
            filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
        ),
        FieldSpec(
            name="email",
            type=FieldType.STRING,
            max_length=255,
            required=True,
            unique=True,
            indexed=True,
            ui_widget="email",
        ),
        FieldSpec(
            name="status",
            type=FieldType.ENUM,
            enum_values=["active", "inactive", "prospect"],
            default="prospect",
        ),
    ],

    # Relationships
    relationships=[
        RelationshipSpec(
            name="orders",
            target_model="Order",
            type="one_to_many",
            back_populates="customer",
            cascade="all, delete-orphan",
        ),
    ],

    # Enable nested creation
    nested_create=["orders"],

    # Lifecycle hooks
    before_create="validate_customer",
    after_create="send_welcome_email",

    # Test factory
    test_factory="CustomerFactory",

    # Exposure
    rest=RESTExposure(enabled=True, tags=["customers"]),
    graphql=GraphQLExposure(enabled=True, use_connection=True),
    mcp=MCPExposure(enabled=True, tool_prefix="customer"),
    frontend=FrontendExposure(enabled=True, nav_label="Customers"),
)
```

## See Also

- [FieldSpec Reference](field-spec.md)
- [Exposure Config Reference](exposure-config.md)
- [StackSpec Reference](stack-spec.md)

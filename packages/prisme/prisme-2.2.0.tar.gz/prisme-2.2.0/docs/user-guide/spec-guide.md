# Prism Model Specification Guide

This guide provides comprehensive documentation for writing Prism model specifications. Specs are defined in Python using Pydantic models, making them type-safe, validatable, and IDE-friendly.

## Table of Contents

- [Quick Start](#quick-start)
- [StackSpec](#stackspec)
- [ModelSpec](#modelspec)
- [FieldSpec](#fieldspec)
- [RelationshipSpec](#relationshipspec)
- [Exposure Configuration](#exposure-configuration)
- [Advanced Features](#advanced-features)

---

## Quick Start

> **⚠️ Prerequisites:** Before using `prism generate`, ensure you have core backend files in place. These are automatically created by `prism create`. If setting up manually, see the [Getting Started guide](../getting-started/first-project.md) for required files.

Create a `specs/models.py` file in your project:

```python
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
)

stack = StackSpec(
    name="my-app",
    version="1.0.0",
    description="My Application",
    models=[
        ModelSpec(
            name="User",
            fields=[
                FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        ),
    ],
)
```

Then generate your code:

```bash
prism generate
```

---

## StackSpec

The root specification that defines your entire application.

```python
from prism import StackSpec, DatabaseConfig, GraphQLConfig, GeneratorConfig

stack = StackSpec(
    # Required
    name="my-app",                    # Project name (kebab-case)
    models=[...],                     # List of ModelSpec

    # Optional metadata
    version="1.0.0",                  # Semantic version
    title="My Application",           # Human-readable title (defaults to formatted name)
    description="App description",    # Project description

    # Configuration objects (all have sensible defaults)
    database=DatabaseConfig(...),
    graphql=GraphQLConfig(...),
    generator=GeneratorConfig(...),
    testing=TestingConfig(...),
    extensions=ExtensionConfig(...),
    widgets=WidgetConfig(...),

    # Global exposure defaults
    default_rest_exposure=RESTExposure(...),
    default_graphql_exposure=GraphQLExposure(...),
    default_mcp_exposure=MCPExposure(...),
    default_frontend_exposure=FrontendExposure(...),
)
```

### DatabaseConfig

```python
from prism import DatabaseConfig

database = DatabaseConfig(
    dialect="postgresql",       # "postgresql" or "sqlite"
    async_driver=True,          # Use async database driver
    naming_convention={...},    # SQLAlchemy naming conventions
)
```

### GraphQLConfig

```python
from prism import GraphQLConfig

graphql = GraphQLConfig(
    enabled=True,                    # Enable GraphQL endpoint
    path="/graphql",                 # GraphQL endpoint path
    graphiql=True,                   # Enable GraphiQL playground
    subscriptions_enabled=True,      # Enable subscriptions
    subscription_path="/graphql/ws", # WebSocket path
    query_depth_limit=10,            # Maximum query depth
    query_complexity_limit=100,      # Maximum query complexity
    enable_tracing=False,            # Apollo tracing
    enable_apollo_federation=False,  # Federation support
    dataloader_cache_per_request=True,
)
```

### GeneratorConfig

```python
from prism import GeneratorConfig

generator = GeneratorConfig(
    # Output paths
    backend_output="packages/backend/src",
    frontend_output="packages/frontend/src",

    # Backend structure
    models_path="models",
    schemas_path="schemas",
    services_path="services",
    services_generated_path="services/_generated",
    rest_path="api/rest",
    graphql_path="api/graphql",
    graphql_generated_path="api/graphql/_generated",
    mcp_path="mcp_server",
    tests_path="tests",

    # Frontend structure
    types_path="types",
    graphql_operations_path="graphql",
    api_client_path="api",
    components_path="components",
    components_generated_path="components/_generated",
    hooks_path="hooks",
    pages_path="pages",
    prism_path="prism",
    frontend_tests_path="__tests__",

    # Options
    generate_migrations=True,
    overwrite_existing=False,
    dry_run=False,
)
```

### TestingConfig

```python
from prism import TestingConfig

testing = TestingConfig(
    generate_unit_tests=True,
    generate_integration_tests=True,
    generate_factories=True,
    test_database="sqlite",          # "sqlite" or "postgresql"
    generate_graphql_tests=True,
    generate_component_tests=True,
    generate_hook_tests=True,
    generate_e2e_tests=False,
)
```

### ExtensionConfig

Controls how Prism handles file regeneration and customization.

```python
from prism import ExtensionConfig, FileStrategy

extensions = ExtensionConfig(
    # Backend strategies
    services_strategy=FileStrategy.GENERATE_BASE,
    graphql_types_strategy=FileStrategy.GENERATE_BASE,
    graphql_queries_strategy=FileStrategy.GENERATE_BASE,
    graphql_mutations_strategy=FileStrategy.GENERATE_BASE,
    rest_endpoints_strategy=FileStrategy.GENERATE_BASE,

    # Frontend strategies
    components_strategy=FileStrategy.GENERATE_BASE,
    hooks_strategy=FileStrategy.GENERATE_ONCE,
    pages_strategy=FileStrategy.GENERATE_ONCE,

    # Assembly strategies
    schema_assembly=FileStrategy.MERGE,
    router_assembly=FileStrategy.MERGE,

    # Protected regions
    use_protected_regions=True,
    protected_region_marker="PRISM:PROTECTED",
)
```

**FileStrategy options:**
- `ALWAYS_OVERWRITE` - Always regenerate (pure boilerplate)
- `GENERATE_ONCE` - Only create if doesn't exist
- `GENERATE_BASE` - Generate base files, user extends
- `MERGE` - Smart merge with conflict markers

### WidgetConfig

```python
from prism import WidgetConfig

widgets = WidgetConfig(
    # Override widgets by field type
    type_widgets={
        "string": "CustomTextInput",
        "date": "CustomDatePicker",
    },

    # Override widgets by ui_widget hint
    ui_widgets={
        "currency": "CurrencyInput",
        "address": "AddressAutocomplete",
    },

    # Override widgets by Model.field
    field_widgets={
        "Customer.email": "CustomerEmailWidget",
        "Order.total": "CurrencyInput",
    },
)
```

---

## ModelSpec

Defines a data model with its fields, relationships, and exposure settings.

```python
from prism import ModelSpec, FieldSpec, FieldType, RelationshipSpec

model = ModelSpec(
    # Required
    name="Customer",                  # Model name (PascalCase)
    fields=[...],                     # List of FieldSpec

    # Optional metadata
    table_name="customers",           # Database table name (defaults to snake_case)
    description="Customer entity",    # Documentation

    # Relationships
    relationships=[
        RelationshipSpec(
            name="orders",
            target_model="Order",
            type="one_to_many",
        ),
    ],

    # Common behaviors
    soft_delete=True,                 # Add deleted_at field
    timestamps=True,                  # Add created_at, updated_at

    # Lifecycle hooks (function names to call)
    before_create="validate_customer",
    after_create="send_welcome_email",
    before_update="check_permissions",
    after_update="notify_changes",
    before_delete="check_dependencies",
    after_delete="cleanup_resources",

    # Testing
    test_factory="CustomerFactory",   # Factory class name

    # Advanced features
    nested_create=["orders"],         # Enable nested creation for relationships
    temporal=TemporalConfig(...),     # Time-series queries

    # Exposure (override global defaults)
    rest=RESTExposure(...),
    graphql=GraphQLExposure(...),
    mcp=MCPExposure(...),
    frontend=FrontendExposure(...),
)
```

---

## FieldSpec

Defines a single field within a model.

### Basic Field Definition

```python
from prism import FieldSpec, FieldType

field = FieldSpec(
    # Required
    name="email",                     # Field name (snake_case)
    type=FieldType.STRING,            # Field type

    # Core options
    required=True,                    # Is the field required?
    unique=False,                     # Must values be unique?
    indexed=False,                    # Create database index?
    default=None,                     # Default value
    default_factory="uuid.uuid4",     # Factory function for default
)
```

### Field Types

```python
from prism import FieldType

# All available field types
FieldType.STRING      # Short text (varchar)
FieldType.TEXT        # Long text
FieldType.INTEGER     # Integer numbers
FieldType.FLOAT       # Floating point numbers
FieldType.DECIMAL     # Precise decimal numbers
FieldType.BOOLEAN     # True/False
FieldType.DATETIME    # Date and time
FieldType.DATE        # Date only
FieldType.TIME        # Time only
FieldType.UUID        # UUID identifier
FieldType.JSON        # JSON data
FieldType.ENUM        # Enumeration
FieldType.FOREIGN_KEY # Foreign key reference
```

### Type-Specific Options

#### Enum Fields

```python
FieldSpec(
    name="status",
    type=FieldType.ENUM,
    enum_values=["active", "inactive", "pending"],
    default="pending",
)
```

#### Decimal Fields

```python
FieldSpec(
    name="price",
    type=FieldType.DECIMAL,
    precision=10,                     # Total digits
    scale=2,                          # Decimal places
)
```

#### Foreign Key Fields

```python
FieldSpec(
    name="customer_id",
    type=FieldType.FOREIGN_KEY,
    references="Customer",            # Referenced model name
    on_delete="CASCADE",              # CASCADE, SET NULL, RESTRICT, etc.
)
```

#### JSON Fields with Typed Arrays

```python
# Generic JSON
FieldSpec(
    name="metadata",
    type=FieldType.JSON,
)

# Typed array - generates list[str] / string[]
FieldSpec(
    name="tags",
    type=FieldType.JSON,
    json_item_type="str",             # "str", "int", "float", "bool"
)
```

### Validation Constraints

```python
FieldSpec(
    name="username",
    type=FieldType.STRING,

    # String constraints
    min_length=3,
    max_length=50,
    pattern=r"^[a-zA-Z0-9_]+$",       # Regex pattern

    # Numeric constraints
    min_value=0,
    max_value=100,
)
```

### Filter Operators

Control which filter operators are available for list queries.

```python
from prism import FilterOperator

FieldSpec(
    name="name",
    type=FieldType.STRING,
    filterable=True,                  # Can be used in filters
    sortable=True,                    # Can be used for sorting
    searchable=True,                  # Include in full-text search

    filter_operators=[
        FilterOperator.EQ,            # Equals
        FilterOperator.NE,            # Not equals
        FilterOperator.GT,            # Greater than
        FilterOperator.GTE,           # Greater than or equal
        FilterOperator.LT,            # Less than
        FilterOperator.LTE,           # Less than or equal
        FilterOperator.LIKE,          # SQL LIKE (case-sensitive)
        FilterOperator.ILIKE,         # SQL ILIKE (case-insensitive)
        FilterOperator.IN,            # In list
        FilterOperator.NOT_IN,        # Not in list
        FilterOperator.IS_NULL,       # Is null
        FilterOperator.BETWEEN,       # Between two values
        FilterOperator.CONTAINS,      # Contains substring
        FilterOperator.STARTS_WITH,   # Starts with
        FilterOperator.ENDS_WITH,     # Ends with
    ],
)
```

### Display Settings

```python
FieldSpec(
    name="customer_name",
    type=FieldType.STRING,

    label="Customer Name",            # Human-readable label
    description="Full name",          # API documentation
    tooltip="Enter the full name",    # UI tooltip/help text
    hidden=False,                     # Hide from generated UIs
)
```

### UI Widget Configuration

```python
FieldSpec(
    name="email",
    type=FieldType.STRING,

    ui_widget="email",                # Widget type from registry
    ui_placeholder="name@example.com",# Placeholder text
    ui_widget_props={                 # Additional widget props
        "autocomplete": "email",
        "showValidation": True,
    },
)
```

**Available ui_widget values:**
- `textarea`, `richtext`, `markdown` - Text widgets
- `datepicker`, `datetimepicker`, `timepicker` - Date/time widgets
- `select`, `multiselect`, `radio` - Choice widgets
- `checkbox`, `switch` - Boolean widgets
- `slider`, `rating` - Numeric widgets
- `color` - Color picker
- `file`, `image` - File upload
- `password`, `email`, `url`, `phone` - Specialized inputs
- `currency`, `percentage` - Formatted numbers
- `tags` - Tag input
- `json`, `code` - Structured data

### Conditional Validation

```python
# Field required only when another field has specific value
FieldSpec(
    name="mining_license",
    type=FieldType.STRING,
    required=False,
    conditional_required="sector == mining",  # Required when sector is "mining"
)

# Enum values depend on another field
FieldSpec(
    name="job_title",
    type=FieldType.ENUM,
    enum_values=["manager", "engineer", "analyst"],
    conditional_enum={
        "sector:mining": ["gold_miner", "silver_miner"],
        "sector:tech": ["developer", "designer"],
    },
)
```

### GraphQL-Specific Settings

```python
FieldSpec(
    name="email",
    type=FieldType.STRING,
    graphql_type="EmailAddress",      # Override GraphQL type
    graphql_deprecation="Use emailAddress instead",  # Deprecation reason
)
```

---

## RelationshipSpec

Defines relationships between models.

```python
from prism import RelationshipSpec

relationship = RelationshipSpec(
    # Required
    name="orders",                    # Relationship field name
    target_model="Order",             # Target model name
    type="one_to_many",               # Relationship type

    # SQLAlchemy options
    back_populates="customer",        # Back-reference field
    lazy="select",                    # Lazy loading strategy
    cascade="all, delete-orphan",     # Cascade behavior
    association_table="order_tags",   # For many-to-many

    # GraphQL options
    graphql_field_name="customerOrders",  # Override field name
    use_dataloader=True,              # Use DataLoader for N+1 prevention
)
```

**Relationship types:**
- `one_to_many` - One parent, many children (e.g., Customer -> Orders)
- `many_to_one` - Many children, one parent (e.g., Order -> Customer)
- `many_to_many` - Many to many with association table
- `one_to_one` - Exclusive one-to-one relationship

---

## Exposure Configuration

Control how models are exposed through different interfaces.

### RESTExposure

```python
from prism import RESTExposure, CRUDOperations, PaginationConfig, PaginationStyle

rest = RESTExposure(
    enabled=True,                     # Enable REST endpoints

    # CRUD operations
    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=True,
        list=True,
    ),

    # URL configuration
    prefix="/api/v1",                 # URL prefix
    tags=["customers"],               # OpenAPI tags

    # Pagination
    pagination=PaginationConfig(
        style=PaginationStyle.OFFSET, # OFFSET, CURSOR, or LIMIT_OFFSET
        default_page_size=20,
        max_page_size=100,
    ),

    # Field visibility
    create_fields=["name", "email"],  # Fields allowed in create (None = all)
    update_fields=["name"],           # Fields allowed in update
    read_fields=None,                 # Fields in response (None = all)
    list_fields=["id", "name"],       # Fields in list response

    # Security
    auth_required=True,
    permissions={
        "create": ["admin", "manager"],
        "delete": ["admin"],
    },

    # OpenAPI customization
    operation_ids={
        "create": "createNewCustomer",
        "list": "listAllCustomers",
    },
)
```

### GraphQLExposure

```python
from prism import GraphQLExposure

graphql = GraphQLExposure(
    enabled=True,

    # Operations
    operations=CRUDOperations(...),

    # Type naming
    type_name="CustomerType",         # Override type name
    input_type_name="CustomerInput",
    query_name="customer",            # Single-item query
    query_list_name="customers",      # List query

    # Connections (pagination)
    use_connection=True,              # Relay-style connections
    connection_name="CustomerConnection",

    # Mutations
    mutation_prefix="customer",       # createCustomer, updateCustomer

    # Subscriptions
    enable_subscriptions=True,
    subscription_events=["created", "updated", "deleted"],

    # Field visibility
    query_fields=["id", "name", "email"],
    mutation_fields=["name", "email"],

    # Performance
    use_dataloader=True,
    max_depth=5,
    max_complexity=50,

    # Security
    auth_required=True,
    permissions={...},

    # Relationships
    nested_queries=True,              # Allow querying through relationships

    # Documentation
    type_description="A customer entity",
    field_descriptions={
        "email": "Primary contact email",
    },
)
```

### MCPExposure

Configure MCP (Model Context Protocol) tools for AI assistants.

```python
from prism import MCPExposure

mcp = MCPExposure(
    enabled=True,

    operations=CRUDOperations(...),

    # Tool naming
    tool_prefix="customer",           # customer_list, customer_read, etc.
    tool_descriptions={
        "list": "Search and list customers",
        "read": "Get customer details by ID",
        "create": "Create a new customer",
    },
    field_descriptions={
        "email": "Customer's primary email address",
    },

    # Resource exposure
    expose_as_resource=True,
    resource_uri_template="customer://{id}",
)
```

### FrontendExposure

```python
from prism import FrontendExposure

frontend = FrontendExposure(
    enabled=True,

    operations=CRUDOperations(...),

    # API configuration
    api_style="graphql",              # "graphql", "rest", or "both"
    graphql_client="urql",            # "urql" or "apollo"

    # Component generation
    generate_form=True,
    generate_table=True,
    generate_detail_view=True,

    # Layout
    form_layout="vertical",           # "vertical", "horizontal", "grid"
    table_columns=["id", "name", "email", "status"],

    # Navigation
    include_in_nav=True,
    nav_label="Customers",
    nav_icon="users",                 # Lucide icon name

    # Widget overrides (model-specific)
    widget_overrides={
        "email": "custom_email_widget",
    },
)
```

---

## Advanced Features

### Nested Create

Create parent and child entities in a single transaction.

```python
ModelSpec(
    name="Order",
    fields=[...],
    relationships=[
        RelationshipSpec(
            name="items",
            target_model="OrderItem",
            type="one_to_many",
        ),
    ],
    nested_create=["items"],          # Enable for 'items' relationship
)
```

This generates a `create_with_nested()` method in the service:

```python
await order_service.create_with_nested(
    data=OrderCreateNested(
        order_number="ORD-001",
        total=99.99,
        items=[
            OrderItemCreate(product_name="Widget", quantity=2, price=49.99),
        ],
    )
)
```

### Temporal/Time-Series Queries

Enable specialized queries for time-series data.

```python
from prism import TemporalConfig

ModelSpec(
    name="PriceHistory",
    fields=[
        FieldSpec(name="symbol", type=FieldType.STRING, required=True),
        FieldSpec(name="price", type=FieldType.DECIMAL, required=True),
        FieldSpec(name="as_of_date", type=FieldType.DATETIME, required=True),
    ],
    temporal=TemporalConfig(
        timestamp_field="as_of_date",     # Field containing timestamp
        group_by_field="symbol",          # Group for latest queries
        generate_latest_query=True,       # Generate get_latest()
        generate_history_query=True,      # Generate get_history()
    ),
)
```

Generated methods:

```python
# Get latest price for each symbol (or specific symbol)
latest = await service.get_latest(symbol="AAPL")

# Get price history with date range
history = await service.get_history(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    skip=0,
    limit=100,
)
```

### Soft Delete

Enable soft deletion with `deleted_at` timestamp.

```python
ModelSpec(
    name="Customer",
    fields=[...],
    soft_delete=True,                 # Adds deleted_at field
)
```

Service methods automatically filter deleted records:

```python
# Excludes soft-deleted by default
customers = await service.list()

# Include soft-deleted
all_customers = await service.list(include_deleted=True)
```

### Timestamps

Auto-generate `created_at` and `updated_at` fields.

```python
ModelSpec(
    name="Customer",
    fields=[...],
    timestamps=True,                  # Adds created_at, updated_at
)
```

---

## Complete Example

```python
"""Complete specification example."""
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RelationshipSpec, TemporalConfig,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
    CRUDOperations, PaginationConfig, PaginationStyle,
    DatabaseConfig, GraphQLConfig, GeneratorConfig, TestingConfig,
    ExtensionConfig, WidgetConfig, FileStrategy,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    description="Customer Relationship Management System",

    database=DatabaseConfig(dialect="postgresql"),
    graphql=GraphQLConfig(subscriptions_enabled=True),

    testing=TestingConfig(
        generate_unit_tests=True,
        generate_integration_tests=True,
        generate_graphql_tests=True,
    ),

    widgets=WidgetConfig(
        ui_widgets={"currency": "CurrencyInput"},
        field_widgets={"Customer.email": "CustomerEmailWidget"},
    ),

    models=[
        ModelSpec(
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
                    searchable=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
                    label="Customer Name",
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    indexed=True,
                    pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                    ui_widget="email",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["active", "inactive", "prospect"],
                    default="prospect",
                ),
                FieldSpec(
                    name="lifetime_value",
                    type=FieldType.DECIMAL,
                    precision=10,
                    scale=2,
                    default=0.0,
                    ui_widget="currency",
                    ui_widget_props={"currency": "USD"},
                ),
                FieldSpec(
                    name="tags",
                    type=FieldType.JSON,
                    json_item_type="str",
                    required=False,
                    ui_widget="tags",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="orders",
                    target_model="Order",
                    type="one_to_many",
                    back_populates="customer",
                ),
            ],
            nested_create=["orders"],
            rest=RESTExposure(
                enabled=True,
                tags=["customers"],
                pagination=PaginationConfig(
                    style=PaginationStyle.OFFSET,
                    default_page_size=25,
                ),
            ),
            graphql=GraphQLExposure(
                enabled=True,
                use_connection=True,
                enable_subscriptions=True,
            ),
            mcp=MCPExposure(
                enabled=True,
                tool_prefix="customer",
            ),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Customers",
                nav_icon="users",
            ),
        ),

        ModelSpec(
            name="Order",
            description="Customer order",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="customer_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Customer",
                    required=True,
                ),
                FieldSpec(
                    name="order_number",
                    type=FieldType.STRING,
                    max_length=50,
                    required=True,
                    unique=True,
                ),
                FieldSpec(
                    name="total",
                    type=FieldType.DECIMAL,
                    precision=10,
                    scale=2,
                    required=True,
                    ui_widget="currency",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["pending", "paid", "shipped", "delivered"],
                    default="pending",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="customer",
                    target_model="Customer",
                    type="many_to_one",
                    back_populates="orders",
                ),
            ],
        ),
    ],
)
```

---

## Next Steps

- Run `prism validate specs/models.py` to check your specification
- Run `prism generate --dry-run` to preview generated files
- Run `prism generate` to generate all code
- Run `prism dev` to start development servers

For more examples, see the [Building a CRM tutorial](../tutorials/building-a-crm.md).

# StackSpec Reference

The root specification that defines your entire application.

## Basic Usage

```python
from prism import StackSpec, ModelSpec

stack = StackSpec(
    name="my-app",
    version="1.0.0",
    description="My Application",
    models=[
        ModelSpec(name="User", fields=[...]),
    ],
)
```

## Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Project name (kebab-case recommended) |
| `models` | `list[ModelSpec]` | List of model specifications |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | `str` | `"0.1.0"` | Semantic version |
| `title` | `str` | Formatted name | Human-readable title |
| `description` | `str` | `None` | Project description |

### Configuration Objects

| Parameter | Type | Description |
|-----------|------|-------------|
| `database` | `DatabaseConfig` | Database settings |
| `graphql` | `GraphQLConfig` | GraphQL endpoint settings |
| `generator` | `GeneratorConfig` | Code generation settings |
| `testing` | `TestingConfig` | Test generation settings |
| `extensions` | `ExtensionConfig` | File generation strategies |
| `widgets` | `WidgetConfig` | Frontend widget overrides |

### Default Exposure

| Parameter | Type | Description |
|-----------|------|-------------|
| `default_rest_exposure` | `RESTExposure` | Default REST settings for all models |
| `default_graphql_exposure` | `GraphQLExposure` | Default GraphQL settings |
| `default_mcp_exposure` | `MCPExposure` | Default MCP settings |
| `default_frontend_exposure` | `FrontendExposure` | Default frontend settings |

## DatabaseConfig

```python
from prism import DatabaseConfig

database = DatabaseConfig(
    dialect="postgresql",      # "postgresql" or "sqlite"
    async_driver=True,         # Use async database driver
    naming_convention={        # SQLAlchemy naming conventions
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)
```

## GraphQLConfig

```python
from prism import GraphQLConfig

graphql = GraphQLConfig(
    enabled=True,                    # Enable GraphQL endpoint
    path="/graphql",                 # Endpoint path
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

## GeneratorConfig

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

## TestingConfig

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

## ExtensionConfig

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

## WidgetConfig

```python
from prism import WidgetConfig

widgets = WidgetConfig(
    # Override by field type
    type_widgets={
        "string": "CustomTextInput",
        "date": "CustomDatePicker",
    },

    # Override by ui_widget hint
    ui_widgets={
        "currency": "CurrencyInput",
        "phone": "PhoneInput",
    },

    # Override by Model.field
    field_widgets={
        "Customer.email": "CustomerEmailWidget",
        "Order.total": "CurrencyInput",
    },
)
```

## Complete Example

```python
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType,
    RESTExposure, GraphQLExposure,
    DatabaseConfig, GraphQLConfig, GeneratorConfig,
    TestingConfig, ExtensionConfig, WidgetConfig,
    FileStrategy,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    title="My CRM Application",
    description="Customer Relationship Management System",

    database=DatabaseConfig(
        dialect="postgresql",
        async_driver=True,
    ),

    graphql=GraphQLConfig(
        enabled=True,
        subscriptions_enabled=True,
        query_depth_limit=10,
    ),

    generator=GeneratorConfig(
        backend_output="packages/backend/src",
        frontend_output="packages/frontend/src",
    ),

    testing=TestingConfig(
        generate_unit_tests=True,
        generate_integration_tests=True,
    ),

    extensions=ExtensionConfig(
        services_strategy=FileStrategy.GENERATE_BASE,
        components_strategy=FileStrategy.GENERATE_BASE,
    ),

    widgets=WidgetConfig(
        ui_widgets={
            "currency": "CurrencyInput",
        },
    ),

    # Global exposure defaults
    default_rest_exposure=RESTExposure(enabled=True),
    default_graphql_exposure=GraphQLExposure(enabled=True),

    models=[
        ModelSpec(
            name="Customer",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
                FieldSpec(name="email", type=FieldType.STRING, required=True),
            ],
        ),
    ],
)
```

## See Also

- [ModelSpec Reference](model-spec.md)
- [FieldSpec Reference](field-spec.md)
- [Exposure Config Reference](exposure-config.md)

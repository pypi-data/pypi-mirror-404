# Exposure Config Reference

Configure how models are exposed through REST, GraphQL, MCP, and Frontend interfaces.

## Overview

Each model can have independent exposure settings:

```python
ModelSpec(
    name="Customer",
    fields=[...],
    rest=RESTExposure(enabled=True),
    graphql=GraphQLExposure(enabled=True),
    mcp=MCPExposure(enabled=True),
    frontend=FrontendExposure(enabled=True),
)
```

## CRUDOperations

Shared configuration for which operations to enable:

```python
from prism import CRUDOperations

operations = CRUDOperations(
    create=True,
    read=True,
    update=True,
    delete=True,
    list=True,
)
```

## RESTExposure

Configure REST API endpoints.

```python
from prism import RESTExposure, CRUDOperations, PaginationConfig, PaginationStyle

rest = RESTExposure(
    enabled=True,

    # CRUD operations
    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=True,
        list=True,
    ),

    # URL configuration
    prefix="/api/v1",
    tags=["customers"],

    # Pagination
    pagination=PaginationConfig(
        style=PaginationStyle.OFFSET,  # OFFSET, CURSOR, LIMIT_OFFSET
        default_page_size=20,
        max_page_size=100,
    ),

    # Field visibility
    create_fields=["name", "email"],  # Fields allowed in create
    update_fields=["name"],           # Fields allowed in update
    read_fields=None,                 # Fields in response (None = all)
    list_fields=["id", "name"],       # Fields in list response

    # Security
    auth_required=True,
    permissions={
        "create": ["admin", "manager"],
        "read": ["user", "admin"],
        "update": ["admin", "manager"],
        "delete": ["admin"],
        "list": ["user", "admin"],
    },

    # OpenAPI customization
    operation_ids={
        "create": "createNewCustomer",
        "read": "getCustomer",
        "update": "updateCustomer",
        "delete": "deleteCustomer",
        "list": "listAllCustomers",
    },
)
```

### Pagination Styles

| Style | Description | URL Example |
|-------|-------------|-------------|
| `OFFSET` | Page-based | `?page=2&page_size=20` |
| `CURSOR` | Cursor-based | `?cursor=abc123&limit=20` |
| `LIMIT_OFFSET` | Skip/take | `?skip=40&limit=20` |

## GraphQLExposure

Configure GraphQL types, queries, and mutations.

```python
from prism import GraphQLExposure, CRUDOperations

graphql = GraphQLExposure(
    enabled=True,

    # Operations
    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=True,
        list=True,
    ),

    # Type naming
    type_name="CustomerType",
    input_type_name="CustomerInput",
    query_name="customer",
    query_list_name="customers",

    # Connections (Relay-style pagination)
    use_connection=True,
    connection_name="CustomerConnection",

    # Mutations
    mutation_prefix="customer",  # createCustomer, updateCustomer

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
    permissions={
        "query": ["user"],
        "mutation": ["admin"],
    },

    # Relationships
    nested_queries=True,

    # Documentation
    type_description="A customer in the CRM system",
    field_descriptions={
        "email": "Primary contact email address",
        "status": "Current customer lifecycle stage",
    },
)
```

### Generated GraphQL Operations

With the above configuration, Prisme generates:

**Queries:**
```graphql
query {
  customer(id: 1) { ... }
  customers(first: 10, after: "cursor") { edges { node { ... } } }
}
```

**Mutations:**
```graphql
mutation {
  createCustomer(input: { ... }) { ... }
  updateCustomer(id: 1, input: { ... }) { ... }
  deleteCustomer(id: 1)
}
```

**Subscriptions:**
```graphql
subscription {
  customerCreated { ... }
  customerUpdated { ... }
  customerDeleted { id }
}
```

## MCPExposure

Configure MCP (Model Context Protocol) tools for AI assistants.

```python
from prism import MCPExposure, CRUDOperations

mcp = MCPExposure(
    enabled=True,

    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=False,  # Disable destructive operations
        list=True,
    ),

    # Tool naming
    tool_prefix="customer",  # customer_list, customer_read, etc.

    # Tool documentation
    tool_descriptions={
        "list": "Search and list customers with optional filters",
        "read": "Get detailed customer information by ID",
        "create": "Create a new customer record",
        "update": "Update an existing customer's information",
    },

    # Field documentation
    field_descriptions={
        "name": "Customer's full name",
        "email": "Primary email address",
        "status": "Customer status: lead, prospect, customer, or churned",
    },

    # Resource exposure (for MCP resources)
    expose_as_resource=True,
    resource_uri_template="customer://{id}",
)
```

### Generated MCP Tools

With `tool_prefix="customer"`:

| Tool | Description |
|------|-------------|
| `customer_list` | Search and list customers |
| `customer_read` | Get customer by ID |
| `customer_create` | Create new customer |
| `customer_update` | Update existing customer |

## FrontendExposure

Configure frontend component generation.

```python
from prism import FrontendExposure, CRUDOperations

frontend = FrontendExposure(
    enabled=True,

    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=True,
        list=True,
    ),

    # API configuration
    api_style="graphql",  # "graphql", "rest", or "both"
    graphql_client="urql",  # "urql" or "apollo"

    # Component generation
    generate_form=True,
    generate_table=True,
    generate_detail_view=True,

    # Layout
    form_layout="vertical",  # "vertical", "horizontal", "grid"
    table_columns=["id", "name", "email", "status"],

    # Navigation
    include_in_nav=True,
    nav_label="Customers",
    nav_icon="users",  # Lucide icon name

    # Widget overrides
    widget_overrides={
        "email": "custom_email_widget",
        "phone": "phone_input",
    },
)
```

### Generated Components

| Component | File | Description |
|-----------|------|-------------|
| Form | `CustomerForm.tsx` | Create/edit form |
| Table | `CustomerTable.tsx` | List table with sorting/filtering |
| Detail | `CustomerDetail.tsx` | Single record view |
| Page | `CustomersPage.tsx` | Page component |

## Default Exposure

Set defaults at the StackSpec level:

```python
StackSpec(
    name="my-app",
    default_rest_exposure=RESTExposure(
        enabled=True,
        pagination=PaginationConfig(default_page_size=25),
    ),
    default_graphql_exposure=GraphQLExposure(
        enabled=True,
        use_connection=True,
    ),
    default_mcp_exposure=MCPExposure(enabled=False),
    default_frontend_exposure=FrontendExposure(enabled=True),
    models=[
        # Models inherit defaults unless overridden
        ModelSpec(
            name="Customer",
            fields=[...],
            # This model uses defaults
        ),
        ModelSpec(
            name="InternalLog",
            fields=[...],
            # Override to disable frontend
            frontend=FrontendExposure(enabled=False),
        ),
    ],
)
```

## Disabling Specific Operations

Disable individual operations while keeping others:

```python
# Read-only API
RESTExposure(
    enabled=True,
    operations=CRUDOperations(
        create=False,
        read=True,
        update=False,
        delete=False,
        list=True,
    ),
)

# No delete in frontend
FrontendExposure(
    enabled=True,
    operations=CRUDOperations(delete=False),
)
```

## Complete Example

```python
from prism import (
    ModelSpec, FieldSpec, FieldType,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
    CRUDOperations, PaginationConfig, PaginationStyle,
)

ModelSpec(
    name="Customer",
    fields=[
        FieldSpec(name="name", type=FieldType.STRING, required=True),
        FieldSpec(name="email", type=FieldType.STRING, required=True),
        FieldSpec(name="status", type=FieldType.ENUM, enum_values=["active", "inactive"]),
    ],

    # Full REST API with pagination
    rest=RESTExposure(
        enabled=True,
        tags=["customers"],
        pagination=PaginationConfig(
            style=PaginationStyle.OFFSET,
            default_page_size=25,
        ),
        auth_required=True,
    ),

    # GraphQL with subscriptions
    graphql=GraphQLExposure(
        enabled=True,
        use_connection=True,
        enable_subscriptions=True,
        use_dataloader=True,
    ),

    # MCP tools for AI
    mcp=MCPExposure(
        enabled=True,
        tool_prefix="customer",
        tool_descriptions={
            "list": "Search customers by name or email",
            "read": "Get customer details",
        },
    ),

    # Frontend with custom navigation
    frontend=FrontendExposure(
        enabled=True,
        nav_label="Customers",
        nav_icon="users",
        table_columns=["name", "email", "status"],
    ),
)
```

## See Also

- [ModelSpec Reference](model-spec.md)
- [FieldSpec Reference](field-spec.md)
- [StackSpec Reference](stack-spec.md)

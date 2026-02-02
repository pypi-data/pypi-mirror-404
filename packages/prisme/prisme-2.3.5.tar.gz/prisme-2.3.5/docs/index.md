# Prisme

**"One spec, full spectrum."**

Prisme is a code generation framework that enables defining data models once in Python/Pydantic and generating consistent CRUD operations, list endpoints (with filtering, sorting, pagination), and UI components across the entire stack—without losing your customizations on regeneration.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Get up and running with Prisme in under 5 minutes

    [:octicons-arrow-right-24: Getting Started](getting-started/quickstart.md)

-   :material-code-braces:{ .lg .middle } **Spec as Code**

    ---

    Define your entire application using Python and Pydantic models

    [:octicons-arrow-right-24: Model Specification](user-guide/spec-guide.md)

-   :material-api:{ .lg .middle } **Full-Stack Generation**

    ---

    Generate REST, GraphQL, MCP APIs, and React components automatically

    [:octicons-arrow-right-24: Code Generation](user-guide/code-generation.md)

-   :material-tools:{ .lg .middle } **CLI Reference**

    ---

    Explore all available commands and options

    [:octicons-arrow-right-24: CLI Documentation](user-guide/cli-reference.md)

</div>

## Features

- **Spec as Code**: Define all specifications in Python using Pydantic models
- **Code-First**: Models are the source of truth; everything else is generated
- **Selective Exposure**: Fine-grained control over REST, GraphQL, MCP, and Frontend exposure
- **Build-Time Generation**: Static, inspectable output generated at build time
- **Type Safety**: End-to-end type safety from database to frontend
- **Extend, Don't Overwrite**: Downstream customizations preserved across regenerations
- **Pluggable Widgets**: Default widgets with dependency injection for customization

## Technology Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL / SQLite |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic |
| REST API | FastAPI |
| GraphQL | Strawberry GraphQL |
| MCP | FastMCP |
| Frontend | Vite + React + TypeScript + Tailwind |
| Testing | pytest (backend) / Vitest (frontend) |

## Installation

=== "uv (recommended)"

    ```bash
    uv add prisme
    ```

=== "pip"

    ```bash
    pip install prisme
    ```

## Quick Example

**One command** to create, install, generate, test, and start development:

```bash
prism create my-app && cd my-app && prism install && prism generate && prism test && prism dev
```

### Define Your Models

```python title="specs/models.py"
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    description="Customer Relationship Management System",
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
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    ui_widget="email",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["active", "inactive", "prospect"],
                    default="prospect",
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["customers"]),
            graphql=GraphQLExposure(enabled=True, use_connection=True),
            mcp=MCPExposure(enabled=True, tool_prefix="customer"),
            frontend=FrontendExposure(enabled=True, nav_label="Customers"),
        ),
    ],
)
```

### Generate Everything

```bash
prism generate
```

This generates:

- **Backend**: SQLAlchemy models, Pydantic schemas, service layer, REST endpoints, GraphQL types/queries/mutations, MCP tools
- **Frontend**: TypeScript types, React components, hooks, GraphQL operations
- **Testing**: Unit tests, integration tests, component tests

## Next Steps

<div class="grid cards" markdown>

-   [:octicons-arrow-right-24: Installation Guide](getting-started/installation.md)
-   [:octicons-arrow-right-24: Quick Start Tutorial](getting-started/quickstart.md)
-   [:octicons-arrow-right-24: Model Specification Guide](user-guide/spec-guide.md)
-   [:octicons-arrow-right-24: CLI Reference](user-guide/cli-reference.md)

</div>

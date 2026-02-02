# Prisme for AI Agents

Instructions for AI assistants working with Prisme projects.

## Overview

Prisme is a code generation framework that creates full-stack applications from Python specifications. This page provides context for AI assistants (like Claude) working with Prisme projects.

## Recognizing Prisme Projects

A Prisme project typically has:

```
project/
├── prism.config.py           # Prisme configuration
├── specs/
│   └── models.py             # Model specifications
├── packages/
│   ├── backend/              # Python/FastAPI backend
│   └── frontend/             # React/TypeScript frontend
```

Key indicators:
- `prism.config.py` or `specs/models.py` files
- Imports from `prism` package
- `StackSpec`, `ModelSpec`, `FieldSpec` classes

## Understanding the Specification

### StackSpec

Root configuration containing all models:

```python
stack = StackSpec(
    name="my-app",
    models=[...],
    database=DatabaseConfig(...),
    graphql=GraphQLConfig(...),
)
```

### ModelSpec

Defines a data model:

```python
ModelSpec(
    name="Customer",
    fields=[
        FieldSpec(name="email", type=FieldType.STRING, required=True),
    ],
    rest=RESTExposure(enabled=True),
    graphql=GraphQLExposure(enabled=True),
)
```

### Field Types

- `STRING`, `TEXT`: Text data
- `INTEGER`, `FLOAT`, `DECIMAL`: Numbers
- `BOOLEAN`: True/False
- `DATETIME`, `DATE`, `TIME`: Temporal
- `UUID`: Unique identifiers
- `JSON`: Structured data
- `ENUM`: Enumerated values
- `FOREIGN_KEY`: Relationships

## Common Tasks

### Adding a New Model

1. Edit `specs/models.py`
2. Add a new `ModelSpec` to the `models` list
3. Run `prism generate`

```python
# In specs/models.py
ModelSpec(
    name="NewModel",
    fields=[
        FieldSpec(name="name", type=FieldType.STRING, required=True),
    ],
    rest=RESTExposure(enabled=True),
    graphql=GraphQLExposure(enabled=True),
    frontend=FrontendExposure(enabled=True),
)
```

### Adding a Field

1. Find the model in `specs/models.py`
2. Add a `FieldSpec` to the `fields` list
3. Run `prism generate`
4. Run `prism db migrate` if database changes needed

### Modifying Generated Code

**Safe to modify:**
- `services/<model>_service.py` (user extension files)
- `components/<Model>Form.tsx` (user extension files)
- Any file NOT in `_generated/` directories

**Do NOT modify:**
- `services/_generated/*.py`
- `components/_generated/*.tsx`
- `schemas/*.py`
- `types/*.ts`

These are regenerated and changes will be lost.

### Custom Business Logic

Extend the generated service:

```python
# services/customer_service.py
from ._generated.customer_service import CustomerServiceBase

class CustomerService(CustomerServiceBase):
    async def custom_method(self, id: int):
        """Add custom business logic here."""
        customer = await self.read(id)
        # Custom logic
        return customer
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `prism create <name>` | Create new project |
| `prism generate` | Generate code from spec |
| `prism generate --dry-run` | Preview changes |
| `prism install` | Install dependencies |
| `prism dev` | Start dev servers |
| `prism test` | Run tests |
| `prism db migrate` | Run database migrations |
| `prism validate` | Validate spec file |

## File Organization

### Backend Structure

```
packages/backend/src/<package>/
├── models/              # SQLAlchemy models
│   ├── base.py          # Base model class
│   └── customer.py      # Generated model
├── schemas/             # Pydantic schemas (generated)
├── services/            # Business logic
│   ├── _generated/      # Generated base classes
│   └── customer_service.py  # User extensions
├── api/
│   ├── rest/            # REST endpoints
│   └── graphql/         # GraphQL types
└── mcp_server/          # MCP tools
```

### Frontend Structure

```
packages/frontend/src/
├── types/               # TypeScript types (generated)
├── components/          # React components
│   ├── _generated/      # Generated base components
│   └── CustomerForm.tsx # User extensions
├── hooks/               # React hooks
├── pages/               # Page components
└── graphql/             # GraphQL operations
```

## Working with MCP

Prisme generates MCP tools for AI assistant integration:

- Tools are in `mcp_server/tools/`
- Each model gets CRUD tools: `<model>_list`, `<model>_read`, `<model>_create`, `<model>_update`
- Tool names are prefixed with `tool_prefix` from `MCPExposure`

## Best Practices for AI Assistants

### When Modifying Specs

1. Read the existing spec first
2. Follow existing patterns
3. Use appropriate field types
4. Configure exposure settings
5. Remind user to run `prism generate`

### When Modifying Code

1. Check if file is in `_generated/` directory
2. If generated, modify the user extension file instead
3. Follow the extension pattern (inherit from base class)
4. Add custom methods, don't override generated ones unless necessary

### When Debugging

1. Check that `prism generate` has been run after spec changes
2. Verify database migrations are applied
3. Check for type errors in generated schemas
4. Review service layer for custom logic issues

## Common Patterns

### Adding Validation

```python
# In services/customer_service.py
class CustomerService(CustomerServiceBase):
    async def create(self, data: CustomerCreate) -> Customer:
        # Custom validation
        if not self._is_valid_email(data.email):
            raise ValueError("Invalid email")
        # Call parent
        return await super().create(data)
```

### Adding Relationships

```python
# In specs/models.py
ModelSpec(
    name="Order",
    fields=[
        FieldSpec(
            name="customer_id",
            type=FieldType.FOREIGN_KEY,
            references="Customer",
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
)
```

### Adding Custom API Endpoints

```python
# In api/rest/customers.py (after generated router)
@router.post("/{id}/activate")
async def activate_customer(
    id: int,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.activate(id)
```

## Documentation Links

- [Installation Guide](/getting-started/installation/)
- [Model Specification Guide](/user-guide/spec-guide/)
- [CLI Reference](/user-guide/cli-reference/)
- [Extensibility Guide](/user-guide/extensibility/)
- [MCP Integration Tutorial](/tutorials/mcp-integration/)

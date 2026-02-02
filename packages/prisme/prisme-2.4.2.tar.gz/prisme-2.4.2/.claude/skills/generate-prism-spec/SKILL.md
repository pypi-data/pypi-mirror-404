---
name: generate-prism-spec
description: Generate a Prism StackSpec (specs/models.py) from a natural-language description of models, fields, and relationships. Use when the user wants to create or scaffold a new Prism specification.
argument-hint: "[description of the app and its models]"
---

Generate a Prism `StackSpec` in `specs/models.py` based on the user's description.

## Steps

1. **Clarify requirements** — ask about models, fields, relationships, auth, and exposure needs if the description is ambiguous.
2. **Write the spec** — produce a valid `specs/models.py` using only imports from `prism.spec`.
3. **Validate** — run `uv run prism validate` to confirm the spec is valid.
4. **Generate (if asked)** — run `uv run prism generate --dry-run` to preview, then `uv run prism generate` to write files.

## Template

```python
from prism.spec import (
    StackSpec,
    ModelSpec,
    FieldSpec,
    FieldType,
    RelationshipSpec,
    RESTExposure,
    GraphQLExposure,
    FrontendExposure,
    MCPExposure,
)

stack = StackSpec(
    name="my-app",
    version="1.0.0",
    description="...",
    models=[
        # ModelSpec entries here
    ],
)
```

## Quick Reference

### FieldType values

`STRING`, `TEXT`, `INTEGER`, `FLOAT`, `DECIMAL`, `BOOLEAN`, `DATETIME`, `DATE`, `TIME`, `UUID`, `JSON`, `ENUM`, `FOREIGN_KEY`

### FieldSpec — common options

```python
FieldSpec(
    name="email",
    type=FieldType.STRING,
    required=True,          # default: True
    unique=False,           # default: False
    indexed=False,          # default: False
    default=None,           # static default
    default_factory=None,   # e.g. "uuid.uuid4"
    # String constraints
    min_length=None,
    max_length=None,
    pattern=None,           # regex
    # Numeric constraints
    min_value=None,
    max_value=None,
    # Decimal
    precision=None,
    scale=None,
    # Enum
    enum_values=None,       # e.g. ["draft", "published"]
    # Foreign key
    references=None,        # target model name
    on_delete="CASCADE",    # CASCADE, SET NULL, RESTRICT
    # JSON typed arrays
    json_item_type=None,    # "str", "int", "float"
    # List/filter behavior
    filterable=True,
    sortable=True,
    searchable=False,       # full-text search
    # Display
    label=None,
    description=None,
    hidden=False,           # hide from generated UIs
    # Frontend widget
    ui_widget=None,
    ui_placeholder=None,
    ui_widget_props=None,
)
```

### RelationshipSpec

```python
RelationshipSpec(
    name="posts",
    target_model="Post",
    type="one_to_many",     # one_to_many | many_to_one | many_to_many | one_to_one
    back_populates="author",
    optional=False,         # nullable FK (many_to_one)
    cascade="all, delete-orphan",
    use_dataloader=True,
)
```

### ModelSpec — common options

```python
ModelSpec(
    name="Post",
    description=None,
    table_name=None,        # defaults to snake_case
    fields=[...],
    relationships=[],
    timestamps=True,        # created_at, updated_at
    soft_delete=False,      # deleted_at
    nested_create=None,     # e.g. ["comments"]
    # Lifecycle hooks (function name strings)
    before_create=None, after_create=None,
    before_update=None, after_update=None,
    before_delete=None, after_delete=None,
    # Exposure (each has enabled=True/False + CRUDOperations)
    rest=RESTExposure(...),
    graphql=GraphQLExposure(...),
    frontend=FrontendExposure(...),
    mcp=MCPExposure(...),
)
```

### Exposure highlights

All exposures share `enabled: bool` and `operations: CRUDOperations(create, read, update, delete, list)`.

- **RESTExposure** — `create_fields`, `update_fields`, `read_fields`, `list_fields` to control field visibility per operation; `auth_required`, `permissions`
- **GraphQLExposure** — `enable_subscriptions`, `subscription_events`, `use_connection` (Relay), `query_fields`, `mutation_fields`
- **FrontendExposure** — `generate_form`, `generate_table`, `generate_detail_view`, `nav_label`, `nav_icon`, `form_layout` ("vertical"/"horizontal"/"grid")
- **MCPExposure** — `tool_prefix`, `tool_descriptions`, `expose_as_resource`

For the full spec API with all options, see [reference.md](reference.md).

## Rules

- Always import from `prism.spec`, never from internal submodules.
- Use PascalCase for model names, snake_case for field names.
- Every foreign key field needs a corresponding `RelationshipSpec` on both sides.
- Set `hidden=True` on sensitive fields like `password_hash`.
- If auth is needed, add `AuthConfig` with a `User` model containing at minimum: the username field, `password_hash` (hidden), `is_active`, and `roles`.
- Prefer `soft_delete=True` for user-facing models.
- Run `uv run prism validate` after writing the spec to catch errors early.

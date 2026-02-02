# Issue: No Built-in Extension Point for Custom GraphQL Mutations

**Status**: Deferred
**Priority**: Medium
**Type**: Feature Request
**Created**: 2026-01-25

## Problem

The `schema.py` file is auto-generated and marked "DO NOT EDIT", but there's no mechanism to add custom mutations (like admin operations) without modifying it.

This makes it impossible to:
- Add custom business logic mutations
- Create admin-only operations
- Extend the schema without risk of losing changes on regeneration

## Impact

- Users must create workaround files that may break on updates
- No clear pattern for extending generated schemas
- Custom mutations require knowledge of internal structure

## Proposed Solution

Prism should provide one of:

### Option 1: Extension Template (Recommended)
Generate a `custom_schema.py` template that imports and extends the generated schema:
```python
# custom_schema.py (user-editable, not overwritten)
from .schema import Query, Mutation

class CustomMutation(Mutation):
    # Add custom mutations here
    pass

class CustomQuery(Query):
    # Add custom queries here
    pass
```

### Option 2: Hook System
Provide a registration system for custom mutations/queries:
```python
# In spec or separate config
custom_mutations = [
    "app.mutations.AdminMutations",
    "app.mutations.ReportMutations",
]
```

### Option 3: Directory Structure
Use a `_generated/` vs `custom/` directory structure:
```
graphql/
├── _generated/    # Auto-generated, overwritten
│   └── schema.py
└── custom/        # User-editable, preserved
    └── mutations.py
```

## Workaround

1. Create `custom_mutations.py` with custom mutation classes
2. Create `custom_schema.py` that extends the generated schema:
```python
from .schema import Query, Mutation as GeneratedMutation

class Mutation(GeneratedMutation):
    admin_reset = AdminMutation.Field()
    # ... other custom mutations

schema = strawberry.Schema(query=Query, mutation=Mutation)
```
3. Modify `main.py` to import from `custom_schema` instead of `schema`

## Resolution

**Deferred**: 2026-01-25

This is a feature request that requires architectural decisions about extension patterns. The workaround documented above is functional and allows users to extend generated schemas.

Recommended approach for future implementation: Option 1 (Extension Template) as it provides a clear pattern for users while keeping generated code separate.

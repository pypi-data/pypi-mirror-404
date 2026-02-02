# Issue: Async SQLAlchemy Relationships Not Loaded in Generated Services

**Status**: Resolved
**Priority**: High
**Created**: 2026-01-26

## Problem

The generated `*_from_model()` functions in GraphQL types expect relationships to be loaded via `obj.__dict__.get('relationship_name')`, but the generated `ServiceBase.get()` and `list()` methods don't eagerly load relationships. In SQLAlchemy async, lazy loading doesn't work the same way as sync, so relationship data is never fetched.

This caused:
1. Relationship fields returning `None` or empty lists in GraphQL responses
2. M2M relationship methods (`add_*`, `remove_*`, `set_*`) failing when accessing relationship collections

## Impact

- Users querying nested relationships via GraphQL receive empty/null data
- M2M relationship mutations fail with lazy loading errors
- Users must manually override service methods to add `selectinload()` calls

## Proposed Solution

Add optional `load_relationships` parameter to service methods that uses `selectinload()` to eagerly load specified relationships.

## Resolution

Fixed in commit `eed3679` - Added `load_relationships: list[str] | None = None` parameter to:

1. **`ServiceBase.get()`** - [base.py.jinja2:39-69](../../../src/prism/templates/jinja2/backend/services/base.py.jinja2)
2. **`ServiceBase.get_multi()`** - [base.py.jinja2:71-104](../../../src/prism/templates/jinja2/backend/services/base.py.jinja2)
3. **`*ServiceBase.list()`** - [service_base.py.jinja2:35-87](../../../src/prism/templates/jinja2/backend/services/service_base.py.jinja2)

Also fixed M2M methods to eagerly load relationships before accessing collections:
- `add_*()`, `remove_*()`, `set_*()` now use `load_relationships=["rel_name"]`

### Usage

```python
# Get a single record with relationships loaded
project = await service.get(id, load_relationships=["sites", "tags"])

# List records with relationships loaded
projects = await service.list(load_relationships=["sites"])
```

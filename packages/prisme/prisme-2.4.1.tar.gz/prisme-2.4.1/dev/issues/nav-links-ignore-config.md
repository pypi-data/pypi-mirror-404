# Issue: Nav links generated despite include_in_nav=False

**Status**: Resolved
**Priority**: High
**Created**: 2026-01-26

## Problem

When `include_in_nav=False` is set in `FrontendExposure`, the nav link is still generated in the router's sidebar navigation.

Example spec configuration:
```python
frontend=FrontendExposure(
    enabled=True,
    include_in_nav=False,
    generate_form=False,
    generate_table=True,
    generate_detail_view=False,
),
```

## Impact

Models that should be hidden from navigation (e.g., association tables, internal data models) still appear in the sidebar, cluttering the UI and confusing users.

## Proposed Solution

Modify the router/navigation generator to respect the `include_in_nav` flag when building the navigation structure.

## Resolution

Fixed in router.py by adding a check for `include_in_nav` flag before generating navigation links:
```python
if not model.frontend.include_in_nav:
    continue
```

Models with `include_in_nav=False` are now correctly skipped when building the sidebar navigation.

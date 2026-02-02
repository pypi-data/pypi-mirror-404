# Issue: Router generates routes for pages that don't exist

**Status**: Resolved
**Priority**: High
**Created**: 2026-01-26

## Problem

When a model has `generate_detail_view=False` and `generate_form=False` in its `FrontendExposure` config, the router generator still creates imports and routes for these non-existent pages.

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

Generated code includes imports for files that don't exist:
```tsx
// These imports are generated but files don't exist
import WindRoseSectorDetailPage from './pages/wind-rose-sectors/[id]';
import WindRoseSectorCreatePage from './pages/wind-rose-sectors/new';
import WindRoseSectorEditPage from './pages/wind-rose-sectors/[id]/edit';
```

## Impact

Vite fails to build with error:
```
Failed to resolve import "./pages/wind-rose-sectors/[id]" from "src/router.tsx". Does the file exist?
```

This blocks development and requires manual removal of the invalid imports/routes.

## Proposed Solution

Modify the router generator to check `FrontendExposure` config before generating routes:
- Only generate detail route if `generate_detail_view=True`
- Only generate create/edit routes if `generate_form=True`
- Conditionally generate imports based on which pages are actually generated

## Resolution

Fixed in router.py by adding checks for `generate_detail_view` and `generate_form` flags:
- Detail route only generated when `ops.read and has_detail`
- Create route only generated when `ops.create and has_form`
- Edit route only generated when `ops.update and has_form`

This aligns router generation with the existing logic in PagesGenerator.

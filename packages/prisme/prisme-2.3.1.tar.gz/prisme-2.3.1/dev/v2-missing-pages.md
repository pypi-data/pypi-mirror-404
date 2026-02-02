# v2 Missing Pages

Tracking frontend pages that prisme does not yet generate but should for a complete v2 experience.

## Search / Filter Page

- No dedicated search page is generated
- Headless composables exist (`useFiltering`, `useSearch`) but no pre-built page wires them up
- Each list page should support inline filtering; a global search page would add cross-model search

## User Profile / Settings Page

- No profile or account settings page for authenticated users
- Should allow: display name edit, password change, email update, MFA enrollment
- Only relevant when `auth.enabled == True`

## Error Pages

- No 404 or generic error pages are generated
- Errors are handled inline but there are no fallback route pages
- Should generate: 404 Not Found, 403 Forbidden, 500 generic error

## Bulk Operations UI

- `useSelection` hook exists but no UI for bulk actions
- Missing: bulk delete, bulk export, bulk status change
- Should be opt-in per model via frontend overrides

## Export / Import Pages

- `export.ts` utility exists in headless composables but no page uses it
- No CSV/JSON import page or upload UI
- Should support at minimum: CSV export from list view, CSV import page

## Relationship Browser

- Related records shown inline in detail views but no dedicated browsing
- For many-to-many and one-to-many relations, a sub-page or tab for managing related records would be useful

## Admin Enhancements

- Admin dashboard is minimal (user count only)
- Missing: role management page, permission management page, activity/audit log page
- Current admin pages: Dashboard, Users, User Detail, Whitelist

## Data Visualization / Dashboard

- No analytics or chart pages for model data
- Could generate a simple dashboard with record counts, recent activity, etc.

---

## Priority

| Page | Priority | Depends On |
|------|----------|------------|
| Error Pages (404/403/500) | High | — |
| User Profile / Settings | High | auth.enabled |
| Search / Filter | Medium | headless composables |
| Export from List View | Medium | export.ts |
| Bulk Operations UI | Medium | useSelection |
| Import Page | Low | — |
| Relationship Browser | Low | — |
| Admin Enhancements | Low | admin_panel.enabled |
| Data Visualization | Low | — |

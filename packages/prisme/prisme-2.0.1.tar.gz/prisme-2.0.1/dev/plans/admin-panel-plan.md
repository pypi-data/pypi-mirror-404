# Plan: Admin Panel & User Access Control

**Status**: Complete (PR #63)
**Author**: Prism Core Team
**Created**: 2026-01-30
**Updated**: 2026-01-30
**Priority**: HIGH
**Roadmap Reference**: New Priority 19

## Overview

Generate admin-level pages within Prism apps for managing the application environment. The initial scope focuses on **authentication administration**: user whitelisting (email, domain, regex), admin promotion, and first-admin bootstrapping. The admin panel is a generated React frontend section with corresponding backend APIs, protected by the existing `require_roles("admin")` infrastructure.

## Goals

- Generate an `/admin` section in the frontend with role-gated access
- Provide user management: list, activate/deactivate, promote/demote, delete
- Implement signup whitelisting: restrict who can register via email addresses, email domains, and regex patterns
- Provide a secure bootstrap mechanism for the first admin user
- Fit naturally into Prism's existing auth system (JWT preset, roles, `require_roles`)

## Non-Goals

- Full CMS or content management system
- Replacing Authentik for enterprise deployments (this is for the built-in JWT auth preset)
- Multi-tenancy or organization management (future extension)
- Audit logging (future extension, tracked separately)

## Design

### 1. Specification Extensions

```yaml
# specs/models.py - AuthConfig additions
auth:
  enabled: true
  preset: jwt

  # NEW: Admin panel configuration
  admin_panel:
    enabled: true                    # Generate admin pages and APIs
    path: "/admin"                   # Frontend route prefix

  # NEW: Signup access control
  signup_access:
    mode: open                       # open | whitelist | invite_only
    whitelist:
      emails: []                     # Exact email addresses
      domains: []                    # e.g., ["company.com", "partner.org"]
      patterns: []                   # Regex patterns, e.g. [".*@.*\\.edu"]
    # invite_only: invite codes required (future)
```

**Python spec model additions** (in `src/prism/spec/auth.py`):

```python
class SignupWhitelist(BaseModel):
    emails: list[str] = []
    domains: list[str] = []
    patterns: list[str] = []

class SignupAccessConfig(BaseModel):
    mode: Literal["open", "whitelist", "invite_only"] = "open"
    whitelist: SignupWhitelist = SignupWhitelist()

class AdminPanelConfig(BaseModel):
    enabled: bool = False
    path: str = "/admin"

# Add to AuthConfig:
class AuthConfig(BaseModel):
    # ... existing fields ...
    admin_panel: AdminPanelConfig = AdminPanelConfig()
    signup_access: SignupAccessConfig = SignupAccessConfig()
```

### 2. Backend: Admin API Endpoints

All endpoints require `admin` role via `require_roles("admin")`.

```
# User Management
GET    /api/admin/users              # List users (paginated, searchable)
GET    /api/admin/users/:id          # Get user detail
PATCH  /api/admin/users/:id          # Update user (roles, is_active)
DELETE /api/admin/users/:id          # Soft-delete user
POST   /api/admin/users/:id/promote  # Add admin role
POST   /api/admin/users/:id/demote   # Remove admin role

# Whitelist Management (runtime-editable)
GET    /api/admin/whitelist           # Get current whitelist rules
PUT    /api/admin/whitelist           # Replace whitelist rules
POST   /api/admin/whitelist/test      # Test an email against current rules
```

**Whitelist storage**: A `signup_whitelist` table with columns:
- `id` (UUID)
- `rule_type` (enum: email, domain, pattern)
- `value` (string)
- `created_by` (FK to user)
- `created_at` (timestamp)

This allows runtime editing without redeployment. The initial values from the spec seed the table on first migration.

### 3. Backend: Signup Validation

The existing signup endpoint (`POST /api/auth/signup`) gains a validation step:

```python
async def validate_signup_access(email: str, db: AsyncSession) -> bool:
    """Check if email is allowed to sign up based on whitelist rules."""
    config = await get_signup_access_config(db)

    if config.mode == "open":
        return True

    if config.mode == "whitelist":
        rules = await get_whitelist_rules(db)
        for rule in rules:
            match rule.rule_type:
                case "email":
                    if email.lower() == rule.value.lower():
                        return True
                case "domain":
                    if email.lower().endswith(f"@{rule.value.lower()}"):
                        return True
                case "pattern":
                    if re.fullmatch(rule.value, email, re.IGNORECASE):
                        return True
        return False

    return False  # invite_only: reject unless invite code provided
```

**Security**: Regex patterns are validated on creation (compiled with `re.compile()` to catch syntax errors, and execution is time-limited to prevent ReDoS).

### 4. Frontend: Admin Pages

Generated React pages under `/admin` route, protected by `ProtectedRoute` with `roles={["admin"]}`:

```
/admin                      # Dashboard: user count, recent signups, whitelist status
/admin/users                # User table: search, filter by role/status, sort
/admin/users/:id            # User detail: edit roles, activate/deactivate
/admin/whitelist            # Whitelist editor: add/remove rules, test email input
```

**Components generated**:
- `pages/admin/AdminDashboard.tsx` - Overview cards
- `pages/admin/AdminUsers.tsx` - User list with Prism's headless UI (pagination, search, sorting)
- `pages/admin/AdminUserDetail.tsx` - Edit user roles and status
- `pages/admin/AdminWhitelist.tsx` - CRUD for whitelist rules with test feature
- `components/admin/AdminLayout.tsx` - Sidebar nav for admin section
- `components/admin/RoleBadge.tsx` - Visual role indicator

**Navigation**: An "Admin" link appears in the main sidebar/nav only when `user.roles.includes("admin")`.

### 5. First Admin Bootstrap

This is the critical question. After reviewing common approaches:

| Approach | Used By | Pros | Cons |
|----------|---------|------|------|
| CLI command creates admin | Django, Rails | Secure, explicit, auditable | Requires shell access |
| Env var `ADMIN_EMAIL` + first login auto-promotes | Supabase, some SaaS | Works in containerized deploys | Env var persists after use |
| First registered user is admin | Simple apps | Zero config | Race condition, insecure |
| Bootstrap token in URL | Grafana | No shell needed | Token management |

**Recommended approach: CLI command + env var fallback**

#### Primary: CLI Command

```bash
# During initial setup (requires shell access to the container/server)
prism admin bootstrap --email admin@example.com

# This creates the user with:
# - email: admin@example.com
# - roles: ["admin"]
# - is_active: true
# - password: null (must use password reset flow to set password)
# - bootstrap_token: <random UUID> (one-time login link)
```

The command outputs a one-time bootstrap URL:
```
Admin user created: admin@example.com
Set your password at: https://app.example.com/auth/bootstrap/<token>
This link expires in 24 hours.
```

The bootstrap endpoint allows setting the initial password without knowing a previous one. The token is single-use and time-limited.

#### Fallback: Environment Variable

For containerized/serverless environments where CLI access isn't available at startup:

```env
# .env
ADMIN_BOOTSTRAP_EMAIL=admin@example.com
```

On application startup, if this env var is set and no admin user exists:
1. Create user with `roles: ["admin"]`, `is_active: true`, `password: null`
2. Log the bootstrap URL to stdout
3. The env var is consumed (the app ignores it if an admin already exists)

This matches how Authentik (`AUTHENTIK_BOOTSTRAP_EMAIL`/`AUTHENTIK_BOOTSTRAP_PASSWORD`) and Grafana (`GF_SECURITY_ADMIN_USER`) handle it.

#### Bootstrap Flow (Frontend)

```
/auth/bootstrap/:token  →  BootstrapPage.tsx
```

Shows a "Set your password" form. On submit:
1. Validates the bootstrap token
2. Sets the password
3. Invalidates the token
4. Redirects to login

### 6. Generated Code Summary

When `auth.admin_panel.enabled: true`, Prism generates:

**Backend** (new templates):
- `api/rest/admin.py` - Admin API routes
- `services/admin_service.py` - User management + whitelist logic
- `models/signup_whitelist.py` - Whitelist SQLAlchemy model
- `schemas/admin.py` - Pydantic schemas for admin APIs
- `services/bootstrap_service.py` - Bootstrap token logic
- `api/rest/bootstrap.py` - Bootstrap endpoint

**Frontend** (new templates):
- `pages/admin/AdminDashboard.tsx`
- `pages/admin/AdminUsers.tsx`
- `pages/admin/AdminUserDetail.tsx`
- `pages/admin/AdminWhitelist.tsx`
- `components/admin/AdminLayout.tsx`
- `components/admin/RoleBadge.tsx`
- `pages/auth/BootstrapPage.tsx`

**Migrations**:
- `signup_whitelist` table
- `bootstrap_token` and `bootstrap_token_expires` columns on user model

**Modified templates**:
- Auth signup route: add whitelist validation step
- Frontend router: add `/admin/*` routes
- Frontend nav: add conditional admin link
- App startup: add bootstrap check from env var

### 7. Interaction with Authentik (Priority 12)

When `auth.provider: authentik` is used instead of `jwt`, the admin panel adapts:
- User management reads from the local synced user table (read-only for Authentik-managed fields)
- Role changes are pushed to Authentik groups via API
- Whitelist rules are enforced at the Authentik enrollment flow level (via policies)
- Bootstrap uses Authentik's built-in `AUTHENTIK_BOOTSTRAP_EMAIL`

This plan focuses on the **JWT preset** implementation. Authentik adaptation is deferred to Priority 12.

## Implementation Steps

1. [x] Extend `AuthConfig` spec model with `admin_panel` and `signup_access` fields
2. [x] Create `SignupWhitelist` SQLAlchemy model and migration template
3. [x] Generate admin API routes (user management + whitelist CRUD)
4. [x] Add whitelist validation to signup route template
5. [x] Implement bootstrap service (CLI command + token generation)
6. [x] Generate frontend admin pages (dashboard, users, whitelist)
7. [x] Generate bootstrap page (`/bootstrap?token=...`)
8. [x] Add admin nav link (conditional on role) to layout template
9. [x] Add `prism admin bootstrap` CLI command
10. [ ] Seed whitelist table from spec config on first migration (deferred)
11. [x] Write unit tests for spec models, backend generator, frontend generator (20 tests)
12. [ ] Write integration tests for admin APIs (deferred — needs running app)
13. [ ] Write E2E tests for admin panel and bootstrap flow (deferred — needs running app)
14. [x] Update documentation

## Testing Strategy

1. **Unit Tests**: Whitelist matching logic (email, domain, regex, ReDoS protection)
2. **Unit Tests**: Bootstrap token generation, validation, expiry
3. **Integration Tests**: Admin API endpoints with role enforcement
4. **Integration Tests**: Signup rejection when not whitelisted
5. **E2E Tests**: Full bootstrap flow (CLI → set password → login → admin panel)
6. **E2E Tests**: Add whitelist rule → test email → signup attempt

## Rollout Plan

1. Release as opt-in via `auth.admin_panel.enabled: true` in spec
2. Default `signup_access.mode: open` preserves current behavior
3. `prism admin bootstrap` added to CLI
4. Document in getting-started guide as recommended post-setup step

## Security Considerations

- All admin endpoints behind `require_roles("admin")`
- Bootstrap tokens are single-use, time-limited (24h), and stored hashed
- Regex patterns validated and execution time-limited to prevent ReDoS
- Whitelist `test` endpoint is admin-only (no information leakage)
- Soft-delete for users (preserve audit trail)
- Admin cannot demote themselves (prevent lockout)

## Open Questions

- Should there be a "super admin" role that cannot be demoted by other admins?
- Should whitelist rules support comments/labels for organization?
- Should we generate an audit log for admin actions from the start, or defer?
- Should the admin panel include app settings management beyond auth (e.g., feature flags)?

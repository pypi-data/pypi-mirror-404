# Prism Generator Feature List (v1 Baseline)

**Referenced by:** [PRD-v2-refactor.md](PRD-v2-refactor.md)
**Date:** 2026-01-31
**Purpose:** Complete inventory of what Prism v1 generators produce, to inform v2 scope and ensure nothing is lost in the refactor.

---

## 1. Data Models

**Generator:** `ModelsGenerator` (`generators/backend/models.py`)

| Feature | Details |
|---|---|
| SQLAlchemy ORM models | Full type annotations, metadata, Base class |
| Field types | string, text, int, float, decimal, boolean, datetime, date, time, UUID, JSON, enum, foreign key |
| Relationships | one-to-one, one-to-many, many-to-one, many-to-many (with association tables) |
| Mixins | `TimestampMixin` (created_at/updated_at), `SoftDeleteMixin` (deleted_at) |
| Constraints | unique, indexed, nullable, default values |
| Cascades | Configurable cascade behavior, lazy loading strategies |
| Typed JSON arrays | `json_item_type` for typed JSON fields |
| Enum types | Table-specific enum naming |
| Auto FK columns | Auto-generated foreign key columns for many-to-one |
| `__init__.py` exports | Model index with all exports |

---

## 2. Pydantic Schemas

**Generator:** `SchemasGenerator` (`generators/backend/schemas.py`)

| Feature | Details |
|---|---|
| Base schemas | Per-model base schema |
| Create schemas | Optional fields for defaults |
| Update schemas | All fields optional |
| Read schemas | Includes ID, timestamps, relationships |
| Filter schemas | Per-field with operator support (eq, ne, gt, lt, gte, lte, like, ilike, contains, in, between) |
| Nested create schemas | Create parent + children in one request |
| Conditional validators | `conditional_required`, `conditional_enum` |
| Field validation | min_length, max_length, min_value, max_value, pattern |
| Enum → Literal | Enum fields as Python Literal types |
| Relationship filters | Filter by FK ID, multiple IDs |
| Timestamp filters | created_after, created_before |
| Soft delete filters | include_deleted flag |

---

## 3. Service Layer (CRUD)

**Generator:** `ServicesGenerator` (`generators/backend/services.py`)

| Feature | Details |
|---|---|
| Base service class | Abstract `ServiceBase` with full CRUD |
| create | Single entity creation |
| get | Get by ID |
| get_multi | List with pagination, sorting, filtering |
| update | Partial update |
| delete | Hard or soft delete |
| Extension services | User-customizable via `GENERATE_ONCE` strategy |
| M2M management | add/remove related entities |
| Nested create | Create with related entities in single transaction |
| Temporal queries | `get_latest()`, `get_history()` (date-range) for time-series models |
| Pagination | Offset-based with configurable page size |
| Sorting | Multi-field sorting |

---

## 4. REST API

**Generator:** `RESTGenerator` (`generators/backend/rest.py`)

| Feature | Details |
|---|---|
| FastAPI routers | Base + extension pattern |
| `GET /models` | List with pagination, sorting, filtering |
| `GET /models/{id}` | Get single record |
| `POST /models` | Create |
| `PATCH /models/{id}` | Update |
| `DELETE /models/{id}` | Delete (hard or soft) |
| `POST /models/{id}/{relation}` | Add M2M relation |
| `DELETE /models/{id}/{relation}` | Remove M2M relation |
| Per-model operations | Enable/disable individual endpoints |
| Field visibility | Configurable create_fields, update_fields |
| OpenAPI tags | Per-model tags |
| Auth integration | Optional auth dependency |
| Common dependencies | get_db, pagination params, sorting params |
| Main router | Aggregates all model routers |

---

## 5. GraphQL API

**Generator:** `GraphQLGenerator` (`generators/backend/graphql.py`)

| Feature | Details |
|---|---|
| Strawberry types | Types, inputs, update inputs per model |
| Query resolvers | Single item + list |
| Mutation resolvers | Create, update, delete |
| Subscription support | Per-model real-time events (created, updated, deleted) |
| Filter input types | StringFilter, IntFilter, FloatFilter, BoolFilter, DateTimeFilter, DateFilter |
| Relationship resolvers | Lazy-loaded, forward references |
| ListRelationFilter | Filter by related entity existence/properties |
| Pagination types | Connection/edge pattern |
| Context + scalars | Custom context, JSON scalar |
| camelCase naming | Automatic camelCase for GraphQL convention |
| Schema composition | Main schema combining all types |
| Use Connection | Relay-style connection pagination |
| Use DataLoader | N+1 prevention |
| Max depth/complexity | Query depth and complexity limits |

---

## 6. MCP Tools

**Generator:** `MCPGenerator` (`generators/backend/mcp.py`)

| Feature | Details |
|---|---|
| FastMCP server setup | MCP server initialization |
| `list_{model}` | List with filtering and pagination |
| `get_{model}` | Get by ID |
| `create_{model}` | Create new record |
| `update_{model}` | Update record |
| `delete_{model}` | Delete record |
| Per-model operations | Configurable which tools are generated |
| Custom tool prefix | `tool_prefix` per model |
| Custom tool descriptions | `tool_descriptions` per operation |
| Field descriptions | Used as tool parameter documentation |
| Relationship filters | Filter by related entity ID in list tool |
| Resource exposure | Optional MCP resource with URI template |

---

## 7. Authentication (Backend)

**Generator:** `AuthGenerator` (`generators/backend/auth.py`)

| Feature | Details |
|---|---|
| JWT token service | Cookie-based JWT creation/verification |
| Password service | bcrypt hashing and validation |
| Auth middleware | FastAPI dependency injection |
| Auth routes | signup, login, logout, refresh, me, change-password |
| User model | Generated User SQLAlchemy model |
| Auth schemas | Login, signup, token, user schemas |
| Auth config | Settings model with all auth parameters |
| Email verification | Token-based email verification flow |
| Password reset | Token-based password reset flow |
| MFA/TOTP | TOTP-based two-factor authentication |
| Account lockout | Lock after N failed login attempts |
| OAuth providers | Google, GitHub, etc. |
| Password policy | Min length, uppercase, lowercase, number, special char |
| Email or username login | Configurable login field |
| Default roles | Configurable default role assignment |
| Session expiry | Configurable token lifetime |

---

## 8. API Key Authentication

**Generator:** `APIKeyAuthGenerator` (`generators/backend/api_key_auth.py`)

| Feature | Details |
|---|---|
| API key verification | Verify against environment variable |
| API key middleware | FastAPI dependency |
| Single or multiple keys | Comma-separated keys from env var |
| Custom header name | Configurable auth header |
| Custom auth scheme | Configurable scheme name |

---

## 9. Admin Panel (Backend)

**Generator:** `AdminGenerator` (`generators/backend/admin.py`)

| Feature | Details |
|---|---|
| Admin service | User management (CRUD) |
| Bootstrap service | Initial admin user creation |
| Whitelist model | Email/domain-based signup control |
| Admin API routes | User management endpoints |
| Admin schemas | Admin-specific request/response schemas |
| Role management | Assign/change user roles |
| Email verification status | View/manage verification |
| Signup modes | Open, invite-only, whitelist (email or domain) |

---

## 10. Database Migrations

**Generator:** `AlembicGenerator` (`generators/backend/alembic.py`)

| Feature | Details |
|---|---|
| `alembic.ini` | Configuration file |
| `alembic/env.py` | Async SQLAlchemy support |
| `alembic/script.py.mako` | Migration template |
| Auto model imports | Discovers all models including auth/admin |
| Async driver support | Configurable async DB drivers |

---

## 11. TypeScript Types

**Generator:** `TypeScriptGenerator` (`generators/frontend/types.py`)

| Feature | Details |
|---|---|
| Model interfaces | Full TypeScript interfaces |
| Create interfaces | Without ID/timestamps |
| Update interfaces | All optional fields |
| Filter interfaces | Per-field filter types |
| Enum type aliases | Union types from enum choices |
| Common utility types | PaginatedResponse, Sorting, Pagination |
| Relationship fields | Nested objects or ID arrays |
| camelCase naming | Automatic conversion |

---

## 12. React Components

**Generator:** `ComponentsGenerator` (`generators/frontend/components.py`)

| Feature | Details |
|---|---|
| Form components | Base + extension (user-customizable) |
| Table components | Base + extension |
| Detail view components | Base + extension |
| Widget integration | Field → widget mapping |
| Field metadata | Labels, descriptions, tooltips |
| Configurable columns | `table_columns` per model |
| Hidden fields | Excluded from default views |
| FK references | Related entity display |
| Component index | Per-model exports |

---

## 13. React Hooks

**Generator:** `HooksGenerator` (`generators/frontend/hooks.py`)

| Feature | Details |
|---|---|
| Data fetching hooks | GraphQL (urql or Apollo) or REST (fetch) |
| Form state hooks | Field values, validation, errors, dirty tracking |
| Table state hooks | Pagination, sorting, filtering, search, selection |
| Loading/error states | Consistent loading and error handling |
| Cache invalidation | Mutation-aware refetching |
| Hooks index | Per-model exports |

---

## 14. Frontend Pages

**Generator:** `PagesGenerator` (`generators/frontend/pages.py`)

| Feature | Details |
|---|---|
| List pages | Table view with pagination/filtering |
| Detail pages | Single record view |
| Create pages | Form for new records |
| Edit pages | Form for updating records |
| Conditional generation | Based on model operations and component flags |
| React Router integration | Linked navigation between pages |
| CRUD action buttons | Context-appropriate actions |

---

## 15. Frontend Router

**Generator:** `RouterGenerator` (`generators/frontend/router.py`)

| Feature | Details |
|---|---|
| React Router config | Route definitions for all models |
| App.tsx | RouterProvider setup |
| main.tsx | GraphQL client provider wrapping |
| Navigation layout | Sidebar with model links |
| Protected routes | Auth-gated routes |
| Role-based access | Route-level RBAC |
| Admin routes | Admin panel pages |
| Auth routes | Login, signup, password reset, email verification, OAuth callback |
| Dark mode toggle | In navigation |
| Nav icons | Per-model icon support |

---

## 16. GraphQL Operations (Frontend)

**Generator:** `GraphQLOpsGenerator` (`generators/frontend/graphql_ops.py`)

| Feature | Details |
|---|---|
| Fragments | All fields for each model |
| Queries | Get single, list with pagination/filters |
| Mutations | Create, update, delete |
| Subscriptions | Real-time event subscriptions |
| Client setup | urql or Apollo client configuration |
| `gql` helper | Tagged template literal utility |
| Relationship fields | Included in fragments/queries |

---

## 17. Headless UI Hooks

**Generator:** `HeadlessGenerator` (`generators/frontend/headless.py`)

| Feature | Details |
|---|---|
| `usePagination` | Page state, navigation (next/prev/goto) |
| `useSelection` | Multi-select logic (toggle, select all, clear) |
| `useSorting` | Sort state, toggle direction |
| `useFiltering` | Filter state, apply/clear |
| `useSearch` | Search state with debounce |
| `useModal` | Modal open/close state |
| `useConfirmation` | Confirmation dialog with context |
| `useToast` | Toast notifications with context provider |
| `useDrawer` | Drawer/sidebar toggle state |
| Transform utilities | Data mapping, formatting helpers |
| Export utilities | CSV and JSON download |

---

## 18. Widget System

**Generator:** `WidgetSystemGenerator` (`generators/frontend/widgets.py`)

| Feature | Details |
|---|---|
| Widget type definitions | TypeScript interfaces for widget props |
| Default widget mapping | Field type → widget component |
| Widget registry | Runtime registry for widget lookup |
| Widget context provider | React context for widget access |
| Default widgets | TextInput, TextArea, NumberInput, Checkbox, Select, DatePicker, EmailInput, UrlInput, PhoneInput, PasswordInput, CurrencyInput, PercentageInput, TagInput, JsonEditor, RelationSelect |
| Custom widget registration | User-defined widgets via registry |
| Widget props/config | Per-widget configuration |

---

## 19. Design System

**Generator:** `DesignSystemGenerator` (`generators/frontend/design.py`)

| Feature | Details |
|---|---|
| ThemeToggle component | Dark/light mode toggle |
| Icon wrapper | Consistent icon rendering |
| UI component exports | Shared UI primitives |
| Icon sets | Lucide, Heroicons |
| Dark mode | Full dark mode support |

---

## 20. Frontend Auth

**Generator:** `FrontendAuthGenerator` (`generators/frontend/auth.py`)

| Feature | Details |
|---|---|
| AuthContext + useAuth() | React context with login/logout/signup/user state |
| Login form | Email/username + password |
| Signup form | Registration with validation |
| ProtectedRoute | Auth-gated route wrapper |
| Auth API client | Backend auth endpoint calls |
| Forgot password form | Email-based password reset initiation |
| Reset password page | Token-based password reset |
| Email verification page | Token-based email verification |
| TOTP verification | MFA code entry |
| OAuth callback | OAuth provider redirect handling |
| Role-based access | Current user role checks |

---

## 21. Frontend Admin Panel

**Generator:** `FrontendAdminGenerator` (`generators/frontend/admin.py`)

| Feature | Details |
|---|---|
| Admin API client | Admin endpoint calls |
| AdminLayout | Admin-specific layout wrapper |
| AdminDashboard | Admin overview page |
| AdminUsers | User list with management actions |
| AdminUserDetail | User detail with role/status editing |
| AdminWhitelist | Whitelist management (add/remove emails/domains) |
| BootstrapPage | Initial admin creation flow |
| Admin routes | Admin-only route definitions |

---

## 22. Backend Tests

**Generator:** `BackendTestGenerator` (`generators/testing/backend.py`)

| Feature | Details |
|---|---|
| pytest conftest | Fixtures for DB, client, auth |
| Test database setup | SQLite in-memory or PostgreSQL |
| Factory Boy factories | Per-model test data factories |
| Service unit tests | CRUD operation coverage |
| API integration tests | Endpoint request/response testing |
| GraphQL tests | Query/mutation testing |
| Auth tests | Login, signup, token verification |
| Migration check tests | Alembic migration validation |
| Async fixtures | Async SQLAlchemy test support |
| Auth bypass client | Testing without auth overhead |

---

## 23. Frontend Tests

**Generator:** `FrontendTestGenerator` (`generators/testing/frontend.py`)

| Feature | Details |
|---|---|
| Vitest setup | Test runner configuration |
| Test utilities | Custom render with providers |
| Component tests | React Testing Library tests |
| Hook tests | Hook behavior tests |
| Auth tests | Auth flow tests |
| Mock GraphQL client | Test doubles for GraphQL |
| Mock data helpers | Test data generation |

---

## 24. GitHub Actions CI/CD

**Generator:** `GitHubCIGenerator` (`ci/github.py`)

| Feature | Details |
|---|---|
| CI workflow | `ci.yml` — Python + Node.js test matrix |
| Release workflow | `release.yml` — semantic versioning |
| Dependabot config | Automated dependency updates |
| Semantic release | `.releaserc.json` config |
| Commitlint | `commitlint.config.js` — conventional commits |
| CHANGELOG | Initial CHANGELOG.md |
| Code coverage | Codecov integration |

---

## 25. Docker

**Generators:** `ComposeGenerator` (`docker/compose.py`), `ProductionComposeGenerator` (`docker/production.py`), `DockerCIGenerator` (`ci/docker.py`)

| Feature | Details |
|---|---|
| Dev docker-compose | `docker-compose.dev.yml` with hot reload |
| Prod docker-compose | `docker-compose.prod.yml` with replicas |
| Backend Dockerfile (dev) | Python dev image with hot reload |
| Backend Dockerfile (prod) | Multi-stage production build |
| Frontend Dockerfile (dev) | Node dev image with HMR |
| Frontend Dockerfile (prod) | Multi-stage production build |
| .dockerignore | Exclude unnecessary files |
| .env examples | Dev and prod environment templates |
| PostgreSQL service | Database container |
| Redis service | Optional Redis container |
| MCP server service | Optional MCP container |
| Health checks | Backend health check endpoint |
| Configurable ports | Backend, frontend, DB, Redis, MCP |
| Docker build workflow | CI workflow for Docker images |

---

## 26. DevContainer

**Generators:** `DevContainerGenerator` (`devcontainer/generator.py`) + `DevContainerGenerator` (`dx/devcontainer.py`)

Two implementations exist: `devcontainer/generator.py` (workspace-level, used by `prism devcontainer` CLI) and `dx/devcontainer.py` (project-level, used during `prism create`).

| Feature | Details |
|---|---|
| `devcontainer.json` | VS Code devcontainer configuration |
| `docker-compose.yml` | Dev environment services |
| `Dockerfile.dev` | Development image (Python + Node) |
| `.env.template` | Environment variable template |
| `setup.sh` | Post-create setup script |
| `.gitignore` update | Ignore devcontainer artifacts |
| Redis support | Optional Redis in dev container |
| PostgreSQL support | Optional PostgreSQL in dev container |

---

## 27. Deployment (Hetzner)

**Generator:** `HetznerDeployGenerator` (`deploy/hetzner.py`)

| Feature | Details |
|---|---|
| Terraform files | Main config, variables, outputs |
| Terraform modules | Server module, volume module |
| Cloud-init | Server provisioning scripts |
| Environment templates | Production env var templates |
| Deploy scripts | Deployment automation scripts |
| Traefik config | Reverse proxy with SSL/TLS |
| GitHub workflow | Deploy workflow for CI/CD |
| README | Deployment documentation |
| Server types | CX22–CX52, CAX11 (ARM) |
| Locations | Nuremberg, Falkenstein, Helsinki, Ashburn, Hillsboro |
| Floating IP | Production static IP |
| Private networking | VPC with configurable IP range |
| Firewall rules | SSH, HTTP, HTTPS |
| Remote state | Hetzner Object Storage for Terraform state |
| SSL/TLS | Let's Encrypt via Traefik |
| Docker registry | GHCR integration |
| PostgreSQL | VM-hosted with configurable version |
| Swap | Configurable swap for small VMs |

---

## 28. Developer Experience

**Generator:** `PreCommitGenerator` (`dx/precommit.py`)

| Feature | Details |
|---|---|
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| Ruff | Python linting/formatting |
| mypy | Type checking |
| pytest | Pre-push test execution |
| Frontend linting | ESLint/Prettier for frontend |

---

## 29. Documentation

**Generator:** `DocsGenerator` (`dx/docs.py`)

| Feature | Details |
|---|---|
| MkDocs config | `mkdocs.yml` with Material theme |
| Documentation structure | Index, getting started, API reference |
| Requirements | Docs dependencies |
| ReadTheDocs config | `.readthedocs.yml` |
| API docs | Auto-generated API documentation |

---

## 30. Change Tracking & Provenance

**Utilities:** `tracking/differ.py`, `tracking/logger.py`, `tracking/manifest.py`, `tracking/model_diff.py`

| Feature | Details |
|---|---|
| Unified diffs | Between generated and user-modified code (`DiffGenerator`) |
| Diff summaries | Lines added/removed/changed, JSON serializable |
| Override logging | JSON + Markdown logs when user code conflicts with generated code (`OverrideLogger`) |
| File manifest | SHA-256 hashes, timestamps, file strategies for all generated files (`FileManifest`) |
| Tamper detection | Detect user edits to generated files via manifest hash comparison |
| Model field diffs | Field-level change detection (added/removed fields per model class) (`ModelFieldChange`) |
| Markdown reports | Human-readable override/change reports |

---

## Summary

| Category | Generator Count | Key Capabilities |
|---|---|---|
| **Backend — Data** | 3 | Models, schemas, services with full CRUD + temporal + nested create |
| **Backend — API** | 3 | REST (FastAPI), GraphQL (Strawberry), MCP (FastMCP) |
| **Backend — Auth** | 3 | JWT auth, API key auth, admin panel |
| **Backend — DB** | 1 | Alembic migrations with async support |
| **Frontend — Core** | 6 | Types, components, hooks, pages, router, GraphQL ops |
| **Frontend — UI** | 3 | Headless hooks, widget system, design system |
| **Frontend — Auth** | 2 | Auth flows, admin panel |
| **Testing** | 2 | Backend (pytest + factories), frontend (Vitest) |
| **Infrastructure** | 4 | Docker (dev + prod), DevContainer, Hetzner deploy |
| **CI/CD** | 1 | GitHub Actions (CI + release + Docker build) |
| **DX** | 2 | Pre-commit hooks, documentation setup |
| **Utilities** | 4 | Diff generation, override logging, file manifest, model field diffs |
| **Total** | **34** | |

### Exposure Channels Per Model

Each model can be independently exposed via:

1. **REST** — FastAPI endpoints with OpenAPI docs
2. **GraphQL** — Strawberry schema with queries, mutations, subscriptions
3. **MCP** — FastMCP tools for AI assistant integration
4. **Frontend** — React components, hooks, pages, navigation

### Spec-Level Configuration Surface

| Spec Area | Configurable Options |
|---|---|
| **Fields** | 15+ attributes (type, required, unique, indexed, default, hidden, label, description, ui_placeholder, pattern, filterable, filter_operators, sortable, searchable, ui_widget, ui_widget_props, json_item_type) |
| **Relationships** | target, type, back_populates, cascade, on_delete, lazy |
| **Model behaviors** | timestamps, soft_delete, nested_create, temporal, bulk operations, table_name |
| **Exposure (REST)** | enabled, operations, prefix, tags, pagination, field visibility, auth, permissions, operation_ids |
| **Exposure (GraphQL)** | enabled, operations, type naming, connections, mutations, subscriptions, field visibility, dataloader, max depth/complexity, auth, permissions, nested queries |
| **Exposure (MCP)** | enabled, operations, tool prefix, tool descriptions, field descriptions, resource exposure |
| **Exposure (Frontend)** | enabled, operations, api_style, graphql_client, generate_form/table/detail_view, form_layout, table_columns, nav_label, nav_icon, widget_overrides |
| **Auth** | preset (jwt/api_key/custom), email verification, password reset, MFA, OAuth providers, password policy, signup mode, admin panel, roles |
| **Design** | icon_set, dark_mode, colors |
| **Database** | URL, async_driver, pool_size |
| **Testing** | factories, unit/integration/component/hook/graphql tests, test_database |
| **Templates** | minimal, full, saas, api-only |

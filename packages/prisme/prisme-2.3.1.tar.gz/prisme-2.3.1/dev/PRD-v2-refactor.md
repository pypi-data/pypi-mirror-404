# PRD: Prisme v2 Refactor — CLI / Spec / Config Boundaries

**Status:** Draft v3
**Author:** Lasse Thomsen
**Date:** 2026-01-31
**Branch:** `refactor_v2`

---

## 1. Problem Statement

Prisme v1 is conceptually strong but mentally expensive because users lack a stable mental model of where decisions live. The same category of decision (stack shape, exposure, auth) can appear as:

- A CLI flag (`--template saas`, `--database sqlite`)
- A spec attribute (`rest=RESTExposure(...)`, `mcp=MCPExposure(...)`)
- A generated target project config file (`config.py`, `database.py`)

There is no single source of truth, no documented precedence, and no explicit boundary between generated and user-owned code. This causes:

- **Regeneration anxiety** — users don't know what will be overwritten
- **Decision paralysis** — "should I change the flag, the spec, or the config?"
- **Upgrade friction** — no versioned schema means silent breakage

---

## 2. Goals

- Establish clear ownership boundaries between **CLI**, **Domain Spec**, **Project Spec**, and **Prisme Config**
- Introduce explicit versioning for spec and config schemas
- Make regeneration safe, predictable, and boring
- Enable evolution without breaking existing projects
- Rename CLI and all references to **prisme** consistently

---

## 3. Non-Goals

> **See also:** [generator-feature-list.md](generator-feature-list.md) — complete inventory of v1 generation capabilities (34 generators/utilities) that must be preserved or explicitly migrated.

- Redesign the Pydantic DSL from scratch
- Remove existing generators
- Add new product features (auth providers, new frameworks)
- Force migration of all existing projects immediately
- Build ejection tooling (but see section 6.5 for the ejection story)

---

## 4. Core Mental Model

### 4.1 5-Minute Walkthrough

```bash
# 1. Create a new project
prisme create wind-pipeline --database postgresql --template saas

# 2. Define your domain — what exists
vim specs/models.py

# 3. Configure the target project — what to generate
vim specs/project.py

# 4. Regenerate — ALWAYS_OVERWRITE files updated, your GENERATE_ONCE files are safe
prisme generate

# 5. Customize in app/ — add business logic, override components
vim app/backend/extensions/routers.py

# 6. Regenerate again — your customizations are untouched
prisme generate   # app/ and packages/ are never modified
```

Core loop: **create once**, then iterate between editing specs and running **generate**. Your GENERATE_ONCE files (pages, extensions, entry points) are never touched by `generate`.

---

### 4.2 The Four Layers

- **CLI** = when / how (ephemeral, execution-time)
- **Domain Spec** = what exists (domain truth, versioned, regen-safe)
- **Project Spec** = what to generate (target project blueprint, versioned, regen-safe)
- **Prisme Config** = generator policy (tool choices, paths, strict mode)

#### Domain Spec (`specs/models.py`)

Defines models, fields, relationships, behaviors. Answers: **"What does my product mean?"**

#### Project Spec (`specs/project.py`)

Defines target blueprint: database, exposure, auth, frontend, design, testing. Answers: **"What do I want generated?"**
This describes the **target project**, not the generator.

#### Prisme Config (`prisme.toml`)

Defines generator behavior: strict mode, auto-format, tool choices, paths. Answers: **"How should Prisme behave?"**
This file is intentionally small (~15 lines).

---

### 4.3 Why Two Spec Files?

Previous thinking put target-project choices (database, auth, frontend, design) in `prisme.toml`. That was wrong — those are part of the **generation specification**. They describe what the user wants generated, not how the generator runs.

Test: *If I copy my specs to a different machine with prisme installed, should the same target project come out?*
**Yes.** Therefore DB/auth/frontend/design/exposure belong in specs, not in prisme.toml.

---

### 4.4 Precedence

**Precedence for target-project meaning:**

```
CLI flags  >  Project Spec  >  Domain Spec defaults
```

Prisme Config is not part of target-meaning precedence — it affects tool behavior only.

Constraints:

- CLI flags may not affect generated output shape (except `create`, which writes durable choices into specs/config)
- Project Spec selects generators, defaults, and target infrastructure
- Domain Spec is never overridden — only interpreted
- Prisme Config affects generator behavior only (strictness, formatting, paths)

---

### 4.5 User Decision Rule

| Question | Answer |
|---|---|
| Will this survive regeneration? | Yes → Spec (domain or project). No → CLI. |
| Is this about domain meaning? | Yes → Domain Spec. |
| Is this about what gets generated (DB, auth, frontend, design)? | Yes → Project Spec. |
| Is this about the prisme tool itself (formatting, paths, strict mode)? | Yes → Prisme Config. |
| Should this differ in prod vs dev? | Possibly → Project Spec (env-aware defaults). |

---

## 5. Layer Contracts

### 5.1 CLI Contract

The CLI command is renamed from `prism` to `prisme`.

Allowed responsibilities: **execution only**.

| Command | Purpose | Category |
|---|---|---|
| `prisme create` | Scaffold a new project (writes `prisme.toml` + `specs/` + full stack) | Core |
| `prisme generate` | Regenerate from specs + config | Core |
| `prisme plan` | Preview generation output (dry-run diff) | Core (P2) |
| `prisme apply` | Execute planned generation | Core (P2) |
| `prisme validate` | Validate spec files | Core |
| `prisme doctor` | Diagnose project health | Core |
| `prisme migrate` | Upgrade spec/config schema versions | Core |
| `prisme dev` | Start dev servers | Runtime |
| `prisme test` | Run test suite | Runtime |
| `prisme install` | Install deps | Runtime |
| `prisme db` | DB ops (init/migrate/reset/seed) | Runtime |
| `prisme deploy` | Infra deployment ops | Operations |
| `prisme docker` | Docker ops | Operations |
| `prisme devcontainer` | Devcontainer ops | Operations |
| `prisme ci` | CI workflow ops | Operations |
| `prisme proxy` | Reverse proxy ops | Operations |
| `prisme subdomain` | Subdomain ops | Operations |
| `prisme auth` | Auth to prisme.dev | Operations |
| `prisme admin` | Admin ops | Operations |
| `prisme schema` | Output GraphQL schema | Utility |

Allowed flags (execution-only):

- `--path`, `--verbose`, `--quiet`
- `--dry-run`, `--force`, `--watch`
- `--env dev|prod`
- `--diff`

Disallowed — CLI flags must NOT control:

- API exposure (REST/GraphQL/MCP)
- UI inclusion/framework choice
- Auth strategy
- Database choice
- Template/architecture selection (after initial create)

**`create` exception:** `prisme create` may accept durable flags as input, but **must write them into** `specs/project.py` and `prisme.toml`. Flags are not retained as parallel truth.

---

### 5.2 Domain Spec Contract (`specs/models.py`)

The domain spec defines domain truth: what exists and what it means.

**✅ Domain Spec defines:**

- Models and fields (types, validation, constraints)
- Field attributes: `required`, `unique`, `indexed`, `default`, `hidden`, `label`, `description`, `ui_placeholder`, `pattern`
- Field types including `json` with optional `json_item_type`
- Field UI hints: `ui_widget`, `ui_widget_props` (field-specific)
- Relationships: `target`, `type`, `back_populates`, `cascade`, `on_delete`
- Exposure intent per model:
  - `expose=True/False`
  - `operations=[create|read|update|delete|list]`
- Field query behavior: `filterable`, `filter_operators`, `sortable`, `searchable`
- Enums and custom types
- Conditional validation: `conditional_required`, `conditional_enum`
- Nested create relationships
- Temporal/time-series configuration
- Lifecycle hook names (`before_create`, `after_create`, …)
- Model behaviors: `soft_delete`, `timestamps` (independent)
- Field visibility controls (`create_fields`/`update_fields`/`read_fields`/`list_fields`)
- Domain RBAC: roles and permissions (domain truth)

**❌ Domain Spec does NOT define:**

- Framework mechanics (FastAPI route naming, Strawberry type naming)
- Delivery mechanics (URL prefixes, MCP tool prefixes, naming conventions)
- Global pagination defaults (page size, max page size) — per-model overrides via `DeliveryOverrides` are allowed
- Auth provider details (JWT settings, OAuth secrets)
- Database engine/driver/connection strings
- Design system globals (theme/colors/fonts)
- Frontend framework choice

**Per-model deviations from project defaults** must be typed overrides (no raw dicts).

**Minimal example:**

```python
PRISME_DOMAIN_VERSION = 2

from prisme.spec import StackSpec, Model, Field, Relationship

stack = StackSpec(
    name="blog",
    models=[
        Model(
            name="Post",
            fields=[
                Field("title", type="string", required=True),
                Field("body", type="text"),
                Field("published", type="boolean", default=False),
            ],
            relationships=[Relationship("comments", target="Comment", type="one-to-many")],
        ),
        Model(
            name="Comment",
            fields=[
                Field("author", type="string", required=True),
                Field("body", type="text", required=True),
            ],
        ),
    ],
)
```

Defaults: all models exposed, full CRUD, timestamps enabled. Everything else (`expose`, `operations`, `soft_delete`, lifecycle hooks, `overrides`, `temporal`, etc.) is opt-in.

**Full example** — showing advanced features:

```python
PRISME_DOMAIN_VERSION = 2

from prisme.spec import (
    StackSpec, Model, Field, Relationship,
    DeliveryOverrides, FrontendOverrides, MCPOverrides,
)

stack = StackSpec(
    name="wind-pipeline",
    models=[
        Model(
            name="Turbine",
            fields=[
                Field("name", type="string", required=True, unique=True, label="Turbine Name"),
                Field("capacity_mw", type="float", label="Capacity (MW)", ui_widget="slider", ui_widget_props={"min": 0.5, "max": 20, "step": 0.5}),
                Field("status", type="enum", choices=["active", "maintenance", "offline"]),
                Field("location", type="json", json_item_type="float"),
                Field("api_key", type="string", hidden=True),
                Field("color_hex", type="string", pattern=r"^#[0-9A-Fa-f]{6}$", ui_placeholder="#FF5733"),
            ],
            relationships=[
                Relationship("readings", target="Reading", type="one-to-many", back_populates="turbine", cascade="all, delete-orphan"),
            ],
            expose=True,
            operations=["create", "read", "update", "list"],  # no delete
            soft_delete=True,
            timestamps=True,
            before_create="validate_turbine_capacity",
            after_create="notify_turbine_added",
            delivery_overrides=DeliveryOverrides(page_size=50),
            frontend_overrides=FrontendOverrides(nav_icon="wind", nav_label="Turbines", table_columns=["name", "capacity_mw", "status"], include_in_nav=True),
            mcp_overrides=MCPOverrides(tool_prefix="turbine", tool_descriptions={"list": "List all wind turbines"}),
        ),
        Model(
            name="Reading",
            fields=[
                Field("timestamp", type="datetime", required=True),
                Field("wind_speed", type="float", filterable=True, filter_operators=["eq", "gt", "lt", "between"], label="Wind Speed (m/s)"),
                Field("power_output", type="float", searchable=False, description="Generated power in kW"),
            ],
            relationships=[
                Relationship("turbine", target="Turbine", type="many-to-one", back_populates="readings", on_delete="CASCADE"),
            ],
            expose=True,
            operations=["create", "read", "list"],  # read-only after creation
            timestamps=True,
            delivery_overrides=DeliveryOverrides(page_size=100),
            temporal={"timestamp_field": "timestamp", "group_by_field": "turbine_id"},
            nested_create=["turbine"],
        ),
    ],
)
```

**Typed override sub-models** replace the untyped `overrides: dict`:

| Sub-model | Fields | Purpose |
|---|---|---|
| `DeliveryOverrides` | `page_size`, `max_page_size`, `rest_tags`, `subscriptions` | Per-model deviation from project spec delivery defaults |
| `FrontendOverrides` | `nav_icon`, `nav_label`, `table_columns`, `form_layout`, `list_fields`, `include_in_nav`, `generate_form`, `generate_table`, `generate_detail_view` | Per-model UI presentation and generation hints |
| `MCPOverrides` | `tool_prefix`, `tool_descriptions` | Per-model MCP tool customization |

These are Pydantic models with full validation, IDE autocomplete, and documentation. No more guessing which keys are valid.

**Versioning:**
- `PRISME_DOMAIN_VERSION = <integer>` at module level
- Generator refuses unknown/unsupported versions with a clear error

---

### 5.3 Project Spec Contract (`specs/project.py`)

The project spec defines the target blueprint — everything describing what you want generated.

**✅ Project Spec defines:**

- Backend / frontend enablement and ports
- Exposure channels (REST/GraphQL/MCP/frontend), each as typed config with `enabled`
- Exposure defaults (pagination, filter operator defaults, limits)
- Auth provider choice + signup mode + admin panel etc.
- Database engine + driver type + env var naming
- Design defaults (theme, icon set, border radius)
- Global widget registry (widget component names)
- Testing defaults (unit/integration/component, factories)
- Extension policy (strategies + protected regions)

Project Spec is a Pydantic class with typed sub-models.

**Full example:**

```python
PRISME_PROJECT_VERSION = 1

from prisme.spec import (
    ProjectSpec,
    BackendConfig, FrontendConfig, ExposureConfig, ExposureDefaults,
    RESTConfig, GraphQLConfig, MCPConfig, FrontendExposureConfig,
    AuthConfig, DatabaseConfig, DesignConfig, WidgetConfig,
    TestingConfig, ExtensionConfig,
)

project = ProjectSpec(
    name="wind-pipeline",

    backend=BackendConfig(
        framework="fastapi",
        module_name="wind_pipeline",
        port=8000,
    ),

    frontend=FrontendConfig(
        enabled=True,
        framework="react",
        port=5173,
    ),

    exposure=ExposureConfig(
        defaults=ExposureDefaults(
            page_size=20,
            max_page_size=100,
            filter_operators=["eq", "ne", "gt", "lt", "gte", "lte", "like", "ilike", "contains", "in", "between"],
            pagination_style="offset",
        ),
        rest=RESTConfig(
            enabled=True,
        ),
        graphql=GraphQLConfig(
            enabled=True,
            path="/graphql",
            graphiql=True,
            subscriptions=False,
            query_depth_limit=5,
            use_connection=True,
            use_dataloader=True,
        ),
        mcp=MCPConfig(
            enabled=True,
        ),
        frontend=FrontendExposureConfig(
            api_style="graphql",
            generate_form=True,
            generate_table=True,
            generate_detail_view=True,
        ),
    ),

    auth=AuthConfig(
        provider="jwt",
        admin_panel=True,
        signup_mode="whitelist",
        signup_domains=["numerous.com"],
    ),

    database=DatabaseConfig(
        engine="sqlite",
        async_driver=True,
        url_env="DATABASE_URL",
    ),

    design=DesignConfig(
        theme="nordic",
        dark_mode=True,
        icon_set="lucide",
        border_radius="md",
        widgets=WidgetConfig(
            custom_widgets={"coordinates": "CoordinatesInput", "roughness": "RoughnessDisplay"},
            field_widgets={"EnvironmentAnalysis.center_lat": "LatitudeInput", "EnvironmentAnalysis.center_lon": "LongitudeInput"},
        ),
    ),

    testing=TestingConfig(
        unit_tests=True,
        integration_tests=True,
        factories=True,
        graphql_tests=True,
        component_tests=True,
        hook_tests=True,
        test_database="sqlite",
    ),

    extensions=ExtensionConfig(
        services_strategy="generate_base",
        components_strategy="generate_base",
        pages_strategy="generate_once",
        use_protected_regions=True,
    ),
)
```

**Minimal example** — most fields have sensible defaults:

```python
PRISME_PROJECT_VERSION = 1

from prisme.spec import ProjectSpec, DatabaseConfig

project = ProjectSpec(
    name="blog",
    database=DatabaseConfig(engine="sqlite"),
)
```

This gives you: FastAPI backend, React frontend, REST + GraphQL exposure, SQLite, JWT auth, default design — all from sensible defaults in the Pydantic model.

**Why Python (Pydantic) instead of TOML:**

- IDE autocomplete and validation
- Composability (import shared configs, use conditionals)
- Consistent with domain spec (both Python, both in `specs/`)
- Can be serialized to TOML/JSON later if needed

**Versioning:**
- `PRISME_PROJECT_VERSION = <integer>` at module level
- Independent from domain spec version

---

### 5.4 Prisme Config Contract (`prisme.toml`)

Prisme config defines generator policy — **tool behavior only**.

**Config owns:**

| Category | Examples |
|---|---|
| Generator version | `prisme_version` |
| Config schema | `config_version` |
| Paths | `spec_path`, `project_path` |
| Generation policy | `strict` / `lenient` mode |
| Formatting | `auto_format`, `formatter` |
| Tool choices | `python_manager`, `package_manager` |

**Example:**

```toml
prisme_version = "2.0.0"
config_version = 1

[project]
spec_path = "specs/models.py"
project_path = "specs/project.py"

[generation]
mode = "strict"       # "strict" or "lenient"
auto_format = true

[tools]
python_manager = "uv"
package_manager = "pnpm"
```

That's it. Everything about the target project lives in `specs/project.py`. Everything about the domain lives in `specs/models.py`. The config file is boring on purpose.

**Modularity (P2):** Config includes (`prisme.d/*.toml`) are deferred to Phase 2. For P0 and P1, all config lives in a single `prisme.toml`.

**Versioning:**
- `config_version = <integer>` — schema version for this file format
- `prisme_version = "<semver>"` — generator version last used
- Config is **mandatory** (empty file is valid; generator fails with helpful error if missing)

---

## 6. Ownership Boundaries in the Repo

### 6.1 Two-Phase Generation Model

**Phase A: `prisme create`**

- Scaffolds a fully bootable project with entry points, config, infrastructure
- Writes scaffolding files using **GENERATE_ONCE** strategy
- Runs an initial `generate` to populate generated code inside `packages/`

**Phase B: `prisme generate`**

- Writes into `packages/` using **file strategy** to determine safety
- `ALWAYS_OVERWRITE` files are regenerated every time (types, base components, schemas, etc.)
- `GENERATE_ONCE` files are only created if missing — never overwritten (pages, extension components, entry points)
- Safe to run anytime — user-customized files are never touched

This separation means:
- `create` gives you a working stack immediately (no manual wiring needed)
- `generate` is safe to run at any time without fear of losing work
- Safety is enforced by **file strategy per file**, not by directory boundaries

### 6.2 Directory Structure

Generated and user-owned files coexist inside `packages/`. The **file strategy** (not directory location) determines ownership. `ALWAYS_OVERWRITE` files are fully managed by Prism. `GENERATE_ONCE` files belong to the user after first creation.

```
project-root/
├── prisme.toml                    # Prisme Config (generator policy, user-owned)
├── specs/
│   ├── models.py                  # Domain Spec (user-owned, versioned)
│   └── project.py                 # Project Spec (user-owned, versioned)
├── packages/
│   ├── backend/
│   │   ├── pyproject.toml         # GENERATE_ONCE (from create)
│   │   └── src/{name}/
│   │       ├── __init__.py        # GENERATE_ONCE (from create)
│   │       ├── main.py            # GENERATE_ONCE — entry point, user-owned
│   │       ├── config.py          # GENERATE_ONCE — app config, user-owned
│   │       ├── database.py        # GENERATE_ONCE — DB setup, user-owned
│   │       ├── models/            # ALWAYS_OVERWRITE — regenerated
│   │       ├── schemas/           # ALWAYS_OVERWRITE — regenerated
│   │       ├── services/          # Mixed — base (overwrite) + extensions (once)
│   │       ├── api/
│   │       │   ├── rest/          # Mixed — base routers (overwrite) + extensions (once)
│   │       │   ├── graphql/       # ALWAYS_OVERWRITE — regenerated
│   │       │   └── mcp/           # ALWAYS_OVERWRITE — regenerated
│   │       ├── auth/              # ALWAYS_OVERWRITE — regenerated (when auth enabled)
│   │       ├── alembic/           # ALWAYS_OVERWRITE — regenerated
│   │       └── tests/             # GENERATE_ONCE — test scaffolds
│   └── frontend/
│       ├── package.json           # GENERATE_ONCE (from create)
│       └── src/
│           ├── main.tsx           # ALWAYS_OVERWRITE — GraphQL provider wiring
│           ├── App.tsx            # ALWAYS_OVERWRITE — RouterProvider
│           ├── router.tsx         # ALWAYS_OVERWRITE — route definitions
│           ├── types/             # ALWAYS_OVERWRITE — TypeScript interfaces
│           ├── graphql/           # ALWAYS_OVERWRITE — operations & client
│           ├── hooks/             # ALWAYS_OVERWRITE — data hooks
│           ├── components/
│           │   ├── _generated/    # ALWAYS_OVERWRITE — base components
│           │   └── {Model}*.tsx   # GENERATE_ONCE — extension components
│           ├── pages/             # GENERATE_ONCE — user-customizable pages
│           ├── contexts/          # ALWAYS_OVERWRITE — auth context (when enabled)
│           ├── lib/               # ALWAYS_OVERWRITE — API clients
│           ├── prism/             # ALWAYS_OVERWRITE — headless hooks & utilities
│           └── ui/                # GENERATE_ONCE — design system components
├── docker/                        # GENERATE_ONCE (from create, user-owned)
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── Dockerfile
├── .github/                       # GENERATE_ONCE (from create, user-owned)
└── .devcontainer/                 # GENERATE_ONCE (from create, user-owned)
```

### 6.3 File Strategy

| Strategy | Behavior | Written by | Used for |
|---|---|---|---|
| `ALWAYS_OVERWRITE` | Replaced every regeneration | `prisme generate` | Types, schemas, models, base components, hooks, router, GraphQL ops, API clients |
| `GENERATE_ONCE` | Created if missing, never overwritten | `prisme create` or first `prisme generate` | Entry points, config, pages, extension components, tests, infrastructure |

**Key principle:** Safety is enforced by **file strategy**, not by directory location. Both strategies can coexist in the same directory (e.g., `components/` has `_generated/` base files that are always overwritten and extension files that are generate-once).

### 6.4 Rules

> **`prisme generate`** writes files using their declared strategy. `ALWAYS_OVERWRITE` files are regenerated. `GENERATE_ONCE` files are skipped if they already exist.
>
> **`prisme create`** scaffolds the full project and runs an initial `generate`. It writes three key artifacts: `prisme.toml`, `specs/models.py`, `specs/project.py`.
>
> **User customization** happens in `GENERATE_ONCE` files (pages, extension components, service extensions, entry points). These are created once and then belong entirely to the user.
>
> **Editing `ALWAYS_OVERWRITE` files is unsupported** and detectable via manifest hashes. Customizations should go in extension files or `GENERATE_ONCE` counterparts.

### 6.5 Ejection Story

Prisme is designed so ejection is trivial even without dedicated tooling. To eject:

1. Delete `prisme.toml` and `specs/`
2. You now own all the code — it's standard Python/TypeScript with no prisme runtime dependency

Generated code has **no imports from `prisme`** at runtime. It uses only standard libraries (FastAPI, SQLAlchemy, Pydantic, React, etc.). The `prisme` package is a dev-time code generator, not a runtime framework. This is intentional: lock-in anxiety is an adoption blocker, and the answer is "your generated code already works without us."

### 6.6 Import Direction

Within `packages/`, generated code (models, schemas, hooks, types) is imported by entry points and extension files:

```
packages/backend/src/{name}/main.py    (GENERATE_ONCE, user-owned)
  ├── imports from models/              (ALWAYS_OVERWRITE, generated)
  ├── imports from services/            (mixed: base generated, extensions user-owned)
  ├── imports from api/rest/            (mixed: base generated, extensions user-owned)
  └── wires them together
```

Generated base code is **pure library code** — it exports symbols but does not import from extension files. Extension files import from generated base code and add or override behavior.

---

## 7. Extension Points (First-Class Hooks)

Customization happens via **explicit, stable hooks** — not ad-hoc edits to generated code.

### Backend

Extension files are `GENERATE_ONCE` — created once by `prisme create` or first `prisme generate`, then owned by the user.

| Hook | Purpose | Location | Strategy |
|---|---|---|---|
| `main.py` | Entry point, wires everything together | `packages/backend/src/{name}/` | GENERATE_ONCE |
| Service extensions | Override/extend service methods per model | `packages/backend/src/{name}/services/` | GENERATE_ONCE |
| Router extensions | Additional API routes | `packages/backend/src/{name}/api/rest/` | GENERATE_ONCE |

### Frontend

| Hook | Purpose | Location | Strategy |
|---|---|---|---|
| Extension components | User-customizable form/table/detail | `packages/frontend/src/components/` | GENERATE_ONCE |
| Pages | User-customizable page components | `packages/frontend/src/pages/` | GENERATE_ONCE |
| UI components | Design system components | `packages/frontend/src/ui/` | GENERATE_ONCE |

All `GENERATE_ONCE` files are preserved across regeneration — `prisme generate` skips them if they already exist.

### Discovery Mechanism

Extension discovery is **not magic** — it happens in the user-owned entry point (`packages/backend/src/{name}/main.py`), which is scaffolded by `prisme create` with `GENERATE_ONCE` strategy. The entry point imports from generated base code (ALWAYS_OVERWRITE) and extension files (GENERATE_ONCE):

```python
# packages/backend/src/wind_pipeline/main.py (GENERATE_ONCE, user-owned after creation)

from fastapi import FastAPI
from .api.rest.routes import router as generated_router  # ALWAYS_OVERWRITE base
from .api.rest.extensions import router as ext_router     # GENERATE_ONCE extension

app = FastAPI()
app.include_router(generated_router)
app.include_router(ext_router)
```

This means:
- **No runtime magic.** Discovery is plain Python imports.
- **The user owns the wiring.** Since `main.py` is `GENERATE_ONCE`, users can change the composition logic however they want.
- **Base code never imports from extensions.** ALWAYS_OVERWRITE files are pure library code. Extension files import from base code and add or override behavior.

### Contract Between Base and Extension Files

| Scenario | Behavior |
|---|---|
| Extension file exists (GENERATE_ONCE) | Imported by entry point, used at runtime |
| Extension file has an import error | **App crashes at startup** (intentional — bug in user code) |
| Extension file deleted by user | Entry point import fails — user must update main.py |

This is a standard Python convention: presence = opt-in, absence = opt-out, broken code = loud failure.

---

## 8. Versioning & Migration

### 8.1 Schema Versions

| Artifact | Version type | Example |
|---|---|---|
| Domain Spec | Integer (`PRISME_DOMAIN_VERSION`) | `2` |
| Project Spec | Integer (`PRISME_PROJECT_VERSION`) | `1` |
| Config | Integer (`config_version`) | `1` |
| Generator | SemVer (`prisme_version`) | `"2.0.0"` |

These are **independent** — a generator bugfix doesn't bump schema versions.

### 8.2 Compatibility Rules

- `prisme generate` **refuses** unknown/unsupported schema versions
- Deprecated versions produce warnings with migration guidance
- No silent behavior changes across versions

**Error examples:**

```
$ prisme generate
ERROR: specs/models.py declares PRISME_DOMAIN_VERSION = 3, but this version
of prisme (2.0.0) only supports domain spec versions 1–2.

  → Upgrade prisme:  uv pip install --upgrade prisme
  → Or downgrade your spec version if this was unintentional.
```

```
$ prisme generate
ERROR: prisme.toml not found in /home/user/wind-pipeline.

  → Run `prisme create` to scaffold a new project, or
  → Create prisme.toml manually (see: https://prisme.dev/docs/config)
```

```
$ prisme generate
ERROR: specs/project.py not found.

  → Run `prisme migrate` to generate specs/project.py from your prisme.toml, or
  → Create it manually (see: https://prisme.dev/docs/project-spec)
```

```
$ prisme doctor
✓ prisme.toml valid (config_version=1)
✓ domain spec version supported (PRISME_DOMAIN_VERSION=2)
✓ project spec version supported (PRISME_PROJECT_VERSION=1)
✗ packages/backend/src/wind_pipeline/models/turbine.py has been manually edited (ALWAYS_OVERWRITE)
  → Run `prisme generate` to restore, or customize via service/router extensions instead
✓ extension hooks correctly placed
✓ dependency managers match config (uv, pnpm)
```

### 8.3 Migration Command (P2)

```bash
prisme migrate              # Auto-migrate if safe
prisme migrate --dry-run    # Show what would change
prisme migrate --write      # Write changes
```

Migration handles:
- Domain spec schema upgrades (v1 → v2: move delivery mechanics out of spec)
- Project spec introduction (v0 → v1: extract from old `prisme.toml`)
- Config schema upgrades (v0 → v1: shrink to generator policy only)
- Detection of current state (e.g., infer python_manager from lockfiles)

---

## 9. Project Manifest (Provenance)

Each generation writes `.prisme-manifest.json` in the project root:

```json
{
  "prisme_version": "2.0.0",
  "domain_version": 2,
  "project_version": 1,
  "config_version": 1,
  "domain_hash": "sha256:abc123...",
  "project_hash": "sha256:789xyz...",
  "config_hash": "sha256:def456...",
  "generators_enabled": ["rest", "graphql", "mcp", "frontend"],
  "generated_at": "2026-01-31T14:30:00Z",
  "files": {
    "packages/backend/src/wind_pipeline/models/turbine.py": "sha256:...",
    "packages/backend/src/wind_pipeline/models/reading.py": "sha256:..."
  }
}
```

Used for: debugging, CI validation, support triage, detecting edited ALWAYS_OVERWRITE files.

---

## 10. Plan / Apply Workflow (P2)

**Default workflow:** `prisme generate` — this is what users run. It regenerates ALWAYS_OVERWRITE files and creates any missing GENERATE_ONCE files. There is no decision to make.

**Team/CI workflow (P2):** For code review and CI pipelines, `plan` and `apply` split generation into preview and execution:

```bash
prisme generate          # The only command most users need
prisme generate --diff   # Same, but show what changed afterward

# P2 only — for team review workflows:
prisme plan              # Preview what will change (writes a plan file, no code changes)
prisme apply             # Execute the last plan
```

`prisme plan` outputs:
- Files to create / modify / delete
- Diff summary
- Risk classification (safe / modified generated files detected)

`plan`/`apply` is deferred to P2 because it primarily serves team workflows and CI. Solo developers use `prisme generate` and never think about it.

---

## 11. Doctor Command

```bash
prisme doctor
```

Checks:
- `prisme.toml` exists and is valid
- `specs/models.py` exists and domain version is supported
- `specs/project.py` exists and project version is supported
- Generated files haven't been manually edited
- Dependency managers match config
- Required directories exist
- Extension hooks are correctly placed

Usable locally and in CI.

---

## 12. Regeneration Guarantees (Golden Tests)

Automated CI tests proving:

1. **Generate → edit user files → regenerate → user files unchanged**
2. **Change domain spec → regenerate → only ALWAYS_OVERWRITE files change, GENERATE_ONCE files untouched**
3. **Change project spec → regenerate → only ALWAYS_OVERWRITE files change, GENERATE_ONCE files untouched**
4. **Migrate v1 → v2 → generate succeeds**
5. **Extension hooks are discovered and preserved**

These tests are the **credibility engine** for the "regen without fear" promise.

---

## 13. Naming

All references are unified under **`prisme`**:
- CLI command: `prisme`
- PyPI package: `prisme`
- Config file: `prisme.toml`
- Import: `from prisme.spec import ...`
- Manifest: `.prisme-manifest.json`
- Documentation, README, all references

The `prism` name is retired to avoid OSS namespace collisions.

---

## 14. Phased Rollout

### Phase 0 (P0): Foundation — Boundaries, Spec Split, & Config

**Goal:** Establish the four-layer contract. Users can point to one file for each concern.

- [x] Rename CLI and package to `prisme`
- [x] Introduce `prisme.toml` (config_version=1) — generator policy only (~15 lines)
- [x] Introduce `specs/project.py` with `ProjectSpec` Pydantic class (PRISME_PROJECT_VERSION=1)
- [x] `ProjectSpec` with typed sub-models: `BackendConfig`, `FrontendConfig`, `ExposureConfig`, `ExposureDefaults`, `GraphQLConfig`, `MCPConfig`, `FrontendExposureConfig`, `AuthConfig`, `DatabaseConfig`, `DesignConfig`, `WidgetConfig`, `TestingConfig`, `ExtensionConfig`
- [x] Replace `overrides: dict` with typed sub-models: `DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides`
- [ ] `prisme create` scaffolds full bootable project (GENERATE_ONCE for entry points, config, infrastructure)
- [ ] `prisme create` writes 3 artifacts: `prisme.toml`, `specs/models.py`, `specs/project.py`
- [ ] `prisme create` runs initial `prisme generate` at end
- [ ] `prisme generate` reads from `prisme.toml` + `specs/` (fail if missing)
- [x] `prisme generate` uses file strategy (ALWAYS_OVERWRITE / GENERATE_ONCE) to determine safety per file
- [x] Add `PRISME_DOMAIN_VERSION` to domain spec files
- [x] Add `PRISME_PROJECT_VERSION` to project spec files
- [x] Move delivery mechanics (pagination, prefixes, default filter operators) from domain spec to project spec defaults
- [x] Simplify domain spec exposure to intent-level (operations list + expose flag)
- [x] Keep per-field query behavior in domain spec (filterable, filter_operators, sortable, searchable)
- [x] Keep `ui_widget` and `ui_widget_props` on Field (domain spec) — field-specific UI hints are domain-adjacent
- [ ] Document `hidden`, `pattern`, `json_item_type`, `label`, `description`, `ui_placeholder` on Field
- [ ] Document `back_populates`, `cascade`, `on_delete` on Relationship
- [ ] Document `timestamps` as independent toggle from `soft_delete`
- [x] Keep lifecycle hooks in domain spec (before_create, after_create, etc.)
- [x] Keep conditional validation in domain spec (conditional_required, conditional_enum)
- [x] Keep nested_create and temporal config in domain spec
- [x] Keep per-model field visibility in domain spec (create_fields, update_fields, read_fields, list_fields)
- [ ] Ensure ALWAYS_OVERWRITE code is pure library code (no imports from GENERATE_ONCE extension files)
- [ ] Entry points (GENERATE_ONCE) wire generated base code + extensions together
- [ ] Document the mental model ("Where does this live in Prisme?")
- [ ] Basic version detection (warn on missing versions)

### Phase 1 (P1): Safety & Trust

**Goal:** Make regeneration provably safe.

- [ ] `.prisme-manifest.json` written on every generation (provenance metadata)
- [ ] Extension hooks system (backend: dependencies, routers, events, policies)
- [ ] Extension hooks system (frontend: component overrides, custom pages)
- [ ] `prisme doctor` command
- [ ] Golden regeneration tests in CI
- [ ] Detection of edited ALWAYS_OVERWRITE files (warn/block via manifest hashes)
- [ ] Deterministic generation (stable ordering, formatting)

### Phase 2 (P2): Evolution & Teams

**Goal:** Support upgrades and team workflows.

- [ ] `prisme migrate` command (domain v1→v2, project v0→v1, config v0→v1)
- [ ] `prisme plan` / `prisme apply` workflow
- [ ] Config includes (`prisme.d/*.toml`)
- [ ] Strict vs lenient generation mode
- [ ] Multi-file spec support (`specs/` directory auto-loading)
- [ ] Error taxonomy with fix-it messages
- [ ] MCP tool hooks (pre/post)

---

## 15. Success Criteria

This refactor is successful when:

1. Users **always know** where a change belongs (CLI vs domain spec vs project spec vs config)
2. Regeneration is **boring and safe** — no surprises
3. Upgrades are **explicit and guided** — no silent breakage
4. The framework feels **predictable and trustworthy**
5. New users can understand the mental model in **under 2 minutes**

---

## 16. Resolved Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Monorepo vs flat layout | **Monorepo only** — standardize on `packages/backend` + `packages/frontend`. |
| 2 | v1 backwards compatibility | **Clean break** — v2 is a fresh start. No v1 migration tooling. There are no external v1 users, so this carries zero migration burden. |
| 3 | Spec DSL class names | **New names** — `Model`, `Field`, `Relationship` (not `ModelSpec`, `FieldSpec`, `RelationshipSpec`). |
| 4 | Auth split (spec vs config) | **Split confirmed** — roles/permissions in domain spec (domain truth), provider details (JWT/Keycloak, signup mode, admin panel) in project spec (target blueprint). |
| 5 | GraphQL | **Keep first-class** — REST + GraphQL + MCP all remain as exposure targets. |
| 6 | Create vs Generate separation | **Two-phase model** — `create` scaffolds a fully bootable project (GENERATE_ONCE for entry points, config, infrastructure). `generate` writes files into `packages/` using file strategy: ALWAYS_OVERWRITE for regenerated code, GENERATE_ONCE for user-customizable files (skipped if they exist). Safety is enforced per-file, not per-directory. |
| 7 | Per-field query behavior in spec | **Keep in domain spec** — `filterable`, `filter_operators`, `sortable`, `searchable` are domain truth (which fields can be queried how). Global defaults in project spec, per-field overrides in domain spec. |
| 8 | Lifecycle hooks | **Keep in domain spec** — `before_create`, `after_create`, etc. on Model. Implementation lives in GENERATE_ONCE service extension files. Spec declares intent, user code provides the function body. |
| 9 | Conditional validation | **Keep in domain spec** — `conditional_required`, `conditional_enum` are domain constraints. |
| 10 | Nested create & temporal | **Keep in domain spec** — `nested_create` (relationship list) and `temporal` config are domain-specific model behaviors. |
| 11 | Per-model field visibility | **Keep in domain spec as overrides** — `create_fields`, `update_fields`, `read_fields`, `list_fields` control which fields appear per operation. Domain truth, not infrastructure. |
| 12 | GraphQL subscriptions | **Project spec default + domain spec override** — Global `subscriptions=False` in project spec's GraphQL config, per-model `delivery_overrides=DeliveryOverrides(subscriptions=True)` in domain spec. |
| 13 | Operational CLI commands | **Unchanged** — docker, deploy, devcontainer, ci, proxy, subdomain, auth, admin commands carry over from v1. They are orthogonal to the spec/config/generate refactor. |
| 14 | Frontend per-model UI hints | **Typed overrides on Model** — `frontend_overrides=FrontendOverrides(nav_icon=..., nav_label=..., table_columns=...)` replaces untyped dict. These describe what the model looks like in the UI, not how the UI framework works. |
| 15 | Two spec files vs one | **Two files** — `specs/models.py` (domain) and `specs/project.py` (project blueprint). Domain spec is portable across projects; project spec is project-specific. Separating them makes the mental model clearer: "what exists" vs "what to generate." |
| 16 | Typed overrides vs dict | **Typed sub-models** — `DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides` replace `overrides: dict`. Full Pydantic validation, IDE autocomplete, no silent typos. |
| 17 | `ui_widget` / `ui_widget_props` placement | **Keep on Field in domain spec** — field-specific UI hints like `ui_widget="slider"` with min/max/step are domain-adjacent (they describe the field's semantics). Global widget type registry goes in project spec under `DesignConfig.widgets`. |
| 18 | Project spec format (Python vs TOML) | **Python (Pydantic)** — consistent with domain spec, full IDE support, type safety. Can serialize to TOML/JSON later if needed. |
| 19 | Config scope | **Generator policy only** — `prisme.toml` contains ~15 lines about the tool (strict mode, formatter, paths, tool choices). All target-project decisions (database, auth, frontend, design) live in project spec. |
| 20 | `hidden` field attribute | **Keep as syntactic sugar** — `hidden=True` excludes a field from default list/read views. Avoids enumerating all visible fields just to exclude one. |
| 21 | Exposure channel config pattern | **Each channel is a config object with `enabled` flag** — `rest=RESTConfig(enabled=True)`, `graphql=GraphQLConfig(enabled=True, ...)`, `mcp=MCPConfig(enabled=True)`. Avoids duplicate keyword arguments (e.g., `graphql=True` + `graphql=GraphQLConfig(...)` is invalid Python). Omitting the key or setting `enabled=False` disables the channel. |
| 22 | `FrontendOverrides` generation toggles | **Per-model frontend generation control on `FrontendOverrides`** — `include_in_nav`, `generate_form`, `generate_table`, `generate_detail_view` live on `FrontendOverrides`. Defaults are derived from `operations` (no `create`/`update` → `generate_form=False`, etc.) but can be overridden explicitly. Child models accessed via parent detail views use `include_in_nav=False`. |
| 23 | Domain spec version constant name | **`PRISME_DOMAIN_VERSION`** — distinguishes domain spec from project spec unambiguously. Avoids "SPEC vs PROJECT vs SPEC" confusion. |

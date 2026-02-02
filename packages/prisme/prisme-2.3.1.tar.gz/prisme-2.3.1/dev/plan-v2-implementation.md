# Prisme v2 Refactor — Implementation Plan

**Source:** `dev/PRD-v2-refactor.md` | **Branch:** `refactor_v2`
**Done when:** `~/code/wind-pipeline` project reaches current status and stability on v2.

---

## Overview

Refactor from v1 (all config in StackSpec, `prism` naming, flat output) to v2 (four-layer model, `prisme` naming, file-strategy-per-file safety). Clean break — no v1 backwards compatibility needed.

**Architecture:** Safety is per-file via `FileStrategy` (`ALWAYS_OVERWRITE` vs `GENERATE_ONCE`), not per-directory. There is no separate `generated/` output directory — all output goes into `packages/` with strategy annotations on each `GeneratedFile`.

**Phases:** P0 (Foundation) → P1 (Safety) → P2 (Evolution)

**Validation project:** `~/code/wind-pipeline` — use throughout to verify v2 works end-to-end.

### Status

| Step | Status | Notes |
|------|--------|-------|
| P0.1 Package rename | ✅ Done | All source, tests, templates, docs renamed `prism` → `prisme` |
| P0.2.1 Override models | ✅ Done | `src/prisme/spec/overrides.py` + tests |
| P0.2.2 ProjectSpec | ✅ Done | `src/prisme/spec/project.py` — now uses full AuthConfig + DesignSystemConfig |
| P0.2.3 Domain spec refactor | ✅ Done | v1 per-model exposure fields removed; generators migrated to model.expose + model.has_operation() + overrides; StackSpec stripped to domain-only; GeneratorConfig moved to ProjectSpec |
| P0.2.4 PrismeConfig | ✅ Done | `src/prisme/config/schema.py` + loader + tests. `[project]` section aligned with PRD |
| P0.3.1 Two-spec loader | ✅ Done | `load_domain_spec`, `load_project_spec`, `load_config` |
| P0.3.2 GeneratorContext | ✅ Done | `domain_spec` is now primary field; `spec` kept as deprecated property |
| P0.3.3 Update generators | ✅ Done | All generators use `domain_spec=` + `auth_config`/`design_config`/`testing_config`/`database_config` properties that prefer project_spec |
| P0.4.1 Structure constants | ✅ Done | `src/prisme/project/structure.py` |
| P0.4.2 Simplify FileStrategy | ✅ Done | Removed GENERATE_BASE and MERGE; only ALWAYS_OVERWRITE and GENERATE_ONCE remain |
| P0.4.3 Refactor create | ✅ Done | Generates prisme.toml + specs/project.py + extension stubs |
| P0.4.4 Refactor generate | ✅ Done | Output uses file-strategy-per-file model; generators set strategy on each `GeneratedFile` |
| P0.5 Update templates | ✅ Done | Templates use extracted values via generator properties, not spec.* |
| P0.6 Update manifest | ✅ Done | `.prisme` dir + v2 fields (domain/project/config version, hashes, generators_enabled) |
| P0.7 CLI commands | ✅ Done | `_resolve_spec_file()` helper; all commands use prisme.toml first; legacy fallback preserved |
| P0.8 Exports | ✅ Done | `src/prisme/spec/__init__.py` updated |
| v2 Frontend pages | ✅ Done | Error pages, profile/settings, search, dashboard, import, bulk ops, export, filtering, relationship tabs, admin enhancements |

**Tests:** 802 passed, 85 skipped, 0 failures.

### Deferred Items

Items explicitly deferred to keep P0 stable and unblock validation with `~/code/wind-pipeline`:

1. ~~**P0.2.3 per-model exposure migration**~~ — ✅ Complete.
2. ~~**P0.4.3 app/ scaffolding**~~ — ✅ Extension stubs complete. `packages/` entry points deferred.
3. ~~**P0.4.4 file-strategy output**~~ — ✅ Complete. Generators annotate each `GeneratedFile` with a strategy.
4. **ProjectSpec.auth uses full AuthConfig** — Pragmatic decision: ProjectSpec imports the full `AuthConfig` from `spec.auth` rather than the PRD's simplified version. Works correctly; simplification can happen later if needed.

---

## P0: Foundation

### ✅ P0.1 — Package Rename (`prism` → `prisme`)

Do this first to avoid merge conflicts in all subsequent work.

**Changes:**
- `mv src/prism/ src/prisme/`
- `pyproject.toml`: update `[project.scripts]` to `prisme = "prisme.cli:main"`, `packages = ["src/prisme"]`, `known-first-party = ["prisme"]`
- All `.py` files in `src/` and `tests/`: `from prism.` → `from prisme.`, `import prism` → `import prisme`
- Template headers: update "Prism" references
- `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`

**Verify:** `uv run pytest` passes, `uv run prisme --version` works.

---

### ✅ P0.2 — New Spec Models

#### ✅ P0.2.1 — Typed Override Models
**New file:** `src/prisme/spec/overrides.py`

- `DeliveryOverrides`: page_size, max_page_size, rest_tags, subscriptions
- `FrontendOverrides`: nav_icon, nav_label, table_columns, form_layout, include_in_nav, generate_form/table/detail_view, enable_bulk_actions, filterable_fields, enable_import
- `MCPOverrides`: tool_prefix, tool_descriptions

All with `model_config = {"extra": "forbid"}`.

#### ✅ P0.2.2 — ProjectSpec Model
**New file:** `src/prisme/spec/project.py`

`ProjectSpec` with typed sub-models:
- `BackendConfig` (framework, module_name, port)
- `FrontendConfig` (enabled, framework, port)
- `ExposureConfig` containing `ExposureDefaults`, `RESTConfig`, `GraphQLConfig`, `MCPConfig`, `FrontendExposureConfig`
- `AuthConfig` (provider, admin_panel, signup_mode, signup_domains)
- `DatabaseConfig` (engine, async_driver, url_env)
- `DesignConfig` (theme, dark_mode, icon_set, border_radius, widgets: `WidgetConfig`)
- `TestingConfig` (unit/integration/component/graphql/hook tests, factories, test_database)
- `ExtensionConfig` (services/components/pages strategy, use_protected_regions)

Module-level `PRISME_PROJECT_VERSION = 1`.

#### ✅ P0.2.3 — Refactor Domain Spec Models
**Modify:** `src/prisme/spec/model.py`, `fields.py`, `stack.py`

Added `Model`/`Relationship`/`Field` aliases, added v2 fields (`expose`, `operations`, overrides, create/update/read/list_fields), renamed `enum_values` → `choices` (primary field, `enum_values` kept as validation alias + deprecated property), added `PRISME_DOMAIN_VERSION = 2` to `stack.py`. Old per-channel exposure fields removed; generators migrated.

#### ✅ P0.2.4 — PrismeConfig (TOML schema)
**New file:** `src/prisme/config/schema.py`

- `PrismeConfig`: prisme_version (str), config_version (int)
- `ProjectPaths`: spec_path, project_path
- `GenerationPolicy`: mode (strict/lenient), auto_format
- `ToolChoices`: python_manager, package_manager

**New file:** `src/prisme/config/loader.py` — TOML loading via `tomllib`

**Tests:** `tests/spec/test_overrides.py`, `tests/spec/test_project_spec.py`, `tests/config/test_prisme_config.py`

---

### ✅ P0.3 — Spec Loading & Generator Context

#### ✅ P0.3.1 — Two-Spec Loader
**Modify:** `src/prisme/utils/spec_loader.py`

Add: `load_domain_spec(path) → StackSpec`, `load_project_spec(path) → ProjectSpec`, `load_prisme_config(path) → PrismeConfig`. Version validation with clear error messages.

#### ✅ P0.3.2 — Update GeneratorContext
**Modify:** `src/prisme/generators/base.py`

Added `project_spec` and `config` optional fields, `domain_spec` property alias. Backwards-compatible — existing `spec` field still works.

#### ✅ P0.3.3 — Update All Generators
**Modify:** Every file in `src/prisme/generators/backend/` and `src/prisme/generators/frontend/`

All generators use `domain_spec=` as primary field + `auth_config`/`design_config`/`testing_config`/`database_config` properties that prefer project_spec. Per-model exposure uses `model.expose` + `model.has_operation()`.

---

### ✅ P0.4 — File-Strategy Generation

#### ✅ P0.4.1 — Directory Structure Constants
**New file:** `src/prisme/project/structure.py`

Constants for all standard paths: `PACKAGES_DIR`, `SPECS_DIR`, manifest path, etc.

#### ✅ P0.4.2 — Simplify FileStrategy
**Modify:** `src/prisme/spec/stack.py`

Keep only `ALWAYS_OVERWRITE` (regenerated every time) and `GENERATE_ONCE` (created once, never overwritten). Removed `GENERATE_BASE` and `MERGE`.

#### ✅ P0.4.3 — Refactor `prisme create`
**Modify:** `src/prisme/cli.py` (create command)

Generates prisme.toml + specs/project.py + extension stubs. CLI flags (--database, --template, --auth) write into specs/project.py, not retained as parallel truth.

#### ✅ P0.4.4 — Refactor `prisme generate`
**Modify:** `src/prisme/cli.py` (generate command)

Each generator returns `list[GeneratedFile]` with a `strategy` annotation per file. The CLI respects strategies: `ALWAYS_OVERWRITE` files are regenerated every run, `GENERATE_ONCE` files are only written if they don't already exist. No separate `generated/` directory — output goes into `packages/` paths set by each generator.

---

### ✅ P0.5 — Update Templates

All templates use extracted values via generator properties (e.g., `auth_config`, `design_config`), not raw `spec.*` references. Generators abstract the four-layer model away from templates.

---

### ✅ P0.6 — Update Manifest

**Modify:** `src/prisme/tracking/manifest.py`

Renamed `.prism` → `.prisme` directory, `prism_version` → `prisme_version` field. Manifest stored in `.prisme/` project directory with v2 fields (domain/project/config version, hashes, generators_enabled).

---

### ✅ P0.7 — Update CLI Commands

**Modify:** `src/prisme/cli.py`

`_resolve_spec_file()` helper; all commands use prisme.toml first; legacy fallback preserved.

---

### ✅ P0.8 — Update `spec/__init__.py` Exports

**Modify:** `src/prisme/spec/__init__.py`

Export new public API: `StackSpec`, `Model`, `Field`, `Relationship`, `ProjectSpec`, `BackendConfig`, `FrontendConfig`, `ExposureConfig`, `ExposureDefaults`, `RESTConfig`, `GraphQLConfig`, `MCPConfig`, `FrontendExposureConfig`, `AuthConfig`, `DatabaseConfig`, `DesignConfig`, `WidgetConfig`, `TestingConfig`, `ExtensionConfig`, `DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides`.

---

### ✅ v2 Frontend Pages

Added 9 missing page features across 5 areas:

1. **Error Pages (404/403/500)** — `ErrorPagesGenerator`, unconditional, `GENERATE_ONCE`
2. **Export from List View** — CSV/JSON export buttons on all list pages
3. **Bulk Operations UI** — Conditional on `FrontendOverrides.enable_bulk_actions`
4. **User Profile / Settings** — `ProfilePagesGenerator`, auth-conditional
5. **Global Search Page** — `SearchPageGenerator`, cross-model search
6. **Inline Filtering** — Filter bar via `FrontendOverrides.filterable_fields`
7. **Import Page** — Conditional on `FrontendOverrides.enable_import`
8. **Relationship Browser** — Tabs on detail page for related records
9. **Admin Enhancements** — Roles, Permissions, Activity Log pages
10. **Dashboard** — `DashboardGenerator`, model count cards

**New generators:** `ErrorPagesGenerator`, `ProfilePagesGenerator`, `SearchPageGenerator`, `DashboardGenerator`
**Modified generators:** `PagesGenerator` (export, bulk, filter, import, relationship tabs), `AdminGenerator` (3 new pages), `RouterGenerator` (all new routes)
**New FrontendOverrides fields:** `enable_bulk_actions`, `filterable_fields`, `enable_import`

---

## ✅ P1: Safety & Trust

| Step | Status | Notes |
|------|--------|-------|
| P1.1 Manifest integration | ✅ Done | Hash verification wired into generate command, edited-file detection |
| P1.2 Extension hooks | ✅ Done | Backend + frontend stubs generated with GENERATE_ONCE strategy |
| P1.3 `prisme doctor` | ✅ Done | Config, specs, versions, edited files, deps checks |
| P1.4 Golden regen tests | ✅ Done | GENERATE_ONCE protection, ALWAYS_OVERWRITE regeneration, deterministic output |
| P1.5 Deterministic generation | ✅ Done | Stable sorting, consistent formatting |

**Tests:** 817+ passed, 85 skipped, 0 failures.

---

## P2: Evolution & Teams

### P2.1 — `prisme migrate` command

Spec/config schema migration:
```bash
prisme migrate              # Auto-migrate if safe
prisme migrate --dry-run    # Show what would change
prisme migrate --write      # Write changes
```

Handles: domain spec v1→v2, project spec extraction, config schema upgrades, current state detection.

**Files:** `src/prisme/migration/` module (detector, domain_v1_to_v2, project_extractor), CLI command.

### P2.2 — `prisme plan` / `prisme apply` workflow

Team/CI workflow splitting generation into preview and execution:
```bash
prisme plan              # Preview changes, write .prisme/plan.json
prisme apply             # Execute last plan
```

### P2.3 — Config includes (`prisme.d/*.toml`)

Allow splitting config across multiple TOML files, merged into main config.

### P2.4 — Strict vs lenient generation mode

Wire `PrismeConfig.generation.mode` (strict/lenient) into generator behavior. Strict: fail on warnings. Lenient: warn and continue.

### P2.5 — Error taxonomy with fix-it messages

Enhance `SpecValidationError.errors` with `fix` field containing actionable suggestions. Display in `prisme validate`.

---

## Dependency Order

```
P0.1 (rename)
  → P0.2 (new spec models)
    → P0.3 (loader + generator context + update all generators)
      → P0.4 (file-strategy generation)
        → P0.5 (update templates)
        → P0.6 (manifest)
        → P0.7 (remaining CLI)
        → P0.8 (exports)
        → v2 Frontend pages
```

## Verification

After each P0 sub-step:
- `uv run pytest` — full test suite
- `uv run prisme create test-project --database sqlite` — smoke test create
- `uv run prisme generate` (inside test-project) — smoke test generate
- Inspect output for correct file strategies (`ALWAYS_OVERWRITE` vs `GENERATE_ONCE`)

**Final validation (done = success):**
1. `prisme create wind-pipeline --database postgresql --template saas`
2. Port the wind-pipeline domain spec from `~/code/wind-pipeline`
3. `prisme generate` — produces working project with correct file strategies
4. `prisme dev` — servers start, CRUD works
5. `prisme test` — tests pass
6. Edit a `GENERATE_ONCE` file → `prisme generate` → edited file untouched
7. `prisme validate` — passes
8. Project reaches current wind-pipeline stability level

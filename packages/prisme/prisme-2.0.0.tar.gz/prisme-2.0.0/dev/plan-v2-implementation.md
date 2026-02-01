# Prisme v2 Refactor — Implementation Plan

**Source:** `dev/PRD-v2-refactor.md` | **Branch:** `refactor_v2`
**Done when:** `~/code/wind-pipeline` project reaches current status and stability on v2.

---

## Overview

Refactor from v1 (all config in StackSpec, `prism` naming, flat output) to v2 (four-layer model, `prisme` naming, `generated/` + `app/` separation). Clean break — no v1 backwards compatibility needed.

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
| P0.4.3 Refactor create | ✅ Done | Generates prisme.toml + specs/project.py + app/ extension stubs; packages/ entry points deferred |
| P0.4.4 Refactor generate | ✅ Done | Output routed to `generated/` subdirectory; migration warnings use output_dir |
| P0.5 Update templates | ✅ Done | Templates already use extracted values, not spec.* — generators abstract via properties |
| P0.6 Update manifest | ✅ Done | `.prisme` dir + v2 fields (domain/project/config version, hashes, generators_enabled) |
| P0.7 CLI commands | ✅ Done | `_resolve_spec_file()` helper; all commands use prisme.toml first; legacy fallback preserved |
| P0.8 Exports | ✅ Done | `src/prisme/spec/__init__.py` updated |

**Tests:** 777 passed, 85 skipped, 0 failures.

### Deferred Items

Items explicitly deferred to keep P0 stable and unblock validation with `~/code/wind-pipeline`:

1. ~~**P0.2.3 per-model exposure migration**~~ — ✅ Complete.
2. ~~**P0.4.3 app/ scaffolding**~~ — ✅ Extension stubs complete. `packages/` entry points deferred.
3. ~~**P0.4.4 generated/ output**~~ — ✅ Complete. `output_dir = Path.cwd() / GENERATED_DIR` in generate command.
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
- `FrontendOverrides`: nav_icon, nav_label, table_columns, form_layout, include_in_nav, generate_form/table/detail_view
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

#### 🔶 P0.2.3 — Refactor Domain Spec Models (partial)
**Modify:** `src/prisme/spec/model.py`, `fields.py`, `stack.py`

**Done:** Added `Model`/`Relationship`/`Field` aliases, added v2 fields (`expose`, `operations`, overrides, create/update/read/list_fields), renamed `enum_values` → `choices` (primary field, `enum_values` kept as validation alias + deprecated property), added `PRISME_DOMAIN_VERSION = 2` to `stack.py`.

**Deferred:** Old per-channel exposure fields (`rest`, `graphql`, `mcp`, `frontend`) and StackSpec infrastructure fields (`database`, `graphql`, etc.) kept for now — generators still depend on them. Will be removed when generators are migrated (P0.3.3).

- Rename: `ModelSpec` → `Model`, `FieldSpec` → `Field`, `RelationshipSpec` → `Relationship`
- Keep aliases (`ModelSpec = Model` etc.) for internal generator compat during transition
- `Model`: remove per-channel exposure objects (`rest: RESTExposure`, etc.), replace with:
  - `expose: bool = True`
  - `operations: list[str] = ["create", "read", "update", "delete", "list"]`
  - `delivery_overrides: DeliveryOverrides | None`
  - `frontend_overrides: FrontendOverrides | None`
  - `mcp_overrides: MCPOverrides | None`
- Keep on `Model`: soft_delete, timestamps, lifecycle hooks, nested_create, temporal, create/update/read/list_fields
- `Field`: rename `enum_values` → `choices`, keep all query/UI/validation fields
- `StackSpec`: strip out database, graphql, generator, testing, extensions, widgets, auth, design, traefik, default exposures. Add `PRISME_DOMAIN_VERSION = 2` at module level.

#### ✅ P0.2.4 — PrismeConfig (TOML schema)
**New file:** `src/prisme/config/schema.py`

- `PrismeConfig`: prisme_version (str), config_version (int)
- `ProjectPaths`: spec_path, project_path
- `GenerationPolicy`: mode (strict/lenient), auto_format
- `ToolChoices`: python_manager, package_manager

**New file:** `src/prisme/config/loader.py` — TOML loading via `tomllib`

**Tests:** `tests/spec/test_overrides.py`, `tests/spec/test_project_spec.py`, `tests/config/test_prisme_config.py`

---

### 🔶 P0.3 — Spec Loading & Generator Context (partial)

#### ✅ P0.3.1 — Two-Spec Loader
**Modify:** `src/prisme/utils/spec_loader.py`

Add: `load_domain_spec(path) → StackSpec`, `load_project_spec(path) → ProjectSpec`, `load_prisme_config(path) → PrismeConfig`. Version validation with clear error messages.

#### ✅ P0.3.2 — Update GeneratorContext
**Modify:** `src/prisme/generators/base.py`

**Done:** Added `project_spec` and `config` optional fields, `domain_spec` property alias. Backwards-compatible — existing `spec` field still works.

```python
@dataclass
class GeneratorContext:
    spec: StackSpec           # kept for v1 compat
    output_dir: Path
    dry_run: bool = False
    force: bool = False
    protected_marker: str = "PRISM:PROTECTED"
    backend_module_name: str | None = None
    project_spec: ProjectSpec | None = None   # v2
    config: PrismeConfig | None = None        # v2

    @property
    def domain_spec(self) -> StackSpec:
        return self.spec
```

#### ⬜ P0.3.3 — Update All 24 Generators
**Modify:** Every file in `src/prisme/generators/backend/` and `src/prisme/generators/frontend/`

**Decision:** Clean break — flip `GeneratorContext` to use `domain_spec` as primary field (remove `spec`). Also remove old ModelSpec exposure fields (`rest`, `graphql`, `mcp`, `frontend`) at the same time.

Pattern: `self.context.spec` → `self.context.domain_spec` for models/fields/relationships. Infrastructure config (database, graphql settings, auth, design, testing) read from `self.context.project_spec`. Per-model exposure: check `model.expose` + `project_spec.exposure.{channel}.enabled`.

**Order:** models → schemas → services → rest → graphql → mcp → auth → admin → alembic → types → components → hooks → pages → router → graphql_ops → headless → widgets → design → frontend_auth → frontend_admin → backend_tests → frontend_tests

**Verify:** `uv run pytest tests/generators/` after each generator.

---

### P0.4 — Two-Phase Generation

#### ✅ P0.4.1 — Directory Structure Constants
**New file:** `src/prisme/project/structure.py`

Constants for all standard paths: `GENERATED_DIR`, `APP_DIR`, `PACKAGES_DIR`, `SPECS_DIR`, manifest path, etc.

#### ⬜ P0.4.2 — Simplify FileStrategy
**Modify:** `src/prisme/spec/stack.py`

Keep only `ALWAYS_OVERWRITE` (for `generated/`) and `GENERATE_ONCE` (for `prisme create` scaffolds). Remove `GENERATE_BASE` and `MERGE` (defer to P1 extension hooks).

#### ⬜ P0.4.3 — Refactor `prisme create`
**Modify:** `src/prisme/cli.py` (create command ~line 171)

New flow:
1. Create project dir
2. Write `prisme.toml` (from CLI flags → durable config)
3. Write `specs/models.py` (starter domain spec based on template)
4. Write `specs/project.py` (from CLI flags like --database)
5. Scaffold `app/` with extension stubs (dependencies.py, routers.py, events.py, policies.py)
6. Scaffold `packages/` entry points (main.py with try/except discovery, config.py, database.py)
7. Scaffold infrastructure (docker/, .github/, .devcontainer/)
8. Run initial `prisme generate` to populate `generated/`

CLI flags (--database, --template, --auth) write into specs/project.py, not retained as parallel truth.

#### ✅ P0.4.4 — Refactor `prisme generate`
**Modify:** `src/prisme/cli.py` (generate command ~line 919)

New flow:
1. Load `prisme.toml` → `PrismeConfig`
2. Load `specs/models.py` → `StackSpec` (validate `PRISME_DOMAIN_VERSION`)
3. Load `specs/project.py` → `ProjectSpec` (validate `PRISME_PROJECT_VERSION`)
4. Create `GeneratorContext(output_dir=Path("generated"))`
5. Run enabled generators (based on project_spec exposure flags)
6. Write manifest to `generated/.prisme-manifest.json`
7. Auto-format if configured

**Hard rule:** generate only writes inside `generated/`.

**New templates needed** for scaffolding:
- `templates/jinja2/project/prisme_toml.jinja2`
- `templates/jinja2/project/specs/domain_spec.py.jinja2`
- `templates/jinja2/project/specs/project_spec.py.jinja2`
- `templates/jinja2/project/app/` stubs
- `templates/jinja2/project/packages/` entry points (main.py with discovery pattern)

---

### ⬜ P0.5 — Update Templates

**Modify:** All 237 templates in `src/prisme/templates/jinja2/`

Key context variable changes in all templates:
- `spec.models` → `domain_spec.models`
- `spec.database` → `project_spec.database`
- `spec.graphql` → `project_spec.exposure.graphql`
- `spec.auth` → `project_spec.auth`
- `spec.design` → `project_spec.design`
- `spec.testing` → `project_spec.testing`
- `model.rest.enabled` → `model.expose and project_spec.exposure.rest.enabled`
- `model.graphql.enabled` → `model.expose and project_spec.exposure.graphql.enabled`
- `model.frontend` → merge of `project_spec.exposure.frontend` + `model.frontend_overrides`

Output paths: generators already set `path` on `GeneratedFile`, so templates don't need path changes — the generators handle writing to `generated/`.

**Verify:** Render each template with sample specs, check for Jinja2 errors.

---

### 🔶 P0.6 — Update Manifest (partial)

**Modify:** `src/prisme/tracking/manifest.py`

**Done:** Renamed `.prism` → `.prisme` directory, `prism_version` → `prisme_version` field.

**Deferred:** New fields (`domain_version`, `project_version`, `config_version`, hashes, `generators_enabled`) and moving manifest to `generated/.prisme-manifest.json` — depends on P0.4 two-phase generation.

- Manifest location: `generated/.prisme-manifest.json`
- Add fields: `domain_version`, `project_version`, `config_version`, `domain_hash`, `project_hash`, `config_hash`, `generators_enabled`
- Rename `.prism-manifest.json` → `.prisme-manifest.json`

---

### ⬜ P0.7 — Update Remaining CLI Commands

**Modify:** `src/prisme/cli.py`

- `prisme validate`: validate both specs + config, check version compat
- `prisme dev`/`test`/`db`: read paths from `prisme.toml` + project_spec
- Remove config-affecting CLI flags (--database etc. except on `create`)

---

### ✅ P0.8 — Update `spec/__init__.py` Exports

**Modify:** `src/prisme/spec/__init__.py`

Export new public API: `StackSpec`, `Model`, `Field`, `Relationship`, `ProjectSpec`, `BackendConfig`, `FrontendConfig`, `ExposureConfig`, `ExposureDefaults`, `RESTConfig`, `GraphQLConfig`, `MCPConfig`, `FrontendExposureConfig`, `AuthConfig`, `DatabaseConfig`, `DesignConfig`, `WidgetConfig`, `TestingConfig`, `ExtensionConfig`, `DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides`.

---

## P1: Safety & Trust (outline)

- **P1.1** — Enhanced manifest with hash verification, pre-generation edited-file detection
- **P1.2** — Extension hooks system (backend + frontend stubs, discovery in main.py)
- **P1.3** — `prisme doctor` command (config valid, specs valid, versions compat, no edited generated files, hooks valid, deps match)
- **P1.4** — Golden regeneration tests: generate→edit user→regenerate→user unchanged; spec change→only generated/ changes; deterministic output
- **P1.5** — Deterministic generation (stable model/field sorting, consistent formatting)

## P2: Evolution & Teams (outline)

- **P2.1** — `prisme migrate` (v1→v2 domain spec, extract project spec from old StackSpec)
- **P2.2** — `prisme plan` / `prisme apply` (dry-run diff, plan file, team review workflow)
- **P2.3** — Config includes (`prisme.d/*.toml`), multi-file specs, strict vs lenient mode, MCP tool hooks

---

## Dependency Order

```
P0.1 (rename)
  → P0.2 (new spec models)
    → P0.3 (loader + generator context + update all generators)
      → P0.4 (two-phase generation: create/generate refactor)
        → P0.5 (update templates)
        → P0.6 (manifest)
        → P0.7 (remaining CLI)
        → P0.8 (exports)
```

## Verification

After each P0 sub-step:
- `uv run pytest` — full test suite
- `uv run prisme create test-project --database sqlite` — smoke test create
- `uv run prisme generate` (inside test-project) — smoke test generate
- Inspect `generated/` structure matches PRD section 6.2

**Final validation (done = success):**
1. `prisme create wind-pipeline --database postgresql --template saas`
2. Port the wind-pipeline domain spec from `~/code/wind-pipeline`
3. `prisme generate` — produces working project
4. `prisme dev` — servers start, CRUD works
5. `prisme test` — tests pass
6. Edit `app/backend/extensions/routers.py` → `prisme generate` → `app/` untouched
7. `prisme validate` — passes
8. Project reaches current wind-pipeline stability level

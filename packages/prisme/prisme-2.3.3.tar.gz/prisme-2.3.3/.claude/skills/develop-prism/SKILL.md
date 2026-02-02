---
name: develop-prism
description: Develop features and fix bugs in the Prism framework itself. Use when working on generators, templates, CLI commands, spec models, or tests in the prisme codebase.
---

Guide for contributing to the Prism (`prisme`) codebase — the code generation framework, not generated projects.

## Before You Start

1. Check `dev/roadmap.md` for priorities and dependencies.
2. Check `dev/issues/` and `dev/plans/` for existing context on the area you're touching.

## Setup

```bash
uv sync --all-extras
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

## Development Loop

```bash
uv run pytest -x                        # Run tests, stop on first failure
uv run pytest tests/path/to/test.py     # Run specific test file
uv run ruff check . --fix               # Lint + auto-fix
uv run ruff format .                    # Format
uv run mypy src                         # Type check
uv run mkdocs build --strict            # Build docs (if touching docs)
```

Test markers: `slow`, `e2e`, `docker` — all excluded from default runs. Use `-m slow` etc. to include. Timeout: 120s per test. Async mode: auto.

## Architecture

```
src/prism/
├── cli.py                  # CLI entry point (Click, 58+ commands, 11 groups)
├── spec/                   # Pydantic specification models (StackSpec → ModelSpec → FieldSpec)
│   ├── stack.py            # StackSpec, DatabaseConfig, GeneratorConfig, ExtensionConfig
│   ├── model.py            # ModelSpec, RelationshipSpec, TemporalConfig
│   ├── fields.py           # FieldSpec, FieldType, FilterOperator
│   ├── exposure.py         # RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure
│   ├── auth.py             # AuthConfig, Role, APIKeyConfig, AuthentikConfig
│   ├── design.py           # DesignSystemConfig, ThemePreset, IconSet, FontFamily
│   ├── infrastructure.py   # TraefikConfig
│   └── validators.py       # Cross-model validation
├── generators/             # 30 generator classes
│   ├── base.py             # GeneratedFile, GeneratorContext, GeneratorResult
│   ├── backend/            # 10 generators (models, schemas, services, rest, graphql, mcp, auth, alembic)
│   ├── frontend/           # 11 generators (components, pages, hooks, types, router, design, widgets, auth)
│   ├── infrastructure/     # 1 generator (authentik compose)
│   └── testing/            # 2 generators (backend tests, frontend tests)
├── templates/jinja2/       # 100+ Jinja2 templates mirroring generator structure
├── docker/                 # Docker/Traefik proxy management
├── deploy/                 # Hetzner/Terraform deployment
└── devcontainer/           # Dev container lifecycle
```

### Generator Pipeline

```
StackSpec → GeneratorContext → Generator.generate() → GeneratorResult → files written
```

Every generator:
1. Inherits from the abstract base in `generators/base.py`
2. Implements `generate()` returning a `GeneratorResult`
3. Uses `TemplateRenderer` for Jinja2 processing
4. Creates `GeneratedFile` objects with a `FileStrategy`

### File Strategies

| Strategy | Behavior | Example |
|----------|----------|---------|
| `ALWAYS_OVERWRITE` | Regenerated every time | types, schemas |
| `GENERATE_ONCE` | Created once, never overwritten | custom pages, hooks |
| `GENERATE_BASE` | Base class regenerated, user extension preserved | services, components |
| `MERGE` | Smart merge with conflict markers | schema/router assembly |

### Override Tracking

`ManifestManager` tracks file hashes. When a user modifies a generated file, the `prism review` workflow detects and preserves customizations. Protected regions (`PRISM:PROTECTED` markers) allow inline custom code within generated files.

## Test Structure

```
tests/
├── conftest.py             # sample_field_spec, sample_model_spec, sample_stack_spec fixtures
├── spec/                   # Specification model tests
├── generators/
│   ├── backend/            # Backend generator tests
│   ├── frontend/           # Frontend generator tests
│   └── infrastructure/     # Infrastructure tests
├── cli/                    # CLI command tests
├── e2e/                    # End-to-end tests
├── docker/                 # Docker integration tests
├── deploy/                 # Deployment tests
├── devcontainer/           # Dev container tests
├── tracking/               # Manifest & override tracking tests
└── test_templates/         # Template rendering tests
```

## Code Style

- **Ruff**: line-length 100, target py313, rules `E/W/F/I/UP/B/SIM/TCH/RUF`
- **Ignored**: `E501` (line length handled by formatter), `RUF001`, `RUF012`, `SIM105`
- **Imports**: isort with `prism` as first-party
- **Tests**: `TCH003` ignored (runtime imports allowed)
- **Mypy**: pydantic plugin, `ignore_missing_imports = true`, not strict

## Commit Convention

```
type(scope): description
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`
- **Breaking**: add `!` after type (e.g., `feat!: remove legacy API`)
- **Scopes**: `generators`, `spec`, `cli`, `templates`, `docker`, `deploy`, `tests`, etc.
- Semantic release: `feat` → minor, `fix`/`perf` → patch

## Common Tasks

### Adding a new field to a spec model

1. Add field to the Pydantic model in `src/prism/spec/`
2. Update relevant generators that read this field
3. Update Jinja2 templates if the field affects output
4. Add/update validators in `validators.py` if cross-model rules apply
5. Add tests for the new field behavior

### Adding a new generator

1. Create class in `src/prism/generators/<layer>/`
2. Inherit from base, implement `generate()` → `GeneratorResult`
3. Add Jinja2 templates in `src/prism/templates/jinja2/<layer>/`
4. Register in `cli.py`'s `_run_generators()` pipeline
5. Add tests in `tests/generators/<layer>/`

### Adding a CLI command

1. Add Click command/group in `src/prism/cli.py`
2. Use Rich console for output (spinners, tables, panels)
3. Add tests in `tests/cli/`

### Modifying a Jinja2 template

1. Find template in `src/prism/templates/jinja2/`
2. Update template (templates mirror generator structure)
3. Run affected generator tests to verify output
4. Check `FileStrategy` — if `GENERATE_BASE`, ensure user extensions aren't broken

For the full spec API reference, see the [generate-prism-spec skill](../generate-prism-spec/SKILL.md) and its [reference.md](../generate-prism-spec/reference.md).

## CI/CD

GitHub Actions pipeline: lint → test → docs → e2e → e2e-docker. Semantic release on main merge publishes to PyPI. Pre-push hooks mirror CI locally.

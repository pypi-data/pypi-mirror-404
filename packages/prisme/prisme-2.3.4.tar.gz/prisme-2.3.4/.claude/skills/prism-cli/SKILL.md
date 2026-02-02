---
name: prism-cli
description: Prism CLI for generating full-stack CRUD apps from Pydantic specs. Use when creating projects, generating code, running migrations, managing Docker, deploying, or working with Prism specifications.
---

Prism (`prisme` on PyPI) is a code generation framework that produces full-stack CRUD applications from Pydantic model specifications. Python 3.13+.

Always prefix commands with `uv run` (e.g., `uv run prism generate`).

## Core Workflow

```bash
uv run prism create my-app         # 1. Create project
# Edit specs/models.py             # 2. Define models
uv run prism generate              # 3. Generate code
uv run prism install               # 4. Install deps
uv run prism db init               # 5. Init migrations
uv run prism db migrate            # 6. Run migrations
uv run prism dev                   # 7. Start dev servers
```

## Key Commands

- `prism create <name>` — Create a new project
- `prism generate` — Generate code from specs (`--dry-run` to preview)
- `prism validate` — Validate spec files
- `prism dev` — Start dev servers (backend, frontend, MCP)
- `prism install` — Install dependencies
- `prism test` — Run tests
- `prism db init|migrate|reset|seed` — Database operations
- `prism docker init|logs|shell|down|reset-db|backup-db|restore-db|init-prod|build-prod` — Docker
- `prism review list|diff|show|mark-reviewed|clear|restore` — Code override review
- `prism deploy init|plan|apply|destroy|ssh|logs|status|ssl` — Hetzner/Terraform deployment
- `prism ci init|status|validate|add-docker` — CI/CD pipelines
- `prism devcontainer up|down|shell|logs|status|list|exec|test|migrate|url|generate` — Dev containers
- `prism proxy status|diagnose|restart` — Reverse proxy
- `prism auth login|logout|status` — Authentication
- `prism subdomain list|claim|activate|status|release` — Managed subdomains
- `prism projects list|down-all` — Multi-project management

For the full command reference with descriptions, see [commands.md](commands.md).

## Specification Model

Projects are defined via a `StackSpec` in `specs/models.py`:

```python
from prism.spec import StackSpec, ModelSpec, FieldSpec, FieldType
from prism.spec import RESTExposure, GraphQLExposure, FrontendExposure

stack = StackSpec(
    name="my-app",
    models=[
        ModelSpec(
            name="Customer",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
                FieldSpec(name="email", type=FieldType.STRING, required=True),
            ],
            rest=RESTExposure(enabled=True),
            graphql=GraphQLExposure(enabled=True),
            frontend=FrontendExposure(enabled=True),
        ),
    ],
)
```

### Field Types

`STRING`, `TEXT`, `INTEGER`, `FLOAT`, `DECIMAL`, `BOOLEAN`, `DATETIME`, `DATE`, `TIME`, `UUID`, `JSON`, `ENUM`, `FOREIGN_KEY`

### Relationships

```python
from prism.spec import RelationshipSpec

ModelSpec(
    name="Order",
    fields=[
        FieldSpec(name="customer_id", type=FieldType.FOREIGN_KEY, references="Customer"),
    ],
    relationships=[
        RelationshipSpec(
            name="customer",
            target_model="Customer",
            type="many_to_one",
            back_populates="orders",
        ),
    ],
)
```

## Generated Project Structure

```
project/
├── prism.config.py           # Configuration
├── specs/models.py           # Model specifications
├── packages/
│   ├── backend/src/<pkg>/
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas (generated, do not edit)
│   │   ├── services/
│   │   │   ├── _generated/   # Generated base classes (do not edit)
│   │   │   └── *_service.py  # User extension files (safe to edit)
│   │   ├── api/rest/         # REST endpoints
│   │   ├── api/graphql/      # GraphQL types
│   │   └── mcp_server/       # MCP tools
│   └── frontend/src/
│       ├── types/            # TypeScript types (generated, do not edit)
│       ├── components/
│       │   ├── _generated/   # Generated components (do not edit)
│       │   └── *.tsx         # User extension files (safe to edit)
│       ├── hooks/
│       ├── pages/
│       └── graphql/
```

## Key Rules

- **Never edit** files in `_generated/`, `schemas/`, or `types/` — they are regenerated
- **Safe to edit**: service extension files, component extension files, anything outside `_generated/`
- After changing specs, run `prism generate` then `prism db migrate` if schema changed
- Use `prism generate --dry-run` to preview changes before applying

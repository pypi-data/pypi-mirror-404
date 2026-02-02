# Prism

> See also: [AGENT.md](AGENT.md) (AI agent instructions) | [CONTRIBUTING.md](CONTRIBUTING.md) (development guidelines)
>
> CLI: `uv run prism --help` (install: `uv add prisme`) | Docs: [docs/](docs/) | [prisme.readthedocs.io](https://prisme.readthedocs.io/)

**Quick start for contributors:** `uv sync --all-extras && uv run pre-commit install && uv run pre-commit install --hook-type pre-push`

[![CI](https://github.com/Lasse-numerous/prisme/actions/workflows/ci.yml/badge.svg)](https://github.com/Lasse-numerous/prisme/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Lasse-numerous/prisme/graph/badge.svg?flag=prism-core)](https://codecov.io/gh/Lasse-numerous/prisme)
[![Generated Backend](https://codecov.io/gh/Lasse-numerous/prisme/graph/badge.svg?flag=generated-backend)](https://codecov.io/gh/Lasse-numerous/prisme)
[![Generated Frontend](https://codecov.io/gh/Lasse-numerous/prisme/graph/badge.svg?flag=generated-frontend)](https://codecov.io/gh/Lasse-numerous/prisme)
[![PyPI](https://img.shields.io/pypi/v/prisme)](https://pypi.org/project/prisme/)
[![Documentation](https://img.shields.io/badge/docs-readthedocs-blue)](https://prisme.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **"One spec, full spectrum."**

Prism is a code generation framework that enables defining data models once in Python/Pydantic and generating consistent CRUD operations, list endpoints (with filtering, sorting, pagination), and UI components across the entire stack—without losing your customizations on regeneration.

```bash
prism create my-app && cd my-app && prism install && prism generate && prism test && prism dev
```

## Features

- **Spec as Code**: Define all specifications in Python using Pydantic models
- **Code-First**: Models are the source of truth; everything else is generated
- **Selective Exposure**: Fine-grained control over REST, GraphQL, MCP, and Frontend exposure
- **Build-Time Generation**: Static, inspectable output generated at build time
- **Type Safety**: End-to-end type safety from database to frontend
- **Extend, Don't Overwrite**: Downstream customizations preserved across regenerations
- **Pluggable Widgets**: Default widgets with dependency injection for customization

## Technology Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL / SQLite |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Validation | Pydantic + pydantic-settings |
| REST API | FastAPI |
| GraphQL | Strawberry GraphQL |
| MCP | FastMCP |
| Frontend | Vite + React 19 + TypeScript + Tailwind + PostCSS |
| Testing | pytest (backend) / Vitest + React Testing Library (frontend) |
| CI/CD | GitHub Actions + semantic-release |
| Deployment | Docker + Terraform (Hetzner Cloud) |

## Installation

```bash
# Using uv (recommended)
uv add prisme

# Using pip
pip install prisme
```

## Documentation

Full documentation is available at **[prisme.readthedocs.io](https://prisme.readthedocs.io/)**:

- [Getting Started](https://prisme.readthedocs.io/getting-started/) - Installation and quickstart
- [User Guide](https://prisme.readthedocs.io/user-guide/) - CLI reference, spec guide, extensibility
- [Tutorials](https://prisme.readthedocs.io/tutorials/) - Step-by-step project tutorials
- [API Reference](https://prisme.readthedocs.io/reference/) - Specification class reference
- [Architecture](https://prisme.readthedocs.io/architecture/) - Design principles and internals

## Quick Start

**One-liner** to create, install, generate, test, and start dev:

```bash
prism create my-app && cd my-app && prism install && prism generate && prism test && prism dev
```

### 1. Create a New Project

```bash
prism create my-project
cd my-project
```

This scaffolds a full-stack project with:
- `packages/backend/` - Python/FastAPI backend with SQLAlchemy, Pydantic
- `packages/frontend/` - React + TypeScript + Vite + Tailwind (scaffolded via create-vite)
- `specs/models.py` - Example spec file to define your models

### 2. Define Your Models

Edit `specs/models.py` to define your data models:

```python
# specs/models.py
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    description="Customer Relationship Management System",
    models=[
        ModelSpec(
            name="Customer",
            description="Customer entity",
            soft_delete=True,
            timestamps=True,
            fields=[
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    searchable=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    ui_widget="email",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["active", "inactive", "prospect"],
                    default="prospect",
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["customers"]),
            graphql=GraphQLExposure(enabled=True, use_connection=True),
            mcp=MCPExposure(enabled=True, tool_prefix="customer"),
            frontend=FrontendExposure(enabled=True, nav_label="Customers"),
        ),
    ],
)
```

### 3. Generate Code

> **⚠️ Important:** `prism generate` requires core backend files (`__init__.py`, `main.py`, `config.py`, `database.py`) that are created by `prism create`. If you're setting up manually or in an existing project, you must create these files first. See [Troubleshooting](#troubleshooting) for details.

```bash
prism generate
```

This generates all the backend and frontend code from your spec: models, schemas, services, REST/GraphQL/MCP APIs, TypeScript types, React hooks, and components.

### 4. Start Development

```bash
prism dev
```

For detailed specification options, see the [Model Spec Guide](https://prisme.readthedocs.io/user-guide/spec-guide/).

## CLI Commands

```bash
# Project scaffolding (creates project structure, does NOT generate code from spec)
prism create my-project                    # Create new project with full template
prism create my-project --template minimal # Create minimal backend-only project
prism create my-project --template api-only # Create API project (no frontend)
prism create my-project --template saas    # Create SaaS template with auth
prism create my-project --spec models.py   # Create and copy existing spec file
prism create my-project --database sqlite  # Use SQLite instead of PostgreSQL
prism create my-project --package-manager pnpm  # Use pnpm for frontend
prism create my-project --python-manager poetry # Use poetry for backend
prism create my-project --docker           # Include Docker configuration
prism create my-project --no-install       # Skip dependency installation
prism create my-project --no-git           # Skip git initialization
prism create my-project --no-ci            # Skip CI/CD workflows generation
prism create my-project -y                 # Skip interactive prompts

# Dependency management
prism install                              # Install all dependencies (backend + frontend)
prism install --backend-only               # Install only backend dependencies
prism install --frontend-only              # Install only frontend dependencies

# Code generation (generates code from your spec - run after editing specs/models.py)
prism generate                             # Generate from default spec (specs/models.py)
prism generate --dry-run                   # Preview changes without writing files
prism generate --only graphql              # Generate specific layers only
prism generate --force                     # Force overwrite all files
prism generate --diff                      # Show diff of changes

# Testing
prism test                                 # Run all tests (backend + frontend)
prism test --backend-only                  # Run only backend tests (pytest)
prism test --frontend-only                 # Run only frontend tests (vitest)
prism test --coverage                      # Run with coverage reporting
prism test -- -k test_health               # Pass arguments to pytest

# Development
prism dev                                  # Start all dev servers
prism dev --backend-only                   # Start backend only
prism dev --frontend-only                  # Start frontend only
prism dev --mcp                            # Also start the MCP server
prism dev --watch                          # Watch for spec changes and regenerate
prism dev --quiet                          # Suppress output from servers
prism dev --docker                         # Run in Docker

# Database
prism db init                              # Initialize Alembic for migrations
prism db migrate                           # Create and apply migrations
prism db migrate -m "add users table"      # Create named migration and apply
prism db reset                             # Reset database
prism db reset -y                          # Reset without confirmation
prism db seed                              # Seed with test data

# Validation & Schema
prism validate specs/models.py             # Validate specification
prism schema                               # Generate GraphQL schema SDL
prism schema --output schema.graphql       # Output schema to file
```

**Important:**
- `prism create` scaffolds the project structure and creates core backend files (`__init__.py`, `main.py`, `config.py`, `database.py`)
- `prism generate` generates code from your spec (models, schemas, services, APIs, UI)
- You must run `prism create` first OR manually create core backend files before running `prism generate`
- After creating a project, edit `specs/models.py` to define your models, then run `prism generate`

## Docker Development Environment

Prism provides a containerized development environment using Docker for seamless local development:

```bash
# Create project with Docker support
prism create my-project --docker

# Or add Docker to existing project
cd my-project
prism docker init

# Start everything with Docker
prism dev --docker

# Your app is now running at http://my-project.localhost
```

### Benefits

- **Zero Configuration** - Just run `prism dev --docker`, everything starts automatically
- **No Port Conflicts** - Multiple projects run simultaneously without interference
- **Team Consistency** - Everyone runs the same environment
- **Fast Onboarding** - New developers productive in < 5 minutes
- **Automatic Setup** - Backend, frontend, database, and Redis all configured

### Docker Commands

```bash
# Setup
prism docker init                      # Generate Docker development config
prism docker init --redis              # Include Redis service

# Service Management
prism docker logs [-f] [service]       # View logs
prism docker shell <service>           # Open shell in container
prism docker down                      # Stop all services

# Database Management
prism docker backup-db backup.sql      # Backup database
prism docker restore-db backup.sql     # Restore database
prism docker reset-db                  # Reset database

# Production
prism docker init-prod --domain example.com  # Generate production config
prism docker init-prod --ssl --replicas 3    # With SSL and scaling
prism docker build-prod                      # Build production images
prism docker build-prod --push --registry    # Build and push to registry

# Multi-Project
prism projects list                    # List running projects
prism projects down-all                # Stop all projects
```

### How It Works

- **Shared Reverse Proxy**: One Traefik container routes traffic to all projects
- **Automatic Subdomains**: Each project accessible at `project-name.localhost`
- **Hot Reload**: Full support for backend (uvicorn) and frontend (Vite HMR)
- **Isolated Networks**: Projects don't interfere with each other

For more details, see [Docker Development Guide](https://prisme.readthedocs.io/user-guide/docker-development/).

## Override Management

Prism tracks user modifications to generated files and prevents overwriting your customizations. Use the `prism review` commands to manage these overrides:

```bash
# View overrides
prism review list                      # List all overridden files
prism review list --unreviewed         # Show only unreviewed overrides
prism review summary                   # Show override status summary
prism review diff <file>               # Show diff for specific file
prism review show <file>               # Show full override details

# Manage overrides
prism review mark-reviewed <file>      # Mark override as reviewed
prism review mark-all-reviewed         # Mark all overrides as reviewed
prism review clear                     # Clear reviewed overrides from log
prism review clear --all               # Clear entire log (including unreviewed)
```

## CI/CD Workflows

Prism can generate GitHub Actions CI/CD workflows for your project:

```bash
# Generate CI/CD configuration
prism ci init                          # Generate all CI/CD workflows
prism ci init --no-codecov             # Skip Codecov integration
prism ci init --no-dependabot          # Skip Dependabot config
prism ci init --no-release             # Skip semantic-release setup
prism ci init --no-commitlint          # Skip commitlint config

# Manage CI/CD
prism ci status                        # Check CI/CD setup status
prism ci validate                      # Validate GitHub Actions workflows locally
prism ci add-docker                    # Add Docker build/test workflows
```

Generated workflows include:
- Linting and type checking
- Backend and frontend tests
- Codecov coverage reporting
- Semantic versioning and releases
- Dependabot for dependency updates
- Commitlint for conventional commits

## Cloud Deployment

Prism provides infrastructure-as-code deployment to Hetzner Cloud using Terraform:

```bash
# Initialize deployment
prism deploy init                      # Initialize deployment configuration
prism deploy init --domain example.com # Set production domain
prism deploy init --location fsn1      # Set datacenter location
prism deploy init --redis              # Include Redis in deployment

# Manage infrastructure
prism deploy plan                      # Preview infrastructure changes
prism deploy plan -e staging           # Preview staging environment only
prism deploy apply -e staging          # Apply to staging environment
prism deploy apply -e production       # Apply to production environment
prism deploy destroy -e staging        # Destroy staging infrastructure

# Operations
prism deploy status                    # Show deployment status
prism deploy ssh staging               # SSH into staging server
prism deploy ssh production            # SSH into production server
prism deploy logs staging              # View staging logs
prism deploy logs production -f        # Follow production logs
prism deploy ssl staging --domain example.com  # Setup SSL certificate
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/prism-framework/prism.git
cd prism

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/spec/test_models.py
```

### Code Quality

```bash
# Lint and format
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run mypy src
```

## Project Structure

```
prism/
├── src/
│   └── prism/
│       ├── __init__.py          # Package exports
│       ├── cli.py               # CLI entry point
│       ├── py.typed             # PEP 561 marker
│       ├── spec/                # Specification models
│       │   ├── fields.py        # FieldSpec, FieldType, FilterOperator
│       │   ├── exposure.py      # REST/GraphQL/MCP/Frontend exposure
│       │   ├── model.py         # ModelSpec, RelationshipSpec
│       │   └── stack.py         # StackSpec, configs
│       ├── generators/          # Code generators (16 generators)
│       │   ├── backend/         # Models, schemas, services, REST, GraphQL, MCP
│       │   ├── frontend/        # Types, components, hooks, pages, router
│       │   └── testing/         # Backend and frontend test generators
│       ├── templates/           # Jinja2 templates for code generation
│       │   ├── project/         # Project scaffolding templates
│       │   ├── docker/          # Docker configuration templates
│       │   └── ci/              # CI/CD workflow templates
│       ├── docker/              # Docker compose generation
│       ├── ci/                  # CI/CD workflow generation
│       ├── deploy/              # Cloud deployment (Terraform)
│       └── auth/                # Authentication system generation
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── spec/                    # Spec model tests
│   ├── generators/              # Generator tests
│   └── e2e/                     # End-to-end tests
├── pyproject.toml               # Project configuration
└── README.md
```

## Troubleshooting

### Missing Core Backend Files

If you get a warning about missing core backend files when running `prism generate`:

```
⚠️ Warning: Core backend files are missing:
  • __init__.py - Package initialization
  • main.py - FastAPI application entry point
  • config.py - Application configuration
  • database.py - Database connection and session management
```

**Solution:** These files are created by `prism create`. You have two options:

#### Option 1: Use prism create (Recommended)

Create a new project with the proper structure:

```bash
prism create my-project
cd my-project
```

#### Option 2: Manual Setup

If you're working with an existing project structure, create these files manually:

**`__init__.py`** (in your backend package root, e.g., `packages/backend/src/your_package/`):
```python
"""Your Project Name - Description"""
__version__ = "0.1.0"
```

**`config.py`**:
```python
"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (adjust for your stack)
    database_url: str = "postgresql+asyncpg://user:pass@localhost/db"  # For async PostgreSQL
    # database_url: str = "sqlite+aiosqlite:///./data.db"  # For async SQLite

    # API
    secret_key: str = "change-me-in-production"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

settings = Settings()
```

**`database.py`** (for async databases):
```python
"""Async database configuration."""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session() as session:
        yield session
```

**`main.py`** (for FastAPI with GraphQL):
```python
"""Your API."""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine

# Import routers (will be available after prism generate)
try:
    from .api.rest.router import router as rest_router
    HAS_REST = True
except ImportError:
    HAS_REST = False

try:
    from .api.graphql.schema import get_graphql_router
    HAS_GRAPHQL = True
except ImportError:
    HAS_GRAPHQL = False

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    try:
        from .models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except ImportError:
        pass  # Models will be generated by prism generate
    yield
    await engine.dispose()

app = FastAPI(title="Your API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if HAS_REST:
    app.include_router(rest_router, prefix="/api")
if HAS_GRAPHQL:
    app.include_router(get_graphql_router(), prefix="/graphql")
```

After creating these files, run `prism generate` to generate the rest of your code.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Please format your commit messages as:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`

## License

MIT License - see [LICENSE](LICENSE) for details.

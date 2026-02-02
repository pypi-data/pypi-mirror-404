# CLI Reference

Complete reference for all Prisme CLI commands.

## Global Options

```bash
prism --version  # Show version
prism --help     # Show help
```

## Project Commands

### `prism create`

Create a new Prisme project.

```bash
prism create <project_name> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `project_name` | Name of the project (kebab-case recommended) |

**Options:**

| Option | Description |
|--------|-------------|
| `--template` | Project template: `full` (default), `minimal`, `api-only` |
| `--docker` | Initialize with Docker support |
| `--spec <file>` | Copy existing spec file into project |

**Examples:**

```bash
# Full-stack project
prism create my-app

# Backend-only minimal project
prism create my-api --template minimal

# With Docker support
prism create my-app --docker

# With existing spec file
prism create my-app --spec ../specs/models.py
```

---

### `prism generate`

Generate code from your specification.

```bash
prism generate [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview changes without writing files |
| `--only <layer>` | Generate specific layer only |
| `--spec <file>` | Use specific spec file (default: auto-detect) |

**Layers for `--only`:**

- `models` - SQLAlchemy models
- `schemas` - Pydantic schemas
- `services` - Service layer
- `rest` - REST API endpoints
- `graphql` - GraphQL types and resolvers
- `mcp` - MCP tools
- `frontend` - React components and hooks
- `tests` - Test files

**Examples:**

```bash
# Generate everything
prism generate

# Preview changes
prism generate --dry-run

# Generate only GraphQL
prism generate --only graphql

# Use specific spec file
prism generate --spec specs/v2/models.py
```

---

### `prism validate`

Validate a specification file.

```bash
prism validate [spec_path]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `spec_path` | Path to spec file (optional, auto-detects if omitted) |

**Examples:**

```bash
# Validate default spec
prism validate

# Validate specific file
prism validate specs/models.py
```

---

### `prism install`

Install project dependencies.

```bash
prism install [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--backend-only` | Install only Python dependencies |
| `--frontend-only` | Install only Node.js dependencies |

**Examples:**

```bash
# Install all dependencies
prism install

# Backend only
prism install --backend-only

# Frontend only
prism install --frontend-only
```

---

### `prism dev`

Start development servers.

```bash
prism dev [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--backend-only` | Start only backend server |
| `--frontend-only` | Start only frontend server |
| `--docker` | Use Docker development environment |

**Examples:**

```bash
# Start all servers
prism dev

# Backend only
prism dev --backend-only

# With Docker
prism dev --docker
```

---

### `prism test`

Run tests.

```bash
prism test [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--backend-only` | Run only backend tests (pytest) |
| `--frontend-only` | Run only frontend tests (vitest) |
| `--coverage` | Generate coverage report |

**Examples:**

```bash
# Run all tests
prism test

# With coverage
prism test --coverage

# Backend only
prism test --backend-only
```

---

## Database Commands

### `prism db init`

Initialize Alembic for database migrations.

```bash
prism db init
```

Creates the `alembic/` directory and configuration.

---

### `prism db migrate`

Create and apply database migrations.

```bash
prism db migrate [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `-m <message>` | Migration message (descriptive name) |

**Examples:**

```bash
# Auto-generate and apply migration
prism db migrate

# With descriptive message
prism db migrate -m "add customer status field"
```

---

### `prism db reset`

Reset the database (drops all tables and recreates).

```bash
prism db reset
```

!!! warning
    This deletes all data in the database. Use with caution!

---

### `prism db seed`

Seed the database with test data.

```bash
prism db seed
```

---

## Docker Commands

### `prism docker init`

Initialize Docker configuration for the project.

```bash
prism docker init
```

Creates:

- `docker-compose.dev.yml`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `.dockerignore`

---

### `prism docker logs`

View container logs.

```bash
prism docker logs [options] [service]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `service` | Service name: `backend`, `frontend`, `db`, `redis` |

**Options:**

| Option | Description |
|--------|-------------|
| `-f` | Follow log output |

**Examples:**

```bash
# All logs
prism docker logs

# Follow backend logs
prism docker logs -f backend
```

---

### `prism docker shell`

Open a shell in a container.

```bash
prism docker shell <service>
```

**Examples:**

```bash
prism docker shell backend
prism docker shell db
```

---

### `prism docker down`

Stop all Docker services.

```bash
prism docker down
```

---

### `prism docker reset-db`

Reset the Docker database.

```bash
prism docker reset-db
```

---

### `prism docker backup-db`

Backup the database to a SQL file.

```bash
prism docker backup-db <filename>
```

**Example:**

```bash
prism docker backup-db backup-2024-01-15.sql
```

---

### `prism docker restore-db`

Restore the database from a SQL file.

```bash
prism docker restore-db <filename>
```

**Example:**

```bash
prism docker restore-db backup-2024-01-15.sql
```

---

### `prism docker init-prod`

Initialize production Docker configuration.

```bash
prism docker init-prod
```

---

### `prism docker build-prod`

Build production Docker images.

```bash
prism docker build-prod
```

---

## Project Management Commands

### `prism projects list`

List all running Prisme projects.

```bash
prism projects list
```

---

### `prism projects down-all`

Stop all running Prisme projects.

```bash
prism projects down-all
```

**Options:**

| Option | Description |
|--------|-------------|
| `--volumes`, `-v` | Also remove volumes when stopping |
| `--quiet`, `-q` | Suppress detailed output |

This command:
1. Uses `docker compose down --remove-orphans` for each project
2. Falls back to individual container stops if compose fails
3. Finds and stops orphaned containers not on the proxy network

---

## Review Commands

Commands for reviewing generated changes.

### `prism review list`

List files pending review.

```bash
prism review list [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--unreviewed` | Show only unreviewed files |

---

### `prism review summary`

Show summary of changes.

```bash
prism review summary
```

---

### `prism review mark-reviewed`

Mark a file as reviewed.

```bash
prism review mark-reviewed <file>
```

---

### `prism review mark-all-reviewed`

Mark all files as reviewed.

```bash
prism review mark-all-reviewed
```

---

### `prism review diff`

Show diff for a specific overridden file.

```bash
prism review diff <file>
```

---

### `prism review show`

Show full override details for a file.

```bash
prism review show <file>
```

---

### `prism review clear`

Clear reviewed overrides from the log.

```bash
prism review clear
```

---

### `prism review restore`

Restore generated code, discarding your override.

```bash
prism review restore <file>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--yes`, `-y` | Skip confirmation |

This command replaces your customized code with the originally generated code, effectively rejecting your override. The override is removed from the log after restoration.

---

## CI Commands

### `prism ci init`

Initialize CI/CD configuration.

```bash
prism ci init
```

---

### `prism ci status`

Check CI status.

```bash
prism ci status
```

---

### `prism ci validate`

Validate CI configuration.

```bash
prism ci validate
```

---

### `prism ci add-docker`

Add Docker support to CI workflow.

```bash
prism ci add-docker
```

---

## Environment Variables

Prisme respects these environment variables:

| Variable | Description |
|----------|-------------|
| `PRISM_SPEC_FILE` | Default spec file path |
| `PRISM_BACKEND_PATH` | Override backend output path |
| `PRISM_FRONTEND_PATH` | Override frontend output path |
| `DATABASE_URL` | Database connection string |
| `DEBUG` | Enable debug mode |

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | Spec validation error |
| `4` | Generation error |
| `5` | Test failure |

---

## See Also

- [Quick Start](../getting-started/quickstart.md)
- [Model Specification Guide](spec-guide.md)
- [Docker Development](docker-development.md)

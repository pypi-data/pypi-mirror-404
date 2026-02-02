# Prism CLI — Full Command Reference

All commands should be run with `uv run prism ...`.

## Project & Code Generation

| Command | Description |
|---------|-------------|
| `prism create <name>` | Create a new project with template, package manager, and DX options |
| `prism generate` | Generate code from Pydantic specifications |
| `prism generate --dry-run` | Preview what would be generated without writing files |
| `prism validate` | Validate specification files |
| `prism schema` | Generate GraphQL SDL or output schema |

## Development

| Command | Description |
|---------|-------------|
| `prism dev` | Start development servers (backend, frontend, MCP) |
| `prism install` | Install dependencies (backend, frontend, or both) |
| `prism test` | Run tests with coverage support |

## Database (`prism db`)

| Command | Description |
|---------|-------------|
| `prism db init` | Initialize Alembic for migrations |
| `prism db migrate` | Create/run database migrations |
| `prism db reset` | Reset database |
| `prism db seed` | Seed database with test data |

## Docker (`prism docker`)

| Command | Description |
|---------|-------------|
| `prism docker init` | Generate Docker Compose files |
| `prism docker logs` | View container logs |
| `prism docker shell` | Open shell in container |
| `prism docker down` | Stop containers |
| `prism docker reset-db` | Reset database in containers |
| `prism docker backup-db` | Backup database |
| `prism docker restore-db` | Restore database |
| `prism docker init-prod` | Initialize production setup |
| `prism docker build-prod` | Build production images |

## Code Review (`prism review`)

Manages conflicts between custom code overrides and regenerated code.

| Command | Description |
|---------|-------------|
| `prism review list` | List overridden files |
| `prism review diff` | Show differences |
| `prism review show` | Show file content |
| `prism review mark-reviewed` | Mark as reviewed |
| `prism review mark-all-reviewed` | Mark all as reviewed |
| `prism review clear` | Clear overrides |
| `prism review restore` | Restore generated code |

## Multi-Project (`prism projects`)

| Command | Description |
|---------|-------------|
| `prism projects list` | List projects |
| `prism projects down-all` | Stop all running projects |

## Proxy (`prism proxy`)

| Command | Description |
|---------|-------------|
| `prism proxy status` | Check proxy status |
| `prism proxy diagnose` | Diagnose proxy issues |
| `prism proxy restart` | Restart proxy |

## CI/CD (`prism ci`)

| Command | Description |
|---------|-------------|
| `prism ci init` | Initialize CI workflows |
| `prism ci status` | Check CI status |
| `prism ci validate` | Validate CI configuration |
| `prism ci add-docker` | Add Docker to CI |

## Deployment (`prism deploy`)

| Command | Description |
|---------|-------------|
| `prism deploy init` | Initialize Hetzner/Terraform deployment |
| `prism deploy plan` | Show terraform plan |
| `prism deploy apply` | Apply terraform changes |
| `prism deploy destroy` | Destroy infrastructure |
| `prism deploy ssh` | SSH into deployed instance |
| `prism deploy logs` | View deployment logs |
| `prism deploy status` | Check deployment status |
| `prism deploy ssl` | Configure SSL certificates |

## Auth (`prism auth`)

| Command | Description |
|---------|-------------|
| `prism auth login` | Login to Prism services |
| `prism auth logout` | Logout |
| `prism auth status` | Check auth status |

## Subdomains (`prism subdomain`)

| Command | Description |
|---------|-------------|
| `prism subdomain list` | List managed subdomains |
| `prism subdomain claim` | Claim a subdomain |
| `prism subdomain activate` | Activate subdomain |
| `prism subdomain status` | Check subdomain status |
| `prism subdomain release` | Release subdomain |

## Dev Containers (`prism devcontainer`)

| Command | Description |
|---------|-------------|
| `prism devcontainer up` | Start dev container |
| `prism devcontainer down` | Stop dev container |
| `prism devcontainer shell` | Open shell in dev container |
| `prism devcontainer logs` | View dev container logs |
| `prism devcontainer status` | Check dev container status |
| `prism devcontainer list` | List dev containers |
| `prism devcontainer exec` | Execute command in dev container |
| `prism devcontainer test` | Run tests in dev container |
| `prism devcontainer migrate` | Run migrations in dev container |
| `prism devcontainer url` | Get dev container URL |
| `prism devcontainer generate` | Generate code in dev container |

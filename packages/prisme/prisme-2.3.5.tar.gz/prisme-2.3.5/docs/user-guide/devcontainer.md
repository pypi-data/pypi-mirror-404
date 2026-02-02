# Dev Containers

Prism provides CLI-first dev containers for isolated, reproducible development environments.

## Overview

Dev containers allow you to:

- Start development instantly in a fully configured environment
- Work on multiple projects simultaneously with isolated environments
- Persist your work across container restarts with named volumes
- Access services through Traefik reverse proxy

## Quick Start

```bash
# Start a dev container from a repository
prism devcontainer start https://github.com/user/repo.git

# Open a shell in the container
prism devcontainer shell repo
```

## Commands

### Start a Container

Create and start a new dev container:

```bash
# Basic usage
prism devcontainer start https://github.com/user/repo.git

# With custom name
prism devcontainer start https://github.com/user/repo.git --name myproject

# Specific branch
prism devcontainer start https://github.com/user/repo.git --branch develop

# Skip automatic prism generate
prism devcontainer start https://github.com/user/repo.git --no-generate
```

If you're in a git repository, you can omit the URL:

```bash
cd my-project
prism devcontainer start
```

### Shell Access

Open an interactive shell in a container:

```bash
# As developer user (default)
prism devcontainer shell myproject

# As root (for system-level operations)
prism devcontainer shell myproject --root
```

### List Containers

View all dev containers:

```bash
prism devcontainer list
```

Output shows:
- Container name
- Status (running/stopped)
- Image version
- Creation time

### Stop a Container

Stop a running container (preserves data):

```bash
prism devcontainer stop myproject
```

### Restart a Container

Restart a container:

```bash
prism devcontainer restart myproject
```

### Destroy a Container

Remove a container:

```bash
# Remove container only
prism devcontainer destroy myproject

# Remove container and all volumes (workspace, deps, database)
prism devcontainer destroy myproject --volumes
```

### Build Custom Image

Build a local dev container image:

```bash
# Build with defaults
prism devcontainer build-image

# Custom tag
prism devcontainer build-image --tag v1.0.0

# Custom Python/Node versions
prism devcontainer build-image --python 3.12 --node 20

# Build and push to registry
prism devcontainer build-image --push
```

## What's Included

The dev container image includes:

- **Python 3.13** with `uv` package manager
- **Node.js 22** with `pnpm`
- **PostgreSQL client** for database operations
- **Git, curl, jq, vim** and other utilities

## Volume Persistence

Each container uses named volumes for persistent data:

| Volume | Purpose | Path |
|--------|---------|------|
| `{name}-persist` | Dependencies (venv + node_modules) | `/persist` |
| `{name}-pgdata` | Database data | (PostgreSQL) |

The persist volume uses symlinks to map dependencies back into the workspace:
- `/persist/venv` → `/workspace/.venv`
- `/persist/node_modules` → `/workspace/{frontend_path}/node_modules`

Data persists across container restarts. Use `--volumes` with destroy to remove.

## Traefik Integration

Containers automatically integrate with Prism's Traefik proxy:

| Service | URL |
|---------|-----|
| Frontend | `http://{name}.localhost` |
| API | `http://{name}.localhost/api` |

Make sure the Prism proxy is running:

```bash
prism dev --docker  # Starts proxy automatically
```

## Workflow Example

1. **Start Development**
   ```bash
   prism devcontainer start https://github.com/myorg/myproject.git
   prism devcontainer shell myproject
   ```

2. **Inside Container**
   ```bash
   uv sync
   uv run pytest
   ```

3. **Access Services**
   - Frontend: http://myproject.localhost
   - API: http://myproject.localhost/api

4. **End Session**
   ```bash
   exit  # Leave container (it keeps running)
   prism devcontainer stop myproject  # Stop when done
   ```

## Comparison with VS Code Dev Containers

| Feature | Prism Dev Containers | VS Code Dev Containers |
|---------|---------------------|----------------------|
| Primary Interface | CLI | VS Code |
| IDE Required | No | Yes |
| Pre-installed Tools | uv, pnpm, prism CLI | Varies |
| Multiple Projects | Named volumes | Per-project |
| Traefik Integration | Automatic | Manual |

## Troubleshooting

### Container won't start

Check Docker is running:
```bash
docker info
```

### Can't access services

Ensure the Prism proxy is running:
```bash
docker ps | grep prism-proxy
```

Start it if needed:
```bash
prism dev --docker
```

### Permission issues

Use `--root` for system-level operations:
```bash
prism devcontainer shell myproject --root
apt-get update && apt-get install something
```

### Reset container completely

```bash
prism devcontainer destroy myproject --volumes
prism devcontainer start https://github.com/user/repo.git --name myproject
```

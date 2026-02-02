# Docker Development Environment

This guide covers using Prism's Docker-based development environment for local development.

## Overview

Prism provides a containerized development environment that eliminates common pain points:

- **No port conflicts** - Multiple projects run simultaneously without interference
- **Consistent environments** - Same setup across all team members
- **Simple onboarding** - New developers productive in minutes
- **Zero configuration** - Docker handles backend, frontend, database, and Redis

## Quick Start

### Prerequisites

- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
- Docker Compose V2 (bundled with Docker Desktop)
- Port 80 available for Traefik reverse proxy

**Installation guides:**
- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Docker Engine for Linux](https://docs.docker.com/engine/install/)

### Starting Development Environment

```bash
# Create a new Prism project with Docker support
prism create myproject --docker

# Or add Docker to an existing project
cd myproject
prism docker init

# Start all services with Docker
prism dev --docker
```

That's it! Your application is now running at `http://myproject.localhost`.

## How It Works

### Architecture

Prism uses a **shared reverse proxy** (Traefik) to route traffic to multiple projects:

```
┌─────────────────────────────────────────┐
│     http://myproject.localhost          │
│              ↓                           │
│     Traefik Reverse Proxy (Port 80)     │
│              ↓                           │
│     ┌────────────────────────────┐      │
│     │  Project: myproject        │      │
│     │  • Frontend (React + Vite) │      │
│     │  • Backend (FastAPI)       │      │
│     │  • PostgreSQL Database     │      │
│     │  • Redis (optional)        │      │
│     └────────────────────────────┘      │
└─────────────────────────────────────────┘
```

**Key benefits:**
- One proxy for all projects (runs on port 80 only once)
- Each project gets its own subdomain: `project-name.localhost`
- Services communicate internally (no port mapping needed)
- Automatic service discovery via Docker labels

### Generated Files

Running `prism docker init` generates:

- **docker-compose.dev.yml** - Service definitions
- **Dockerfile.backend** - Python backend container
- **Dockerfile.frontend** - Node.js frontend container
- **.dockerignore** - Files to exclude from Docker builds

## Docker Commands

### Service Management

```bash
# Start all services
prism dev --docker

# Stop all services
prism docker down

# View logs (all services)
prism docker logs

# View logs (specific service)
prism docker logs backend

# Follow logs in real-time
prism docker logs -f

# Open shell in backend container
prism docker shell backend

# Open shell in frontend container
prism docker shell frontend

# Open shell in database container
prism docker shell db
```

### Database Management

```bash
# Reset database (WARNING: deletes all data)
prism docker reset-db

# Backup database to SQL file
prism docker backup-db backup.sql

# Restore database from SQL file
prism docker restore-db backup.sql
```

### Multi-Project Management

```bash
# List all running Prism projects
prism projects list

# Stop all running projects
prism projects down-all

# View Traefik dashboard
open http://traefik.localhost:8080
```

## Development Workflow

### Typical Development Session

```bash
# Start your project
cd myproject
prism dev --docker

# Project starts, shows URLs:
# ✓ All services healthy
#   Application: http://myproject.localhost
#   API Docs:    http://myproject.localhost/api/docs
#   Traefik:     http://traefik.localhost:8080

# In another terminal, view logs
prism docker logs -f backend

# Make code changes - hot reload works automatically
# Backend: uvicorn --reload
# Frontend: vite with HMR

# When done, stop services
prism docker down
```

### Working on Multiple Projects

```bash
# Terminal 1: Project A
cd projectA
prism dev --docker
# → http://projectA.localhost

# Terminal 2: Project B
cd projectB
prism dev --docker
# → http://projectB.localhost

# List all running projects
prism projects list

# Clean up all projects
prism projects down-all
```

## Configuration

### Docker Compose Customization

Edit `docker-compose.dev.yml` to customize:

```yaml
services:
  backend:
    # Add environment variables
    environment:
      - DEBUG=1
      - LOG_LEVEL=debug

    # Expose additional ports
    ports:
      - "8001:8001"

    # Add volumes
    volumes:
      - ./data:/app/data

  frontend:
    # Override dev server settings
    command: npm run dev -- --host 0.0.0.0 --port 3000
```

### Adding Redis

Edit `docker-compose.dev.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME}_redis
    volumes:
      - ${PROJECT_NAME}_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - default
      - prism_proxy

volumes:
  ${PROJECT_NAME}_redis_data:
```

## Troubleshooting

### Port 80 Already in Use

If you see "port 80 is already allocated":

```bash
# Check what's using port 80
sudo lsof -i :80

# Stop conflicting service (e.g., Apache)
sudo systemctl stop apache2  # Linux
sudo apachectl stop          # macOS

# Or configure Traefik to use a different port
# Edit ~/.prism/docker/traefik.yml
```

### Services Won't Start

```bash
# Check Docker is running
docker info

# Check for errors
prism docker logs

# Rebuild containers
prism dev --docker --build

# Clean up and start fresh
prism docker down
docker system prune -a  # WARNING: removes all unused Docker data
prism dev --docker
```

### Slow Performance on macOS

Docker on macOS has slower file I/O due to volume mounts. To improve:

1. **Use :cached mount option** (already configured in templates):
   ```yaml
   volumes:
     - ./backend:/app/backend:cached
   ```

2. **Increase Docker resources**:
   - Docker Desktop → Settings → Resources
   - Increase CPUs and Memory

3. **Consider Mutagen** (for large projects):
   ```bash
   # Install Mutagen
   brew install mutagen-io/mutagen/mutagen

   # Use Mutagen volumes (advanced)
   # See: https://mutagen.io/documentation/introduction
   ```

### Database Connection Issues

```bash
# Check database is healthy
prism docker logs db

# Try resetting the database
prism docker reset-db

# Check database from shell
prism docker shell db
psql -U postgres -d myproject
\dt  # List tables
```

### Can't Access Application

```bash
# 1. Check if proxy is running
docker ps | grep prism-proxy

# 2. Restart proxy if needed
docker stop prism-proxy
prism dev --docker  # Proxy will auto-start

# 3. Check Docker networks
docker network ls | grep prism

# 4. Verify Traefik labels
docker inspect myproject_frontend | grep traefik
```

## Performance Considerations

### Resource Usage

Each project typically uses:
- **CPU**: 10-20% idle, 50-100% during builds
- **Memory**: ~2GB (backend + frontend + DB + Redis)
- **Disk**: ~500MB for images, data volumes grow over time

**Recommendations:**
- Minimum: 8GB RAM for 2-3 projects
- Optimal: 16GB+ RAM for 5+ projects

### Build Times

- **Initial build**: 2-3 minutes (downloads base images, installs dependencies)
- **Rebuild with cache**: 10-30 seconds
- **No-cache rebuild**: 2-3 minutes

**Optimization tips:**
- Don't use `--build` flag unless necessary
- Layer caching is automatic (dependencies cached separately from code)
- Multi-stage builds keep images small

## Best Practices

### Do's

✅ **Use Docker for team consistency** - Everyone runs the same environment

✅ **Commit docker-compose.dev.yml** - Share configuration with team

✅ **Use .dockerignore** - Exclude unnecessary files from builds

✅ **Monitor resource usage** - Stop unused projects with `prism projects down-all`

✅ **Back up databases** - Before major migrations: `prism docker backup-db`

### Don'ts

❌ **Don't commit .env files** - Keep secrets out of version control

❌ **Don't use force flags** - Avoid `docker system prune -a` unless necessary

❌ **Don't run too many projects** - Stop unused ones to conserve resources

❌ **Don't skip health checks** - They ensure services are ready before connecting

## Comparison: Docker vs Native

| Feature | Docker | Native |
|---------|--------|--------|
| **Setup Time** | 5 minutes | 30-60 minutes |
| **Consistency** | Identical across machines | Varies by OS/setup |
| **Port Conflicts** | None (isolated networks) | Common |
| **Performance** | Good (great on Linux) | Excellent |
| **Hot Reload** | Full support | Full support |
| **Multiple Projects** | Easy (subdomains) | Port juggling |
| **Dependencies** | Containerized | System-wide |

**Use Docker if:**
- Working on multiple projects
- Team development (consistency)
- New to the codebase (fast onboarding)

**Use Native if:**
- Maximum performance required
- Docker not available
- Debugging at system level

## Advanced Topics

### Custom Networks

Connect services across projects:

```yaml
networks:
  prism_proxy:
    external: true
  shared_services:
    external: true
    name: my_shared_network
```

### Production Builds

For production-ready Docker images:

```dockerfile
# Multi-stage build
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend ./backend
ENV PATH="/app/.venv/bin:$PATH"
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app"]
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and test
        run: |
          docker-compose -f docker-compose.dev.yml build
          docker-compose -f docker-compose.dev.yml run backend pytest
          docker-compose -f docker-compose.dev.yml run frontend npm test
```

## Getting Help

If you encounter issues:

1. Check this documentation
2. Search GitHub issues: https://github.com/anthropics/prism/issues
3. Run `prism docker logs` to see error messages
4. Ask for help with detailed error logs

## Next Steps

- Learn about [Spec-Driven Development](spec-guide.md)
- Explore [Prism CLI Commands](cli-reference.md)
- Contribute to [Prism on GitHub](https://github.com/anthropics/prism)

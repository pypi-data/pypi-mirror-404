# CLI Command Audit — PRD v2 Four-Layer Compliance

## Principle

Per `dev/PRD-v2-refactor.md`, the four layers are:
1. **CLI** — execution only, no durable output decisions
2. **Domain Spec** (`specs/models.py`) — models and per-model behavior
3. **Project Spec** (`specs/project.py`) — infrastructure, exposure defaults, extensions
4. **Prisme Config** (`prisme.toml`) — generator policy, tool preferences

**Rule**: CLI flags must NOT control the shape of durable generated output. If a flag changes what gets generated, it belongs in a spec or config file.

## Violations Found

### 1. `deploy init` — HIGH
**File**: `src/prisme/cli.py` (deploy group)
**Flags**: `--provider`, `--region`, `--domain`, `--staging`
**Problem**: Infrastructure decisions (which cloud provider, region, domain) are CLI flags that determine which deployment files are generated.
**Fix**: Add `ProjectSpec.deploy` section. `prisme generate` reads it. Remove `deploy init` command.

### 2. `ci init` — HIGH
**File**: `src/prisme/cli.py` (ci group)
**Flags**: `--provider`, `--test`, `--lint`, `--type-check`, `--deploy`
**Problem**: CI feature toggles control generated GitHub Actions / GitLab CI files via CLI flags.
**Fix**: Add `ProjectSpec.ci` section. `prisme generate` reads it. Remove `ci init` command.

### 3. `docker init` — MEDIUM
**File**: `src/prisme/cli.py` (docker group)
**Flags**: `--redis`, `--mcp`
**Problem**: Service inclusion flags control which services appear in generated docker-compose.
**Fix**: Already partially in WorkspaceConfig. Formalize as `ProjectSpec.docker` or `prisme.toml [docker]`.

### 4. `docker init-prod` — MEDIUM
**File**: `src/prisme/cli.py` (docker group)
**Flags**: `--domain`, `--replicas`
**Problem**: Production docker config controlled by CLI flags.
**Fix**: Move to `ProjectSpec.deploy` or `ProjectSpec.docker.production`.

### 5. `create` DX flags — LOW
**File**: `src/prisme/cli.py` (create command)
**Flags**: `--auth`, `--graphql`, `--redis`, `--mcp`
**Problem**: Scaffold choices aren't persisted into `prisme.toml` / `ProjectSpec`. Re-scaffolding loses them.
**Fix**: `create` should write chosen options into generated spec files so they're the source of truth.

## Compliant Commands (no changes needed)
- `generate` — reads specs, no durable flags
- `dev` — runtime only (ports, watch mode)
- `devcontainer up/down/shell/exec/logs/status/list` — runtime only
- `test` — runtime only
- `db migrate/upgrade/seed` — runtime only

## Implementation Plan

### Step 1: Add ProjectSpec sections
**File**: `src/prisme/spec/project.py`
- Add `DeployConfig` model: `provider`, `region`, `domain`, `staging`
- Add `CIConfig` model: `provider`, `test`, `lint`, `type_check`, `deploy`
- Add `DockerConfig` model: `include_redis`, `include_mcp`, `production` (domain, replicas)
- Wire into `ProjectSpec` as optional fields

### Step 2: Add generators for deploy/CI/docker
**Files**: `src/prisme/generators/deploy.py`, `ci.py`, `docker.py`
- Read from `ProjectSpec` instead of CLI args
- Integrate into main `prisme generate` pipeline

### Step 3: Deprecate old CLI commands
**File**: `src/prisme/cli.py`
- `deploy init` → print deprecation warning pointing to `ProjectSpec.deploy`
- `ci init` → print deprecation warning pointing to `ProjectSpec.ci`
- `docker init` → print deprecation warning pointing to `ProjectSpec.docker`
- Keep commands for one minor version, then remove

### Step 4: Update `create` scaffolding
**File**: `src/prisme/cli.py` + scaffold templates
- Write `--auth`, `--graphql`, `--redis`, `--mcp` choices into generated `specs/project.py`

## Verification
```bash
cd ~/code/prism
uv run pytest tests/ -x
uv run mypy src/prisme/
# Test that ProjectSpec accepts new sections
uv run python -c "from prisme.spec.project import ProjectSpec; p = ProjectSpec(name='test', deploy={'provider': 'fly'}); print(p.deploy)"
# Test generate reads deploy/ci config
cd ~/code/wind-pipeline/app && uv run --project ~/code/prism prisme generate
```

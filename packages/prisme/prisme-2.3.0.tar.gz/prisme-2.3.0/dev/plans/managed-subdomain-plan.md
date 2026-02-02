# Plan: Managed Subdomain + HTTPS (madewithpris.me)

**Status**: In Progress (Phases 0-5 Complete)
**Author**: Prism Core Team
**Created**: 2026-01-26
**Updated**: 2026-01-26
**Revision Note**: Phase 5 complete - Full integration testing, CI/CD, pre-commit hooks, documentation
**Priority**: MEDIUM-HIGH
**Roadmap Reference**: Priority 15
**Domain**: madewithpris.me (GoDaddy)
**Repository**: `/home/lassethomsen/code/prisme-saas/`

## Overview

Provide managed `*.madewithpris.me` subdomains with automatic HTTPS for Prism projects deployed to Hetzner. This is **not** managed hosting—users bring their own Hetzner server, and MadeWithPris.me provides DNS + SSL convenience.

**Key Value Proposition**: Spin up a production-ready app at `https://myapp.madewithpris.me` in under 5 minutes with a Hetzner account.

**Implementation Strategy**: Build prisme-saas using existing Prism framework features, adding only the API key authentication preset that's currently missing.

## Goals

### Framework Goals (Prism)
- API key authentication preset (the only missing framework feature)

### Existing Framework Features (No Work Needed)
- `prism docker init` / `prism docker init-prod` - Already implemented
- `prism ci init` - Already implemented with GitHub Actions support
- `prism deploy init` - Already implemented with Hetzner/Terraform support

### SaaS Goals (madewithpris.me)
- Users can claim a subdomain (e.g., `myapp.madewithpris.me`) via madewithpris.me API
- DNS A record automatically points to user's Hetzner server IP (GoDaddy DNS)
- User's Traefik handles Let's Encrypt SSL provisioning
- CLI integration for seamless `prism deploy` workflow

## Non-Goals

- **No managed compute**: Users deploy to their own Hetzner servers
- **No central proxy**: Traffic goes directly to user's server (no bandwidth costs)
- **No database hosting**: Users manage their own PostgreSQL
- **No usage-based billing** (for MVP): Simple free tier or flat subscription

## Architecture

### Infrastructure Approach (Self-Hosted on Hetzner)

Based on the Authentik integration pattern (Priority 12):
- **GoDaddy DNS** for DNS record management (madewithpris.me domain)
- **Traefik** with Let's Encrypt for SSL termination
- **Terraform** with Hetzner provider for infrastructure-as-code
- All services self-hosted on Hetzner VM

### System Overview

```mermaid
flowchart TB
    subgraph Prisme["MadeWithPris.me SaaS (Built with Prism)"]
        Auth[API Key Auth<br/>MVP: Single Admin Key]
        API[Subdomain API]
        DNS[GoDaddy DNS]
        DB[(PostgreSQL<br/>Subdomains)]
    end

    subgraph User["User's Environment"]
        CLI[Prism CLI]
        Hetzner[Hetzner Server]
        Traefik[Traefik<br/>Let's Encrypt]
        App[Prism App]
    end

    subgraph Internet["Internet"]
        Browser[User's Browser]
        LE[Let's Encrypt]
    end

    CLI -->|1. prism auth login| Auth
    CLI -->|2. prism subdomain claim myapp| API
    API -->|3. Create A record| DNS
    CLI -->|4. prism deploy apply| Hetzner
    Hetzner --> Traefik
    Traefik -->|5. Request cert| LE
    Traefik --> App

    Browser -->|myapp.madewithpris.me| DNS
    DNS -->|A record| Hetzner
    Hetzner --> Traefik
    Traefik --> App

    style DNS fill:#f39c12,color:white
    style Traefik fill:#4caf50,color:white
    style Auth fill:#3498db,color:white
```

---

## Implementation Phases

### Phase 0: Framework Prerequisites (Prism) - COMPLETE

The only missing framework feature needed for prisme-saas.

#### 0.1: API Key Authentication Preset

Simple API key authentication for backend services.

**Specification**:
```yaml
# prism.yaml
authentication:
  preset: api_key  # api_key | jwt | oidc | none
  api_key:
    header: Authorization
    scheme: Bearer
    env_var: API_KEY
```

**Generated Code**:
- `auth/api_key.py` - Bearer token verification dependency
- Middleware to protect routes
- Environment variable configuration

**Tasks**:
- [x] Add `APIKeyConfig` to spec (`src/prism/spec/auth.py`)
- [x] Add `preset` field to `AuthConfig` (supports `jwt` or `api_key`)
- [x] Create API key auth template (`src/prism/templates/jinja2/backend/auth/api_key/`)
- [x] Create `APIKeyAuthGenerator` (`src/prism/generators/backend/api_key_auth.py`)
- [x] Generate auth middleware
- [x] Update validators to skip User model validation for API key preset
- [x] Write tests (`tests/generators/backend/test_api_key_auth_generator.py`)

**Implementation Notes**:
- Added `APIKeyConfig` class with fields: `header`, `scheme`, `env_var`, `allow_multiple_keys`
- `AuthGenerator` (JWT) now skips when `preset != "jwt"`
- `APIKeyAuthGenerator` generates when `preset == "api_key"`
- Templates generate: `api_key_service.py`, `middleware/api_key.py`, init files

---

### Phase 1: Core DNS Functionality (prisme-saas) - COMPLETE

**Goal**: Validate framework features by building prisme-saas.

**Location**: `/home/lassethomsen/code/prisme-saas/`

#### 1.1: Create prisme-saas Project

```bash
mkdir prisme-saas && cd prisme-saas
prism create . --template api-only --database postgresql
```

**Tasks**:
- [x] Create prisme-saas project structure
- [x] Write Subdomain model spec with API key auth (`specs/models.py`)
- [x] Generate code and infrastructure (using existing `prism generate`)
- [x] Implement HetznerDNSService (`packages/backend/src/prisme_api/services/hetzner_dns.py`)
- [x] Extend subdomain routes with DNS integration (`packages/backend/src/prisme_api/api/rest/subdomain.py`)
- [x] Add reserved name validation (50+ reserved names)
- [ ] Deploy to Hetzner
- [ ] Manual testing: claim → set IP → verify DNS

**Implementation Notes**:
- Custom endpoints: `/subdomains/claim`, `/subdomains/{name}/activate`, `/subdomains/{name}/status`, `/subdomains/{name}/release`
- HetznerDNSService supports create/update/delete A records and propagation checking
- Reserved subdomain list includes: www, api, admin, app, mail, etc.

---

### Phase 2: Test Script & Validation - COMPLETE

**Goal**: Automated testing of core flow.

**Tasks**:
- [x] Write test-dns-flow.sh script (`scripts/test-dns-flow.sh`)
- [ ] Run tests against live deployment
- [ ] Document any issues

**Implementation Notes**:
- Script tests: claim → activate → status → wait for propagation → release
- Supports both local (`http://localhost:8000`) and production (`https://api.madewithpris.me`) URLs

---

### Phase 3: CLI Integration - COMPLETE

**Goal**: Seamless CLI workflow for subdomain management.

**New CLI Commands** (added to `src/prism/cli.py`):
```bash
# Authentication
prism auth login              # Store API key (prompts for key, validates with API)
prism auth logout             # Remove stored credentials
prism auth status             # Show current auth status

# Subdomain Management
prism subdomain list          # List claimed subdomains
prism subdomain claim <name>  # Claim a subdomain
prism subdomain activate <name> --ip <ip>  # Activate with IP
prism subdomain status <name> # Check DNS propagation
prism subdomain release <name> # Release subdomain
```

**Tasks**:
- [x] Add `prism subdomain` command group
- [x] Add `prism auth` command group
- [x] Store API key in `~/.config/prism/credentials.json`
- [ ] Modify `prism deploy init` for madewithpris.me detection
- [ ] Modify `prism deploy apply` for subdomain IP update
- [ ] Write CLI tests

**Implementation Notes**:
- Credentials stored with restrictive permissions (0600)
- API key validated on login via test request to `/subdomains`
- `subdomain release` requires confirmation

---

### Phase 4: Auth & User Accounts - COMPLETE (Spec Only)

**Goal**: Multi-user support with proper authentication.

**Additional Models** (added to `specs/models.py`):
- `User` model with: email, password_hash (hidden), email_verified, mfa_enabled, mfa_secret, subdomain_limit, is_admin
- `APIKey` model with: user_id (FK), key_hash (hidden), key_prefix, name, last_used_at, expires_at, is_active
- `Subdomain` updated with: owner_id (FK to User)

**Tasks**:
- [x] Add User model with email verification fields
- [x] Add TOTP-based MFA fields (mfa_enabled, mfa_secret)
- [x] Add API key model (multiple keys per user)
- [x] Associate subdomains with users (owner_id FK)
- [x] Add subdomain_limit field for rate limiting
- [ ] Implement MFA verification logic
- [ ] Implement email verification flow
- [ ] Implement user-scoped API key authentication

---

### Phase 5: Full Integration Testing - COMPLETE

**Goal**: Complete E2E test suite with CI/CD.

**What Was Implemented**:

1. **Pre-commit Hooks** (`.pre-commit-config.yaml`):
   - Ruff linting and formatting
   - Conventional commit validation
   - Trailing whitespace / end-of-file fixes
   - YAML validation
   - Pre-push pytest execution

2. **CI/CD Workflows**:
   - `.github/workflows/ci.yml` - Lint, test, docs, e2e jobs (matching main prism project)
   - `.github/workflows/release.yml` - python-semantic-release for versioning

3. **Test Suite** (66 tests passing):
   - Unit tests: `tests/unit/test_subdomain_service.py`, etc.
   - Integration tests: `tests/integration/test_subdomain_api.py`
   - Custom API tests: `tests/integration/test_subdomain_custom_api.py` (17 tests for claim/activate/status/release)
   - GraphQL tests: `tests/graphql/`
   - Factory-boy fixtures with valid subdomain patterns

4. **Documentation**:
   - MkDocs with Material theme (`mkdocs.yml`)
   - API reference, CLI reference, getting started guides
   - All docs updated with madewithpris.me domain

5. **Docker Configuration** (via `prism docker init`):
   - `docker-compose.dev.yml` with Traefik labels
   - `Dockerfile.backend` - Python 3.13 slim with uv
   - `.dockerignore` for build optimization

**Tasks**:
- [x] Write API integration tests (17 custom endpoint tests)
- [x] Set up pre-commit hooks (matching main prism project)
- [x] Create CI workflow (lint → test → docs → e2e)
- [x] Generate Docker configuration (`prism docker init`)
- [x] All 66 tests passing, lint clean
- [ ] Deploy to production and run E2E tests

---

### Phase 6: Documentation - NOT STARTED

**Goal**: User-facing documentation.

**Tasks**:
- [ ] User guide: "Deploy to madewithpris.me in 5 minutes"
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Troubleshooting guide (DNS, SSL issues)
- [ ] Update main Prism docs with madewithpris.me integration
- [ ] Landing page for madewithpris.me

---

## Project Structure

### prisme-saas (Validation Project)

```
prisme-saas/
├── specs/
│   └── models.py                    # Prism specification (User, APIKey, Subdomain)
├── packages/
│   └── backend/
│       └── src/
│           └── prisme_api/
│               ├── services/
│               │   ├── _generated/  # Auto-generated
│               │   ├── subdomain.py # Extended service (get_by_name)
│               │   └── hetzner_dns.py # Custom DNS service
│               ├── auth/
│               │   └── api_key_service.py  # Generated from preset
│               ├── middleware/
│               │   └── api_key.py   # Generated middleware
│               └── api/rest/
│                   ├── _generated/  # Auto-generated
│                   └── subdomain.py # Custom endpoints (claim, activate, status, release)
├── scripts/
│   └── test-dns-flow.sh            # DNS flow validation script
├── .env.example                     # Environment variables template
├── pyproject.toml
└── prism.config.py
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/madewithprisme

# GoDaddy DNS (production)
# Note: DNS service currently uses Hetzner API pattern, will need GoDaddy adapter
HETZNER_DNS_API_TOKEN=<token>
HETZNER_DNS_ZONE_ID=<zone-id>

# Authentication (MVP)
PRISME_ADMIN_API_KEY=prisme_live_sk_xxxxx

# Domain Configuration
BASE_DOMAIN=madewithpris.me

# SSL
SSL_EMAIL=admin@madewithpris.me
```

---

## Effort Summary

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 0. Framework Prerequisites | API key auth preset only | 0.5 weeks | ✅ COMPLETE |
| 1. Core DNS Functionality | prisme-saas with DNS integration | 1 week | ✅ COMPLETE |
| 2. Test Script & Validation | Validate DNS flow works | 0.5 weeks | ✅ COMPLETE |
| 3. CLI Integration | `prism subdomain` commands | 1 week | ✅ COMPLETE |
| 4. Auth & User Accounts | MFA, email verification, multi-user | 2 weeks | ✅ SPEC COMPLETE |
| 5. Full Integration Testing | Tests, CI/CD, pre-commit, docs | 0.5 weeks | ✅ COMPLETE |
| 6. Production Deployment | Deploy to Hetzner, live testing | 0.5 weeks | 🔴 NOT STARTED |
| **Total** | | **6 weeks** | **~85% Complete** |

### Recent Commits (prisme-saas)

| Commit | Description |
|--------|-------------|
| `cb04822` | feat: rebrand to madewithpris.me domain |
| `908962c` | feat(docker): use prism-generated Docker configuration |
| `0751ee8` | chore: add site/ to .gitignore |
| `a29d8bb` | feat: initial prisme-saas project with Phase 5 infrastructure |

---

## Security Considerations

1. **API Key Storage**: Use system keyring (not plaintext config files)
2. **Rate Limiting**: Limit subdomain claims per account (e.g., 5 free)
3. **Subdomain Validation**: Reject reserved names (admin, api, www, etc.)
4. **Abuse Prevention**: Monitor for subdomain squatting, phishing attempts
5. **MFA Enforcement**: Require MFA for API key creation (Phase 4)

---

## Open Questions

1. **Subdomain limits**: How many free subdomains per account?
2. **Subdomain expiry**: Should inactive subdomains auto-release after N months?
3. **Reserved words**: Full list of reserved subdomain names?
4. **Abuse handling**: Process for handling abuse reports?

---

## References

- [Hetzner DNS API Documentation](https://dns.hetzner.com/api-docs)
- [Traefik Let's Encrypt Configuration](https://doc.traefik.io/traefik/https/acme/)
- [Authentik Integration Plan](authentik-integration-plan.md) - Infrastructure pattern reference
- [Existing Hetzner Deployment](../issues/hetzner-deployment-templates.md)

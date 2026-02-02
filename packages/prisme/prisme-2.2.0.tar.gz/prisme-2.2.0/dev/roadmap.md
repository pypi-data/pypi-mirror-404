# Prism Development Roadmap

**Document Purpose**: Development timeline and priorities for both the Prism framework and user-facing features
**Last Updated**: 2026-01-31
**Prioritization Basis**: Strategic impact, dependencies, and user value
**Current Version**: 1.7.0

---

## Recent Releases (0.3.0 - 1.7.0)

Since the initial release, significant features have been shipped:

### v1.7.0 (2026-01-31)
- **Deploy Infrastructure**: Default to cx23 in Falkenstein for deploy infrastructure

### v1.6.0 (2026-01-30)
- **Admin Panel & User Access Control**: Admin pages, user whitelisting, signup access control, bootstrap flow, `prism admin bootstrap` CLI command (PR #63)

### v1.5.0 (2026-01-30)
- **Protected Routes**: Wrap model routes with ProtectedRoute, render auth routes outside Layout

### v1.4.x (2026-01-29 - 2026-01-30)
- **Frontend Auth Tests**: Generate frontend auth test files for JWT projects
- **Multiple TypeScript Fixes**: JSX imports, enum types, CRUD operations in page templates (PRs #60, #62)
- **DevContainer Fixes**: asyncpg driver, Vite bind to all interfaces, Traefik labels, volume permissions

### v1.3.0 (2026-01-29)
- **Migration Drift Detection**: Generate migration drift detection test and CI job (#57)

### v1.2.0 (2026-01-29)
- **Migration Warnings**: Show specific field-level changes in migration warnings (#55)

### v1.1.x (2026-01-29)
- **Migration Warnings**: Show migration warnings after code generation (#55, #57)
- **DevContainer Refactor**: Remove Claude Code dependency, consolidate volumes into single persist volume

### v1.0.0 (2026-01-29)
- **Python 3.13 Compatibility**: Replace passlib with bcrypt in templates
- **Dependency Updates**: Bump github-actions group

### v0.15.0 (2026-01-29)
- **Full-Featured Auth System**: Cookie-based JWT sessions, email verification (Resend), password reset, TOTP MFA, account lockout, OAuth social login, headless UI templates
- **Authentik Removal**: Removed deprecated Authentik SSO integration
- **TypeScript Type-Checking**: `--typecheck` flag for `prism generate` and `prism test`
- **Multiple Bug Fixes**: GraphQL future annotations, strawberry inputs, ruff lint errors, template bugs (#46-#53)

### v0.13.x - v0.14.x (2026-01-27 - 2026-01-28)
- **TypeScript Type-Checking**: Added `--typecheck` flag to generate and test commands (#40)
- **Authentik Bug Fixes**: Pydantic-settings defaults, auth router inclusion (#41, #42)
- **Docker Test Fixes**: Unified `--run-docker` skip flag

### v0.12.1 (2026-01-26)
- **Headless UI Generation Layer**: Model-agnostic composable UI primitives (pagination, selection, sorting, filtering, search, modals, toasts, drawers)
- **Custom Error Pages**: Traefik proxy error pages (404, 503) with diagnostic CLI commands (`prism proxy diagnose`)
- **DevContainer Exec Commands**: Added `exec`, `test`, `migrate`, `url`, `generate` commands for dev containers

### v0.12.0 (2026-01-26)
- **Frontend Design System**: Nordic-inspired design tokens, Tailwind integration, dark mode support (PR #2)
- **Dev Container with Claude Code**: Full devcontainer lifecycle management with 11 CLI commands (PR #3)

### v0.11.x (2026-01-26)
- **Template Bug Fixes**: Fixed 10 GitHub issues (#10-#19) covering Terraform, frontend, backend, and CI/CD generators (PR #26)
- **Multiple Generation Fixes**: Auth import paths, module naming, type errors (PR #39)

### v0.10.0 (2026-01-26)
- **API Key Authentication**: Bearer token auth preset for SaaS integrations
- **Managed Subdomain CLI**: `prism subdomain` and `prism auth` command groups for madewithpris.me

### v0.8.0
- **RelationSelect Widget**: Automatic GraphQL option loading for relation selects
- **Optional FK Support**: Many-to-one relationships now support optional foreign keys
- **Bug Fixes**: Snake_case conversion for GraphQL inputs, table prefix for enum fields

### v0.7.0
- **Many-to-Many Relationships**: Full M2M support across Services, MCP, and REST generators
- Association tables generated automatically for M2M relationships

### v0.6.x
- **MCP in Docker**: MCP server support in Docker development environment with Traefik routing
- **JSON Field Types**: Both dict and list types now supported in JSON fields
- **Auto-generated ForeignKey columns** for many_to_one relationships

### v0.5.0
- **Relationship Filtering**: List operations now support filtering by relationship fields

### v0.4.0
- **Relationship Fields in GraphQL**: Input types, frontend types, and operations
- **MCP Relationship Parameters**: Tools include relationship field parameters
- **Alembic Configuration**: Auto-generated during `prism generate`

### v0.3.x
- **Vite Proxy Configuration**: Local development support with relative URLs in GraphQL clients
- **MCP Schema Improvements**: Better handling of json_item_type

---

## Table of Contents

### Active Priorities (User-Facing Features)
- [Priority 1: AI Agents with MCP Integration](#priority-1-ai-agents-with-mcp-integration)
- [Priority 2: Email Integration & Specification](#priority-2-email-integration--specification)
- [Priority 3: Enhanced Dependency & Install Templates](#priority-3-enhanced-dependency--install-templates)

### IoT & Data Platform Features (Hjemme IT Use Case)
- [Priority 4: Background Jobs & Scheduling](#priority-4-background-jobs--scheduling) 🔥 P0
- [Priority 5: TimescaleDB Support](#priority-5-timescaledb-support) 🔥 P0
- [Priority 6: External Service Integration](#priority-6-external-service-integration) 🟡 P1
- [Priority 7: Webhook/Event Handling](#priority-7-webhookevent-handling) 🟡 P1
- [Priority 8: Media File Handling](#priority-8-media-file-handling) 🟡 P2
- [Priority 9: Docker Compose Templates](#priority-9-docker-compose-templates) 🟡 P2
- [Priority 10: Custom Frontend Routes/Pages + Landing](#priority-10-custom-frontend-routespages--landing-page) ⬆️ **HIGH**
- [Priority 11: Continuous Aggregates (TimescaleDB)](#priority-11-continuous-aggregates-timescaledb) 🟢 P3
- [Priority 12: Enterprise Auth (Built-in)](#priority-12-enterprise-auth-with-authentik-built-in) ✅ **COMPLETE**
- [Priority 13: Migration Rollback Support](#priority-13-migration-rollback-support) 🟢 P3

### Strategic Priorities
- [Priority 14: Service Abstraction (Custom Business Logic)](#priority-14-service-abstraction-custom-business-logic) **HIGH**
- [Priority 15: madewithpris.me Managed Subdomain](#priority-15-managed-subdomain--https-madewithpris.me) 🟡 **IN PROGRESS**
- [Priority 16: CLI Simplification & Developer Experience](#priority-16-cli-simplification--developer-experience) ⬆️ **HIGH**
- [Priority 17: Frontend Design System](#priority-17-frontend-design-system) ✅ **COMPLETE**
- [Priority 18: Dev Container with Claude Code](#priority-18-dev-container-with-claude-code) ✅ **COMPLETE**

### User-Facing Features (New)
- [Priority 19: Admin Panel & User Access Control](#priority-19-admin-panel--user-access-control) ✅ **COMPLETE**

### Appendix
- [Completed Features (Archived)](#completed-features-archived)
- [Summary Table](#summary-table)
- [Implementation Timeline](#implementation-timeline)
- [Notes](#notes)

---

## Priority 1: AI Agents with MCP Integration

**Status**: 🔴 Not Started | **Priority**: HIGH | **Complexity**: HIGH | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Modern applications increasingly need AI-powered capabilities, but integrating AI agents requires:
- Manual setup of LLM providers (OpenAI, Anthropic, etc.)
- Building custom tool calling/function execution infrastructure
- Creating chat interfaces and conversation state management from scratch
- Integrating AI capabilities with existing REST/GraphQL APIs
- Managing context, prompt engineering, and response streaming

Prism already generates MCP (Model Context Protocol) tools, but there's no easy way for users to leverage these in AI agent workflows.

**Target Users**:
- Developers building AI-powered SaaS applications
- Teams adding copilot/assistant features to existing products
- Applications requiring natural language interfaces to data/operations
- Enterprises wanting AI agents with controlled tool access

**Use Cases**:
1. **Customer Support Chatbot**: AI agent uses MCP tools to query orders, update tickets, send emails
2. **Data Analysis Assistant**: Agent executes database queries, generates reports, visualizes data
3. **Admin Copilot**: Natural language interface for CRUD operations ("create a new user with email...")
4. **Multi-step Workflows**: Agent orchestrates multiple tool calls ("find overdue invoices and email customers")
5. **Conversational UI**: Embedded chat widget in React frontend for agent interaction

**Expected Outcome**: Add production-ready AI agent capabilities to Prism projects in under 1 hour, with full chat UI and MCP tool integration.

### Implementation Complexity

**Effort Estimate**: 5-6 weeks (1 senior developer with AI/LLM experience)

**Technical Scope**:

1. **Specification Extensions** (`prism.yaml`):
   ```yaml
   agents:
     - name: support_agent
       description: "Customer support assistant"
       model_provider: anthropic  # anthropic | openai | ollama
       model: claude-3-5-sonnet-20241022
       system_prompt: |
         You are a helpful customer support agent for {app_name}.
         You can help users with orders, account issues, and general questions.
       tools:
         - all  # Use all generated MCP tools
       max_tokens: 4096
       temperature: 0.7
       expose_via:
         - rest  # POST /api/agents/support_agent/chat
         - graphql  # mutation { chat(agentName: "support_agent", ...) }
       auth_required: true
       allowed_roles: ["user", "admin"]
   ```

2. **Backend Components**:
   - Agent Service with multi-provider support (Anthropic, OpenAI, Ollama)
   - Conversation Manager for thread-based history
   - Tool Executor for MCP integration
   - Streaming responses (Server-Sent Events)

3. **Frontend Components**:
   - Chat Widget (`AgentChat.tsx`)
   - API Client with streaming support
   - Tool call visualization

4. **CLI Commands**:
   - `prism agents list` - Show configured agents
   - `prism agents test <agent> "message"` - Test agent locally
   - `prism agents chat <agent>` - Interactive CLI chat

### Dependencies & Prerequisites

**Hard Dependencies**:
- LLM provider API keys (Anthropic, OpenAI, or Ollama for local)
- MCP tool generation (already implemented)

**Recommended First**:
- Priority 2 (Email integration) - agents can trigger email sending via tools

**Breaking Changes**: None - purely additive, opt-in via `agents:` section

### Risk Assessment

**High Risks**:
- **LLM API Costs**: Rate limiting, token budgets, usage alerts
- **Unsafe Tool Execution**: Require confirmation for destructive tools, audit logging
- **Prompt Injection**: Input sanitization, system prompt isolation

**Adoption Risk**: MEDIUM-HIGH - Cutting-edge feature with high user interest.

---

## Priority 2: Email Integration & Specification

**Status**: 🔴 Not Started | **Priority**: HIGH | **Complexity**: MEDIUM-HIGH | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Many SaaS applications require email functionality, but Prism-generated projects have no built-in email support. Users must manually integrate email libraries, set up templates, and configure SMTP providers.

**Target Users**:
- Developers building SaaS applications with user authentication
- Teams requiring transactional email (order confirmations, alerts)
- Applications needing email-based workflows (invitations, notifications)

**Use Cases**:
1. **Authentication Flows**: Password reset, email verification, welcome emails
2. **Transactional Emails**: Order confirmations, invoice notifications
3. **Team Collaboration**: Invitation emails, activity notifications

**Expected Outcome**: 80% reduction in email integration time, production-ready email flows out-of-the-box.

### Implementation Complexity

**Effort Estimate**: 4-5 weeks (1 senior developer)

**Technical Scope**:

1. **Specification Extensions** (`prism.yaml`):
   ```yaml
   email:
     provider: smtp  # smtp | sendgrid | mailgun | aws_ses
     from_email: "noreply@example.com"
     templates_dir: "emails/templates"

   email_actions:
     - name: password_reset
       subject: "Reset your password"
       template: "password_reset.html"
       trigger: auth.password_reset_request
   ```

2. **Backend Components**:
   - Email Service with multi-provider support
   - Template Rendering (Jinja2)
   - Async email sending with retry logic

3. **Email Templates**: Default templates for auth flows (GENERATE_ONCE)

4. **CLI Commands**:
   - `prism email send --to user@example.com --template welcome`
   - `prism email test-config`

### Dependencies & Prerequisites

**Hard Dependencies**: `aiosmtplib`, `jinja2`, `email-validator`

**Breaking Changes**: None - purely additive, opt-in via `email:` section

---

## Priority 3: Enhanced Dependency & Install Templates

**Status**: 🔴 Not Started | **Priority**: MEDIUM | **Complexity**: LOW | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Generated projects may have unclear dependency management, leading to inconsistent environments and "works on my machine" issues.

**Expected Outcome**: Zero dependency-related issues, sub-5-minute setup for new developers.

### Implementation Complexity

**Effort Estimate**: 1-2 weeks (1 developer)

**Technical Scope**:
- Improve `pyproject.toml` with grouped dependencies
- Add `.python-version` and `.nvmrc` files
- Generate `INSTALL.md` with step-by-step setup
- Add `setup.sh` script for Unix systems
- `prism install` command

---

## IoT & Data Platform Features (Hjemme IT Use Case)

> **Source**: Feature requests from Hjemme IT Platform team building a home automation/data platform combining time-series data ingestion, Home Assistant integration, timeline UI, and Model Predictive Control (MPC) for energy optimization.

---

## Priority 4: Background Jobs & Scheduling

**Status**: 🔴 Not Started | **Priority**: HIGH (P0) | **Complexity**: MEDIUM | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Data ingestion use cases require fetching data from external APIs on a schedule. Prism has no built-in support for background jobs.

**Use Cases**:
1. **Data Ingestion**: Fetch electricity prices, weather data every N minutes
2. **Scheduled Reports**: Generate daily/weekly reports
3. **Cleanup Jobs**: Archive old data, clear caches
4. **Sync Jobs**: Synchronize data with external systems

**Expected Outcome**: Define scheduled jobs in specification, auto-generate APScheduler config with history/logging.

### Implementation Complexity

**Effort Estimate**: 3-4 weeks

**Technical Scope**:
```yaml
schedulers:
  - name: electricity_price_fetcher
    trigger: interval
    interval_minutes: 15
    function: plugins.electricity_price.fetch_prices
    retry_on_failure: true
```

**Detailed Plan**: [background-jobs-scheduling-plan.md](plans/background-jobs-scheduling-plan.md)

---

## Priority 5: TimescaleDB Support

**Status**: 🔴 Not Started | **Priority**: HIGH (P0) | **Complexity**: MEDIUM | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Time-series data requires optimized storage and querying. Standard PostgreSQL doesn't leverage TimescaleDB's hypertables, compression, or retention policies.

**Use Cases**:
1. **Efficient Storage**: Automatic data compression
2. **Fast Queries**: Time-bucket aggregations
3. **Data Retention**: Automatic deletion of old data
4. **Chunking**: Optimized storage partitioning

**Expected Outcome**: Define time-series models in specification, auto-generate hypertable migrations and optimized queries.

### Implementation Complexity

**Effort Estimate**: 3-4 weeks

**Technical Scope**:
```yaml
models:
  - name: DataPoint
    timeseries:
      time_column: timestamp
      chunk_interval: 1 week
      compression:
        enabled: true
        after: 1 month
      retention:
        drop_after: 1 year
```

**Detailed Plan**: [timescaledb-support-plan.md](plans/timescaledb-support-plan.md)

---

## Priority 6: External Service Integration

**Status**: 🔴 Not Started | **Priority**: MEDIUM (P1) | **Complexity**: SMALL | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Applications need to call external APIs but there's no built-in way to define type-safe clients.

**Use Cases**: Home Assistant integration, payment APIs, notifications, data enrichment

**Expected Outcome**: Define external services in specification, auto-generate type-safe Python client classes.

**Effort Estimate**: 2-3 weeks

**Detailed Plan**: [external-service-integration-plan.md](plans/external-service-integration-plan.md)

---

## Priority 7: Webhook/Event Handling

**Status**: 🔴 Not Started | **Priority**: MEDIUM (P1) | **Complexity**: SMALL | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: External systems need to send events via webhooks. There's no built-in webhook support.

**Use Cases**: Home automation events, payment notifications, CI/CD triggers, IoT events

**Expected Outcome**: Define webhooks in specification, auto-generate authenticated endpoints with validation.

**Effort Estimate**: 2 weeks

**Detailed Plan**: [webhook-event-handling-plan.md](plans/webhook-event-handling-plan.md)

---

## Priority 8: Media File Handling

**Status**: 🔴 Not Started | **Priority**: MEDIUM (P2) | **Complexity**: LARGE | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Applications need file uploads but Prism has no file storage support.

**Use Cases**: Photo libraries, document upload, media timeline, user avatars

**Expected Outcome**: Define file fields in models, auto-generate upload endpoints, storage backends, thumbnails.

**Effort Estimate**: 4-5 weeks

---

## Priority 9: Docker Compose Templates

**Status**: 🔴 Not Started | **Priority**: MEDIUM (P2) | **Complexity**: SMALL | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Prism generates a monorepo but no Docker Compose setup. Users must manually create multi-container configurations.

**Use Cases**: Local development, CI testing, production deployment

**Expected Outcome**: Generate Docker Compose files with all required services.

**Effort Estimate**: 2 weeks

---

## Priority 10: Custom Frontend Routes/Pages + Landing Page

**Status**: 🔴 Not Started | **Priority**: HIGH | **Complexity**: MEDIUM | **Category**: User-Facing Feature

> **Note**: Upgraded to HIGH priority (2026-01-26). Essential for presentable apps.

### User Value & Use Cases

**Problem Statement**: Prism auto-generates CRUD views but provides no guidance for custom pages (dashboards, landing pages).

**Use Cases**: Landing pages, custom dashboards, pricing pages, onboarding flows

**Expected Outcome**: Hook-based system where users can override the main page and add custom routes via `router.hook.tsx`.

**Effort Estimate**: 2-3 weeks

---

## Priority 11: Continuous Aggregates (TimescaleDB)

**Status**: 🔴 Not Started | **Priority**: LOW (P3) | **Complexity**: MEDIUM | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Dashboard queries over large time-series datasets are slow. Pre-computed aggregates improve performance.

**Expected Outcome**: Define continuous aggregates in model specification, auto-generate TimescaleDB views.

**Dependencies**: Requires Priority 5 (TimescaleDB Support)

**Effort Estimate**: 2-3 weeks

---

## Priority 12: Enterprise Auth ~~with Authentik~~ (Built-in)

**Status**: 🟢 Complete (v0.15.0, replaced by built-in auth) | **Priority**: HIGH | **Complexity**: MEDIUM-HIGH | **Category**: User-Facing Feature

> **Note**: Authentik integration was removed in v0.15.0. Replaced by a full-featured built-in auth system with cookie-based JWT sessions, email verification (Resend), password reset, TOTP MFA, account lockout, and OAuth social login.

### What Was Implemented (v0.15.0)

Instead of bundling Authentik as an external identity provider, a complete built-in auth system was implemented:
1. **Cookie-based JWT Sessions**: Secure httpOnly cookies
2. **Email Verification**: Via Resend integration
3. **Password Reset**: Token-based secure flows
4. **TOTP MFA**: Time-based one-time passwords
5. **Account Lockout**: Brute-force protection
6. **OAuth Social Login**: Third-party provider support
7. **Headless UI Templates**: Login, signup, password reset, MFA pages

---

## Priority 13: Migration Rollback Support

**Status**: 🔴 Not Started | **Priority**: LOW (P3) | **Complexity**: MEDIUM | **Category**: User-Facing Feature

### User Value & Use Cases

**Problem Statement**: Model changes may need to be reverted. Prism only generates forward migrations.

**Expected Outcome**: Generate down migrations alongside up migrations, provide CLI commands for rollback.

**Effort Estimate**: 2-3 weeks

---

## Priority 14: Service Abstraction (Custom Business Logic)

**Status**: 🔴 Not Started | **Priority**: HIGH | **Complexity**: MEDIUM-HIGH | **Category**: Framework Architecture

> **Note**: New priority added (2026-01-26). Enables sophisticated apps beyond CRUD.

### User Value & Use Cases

**Problem Statement**: Prism generates CRUD services, but real applications need custom business logic services that combine data, integrate external APIs, and perform calculations.

**Use Cases**:
1. **Portfolio Value Calculator**: Read holdings, fetch stock prices, return totals
2. **Order Processing**: Validate, calculate, update inventory, trigger notifications
3. **Report Generator**: Aggregate across models, compute statistics
4. **External API Wrapper**: Fetch, cache, normalize data

**Expected Outcome**: Define custom services in spec with method signatures. Prism generates scaffolds with typed interfaces and DI for CRUD services.

**Effort Estimate**: 4-5 weeks

---

## Priority 15: Managed Subdomain + HTTPS (madewithpris.me)

**Status**: 🟡 In Progress (~85% Complete) | **Priority**: MEDIUM-HIGH | **Complexity**: MEDIUM | **Category**: Platform / DX

> **Note**: Phases 0-5 complete (2026-01-26). Domain is `madewithpris.me` on GoDaddy.
> **Detailed Plan**: [managed-subdomain-plan.md](plans/managed-subdomain-plan.md)
> **Repository**: `prisme-saas` at `/home/lassethomsen/code/prisme-saas/`

### User Value & Use Cases

**Problem Statement**: Users deploying to Hetzner need a domain and SSL setup. Prism can provide `*.madewithpris.me` subdomains with automatic HTTPS, eliminating domain/DNS configuration.

**Architecture**: Users deploy to their own Hetzner server. Prism manages DNS (GoDaddy) pointing to user's IP. Traefik on user's server handles Let's Encrypt SSL.

**Use Cases**:
1. **5-Minute Deploy**: `prism deploy --domain myapp.madewithpris.me` → production app with SSL
2. **Demo/Prototype Sharing**: Share working demos without domain purchase
3. **Evaluation Path**: Start with madewithpris.me, migrate to custom domain when ready

**Expected Outcome**: Spin up a production-ready app at `https://myapp.madewithpris.me` in under 5 minutes.

### Implementation Phases

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 0. Framework | API key auth preset | 0.5 weeks | ✅ Complete |
| 1. Core DNS | Minimal API + DNS, prisme-saas project | 1 week | ✅ Complete |
| 2. Validation | Test script to verify DNS flow works | 0.5 weeks | ✅ Complete |
| 3. CLI Integration | `prism subdomain` commands | 1 week | ✅ Complete |
| 4. Auth & Users | MFA, email verification, multi-user (spec) | 2 weeks | ✅ Spec Complete |
| 5. Integration Testing | Tests, CI/CD, pre-commit, docs | 0.5 weeks | ✅ Complete |
| 6. Production Deploy | Deploy to Hetzner, live testing | 0.5 weeks | 🔴 Not Started |

**Effort Estimate**: 5-6 weeks (85% complete)

**Recent Progress**:
- 66 tests passing with full integration test suite
- Pre-commit hooks matching main prism project
- CI/CD workflows (lint → test → docs → e2e)
- Docker configuration via `prism docker init`
- MkDocs documentation with Material theme

---

## Priority 16: CLI Simplification & Developer Experience

**Status**: 🔴 Not Started | **Priority**: HIGH | **Complexity**: MEDIUM-HIGH | **Category**: Framework / DX

> **Note**: New priority added (2026-01-26). Reduces onboarding friction and improves developer experience.
> **Detailed Plan**: [cli-simplification-roadmap.md](issues/cli-simplification-roadmap.md)

### User Value & Use Cases

**Problem Statement**: Prism CLI has ~37 commands, which is overwhelming for new users. The current opt-in approach for components (Docker, deployment, etc.) contradicts Prism's value proposition of providing a complete enterprise solution out-of-the-box.

**Vision**: Make `prism init` + `prism dev` the primary workflow. Everything else is opt-out or power-user functionality.

**Key Features**:
1. **Interactive Wizard** (`prism init`): Generates full stack by default, config file stores opt-out choices
2. **Smart Dev Mode** (`prism dev`): File watcher auto-regenerates on spec changes, version notifications
3. **Protected Regions**: Inline `// PRISM:PROTECTED:START/END` markers preserve custom code during regeneration
4. **Self-Upgrade** (`prism self-upgrade`): One-command upgrade with changelog display

**Expected Outcome**: Onboarding time reduced from 15+ minutes to under 5 minutes. 90% of workflows use only `init` + `dev`.

### Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Protected Regions | Extend to all generated files | Partially done |
| 2. Config System | `.prism/config.yaml` for project settings | Not started |
| 3. Interactive Wizard | `prism init` replaces `prism create` | Not started |
| 4. Auto-regeneration | File watcher in `prism dev` | Not started |
| 5. Version Management | `prism self-upgrade` + notifications | Not started |

**Effort Estimate**: 4-6 weeks (across phases)

---

## Priority 17: Frontend Design System

**Status**: 🟢 Complete (PR #2, merged 2026-01-26) | **Priority**: HIGH | **Complexity**: MEDIUM | **Category**: User-Facing Feature

> **Note**: New priority added (2026-01-26). Design should not be an afterthought.

### User Value & Use Cases

**Problem Statement**: Frontend CSS in generated projects often becomes gigantic, with duplicate definitions and inconsistent styling. Design is typically an afterthought, leading to poor visual consistency and significant rework. Users lack an opinionated starting point that enforces good patterns automatically.

**Vision**: Provide an opinionated, Nordic-inspired modern design system that ships with every Prism project. Users get a polished, consistent look out-of-the-box while having clear extension points for customization.

**Target Users**:
- Developers who want production-ready UI without design expertise
- Teams building MVPs/prototypes that need to look professional immediately
- Projects that want consistent styling without CSS sprawl

**Use Cases**:
1. **Instant Polish**: Generated CRUD views look production-ready from first run
2. **Design Token Consistency**: Colors, spacing, typography defined once in `_design-tokens.scss`
3. **Component Styling**: Consistent button, form, card, table styles across the app
4. **Dark Mode Ready**: Light/dark themes built-in via CSS custom properties
5. **Icon System**: Curated icon set (Lucide/Heroicons) with consistent usage patterns

**Expected Outcome**: Zero CSS duplication, professional Nordic aesthetic out-of-the-box, 80% reduction in design-related rework.

### Design Philosophy

**Nordic Design Principles**:
- **Minimalism**: Clean layouts, generous whitespace, reduced visual noise
- **Functional Beauty**: Every element serves a purpose
- **Natural Palette**: Muted colors inspired by Scandinavian landscapes (soft grays, blues, warm whites)
- **Typography First**: Clear hierarchy with well-chosen font stack (Inter, system fonts)
- **Subtle Depth**: Light shadows, smooth transitions, no harsh contrasts

### Implementation Complexity

**Effort Estimate**: 3-4 weeks (1 frontend developer with design sensibility)

**Technical Scope**:

1. **Design Token System** (`frontend/src/styles/_design-tokens.scss`):
   ```scss
   // Color palette - Nordic inspired
   :root {
     --color-primary: #2563eb;      // Clear blue
     --color-secondary: #64748b;    // Slate gray
     --color-accent: #0891b2;       // Teal
     --color-surface: #f8fafc;      // Off-white
     --color-background: #ffffff;
     --color-text: #1e293b;
     --color-text-muted: #64748b;
     --color-border: #e2e8f0;
     --color-error: #dc2626;
     --color-success: #16a34a;
     --color-warning: #d97706;

     // Spacing scale
     --space-xs: 0.25rem;
     --space-sm: 0.5rem;
     --space-md: 1rem;
     --space-lg: 1.5rem;
     --space-xl: 2rem;

     // Typography
     --font-sans: 'Inter', system-ui, sans-serif;
     --font-mono: 'JetBrains Mono', monospace;

     // Shadows
     --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
     --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
     --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

     // Radii
     --radius-sm: 0.25rem;
     --radius-md: 0.5rem;
     --radius-lg: 0.75rem;
   }

   [data-theme="dark"] {
     --color-surface: #1e293b;
     --color-background: #0f172a;
     --color-text: #f1f5f9;
     --color-border: #334155;
   }
   ```

2. **File Structure**:
   ```
   frontend/src/styles/
   ├── _design-tokens.scss    # Core variables (GENERATE_ONCE)
   ├── _typography.scss       # Font styles, headings
   ├── _components.scss       # Button, card, form, table styles
   ├── _utilities.scss        # Spacing, layout helpers
   ├── _animations.scss       # Transitions, keyframes
   └── main.scss              # Entry point, imports all
   ```

3. **Tailwind Integration**:
   - Extend Tailwind config with design tokens
   - Custom color palette mapped to CSS variables
   - Preset component classes (`.btn-primary`, `.card`, `.form-input`)

4. **Icon System**:
   - Lucide React icons (MIT licensed, consistent style)
   - Icon component with size/color props
   - Recommended icons per use case (actions, navigation, status)

5. **Component Styling** (via Tailwind + SCSS):
   - Buttons: Primary, secondary, ghost, danger variants
   - Forms: Input, select, checkbox, radio with consistent styling
   - Cards: Surface elevation, hover states
   - Tables: Clean headers, alternating rows, responsive
   - Navigation: Sidebar, topbar, breadcrumbs

6. **Specification Extensions** (`prism.config.py`):
   ```python
   config = PrismConfig(
       design_system=DesignSystemConfig(
           theme="nordic",           # nordic | minimal | corporate
           primary_color="#2563eb",  # Override primary
           dark_mode=True,           # Enable dark mode toggle
           icon_set="lucide",        # lucide | heroicons
           font_family="inter",      # inter | system | custom
       )
   )
   ```

### Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Design Tokens | Core SCSS variables, CSS custom properties | Not started |
| 2. Tailwind Config | Extend Tailwind with design system | Not started |
| 3. Component Styles | Button, form, card, table styles | Not started |
| 4. Icon Integration | Lucide setup, icon component | Not started |
| 5. Dark Mode | Theme toggle, CSS variable switching | Not started |
| 6. Documentation | Style guide, component examples | Not started |

### Dependencies & Prerequisites

**Hard Dependencies**:
- Tailwind CSS (already in Prism frontend template)
- SCSS support (sass package)
- Lucide React icons

**Recommended First**:
- Priority 10 (Custom Frontend Routes) - for landing page styling

**Breaking Changes**: None - purely additive. Existing projects can opt-in via regeneration.

### Risk Assessment

**Low Risks**:
- Design preferences are subjective (mitigated by clean override system)
- Additional dependencies (minimal: sass, lucide-react)

**Adoption Risk**: LOW - Users can ignore design system and use raw Tailwind if preferred.

---

## Priority 18: Dev Container with Claude Code

**Status**: 🟢 Complete (PR #3, merged 2026-01-26) | **Priority**: HIGH | **Complexity**: MEDIUM | **Category**: Platform / DX

> **Note**: New priority added (2026-01-26). Self-hosted Codespaces/Gitpod alternative with Claude Code built-in.
> **Detailed Plan**: [devcontainer-claude-code-plan.md](plans/devcontainer-claude-code-plan.md)

### User Value & Use Cases

**Problem Statement**: Developers building Prism apps need reproducible, isolated development environments. Setting up Claude Code, dependencies, and services for each project is repetitive. Running multiple feature branches simultaneously requires careful environment management.

**Vision**: Provide a CLI-first dev container experience where developers can spin up a complete, isolated Prism development environment with Claude Code pre-installed in a single command. Think "self-hosted GitHub Codespaces for Prism projects."

**Target Users**:
- Developers who want reproducible dev environments
- Teams working on multiple branches/features simultaneously
- Developers who want AI-assisted coding (Claude Code) without setup friction

**Use Cases**:
1. **Feature Branch Isolation**: `prism devcontainer start --name feature-auth --branch feature/auth` - work on auth feature without affecting main
2. **Fresh Start**: Clone any Prism project into a clean container, avoid "works on my machine"
3. **AI-Assisted Development**: Claude Code pre-installed, API key mounted from host config
4. **Multi-Project**: Run dev containers for different projects simultaneously, each with isolated databases

**Expected Outcome**: Spin up a fully functional Prism dev environment with Claude Code in under 2 minutes.

### Implementation Complexity

**Effort Estimate**: 2-3 weeks (1 developer)

**Technical Scope**:

1. **Pre-built Docker Image** (`ghcr.io/prism/devcontainer`):
   - Base: `nikolaik/python-nodejs:python3.13-nodejs22`
   - Claude Code pre-installed (`npm install -g @anthropic-ai/claude-code`)
   - Prism CLI pre-installed (`pip install prisme`)
   - Git, curl, jq, PostgreSQL client

2. **CLI Commands** (`prism devcontainer` group):
   ```bash
   prism devcontainer start [URL] [--name NAME] [--branch BRANCH]
   prism devcontainer shell <name>
   prism devcontainer list
   prism devcontainer stop <name>
   prism devcontainer restart <name>
   prism devcontainer destroy <name> [--volumes]
   ```

3. **Volume Persistence**:
   ```
   prism-dc-{name}-code   # Git working directory
   prism-dc-{name}-db     # PostgreSQL data
   prism-dc-{name}-deps   # node_modules + .venv
   ```

4. **Traefik Integration**: Services accessible at `{name}.localhost` via existing proxy

5. **Claude Code Config**: Mount `~/.config/claude-code` read-only from host

### Example Workflow

```bash
# Start a new dev container
$ prism devcontainer start https://github.com/myorg/myapp.git --name myapp-feature

# Enter the container
$ prism devcontainer shell myapp-feature

# Inside: Claude Code is ready to use
root@...:/workspace# claude --version
Claude Code v1.x.x

# Start development servers
root@...:/workspace# prism dev
  Backend:  http://myapp-feature.localhost/api
  Frontend: http://myapp-feature.localhost

# Clean up when done
$ prism devcontainer destroy myapp-feature --volumes
```

### Implementation Phases

Work in feature branch `feature/devcontainer-claude-code`. Each phase includes tests, regression run, commit, and push.

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| 1 | Docker Image & Dockerfile | `test_dockerfile.py` | ✅ Complete |
| 2 | Core Manager class | `test_config.py`, `test_manager.py` | ✅ Complete |
| 3 | CLI: up, shell, generate | `test_cli.py` | ✅ Complete |
| 4 | CLI: down, logs, status, list | `test_cli.py` | ✅ Complete |
| 5 | Traefik Integration | `test_manager.py` | ✅ Complete |
| 6 | Integration Tests | `test_integration.py` | ✅ Complete |
| 7 | Documentation | `mkdocs build --strict` | ✅ Complete |
| 8 | Final Review & PR | Full regression + `gh pr create` | ✅ Complete (PR #3) |

### Dependencies & Prerequisites

**Hard Dependencies**:
- Docker Engine on host
- Existing Traefik proxy setup (from `prism dev --docker`)

**Breaking Changes**: None - purely additive, new `prism devcontainer` command group.

### Risk Assessment

**Low Risks**:
- Docker image size (mitigated by multi-stage builds, layer caching)
- Container startup time (mitigated by pre-installed dependencies)

**Adoption Risk**: LOW - Opt-in feature, doesn't affect existing workflows.

---

## Priority 19: Admin Panel & User Access Control

**Status**: 🟢 Complete (PR #63, 2026-01-30) | **Priority**: HIGH | **Complexity**: MEDIUM | **Category**: User-Facing Feature

> **Detailed Plan**: [admin-panel-plan.md](plans/admin-panel-plan.md)

### User Value & Use Cases

**Problem Statement**: Prism generates JWT auth with roles (`require_roles("admin")`), but there is no admin UI to manage users, control who can sign up, or bootstrap the first admin. App operators must use direct database access for user management tasks.

**Use Cases**:
1. **User Management**: List, search, activate/deactivate, and delete users from a web UI
2. **Signup Whitelisting**: Restrict registration to specific email addresses, domains (e.g., `@company.com`), or regex patterns (e.g., `.*@.*\.edu`)
3. **Admin Promotion**: Promote/demote users to admin role from the UI
4. **First Admin Bootstrap**: Securely create the initial admin user without database access

### Key Design Decisions

**Signup Access Control**:
```yaml
auth:
  signup_access:
    mode: open              # open | whitelist | invite_only
    whitelist:
      emails: ["cto@company.com"]
      domains: ["company.com", "partner.org"]
      patterns: [".*@.*\\.edu"]
```

Whitelist rules are stored in a database table for runtime editing via the admin panel, seeded from spec values on first migration.

**First Admin Bootstrap** (CLI + env var fallback):

```bash
# Primary: CLI command (Django-style)
prism admin bootstrap --email admin@example.com
# → Creates admin user with one-time password-set link (24h expiry)

# Fallback: Environment variable (for containerized deploys)
ADMIN_BOOTSTRAP_EMAIL=admin@example.com
# → On startup, if no admin exists, creates user + logs bootstrap URL
```

The bootstrap flow uses a single-use, time-limited token. The user visits the link, sets their password, and is redirected to login. This avoids the security issues of hardcoded passwords or "first user is admin" patterns.

**Generated Admin Pages** (at `/admin`, role-gated):
- Dashboard: user count, recent signups, whitelist status
- User list: search, filter by role/status, paginated
- User detail: edit roles, activate/deactivate
- Whitelist editor: add/remove rules, test an email against current rules

### Implementation Complexity

**Effort Estimate**: 3-4 weeks

**Technical Scope**:
- Spec model extensions (`AdminPanelConfig`, `SignupAccessConfig`)
- Backend: admin API routes, whitelist service, bootstrap service
- Frontend: 4 admin pages + layout, bootstrap page
- Database: `signup_whitelist` table, bootstrap token columns on user
- CLI: `prism admin bootstrap` command
- Modify existing signup template to validate against whitelist

### Dependencies & Prerequisites

**Hard Dependencies**:
- Existing JWT auth system (already implemented)
- Existing `require_roles` infrastructure (already implemented)
- Headless UI primitives for admin tables (already implemented in v0.12.1)

**Recommended First**:
- Priority 2 (Email Integration) - for bootstrap link delivery via email instead of stdout

**Breaking Changes**: None - opt-in via `auth.admin_panel.enabled: true`

### Risk Assessment

**Medium Risks**:
- ReDoS via user-provided regex patterns (mitigated: validation + time-limited execution)
- Admin lockout if only admin demotes themselves (mitigated: prevent self-demotion)

**Adoption Risk**: LOW - Opt-in, preserves existing behavior when disabled.

---

## Completed Features (Archived)

These features have been implemented and are available in the current release.

### CI/CD Pipeline for Prism Framework ✅

**Completed**: 2026-01-23

**What was implemented:**
- **CI Workflow** (`.github/workflows/ci.yml`): Split into `lint`, `test`, `docs`, `e2e`, `e2e-docker` jobs
- **Release Workflow** (`.github/workflows/release.yml`): Triggers after CI success, publishes to PyPI
- **Package Naming**: Renamed from `prism` to `prisme` for PyPI
- **Pre-commit Hooks** (`.pre-commit-config.yaml`): Ruff linting/formatting, YAML validation
- **E2E Testing Infrastructure** (`tests/e2e/`): CLI workflow tests, Docker integration tests
- **Documentation**: Created `CONTRIBUTING.md`, added badges to README
- **Code Quality**: Fixed 137 ruff lint errors, all tests passing (500+ passed)

---

### Prism Documentation Site (MkDocs) ✅

**Completed**: 2026-01-23

**What was implemented:**
- **MkDocs Configuration** (`mkdocs.yml`): Material theme with dark/light mode, mkdocstrings plugin
- **ReadTheDocs Integration** (`.readthedocs.yaml`): Hosted at `prisme.readthedocs.io`
- **Documentation Structure** (29 files): Getting started, user guide, tutorials, reference, architecture
- **CI Integration**: Added `docs` job with `mkdocs build --strict`
- **README Updates**: Added ReadTheDocs badge and documentation links

---

### Hetzner Deployment Templates ✅

**Completed**: 2026-01-23

**What was implemented:**
- **CLI Commands** (`prism deploy`): `init`, `plan`, `apply`, `destroy`, `ssh`, `logs`, `status`, `ssl`
- **Terraform Templates** (`deploy/terraform/`): Hetzner Cloud resources, modules for server and volume
- **Cloud-init Provisioning**: Docker, firewall, fail2ban, nginx, systemd service
- **Deployment Scripts**: Zero-downtime deployment, rollback support
- **CI/CD Integration**: GitHub Actions workflow for automated deployment
- **Tests**: 43 tests for config, generator, and CLI

---

## Summary Table

### Active Priorities

| Priority | Feature | Category | Status | Complexity | Effort |
|----------|---------|----------|--------|------------|--------|
| 1 | AI Agents with MCP Integration | User-Facing | 🔴 Not Started | HIGH | 5-6 weeks |
| 2 | Email Integration & Spec | User-Facing | 🔴 Not Started | MEDIUM-HIGH | 4-5 weeks |
| 3 | Enhanced Dependency Templates | User-Facing | 🔴 Not Started | LOW | 1-2 weeks |
| 4 | Background Jobs & Scheduling | User-Facing | 🔴 Not Started | MEDIUM | 3-4 weeks |
| 5 | TimescaleDB Support | User-Facing | 🔴 Not Started | MEDIUM | 3-4 weeks |
| 6 | External Service Integration | User-Facing | 🔴 Not Started | SMALL | 2-3 weeks |
| 7 | Webhook/Event Handling | User-Facing | 🔴 Not Started | SMALL | 2 weeks |
| 8 | Media File Handling | User-Facing | 🔴 Not Started | LARGE | 4-5 weeks |
| 9 | Docker Compose Templates | User-Facing | 🔴 Not Started | SMALL | 2 weeks |
| 10 | Custom Frontend Routes + Landing | User-Facing | 🔴 Not Started | MEDIUM | 2-3 weeks |
| 11 | Continuous Aggregates | User-Facing | 🔴 Not Started | MEDIUM | 2-3 weeks |
| 12 | Enterprise Auth (Built-in) | User-Facing | 🟢 Complete | MEDIUM-HIGH | 3-4 weeks |
| 13 | Migration Rollback Support | User-Facing | 🔴 Not Started | MEDIUM | 2-3 weeks |
| 14 | Service Abstraction | Framework | 🔴 Not Started | MEDIUM-HIGH | 4-5 weeks |
| 15 | Managed Subdomain (madewithpris.me) | Platform/DX | 🟡 In Progress (85%) | MEDIUM | 5-6 weeks |
| 16 | CLI Simplification & DX | Framework | 🔴 Not Started | MEDIUM-HIGH | 4-6 weeks |
| 17 | Frontend Design System | User-Facing | 🟢 Complete | MEDIUM | 3-4 weeks |
| 18 | Dev Container with Claude Code | Platform/DX | 🟢 Complete | MEDIUM | 2-3 weeks |
| 19 | Admin Panel & User Access Control | User-Facing | 🟢 Complete | MEDIUM | 3-4 weeks |

### Completed

| Feature | Category | Completed |
|---------|----------|-----------|
| Admin Panel & User Access Control (P19) | User-Facing | 2026-01-30 |
| Enterprise Auth - Built-in (P12) | User-Facing | 2026-01-29 |
| Frontend Design System (P17) | User-Facing | 2026-01-26 |
| Dev Container with Claude Code (P18) | Platform/DX | 2026-01-26 |
| CI/CD Pipeline for Prism | Framework | 2026-01-23 |
| Prism Documentation Site | Framework | 2026-01-23 |
| Hetzner Deployment Templates | User-Facing | 2026-01-23 |

---

## Implementation Timeline

### Phase 1: Foundation ✅ COMPLETE

**Completed**: CI/CD Pipeline, Documentation Site, Hetzner Deployment Templates

### Phase 2: High-Value User Features (Current)

1. **Enhanced Dependency & Install Templates** (Priority 3)
2. **AI Agents with MCP Integration** (Priority 1)
3. **Email Integration** (Priority 2)

### Phase 3: IoT & Data Platform

4. **Background Jobs & Scheduling** (Priority 4)
5. **TimescaleDB Support** (Priority 5)
6. **External Service Integration** (Priority 6)
7. **Webhook/Event Handling** (Priority 7)

### Phase 4: Advanced Features

8. **Custom Frontend Routes** (Priority 10)
9. ~~**Enterprise Auth with Authentik** (Priority 12)~~ → ✅ Replaced by built-in auth (v0.15.0)
10. **Service Abstraction** (Priority 14)
11. ~~**Frontend Design System** (Priority 17)~~ → ✅ Complete (v0.12.0)
12. ~~**Dev Container with Claude Code** (Priority 18)~~ → ✅ Complete (v0.12.0)

---

## Notes

### Prioritization Rationale

**Why AI Agents is Priority 1**:
- Cutting-edge feature with high strategic value (differentiates Prism)
- Leverages existing MCP tool generation
- Creates unique value proposition: "full-stack framework with built-in AI agents"

**Why Email Integration is Priority 2**:
- Essential for production-ready apps
- Blocker for auth flows (password reset, verification)
- Agents can use email as a tool once both are implemented

**Why IoT Features are grouped**:
- Background Jobs, TimescaleDB, External Services, and Webhooks form a cohesive platform for IoT/data applications
- These enable the Hjemme IT use case (home automation, energy management)

### Hjemme IT Platform Use Case (2026-01-24)

Added features from the Hjemme IT Platform team:
- **P0**: Background Jobs & Scheduling, TimescaleDB Support
- **P1**: External Service Integration, Webhook/Event Handling
- **P2**: Media File Handling, Docker Compose Templates
- **P3**: Custom Frontend Routes, Continuous Aggregates, Migration Rollback

### Authentik Integration → Built-in Auth (2026-01-25 → 2026-01-29)

Priority 12 was originally planned as an Authentik integration but was replaced in v0.15.0 with a full-featured built-in auth system:
- Cookie-based JWT sessions (replaced Authentik OIDC)
- Email verification via Resend
- TOTP MFA
- Account lockout / brute-force protection
- OAuth social login
- Password reset with secure token flows
- Authentik code and references fully removed

### Frontend Design System (2026-01-26)

Priority 17 addresses a common pain point:
- CSS becomes gigantic and duplicated across projects
- Design is typically an afterthought, leading to inconsistent UI
- Nordic-inspired, modern design system ships with every Prism project
- Design tokens in `_design-tokens.scss` ensure single source of truth
- Tailwind extended with design system for consistent component styling
- Dark mode support built-in via CSS custom properties

### Dev Container with Claude Code (2026-01-26)

Priority 18 enables self-hosted Codespaces-like experience:
- Pre-built Docker image with Claude Code and Prism CLI baked in
- Git clone inside container for reproducibility and isolation
- Named volumes persist code, database, and dependencies
- Multiple dev containers for different branches/projects simultaneously
- Integrates with existing Traefik proxy for service access
- Claude Code API key mounted from host config (`~/.config/claude-code`)

---

### Open GitHub Issues (2026-01-28)

**13 open issues**, 20+ closed. Key open issues:

| # | Title | Category |
|---|-------|----------|
| 37 | Terraform artifact upload needs absolute paths | Deploy |
| 36 | Generate Hetzner Object Storage backend for terraform state | Deploy |
| 35 | Deploy workflow should accept server_ip as workflow_dispatch input | Deploy |
| 34 | Use workflow_run trigger for terraform after CI tests pass | Deploy |
| 33 | Terraform firewall missing inbound ICMP rule | Deploy |
| 32 | Deploy workflow runs alembic from wrong directory | Deploy |
| 31 | Cloud-init template creates deploy user without SSH keys | Deploy |
| 30 | Generated test factories produce invalid data for fields with validation | Testing |
| 29 | Missing ThemeToggle component in generated frontend | Frontend |
| 9 | Managed Subdomain + HTTPS (madewithpris.me) | Platform |
| 7 | No extension point for custom GraphQL mutations/queries | Framework |
| 6 | Schema drift detection: Database doesn't match models | Framework |
| 4 | CLI Simplification & Developer Experience | DX |

**Open PRs**: #38 (Dependabot: bump github-actions group)

### Codebase Statistics (2026-01-30)

- **32 generator classes** (11 backend, 12 frontend, 1 infrastructure, 2 testing, 6 support)
- **66+ CLI commands** across 16 command groups
- **751+ tests** across 60 test files
- **230+ Jinja2 templates**
- **40+ releases** (v0.1.0 through v1.7.0)

---

**Last Updated**: 2026-01-31 | **Maintainer**: Prism Core Team

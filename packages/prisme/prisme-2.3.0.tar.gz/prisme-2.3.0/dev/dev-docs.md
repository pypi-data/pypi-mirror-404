# Development Documentation Guide

This document defines the structure and conventions for the `dev/` folder, which contains internal development documentation for the Prism project.

## Current Status (2026-01-30)

- **Version**: 1.1.1
- **Generators**: 25 classes (10 backend, 11 frontend, 2 testing, 2 base/support)
- **CLI Commands**: 66+ across 16 command groups
- **Tests**: 751+ test functions in 60 files
- **Templates**: 230+ Jinja2 templates
- **GitHub Issues**: 11 open, 40 closed
- **Open PRs**: 1
- **Plans**: 8 feature plans in `plans/`
- **Issues Tracked**: 15 documents in `issues/`

## Folder Structure

```
dev/
├── dev-docs.md      # This file - conventions and guidelines
├── roadmap.md       # Development roadmap and priorities
├── issues/          # Active issue tracking documents (15 files)
│   ├── index.md
│   ├── app-tsx-overwrites-providers.md
│   ├── async-sqlalchemy-eager-loading.md
│   ├── ci-init-spec-loading.md
│   ├── cli-docs-missing-commands.md
│   ├── cli-simplification-roadmap.md
│   ├── custom-routes-not-preserved.md
│   ├── down-all-incomplete.md
│   ├── generate-ignores-config-paths.md
│   ├── nav-links-ignore-config.md
│   ├── no-custom-graphql-extension.md
│   ├── no-override-restore-mechanism.md
│   ├── override-warning-unclear.md
│   ├── router-generates-nonexistent-routes.md
│   └── schema-drift-not-detected.md
├── plans/           # Implementation plans for features (8 plans)
│   ├── index.md
│   ├── authentik-integration-plan.md
│   ├── background-jobs-scheduling-plan.md
│   ├── external-service-integration-plan.md
│   ├── managed-subdomain-plan.md             # 🟡 In Progress
│   ├── timescaledb-support-plan.md
│   ├── webhook-event-handling-plan.md
│   └── admin-panel-plan.md
└── tasks/           # Active task tracking documents
    └── index.md
```

## Document Types

### Roadmap (`roadmap.md`)

The central planning document containing:
- Prioritized features with status tracking
- Implementation timelines
- Dependency relationships between features
- Risk assessments

**Status indicators:**
- `🟢 Complete` - Feature is implemented and tested
- `🟡 In Progress` - Currently being worked on
- `🔴 Not Started` - Planned but not yet started

### Issues (`issues/`)

Documents tracking specific bugs, problems, or improvements that need attention.

**File naming:** `<short-description>.md`

Examples:
- `docker-build-context-size.md`
- `api-rate-limiting.md`
- `frontend-bundle-size.md`

**Template:**
```markdown
# Issue: <Title>

**Status**: Open | In Progress | Resolved
**Priority**: Low | Medium | High | Critical
**Created**: YYYY-MM-DD

## Problem

Description of the issue.

## Impact

Who/what is affected and how.

## Proposed Solution

How to fix it.

## Resolution

(Fill in when resolved)
```

### Plans (`plans/`)

Detailed implementation plans for features or significant changes.

**File naming:** `<feature-name>-plan.md`

Examples:
- `ai-agents-plan.md`
- `email-integration-plan.md`
- `multi-tenancy-plan.md`

**Template:**
```markdown
# Plan: <Feature Name>

**Status**: Draft | Approved | In Progress | Complete
**Author**: <name>
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Overview

Brief description of what this plan covers.

## Goals

- Goal 1
- Goal 2

## Non-Goals

- What this plan does NOT cover

## Design

### Technical Approach

Detailed technical design.

### API Changes

Any new or modified APIs.

### Database Changes

Schema modifications if applicable.

## Implementation Steps

1. Step 1
2. Step 2

## Testing Strategy

How the feature will be tested.

## Rollout Plan

How to deploy/enable the feature.

## Open Questions

- Question 1?
- Question 2?
```

### Tasks (`tasks/`)

Documents tracking active work sessions or multi-step tasks.

**File naming:** `task-<short-description>.md`

Examples:
- `task-jwt-auth.md`
- `task-template-refactor.md`
- `task-docker-optimization.md`

**Template:**
```markdown
# Task: <Title>

**Status**: In Progress | Blocked | Complete
**Started**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Objective

What this task aims to accomplish.

## Progress

- [x] Completed step
- [ ] Pending step

## Notes

Implementation notes, decisions made, etc.

## Blockers

Any blockers or dependencies.
```

## File Naming Conventions

1. **Use lowercase** with hyphens as separators
2. **Be descriptive** but concise (3-5 words max)
3. **Include type prefix** for tasks (`task-`)
4. **Include suffix** for plans (`-plan`)
5. **No dates in filenames** - use metadata inside the document

**Good examples:**
- `docker-build-optimization.md`
- `task-graphql-subscriptions.md`
- `authentication-refactor-plan.md`

**Bad examples:**
- `2026-01-24-fix.md` (date in filename)
- `DockerBuildOptimization.md` (wrong case)
- `thing.md` (not descriptive)
- `really-long-filename-that-describes-everything-in-detail.md` (too long)

## Lifecycle

1. **Create** documents when starting significant work
2. **Update** documents as work progresses
3. **Archive or delete** documents when work is complete and merged
4. Keep `roadmap.md` as the single source of truth for priorities

## Best Practices

- Keep documents focused and up-to-date
- Link related documents together
- Move completed plans to roadmap.md as "Implementation Summary"
- Delete temporary task documents after completion
- Use the roadmap for historical record of completed features

## GitHub Integration

Issues are tracked both in `dev/issues/` (detailed analysis) and on GitHub Issues. Use `gh issue list` to check current state. Key GitHub issue labels:

- `enhancement` - Feature requests
- `priority:high` / `priority:medium` - Priority markers
- `deferred` - Acknowledged but deferred
- `dx` - Developer experience improvements

When resolving a `dev/issues/` document, also close the corresponding GitHub issue if one exists.

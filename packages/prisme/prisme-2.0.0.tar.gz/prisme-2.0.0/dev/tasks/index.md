# Active Tasks

Documents tracking active work sessions or multi-step tasks.

## Current Tasks

!!! info "No active tasks"
    There are currently no active task documents. Tasks are created when starting significant work and deleted upon completion.

## Task Template

When creating a new task document, use this template:

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

## File Naming

- Use `task-` prefix: `task-jwt-auth.md`
- Use lowercase with hyphens
- Be descriptive but concise

## Task Lifecycle

```mermaid
graph LR
    A[Start Work] --> B[Create Task Doc]
    B --> C[Update Progress]
    C --> D{Complete?}
    D -->|No| C
    D -->|Yes| E[Delete Task Doc]
    E --> F[Update Roadmap]

    style A fill:#4ecdc4
    style E fill:#ff6b6b
    style F fill:#95e1d3
```

## Task vs Plan vs Issue

| Document Type | When to Use | Lifespan |
|--------------|-------------|----------|
| **Task** | Active work sessions | Short (days) |
| **Plan** | Feature design & specs | Medium (weeks) |
| **Issue** | Bugs & problems | Until resolved |

# User Guide

This section covers everything you need to use Prisme effectively in your projects.

## Core Concepts

Prisme follows a **spec-driven development** approach:

1. **Define**: Write your data models in Python using Pydantic
2. **Generate**: Run `prism generate` to create all backend and frontend code
3. **Customize**: Extend generated base classes with your business logic
4. **Regenerate**: Update your spec and regenerate without losing customizations

## Topics

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } **CLI Reference**

    ---

    Complete reference for all Prisme commands

    [:octicons-arrow-right-24: CLI Reference](cli-reference.md)

-   :material-code-braces:{ .lg .middle } **Model Specification**

    ---

    Comprehensive guide to writing Prisme specs

    [:octicons-arrow-right-24: Specification Guide](spec-guide.md)

-   :material-cog:{ .lg .middle } **Code Generation**

    ---

    Understanding what Prisme generates and how

    [:octicons-arrow-right-24: Code Generation](code-generation.md)

-   :material-puzzle:{ .lg .middle } **Extensibility**

    ---

    Customizing generated code without losing changes

    [:octicons-arrow-right-24: Extensibility](extensibility.md)

-   :material-docker:{ .lg .middle } **Docker Development**

    ---

    Containerized development environment

    [:octicons-arrow-right-24: Docker Development](docker-development.md)

-   :material-database:{ .lg .middle } **Database Operations**

    ---

    Migrations, seeding, and database management

    [:octicons-arrow-right-24: Database Operations](database-operations.md)

</div>

## Quick Reference

### Essential Commands

```bash
# Project lifecycle
prism create my-app        # Create new project
prism install              # Install dependencies
prism generate             # Generate code from spec
prism test                 # Run tests
prism dev                  # Start development servers

# Database
prism db migrate           # Create and apply migrations
prism db reset             # Reset database
prism db seed              # Seed test data

# Validation
prism validate             # Validate spec file
prism generate --dry-run   # Preview changes
```

### Project Templates

| Template | Description |
|----------|-------------|
| `full` (default) | Complete full-stack with frontend |
| `minimal` | Backend-only, minimal setup |
| `api-only` | API project without frontend |

```bash
prism create my-app --template minimal
```

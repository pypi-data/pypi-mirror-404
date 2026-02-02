# Architecture

Understanding Prisme's design and internal architecture.

## Overview

Prisme is a **spec-driven code generation framework** that transforms Python/Pydantic model definitions into a full-stack application.

```
┌─────────────────────┐
│   specs/models.py   │  Your specification
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Prisme CLI        │  Code generation
│   (prism generate)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│                   Generated Code                     │
├─────────────────────┬───────────────────────────────┤
│     Backend         │        Frontend               │
├─────────────────────┼───────────────────────────────┤
│ • SQLAlchemy Models │ • TypeScript Types            │
│ • Pydantic Schemas  │ • React Components            │
│ • Service Layer     │ • Hooks                       │
│ • REST API (FastAPI)│ • Pages                       │
│ • GraphQL (Straw.)  │ • GraphQL Operations          │
│ • MCP Tools         │ • API Client                  │
│ • Tests             │ • Tests                       │
└─────────────────────┴───────────────────────────────┘
```

## Core Concepts

<div class="grid cards" markdown>

-   :material-lightbulb:{ .lg .middle } **Design Principles**

    ---

    The philosophy behind Prisme's architecture

    [:octicons-arrow-right-24: Design Principles](design-principles.md)

-   :material-cog:{ .lg .middle } **Generators**

    ---

    How code generation works internally

    [:octicons-arrow-right-24: Generator Architecture](generators.md)

</div>

## High-Level Architecture

### Specification Layer

The entry point is your specification file (`specs/models.py`):

- **StackSpec**: Root configuration (database, GraphQL, generator settings)
- **ModelSpec**: Data model definitions with fields and relationships
- **Exposure configs**: REST, GraphQL, MCP, Frontend settings

### Generator Layer

Prisme's generators transform specs into code:

1. **Spec Loading**: Parse Python spec file
2. **Validation**: Ensure spec is valid and consistent
3. **Context Building**: Create generator context with metadata
4. **Code Generation**: Run generators for each layer
5. **File Writing**: Write files using appropriate strategies

### Generated Application

The output is a complete full-stack application:

- **Backend**: Python/FastAPI with async SQLAlchemy
- **Frontend**: React/TypeScript with your choice of tooling
- **Database**: PostgreSQL or SQLite with Alembic migrations

## Module Structure

```
src/prism/
├── cli.py                    # CLI entry point
├── spec/                     # Specification models
│   ├── fields.py             # FieldType, FilterOperator
│   ├── exposure.py           # REST/GraphQL/MCP/Frontend exposure
│   ├── model.py              # ModelSpec, RelationshipSpec
│   ├── stack.py              # StackSpec, configs
│   └── validators.py         # Validation rules
├── generators/               # Code generators
│   ├── base.py               # Generator base classes
│   ├── backend/              # Backend generators
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── services.py       # Service layer
│   │   ├── rest.py           # REST endpoints
│   │   ├── graphql.py        # GraphQL types/resolvers
│   │   └── mcp.py            # MCP tools
│   ├── frontend/             # Frontend generators
│   │   ├── types.py          # TypeScript types
│   │   ├── components.py     # React components
│   │   └── hooks.py          # React hooks
│   └── testing/              # Test generators
├── templates/                # Jinja2 templates
│   ├── base.py               # Template registry
│   └── jinja2/               # Template files
├── utils/                    # Utilities
│   ├── spec_loader.py        # Spec file loading
│   ├── template_engine.py    # Template rendering
│   └── case_conversion.py    # Naming conventions
├── tracking/                 # Change tracking
│   ├── manifest.py           # File tracking
│   ├── differ.py             # Customization detection
│   └── logger.py             # Override logging
└── docker/                   # Docker support
    ├── compose.py            # Docker Compose generation
    └── manager.py            # Docker management
```

## Data Flow

### Generation Pipeline

```
1. Load Spec
   └── specs/models.py → StackSpec

2. Build Context
   └── StackSpec → GeneratorContext

3. Generate Backend
   ├── Models → models/*.py
   ├── Schemas → schemas/*.py
   ├── Services → services/*.py
   ├── REST → api/rest/*.py
   ├── GraphQL → api/graphql/*.py
   └── MCP → mcp_server/*.py

4. Generate Frontend
   ├── Types → types/*.ts
   ├── Components → components/*.tsx
   ├── Hooks → hooks/*.ts
   └── Pages → pages/*.tsx

5. Generate Tests
   ├── Backend → tests/*.py
   └── Frontend → __tests__/*.tsx
```

### Runtime Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Client                              │
│              (Browser / AI Assistant)                    │
└───────────────┬─────────────────────┬───────────────────┘
                │                     │
         HTTP/GraphQL              MCP/stdio
                │                     │
                ▼                     ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     FastAPI Backend       │ │     MCP Server            │
│  ┌─────────────────────┐  │ │  ┌─────────────────────┐  │
│  │   REST Endpoints    │  │ │  │   MCP Tools         │  │
│  ├─────────────────────┤  │ │  └─────────┬───────────┘  │
│  │   GraphQL Schema    │  │ │            │              │
│  └─────────┬───────────┘  │ │            │              │
│            │              │ │            │              │
│            ▼              │ │            ▼              │
│  ┌─────────────────────┐  │ │  ┌─────────────────────┐  │
│  │   Service Layer     │◀─┼─┼──│   Service Layer     │  │
│  └─────────┬───────────┘  │ │  └─────────────────────┘  │
│            │              │ └───────────────────────────┘
│            ▼              │
│  ┌─────────────────────┐  │
│  │   SQLAlchemy ORM    │  │
│  └─────────┬───────────┘  │
└────────────┼──────────────┘
             │
             ▼
     ┌───────────────┐
     │   PostgreSQL  │
     └───────────────┘
```

## Key Design Decisions

### Spec as Code

Specifications are Python code, not YAML/JSON:

- **Type Safety**: IDE support, autocomplete, validation
- **Programmability**: Loops, conditionals, imports
- **Reusability**: Share specs across projects
- **Validation**: Pydantic ensures spec correctness

### Generate Base, Extend User

Separation of generated and custom code:

- **Base files** (`_generated/`) are always regenerated
- **User files** extend base classes and are never touched
- **Customizations are safe** across regenerations

### Async-First

All generated code is async:

- **Database**: `async_sessionmaker`, `AsyncSession`
- **Services**: `async def` methods
- **Endpoints**: Async FastAPI handlers

### Multi-Interface

Same data model exposed through multiple interfaces:

- **REST**: Traditional HTTP API
- **GraphQL**: Flexible query language
- **MCP**: AI assistant tools
- **Frontend**: React components

## See Also

- [Design Principles](design-principles.md) - Philosophy and rationale
- [Generator Architecture](generators.md) - How generation works
- [Code Generation](../user-guide/code-generation.md) - Generated file details

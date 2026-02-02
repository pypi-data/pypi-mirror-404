# Quick Start

Get a full-stack application running in under 5 minutes.

## TL;DR

```bash
prism create my-app && cd my-app && prism install && prism generate && prism test && prism dev
```

## Step-by-Step

### 1. Create a New Project

```bash
prism create my-app
cd my-app
```

This scaffolds a full-stack project with:

```
my-app/
├── packages/
│   ├── backend/          # Python/FastAPI backend
│   │   ├── src/my_app/   # Your Python package
│   │   ├── pyproject.toml
│   │   └── tests/
│   └── frontend/         # React + TypeScript frontend
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
├── specs/
│   └── models.py         # Your model definitions
└── prism.config.py       # Prism configuration
```

### 2. Install Dependencies

```bash
prism install
```

This installs both backend (Python) and frontend (Node.js) dependencies.

### 3. Review the Example Spec

Open `specs/models.py` to see the example model:

```python title="specs/models.py"
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType,
    RESTExposure, GraphQLExposure, FrontendExposure,
)

stack = StackSpec(
    name="my-app",
    version="1.0.0",
    models=[
        ModelSpec(
            name="User",
            fields=[
                FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
            rest=RESTExposure(enabled=True),
            graphql=GraphQLExposure(enabled=True),
            frontend=FrontendExposure(enabled=True),
        ),
    ],
)
```

### 4. Generate Code

```bash
prism generate
```

This generates:

- **Backend**: Models, schemas, services, REST/GraphQL/MCP APIs
- **Frontend**: TypeScript types, React components, hooks
- **Tests**: Unit and integration tests

### 5. Run Tests

```bash
prism test
```

Verifies everything is working correctly.

### 6. Start Development

```bash
prism dev
```

This starts:

- **Backend**: FastAPI server at `http://localhost:8000`
- **Frontend**: Vite dev server at `http://localhost:5173`

Open your browser to:

- **App**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **GraphQL**: [http://localhost:8000/graphql](http://localhost:8000/graphql)

## What's Next?

### Modify Your Models

Edit `specs/models.py` to add or modify models, then regenerate:

```bash
prism generate
```

Your customizations in user files are preserved!

### Add More Models

```python
ModelSpec(
    name="Post",
    fields=[
        FieldSpec(name="title", type=FieldType.STRING, required=True),
        FieldSpec(name="content", type=FieldType.TEXT),
        FieldSpec(name="published", type=FieldType.BOOLEAN, default=False),
    ],
    timestamps=True,  # Adds created_at, updated_at
    soft_delete=True, # Adds deleted_at for soft deletion
)
```

### Use Docker

For containerized development:

```bash
prism docker init
prism dev --docker
```

## Common Commands

| Command | Description |
|---------|-------------|
| `prism create <name>` | Create new project |
| `prism install` | Install dependencies |
| `prism generate` | Generate code from spec |
| `prism generate --dry-run` | Preview changes |
| `prism test` | Run all tests |
| `prism dev` | Start dev servers |
| `prism db migrate` | Create & run migrations |
| `prism validate` | Validate spec file |

## Next Steps

- [First Project Tutorial](first-project.md) - Build a complete CRM
- [Model Specification Guide](../user-guide/spec-guide.md) - Learn all spec options
- [CLI Reference](../user-guide/cli-reference.md) - All available commands

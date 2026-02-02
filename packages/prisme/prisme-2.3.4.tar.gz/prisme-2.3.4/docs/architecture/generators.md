# Generator Architecture

How Prisme's code generation system works internally.

## Overview

Prisme uses a **pipeline-based generator architecture** where each generator is responsible for a specific layer of the application.

## Generator Pipeline

```
┌─────────────────┐
│   Load Spec     │  Parse specs/models.py
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validate      │  Check spec consistency
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Context  │  Create GeneratorContext
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│            Run Generators               │
├─────────────────────────────────────────┤
│  Backend:                               │
│  ├── ModelsGenerator                    │
│  ├── SchemasGenerator                   │
│  ├── ServicesGenerator                  │
│  ├── RESTGenerator                      │
│  ├── GraphQLGenerator                   │
│  └── MCPGenerator                       │
│                                         │
│  Frontend:                              │
│  ├── TypeScriptGenerator                │
│  ├── ComponentsGenerator                │
│  ├── HooksGenerator                     │
│  └── PagesGenerator                     │
│                                         │
│  Testing:                               │
│  ├── BackendTestGenerator               │
│  └── FrontendTestGenerator              │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Write Files   │  Apply file strategies
└─────────────────┘
```

## Core Components

### GeneratorContext

The context holds all information needed for generation:

```python
@dataclass
class GeneratorContext:
    spec: StackSpec              # Loaded specification
    backend_path: Path           # Backend output directory
    frontend_path: Path          # Frontend output directory
    package_name: str            # Python package name
    manifest: Manifest           # File tracking manifest
    dry_run: bool                # Preview mode
```

### GeneratorResult

Each generator returns a result with files to write:

```python
@dataclass
class GeneratedFile:
    path: Path                   # Relative file path
    content: str                 # File content
    strategy: FileStrategy       # Write strategy
    description: str             # Human-readable description

@dataclass
class GeneratorResult:
    files: list[GeneratedFile]   # Files to write
    warnings: list[str]          # Non-fatal issues
```

### Base Generator

All generators inherit from a base class:

```python
class BaseGenerator:
    def __init__(self, context: GeneratorContext):
        self.context = context
        self.spec = context.spec
        self.templates = TemplateRenderer()

    def generate(self) -> GeneratorResult:
        """Generate files. Override in subclass."""
        raise NotImplementedError

    def render_template(self, name: str, **kwargs) -> str:
        """Render a Jinja2 template."""
        return self.templates.render(name, **kwargs)
```

## Generator Types

### ModelsGenerator

Generates SQLAlchemy models.

**Input:**
```python
ModelSpec(
    name="Customer",
    fields=[
        FieldSpec(name="email", type=FieldType.STRING, unique=True),
    ],
    soft_delete=True,
    timestamps=True,
)
```

**Output:**
```python
# models/customer.py
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
```

### SchemasGenerator

Generates Pydantic schemas for validation and serialization.

**Output:**
```python
# schemas/customer_schemas.py
class CustomerBase(BaseModel):
    email: str

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    email: str | None = None

class CustomerRead(CustomerBase):
    id: int
    created_at: datetime
```

### ServicesGenerator

Generates service layer with CRUD operations.

**Strategy:** `GENERATE_BASE` - Base class regenerated, user extends.

**Output:**
```python
# services/_generated/customer_service.py
class CustomerServiceBase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CustomerCreate) -> Customer: ...
    async def read(self, id: int) -> Customer: ...
    async def update(self, id: int, data: CustomerUpdate) -> Customer: ...
    async def delete(self, id: int) -> None: ...
    async def list(self, filters=None, skip=0, limit=20) -> tuple[list, int]: ...

# services/customer_service.py (user file, generated once)
class CustomerService(CustomerServiceBase):
    """Add custom methods here."""
    pass
```

### RESTGenerator

Generates FastAPI endpoints.

**Output:**
```python
# api/rest/customers.py
router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=CustomerRead)
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.create(data)

@router.get("/{id}", response_model=CustomerRead)
async def read_customer(id: int, ...): ...

@router.get("/", response_model=CustomerList)
async def list_customers(...): ...
```

### GraphQLGenerator

Generates Strawberry GraphQL types and resolvers.

**Output:**
```python
# api/graphql/types/customer.py
@strawberry.type
class CustomerType:
    id: int
    email: str
    created_at: datetime

@strawberry.input
class CustomerInput:
    email: str

# api/graphql/queries.py
@strawberry.type
class Query:
    @strawberry.field
    async def customer(self, id: int, info: Info) -> CustomerType | None: ...

    @strawberry.field
    async def customers(self, ...) -> CustomerConnection: ...
```

### TypeScriptGenerator

Generates TypeScript type definitions.

**Output:**
```typescript
// types/customer.ts
export interface Customer {
  id: number;
  email: string;
  createdAt: string;
}

export interface CustomerCreate {
  email: string;
}

export interface CustomerUpdate {
  email?: string;
}
```

### ComponentsGenerator

Generates React components.

**Strategy:** `GENERATE_BASE` - Base component regenerated, user wraps.

**Output:**
```tsx
// components/_generated/CustomerFormBase.tsx
export function CustomerFormBase({ onSubmit, initialData }: Props) {
  const form = useForm<CustomerCreate>({ defaultValues: initialData });
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <TextInput {...form.register("email")} />
      <Button type="submit">Save</Button>
    </form>
  );
}

// components/CustomerForm.tsx (user file)
export function CustomerForm(props: Props) {
  return <CustomerFormBase {...props} />;
}
```

## Template System

### Template Engine

Prisme uses Jinja2 for templates:

```python
class TemplateRenderer:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("prism", "templates/jinja2"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, name: str, **context) -> str:
        template = self.env.get_template(name)
        return template.render(**context)
```

### Template Organization

```
templates/jinja2/
├── backend/
│   ├── model.py.jinja2
│   ├── schema.py.jinja2
│   ├── service.py.jinja2
│   ├── rest_router.py.jinja2
│   └── graphql_type.py.jinja2
├── frontend/
│   ├── types.ts.jinja2
│   ├── component.tsx.jinja2
│   └── hook.ts.jinja2
└── common/
    └── header.jinja2
```

### Template Example

```jinja
{# templates/jinja2/backend/model.py.jinja2 #}
"""{{ model.name }} SQLAlchemy model."""
from sqlalchemy import Column, {{ model.column_imports | join(', ') }}
from sqlalchemy.orm import relationship
from .base import Base

class {{ model.name }}(Base):
    __tablename__ = "{{ model.table_name }}"

    id = Column(Integer, primary_key=True, index=True)
{% for field in model.fields %}
    {{ field.name }} = Column({{ field.column_type }}{{ field.column_args }})
{% endfor %}
{% if model.timestamps %}
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
{% endif %}
{% for rel in model.relationships %}

    {{ rel.name }} = relationship("{{ rel.target }}"{{ rel.args }})
{% endfor %}
```

## File Strategies

### ALWAYS_OVERWRITE

Always regenerated. Never edit manually.

```python
GeneratedFile(
    path=Path("schemas/customer_schemas.py"),
    content=rendered,
    strategy=FileStrategy.ALWAYS_OVERWRITE,
)
```

### GENERATE_ONCE

Created only if doesn't exist.

```python
GeneratedFile(
    path=Path("services/customer_service.py"),
    content=user_template,
    strategy=FileStrategy.GENERATE_ONCE,
)
```

### GENERATE_BASE

Base file always regenerated, user file created once.

```python
# This is always overwritten
GeneratedFile(
    path=Path("services/_generated/customer_service.py"),
    content=base_template,
    strategy=FileStrategy.ALWAYS_OVERWRITE,
)

# This is created once
GeneratedFile(
    path=Path("services/customer_service.py"),
    content=user_template,
    strategy=FileStrategy.GENERATE_ONCE,
)
```

### MERGE

Smart merging with conflict markers.

Used for assembly files like routers that combine multiple sources.

## Manifest Tracking

The manifest tracks all generated files:

```json
{
  "version": "1.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "files": {
    "models/customer.py": {
      "hash": "abc123...",
      "strategy": "ALWAYS_OVERWRITE",
      "generated_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

This enables:
- Detecting customizations to generated files
- Knowing which files to regenerate
- Warning about potential conflicts

## Extending Generators

### Custom Generator

```python
from prism.generators.base import BaseGenerator, GeneratorResult, GeneratedFile

class CustomGenerator(BaseGenerator):
    def generate(self) -> GeneratorResult:
        files = []

        for model in self.spec.models:
            content = self.render_template(
                "custom/my_template.py.jinja2",
                model=model,
            )
            files.append(GeneratedFile(
                path=Path(f"custom/{model.name.lower()}.py"),
                content=content,
                strategy=FileStrategy.ALWAYS_OVERWRITE,
                description=f"Custom file for {model.name}",
            ))

        return GeneratorResult(files=files)
```

### Custom Templates

Add templates to `templates/jinja2/custom/`:

```jinja
{# templates/jinja2/custom/my_template.py.jinja2 #}
"""Custom generated file for {{ model.name }}."""

class {{ model.name }}Custom:
    """Your custom class."""
    pass
```

## See Also

- [Architecture Overview](index.md)
- [Design Principles](design-principles.md)
- [Code Generation Guide](../user-guide/code-generation.md)
- [Extensibility Guide](../user-guide/extensibility.md)

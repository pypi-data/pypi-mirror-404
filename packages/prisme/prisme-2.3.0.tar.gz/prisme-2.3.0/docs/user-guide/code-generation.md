# Code Generation

Understanding what Prisme generates and how to work with generated code.

## Overview

When you run `prism generate`, Prisme analyzes your specification and generates a complete full-stack application. This page explains what gets generated and the patterns used.

## Generated File Categories

### Backend Files

| Category | Location | Description |
|----------|----------|-------------|
| **Models** | `src/<pkg>/models/` | SQLAlchemy ORM models |
| **Schemas** | `src/<pkg>/schemas/` | Pydantic validation schemas |
| **Services** | `src/<pkg>/services/` | Business logic layer |
| **REST API** | `src/<pkg>/api/rest/` | FastAPI endpoints |
| **GraphQL** | `src/<pkg>/api/graphql/` | Strawberry types and resolvers |
| **MCP** | `src/<pkg>/mcp_server/` | FastMCP tools |
| **Tests** | `src/<pkg>/tests/` | pytest test suites |

### Frontend Files

| Category | Location | Description |
|----------|----------|-------------|
| **Types** | `src/types/` | TypeScript type definitions |
| **Components** | `src/components/` | React components (forms, tables) |
| **Hooks** | `src/hooks/` | Custom React hooks |
| **Pages** | `src/pages/` | Page components |
| **GraphQL Ops** | `src/graphql/` | GraphQL queries and mutations |
| **API Client** | `src/api/` | REST API client |
| **Tests** | `src/__tests__/` | Vitest test suites |

## File Generation Strategies

Prisme uses different strategies for different files to balance automation with customization.

### ALWAYS_OVERWRITE

Pure boilerplate that's always regenerated. You should never edit these files.

**Examples:**

- `models/base.py` - Base model class
- `schemas/<model>_schemas.py` - Generated Pydantic schemas
- `types/generated.ts` - TypeScript types

### GENERATE_ONCE

Created only if they don't exist. Edit freely after initial generation.

**Examples:**

- `main.py` - FastAPI application entry
- `config.py` - Application configuration
- `pages/<Model>Page.tsx` - Page components

### GENERATE_BASE

Generates a base class that you extend. Base files are always regenerated; your extension files are never touched.

**Examples:**

- `services/_generated/customer_service.py` (regenerated)
- `services/customer_service.py` (your customizations)
- `components/_generated/CustomerFormBase.tsx` (regenerated)
- `components/CustomerForm.tsx` (your customizations)

### MERGE

Smart merging with conflict markers. Used for assembly files.

**Examples:**

- `api/rest/router.py` - REST router assembly
- `api/graphql/schema.py` - GraphQL schema assembly

## Backend Generation Details

### SQLAlchemy Models

For each model in your spec:

```python
# Generated: models/customer.py
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(Enum("lead", "prospect", "customer"), default="lead")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # soft_delete=True

    # Relationships
    orders = relationship("Order", back_populates="customer")
```

### Pydantic Schemas

Multiple schemas for different operations:

```python
# Generated: schemas/customer_schemas.py

class CustomerBase(BaseModel):
    """Base schema with shared fields."""
    name: str
    email: EmailStr
    status: CustomerStatus = "lead"

class CustomerCreate(CustomerBase):
    """Schema for creating customers."""
    pass

class CustomerUpdate(BaseModel):
    """Schema for updating customers (all optional)."""
    name: str | None = None
    email: EmailStr | None = None
    status: CustomerStatus | None = None

class CustomerRead(CustomerBase):
    """Schema for reading customers."""
    id: int
    created_at: datetime
    updated_at: datetime | None

class CustomerList(BaseModel):
    """Paginated list response."""
    items: list[CustomerRead]
    total: int
    page: int
    page_size: int
```

### Service Layer

Services implement business logic with a base + extension pattern:

```python
# Generated: services/_generated/customer_service.py

class CustomerServiceBase:
    """Base service with CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CustomerCreate) -> Customer:
        ...

    async def read(self, id: int) -> Customer:
        ...

    async def update(self, id: int, data: CustomerUpdate) -> Customer:
        ...

    async def delete(self, id: int) -> None:
        ...

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: CustomerFilters | None = None,
    ) -> tuple[list[Customer], int]:
        ...
```

```python
# Your file: services/customer_service.py

from ._generated.customer_service import CustomerServiceBase

class CustomerService(CustomerServiceBase):
    """Customer service with custom business logic."""

    async def upgrade_to_customer(self, id: int) -> Customer:
        """Custom business method."""
        customer = await self.read(id)
        return await self.update(id, {"status": "customer"})
```

### REST Endpoints

FastAPI routers with full CRUD:

```python
# Generated: api/rest/customers.py

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("/", response_model=CustomerRead)
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
):
    return await service.create(data)

@router.get("/{id}", response_model=CustomerRead)
async def read_customer(id: int, service: CustomerService = Depends()):
    return await service.read(id)

@router.get("/", response_model=CustomerList)
async def list_customers(
    skip: int = 0,
    limit: int = 20,
    filters: CustomerFilters = Depends(),
    service: CustomerService = Depends(),
):
    items, total = await service.list(skip, limit, filters)
    return CustomerList(items=items, total=total, page=skip//limit, page_size=limit)

@router.patch("/{id}", response_model=CustomerRead)
async def update_customer(id: int, data: CustomerUpdate, ...):
    return await service.update(id, data)

@router.delete("/{id}", status_code=204)
async def delete_customer(id: int, ...):
    await service.delete(id)
```

### GraphQL Types

Strawberry GraphQL types and resolvers:

```python
# Generated: api/graphql/types/customer.py

@strawberry.type
class CustomerType:
    id: int
    name: str
    email: str
    status: CustomerStatus
    created_at: datetime

    @strawberry.field
    async def orders(self, info: Info) -> list["OrderType"]:
        return await info.context.loaders.orders_by_customer.load(self.id)

@strawberry.input
class CustomerInput:
    name: str
    email: str
    status: CustomerStatus = "lead"

@strawberry.type
class Query:
    @strawberry.field
    async def customer(self, id: int, info: Info) -> CustomerType | None:
        service = info.context.services.customer
        return await service.read(id)

    @strawberry.field
    async def customers(
        self,
        first: int = 20,
        after: str | None = None,
        info: Info,
    ) -> CustomerConnection:
        ...
```

## Frontend Generation Details

### TypeScript Types

Type-safe definitions matching backend:

```typescript
// Generated: types/customer.ts

export interface Customer {
  id: number;
  name: string;
  email: string;
  status: "lead" | "prospect" | "customer";
  createdAt: string;
  updatedAt: string | null;
}

export interface CustomerCreate {
  name: string;
  email: string;
  status?: "lead" | "prospect" | "customer";
}

export interface CustomerUpdate {
  name?: string;
  email?: string;
  status?: "lead" | "prospect" | "customer";
}

export interface CustomerFilters {
  name?: string;
  email?: string;
  status?: ("lead" | "prospect" | "customer")[];
}
```

### React Components

Form and table components with base + extension pattern:

```tsx
// Generated: components/_generated/CustomerFormBase.tsx

export function CustomerFormBase({
  initialData,
  onSubmit,
  isLoading,
}: CustomerFormProps) {
  const form = useForm<CustomerCreate>({
    defaultValues: initialData,
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <TextInput
        label="Name"
        {...form.register("name", { required: true })}
      />
      <EmailInput
        label="Email"
        {...form.register("email", { required: true })}
      />
      <SelectInput
        label="Status"
        options={["lead", "prospect", "customer"]}
        {...form.register("status")}
      />
      <Button type="submit" loading={isLoading}>
        Save
      </Button>
    </form>
  );
}
```

```tsx
// Your file: components/CustomerForm.tsx

import { CustomerFormBase } from "./_generated/CustomerFormBase";

export function CustomerForm(props: CustomerFormProps) {
  // Add custom validation, styling, or behavior
  return (
    <div className="my-custom-wrapper">
      <CustomerFormBase {...props} />
    </div>
  );
}
```

### React Hooks

Data fetching hooks using your preferred GraphQL client:

```typescript
// Generated: hooks/useCustomer.ts

export function useCustomer(id: number) {
  return useQuery({
    queryKey: ["customer", id],
    queryFn: () => customerApi.read(id),
  });
}

export function useCustomers(filters?: CustomerFilters) {
  return useQuery({
    queryKey: ["customers", filters],
    queryFn: () => customerApi.list(filters),
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: customerApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(["customers"]);
    },
  });
}
```

## Regeneration Workflow

### Safe Regeneration

Your customizations are preserved when you regenerate:

```bash
# 1. Modify your spec
vim specs/models.py

# 2. Preview changes
prism generate --dry-run

# 3. Regenerate
prism generate

# 4. Your custom code in services/customer_service.py is unchanged!
```

### What Gets Updated

| File Type | Regeneration Behavior |
|-----------|----------------------|
| `*_generated/*` | Always overwritten |
| `schemas/*.py` | Always overwritten |
| `types/*.ts` | Always overwritten |
| `services/*.py` | Never touched (user files) |
| `components/*.tsx` | Never touched (user files) |
| `pages/*.tsx` | Never touched (GENERATE_ONCE) |
| `router.py` | Merged with markers |

## Best Practices

### Do

- Extend generated base classes for customization
- Keep custom logic in user service files
- Use the `--dry-run` flag to preview changes
- Commit generated files to version control

### Don't

- Edit files in `_generated/` directories
- Modify schema files directly
- Delete the manifest file (`.prism/manifest.json`)
- Mix generated and custom code in base files

## Troubleshooting

### Missing Generated Files

If files aren't being generated:

```bash
# Check your spec is valid
prism validate

# Force regeneration
prism generate --force
```

### Merge Conflicts

If you see conflict markers in merged files:

```python
<<<<<<< GENERATED
# New generated code
=======
# Your existing code
>>>>>>> EXISTING
```

Manually resolve by keeping the code you want, then remove the markers.

## See Also

- [Extensibility Guide](extensibility.md) - Advanced customization
- [Model Specification Guide](spec-guide.md) - All spec options
- [CLI Reference](cli-reference.md) - Command details

# Extensibility

Learn how to customize Prisme-generated code without losing your changes on regeneration.

## The Extension Pattern

Prisme uses a **generate base, extend user** pattern that separates generated code from your customizations:

```
services/
├── _generated/           # Generated - DO NOT EDIT
│   ├── customer_service.py
│   └── order_service.py
├── customer_service.py   # Your customizations
└── order_service.py      # Your customizations
```

This ensures:

- Generated code is always up-to-date with your spec
- Your customizations are never overwritten
- Clean separation of concerns

## Extending Services

### Basic Extension

Generated services provide CRUD operations. Extend them to add business logic:

```python title="services/customer_service.py"
from ._generated.customer_service import CustomerServiceBase
from ..models import Customer

class CustomerService(CustomerServiceBase):
    """Customer service with custom business logic."""

    async def upgrade_to_customer(self, customer_id: int) -> Customer:
        """Upgrade a lead or prospect to customer status."""
        customer = await self.read(customer_id)
        if customer.status in ("lead", "prospect"):
            return await self.update(customer_id, {"status": "customer"})
        return customer

    async def get_high_value_customers(
        self,
        threshold: float = 10000.0,
    ) -> list[Customer]:
        """Get customers with lifetime value above threshold."""
        query = select(Customer).where(
            Customer.lifetime_value >= threshold,
            Customer.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

### Overriding Base Methods

Override base methods to customize default behavior:

```python title="services/customer_service.py"
class CustomerService(CustomerServiceBase):
    async def create(self, data: CustomerCreate) -> Customer:
        """Override create to add default values and validation."""
        # Custom pre-create logic
        if not data.status:
            data.status = "lead"

        # Call parent implementation
        customer = await super().create(data)

        # Custom post-create logic
        await self._send_welcome_email(customer)

        return customer

    async def delete(self, customer_id: int) -> None:
        """Override to add cascade cleanup."""
        customer = await self.read(customer_id)

        # Custom pre-delete logic
        await self._archive_customer_data(customer)

        # Call parent implementation
        await super().delete(customer_id)
```

### Adding Dependencies

Inject additional dependencies into your services:

```python title="services/customer_service.py"
from ..integrations.email import EmailService
from ..integrations.analytics import AnalyticsService

class CustomerService(CustomerServiceBase):
    def __init__(
        self,
        db: AsyncSession,
        email_service: EmailService,
        analytics: AnalyticsService,
    ):
        super().__init__(db)
        self.email = email_service
        self.analytics = analytics

    async def create(self, data: CustomerCreate) -> Customer:
        customer = await super().create(data)
        await self.email.send_welcome(customer.email)
        await self.analytics.track("customer_created", customer.id)
        return customer
```

## Extending Components

### React Component Extension

Generated components provide UI scaffolding. Extend them for custom styling and behavior:

```tsx title="components/CustomerForm.tsx"
import { CustomerFormBase } from "./_generated/CustomerFormBase";
import type { CustomerFormProps } from "./_generated/CustomerFormBase";

export function CustomerForm(props: CustomerFormProps) {
  const handleSubmit = async (data: CustomerCreate) => {
    // Add validation
    if (!validateEmail(data.email)) {
      toast.error("Invalid email format");
      return;
    }

    // Add analytics
    analytics.track("customer_form_submitted");

    // Call original handler
    await props.onSubmit?.(data);
  };

  return (
    <div className="custom-form-wrapper">
      <h2 className="form-title">Add Customer</h2>
      <CustomerFormBase
        {...props}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
```

### Custom Field Widgets

Override specific field widgets without modifying the entire form:

```tsx title="components/CustomerForm.tsx"
import { CustomerFormBase } from "./_generated/CustomerFormBase";
import { PhoneInput } from "./widgets/PhoneInput";
import { AddressAutocomplete } from "./widgets/AddressAutocomplete";

export function CustomerForm(props: CustomerFormProps) {
  return (
    <CustomerFormBase
      {...props}
      fieldOverrides={{
        phone: (field) => <PhoneInput {...field} countryCode="US" />,
        address: (field) => <AddressAutocomplete {...field} />,
      }}
    />
  );
}
```

### Custom Table Columns

Extend generated tables with custom columns or actions:

```tsx title="components/CustomerTable.tsx"
import { CustomerTableBase } from "./_generated/CustomerTableBase";

export function CustomerTable(props: CustomerTableProps) {
  const customColumns = [
    ...props.columns,
    {
      key: "actions",
      header: "Actions",
      render: (customer) => (
        <div className="flex gap-2">
          <Button onClick={() => handleEdit(customer.id)}>Edit</Button>
          <Button onClick={() => handleDelete(customer.id)} variant="danger">
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <CustomerTableBase
      {...props}
      columns={customColumns}
      onRowClick={(customer) => navigate(`/customers/${customer.id}`)}
    />
  );
}
```

## Extending REST Endpoints

### Adding Custom Endpoints

Add endpoints alongside generated ones:

```python title="api/rest/customers.py"
from ._generated.customers import router, get_customer_service

# Custom endpoint added to generated router
@router.post("/{customer_id}/upgrade")
async def upgrade_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
):
    """Upgrade a lead/prospect to customer status."""
    return await service.upgrade_to_customer(customer_id)

@router.get("/high-value")
async def list_high_value_customers(
    threshold: float = 10000.0,
    service: CustomerService = Depends(get_customer_service),
):
    """List customers with high lifetime value."""
    return await service.get_high_value_customers(threshold)
```

### Overriding Generated Endpoints

Override specific endpoints while keeping others:

```python title="api/rest/customers_override.py"
from fastapi import APIRouter, Depends
from ..services import CustomerService

# Create a new router for overrides
override_router = APIRouter(prefix="/customers", tags=["customers"])

@override_router.get("/{customer_id}")
async def read_customer_with_orders(
    customer_id: int,
    include_orders: bool = False,
    service: CustomerService = Depends(get_customer_service),
):
    """Custom read endpoint that optionally includes orders."""
    customer = await service.read(customer_id)
    if include_orders:
        customer.orders = await service.get_customer_orders(customer_id)
    return customer
```

```python title="main.py"
# Include override router BEFORE generated router to take precedence
app.include_router(override_router)
app.include_router(generated_router)
```

## Extending GraphQL

### Adding Custom Queries

Extend the generated schema with custom queries:

```python title="api/graphql/queries.py"
import strawberry
from ._generated.queries import QueryBase

@strawberry.type
class Query(QueryBase):
    """Extended Query type with custom queries."""

    @strawberry.field
    async def high_value_customers(
        self,
        threshold: float = 10000.0,
        info: strawberry.Info,
    ) -> list[CustomerType]:
        """Get customers with lifetime value above threshold."""
        service = info.context.services.customer
        return await service.get_high_value_customers(threshold)

    @strawberry.field
    async def customer_statistics(
        self,
        info: strawberry.Info,
    ) -> CustomerStatistics:
        """Get aggregate customer statistics."""
        service = info.context.services.customer
        return await service.get_statistics()
```

### Adding Custom Mutations

```python title="api/graphql/mutations.py"
import strawberry
from ._generated.mutations import MutationBase

@strawberry.type
class Mutation(MutationBase):
    """Extended Mutation type."""

    @strawberry.mutation
    async def upgrade_customer(
        self,
        customer_id: int,
        info: strawberry.Info,
    ) -> CustomerType:
        """Upgrade customer status."""
        service = info.context.services.customer
        return await service.upgrade_to_customer(customer_id)

    @strawberry.mutation
    async def merge_customers(
        self,
        source_id: int,
        target_id: int,
        info: strawberry.Info,
    ) -> CustomerType:
        """Merge two customer records."""
        service = info.context.services.customer
        return await service.merge_customers(source_id, target_id)
```

## Widget Customization

### Global Widget Overrides

Configure widget overrides in your spec:

```python title="specs/models.py"
from prism import StackSpec, WidgetConfig

stack = StackSpec(
    name="my-app",
    widgets=WidgetConfig(
        # Override by field type
        type_widgets={
            "string": "CustomTextInput",
            "date": "CustomDatePicker",
        },
        # Override by ui_widget hint
        ui_widgets={
            "currency": "CurrencyInput",
            "phone": "PhoneInput",
            "address": "AddressAutocomplete",
        },
        # Override by Model.field
        field_widgets={
            "Customer.email": "CustomerEmailWidget",
            "Order.total": "OrderTotalWidget",
        },
    ),
    models=[...],
)
```

### Creating Custom Widgets

```tsx title="components/widgets/CurrencyInput.tsx"
import { forwardRef } from "react";
import type { WidgetProps } from "@/prism/widgets";

export const CurrencyInput = forwardRef<HTMLInputElement, WidgetProps>(
  ({ value, onChange, currency = "USD", ...props }, ref) => {
    const formatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    });

    return (
      <div className="currency-input">
        <span className="currency-symbol">{currency}</span>
        <input
          ref={ref}
          type="number"
          step="0.01"
          value={value}
          onChange={(e) => onChange?.(parseFloat(e.target.value))}
          {...props}
        />
      </div>
    );
  }
);
```

## Lifecycle Hooks

Configure model lifecycle hooks in your spec:

```python title="specs/models.py"
ModelSpec(
    name="Customer",
    fields=[...],
    # Lifecycle hooks (function names to call)
    before_create="validate_customer",
    after_create="send_welcome_email",
    before_update="check_permissions",
    after_update="notify_changes",
    before_delete="check_dependencies",
    after_delete="cleanup_resources",
)
```

Implement hooks in your service:

```python title="services/customer_service.py"
class CustomerService(CustomerServiceBase):
    async def validate_customer(self, data: CustomerCreate) -> None:
        """Called before creating a customer."""
        if await self._email_exists(data.email):
            raise ValueError("Email already registered")

    async def send_welcome_email(self, customer: Customer) -> None:
        """Called after creating a customer."""
        await self.email.send(
            to=customer.email,
            template="welcome",
            context={"name": customer.name},
        )

    async def check_dependencies(self, customer: Customer) -> None:
        """Called before deleting a customer."""
        if customer.orders:
            raise ValueError("Cannot delete customer with orders")
```

## Best Practices

### Separation of Concerns

- Keep generated code in `_generated/` directories
- Put all customizations in user files
- Use inheritance for extending, not modification

### Dependency Injection

- Use FastAPI's `Depends()` for service injection
- Create custom dependency factories for complex services
- Avoid hardcoding dependencies in services

### Testing Extensions

Test your extensions separately from generated code:

```python title="tests/services/test_customer_service.py"
async def test_upgrade_to_customer():
    """Test custom upgrade_to_customer method."""
    service = CustomerService(db=mock_db)
    customer = await service.create({"name": "Test", "status": "lead"})

    upgraded = await service.upgrade_to_customer(customer.id)

    assert upgraded.status == "customer"
```

### Documentation

Document your extensions for team members:

```python
class CustomerService(CustomerServiceBase):
    """Customer service with business logic.

    Extensions:
        - upgrade_to_customer: Converts lead/prospect to customer
        - get_high_value_customers: Filters by lifetime value
        - merge_customers: Combines two customer records

    Overrides:
        - create: Adds welcome email
        - delete: Adds cascade cleanup
    """
```

## See Also

- [Code Generation](code-generation.md) - Understanding generated files
- [Model Specification Guide](spec-guide.md) - All spec options
- [Architecture](../architecture/index.md) - Design patterns

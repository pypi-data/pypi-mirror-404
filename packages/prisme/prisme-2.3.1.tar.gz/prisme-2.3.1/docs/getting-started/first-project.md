# First Project Tutorial

In this tutorial, you'll build a complete Customer Relationship Management (CRM) system with Prisme. By the end, you'll have:

- Customer and Order models with relationships
- REST and GraphQL APIs
- MCP tools for AI assistants
- React frontend with forms, tables, and detail views
- Automated tests

## Prerequisites

- Prisme installed ([Installation Guide](installation.md))
- Basic Python knowledge
- Familiarity with REST APIs

## Step 1: Create the Project

```bash
prism create my-crm
cd my-crm
```

## Step 2: Define Your Models

Replace the contents of `specs/models.py` with:

```python title="specs/models.py"
"""CRM Application Specification."""
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RelationshipSpec,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
    CRUDOperations, PaginationConfig, PaginationStyle,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    description="Customer Relationship Management System",
    models=[
        # Customer Model
        ModelSpec(
            name="Customer",
            description="A customer in our CRM system",
            soft_delete=True,
            timestamps=True,
            fields=[
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    searchable=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
                    label="Full Name",
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    indexed=True,
                    ui_widget="email",
                    label="Email Address",
                ),
                FieldSpec(
                    name="phone",
                    type=FieldType.STRING,
                    max_length=20,
                    required=False,
                    ui_widget="phone",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["lead", "prospect", "customer", "churned"],
                    default="lead",
                    filter_operators=[FilterOperator.EQ, FilterOperator.IN],
                ),
                FieldSpec(
                    name="lifetime_value",
                    type=FieldType.DECIMAL,
                    precision=10,
                    scale=2,
                    default=0.0,
                    label="Lifetime Value",
                    ui_widget="currency",
                ),
                FieldSpec(
                    name="notes",
                    type=FieldType.TEXT,
                    required=False,
                    ui_widget="textarea",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="orders",
                    target_model="Order",
                    type="one_to_many",
                    back_populates="customer",
                ),
            ],
            rest=RESTExposure(
                enabled=True,
                tags=["customers"],
                pagination=PaginationConfig(
                    style=PaginationStyle.OFFSET,
                    default_page_size=25,
                    max_page_size=100,
                ),
            ),
            graphql=GraphQLExposure(
                enabled=True,
                use_connection=True,
                enable_subscriptions=True,
            ),
            mcp=MCPExposure(
                enabled=True,
                tool_prefix="customer",
                tool_descriptions={
                    "list": "Search and list customers with optional filters",
                    "read": "Get detailed customer information by ID",
                    "create": "Create a new customer record",
                    "update": "Update an existing customer",
                },
            ),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Customers",
                nav_icon="users",
                generate_form=True,
                generate_table=True,
                generate_detail_view=True,
            ),
        ),

        # Order Model
        ModelSpec(
            name="Order",
            description="A customer order",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="customer_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Customer",
                    required=True,
                ),
                FieldSpec(
                    name="order_number",
                    type=FieldType.STRING,
                    max_length=50,
                    required=True,
                    unique=True,
                    label="Order Number",
                ),
                FieldSpec(
                    name="total",
                    type=FieldType.DECIMAL,
                    precision=10,
                    scale=2,
                    required=True,
                    ui_widget="currency",
                    label="Order Total",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["pending", "processing", "shipped", "delivered", "cancelled"],
                    default="pending",
                    filter_operators=[FilterOperator.EQ, FilterOperator.IN],
                ),
                FieldSpec(
                    name="notes",
                    type=FieldType.TEXT,
                    required=False,
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="customer",
                    target_model="Customer",
                    type="many_to_one",
                    back_populates="orders",
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["orders"]),
            graphql=GraphQLExposure(enabled=True, use_connection=True),
            mcp=MCPExposure(enabled=True, tool_prefix="order"),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Orders",
                nav_icon="shopping-cart",
            ),
        ),
    ],
)
```

## Step 3: Install Dependencies

```bash
prism install
```

## Step 4: Generate Code

```bash
prism generate
```

Review what was generated:

```bash
# Backend files
ls packages/backend/src/my_crm/models/
ls packages/backend/src/my_crm/schemas/
ls packages/backend/src/my_crm/services/
ls packages/backend/src/my_crm/api/rest/
ls packages/backend/src/my_crm/api/graphql/
ls packages/backend/src/my_crm/mcp_server/

# Frontend files
ls packages/frontend/src/types/
ls packages/frontend/src/components/
ls packages/frontend/src/hooks/
ls packages/frontend/src/pages/
```

## Step 5: Initialize Database

```bash
prism db init
prism db migrate -m "Initial schema"
```

## Step 6: Run Tests

```bash
prism test
```

All tests should pass!

## Step 7: Start Development

```bash
prism dev
```

Open your browser:

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **GraphQL Playground**: [http://localhost:8000/graphql](http://localhost:8000/graphql)

## Step 8: Explore the APIs

### REST API

Create a customer:

```bash
curl -X POST http://localhost:8000/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "status": "prospect"
  }'
```

List customers:

```bash
curl http://localhost:8000/api/customers
```

### GraphQL API

Open the GraphQL playground at [http://localhost:8000/graphql](http://localhost:8000/graphql) and try:

```graphql
# Create a customer
mutation {
  createCustomer(input: {
    name: "Jane Doe"
    email: "jane@example.com"
    status: PROSPECT
  }) {
    id
    name
    email
  }
}

# Query customers
query {
  customers(first: 10) {
    edges {
      node {
        id
        name
        email
        status
        orders {
          orderNumber
          total
        }
      }
    }
    pageInfo {
      hasNextPage
    }
  }
}
```

## Step 9: Customize Generated Code

Prisme uses a "generate base, extend user" pattern. You can safely customize generated code.

### Customize a Service

The generated service is in `packages/backend/src/my_crm/services/_generated/customer_service.py`. To add custom logic, edit the user service:

```python title="packages/backend/src/my_crm/services/customer_service.py"
from ._generated.customer_service import CustomerServiceBase

class CustomerService(CustomerServiceBase):
    """Customer service with custom business logic."""

    async def upgrade_to_customer(self, customer_id: int) -> Customer:
        """Upgrade a lead/prospect to customer status."""
        customer = await self.read(customer_id)
        if customer.status in ("lead", "prospect"):
            customer = await self.update(customer_id, {"status": "customer"})
        return customer
```

### Customize a React Component

Similarly, you can extend generated frontend components:

```tsx title="packages/frontend/src/components/CustomerForm.tsx"
import { CustomerFormBase } from './_generated/CustomerFormBase';

export function CustomerForm(props) {
  // Add custom validation, styling, or behavior
  return (
    <CustomerFormBase
      {...props}
      onSubmit={(data) => {
        // Add custom pre-submit logic
        console.log('Submitting customer:', data);
        props.onSubmit?.(data);
      }}
    />
  );
}
```

## Step 10: Regenerate Without Losing Changes

When you modify your spec and regenerate, your customizations are preserved:

```bash
# Add a new field to Customer in specs/models.py
# ...

# Regenerate
prism generate

# Your custom CustomerService.upgrade_to_customer() is still there!
```

## What You've Built

Congratulations! You now have a complete CRM with:

- **Database**: PostgreSQL schema with migrations
- **REST API**: Full CRUD endpoints with pagination and filtering
- **GraphQL API**: Type-safe queries, mutations, and subscriptions
- **MCP Tools**: AI assistant integration
- **Frontend**: React app with forms, tables, and navigation
- **Tests**: Automated test coverage

## Next Steps

- [Model Specification Guide](../user-guide/spec-guide.md) - Learn all spec options
- [Extensibility Guide](../user-guide/extensibility.md) - Advanced customization
- [Docker Development](../user-guide/docker-development.md) - Containerized development
- [MCP Integration Tutorial](../tutorials/mcp-integration.md) - Build AI-powered features

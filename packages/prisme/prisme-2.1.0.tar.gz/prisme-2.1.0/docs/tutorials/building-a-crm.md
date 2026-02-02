# Building a CRM

In this tutorial, you'll build a complete Customer Relationship Management (CRM) system with Prisme.

## What You'll Build

A CRM application with:

- **Customers** with contact info, status tracking, and lifetime value
- **Orders** linked to customers with status workflow
- **REST API** with filtering, pagination, and sorting
- **GraphQL API** with connections and subscriptions
- **React frontend** with forms, tables, and navigation

## Prerequisites

- Prisme installed
- Python 3.13+
- Node.js 22+
- PostgreSQL (or SQLite for development)

## Step 1: Create the Project

```bash
prism create my-crm
cd my-crm
```

## Step 2: Define the Data Models

Replace `specs/models.py` with:

```python title="specs/models.py"
"""CRM Application Specification."""
from prism import (
    StackSpec, ModelSpec, FieldSpec, FieldType, FilterOperator,
    RelationshipSpec, TemporalConfig,
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
    CRUDOperations, PaginationConfig, PaginationStyle,
    DatabaseConfig, GraphQLConfig,
)

stack = StackSpec(
    name="my-crm",
    version="1.0.0",
    description="Customer Relationship Management System",

    # Database configuration
    database=DatabaseConfig(
        dialect="postgresql",
        async_driver=True,
    ),

    # GraphQL configuration
    graphql=GraphQLConfig(
        enabled=True,
        subscriptions_enabled=True,
        graphiql=True,
    ),

    models=[
        # =========================================
        # CUSTOMER MODEL
        # =========================================
        ModelSpec(
            name="Customer",
            description="A customer in our CRM system",
            soft_delete=True,
            timestamps=True,
            fields=[
                # Basic Information
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    searchable=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
                    label="Full Name",
                    description="Customer's full name",
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    indexed=True,
                    pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                    ui_widget="email",
                    label="Email Address",
                ),
                FieldSpec(
                    name="phone",
                    type=FieldType.STRING,
                    max_length=20,
                    required=False,
                    ui_widget="phone",
                    label="Phone Number",
                ),
                FieldSpec(
                    name="company",
                    type=FieldType.STRING,
                    max_length=255,
                    required=False,
                    searchable=True,
                    label="Company Name",
                ),

                # Status and Classification
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["lead", "prospect", "customer", "churned"],
                    default="lead",
                    filter_operators=[FilterOperator.EQ, FilterOperator.IN],
                    label="Customer Status",
                ),
                FieldSpec(
                    name="source",
                    type=FieldType.ENUM,
                    enum_values=["website", "referral", "advertising", "cold_outreach", "other"],
                    required=False,
                    label="Lead Source",
                ),

                # Financial
                FieldSpec(
                    name="lifetime_value",
                    type=FieldType.DECIMAL,
                    precision=12,
                    scale=2,
                    default=0.0,
                    label="Lifetime Value",
                    ui_widget="currency",
                    ui_widget_props={"currency": "USD"},
                ),

                # Additional Info
                FieldSpec(
                    name="notes",
                    type=FieldType.TEXT,
                    required=False,
                    ui_widget="textarea",
                    label="Notes",
                ),
                FieldSpec(
                    name="tags",
                    type=FieldType.JSON,
                    json_item_type="str",
                    required=False,
                    ui_widget="tags",
                    label="Tags",
                ),
            ],

            # Relationships
            relationships=[
                RelationshipSpec(
                    name="orders",
                    target_model="Order",
                    type="one_to_many",
                    back_populates="customer",
                    cascade="all, delete-orphan",
                ),
                RelationshipSpec(
                    name="contacts",
                    target_model="Contact",
                    type="one_to_many",
                    back_populates="customer",
                ),
            ],

            # API Exposure
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
            ),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Customers",
                nav_icon="users",
                table_columns=["name", "email", "company", "status", "lifetime_value"],
            ),
        ),

        # =========================================
        # ORDER MODEL
        # =========================================
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
                    precision=12,
                    scale=2,
                    required=True,
                    ui_widget="currency",
                    label="Order Total",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
                    default="pending",
                    filter_operators=[FilterOperator.EQ, FilterOperator.IN],
                    label="Order Status",
                ),
                FieldSpec(
                    name="shipping_address",
                    type=FieldType.TEXT,
                    required=False,
                    ui_widget="textarea",
                    label="Shipping Address",
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

        # =========================================
        # CONTACT MODEL
        # =========================================
        ModelSpec(
            name="Contact",
            description="Additional contacts for a customer",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="customer_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Customer",
                    required=True,
                ),
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    label="Contact Name",
                ),
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    ui_widget="email",
                ),
                FieldSpec(
                    name="phone",
                    type=FieldType.STRING,
                    max_length=20,
                    ui_widget="phone",
                ),
                FieldSpec(
                    name="role",
                    type=FieldType.STRING,
                    max_length=100,
                    label="Job Title/Role",
                ),
                FieldSpec(
                    name="is_primary",
                    type=FieldType.BOOLEAN,
                    default=False,
                    label="Primary Contact",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="customer",
                    target_model="Customer",
                    type="many_to_one",
                    back_populates="contacts",
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["contacts"]),
            graphql=GraphQLExposure(enabled=True),
            frontend=FrontendExposure(enabled=False),  # Managed through Customer UI
        ),
    ],
)
```

## Step 3: Install Dependencies and Generate

```bash
# Install dependencies
prism install

# Generate all code
prism generate

# Review what was generated
ls packages/backend/src/my_crm/
ls packages/frontend/src/
```

## Step 4: Set Up the Database

```bash
# Initialize migrations
prism db init

# Create and apply initial migration
prism db migrate -m "initial schema"
```

## Step 5: Run Tests

```bash
prism test
```

All generated tests should pass.

## Step 6: Start Development

```bash
prism dev
```

Open your browser:

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **GraphQL**: http://localhost:8000/graphql

## Step 7: Add Custom Business Logic

Let's add some custom features to our CRM.

### Customer Upgrade Logic

```python title="packages/backend/src/my_crm/services/customer_service.py"
from ._generated.customer_service import CustomerServiceBase
from ..models import Customer
from decimal import Decimal

class CustomerService(CustomerServiceBase):
    """Customer service with CRM business logic."""

    async def upgrade_to_customer(self, customer_id: int) -> Customer:
        """Upgrade a lead or prospect to customer status."""
        customer = await self.read(customer_id)
        if customer.status in ("lead", "prospect"):
            return await self.update(customer_id, {"status": "customer"})
        return customer

    async def calculate_lifetime_value(self, customer_id: int) -> Decimal:
        """Calculate and update customer lifetime value from orders."""
        from sqlalchemy import select, func
        from ..models import Order

        query = (
            select(func.sum(Order.total))
            .where(Order.customer_id == customer_id)
            .where(Order.status.in_(["delivered"]))
        )
        result = await self.db.execute(query)
        total = result.scalar() or Decimal("0.00")

        await self.update(customer_id, {"lifetime_value": total})
        return total

    async def get_customers_by_status(self, status: str) -> list[Customer]:
        """Get all customers with a specific status."""
        from sqlalchemy import select

        query = select(Customer).where(
            Customer.status == status,
            Customer.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

### Order Status Workflow

```python title="packages/backend/src/my_crm/services/order_service.py"
from ._generated.order_service import OrderServiceBase
from ..models import Order

class OrderService(OrderServiceBase):
    """Order service with workflow logic."""

    VALID_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["processing", "cancelled"],
        "processing": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": [],
        "cancelled": [],
    }

    async def transition_status(
        self,
        order_id: int,
        new_status: str,
    ) -> Order:
        """Transition order to a new status with validation."""
        order = await self.read(order_id)
        current = order.status

        if new_status not in self.VALID_TRANSITIONS.get(current, []):
            valid = self.VALID_TRANSITIONS.get(current, [])
            raise ValueError(
                f"Cannot transition from '{current}' to '{new_status}'. "
                f"Valid transitions: {valid}"
            )

        updated = await self.update(order_id, {"status": new_status})

        # Update customer lifetime value when order is delivered
        if new_status == "delivered":
            from .customer_service import CustomerService
            customer_service = CustomerService(self.db)
            await customer_service.calculate_lifetime_value(order.customer_id)

        return updated
```

### Add Custom API Endpoint

```python title="packages/backend/src/my_crm/api/rest/customers.py"
# Add to the existing customers router

@router.post("/{customer_id}/upgrade", response_model=CustomerRead)
async def upgrade_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
):
    """Upgrade a lead or prospect to customer status."""
    return await service.upgrade_to_customer(customer_id)

@router.get("/by-status/{status}", response_model=list[CustomerRead])
async def list_customers_by_status(
    status: str,
    service: CustomerService = Depends(get_customer_service),
):
    """Get all customers with a specific status."""
    return await service.get_customers_by_status(status)
```

## Step 8: Test Your Custom Logic

```python title="packages/backend/tests/services/test_customer_service.py"
import pytest
from my_crm.services import CustomerService

@pytest.mark.asyncio
async def test_upgrade_to_customer(db_session):
    service = CustomerService(db_session)

    # Create a lead
    customer = await service.create({
        "name": "Test Customer",
        "email": "test@example.com",
        "status": "lead",
    })
    assert customer.status == "lead"

    # Upgrade to customer
    upgraded = await service.upgrade_to_customer(customer.id)
    assert upgraded.status == "customer"

@pytest.mark.asyncio
async def test_calculate_lifetime_value(db_session):
    customer_service = CustomerService(db_session)
    order_service = OrderService(db_session)

    # Create customer and orders
    customer = await customer_service.create({
        "name": "Test",
        "email": "test@example.com",
    })

    await order_service.create({
        "customer_id": customer.id,
        "order_number": "ORD-001",
        "total": 100.00,
        "status": "delivered",
    })

    # Calculate LTV
    ltv = await customer_service.calculate_lifetime_value(customer.id)
    assert ltv == Decimal("100.00")
```

Run the tests:

```bash
prism test --backend-only
```

## Step 9: Explore the Application

### REST API

```bash
# Create a customer
curl -X POST http://localhost:8000/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "company": "Acme Corp",
    "status": "prospect",
    "source": "website"
  }'

# List customers
curl "http://localhost:8000/api/customers?status=prospect"

# Upgrade customer
curl -X POST http://localhost:8000/api/customers/1/upgrade
```

### GraphQL

Open http://localhost:8000/graphql and try:

```graphql
# Create a customer
mutation {
  createCustomer(input: {
    name: "Widget Inc"
    email: "hello@widget.io"
    status: LEAD
  }) {
    id
    name
    status
  }
}

# Query customers with orders
query {
  customers(first: 10) {
    edges {
      node {
        id
        name
        email
        lifetimeValue
        orders {
          orderNumber
          total
          status
        }
      }
    }
  }
}
```

## Summary

You've built a complete CRM with:

- Three related models (Customer, Order, Contact)
- Full REST and GraphQL APIs
- Custom business logic (upgrades, LTV calculation, workflow)
- React frontend with navigation
- Comprehensive test coverage

## Next Steps

- [MCP Integration](mcp-integration.md) - Add AI assistant capabilities
- [Extensibility Guide](../user-guide/extensibility.md) - More customization options
- [Docker Development](../user-guide/docker-development.md) - Containerized development

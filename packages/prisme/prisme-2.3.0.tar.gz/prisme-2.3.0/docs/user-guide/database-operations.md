# Database Operations

Managing databases, migrations, and data in Prisme projects.

## Overview

Prisme uses:

- **SQLAlchemy** for ORM and database models
- **Alembic** for database migrations
- **PostgreSQL** or **SQLite** as the database backend

## Database Configuration

### PostgreSQL (Recommended for Production)

```python title="config.py"
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/myapp"

settings = Settings()
```

### SQLite (Development)

```python title="config.py"
class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data.db"
```

### Environment Variables

```bash title=".env"
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myapp
```

## Migrations

### Initialize Migrations

First-time setup for Alembic:

```bash
prism db init
```

This creates:

```
alembic/
├── versions/        # Migration files
├── env.py           # Alembic environment
└── alembic.ini      # Alembic configuration
```

### Create and Apply Migrations

```bash
# Auto-generate migration from model changes
prism db migrate

# With descriptive message
prism db migrate -m "add customer status field"
```

This:

1. Compares models to database schema
2. Generates a migration file
3. Applies the migration

### Manual Migration Review

Before applying, review the generated migration:

```python title="alembic/versions/20240115_add_customer_status.py"
"""add customer status field

Revision ID: abc123
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('customers',
        sa.Column('status', sa.String(50), nullable=True)
    )
    op.execute("UPDATE customers SET status = 'active'")
    op.alter_column('customers', 'status', nullable=False)

def downgrade():
    op.drop_column('customers', 'status')
```

### Migration Commands

```bash
# Apply all pending migrations
prism db migrate

# Check migration status
alembic current

# View migration history
alembic history

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Generate empty migration (for custom SQL)
alembic revision -m "custom data migration"
```

## Database Operations

### Reset Database

!!! warning "Data Loss"
    This deletes all data. Use with caution!

```bash
prism db reset
```

This:

1. Drops all tables
2. Runs all migrations from scratch
3. Optionally seeds test data

### Seed Data

Populate the database with test data:

```bash
prism db seed
```

#### Custom Seed Data

Create a seed file:

```python title="scripts/seed.py"
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models import Customer, Order

async def seed_customers(db: AsyncSession):
    """Create sample customers."""
    customers = [
        Customer(name="Acme Corp", email="contact@acme.com", status="customer"),
        Customer(name="Widget Inc", email="hello@widget.io", status="prospect"),
    ]
    db.add_all(customers)
    await db.commit()

async def seed_orders(db: AsyncSession):
    """Create sample orders."""
    customer = await db.get(Customer, 1)
    orders = [
        Order(customer_id=customer.id, order_number="ORD-001", total=99.99),
        Order(customer_id=customer.id, order_number="ORD-002", total=149.99),
    ]
    db.add_all(orders)
    await db.commit()
```

## Docker Database Operations

### View Logs

```bash
prism docker logs db
```

### Connect to Database

```bash
# Open psql shell
prism docker shell db

# Inside container:
psql -U postgres -d myapp
```

### Backup

```bash
prism docker backup-db backup-2024-01-15.sql
```

### Restore

```bash
prism docker restore-db backup-2024-01-15.sql
```

### Reset

```bash
prism docker reset-db
```

## Common Patterns

### Soft Delete

Enable soft delete in your model spec:

```python
ModelSpec(
    name="Customer",
    soft_delete=True,  # Adds deleted_at column
    ...
)
```

Generated service methods handle soft delete automatically:

```python
# Soft delete (sets deleted_at)
await service.delete(customer_id)

# Query excludes soft-deleted by default
customers = await service.list()  # Only non-deleted

# Include soft-deleted
all_customers = await service.list(include_deleted=True)

# Permanently delete
await service.hard_delete(customer_id)

# Restore soft-deleted
await service.restore(customer_id)
```

### Timestamps

Enable automatic timestamps:

```python
ModelSpec(
    name="Customer",
    timestamps=True,  # Adds created_at, updated_at
    ...
)
```

These are automatically managed:

- `created_at`: Set on insert
- `updated_at`: Set on every update

### Transactions

Services use transactions automatically. For custom transactions:

```python
async def transfer_orders(
    self,
    from_customer_id: int,
    to_customer_id: int,
) -> None:
    """Transfer all orders from one customer to another."""
    async with self.db.begin():  # Transaction context
        orders = await self.order_service.list(
            filters={"customer_id": from_customer_id}
        )
        for order in orders:
            await self.order_service.update(
                order.id,
                {"customer_id": to_customer_id}
            )
```

### Bulk Operations

For performance with large datasets:

```python
from sqlalchemy import update, delete

async def bulk_update_status(
    self,
    customer_ids: list[int],
    new_status: str,
) -> int:
    """Update status for multiple customers."""
    stmt = (
        update(Customer)
        .where(Customer.id.in_(customer_ids))
        .values(status=new_status)
    )
    result = await self.db.execute(stmt)
    await self.db.commit()
    return result.rowcount

async def bulk_delete(self, customer_ids: list[int]) -> int:
    """Delete multiple customers."""
    stmt = delete(Customer).where(Customer.id.in_(customer_ids))
    result = await self.db.execute(stmt)
    await self.db.commit()
    return result.rowcount
```

### Raw SQL

When you need raw SQL:

```python
from sqlalchemy import text

async def custom_report(self) -> list[dict]:
    """Run custom SQL query."""
    sql = text("""
        SELECT
            c.status,
            COUNT(*) as count,
            SUM(c.lifetime_value) as total_value
        FROM customers c
        WHERE c.deleted_at IS NULL
        GROUP BY c.status
    """)
    result = await self.db.execute(sql)
    return [dict(row._mapping) for row in result]
```

## Troubleshooting

### Migration Conflicts

If you get migration conflicts after merging branches:

```bash
# View current heads
alembic heads

# Create merge migration
alembic merge heads -m "merge branches"

# Apply
alembic upgrade head
```

### Schema Out of Sync

If models and database are out of sync:

```bash
# Check what would be generated
alembic revision --autogenerate -m "check sync" --sql

# Review and apply if correct
prism db migrate
```

### Connection Issues

```bash
# Test connection
python -c "from myapp.database import engine; print(engine.url)"

# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check credentials in .env
cat .env | grep DATABASE_URL
```

### Performance Issues

For slow queries:

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or in config
class Settings(BaseSettings):
    database_echo: bool = True  # Log all SQL
```

Add indexes in your spec:

```python
FieldSpec(
    name="email",
    type=FieldType.STRING,
    indexed=True,  # Creates database index
)
```

## Best Practices

### Development

- Use SQLite for fast local development
- Use Docker PostgreSQL for team consistency
- Always review generated migrations before applying

### Production

- Always use PostgreSQL
- Test migrations on staging first
- Backup before applying migrations
- Use connection pooling (configured automatically)

### Migrations

- Write reversible migrations (include `downgrade()`)
- Use descriptive migration messages
- Split large migrations into smaller steps
- Test rollback works correctly

## See Also

- [Docker Development](docker-development.md) - Docker database management
- [Model Specification Guide](spec-guide.md) - Database-related options
- [CLI Reference](cli-reference.md) - Database commands

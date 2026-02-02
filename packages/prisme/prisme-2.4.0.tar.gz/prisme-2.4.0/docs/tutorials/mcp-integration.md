# MCP Integration

Learn how to connect your Prisme application with AI assistants using Model Context Protocol (MCP).

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) (MCP) is an open protocol that enables AI assistants (like Claude) to securely interact with external tools and data sources. Prisme automatically generates MCP tools for your models.

## What You'll Learn

- How Prisme generates MCP tools
- Configuring MCP exposure for your models
- Testing MCP tools locally
- Connecting to Claude Desktop

## Prerequisites

- Completed [Building a CRM](building-a-crm.md) tutorial (or any Prisme project)
- [Claude Desktop](https://claude.ai/download) installed (for testing)
- Basic understanding of AI assistants

## Step 1: Enable MCP in Your Spec

MCP is enabled per-model in your specification:

```python title="specs/models.py"
from prism import ModelSpec, MCPExposure

ModelSpec(
    name="Customer",
    fields=[...],
    mcp=MCPExposure(
        enabled=True,
        tool_prefix="customer",  # Tools will be: customer_list, customer_read, etc.
        tool_descriptions={
            "list": "Search and list customers with optional filters",
            "read": "Get detailed customer information by ID",
            "create": "Create a new customer record",
            "update": "Update an existing customer's information",
            "delete": "Delete a customer record",
        },
        field_descriptions={
            "name": "Customer's full name",
            "email": "Primary email address",
            "status": "Customer status: lead, prospect, customer, or churned",
            "lifetime_value": "Total revenue from this customer in USD",
        },
    ),
)
```

## Step 2: Understand Generated MCP Tools

When you run `prism generate`, Prisme creates MCP tools in `packages/backend/src/<pkg>/mcp_server/`.

### Generated Tool Structure

```python title="mcp_server/tools/customer_tools.py (generated)"
from fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("my-crm")

class CustomerListInput(BaseModel):
    """Input schema for customer_list tool."""
    name: str | None = Field(None, description="Filter by customer name")
    email: str | None = Field(None, description="Filter by email address")
    status: str | None = Field(None, description="Filter by status")
    limit: int = Field(20, description="Maximum results to return")

@mcp.tool()
async def customer_list(input: CustomerListInput) -> list[dict]:
    """Search and list customers with optional filters."""
    service = get_customer_service()
    customers, total = await service.list(
        filters=input.model_dump(exclude_none=True),
        limit=input.limit,
    )
    return [c.model_dump() for c in customers]

@mcp.tool()
async def customer_read(id: int) -> dict:
    """Get detailed customer information by ID."""
    service = get_customer_service()
    customer = await service.read(id)
    return customer.model_dump()

@mcp.tool()
async def customer_create(
    name: str = Field(..., description="Customer's full name"),
    email: str = Field(..., description="Primary email address"),
    status: str = Field("lead", description="Initial status"),
) -> dict:
    """Create a new customer record."""
    service = get_customer_service()
    customer = await service.create({
        "name": name,
        "email": email,
        "status": status,
    })
    return customer.model_dump()
```

## Step 3: Run the MCP Server

Prisme generates an MCP server that can run standalone:

```bash
# Navigate to backend
cd packages/backend

# Run MCP server
uv run python -m my_crm.mcp_server
```

The server uses stdio transport by default (for Claude Desktop integration).

## Step 4: Test MCP Tools Locally

### Using the MCP CLI

```bash
# Install MCP inspector
pip install mcp-cli

# Connect to your server
mcp connect "uv run python -m my_crm.mcp_server"

# List available tools
/tools

# Call a tool
/call customer_list {"limit": 5}
/call customer_read {"id": 1}
/call customer_create {"name": "Test Customer", "email": "test@example.com"}
```

### Using Python

```python title="test_mcp.py"
import asyncio
from my_crm.mcp_server import mcp

async def test_tools():
    # List customers
    result = await mcp.call_tool("customer_list", {"limit": 5})
    print("Customers:", result)

    # Create customer
    new_customer = await mcp.call_tool("customer_create", {
        "name": "Test User",
        "email": "test@example.com",
    })
    print("Created:", new_customer)

asyncio.run(test_tools())
```

## Step 5: Connect to Claude Desktop

### Configure Claude Desktop

Add your MCP server to Claude Desktop's configuration:

```json title="~/Library/Application Support/Claude/claude_desktop_config.json"
{
  "mcpServers": {
    "my-crm": {
      "command": "uv",
      "args": ["run", "python", "-m", "my_crm.mcp_server"],
      "cwd": "/path/to/my-crm/packages/backend"
    }
  }
}
```

On Windows:
```json title="%APPDATA%/Claude/claude_desktop_config.json"
{
  "mcpServers": {
    "my-crm": {
      "command": "uv",
      "args": ["run", "python", "-m", "my_crm.mcp_server"],
      "cwd": "C:\\path\\to\\my-crm\\packages\\backend"
    }
  }
}
```

### Restart Claude Desktop

After updating the config, restart Claude Desktop. You should see a hammer icon indicating tools are available.

### Test with Claude

Now you can ask Claude to interact with your CRM:

> "List all my customers"

> "Create a new customer named Acme Corp with email contact@acme.com"

> "Show me details for customer #1"

> "What customers have 'prospect' status?"

## Step 6: Add Custom MCP Tools

Extend the generated tools with custom functionality:

```python title="mcp_server/tools/custom_tools.py"
from fastmcp import FastMCP
from ..tools import mcp  # Import the generated MCP instance

@mcp.tool()
async def customer_upgrade(customer_id: int) -> dict:
    """Upgrade a lead or prospect to customer status.

    Args:
        customer_id: The ID of the customer to upgrade
    """
    from ..services import CustomerService
    service = get_customer_service()
    customer = await service.upgrade_to_customer(customer_id)
    return {
        "success": True,
        "customer": customer.model_dump(),
        "message": f"Customer {customer.name} upgraded to customer status",
    }

@mcp.tool()
async def customer_statistics() -> dict:
    """Get aggregate statistics about customers.

    Returns counts by status and total lifetime value.
    """
    from sqlalchemy import select, func
    from ..models import Customer

    # Query statistics
    stats = await db.execute(
        select(
            Customer.status,
            func.count().label("count"),
            func.sum(Customer.lifetime_value).label("total_value"),
        ).group_by(Customer.status)
    )

    return {
        "by_status": [
            {"status": row.status, "count": row.count, "value": float(row.total_value or 0)}
            for row in stats
        ],
    }

@mcp.tool()
async def recent_orders(
    days: int = 7,
    limit: int = 10,
) -> list[dict]:
    """Get recent orders from the last N days.

    Args:
        days: Number of days to look back (default: 7)
        limit: Maximum orders to return (default: 10)
    """
    from datetime import datetime, timedelta
    from ..services import OrderService

    service = get_order_service()
    cutoff = datetime.utcnow() - timedelta(days=days)

    orders, _ = await service.list(
        filters={"created_at_gte": cutoff},
        limit=limit,
        sort_by="created_at",
        sort_desc=True,
    )

    return [o.model_dump() for o in orders]
```

## Step 7: MCP Resources

MCP also supports "resources" - data that can be read by the AI. Enable resource exposure:

```python title="specs/models.py"
MCPExposure(
    enabled=True,
    tool_prefix="customer",
    expose_as_resource=True,
    resource_uri_template="customer://{id}",
)
```

This allows Claude to directly read customer data:

> "Read the customer resource at customer://1"

## Best Practices

### Tool Descriptions

Write clear, specific tool descriptions that help the AI understand when to use each tool:

```python
MCPExposure(
    tool_descriptions={
        # Good - specific and actionable
        "list": "Search customers by name, email, or status. Returns paginated results.",

        # Bad - vague
        "list": "Get customers",
    }
)
```

### Field Descriptions

Provide context for fields, especially enums:

```python
MCPExposure(
    field_descriptions={
        "status": "Customer lifecycle stage: 'lead' (new contact), 'prospect' (qualified), 'customer' (paying), 'churned' (lost)",
    }
)
```

### Error Handling

MCP tools should return helpful error messages:

```python
@mcp.tool()
async def customer_upgrade(customer_id: int) -> dict:
    try:
        customer = await service.upgrade_to_customer(customer_id)
        return {"success": True, "customer": customer.model_dump()}
    except CustomerNotFoundError:
        return {"success": False, "error": f"Customer {customer_id} not found"}
    except InvalidStatusError as e:
        return {"success": False, "error": str(e)}
```

### Security

Be mindful of what data is exposed:

```python
MCPExposure(
    enabled=True,
    operations=CRUDOperations(
        create=True,
        read=True,
        update=True,
        delete=False,  # Disable destructive operations
        list=True,
    ),
)
```

## Troubleshooting

### Tools Not Appearing in Claude

1. Check Claude Desktop config file syntax (valid JSON)
2. Verify the `cwd` path is correct
3. Restart Claude Desktop after config changes
4. Check the MCP server runs standalone: `uv run python -m my_crm.mcp_server`

### Database Connection Errors

Ensure your database is running and accessible:

```bash
# Check database
prism docker logs db

# Or test connection
python -c "from my_crm.database import engine; print(engine.url)"
```

### Tool Execution Errors

Check the MCP server logs:

```bash
# Run with debug logging
DEBUG=1 uv run python -m my_crm.mcp_server
```

## Summary

You've learned how to:

- Configure MCP exposure for Prisme models
- Understand generated MCP tools
- Test tools locally
- Connect to Claude Desktop
- Add custom MCP tools

## Next Steps

- [Model Specification Guide](../user-guide/spec-guide.md) - More MCP options
- [Extensibility Guide](../user-guide/extensibility.md) - Advanced customization
- [MCP Documentation](https://modelcontextprotocol.io/) - Official MCP docs

"""Exposure configuration models for Prism.

This module defines how models are exposed via REST, GraphQL, MCP, and Frontend.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CRUDOperations(BaseModel):
    """Configure which CRUD operations to expose.

    Example:
        >>> ops = CRUDOperations(create=True, read=True, update=True, delete=False)
    """

    create: bool = Field(default=True, description="Enable create operation")
    read: bool = Field(default=True, description="Enable read/get operation")
    update: bool = Field(default=True, description="Enable update operation")
    delete: bool = Field(default=True, description="Enable delete operation")
    list: bool = Field(default=True, description="Enable list operation")

    model_config = {"extra": "forbid"}


class PaginationStyle(str, Enum):
    """Pagination styles for list operations."""

    OFFSET = "offset"
    CURSOR = "cursor"
    LIMIT_OFFSET = "limit_offset"


class PaginationConfig(BaseModel):
    """Pagination settings for list operations.

    Example:
        >>> pagination = PaginationConfig(
        ...     style=PaginationStyle.CURSOR,
        ...     default_page_size=25,
        ...     max_page_size=100,
        ... )
    """

    style: PaginationStyle = Field(
        default=PaginationStyle.OFFSET,
        description="Pagination style",
    )
    default_page_size: int = Field(
        default=20,
        description="Default number of items per page",
    )
    max_page_size: int = Field(
        default=100,
        description="Maximum allowed items per page",
    )

    model_config = {"extra": "forbid"}


class RESTExposure(BaseModel):
    """FastAPI REST exposure configuration.

    Controls how the model is exposed via REST API endpoints.

    Example:
        >>> rest = RESTExposure(
        ...     enabled=True,
        ...     tags=["customers"],
        ...     prefix="/api/v1",
        ...     auth_required=True,
        ... )
    """

    enabled: bool = Field(default=True, description="Whether to expose via REST")
    operations: CRUDOperations = Field(
        default_factory=CRUDOperations,
        description="CRUD operations to expose",
    )
    prefix: str | None = Field(
        default=None,
        description="URL prefix for endpoints",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="OpenAPI tags for the endpoints",
    )
    pagination: PaginationConfig = Field(
        default_factory=PaginationConfig,
        description="Pagination configuration",
    )

    # Field visibility
    create_fields: list[str] | None = Field(
        default=None,
        description="Fields allowed in create requests (None = all)",
    )
    update_fields: list[str] | None = Field(
        default=None,
        description="Fields allowed in update requests (None = all)",
    )
    read_fields: list[str] | None = Field(
        default=None,
        description="Fields returned in read responses (None = all)",
    )
    list_fields: list[str] | None = Field(
        default=None,
        description="Fields returned in list responses (None = all)",
    )

    # Security
    auth_required: bool = Field(
        default=True,
        description="Whether authentication is required",
    )
    permissions: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Required permissions per operation",
    )

    # OpenAPI customization
    operation_ids: dict[str, str] = Field(
        default_factory=dict,
        description="Custom operation IDs for OpenAPI",
    )

    model_config = {"extra": "forbid"}


class GraphQLExposure(BaseModel):
    """Strawberry GraphQL exposure configuration.

    Controls how the model is exposed via GraphQL schema.

    Example:
        >>> graphql = GraphQLExposure(
        ...     enabled=True,
        ...     use_connection=True,
        ...     enable_subscriptions=True,
        ... )
    """

    enabled: bool = Field(default=True, description="Whether to expose via GraphQL")
    operations: CRUDOperations = Field(
        default_factory=CRUDOperations,
        description="CRUD operations to expose",
    )

    # Type naming
    type_name: str | None = Field(
        default=None,
        description="Override GraphQL type name",
    )
    input_type_name: str | None = Field(
        default=None,
        description="Override input type name",
    )
    query_name: str | None = Field(
        default=None,
        description="Override single-item query name",
    )
    query_list_name: str | None = Field(
        default=None,
        description="Override list query name",
    )

    # Connection (pagination)
    use_connection: bool = Field(
        default=True,
        description="Use Relay-style connections for lists",
    )
    connection_name: str | None = Field(
        default=None,
        description="Override connection type name",
    )

    # Mutations
    mutation_prefix: str | None = Field(
        default=None,
        description="Prefix for mutation names",
    )

    # Subscriptions
    enable_subscriptions: bool = Field(
        default=False,
        description="Enable real-time subscriptions",
    )
    subscription_events: list[str] = Field(
        default_factory=lambda: ["created", "updated", "deleted"],
        description="Events to subscribe to",
    )

    # Field visibility
    query_fields: list[str] | None = Field(
        default=None,
        description="Fields exposed in queries (None = all)",
    )
    mutation_fields: list[str] | None = Field(
        default=None,
        description="Fields allowed in mutations (None = all)",
    )

    # Performance
    use_dataloader: bool = Field(
        default=True,
        description="Use DataLoader for N+1 prevention",
    )
    max_depth: int | None = Field(
        default=None,
        description="Maximum query depth",
    )
    max_complexity: int | None = Field(
        default=None,
        description="Maximum query complexity",
    )

    # Security
    auth_required: bool = Field(
        default=True,
        description="Whether authentication is required",
    )
    permissions: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Required permissions per operation",
    )

    # Relationships
    nested_queries: bool = Field(
        default=True,
        description="Allow querying through relationships",
    )

    # Documentation
    type_description: str | None = Field(
        default=None,
        description="Description for the GraphQL type",
    )
    field_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Descriptions for individual fields",
    )

    model_config = {"extra": "forbid"}


class MCPExposure(BaseModel):
    """FastMCP exposure configuration.

    Controls how the model is exposed as MCP tools for AI assistants.

    Example:
        >>> mcp = MCPExposure(
        ...     enabled=True,
        ...     tool_prefix="customer",
        ...     tool_descriptions={
        ...         "list": "Search and list customers",
        ...         "read": "Get customer details by ID",
        ...     },
        ... )
    """

    enabled: bool = Field(default=True, description="Whether to expose via MCP")
    operations: CRUDOperations = Field(
        default_factory=CRUDOperations,
        description="CRUD operations to expose as tools",
    )

    # Tool naming
    tool_prefix: str | None = Field(
        default=None,
        description="Prefix for tool names",
    )
    tool_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Descriptions for each tool",
    )
    field_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Descriptions for tool parameters",
    )

    # Resource exposure
    expose_as_resource: bool = Field(
        default=False,
        description="Also expose as MCP resource",
    )
    resource_uri_template: str | None = Field(
        default=None,
        description="URI template for resource access",
    )

    model_config = {"extra": "forbid"}


class FrontendExposure(BaseModel):
    """React/TypeScript exposure configuration.

    Controls how the model is exposed in the frontend application.

    Example:
        >>> frontend = FrontendExposure(
        ...     enabled=True,
        ...     api_style="graphql",
        ...     generate_form=True,
        ...     generate_table=True,
        ...     nav_label="Customers",
        ...     nav_icon="users",
        ... )
    """

    enabled: bool = Field(default=True, description="Whether to generate frontend code")
    operations: CRUDOperations = Field(
        default_factory=CRUDOperations,
        description="CRUD operations to support in UI",
    )

    # API configuration
    api_style: str = Field(
        default="graphql",
        description="API style: 'graphql', 'rest', or 'both'",
    )
    graphql_client: str = Field(
        default="urql",
        description="GraphQL client: 'urql' or 'apollo'",
    )

    # Component generation
    generate_form: bool = Field(
        default=True,
        description="Generate form component",
    )
    generate_table: bool = Field(
        default=True,
        description="Generate table/list component",
    )
    generate_detail_view: bool = Field(
        default=True,
        description="Generate detail view component",
    )

    # Layout
    form_layout: str = Field(
        default="vertical",
        description="Form layout: 'vertical', 'horizontal', or 'grid'",
    )
    table_columns: list[str] | None = Field(
        default=None,
        description="Columns to show in table (None = auto)",
    )

    # Navigation
    include_in_nav: bool = Field(
        default=True,
        description="Include in navigation menu",
    )
    nav_label: str | None = Field(
        default=None,
        description="Navigation menu label",
    )
    nav_icon: str | None = Field(
        default=None,
        description="Navigation menu icon (Lucide icon name)",
    )

    # Widget customization
    widget_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Widget overrides for specific fields",
    )

    model_config = {"extra": "forbid"}

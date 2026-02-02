"""Model specification for Prism.

This module defines RelationshipSpec and ModelSpec for specifying
data models and their relationships.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from prisme.spec.fields import FieldSpec  # noqa: TC001
from prisme.spec.overrides import DeliveryOverrides, FrontendOverrides, MCPOverrides  # noqa: TC001


class TemporalConfig(BaseModel):
    """Configuration for time-series/temporal data patterns.

    Enables generation of specialized temporal queries like get_latest
    and get_history for models with time-series data.

    Example:
        >>> temporal = TemporalConfig(
        ...     timestamp_field="as_of_date",
        ...     group_by_field="entity_id",
        ...     generate_latest_query=True,
        ...     generate_history_query=True,
        ... )
    """

    timestamp_field: str = Field(
        ...,
        description="Field name containing the timestamp (e.g., 'as_of_date', 'recorded_at')",
    )
    group_by_field: str | None = Field(
        default=None,
        description="Field to group by when finding latest records (e.g., 'entity_id', 'period')",
    )
    generate_latest_query: bool = Field(
        default=True,
        description="Generate get_latest() query method",
    )
    generate_history_query: bool = Field(
        default=True,
        description="Generate get_history() query method",
    )

    model_config = {"extra": "forbid"}


class RelationshipSpec(BaseModel):
    """Specification for model relationships.

    Defines how models relate to each other (one-to-many, many-to-many, etc.).

    Example:
        >>> relationship = RelationshipSpec(
        ...     name="orders",
        ...     target_model="Order",
        ...     type="one_to_many",
        ...     back_populates="customer",
        ...     use_dataloader=True,
        ... )
    """

    name: str = Field(..., description="Relationship field name")
    target_model: str = Field(..., description="Target model name")
    type: str = Field(
        ...,
        description="Relationship type: 'one_to_many', 'many_to_one', 'many_to_many', 'one_to_one'",
    )
    back_populates: str | None = Field(
        default=None,
        description="Back-reference field name on related model",
    )
    lazy: str = Field(
        default="select",
        description="SQLAlchemy lazy loading strategy",
    )
    cascade: str = Field(
        default="all, delete-orphan",
        description="SQLAlchemy cascade behavior",
    )
    association_table: str | None = Field(
        default=None,
        description="Association table name for many-to-many",
    )
    optional: bool = Field(
        default=False,
        description="For many_to_one relationships, whether the FK is optional/nullable",
    )

    # GraphQL settings
    graphql_field_name: str | None = Field(
        default=None,
        description="Override GraphQL field name",
    )
    use_dataloader: bool = Field(
        default=True,
        description="Use DataLoader for this relationship",
    )

    model_config = {"extra": "forbid"}


class ModelSpec(BaseModel):
    """Complete specification for a data model.

    Defines all aspects of a model including fields, relationships,
    and how it's exposed via different interfaces.

    Example:
        >>> model = ModelSpec(
        ...     name="Customer",
        ...     description="Customer entity",
        ...     soft_delete=True,
        ...     timestamps=True,
        ...     fields=[
        ...         FieldSpec(name="name", type=FieldType.STRING, required=True),
        ...         FieldSpec(name="email", type=FieldType.STRING, unique=True),
        ...     ],
        ...     relationships=[
        ...         RelationshipSpec(
        ...             name="orders",
        ...             target_model="Order",
        ...             type="one_to_many",
        ...         ),
        ...     ],
        ... )
    """

    # Basic info
    name: str = Field(..., description="Model name (PascalCase)")
    table_name: str | None = Field(
        default=None,
        description="Database table name (defaults to snake_case of name)",
    )
    description: str | None = Field(
        default=None,
        description="Model description for documentation",
    )

    # Fields and relationships
    fields: list[FieldSpec] = Field(..., description="List of field specifications")
    relationships: list[RelationshipSpec] = Field(
        default_factory=list,
        description="List of relationship specifications",
    )

    # v2 exposure model: simplified expose + operations + overrides
    expose: bool = Field(
        default=True,
        description="Whether this model is exposed via any delivery channel",
    )
    operations: list[str] = Field(
        default_factory=lambda: ["create", "read", "update", "delete", "list"],
        description="CRUD operations to expose for this model",
    )
    delivery_overrides: DeliveryOverrides | None = Field(
        default=None,
        description="Per-model delivery channel overrides",
    )
    frontend_overrides: FrontendOverrides | None = Field(
        default=None,
        description="Per-model frontend generation overrides",
    )
    mcp_overrides: MCPOverrides | None = Field(
        default=None,
        description="Per-model MCP tool overrides",
    )

    # Field visibility (kept from v1)
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

    # Common behaviors
    soft_delete: bool = Field(
        default=False,
        description="Enable soft delete (deleted_at timestamp)",
    )
    timestamps: bool = Field(
        default=True,
        description="Add created_at and updated_at fields",
    )

    # Lifecycle hooks (function names)
    before_create: str | None = Field(
        default=None,
        description="Hook function called before create",
    )
    after_create: str | None = Field(
        default=None,
        description="Hook function called after create",
    )
    before_update: str | None = Field(
        default=None,
        description="Hook function called before update",
    )
    after_update: str | None = Field(
        default=None,
        description="Hook function called after update",
    )
    before_delete: str | None = Field(
        default=None,
        description="Hook function called before delete",
    )
    after_delete: str | None = Field(
        default=None,
        description="Hook function called after delete",
    )

    # Testing
    test_factory: str | None = Field(
        default=None,
        description="Factory class name for test data generation",
    )

    # Nested creation
    nested_create: list[str] | None = Field(
        default=None,
        description="Relationship names to include in nested create operations. "
        "When set, generates create_with_nested() method that can create parent "
        "with children in a single transaction.",
    )

    # Time-series/Temporal configuration
    temporal: TemporalConfig | None = Field(
        default=None,
        description="Configure time-series behavior for models with temporal data. "
        "Generates get_latest() and get_history() query methods.",
    )

    model_config = {"extra": "forbid"}

    def has_operation(self, op: str) -> bool:
        """Check if a CRUD operation is enabled for this model."""
        return op in self.operations

    def get_frontend_override(self, attr: str, default: Any = None) -> Any:
        """Get a frontend override value, or return default."""
        if self.frontend_overrides is not None:
            return getattr(self.frontend_overrides, attr, default)
        return default

    def get_mcp_override(self, attr: str, default: Any = None) -> Any:
        """Get an MCP override value, or return default."""
        if self.mcp_overrides is not None:
            return getattr(self.mcp_overrides, attr, default)
        return default

    def get_delivery_override(self, attr: str, default: Any = None) -> Any:
        """Get a delivery override value, or return default."""
        if self.delivery_overrides is not None:
            return getattr(self.delivery_overrides, attr, default)
        return default


# v2 aliases — use these names in new code
Model = ModelSpec
Relationship = RelationshipSpec

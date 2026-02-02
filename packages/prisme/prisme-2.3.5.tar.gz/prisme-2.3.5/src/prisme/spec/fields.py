"""Field specification models for Prism.

This module defines FieldType, FilterOperator, and FieldSpec for specifying
individual fields within a model.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class FieldType(str, Enum):
    """Supported field types for model definitions."""

    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    UUID = "uuid"
    JSON = "json"
    ENUM = "enum"
    FOREIGN_KEY = "foreign_key"


class FilterOperator(str, Enum):
    """Supported filter operators for list queries."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    BETWEEN = "between"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class FieldSpec(BaseModel):
    """Specification for a single model field.

    Defines the type, constraints, validation rules, and UI presentation
    for a field in a Prism model.

    Example:
        >>> field = FieldSpec(
        ...     name="email",
        ...     type=FieldType.STRING,
        ...     required=True,
        ...     unique=True,
        ...     max_length=255,
        ...     pattern=r"^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$",
        ...     ui_widget="email",
        ... )
    """

    # Core field definition
    name: str = Field(..., description="Field name (Python identifier)")
    type: FieldType = Field(..., description="Field data type")
    required: bool = Field(default=True, description="Whether the field is required")
    unique: bool = Field(default=False, description="Whether values must be unique")
    indexed: bool = Field(default=False, description="Whether to create a database index")
    default: Any = Field(default=None, description="Default value for the field")
    default_factory: str | None = Field(
        default=None,
        description="Name of factory function for default value (e.g., 'uuid.uuid4')",
    )

    # Enum field options
    choices: list[str] | None = Field(
        default=None,
        description="Allowed values for enum fields",
        validation_alias=AliasChoices("choices", "enum_values"),
    )

    @property
    def enum_values(self) -> list[str] | None:
        """Deprecated alias for choices. Use choices instead."""
        return self.choices

    # JSON field options
    json_item_type: str | None = Field(
        default=None,
        description="For JSON array fields: the type of items (e.g., 'str', 'int'). "
        "When set, generates typed arrays (list[str], string[]) instead of generic JSON.",
    )

    # Foreign key options
    references: str | None = Field(
        default=None,
        description="Referenced model name for foreign key fields",
    )
    on_delete: str = Field(
        default="CASCADE",
        description="ON DELETE behavior for foreign keys",
    )

    # Decimal field options
    precision: int | None = Field(
        default=None,
        description="Total number of digits for decimal fields",
    )
    scale: int | None = Field(
        default=None,
        description="Number of decimal places for decimal fields",
    )

    # Validation constraints
    min_length: int | None = Field(
        default=None,
        description="Minimum string length",
    )
    max_length: int | None = Field(
        default=None,
        description="Maximum string length",
    )
    min_value: float | None = Field(
        default=None,
        description="Minimum numeric value",
    )
    max_value: float | None = Field(
        default=None,
        description="Maximum numeric value",
    )
    pattern: str | None = Field(
        default=None,
        description="Regex pattern for string validation",
    )

    # List operation settings
    filterable: bool = Field(
        default=True,
        description="Whether the field can be used in filters",
    )
    filter_operators: list[FilterOperator] = Field(
        default_factory=lambda: [FilterOperator.EQ],
        description="Allowed filter operators for this field",
    )
    sortable: bool = Field(
        default=True,
        description="Whether the field can be used for sorting",
    )
    searchable: bool = Field(
        default=False,
        description="Whether the field is included in full-text search",
    )

    # Display settings
    label: str | None = Field(
        default=None,
        description="Human-readable label for the field (shown in forms and tables)",
    )
    display_name: str | None = Field(
        default=None,
        description="Alias for label (deprecated, use label instead)",
    )
    description: str | None = Field(
        default=None,
        description="Field description for API/GraphQL documentation",
    )
    tooltip: str | None = Field(
        default=None,
        description="Tooltip/help text shown in UI widgets",
    )
    hidden: bool = Field(
        default=False,
        description="Whether to hide the field in generated UIs",
    )

    @property
    def effective_label(self) -> str:
        """Get the effective label for the field."""
        return self.label or self.display_name or self.name.replace("_", " ").title()

    @property
    def effective_tooltip(self) -> str | None:
        """Get the effective tooltip for the field."""
        return self.tooltip or self.description

    # Frontend widget configuration
    ui_widget: str | None = Field(
        default=None,
        description="Widget type from the widget registry",
    )
    ui_placeholder: str | None = Field(
        default=None,
        description="Placeholder text for input widgets",
    )
    ui_widget_props: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional props passed to the widget",
    )

    # GraphQL specific settings
    graphql_type: str | None = Field(
        default=None,
        description="Override GraphQL type name",
    )
    graphql_deprecation: str | None = Field(
        default=None,
        description="Deprecation reason for GraphQL schema",
    )

    # Conditional validation
    conditional_required: str | None = Field(
        default=None,
        description="Condition when this field is required. "
        "Format: 'field_name == value' (e.g., 'sector == mining'). "
        "Generates Pydantic model_validator for conditional requirement.",
    )
    conditional_enum: dict[str, list[str]] | None = Field(
        default=None,
        description="Enum values conditional on another field. "
        "Format: {'field:value': ['allowed', 'values']}. "
        "Example: {'sector:mining': ['gold_miner', 'silver_miner']}.",
    )

    model_config = {"extra": "forbid", "populate_by_name": True}

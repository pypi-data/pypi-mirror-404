"""Override models for per-model customization in Prisme v2.

These models allow individual models to override project-level defaults
for specific delivery channels.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeliveryOverrides(BaseModel):
    """Per-model overrides for REST/GraphQL delivery settings."""

    page_size: int | None = Field(
        default=None,
        description="Override default page size for this model",
    )
    max_page_size: int | None = Field(
        default=None,
        description="Override maximum page size for this model",
    )
    rest_tags: list[str] | None = Field(
        default=None,
        description="Override REST API tags for this model",
    )
    subscriptions: bool | None = Field(
        default=None,
        description="Override subscription enablement for this model",
    )

    model_config = {"extra": "forbid"}


class FrontendOverrides(BaseModel):
    """Per-model overrides for frontend generation settings."""

    nav_icon: str | None = Field(
        default=None,
        description="Lucide icon name for navigation menu",
    )
    nav_label: str | None = Field(
        default=None,
        description="Navigation menu label",
    )
    table_columns: list[str] | None = Field(
        default=None,
        description="Columns to show in table (None = auto)",
    )
    form_layout: str | None = Field(
        default=None,
        description="Form layout override: 'vertical', 'horizontal', or 'grid'",
    )
    include_in_nav: bool | None = Field(
        default=None,
        description="Override whether to include in navigation menu",
    )
    generate_form: bool | None = Field(
        default=None,
        description="Override form generation",
    )
    generate_table: bool | None = Field(
        default=None,
        description="Override table generation",
    )
    generate_detail_view: bool | None = Field(
        default=None,
        description="Override detail view generation",
    )
    enable_bulk_actions: bool | None = Field(
        default=None,
        description="Enable bulk action UI on list page",
    )
    filterable_fields: list[str] | None = Field(
        default=None,
        description="Fields to show in the filter bar on list page",
    )
    enable_import: bool | None = Field(
        default=None,
        description="Enable CSV/JSON import page for this model",
    )

    model_config = {"extra": "forbid"}


class MCPOverrides(BaseModel):
    """Per-model overrides for MCP tool generation."""

    tool_prefix: str | None = Field(
        default=None,
        description="Override tool name prefix",
    )
    tool_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Override descriptions for each tool",
    )

    model_config = {"extra": "forbid"}


__all__ = [
    "DeliveryOverrides",
    "FrontendOverrides",
    "MCPOverrides",
]

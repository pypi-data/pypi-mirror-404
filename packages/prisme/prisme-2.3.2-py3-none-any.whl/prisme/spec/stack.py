"""Stack specification for Prism.

This module defines the domain-level stack specification: models and metadata.
Infrastructure configuration lives in ProjectSpec (project.py).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from prisme.spec.model import ModelSpec  # noqa: TC001

PRISME_DOMAIN_VERSION = 2


class FileStrategy(str, Enum):
    """How Prism handles each generated file."""

    ALWAYS_OVERWRITE = "always_overwrite"
    """Always regenerate. Use for pure boilerplate.
    Examples: types/generated.ts, graphql operations
    """

    GENERATE_ONCE = "generate_once"
    """Only create if doesn't exist. Never overwrite.
    Examples: custom hooks, page components
    """


class StackSpec(BaseModel):
    """Domain-level stack specification.

    Contains model definitions and project metadata.
    Infrastructure configuration is in ProjectSpec.

    Example:
        >>> stack = StackSpec(
        ...     name="my-crm",
        ...     version="1.0.0",
        ...     description="Customer Relationship Management System",
        ...     models=[
        ...         ModelSpec(
        ...             name="Customer",
        ...             fields=[...],
        ...         ),
        ...     ],
        ... )
    """

    # Basic info
    name: str = Field(..., description="Project name (kebab-case identifier)")
    title: str | None = Field(
        default=None,
        description="Human-readable project title (defaults to formatted name)",
    )
    version: str = Field(default="1.0.0", description="Project version")
    description: str | None = Field(default=None, description="Project description")

    @property
    def effective_title(self) -> str:
        """Get the effective project title."""
        if self.title:
            return self.title
        # Convert kebab-case name to title case
        return self.name.replace("-", " ").replace("_", " ").title()

    # Models
    models: list[ModelSpec] = Field(..., description="List of model specifications")

    model_config = {"extra": "forbid"}

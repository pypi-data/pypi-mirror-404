"""Prisme configuration schema (prisme.toml)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectPaths(BaseModel):
    """Paths configuration within the project."""

    spec_path: str = Field(
        default="specs/models.py",
        description="Path to the domain spec file",
    )
    project_path: str = Field(
        default="specs/project.py",
        description="Path to the project spec file",
    )

    model_config = {"extra": "forbid"}


class GenerationPolicy(BaseModel):
    """Controls generation behavior."""

    mode: Literal["strict", "lenient"] = Field(
        default="strict",
        description="strict: fail on warnings; lenient: continue with warnings",
    )
    auto_format: bool = Field(
        default=True,
        description="Auto-format generated code (ruff for Python, prettier for TS)",
    )

    model_config = {"extra": "forbid"}


class ToolChoices(BaseModel):
    """Tool preferences for the project."""

    python_manager: str = Field(
        default="uv",
        description="Python package manager: 'uv', 'pip', 'poetry'",
    )
    package_manager: str = Field(
        default="npm",
        description="Node package manager: 'npm', 'pnpm', 'yarn'",
    )

    model_config = {"extra": "forbid"}


class PrismeConfig(BaseModel):
    """Root configuration loaded from prisme.toml."""

    prisme_version: str = Field(
        ...,
        description="Prisme version that generated this config",
    )
    config_version: int = Field(
        default=1,
        description="Configuration schema version",
    )
    project: ProjectPaths = Field(
        default_factory=ProjectPaths,
        description="Project path configuration",
    )
    generation: GenerationPolicy = Field(
        default_factory=GenerationPolicy,
        description="Generation policy",
    )
    tools: ToolChoices = Field(
        default_factory=ToolChoices,
        description="Tool preferences",
    )

    model_config = {"extra": "forbid"}


__all__ = [
    "GenerationPolicy",
    "PrismeConfig",
    "ProjectPaths",
    "ToolChoices",
]

"""Dev container workspace management.

This module provides workspace management for dev containers
that builds on VS Code devcontainer spec.
"""

from prisme.devcontainer.config import (
    WorkspaceConfig,
    WorkspaceInfo,
    normalize_workspace_name,
)
from prisme.devcontainer.generator import DevContainerGenerator
from prisme.devcontainer.manager import WorkspaceManager

__all__ = [
    "DevContainerGenerator",
    "WorkspaceConfig",
    "WorkspaceInfo",
    "WorkspaceManager",
    "normalize_workspace_name",
]

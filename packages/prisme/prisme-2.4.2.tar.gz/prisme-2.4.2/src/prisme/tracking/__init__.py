"""File tracking and override detection for Prism.

This module provides file tracking, manifest management, and override logging
to enable safe regeneration of code.
"""

from prisme.tracking.differ import (
    DiffGenerator,
    DiffSummary,
)
from prisme.tracking.logger import (
    Override,
    OverrideLog,
    OverrideLogger,
)
from prisme.tracking.manifest import (
    FileManifest,
    ManifestManager,
    TrackedFile,
)

__all__ = [
    "DiffGenerator",
    "DiffSummary",
    "FileManifest",
    "ManifestManager",
    "Override",
    "OverrideLog",
    "OverrideLogger",
    "TrackedFile",
]

"""Migration utilities for upgrading prisme specs and config."""

from prisme.migration.detector import detect_versions
from prisme.migration.domain_v1_to_v2 import migrate_domain_v1_to_v2
from prisme.migration.project_extractor import extract_project_spec

__all__ = [
    "detect_versions",
    "extract_project_spec",
    "migrate_domain_v1_to_v2",
]

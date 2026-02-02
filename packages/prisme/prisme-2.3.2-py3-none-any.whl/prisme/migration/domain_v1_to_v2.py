"""Migrate domain spec from v1 to v2 format.

v1 StackSpec had delivery mechanics (auth, database, frontend config, etc.)
mixed into the domain spec. v2 strips StackSpec to domain-only (name, models)
and moves infrastructure config to ProjectSpec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MigrationResult:
    """Result of a domain spec migration."""

    new_domain_content: str
    extracted_project_fields: dict[str, Any] = field(default_factory=dict)
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Fields that were on v1 StackSpec but belong in ProjectSpec in v2
_V1_STACKSPEC_INFRA_FIELDS = {
    "database",
    "database_url",
    "database_async_driver",
    "auth_provider",
    "auth_enabled",
    "admin_panel",
    "frontend_framework",
    "frontend_enabled",
    "frontend_port",
    "backend_framework",
    "backend_port",
    "rest_enabled",
    "graphql_enabled",
    "mcp_enabled",
    "generate_tests",
    "test_database",
}

# v1 per-model exposure fields removed in v2
_V1_MODEL_EXPOSURE_FIELDS = {
    "rest_enabled",
    "graphql_enabled",
    "mcp_enabled",
    "frontend_enabled",
    "admin_enabled",
}


def migrate_domain_v1_to_v2(
    spec_path: Path | str,
    *,
    write: bool = False,
) -> MigrationResult:
    """Migrate a v1 domain spec file to v2 format.

    Removes infrastructure fields from StackSpec kwargs and collects them
    for ProjectSpec extraction. Also removes per-model exposure fields
    (replaced by model.expose dict in v2).

    Args:
        spec_path: Path to the v1 domain spec Python file.
        write: If True, write the migrated file. Otherwise dry-run only.

    Returns:
        MigrationResult with the new content and extracted fields.
    """
    spec_path = Path(spec_path)
    content = spec_path.read_text()
    result = MigrationResult(new_domain_content=content)

    # Remove infrastructure fields from StackSpec constructor
    for field_name in sorted(_V1_STACKSPEC_INFRA_FIELDS):
        pattern = rf"^([ \t]*){field_name}\s*=\s*.+,?\n"
        match = re.search(pattern, result.new_domain_content, re.MULTILINE)
        if match:
            # Extract the value for project spec
            value_match = re.search(
                rf"{field_name}\s*=\s*(.+?)(?:,\s*$|$)", match.group(), re.MULTILINE
            )
            if value_match:
                result.extracted_project_fields[field_name] = (
                    value_match.group(1).strip().rstrip(",")
                )
            result.new_domain_content = result.new_domain_content.replace(match.group(), "")
            result.changes.append(f"Removed StackSpec.{field_name} (moved to ProjectSpec)")

    # Remove per-model exposure fields
    for field_name in sorted(_V1_MODEL_EXPOSURE_FIELDS):
        pattern = rf"^([ \t]*){field_name}\s*=\s*.+,?\n"
        while True:
            match = re.search(pattern, result.new_domain_content, re.MULTILINE)
            if not match:
                break
            result.new_domain_content = result.new_domain_content.replace(match.group(), "")
            result.changes.append(f"Removed per-model {field_name} (use model.expose dict in v2)")

    # Remove old imports if present
    old_imports = [
        "from prism.spec",
        "from prism import",
    ]
    for old_import in old_imports:
        if old_import in result.new_domain_content:
            result.new_domain_content = result.new_domain_content.replace(
                old_import, old_import.replace("prism", "prisme")
            )
            result.changes.append(f"Updated import: {old_import} → prisme")

    # Clean up trailing commas and blank lines from removals
    result.new_domain_content = re.sub(r"\n{3,}", "\n\n", result.new_domain_content)

    if not result.changes:
        result.warnings.append("No v1 fields found — spec may already be v2 format")

    if write and result.changes:
        spec_path.write_text(result.new_domain_content)

    return result

"""Extract ProjectSpec from legacy config or v1 StackSpec fields."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_project_spec(
    extracted_fields: dict[str, Any],
    project_name: str = "my-project",
    *,
    write_path: Path | str | None = None,
) -> str:
    """Generate a ProjectSpec Python file from extracted v1 fields.

    Args:
        extracted_fields: Dict of field_name → value extracted from v1 StackSpec.
        project_name: Name for the project.
        write_path: If provided, write the file to this path.

    Returns:
        The generated project spec file content.
    """
    lines = [
        '"""Project specification — infrastructure and delivery config."""',
        "",
        "from prisme.spec.project import ProjectSpec",
        "",
        "",
        "project = ProjectSpec(",
        f'    name="{project_name}",',
    ]

    # Map v1 fields to ProjectSpec structure
    if "database" in extracted_fields:
        lines.append(f"    # database engine: {extracted_fields['database']}")

    if "auth_provider" in extracted_fields or "auth_enabled" in extracted_fields:
        lines.append("    # auth config extracted from v1 — review and adjust")

    if "frontend_framework" in extracted_fields:
        lines.append(f"    # frontend framework: {extracted_fields['frontend_framework']}")

    lines.append(")")
    lines.append("")

    content = "\n".join(lines)

    if write_path:
        write_path = Path(write_path)
        write_path.parent.mkdir(parents=True, exist_ok=True)
        write_path.write_text(content)

    return content

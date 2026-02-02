"""Detect field-level changes in generated SQLAlchemy model files.

Compares old (on-disk) model content with newly generated content to identify
added and removed fields per model class.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prisme.generators.base import GeneratorResult

# Matches lines like: field_name: Mapped[...]
_FIELD_RE = re.compile(r"^\s+(\w+): Mapped\[")

# Matches class declarations like: class User(Base): or class User(TimestampMixin, Base):
_CLASS_RE = re.compile(r"^class (\w+)\(")


@dataclass
class ModelFieldChange:
    """Describes field-level changes for a single model class."""

    model_name: str
    added: list[str]
    removed: list[str]


def _extract_fields(content: str) -> dict[str, set[str]]:
    """Extract field names per class from model file content.

    Returns a dict mapping class name to set of field names.
    """
    result: dict[str, set[str]] = {}
    current_class: str | None = None

    for line in content.splitlines():
        class_match = _CLASS_RE.match(line)
        if class_match:
            current_class = class_match.group(1)
            result.setdefault(current_class, set())
            continue

        if current_class:
            field_match = _FIELD_RE.match(line)
            if field_match:
                result[current_class].add(field_match.group(1))

    return result


def detect_field_changes(
    old_content: str, new_content: str, filename: str = ""
) -> list[ModelFieldChange]:
    """Compare old and new model file content, returning per-class field changes."""
    old_fields = _extract_fields(old_content)
    new_fields = _extract_fields(new_content)

    all_classes = set(old_fields) | set(new_fields)
    changes: list[ModelFieldChange] = []

    for cls in sorted(all_classes):
        old = old_fields.get(cls, set())
        new = new_fields.get(cls, set())
        added = sorted(new - old)
        removed = sorted(old - new)
        if added or removed:
            changes.append(ModelFieldChange(model_name=cls, added=added, removed=removed))

    return changes


def detect_model_changes(results: GeneratorResult) -> list[ModelFieldChange]:
    """Detect field-level changes across all model files in a GeneratorResult.

    For each generated model file, reads the existing file from disk and compares
    with the newly generated content.
    """
    all_changes: list[ModelFieldChange] = []

    for gen_file in results.files:
        path = gen_file.path if isinstance(gen_file.path, Path) else Path(gen_file.path)

        # Only look at model files (contain Mapped[ patterns)
        if "Mapped[" not in gen_file.content:
            continue

        new_content = gen_file.content

        if path.exists():
            try:
                old_content = path.read_text()
            except OSError:
                continue

            if old_content == new_content:
                continue

            changes = detect_field_changes(old_content, new_content, str(path))
        else:
            # New file — all fields are "added"
            changes = detect_field_changes("", new_content, str(path))

        all_changes.extend(changes)

    return all_changes

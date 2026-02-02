"""File handling utilities with protected region support.

Provides functions for reading and writing files while preserving
user-customized sections marked with PRISM:PROTECTED markers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from prisme.spec.stack import FileStrategy


@dataclass
class ProtectedRegion:
    """A protected region of code that should be preserved during regeneration."""

    name: str
    content: str
    start_line: int
    end_line: int


@dataclass
class ParsedFile:
    """A parsed file with protected regions extracted."""

    content: str
    protected_regions: dict[str, ProtectedRegion] = field(default_factory=dict)


def parse_protected_regions(
    content: str,
    marker: str = "PRISM:PROTECTED",
) -> ParsedFile:
    """Parse a file and extract protected regions.

    Protected regions are marked with comments like:
        # PRISM:PROTECTED:START - Region Name
        ... user code ...
        # PRISM:PROTECTED:END

    Args:
        content: The file content to parse.
        marker: The marker string to look for.

    Returns:
        ParsedFile with content and extracted protected regions.
    """
    start_pattern = re.compile(
        rf"(?:[#/]|{{\s*/\*)\s*{re.escape(marker)}:START\s*[-–—]?\s*(.*?)(?:\s*\*/\s*}})?$",
        re.MULTILINE,
    )
    end_pattern = re.compile(
        rf"(?:[#/]|{{\s*/\*)\s*{re.escape(marker)}:END",
        re.MULTILINE,
    )

    protected_regions: dict[str, ProtectedRegion] = {}
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]
        start_match = start_pattern.search(line)

        if start_match:
            region_name = (
                re.sub(r"[\s*/{}]+$", "", start_match.group(1).strip())
                or f"region_{len(protected_regions)}"
            )
            start_line = i
            region_content_lines: list[str] = []

            # Find the end of this region
            j = i + 1
            while j < len(lines):
                if end_pattern.search(lines[j]):
                    protected_regions[region_name] = ProtectedRegion(
                        name=region_name,
                        content="\n".join(region_content_lines),
                        start_line=start_line,
                        end_line=j,
                    )
                    i = j
                    break
                region_content_lines.append(lines[j])
                j += 1
            else:
                # No end marker found, treat rest of file as region
                protected_regions[region_name] = ProtectedRegion(
                    name=region_name,
                    content="\n".join(region_content_lines),
                    start_line=start_line,
                    end_line=len(lines) - 1,
                )
                break

        i += 1

    return ParsedFile(content=content, protected_regions=protected_regions)


def merge_protected_regions(
    new_content: str,
    old_regions: dict[str, ProtectedRegion],
    marker: str = "PRISM:PROTECTED",
) -> str:
    """Merge protected regions from old file into new generated content.

    Args:
        new_content: The newly generated content.
        old_regions: Protected regions extracted from the old file.
        marker: The marker string used for protected regions.

    Returns:
        The new content with old protected regions restored.
    """
    if not old_regions:
        return new_content

    start_pattern = re.compile(
        rf"((?:[#/]|{{\s*/\*)\s*{re.escape(marker)}:START\s*[-–—]?\s*)(.*?)(?:\s*\*/\s*}})?$",
        re.MULTILINE,
    )
    end_pattern = re.compile(
        rf"(?:[#/]|{{\s*/\*)\s*{re.escape(marker)}:END",
        re.MULTILINE,
    )

    lines = new_content.split("\n")
    result_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        start_match = start_pattern.search(line)

        if start_match:
            region_name = re.sub(r"[\s*/{}]+$", "", start_match.group(2).strip())
            result_lines.append(line)

            # Skip to end marker in new content
            j = i + 1
            while j < len(lines) and not end_pattern.search(lines[j]):
                j += 1

            # Insert old region content if it exists
            if region_name in old_regions and old_regions[region_name].content:
                result_lines.append(old_regions[region_name].content)

            # Add end marker
            if j < len(lines):
                result_lines.append(lines[j])
                i = j
        else:
            result_lines.append(line)

        i += 1

    return "\n".join(result_lines)


def should_write_file(
    path: Path,
    strategy: FileStrategy,
) -> bool:
    """Determine if a file should be written based on strategy.

    Args:
        path: The file path to check.
        strategy: The file generation strategy.

    Returns:
        True if the file should be written.
    """
    from prisme.spec.stack import FileStrategy as FS

    if strategy == FS.ALWAYS_OVERWRITE:
        return True

    if strategy == FS.GENERATE_ONCE:
        return not path.exists()

    return True


def write_file_with_strategy(
    path: Path,
    content: str,
    strategy: FileStrategy,
    marker: str = "PRISM:PROTECTED",
    dry_run: bool = False,
) -> bool:
    """Write a file according to the specified strategy.

    Args:
        path: The file path to write.
        content: The content to write.
        strategy: The file generation strategy.
        marker: The protected region marker.
        dry_run: If True, don't actually write the file.

    Returns:
        True if the file was written (or would be written in dry_run mode).
    """
    if not should_write_file(path, strategy):
        return False

    final_content = content
    if path.exists():
        existing = path.read_text()
        parsed = parse_protected_regions(existing, marker)
        if parsed.protected_regions:
            final_content = merge_protected_regions(content, parsed.protected_regions, marker)

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(final_content)

    return True


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_relative_import(from_path: Path, to_path: Path) -> str:
    """Calculate the relative import path between two Python files.

    Args:
        from_path: The file doing the import.
        to_path: The file being imported.

    Returns:
        The relative import string (e.g., "..models.customer").
    """
    from_parts = list(from_path.parent.parts)
    to_parts = list(to_path.parent.parts)

    # Find common prefix
    common_length = 0
    for i, (a, b) in enumerate(zip(from_parts, to_parts, strict=False)):
        if a != b:
            break
        common_length = i + 1

    # Calculate relative path
    ups = len(from_parts) - common_length
    downs = to_parts[common_length:]

    # Build import path
    module_name = to_path.stem
    if ups == 0:
        if downs:
            return "." + ".".join(downs) + "." + module_name
        return "." + module_name
    else:
        prefix = "." * (ups + 1)
        if downs:
            return prefix + ".".join(downs) + "." + module_name
        return prefix + module_name


__all__ = [
    "ParsedFile",
    "ProtectedRegion",
    "ensure_directory",
    "get_relative_import",
    "merge_protected_regions",
    "parse_protected_regions",
    "should_write_file",
    "write_file_with_strategy",
]

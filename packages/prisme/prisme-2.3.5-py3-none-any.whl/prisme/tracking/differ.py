"""Diff generation utilities for override logging.

Generates unified diffs and diff summaries to show what changed between
generated and user-modified code.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass
class DiffSummary:
    """Summary of changes between two versions.

    Attributes:
        lines_added: Number of lines added.
        lines_removed: Number of lines removed.
        lines_changed: Number of lines modified.
    """

    lines_added: int
    lines_removed: int
    lines_changed: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_changed": self.lines_changed,
        }


class DiffGenerator:
    """Utilities for generating diffs between file versions."""

    @staticmethod
    def generate_diff(
        old: str, new: str, old_label: str = "generated", new_label: str = "user"
    ) -> str:
        """Generate a unified diff between two versions.

        Args:
            old: The old/original content (generated).
            new: The new/modified content (user).
            old_label: Label for the old version.
            new_label: Label for the new version.

        Returns:
            Unified diff string.
        """
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            lineterm="",
        )

        return "".join(diff)

    @staticmethod
    def diff_summary(old: str, new: str) -> DiffSummary:
        """Generate a summary of changes between two versions.

        Args:
            old: The old/original content.
            new: The new/modified content.

        Returns:
            DiffSummary with counts of added, removed, and changed lines.
        """
        old_lines = old.splitlines()
        new_lines = new.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        lines_added = 0
        lines_removed = 0
        lines_changed = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                lines_added += j2 - j1
            elif tag == "delete":
                lines_removed += i2 - i1
            elif tag == "replace":
                # Count as changed lines (both removed and added)
                old_count = i2 - i1
                new_count = j2 - j1
                lines_changed += max(old_count, new_count)

        return DiffSummary(
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
        )

    @staticmethod
    def format_diff_colored(diff: str) -> str:
        """Add ANSI color codes to a diff for terminal display.

        Args:
            diff: The unified diff string.

        Returns:
            Diff with ANSI color codes.
        """
        # ANSI color codes
        RED = "\033[31m"
        GREEN = "\033[32m"
        CYAN = "\033[36m"
        RESET = "\033[0m"

        lines = diff.split("\n")
        colored_lines = []

        for line in lines:
            if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                colored_lines.append(f"{CYAN}{line}{RESET}")
            elif line.startswith("+"):
                colored_lines.append(f"{GREEN}{line}{RESET}")
            elif line.startswith("-"):
                colored_lines.append(f"{RED}{line}{RESET}")
            else:
                colored_lines.append(line)

        return "\n".join(colored_lines)

    @staticmethod
    def format_diff_markdown(diff: str) -> str:
        """Format a diff for Markdown rendering.

        Args:
            diff: The unified diff string.

        Returns:
            Markdown-formatted diff.
        """
        return f"```diff\n{diff}\n```"


__all__ = [
    "DiffGenerator",
    "DiffSummary",
]

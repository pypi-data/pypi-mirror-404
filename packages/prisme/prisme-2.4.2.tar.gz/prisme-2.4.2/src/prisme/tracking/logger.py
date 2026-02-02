"""Override logging system for tracking code conflicts.

Logs when user-modified code overrides generated code, creating both
JSON and Markdown logs for review.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from prisme.tracking.differ import DiffGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from prisme.spec.stack import FileStrategy


@dataclass
class Override:
    """Represents a single file override.

    Attributes:
        path: Relative path to the overridden file.
        strategy: The FileStrategy for this file.
        timestamp: ISO timestamp when override was logged.
        generated_hash: Hash of the generated content.
        user_hash: Hash of the user's content.
        reviewed: Whether user has reviewed this override.
        diff_summary: Summary of changes (lines added/removed/changed).
    """

    path: str
    strategy: str
    timestamp: str
    generated_hash: str
    user_hash: str
    reviewed: bool = False
    diff_summary: dict | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "strategy": self.strategy,
            "timestamp": self.timestamp,
            "generated_hash": self.generated_hash,
            "user_hash": self.user_hash,
            "reviewed": self.reviewed,
            "diff_summary": self.diff_summary,
        }

    @staticmethod
    def from_dict(data: dict) -> Override:
        """Create Override from dictionary."""
        return Override(
            path=data["path"],
            strategy=data["strategy"],
            timestamp=data["timestamp"],
            generated_hash=data["generated_hash"],
            user_hash=data["user_hash"],
            reviewed=data.get("reviewed", False),
            diff_summary=data.get("diff_summary"),
        )


class OverrideLog:
    """Collection of file overrides."""

    def __init__(self) -> None:
        """Initialize a new override log."""
        self.last_updated = datetime.now().isoformat()
        self.overrides: dict[str, Override] = {}

    def add_override(self, override: Override) -> None:
        """Add or update an override.

        Args:
            override: The Override to add.
        """
        self.overrides[override.path] = override
        self.last_updated = datetime.now().isoformat()

    def mark_reviewed(self, path: str) -> None:
        """Mark an override as reviewed.

        Args:
            path: The file path to mark as reviewed.
        """
        if path in self.overrides:
            self.overrides[path].reviewed = True
            self.last_updated = datetime.now().isoformat()

    def get_unreviewed(self) -> list[Override]:
        """Get all unreviewed overrides.

        Returns:
            List of unreviewed Override objects.
        """
        return [o for o in self.overrides.values() if not o.reviewed]

    def get_all(self) -> list[Override]:
        """Get all overrides.

        Returns:
            List of all Override objects.
        """
        return list(self.overrides.values())

    def get(self, path: str) -> Override | None:
        """Get override for a specific file.

        Args:
            path: The file path to look up.

        Returns:
            The Override if found, None otherwise.
        """
        return self.overrides.get(path)

    def remove(self, path: str) -> None:
        """Remove an override from the log.

        Args:
            path: The file path to remove.
        """
        if path in self.overrides:
            del self.overrides[path]
            self.last_updated = datetime.now().isoformat()

    def clear_reviewed(self) -> None:
        """Remove all reviewed overrides from the log."""
        self.overrides = {
            path: override for path, override in self.overrides.items() if not override.reviewed
        }
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert log to dictionary for JSON serialization."""
        return {
            "last_updated": self.last_updated,
            "overrides": [o.to_dict() for o in self.overrides.values()],
        }

    @staticmethod
    def from_dict(data: dict) -> OverrideLog:
        """Create OverrideLog from dictionary."""
        log = OverrideLog()
        log.last_updated = data.get("last_updated", datetime.now().isoformat())

        overrides_data = data.get("overrides", [])
        for override_data in overrides_data:
            override = Override.from_dict(override_data)
            log.overrides[override.path] = override

        return log


class OverrideLogger:
    """Manager for override logging."""

    OVERRIDE_DIR = ".prisme"
    OVERRIDE_JSON = "overrides.json"
    OVERRIDE_MD = "overrides.md"

    @staticmethod
    def log_override(
        path: Path,
        generated_content: str,
        user_content: str,
        strategy: FileStrategy,
        project_dir: Path,
    ) -> None:
        """Log an override when user code is preserved over generated code.

        Args:
            path: The file path that was overridden.
            generated_content: What Prism wanted to generate.
            user_content: What the user has in the file.
            strategy: The FileStrategy for this file.
            project_dir: The project root directory.
        """
        from prisme.tracking.manifest import hash_content

        # Load existing log
        log = OverrideLogger.load(project_dir)

        # Generate diff summary
        diff_summary = DiffGenerator.diff_summary(generated_content, user_content)

        # Create override entry
        override = Override(
            path=str(path.relative_to(project_dir) if path.is_absolute() else path),
            strategy=strategy.value,
            timestamp=datetime.now().isoformat(),
            generated_hash=hash_content(generated_content),
            user_hash=hash_content(user_content),
            reviewed=False,
            diff_summary=diff_summary.to_dict(),
        )

        # Add to log
        log.add_override(override)

        # Save JSON and regenerate Markdown
        OverrideLogger.save(log, project_dir)

        # Store the actual content for diff generation and restore functionality
        OverrideLogger._save_diff_cache(project_dir, override.path, generated_content, user_content)
        OverrideLogger._save_generated_content(project_dir, override.path, generated_content)

    @staticmethod
    def load(project_dir: Path) -> OverrideLog:
        """Load the override log from disk.

        Args:
            project_dir: The project root directory.

        Returns:
            The OverrideLog, or a new empty log if not found.
        """
        log_path = project_dir / OverrideLogger.OVERRIDE_DIR / OverrideLogger.OVERRIDE_JSON

        if not log_path.exists():
            return OverrideLog()

        try:
            with log_path.open("r") as f:
                data = json.load(f)
            return OverrideLog.from_dict(data)
        except (OSError, json.JSONDecodeError):
            return OverrideLog()

    @staticmethod
    def save(log: OverrideLog, project_dir: Path) -> None:
        """Save the override log to disk.

        Args:
            log: The OverrideLog to save.
            project_dir: The project root directory.
        """
        override_dir = project_dir / OverrideLogger.OVERRIDE_DIR
        override_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_path = override_dir / OverrideLogger.OVERRIDE_JSON
        with json_path.open("w") as f:
            json.dump(log.to_dict(), f, indent=2)

        # Generate and save Markdown
        md_path = override_dir / OverrideLogger.OVERRIDE_MD
        md_content = OverrideLogger.generate_markdown(log, project_dir)
        md_path.write_text(md_content)

    @staticmethod
    def generate_markdown(log: OverrideLog, project_dir: Path) -> str:
        """Generate Markdown representation of the override log.

        Args:
            log: The OverrideLog to format.
            project_dir: The project root directory.

        Returns:
            Formatted Markdown string.
        """
        lines = []
        lines.append("# Code Override Log\n")
        lines.append(f"**Last Updated**: {log.last_updated}\n")

        unreviewed = log.get_unreviewed()
        lines.append(f"**Unreviewed Overrides**: {len(unreviewed)}\n")
        lines.append("\n---\n")

        if not log.overrides:
            lines.append("\n*No overrides recorded.*\n")
            return "\n".join(lines)

        # Group by reviewed status
        for override in sorted(unreviewed, key=lambda o: o.timestamp, reverse=True):
            lines.append(OverrideLogger._format_override_markdown(override, project_dir))

        reviewed = [o for o in log.get_all() if o.reviewed]
        if reviewed:
            lines.append("\n## Reviewed Overrides\n")
            for override in sorted(reviewed, key=lambda o: o.timestamp, reverse=True):
                lines.append(OverrideLogger._format_override_markdown(override, project_dir))

        return "\n".join(lines)

    @staticmethod
    def _format_override_markdown(override: Override, project_dir: Path) -> str:
        """Format a single override as Markdown.

        Args:
            override: The Override to format.
            project_dir: The project root directory.

        Returns:
            Markdown-formatted override section.
        """
        lines = []

        # Header
        status_icon = "✓" if override.reviewed else "⚠️"
        lines.append(f"\n## {status_icon} {override.path}\n")

        # Metadata
        lines.append(f"**Strategy**: {override.strategy}")
        lines.append(f"**Status**: {'Reviewed' if override.reviewed else 'Not Reviewed'}")

        if override.diff_summary:
            added = override.diff_summary.get("lines_added", 0)
            removed = override.diff_summary.get("lines_removed", 0)
            changed = override.diff_summary.get("lines_changed", 0)
            lines.append(f"**Changes**: +{added} lines, -{removed} lines, ~{changed} lines")

        lines.append(f"**Last Modified**: {override.timestamp}\n")

        # Diff
        lines.append("### What Changed\n")
        lines.append("<details>")
        lines.append("<summary>Show Diff</summary>\n")

        # Try to load cached diff
        diff_content = OverrideLogger._load_diff_cache(project_dir, override.path)
        if diff_content:
            lines.append(DiffGenerator.format_diff_markdown(diff_content))
        else:
            lines.append("*Diff not available (run generation again to regenerate)*\n")

        lines.append("\n</details>\n")

        # Actions
        if not override.reviewed:
            lines.append("### Actions\n")
            lines.append("- Review your custom code to ensure it's still compatible")
            lines.append("- Run `prisme test` to verify functionality")
            lines.append(f"- Run `prisme review mark-reviewed {override.path}` when done\n")

        lines.append("---\n")

        return "\n".join(lines)

    @staticmethod
    def _save_diff_cache(project_dir: Path, file_path: str, generated: str, user: str) -> None:
        """Save diff content to cache for later display.

        Args:
            project_dir: The project root directory.
            file_path: The relative file path.
            generated: Generated content.
            user: User content.
        """
        cache_dir = project_dir / OverrideLogger.OVERRIDE_DIR / "diffs"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Generate diff
        diff = DiffGenerator.generate_diff(generated, user, "generated", "user")

        # Save to cache (use sanitized filename)
        cache_file = cache_dir / f"{file_path.replace('/', '_')}.diff"
        cache_file.write_text(diff)

    @staticmethod
    def _load_diff_cache(project_dir: Path, file_path: str) -> str | None:
        """Load cached diff content.

        Args:
            project_dir: The project root directory.
            file_path: The relative file path.

        Returns:
            Diff content if found, None otherwise.
        """
        cache_file = (
            project_dir
            / OverrideLogger.OVERRIDE_DIR
            / "diffs"
            / f"{file_path.replace('/', '_')}.diff"
        )

        if cache_file.exists():
            return cache_file.read_text()
        return None

    @staticmethod
    def _save_generated_content(project_dir: Path, file_path: str, generated: str) -> None:
        """Save generated content for potential restoration.

        Args:
            project_dir: The project root directory.
            file_path: The relative file path.
            generated: Generated content to save.
        """
        cache_dir = project_dir / OverrideLogger.OVERRIDE_DIR / "generated"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Save to cache (use sanitized filename)
        cache_file = cache_dir / file_path.replace("/", "_")
        cache_file.write_text(generated)

    @staticmethod
    def load_generated_content(project_dir: Path, file_path: str) -> str | None:
        """Load cached generated content for restoration.

        Args:
            project_dir: The project root directory.
            file_path: The relative file path.

        Returns:
            Generated content if found, None otherwise.
        """
        cache_file = (
            project_dir / OverrideLogger.OVERRIDE_DIR / "generated" / file_path.replace("/", "_")
        )

        if cache_file.exists():
            return cache_file.read_text()
        return None


__all__ = [
    "Override",
    "OverrideLog",
    "OverrideLogger",
]

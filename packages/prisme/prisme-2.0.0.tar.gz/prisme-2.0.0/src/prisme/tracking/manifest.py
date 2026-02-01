"""File manifest system for tracking generated files.

Tracks metadata about generated files including content hashes, generation
timestamps, and file strategies to detect user modifications.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class TrackedFile:
    """Represents a tracked generated file.

    Attributes:
        path: Relative path to the file from project root.
        strategy: The FileStrategy used for this file.
        content_hash: SHA-256 hash of the file content when generated.
        generated_at: ISO timestamp when the file was generated.
        has_hooks: Whether the file includes hook methods for customization.
        extends: Path to base file if this is an extension file.
    """

    path: str
    strategy: str  # Store as string for JSON serialization
    content_hash: str
    generated_at: str  # ISO format timestamp
    has_hooks: bool = False
    extends: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "strategy": self.strategy,
            "content_hash": self.content_hash,
            "generated_at": self.generated_at,
            "has_hooks": self.has_hooks,
            "extends": self.extends,
        }

    @staticmethod
    def from_dict(path: str, data: dict) -> TrackedFile:
        """Create TrackedFile from dictionary."""
        return TrackedFile(
            path=path,
            strategy=data["strategy"],
            content_hash=data["content_hash"],
            generated_at=data["generated_at"],
            has_hooks=data.get("has_hooks", False),
            extends=data.get("extends"),
        )


class FileManifest:
    """Manifest of all tracked generated files.

    Manages the manifest file that tracks metadata about generated files
    to detect user modifications.
    """

    def __init__(
        self,
        version: str = "1.0",
        prisme_version: str = "0.4.0",
        spec_hash: str = "",
        domain_version: int | None = None,
        project_version: int | None = None,
        config_version: int | None = None,
        domain_hash: str = "",
        project_hash: str = "",
        config_hash: str = "",
        generators_enabled: list[str] | None = None,
    ) -> None:
        """Initialize a new manifest.

        Args:
            version: Manifest format version.
            prisme_version: Prism version that generated the files.
            spec_hash: Hash of the spec file for change detection (v1 compat).
            domain_version: PRISME_DOMAIN_VERSION from domain spec.
            project_version: PRISME_PROJECT_VERSION from project spec.
            config_version: config_version from prisme.toml.
            domain_hash: Hash of the domain spec file.
            project_hash: Hash of the project spec file.
            config_hash: Hash of the prisme.toml file.
            generators_enabled: List of generator names that ran.
        """
        self.version = version
        self.prisme_version = prisme_version
        self.spec_hash = spec_hash
        self.domain_version = domain_version
        self.project_version = project_version
        self.config_version = config_version
        self.domain_hash = domain_hash
        self.project_hash = project_hash
        self.config_hash = config_hash
        self.generators_enabled = generators_enabled or []
        self.generated_at = datetime.now().isoformat()
        self.files: dict[str, TrackedFile] = {}

    def track_file(self, file: TrackedFile) -> None:
        """Add or update a tracked file.

        Args:
            file: The TrackedFile to track.
        """
        self.files[file.path] = file

    def get_file(self, path: str | Path) -> TrackedFile | None:
        """Get tracked file metadata by path.

        Args:
            path: The file path to look up.

        Returns:
            The TrackedFile if found, None otherwise.
        """
        path_str = str(path)
        return self.files.get(path_str)

    def is_modified(self, path: str | Path, current_content: str) -> bool:
        """Check if a file has been modified by the user.

        Compares the current content hash with the tracked hash.

        Args:
            path: The file path to check.
            current_content: The current content of the file.

        Returns:
            True if the file has been modified, False otherwise.
        """
        tracked = self.get_file(path)
        if not tracked:
            # File not in manifest, assume not modified
            return False

        current_hash = hash_content(current_content)
        return current_hash != tracked.content_hash

    def list_modified_files(self, project_dir: Path) -> list[str]:
        """List all files that have been modified by the user.

        Args:
            project_dir: The project root directory.

        Returns:
            List of relative paths to modified files.
        """
        modified = []
        for path_str, _tracked_file in self.files.items():
            file_path = project_dir / path_str
            if file_path.exists():
                current_content = file_path.read_text()
                if self.is_modified(path_str, current_content):
                    modified.append(path_str)
        return modified

    def remove_file(self, path: str | Path) -> None:
        """Remove a file from tracking.

        Args:
            path: The file path to remove.
        """
        path_str = str(path)
        if path_str in self.files:
            del self.files[path_str]

    def to_dict(self) -> dict:
        """Convert manifest to dictionary for JSON serialization."""
        data: dict = {
            "version": self.version,
            "generated_at": self.generated_at,
            "prisme_version": self.prisme_version,
            "spec_hash": self.spec_hash,
        }
        if self.domain_version is not None:
            data["domain_version"] = self.domain_version
        if self.project_version is not None:
            data["project_version"] = self.project_version
        if self.config_version is not None:
            data["config_version"] = self.config_version
        if self.domain_hash:
            data["domain_hash"] = self.domain_hash
        if self.project_hash:
            data["project_hash"] = self.project_hash
        if self.config_hash:
            data["config_hash"] = self.config_hash
        if self.generators_enabled:
            data["generators_enabled"] = self.generators_enabled
        data["files"] = {path: file.to_dict() for path, file in self.files.items()}
        return data

    @staticmethod
    def from_dict(data: dict) -> FileManifest:
        """Create FileManifest from dictionary."""
        manifest = FileManifest(
            version=data.get("version", "1.0"),
            prisme_version=data.get("prisme_version", "0.4.0"),
            spec_hash=data.get("spec_hash", ""),
            domain_version=data.get("domain_version"),
            project_version=data.get("project_version"),
            config_version=data.get("config_version"),
            domain_hash=data.get("domain_hash", ""),
            project_hash=data.get("project_hash", ""),
            config_hash=data.get("config_hash", ""),
            generators_enabled=data.get("generators_enabled", []),
        )
        manifest.generated_at = data.get("generated_at", datetime.now().isoformat())

        files_data = data.get("files", {})
        for path, file_data in files_data.items():
            manifest.files[path] = TrackedFile.from_dict(path, file_data)

        return manifest


class ManifestManager:
    """Manager for loading and saving file manifests."""

    MANIFEST_DIR = ".prisme"
    MANIFEST_FILE = "manifest.json"

    @staticmethod
    def get_manifest_path(project_dir: Path) -> Path:
        """Get the path to the manifest file.

        Args:
            project_dir: The project root directory.

        Returns:
            Path to the manifest.json file.
        """
        return project_dir / ManifestManager.MANIFEST_DIR / ManifestManager.MANIFEST_FILE

    @staticmethod
    def load(project_dir: Path) -> FileManifest:
        """Load the file manifest from disk.

        Args:
            project_dir: The project root directory.

        Returns:
            The FileManifest, or a new empty manifest if not found.
        """
        manifest_path = ManifestManager.get_manifest_path(project_dir)

        if not manifest_path.exists():
            return FileManifest()

        try:
            with manifest_path.open("r") as f:
                data = json.load(f)
            return FileManifest.from_dict(data)
        except (OSError, json.JSONDecodeError):
            # If manifest is corrupted, return new empty manifest
            # TODO: Log warning
            return FileManifest()

    @staticmethod
    def save(manifest: FileManifest, project_dir: Path) -> None:
        """Save the file manifest to disk.

        Args:
            manifest: The FileManifest to save.
            project_dir: The project root directory.
        """
        manifest_path = ManifestManager.get_manifest_path(project_dir)

        # Ensure .prism directory exists
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Update generated_at timestamp
        manifest.generated_at = datetime.now().isoformat()

        # Write manifest
        with manifest_path.open("w") as f:
            json.dump(manifest.to_dict(), f, indent=2)


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of file content.

    Args:
        content: The file content to hash.

    Returns:
        Hex string of the SHA-256 hash.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = [
    "FileManifest",
    "ManifestManager",
    "TrackedFile",
    "hash_content",
]

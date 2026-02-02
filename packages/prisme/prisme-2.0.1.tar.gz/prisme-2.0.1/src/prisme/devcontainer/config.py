"""Workspace configuration for dev containers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


def normalize_workspace_name(name: str) -> str:
    """Normalize name for use in container/volume/hostname.

    - Lowercase
    - Replace / with -
    - Remove special characters
    - Max 63 chars (DNS limit)
    """
    normalized = name.lower()
    normalized = normalized.replace("/", "-")
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"[^a-z0-9\-]", "", normalized)
    normalized = re.sub(r"-+", "-", normalized)  # Collapse multiple dashes
    normalized = normalized.strip("-")
    return normalized[:63]


def get_current_branch() -> str | None:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def get_project_name_from_dir(project_dir: Path) -> str:
    """Get project name from directory name."""
    return project_dir.name


def _resolve_prisme_src() -> Path | None:
    """Resolve the prisme source directory from the running installation.

    For editable installs (pip install -e), returns the project root.
    For regular installs, returns None (container uses PyPI version).
    """
    try:
        from importlib.metadata import distribution

        dist = distribution("prisme")
        # Check if this is an editable install by looking for direct_url.json
        direct_url = dist.read_text("direct_url.json")
        if direct_url:
            import json

            info = json.loads(direct_url)
            url = info.get("url", "")
            if url.startswith("file://"):
                return Path(url.removeprefix("file://"))
    except Exception:
        pass

    # Fallback: resolve from prisme package __file__
    try:
        import prisme as _prisme

        pkg_path = Path(_prisme.__file__).resolve()
        # src/prisme/__init__.py -> src/prisme -> src -> project root
        candidate = pkg_path.parent.parent.parent
        if (candidate / "pyproject.toml").exists():
            return candidate
    except Exception:
        pass

    return None


@dataclass
class WorkspaceConfig:
    """Configuration for a development workspace."""

    project_name: str
    project_dir: Path
    workspace_name: str | None = None
    branch: str | None = None
    include_redis: bool = False
    python_version: str = "3.13"
    node_version: str = "22"
    frontend_path: str | None = "packages/frontend"
    spec_path: str | None = "specs/models.py"

    def __post_init__(self) -> None:
        """Initialize computed fields after dataclass init."""
        # Auto-detect branch if not provided
        if self.branch is None:
            self.branch = get_current_branch()

        # Generate workspace name if not provided
        if self.workspace_name is None:
            if self.branch:
                self.workspace_name = f"{self.project_name}-{self.branch}"
            else:
                self.workspace_name = self.project_name

        # Normalize the workspace name
        self.workspace_name = normalize_workspace_name(self.workspace_name)

    @property
    def prisme_src(self) -> Path | None:
        """Resolved path to prisme source directory, if editable install."""
        return _resolve_prisme_src()

    @property
    def database_name(self) -> str:
        """Database name (underscores for postgres compatibility)."""
        assert self.workspace_name is not None  # Set in __post_init__
        return self.workspace_name.replace("-", "_")

    @property
    def hostname(self) -> str:
        """Hostname for Traefik routing."""
        assert self.workspace_name is not None  # Set in __post_init__
        return self.workspace_name

    @property
    def devcontainer_dir(self) -> Path:
        """Path to .devcontainer directory."""
        return self.project_dir / ".devcontainer"

    @property
    def env_file(self) -> Path:
        """Path to .env file."""
        return self.devcontainer_dir / ".env"

    @property
    def compose_file(self) -> Path:
        """Path to docker-compose.yml file."""
        return self.devcontainer_dir / "docker-compose.yml"

    @classmethod
    def from_directory(
        cls,
        project_dir: Path | None = None,
        workspace_name: str | None = None,
        include_redis: bool = False,
    ) -> WorkspaceConfig:
        """Create config from project directory.

        Args:
            project_dir: Project directory (defaults to cwd)
            workspace_name: Custom workspace name (defaults to project-branch)
            include_redis: Include Redis service

        Returns:
            WorkspaceConfig instance
        """
        project_dir = project_dir or Path.cwd()
        project_name = get_project_name_from_dir(project_dir)

        # Check for frontend directory
        frontend_path: str | None = None
        for candidate in ["packages/frontend", "frontend", "web", "client"]:
            if (project_dir / candidate / "package.json").exists():
                frontend_path = candidate
                break

        # Check for spec file
        spec_path: str | None = None
        for candidate in ["specs/models.py", "spec.py", "specs/stack.py"]:
            if (project_dir / candidate).exists():
                spec_path = candidate
                break

        return cls(
            project_name=project_name,
            project_dir=project_dir,
            workspace_name=workspace_name,
            include_redis=include_redis,
            frontend_path=frontend_path,
            spec_path=spec_path,
        )


@dataclass
class WorkspaceInfo:
    """Information about a running workspace."""

    workspace_name: str
    status: str  # running, exited, etc.
    services: list[str] = field(default_factory=list)
    url: str = ""
    project_dir: str = ""

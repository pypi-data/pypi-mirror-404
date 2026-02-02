"""Detect current spec/config versions and state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class VersionInfo:
    """Detected version information for a prisme project."""

    has_prisme_toml: bool = False
    config_version: int | None = None
    has_domain_spec: bool = False
    domain_version: int | None = None
    has_project_spec: bool = False
    has_legacy_config: bool = False
    python_manager: str | None = None

    @property
    def needs_config_migration(self) -> bool:
        """Whether the config needs migration."""
        return self.has_legacy_config and not self.has_prisme_toml

    @property
    def needs_domain_migration(self) -> bool:
        """Whether the domain spec needs v1→v2 migration."""
        return self.domain_version is not None and self.domain_version < 2

    @property
    def needs_project_extraction(self) -> bool:
        """Whether a project spec needs to be extracted."""
        return self.has_domain_spec and not self.has_project_spec


def _detect_python_manager(project_dir: Path) -> str | None:
    """Infer python manager from lockfiles."""
    if (project_dir / "uv.lock").exists():
        return "uv"
    if (project_dir / "poetry.lock").exists():
        return "poetry"
    if (project_dir / "Pipfile.lock").exists():
        return "pipenv"
    if (project_dir / "requirements.txt").exists():
        return "pip"
    return None


def detect_versions(project_dir: Path | str) -> VersionInfo:
    """Detect current spec/config versions in a project directory.

    Args:
        project_dir: Path to the project root.

    Returns:
        VersionInfo with detected state.
    """
    project_dir = Path(project_dir)
    info = VersionInfo()

    # Check prisme.toml
    toml_path = project_dir / "prisme.toml"
    if toml_path.exists():
        info.has_prisme_toml = True
        try:
            from prisme.config.loader import load_prisme_config

            config = load_prisme_config(toml_path)
            info.config_version = config.config_version
        except Exception:
            pass

    # Check legacy config
    legacy_path = project_dir / "prism.config.py"
    info.has_legacy_config = legacy_path.exists()

    # Check domain spec
    for spec_candidate in [
        project_dir / "specs" / "models.py",
        project_dir / "spec.py",
    ]:
        if spec_candidate.exists():
            info.has_domain_spec = True
            # Try to detect version from file content
            try:
                content = spec_candidate.read_text()
                if "PRISME_DOMAIN_VERSION" in content:
                    info.domain_version = 2
                else:
                    info.domain_version = 1
            except Exception:
                pass
            break

    # Check project spec
    for project_candidate in [
        project_dir / "specs" / "project.py",
    ]:
        if project_candidate.exists():
            info.has_project_spec = True
            break

    # Detect python manager
    info.python_manager = _detect_python_manager(project_dir)

    return info

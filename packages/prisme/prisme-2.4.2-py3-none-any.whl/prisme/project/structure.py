"""Standard project directory structure constants for Prisme v2.

All generated code goes in GENERATED_DIR.
User customizations go in APP_DIR.
Spec files go in SPECS_DIR.
"""

from pathlib import Path

# Top-level directories
GENERATED_DIR = Path("generated")
APP_DIR = Path("app")
PACKAGES_DIR = Path("packages")
SPECS_DIR = Path("specs")

# Generated subdirectories
GENERATED_BACKEND_DIR = GENERATED_DIR / "backend"
GENERATED_FRONTEND_DIR = GENERATED_DIR / "frontend"

# App extension directories
APP_BACKEND_DIR = APP_DIR / "backend"
APP_FRONTEND_DIR = APP_DIR / "frontend"
APP_BACKEND_EXTENSIONS_DIR = APP_BACKEND_DIR / "extensions"

# Package entry points
PACKAGES_BACKEND_DIR = PACKAGES_DIR / "backend"
PACKAGES_FRONTEND_DIR = PACKAGES_DIR / "frontend"

# Configuration files
CONFIG_FILE = Path("prisme.toml")
MANIFEST_PATH = GENERATED_DIR / ".prisme-manifest.json"

# Spec files
DOMAIN_SPEC_FILE = SPECS_DIR / "models.py"
PROJECT_SPEC_FILE = SPECS_DIR / "project.py"

# Infrastructure
DOCKER_DIR = Path("docker")
GITHUB_DIR = Path(".github")
DEVCONTAINER_DIR = Path(".devcontainer")


__all__ = [
    "APP_BACKEND_DIR",
    "APP_BACKEND_EXTENSIONS_DIR",
    "APP_DIR",
    "APP_FRONTEND_DIR",
    "CONFIG_FILE",
    "DEVCONTAINER_DIR",
    "DOCKER_DIR",
    "DOMAIN_SPEC_FILE",
    "GENERATED_BACKEND_DIR",
    "GENERATED_DIR",
    "GENERATED_FRONTEND_DIR",
    "GITHUB_DIR",
    "MANIFEST_PATH",
    "PACKAGES_BACKEND_DIR",
    "PACKAGES_DIR",
    "PACKAGES_FRONTEND_DIR",
    "PROJECT_SPEC_FILE",
    "SPECS_DIR",
]

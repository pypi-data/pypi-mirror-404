"""E2E test configuration and shared fixtures."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEMO_SPEC_PATH = PROJECT_ROOT / "specs" / "demo.py"


def get_prism_command() -> list[str]:
    """Get the command to invoke prism CLI.

    Works in both local development and CI environments.
    Uses python -m to ensure the installed package is used.
    """
    return [sys.executable, "-m", "prisme.cli"]


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result.

    Args:
        cmd: Command and arguments to run
        cwd: Working directory for the command
        timeout: Timeout in seconds
        check: Whether to raise on non-zero exit code

    Returns:
        CompletedProcess with stdout/stderr captured

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def setup_project_with_spec(project_dir: Path) -> Path:
    """Setup a project directory with the demo spec inside it.

    Args:
        project_dir: Directory to create project in

    Returns:
        Path to the spec file inside the project
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    spec_dir = project_dir / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_dest = spec_dir / "models.py"
    shutil.copy(DEMO_SPEC_PATH, spec_dest)
    return spec_dest


@pytest.fixture(scope="module")
def e2e_temp_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary directory for e2e tests."""
    return tmp_path_factory.mktemp("prism_e2e")


@pytest.fixture
def prism_cmd() -> list[str]:
    """Get the prism command for subprocess calls."""
    return get_prism_command()

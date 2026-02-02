"""Pytest configuration for devcontainer tests."""

import pytest
from jinja2 import Environment, PackageLoader


@pytest.fixture
def template_env() -> Environment:
    """Create a Jinja2 environment for testing templates."""
    return Environment(
        loader=PackageLoader("prisme", "templates/jinja2"),
        trim_blocks=True,
        lstrip_blocks=True,
    )


@pytest.fixture
def docker_available() -> bool:
    """Check if Docker is available for integration tests."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

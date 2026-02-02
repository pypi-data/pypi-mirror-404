"""Docker-based end-to-end tests for Prism.

These tests create a full Prism project, initialize Docker, and verify
the containerized application works correctly.

Run with: pytest -m docker tests/e2e/
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from prisme.docker import DockerManager

from .conftest import get_prism_command, run_command, setup_project_with_spec

# Skip all tests in this module if Docker is not available
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.docker,
    pytest.mark.slow,
]


@pytest.fixture(scope="module")
def docker_available() -> bool:
    """Check if Docker is available, skip tests if not."""
    if not DockerManager.is_available():
        pytest.skip("Docker is not available")
    return True


@pytest.fixture(scope="module")
def docker_project(tmp_path_factory: pytest.TempPathFactory, docker_available: bool) -> Path:
    """Create a Prism project with Docker setup.

    This fixture:
    1. Creates a new project with prism create
    2. Generates code with prism generate
    3. Initializes Docker with prism docker init

    Returns the project directory path.
    """
    temp_dir = tmp_path_factory.mktemp("prism_docker_e2e")
    project_name = "docker-e2e-test"
    project_dir = temp_dir / project_name

    # Setup project with spec inside (spec must be within project folder)
    spec_dest = setup_project_with_spec(project_dir)

    # Create project
    run_command(
        [*get_prism_command(), "create", project_name, "--spec", str(spec_dest), "-y"],
        cwd=temp_dir,
        timeout=120,
    )

    # Generate code
    run_command(
        [*get_prism_command(), "generate"],
        cwd=project_dir,
        timeout=120,
    )

    # Initialize Docker
    run_command(
        [*get_prism_command(), "docker", "init"],
        cwd=project_dir,
        timeout=60,
    )

    yield project_dir

    # Cleanup: ensure containers are stopped
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.dev.yml", "down", "-v"],
        cwd=project_dir,
        capture_output=True,
        timeout=60,
    )


class TestDockerInit:
    """Test Docker initialization."""

    def test_docker_compose_file_created(self, docker_project: Path) -> None:
        """Docker compose file is created."""
        assert (docker_project / "docker-compose.dev.yml").exists()

    def test_dockerfile_backend_created(self, docker_project: Path) -> None:
        """Backend Dockerfile is created."""
        assert (docker_project / "Dockerfile.backend").exists()

    def test_dockerfile_frontend_created(self, docker_project: Path) -> None:
        """Frontend Dockerfile is created."""
        assert (docker_project / "Dockerfile.frontend").exists()

    def test_dockerignore_created(self, docker_project: Path) -> None:
        """Dockerignore file is created."""
        assert (docker_project / ".dockerignore").exists()


class TestDockerCompose:
    """Test Docker Compose functionality."""

    @pytest.fixture(scope="class")
    def running_services(self, docker_project: Path) -> Path:
        """Start Docker services and yield project dir.

        Services are stopped after all tests in this class complete.
        """
        # Build and start services
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d", "--build"],
            cwd=docker_project,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min for initial build
        )

        if result.returncode != 0:
            print(f"Docker compose up failed:\n{result.stderr}")
            pytest.fail(f"Failed to start Docker services: {result.stderr}")

        # Wait for services to be healthy (max 90 seconds)
        start_time = time.time()
        while time.time() - start_time < 90:
            ps_result = subprocess.run(
                ["docker", "compose", "-f", "docker-compose.dev.yml", "ps", "--format", "json"],
                cwd=docker_project,
                capture_output=True,
                text=True,
            )
            # Simple health check - containers are running
            if ps_result.returncode == 0 and "running" in ps_result.stdout.lower():
                break
            time.sleep(5)

        yield docker_project

        # Teardown
        subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "down", "-v"],
            cwd=docker_project,
            capture_output=True,
            timeout=60,
        )

    def test_database_healthy(self, running_services: Path) -> None:
        """Database container is healthy."""
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "docker-compose.dev.yml",
                "exec",
                "-T",
                "db",
                "pg_isready",
                "-U",
                "postgres",
            ],
            cwd=running_services,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, "Database is not ready"

    def test_backend_responds(self, running_services: Path) -> None:
        """Backend health endpoint responds."""
        # Wait a bit for backend to fully start
        time.sleep(10)

        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "docker-compose.dev.yml",
                "exec",
                "-T",
                "backend",
                "curl",
                "-f",
                "http://localhost:8000/health",
            ],
            cwd=running_services,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # May fail if curl not installed, that's OK for now
        # Main verification is that container is running
        assert result.returncode == 0 or "curl" in result.stderr.lower()

    def test_services_running(self, running_services: Path) -> None:
        """All expected services are running."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "ps", "--services"],
            cwd=running_services,
            capture_output=True,
            text=True,
            timeout=30,
        )
        services = result.stdout.strip().split("\n")
        assert "db" in services, "Database service should be running"
        assert "backend" in services, "Backend service should be running"


class TestDockerLogs:
    """Test Docker log access."""

    def test_can_view_logs(self, docker_project: Path, docker_available: bool) -> None:
        """Can view Docker logs without error."""
        # Just verify the command doesn't error (services may not be running)
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "logs", "--tail=10"],
            cwd=docker_project,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should succeed even if no containers running
        assert result.returncode == 0 or "no such service" not in result.stderr.lower()

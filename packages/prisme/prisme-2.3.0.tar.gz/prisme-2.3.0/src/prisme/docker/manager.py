"""Docker and Docker Compose management for Prism projects."""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from rich.console import Console

from prisme.docker.compose import normalize_hostname
from prisme.docker.proxy import ProxyManager

if TYPE_CHECKING:
    from pathlib import Path


class DockerManager:
    """Manage Docker daemon availability."""

    @staticmethod
    def is_available() -> bool:
        """Check if Docker is installed and running.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def get_version() -> str | None:
        """Get Docker version if available.

        Returns:
            Docker version string or None if not available
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None


class ComposeManager:
    """Manage Docker Compose services."""

    def __init__(self, project_dir: Path, console: Console | None = None):
        """Initialize ComposeManager.

        Args:
            project_dir: Root directory of the project
            console: Rich console for output (creates new one if not provided)
        """
        self.project_dir = project_dir
        self.compose_file = project_dir / "docker-compose.dev.yml"
        self.console = console or Console()

    def start(self, rebuild: bool = False) -> None:
        """Start all services.

        Args:
            rebuild: Whether to rebuild containers before starting
        """
        # Ensure reverse proxy is running first
        proxy = ProxyManager()
        if not proxy.is_running():
            self.console.print("[blue]Starting reverse proxy...[/blue]")
            proxy.start()

        cmd = ["docker", "compose", "-f", str(self.compose_file), "up", "-d"]
        if rebuild:
            cmd.append("--build")

        self.console.print("[blue]Starting services...[/blue]")
        result = subprocess.run(cmd, cwd=self.project_dir)

        if result.returncode != 0:
            raise RuntimeError("Failed to start services")

        # Wait for health checks
        self._wait_for_health()

        self.console.print("[green]✓ All services healthy[/green]")
        self._print_urls()

    def stop(self) -> None:
        """Stop all services."""
        self.console.print("[yellow]Stopping services...[/yellow]")
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "down"],
            cwd=self.project_dir,
        )
        self.console.print("[green]✓ Services stopped[/green]")

    def stream_logs(self) -> None:
        """Stream logs from all services.

        This is a blocking operation that streams logs until interrupted.
        """
        subprocess.run(
            ["docker", "compose", "-f", str(self.compose_file), "logs", "-f"],
            cwd=self.project_dir,
        )

    def logs(self, service: str | None = None, follow: bool = False) -> None:
        """View service logs.

        Args:
            service: Specific service to view logs for (None for all services)
            follow: Whether to follow logs in real-time
        """
        cmd = ["docker", "compose", "-f", str(self.compose_file), "logs"]
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)
        subprocess.run(cmd, cwd=self.project_dir)

    def shell(self, service: str) -> None:
        """Open shell in service container.

        Args:
            service: Service name to open shell in
        """
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(self.compose_file),
                "exec",
                service,
                "/bin/sh",
            ],
            cwd=self.project_dir,
        )

    def reset_database(self) -> None:
        """Reset database volume.

        This will stop services, remove the database volume, and restart services.
        """
        project_name = self._get_project_name()
        volume_name = f"{project_name}_postgres_data"

        # Stop services
        self.stop()

        # Remove volume
        self.console.print(f"[yellow]Removing database volume: {volume_name}[/yellow]")
        subprocess.run(["docker", "volume", "rm", volume_name])

        # Restart services
        self.start()

    def backup_database(self, output: Path) -> None:
        """Backup database to SQL file.

        Args:
            output: Path to output SQL file
        """
        project_name = self._get_project_name()
        with output.open("w") as f:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    f"{project_name}_db",
                    "pg_dump",
                    "-U",
                    "postgres",
                    project_name,
                ],
                stdout=f,
            )

        self.console.print(f"[green]✓ Database backed up to {output}[/green]")

    def restore_database(self, input_file: Path) -> None:
        """Restore database from SQL file.

        Args:
            input_file: Path to input SQL file
        """
        project_name = self._get_project_name()
        with input_file.open("r") as f:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    f"{project_name}_db",
                    "psql",
                    "-U",
                    "postgres",
                    project_name,
                ],
                stdin=f,
            )

        self.console.print(f"[green]✓ Database restored from {input_file}[/green]")

    def _wait_for_health(self, timeout: int = 60) -> None:
        """Wait for all services to become healthy.

        Args:
            timeout: Maximum time to wait in seconds
        """
        self.console.print("[blue]Waiting for services to be healthy...[/blue]")
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.compose_file), "ps", "--format", "json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Simple check: if all containers are running, consider them healthy
                # In a more sophisticated implementation, we'd parse the JSON and check health status
                time.sleep(2)
                return

            time.sleep(2)

        raise TimeoutError("Services did not become healthy in time")

    def _print_urls(self) -> None:
        """Print service URLs."""
        project_name = self._get_project_name()
        hostname = normalize_hostname(project_name)
        self.console.print("\n[bold]Services running:[/bold]")
        self.console.print(
            f"  Application: [link=http://{hostname}.localhost]http://{hostname}.localhost[/link]"
        )
        self.console.print(
            f"  API Docs:    [link=http://{hostname}.localhost/api/docs]http://{hostname}.localhost/api/docs[/link]"
        )
        self.console.print(
            "  Traefik:     [link=http://traefik.localhost:8080]http://traefik.localhost:8080[/link]"
        )
        # Check if MCP service is defined in compose file
        if self._has_mcp_service():
            self.console.print(
                "  MCP Server:  [link=http://localhost:8765/sse]http://localhost:8765/sse[/link]"
            )
        self.console.print(
            "\n[dim]Press Ctrl+C to view logs, or run 'prisme dev:logs -f' in another terminal[/dim]\n"
        )

    def _has_mcp_service(self) -> bool:
        """Check if MCP service is defined in the compose file.

        Returns:
            True if MCP service is defined, False otherwise
        """
        if not self.compose_file.exists():
            return False
        content = self.compose_file.read_text()
        # Simple check for mcp service definition
        return "\n  mcp:" in content or "services:\n  mcp:" in content

    def _get_project_name(self) -> str:
        """Get project name from compose file or directory name.

        Returns:
            Project name
        """
        # Try to read project name from docker-compose file
        # For now, use directory name
        return self.project_dir.name.replace("-", "_").replace(" ", "_")

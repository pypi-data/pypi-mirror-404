"""Traefik reverse proxy management for multi-project development."""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from jinja2 import Template
from rich.console import Console


@dataclass
class ProjectInfo:
    """Information about a running Prism project."""

    name: str
    services: list[str]


@dataclass
class RouteInfo:
    """Information about a Traefik route."""

    name: str
    rule: str
    service: str
    status: str
    priority: int = 0
    middlewares: list[str] = field(default_factory=list)


@dataclass
class ServiceInfo:
    """Information about a Traefik service."""

    name: str
    status: str
    servers: list[str] = field(default_factory=list)


@dataclass
class DiagnosisResult:
    """Result of diagnosing a hostname."""

    hostname: str
    route_exists: bool
    service_healthy: bool
    route_name: str | None = None
    service_name: str | None = None
    suggested_actions: list[str] = field(default_factory=list)


class ProxyManager:
    """Manage shared Traefik reverse proxy for multi-project development."""

    CONTAINER_NAME = "prism-proxy"
    NETWORK_NAME = "prism_proxy_network"
    IMAGE = "traefik:v3.0"
    WEB_PORT = 80
    DASHBOARD_PORT = 8080

    def __init__(self):
        self.console = Console()

    @staticmethod
    def is_running() -> bool:
        """Check if prism-proxy container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name=^{ProxyManager.CONTAINER_NAME}$"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return bool(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, TimeoutError):
            return False

    def start(self) -> None:
        """Start shared reverse proxy container."""
        if self.is_running():
            self.console.print("[dim]Proxy already running[/dim]")
            return

        # Create network if needed
        self._ensure_network()

        # Ensure config files exist
        config_path = self._get_config_path()
        dynamic_config_path = self._get_dynamic_config_path()
        error_pages_path = self._get_error_pages_path()

        # Start error pages container first
        self._start_error_pages_container(error_pages_path)

        self.console.print("[blue]Starting reverse proxy...[/blue]")

        try:
            # Start Traefik container
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    self.CONTAINER_NAME,
                    "--network",
                    self.NETWORK_NAME,
                    "-p",
                    f"{self.WEB_PORT}:80",
                    "-p",
                    f"{self.DASHBOARD_PORT}:8080",
                    "-v",
                    "/var/run/docker.sock:/var/run/docker.sock:ro",
                    "-v",
                    f"{config_path}:/etc/traefik/traefik.yml:ro",
                    "-v",
                    f"{dynamic_config_path}:/etc/traefik/dynamic.yml:ro",
                    "--label",
                    "traefik.enable=true",
                    "--label",
                    "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)",
                    "--label",
                    "traefik.http.routers.dashboard.service=api@internal",
                    "--restart",
                    "unless-stopped",
                    self.IMAGE,
                ],
                check=True,
                capture_output=True,
            )

            self.console.print("[green]✓ Proxy started[/green]")
            self.console.print(f"  Dashboard: http://traefik.localhost:{self.DASHBOARD_PORT}")

        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]Failed to start proxy: {e.stderr.decode()}[/red]")
            raise

    def stop(self) -> None:
        """Stop and remove proxy container."""
        if not self.is_running():
            self.console.print("[dim]Proxy not running[/dim]")
            return

        self.console.print("[yellow]Stopping reverse proxy...[/yellow]")

        try:
            subprocess.run(
                ["docker", "rm", "-f", self.CONTAINER_NAME],
                check=True,
                capture_output=True,
            )
            # Also stop error pages container
            subprocess.run(
                ["docker", "rm", "-f", "prism-error-pages"],
                capture_output=True,
            )
            self.console.print("[green]✓ Proxy stopped[/green]")
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]Failed to stop proxy: {e.stderr.decode()}[/red]")
            raise

    def get_routes(self) -> list[RouteInfo]:
        """Query Traefik API for configured routes."""
        if not self.is_running():
            return []

        try:
            with urlopen(
                f"http://localhost:{self.DASHBOARD_PORT}/api/http/routers", timeout=5
            ) as response:
                data = json.loads(response.read().decode())

            routes = []
            for router in data:
                routes.append(
                    RouteInfo(
                        name=router.get("name", ""),
                        rule=router.get("rule", ""),
                        service=router.get("service", ""),
                        status=router.get("status", "unknown"),
                        priority=router.get("priority", 0),
                        middlewares=router.get("middlewares", []),
                    )
                )
            return routes
        except (URLError, TimeoutError, json.JSONDecodeError):
            return []

    def get_services_status(self) -> list[ServiceInfo]:
        """Query Traefik API for service health."""
        if not self.is_running():
            return []

        try:
            with urlopen(
                f"http://localhost:{self.DASHBOARD_PORT}/api/http/services", timeout=5
            ) as response:
                data = json.loads(response.read().decode())

            services = []
            for svc in data:
                servers = []
                lb = svc.get("loadBalancer", {})
                for server in lb.get("servers", []):
                    servers.append(server.get("url", ""))

                services.append(
                    ServiceInfo(
                        name=svc.get("name", ""),
                        status=svc.get("status", "unknown"),
                        servers=servers,
                    )
                )
            return services
        except (URLError, TimeoutError, json.JSONDecodeError):
            return []

    def diagnose(self, hostname: str) -> DiagnosisResult:
        """Diagnose connectivity for a hostname.

        Args:
            hostname: The hostname to diagnose (e.g., 'myproject.localhost')

        Returns:
            DiagnosisResult with route_exists, service_healthy, and suggested_actions
        """
        result = DiagnosisResult(
            hostname=hostname,
            route_exists=False,
            service_healthy=False,
        )

        if not self.is_running():
            result.suggested_actions.append("Start the proxy: prisme devcontainer up")
            return result

        # Check if route exists for this hostname
        routes = self.get_routes()
        matching_route = None
        for route in routes:
            # Check if hostname matches the route rule
            if f"Host(`{hostname}`)" in route.rule or f"Host(`{hostname.lower()}`)" in route.rule:
                matching_route = route
                result.route_exists = True
                result.route_name = route.name
                result.service_name = route.service
                break

        if not matching_route:
            result.suggested_actions.extend(
                [
                    f"No route configured for {hostname}",
                    "Check if project is running: prisme projects list",
                    "Start your project: prisme devcontainer up",
                ]
            )
            return result

        # Check if service is healthy
        services = self.get_services_status()
        for svc in services:
            if svc.name == result.service_name:
                result.service_healthy = svc.status == "enabled"
                if not result.service_healthy:
                    result.suggested_actions.extend(
                        [
                            f"Service {svc.name} is {svc.status}",
                            "Check container status: prisme devcontainer status",
                            "View logs: prisme devcontainer logs",
                            "Restart: prisme devcontainer up --build",
                        ]
                    )
                break

        if result.route_exists and result.service_healthy:
            result.suggested_actions.append("Route and service are healthy")

        return result

    def list_projects(self) -> list[ProjectInfo]:
        """List all running Prism projects connected to the proxy."""
        try:
            # Get all containers connected to the proxy network
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"network={self.NETWORK_NAME}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return []

            # Parse container names to extract project names
            container_names = result.stdout.strip().split("\n")
            projects: dict[str, list[str]] = {}

            for name in container_names:
                if not name or name == self.CONTAINER_NAME:
                    continue

                # Container names are typically: project-name_service-name
                parts = name.split("_")
                if len(parts) >= 2:
                    project_name = parts[0]
                    service_name = "_".join(parts[1:])

                    if project_name not in projects:
                        projects[project_name] = []
                    projects[project_name].append(service_name)

            return [
                ProjectInfo(name=name, services=services) for name, services in projects.items()
            ]

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def stop_all_projects(self, remove_volumes: bool = False, verbose: bool = True) -> None:
        """Stop all Prism projects (not including the proxy itself).

        Args:
            remove_volumes: Also remove volumes when stopping projects.
            verbose: Show detailed output of what's being stopped.
        """
        projects = self.list_projects()
        stopped_containers = []

        if not projects:
            self.console.print("[yellow]No running projects on proxy network[/yellow]")
        else:
            # First, try to use docker compose down for each project
            for project in projects:
                if verbose:
                    self.console.print(f"[yellow]Stopping project: {project.name}...[/yellow]")
                    for service in project.services:
                        self.console.print(f"  [dim]• {service}[/dim]")

                # Try docker compose down first (cleaner)
                compose_cmd = [
                    "docker",
                    "compose",
                    "-p",
                    project.name,
                    "down",
                    "--remove-orphans",
                ]
                if remove_volumes:
                    compose_cmd.append("--volumes")

                try:
                    result = subprocess.run(
                        compose_cmd,
                        capture_output=True,
                        timeout=60,
                    )
                    if result.returncode == 0:
                        stopped_containers.extend([f"{project.name}_{s}" for s in project.services])
                        continue
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass

                # Fallback: stop containers individually
                for service in project.services:
                    container_name = f"{project.name}_{service}"
                    try:
                        subprocess.run(
                            ["docker", "stop", container_name],
                            capture_output=True,
                            timeout=30,
                        )
                        subprocess.run(
                            ["docker", "rm", "-f", container_name],
                            capture_output=True,
                            timeout=10,
                        )
                        stopped_containers.append(container_name)
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                        if verbose:
                            self.console.print(f"  [red]Could not stop: {container_name}[/red]")

        # Also look for any orphaned Prism containers not on the proxy network
        orphaned = self._find_orphaned_containers()
        if orphaned:
            if verbose:
                self.console.print()
                self.console.print(f"[yellow]Found {len(orphaned)} orphaned containers...[/yellow]")

            for container in orphaned:
                if verbose:
                    self.console.print(f"  [dim]• {container}[/dim]")
                try:
                    subprocess.run(
                        ["docker", "stop", container],
                        capture_output=True,
                        timeout=30,
                    )
                    subprocess.run(
                        ["docker", "rm", "-f", container],
                        capture_output=True,
                        timeout=10,
                    )
                    stopped_containers.append(container)
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    if verbose:
                        self.console.print(f"  [red]Could not stop: {container}[/red]")

        if stopped_containers:
            self.console.print()
            self.console.print(f"[green]✓ Stopped {len(stopped_containers)} container(s)[/green]")
        else:
            self.console.print("[dim]No containers to stop[/dim]")

    def _find_orphaned_containers(self) -> list[str]:
        """Find Prism-related containers not connected to proxy network."""
        try:
            # Find containers with Prism-related labels or naming patterns
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",  # Include stopped containers
                    "--filter",
                    "label=com.prism.project",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            containers = []
            if result.returncode == 0 and result.stdout.strip():
                containers.extend(result.stdout.strip().split("\n"))

            # Also look for containers with prism in the name not on proxy network
            result2 = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    "name=_db_1",  # Common database container suffix
                    "--filter",
                    "name=_postgres_1",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result2.returncode == 0 and result2.stdout.strip():
                for name in result2.stdout.strip().split("\n"):
                    if name and name not in containers:
                        containers.append(name)

            # Exclude the proxy container itself
            return [c for c in containers if c and c != self.CONTAINER_NAME]

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    @staticmethod
    def _ensure_network() -> None:
        """Create proxy network if it doesn't exist."""
        try:
            subprocess.run(
                ["docker", "network", "create", ProxyManager.NETWORK_NAME],
                capture_output=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # Network might already exist, which is fine

    @staticmethod
    def _get_config_path() -> Path:
        """Get path to Traefik config file, creating it if needed."""
        config_dir = Path.home() / ".prism" / "docker"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "traefik.yml"

        # Always regenerate from template to ensure latest version
        template_path = Path(__file__).parent.parent / "templates/jinja2/docker/traefik.yml.jinja2"

        if template_path.exists():
            template = Template(template_path.read_text())
            config_file.write_text(template.render())
        elif not config_file.exists():
            # Fallback: create basic config
            config_file.write_text(
                """api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"

providers:
  docker:
    exposedByDefault: false
    network: prism_proxy_network
    watch: true
  file:
    filename: /etc/traefik/dynamic.yml
    watch: true

log:
  level: INFO
"""
            )

        return config_file

    @staticmethod
    def _get_dynamic_config_path() -> Path:
        """Get path to Traefik dynamic config file, creating it if needed."""
        config_dir = Path.home() / ".prism" / "docker"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "traefik-dynamic.yml"

        # Always regenerate from template to ensure latest version
        template_path = (
            Path(__file__).parent.parent / "templates/jinja2/docker/traefik-dynamic.yml.jinja2"
        )

        if template_path.exists():
            template = Template(template_path.read_text())
            config_file.write_text(template.render())
        elif not config_file.exists():
            # Fallback: create minimal dynamic config
            config_file.write_text(
                """# Traefik dynamic configuration
http:
  middlewares:
    service-error:
      errors:
        status:
          - "502-504"
        service: error-pages@file
        query: "/503.html"
"""
            )

        return config_file

    @staticmethod
    def _get_error_pages_path() -> Path:
        """Get path to error pages directory, copying templates if needed."""
        error_pages_dir = Path.home() / ".prism" / "docker" / "error-pages"
        error_pages_dir.mkdir(parents=True, exist_ok=True)

        # Copy error page templates (removing .jinja2 extension)
        template_dir = Path(__file__).parent.parent / "templates/jinja2/docker/error-pages"

        if template_dir.exists():
            for template_file in template_dir.glob("*.html.jinja2"):
                # Remove .jinja2 extension for output file
                output_name = template_file.name.replace(".jinja2", "")
                dest = error_pages_dir / output_name
                shutil.copy2(template_file, dest)

            # Copy 404.html as index.html for nginx default serving
            not_found_page = error_pages_dir / "404.html"
            index_page = error_pages_dir / "index.html"
            if not_found_page.exists():
                shutil.copy2(not_found_page, index_page)

        return error_pages_dir

    def _start_error_pages_container(self, error_pages_path: Path) -> None:
        """Start a simple nginx container to serve error pages."""
        container_name = "prism-error-pages"

        # Check if already running
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name=^{container_name}$"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            return  # Already running

        # Remove any stopped container with same name
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
        )

        # Start nginx to serve error pages
        try:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    container_name,
                    "--network",
                    self.NETWORK_NAME,
                    "-v",
                    f"{error_pages_path}:/usr/share/nginx/html:ro",
                    "--restart",
                    "unless-stopped",
                    "nginx:alpine",
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Non-fatal - error pages just won't work
            pass

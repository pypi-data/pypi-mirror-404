"""Workspace management for dev containers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

from prisme.devcontainer.config import WorkspaceConfig, WorkspaceInfo
from prisme.devcontainer.generator import DevContainerGenerator


class WorkspaceManager:
    """Manage dev container workspaces."""

    def __init__(self, project_dir: Path | None = None, console: Console | None = None):
        """Initialize the workspace manager.

        Args:
            project_dir: Project directory (defaults to cwd)
            console: Rich console for output
        """
        self.project_dir = project_dir or Path.cwd()
        self.console = console or Console()

    def ensure_devcontainer(self, config: WorkspaceConfig) -> None:
        """Ensure .devcontainer exists, generate if needed.

        Args:
            config: Workspace configuration
        """
        if not config.devcontainer_dir.exists():
            self.console.print("[yellow].devcontainer not found, generating...[/yellow]")
            generator = DevContainerGenerator(self.console)
            generator.generate(config)

    def ensure_env(self, config: WorkspaceConfig) -> None:
        """Ensure .env file exists for this workspace.

        Args:
            config: Workspace configuration
        """
        current_workspace = self._get_env_workspace(config)
        if not config.env_file.exists() or current_workspace != config.workspace_name:
            generator = DevContainerGenerator(self.console)
            generator.generate_env(config)
        # Ensure PRISM_SRC is set for editable installs
        if config.prisme_src and config.env_file.exists():
            content = config.env_file.read_text()
            if "PRISM_SRC=" not in content:
                with config.env_file.open("a") as f:
                    f.write(f"\nPRISM_SRC={config.prisme_src}\n")

    def _get_env_workspace(self, config: WorkspaceConfig) -> str | None:
        """Get workspace name from current .env file.

        Args:
            config: Workspace configuration

        Returns:
            Workspace name from .env or None
        """
        if config.env_file.exists():
            for line in config.env_file.read_text().splitlines():
                if line.startswith("WORKSPACE_NAME="):
                    return line.split("=", 1)[1].strip()
        return None

    def ensure_networks(self) -> None:
        """Ensure required Docker networks exist."""
        subprocess.run(
            ["docker", "network", "create", "prism_proxy_network"],
            capture_output=True,
        )

    def up(self, config: WorkspaceConfig, build: bool = False) -> None:
        """Start the workspace.

        Args:
            config: Workspace configuration
            build: Whether to rebuild containers
        """
        self.ensure_devcontainer(config)
        self.ensure_env(config)
        self.ensure_networks()

        self.console.print(f"[blue]Starting workspace: {config.workspace_name}[/blue]")

        cmd = [
            "docker",
            "compose",
            "-f",
            str(config.compose_file),
            "--env-file",
            str(config.env_file),
            "up",
            "-d",
        ]
        if build:
            cmd.append("--build")

        result = subprocess.run(cmd, cwd=self.project_dir)

        if result.returncode == 0:
            container = f"{config.workspace_name}-app"

            # Configure git safe.directory for vscode user
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "-u",
                    "vscode",
                    container,
                    "git",
                    "config",
                    "--global",
                    "--add",
                    "safe.directory",
                    "/workspace",
                ],
                capture_output=True,
            )

            # Fix ownership on persist volume (may be created as root)
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "-u",
                    "root",
                    container,
                    "bash",
                    "-c",
                    "mkdir -p /persist/venv /persist/node_modules && chown -R vscode:vscode /persist",
                ],
                capture_output=True,
            )

            # Auto-run setup if setup.sh exists (install deps, generate code)
            setup_check = subprocess.run(
                [
                    "docker",
                    "exec",
                    "-u",
                    "vscode",
                    "-w",
                    "/workspace",
                    container,
                    "test",
                    "-f",
                    ".devcontainer/setup.sh",
                ],
                capture_output=True,
            )
            if setup_check.returncode == 0:
                self.console.print("[blue]Running setup...[/blue]")
                subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-u",
                        "vscode",
                        "-w",
                        "/workspace",
                        container,
                        "bash",
                        ".devcontainer/setup.sh",
                    ],
                )

            self.console.print(f"[green]✓ Workspace started: {config.workspace_name}[/green]")
            self.console.print()
            self.console.print(f"  URL: http://{config.hostname}.localhost")
            self.console.print("  Shell: prisme devcontainer shell")
            self.console.print()
            self.console.print("[dim]To start dev servers, run:[/dim]")
            self.console.print("  prisme devcontainer exec 'uv run prisme dev'")
            self.console.print()
            self.console.print("[dim]Or open a shell and start manually:[/dim]")
            self.console.print("  prisme devcontainer shell")
            self.console.print("  uv run prisme dev")
        else:
            self.console.print("[red]Failed to start workspace[/red]")
            raise RuntimeError("Failed to start workspace")

    def down(self, config: WorkspaceConfig, volumes: bool = False) -> None:
        """Stop the workspace.

        Args:
            config: Workspace configuration
            volumes: Whether to remove volumes
        """
        self.ensure_env(config)

        self.console.print(f"[yellow]Stopping workspace: {config.workspace_name}[/yellow]")

        cmd = [
            "docker",
            "compose",
            "-f",
            str(config.compose_file),
            "--env-file",
            str(config.env_file),
            "down",
        ]
        if volumes:
            cmd.append("--volumes")

        subprocess.run(cmd, cwd=self.project_dir)
        self.console.print("[green]✓ Workspace stopped[/green]")

    def shell(self, config: WorkspaceConfig, root: bool = False) -> None:
        """Open shell in workspace.

        Args:
            config: Workspace configuration
            root: Whether to open as root user
        """
        self.ensure_env(config)

        container = f"{config.workspace_name}-app"
        user = "root" if root else "vscode"

        subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                "-u",
                user,
                "-w",
                "/workspace",
                container,
                "bash",
            ],
        )

    def exec(self, config: WorkspaceConfig, command: str, root: bool = False) -> int:
        """Execute a command in the workspace container.

        Args:
            config: Workspace configuration
            command: Command to execute
            root: Whether to run as root user

        Returns:
            Exit code from the command
        """
        self.ensure_env(config)

        container = f"{config.workspace_name}-app"
        user = "root" if root else "vscode"

        result = subprocess.run(
            [
                "docker",
                "exec",
                "-u",
                user,
                "-w",
                "/workspace",
                container,
                "bash",
                "-lc",
                command,
            ],
        )
        return result.returncode

    def logs(
        self,
        config: WorkspaceConfig,
        service: str | None = None,
        follow: bool = False,
    ) -> None:
        """View workspace logs.

        Args:
            config: Workspace configuration
            service: Specific service to show logs for
            follow: Whether to follow log output
        """
        self.ensure_env(config)

        cmd = [
            "docker",
            "compose",
            "-f",
            str(config.compose_file),
            "--env-file",
            str(config.env_file),
            "logs",
        ]
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)

        subprocess.run(cmd, cwd=self.project_dir)

    def status(self, config: WorkspaceConfig) -> None:
        """Show workspace status.

        Args:
            config: Workspace configuration
        """
        self.ensure_env(config)

        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(config.compose_file),
                "--env-file",
                str(config.env_file),
                "ps",
            ],
            cwd=self.project_dir,
        )

    def list_workspaces(self) -> list[WorkspaceInfo]:
        """List all Prism workspaces.

        Returns:
            List of workspace information
        """
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{.Names}}\t{{.Status}}",
                "--filter",
                "label=com.prism.workspace=true",
            ],
            capture_output=True,
            text=True,
        )

        workspaces: dict[str, WorkspaceInfo] = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            name, status = parts[0], parts[1]

            # Extract workspace name from container name (remove -app, -db suffix)
            for suffix in ["-app", "-db", "-redis"]:
                if name.endswith(suffix):
                    workspace_name = name[: -len(suffix)]
                    break
            else:
                continue

            # Determine status
            is_running = "Up" in status

            if workspace_name not in workspaces:
                workspaces[workspace_name] = WorkspaceInfo(
                    workspace_name=workspace_name,
                    status="running" if is_running else "stopped",
                    services=[],
                    url=f"http://{workspace_name}.localhost" if is_running else "",
                )

            # Add service
            service = name.replace(f"{workspace_name}-", "")
            workspaces[workspace_name].services.append(service)

        return list(workspaces.values())

    def print_list(self) -> None:
        """Print table of all workspaces."""
        workspaces = self.list_workspaces()

        if not workspaces:
            self.console.print("[dim]No workspaces found[/dim]")
            return

        table = Table(title="Dev Container Workspaces")
        table.add_column("Workspace", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Services")
        table.add_column("URL")

        for ws in workspaces:
            status_style = "green" if ws.status == "running" else "yellow"
            table.add_row(
                ws.workspace_name,
                f"[{status_style}]{ws.status}[/{status_style}]",
                ", ".join(ws.services),
                ws.url if ws.status == "running" else "-",
            )

        self.console.print(table)

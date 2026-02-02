"""Deployment configuration models for Prism."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HetznerServerType(str, Enum):
    """Hetzner Cloud server types."""

    CX22 = "cx22"  # 2 vCPU, 4GB RAM
    CX23 = "cx23"  # 2 vCPU, 4GB RAM (newer gen)
    CX32 = "cx32"  # 4 vCPU, 8GB RAM - small production
    CX42 = "cx42"  # 8 vCPU, 16GB RAM - medium production
    CX52 = "cx52"  # 16 vCPU, 32GB RAM - large production
    CAX11 = "cax11"  # 2 vCPU, 4GB RAM - ARM staging (cost-effective)


class HetznerLocation(str, Enum):
    """Hetzner Cloud datacenter locations."""

    NUREMBERG = "nbg1"
    FALKENSTEIN = "fsn1"
    HELSINKI = "hel1"
    ASHBURN = "ash"
    HILLSBORO = "hil"


@dataclass
class HetznerConfig:
    """Hetzner-specific deployment configuration."""

    # Location
    location: HetznerLocation = HetznerLocation.FALKENSTEIN

    # Server types
    staging_server_type: HetznerServerType = HetznerServerType.CX23
    production_server_type: HetznerServerType = HetznerServerType.CX23

    # Volume sizes (GB)
    staging_volume_size: int = 10
    production_volume_size: int = 20

    # Networking
    production_floating_ip: bool = True
    private_network_ip_range: str = "10.0.0.0/16"
    network_zone: str = "eu-central"

    # Firewall rules
    firewall_rules: list[dict[str, str | int]] = field(
        default_factory=lambda: [
            {"port": 22, "protocol": "tcp", "description": "SSH"},
            {"port": 80, "protocol": "tcp", "description": "HTTP"},
            {"port": 443, "protocol": "tcp", "description": "HTTPS"},
        ]
    )

    # Remote state (Hetzner Object Storage)
    enable_remote_state: bool = False
    s3_bucket_name: str = ""  # Defaults to "{project_name}-terraform-state"
    s3_endpoint: str = "fsn1.your-objectstorage.com"


@dataclass
class DeploymentConfig:
    """Complete deployment configuration."""

    # Project info
    project_name: str
    domain: str = ""

    # SSL/TLS
    ssl_email: str = ""

    # Provider configuration
    hetzner: HetznerConfig = field(default_factory=HetznerConfig)

    # Application settings
    use_redis: bool = False

    # PostgreSQL settings (VM-hosted)
    postgres_version: str = "16"
    postgres_user: str = "app"
    postgres_db: str = ""  # Defaults to project_name

    # System configuration
    enable_swap: bool = True
    swap_size_mb: int = 1024

    # Docker registry
    docker_registry: str = "ghcr.io"

    def __post_init__(self) -> None:
        """Set defaults based on project name."""
        if not self.postgres_db:
            self.postgres_db = self.project_name.replace("-", "_")

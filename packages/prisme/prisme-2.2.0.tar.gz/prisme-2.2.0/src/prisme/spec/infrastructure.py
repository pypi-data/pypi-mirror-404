"""Infrastructure configuration specification.

This module defines infrastructure-related configuration for
Prism-generated applications, including reverse proxy and SSL settings.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TraefikConfig(BaseModel):
    """Traefik reverse proxy configuration.

    Controls the Traefik deployment for routing and SSL termination.

    Example:
        ```python
        from prisme.spec import TraefikConfig

        traefik = TraefikConfig(
            enabled=True,
            ssl_provider="letsencrypt",
            ssl_email="admin@example.com",
            domain="example.com",
        )
        ```
    """

    enabled: bool = Field(
        default=False,
        description="Enable Traefik reverse proxy",
    )
    ssl_provider: Literal["letsencrypt", "manual", "none"] = Field(
        default="letsencrypt",
        description="SSL certificate provider: letsencrypt (automatic), manual (provide certs), none (no SSL)",
    )
    ssl_email: str = Field(
        default="${SSL_EMAIL}",
        description="Email for Let's Encrypt certificate notifications",
    )
    domain: str = Field(
        default="${DOMAIN}",
        description="Primary domain for the application",
    )
    dashboard_enabled: bool = Field(
        default=False,
        description="Enable Traefik dashboard (not recommended in production)",
    )
    dashboard_subdomain: str = Field(
        default="traefik",
        description="Subdomain for Traefik dashboard (e.g., traefik.{domain})",
    )

    model_config = {"extra": "forbid"}

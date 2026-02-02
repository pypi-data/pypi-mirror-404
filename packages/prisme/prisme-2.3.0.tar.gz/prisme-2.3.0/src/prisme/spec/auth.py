"""Authentication configuration specification.

This module defines the authentication and authorization configuration
for Prism-generated applications.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class OAuthProviderConfig(BaseModel):
    """OAuth provider configuration.

    Defines an external OAuth provider (e.g. GitHub, Google) for social login.

    Example:
        ```python
        from prisme.spec import OAuthProviderConfig

        github = OAuthProviderConfig(
            provider="github",
            client_id_env="GITHUB_CLIENT_ID",
            client_secret_env="GITHUB_CLIENT_SECRET",
            scopes=["user:email"],
        )
        ```
    """

    provider: Literal["github", "google"] = Field(..., description="OAuth provider name")
    client_id_env: str = Field(..., description="Environment variable for the OAuth client ID")
    client_secret_env: str = Field(
        ..., description="Environment variable for the OAuth client secret"
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="OAuth scopes to request",
    )

    model_config = {"extra": "forbid"}


class EmailConfig(BaseModel):
    """Email configuration for transactional auth emails.

    Uses Resend API for sending verification and password reset emails.

    Example:
        ```python
        from prisme.spec import EmailConfig

        email = EmailConfig(
            email_from="MyApp <noreply@example.com>",
            resend_api_key_env="RESEND_API_KEY",
        )
        ```
    """

    email_from: str = Field(
        default="noreply@madewithpris.me",
        description="From address for auth emails (e.g. 'MyApp <noreply@example.com>')",
    )
    resend_api_key_env: str = Field(
        default="RESEND_API_KEY",
        description="Environment variable for Resend API key",
    )

    model_config = {"extra": "forbid"}


class Role(BaseModel):
    """RBAC role definition.

    Roles group permissions together for easier access control management.
    """

    name: str = Field(..., description="Role name (e.g., 'admin', 'editor', 'user')")
    permissions: list[str] = Field(
        default_factory=list,
        description="List of permissions (e.g., ['posts.create', 'posts.delete'])",
    )
    description: str | None = Field(default=None, description="Human-readable role description")

    model_config = {"extra": "forbid"}


class APIKeyConfig(BaseModel):
    """API key authentication configuration.

    Simple bearer token authentication for backend services and APIs.

    Example:
        ```python
        from prisme.spec import APIKeyConfig

        api_key = APIKeyConfig(
            header="Authorization",
            scheme="Bearer",
            env_var="API_KEY",
        )
        ```
    """

    header: str = Field(
        default="Authorization",
        description="HTTP header name for the API key (e.g., 'Authorization', 'X-API-Key')",
    )
    scheme: str = Field(
        default="Bearer",
        description="Authentication scheme (e.g., 'Bearer', 'ApiKey', or empty for raw key)",
    )
    env_var: str = Field(
        default="API_KEY",
        description="Environment variable name containing the API key",
    )
    allow_multiple_keys: bool = Field(
        default=False,
        description="Allow multiple valid API keys (comma-separated in env var)",
    )

    model_config = {"extra": "forbid"}


class SignupWhitelist(BaseModel):
    """Whitelist rules for controlling signup access.

    Supports exact email matches, domain matches, and regex patterns.
    """

    emails: list[str] = Field(default_factory=list, description="Exact email addresses allowed")
    domains: list[str] = Field(
        default_factory=list, description="Email domains allowed (e.g. 'example.com')"
    )
    patterns: list[str] = Field(
        default_factory=list, description="Regex patterns for allowed emails"
    )

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Validate that all patterns are valid regular expressions."""
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e
        return v

    model_config = {"extra": "forbid"}


class SignupAccessConfig(BaseModel):
    """Controls who can sign up for the application."""

    mode: Literal["open", "whitelist", "invite_only"] = Field(
        default="open", description="Signup access mode"
    )
    whitelist: SignupWhitelist = Field(default_factory=SignupWhitelist)

    model_config = {"extra": "forbid"}


class AdminPanelConfig(BaseModel):
    """Admin panel configuration."""

    enabled: bool = Field(default=False, description="Enable admin panel generation")
    path: str = Field(default="/admin", description="Admin panel URL path prefix")

    model_config = {"extra": "forbid"}


class AuthConfig(BaseModel):
    """Authentication configuration.

    Controls authentication and authorization behavior for the entire application.
    When enabled=False, no authentication code is generated (backward compatible).

    Supports two presets:
    - jwt: Full cookie-based JWT auth with signup/login, email verification,
           password reset, MFA (TOTP), account lockout, and OAuth social login
    - api_key: Simple API key authentication for backend services

    Example (JWT auth with full features):
        ```python
        from prisme.spec import AuthConfig, Role, OAuthProviderConfig, EmailConfig

        auth = AuthConfig(
            enabled=True,
            preset="jwt",
            secret_key="${JWT_SECRET}",
            email_verification=True,
            password_reset=True,
            mfa_enabled=True,
            account_lockout=True,
            email=EmailConfig(
                email_from="MyApp <noreply@example.com>",
            ),
            oauth_providers=[
                OAuthProviderConfig(
                    provider="github",
                    client_id_env="GITHUB_CLIENT_ID",
                    client_secret_env="GITHUB_CLIENT_SECRET",
                    scopes=["user:email"],
                ),
            ],
            roles=[
                Role(name="admin", permissions=["*"]),
                Role(name="user"),
            ],
        )
        ```

    Example (API key auth):
        ```python
        from prisme.spec import AuthConfig, APIKeyConfig

        auth = AuthConfig(
            enabled=True,
            preset="api_key",
            api_key=APIKeyConfig(
                header="Authorization",
                scheme="Bearer",
                env_var="API_KEY",
            ),
        )
        ```
    """

    # Core Settings
    enabled: bool = Field(
        default=False,
        description="Enable authentication system (opt-in for backward compatibility)",
    )
    preset: Literal["jwt", "api_key", "custom"] = Field(
        default="jwt",
        description="Authentication preset: 'jwt' for full auth flow, 'api_key' for simple API keys, 'custom' for custom auth",
    )

    # API Key Configuration (only used when preset="api_key")
    api_key: APIKeyConfig = Field(
        default_factory=APIKeyConfig,
        description="API key configuration (only used when preset='api_key')",
    )

    # OAuth Providers
    oauth_providers: list[OAuthProviderConfig] = Field(
        default_factory=list,
        description="OAuth providers for social login (e.g. GitHub, Google)",
    )

    # JWT Settings
    secret_key: str = Field(
        default="${JWT_SECRET}",
        description="JWT signing key (must be loaded from environment variable)",
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")

    # Session Settings (cookie-based)
    session_max_age_seconds: int = Field(
        default=86400 * 7,
        description="Session cookie max age in seconds (default: 7 days)",
        gt=0,
    )
    session_cookie_name: str = Field(
        default="",
        description="Session cookie name (defaults to '{project_name}_session')",
    )

    # Password Policy
    password_min_length: int = Field(default=8, description="Minimum password length", ge=4, le=128)
    password_require_uppercase: bool = Field(
        default=True, description="Require at least one uppercase letter"
    )
    password_require_lowercase: bool = Field(
        default=True, description="Require at least one lowercase letter"
    )
    password_require_number: bool = Field(default=True, description="Require at least one number")
    password_require_special: bool = Field(
        default=False, description="Require at least one special character"
    )

    # Feature Flags
    email_verification: bool = Field(
        default=True, description="Require email verification before login"
    )
    password_reset: bool = Field(default=True, description="Enable password reset flow")
    mfa_enabled: bool = Field(
        default=False, description="Enable TOTP-based multi-factor authentication"
    )
    account_lockout: bool = Field(
        default=True, description="Lock accounts after too many failed login attempts"
    )
    max_failed_attempts: int = Field(
        default=5, description="Number of failed login attempts before lockout", ge=1
    )
    lockout_duration_minutes: int = Field(
        default=15, description="Duration of account lockout in minutes", ge=1
    )
    allow_signup: bool = Field(default=True, description="Allow public user registration")

    # Email Configuration
    email: EmailConfig = Field(
        default_factory=EmailConfig,
        description="Email configuration for transactional auth emails (Resend)",
    )

    # Token expiration
    email_verification_token_hours: int = Field(
        default=24, description="Email verification token expiry in hours", gt=0
    )
    password_reset_token_hours: int = Field(
        default=1, description="Password reset token expiry in hours", gt=0
    )

    # RBAC (Role-Based Access Control)
    roles: list[Role] = Field(
        default_factory=list,
        description="Role definitions for RBAC. Empty list means role-free auth.",
    )
    default_role: str = Field(default="user", description="Default role assigned to new users")

    # Admin Panel
    admin_panel: AdminPanelConfig = Field(
        default_factory=AdminPanelConfig,
        description="Admin panel configuration",
    )

    # Signup Access Control
    signup_access: SignupAccessConfig = Field(
        default_factory=SignupAccessConfig,
        description="Signup access control configuration",
    )

    # User Model Configuration
    user_model: str = Field(
        default="User",
        description="Name of the user model in specs (must exist if auth enabled)",
    )
    username_field: str = Field(
        default="email",
        description="Field to use for login (typically 'email' or 'username')",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate secret key is set properly."""
        if v and not v.strip():
            raise ValueError("secret_key cannot be empty string")
        return v

    @field_validator("username_field")
    @classmethod
    def validate_username_field(cls, v: str) -> str:
        """Validate username field name."""
        if v not in ["email", "username"]:
            raise ValueError(f"username_field must be 'email' or 'username', got '{v}'")
        return v

    @field_validator("default_role")
    @classmethod
    def validate_default_role_exists(cls, v: str, info) -> str:
        """Validate default role exists in roles list (if roles are defined)."""
        return v

    @model_validator(mode="after")
    def validate_preset_requirements(self) -> AuthConfig:
        """Validate that required fields are set for the chosen preset."""
        if not self.enabled:
            return self

        if self.preset == "api_key":
            pass
        elif self.preset == "jwt" and (not self.secret_key or self.secret_key == ""):
            raise ValueError("secret_key is required for JWT authentication")
        return self

    def has_oauth_provider(self, provider: str) -> bool:
        """Check if a specific OAuth provider is configured."""
        return any(p.provider == provider for p in self.oauth_providers)

    def get_oauth_provider(self, provider: str) -> OAuthProviderConfig | None:
        """Get OAuth provider config by name."""
        for p in self.oauth_providers:
            if p.provider == provider:
                return p
        return None

    @property
    def has_email_features(self) -> bool:
        """Whether any email-sending feature is enabled."""
        return self.email_verification or self.password_reset

    model_config = {"extra": "forbid"}

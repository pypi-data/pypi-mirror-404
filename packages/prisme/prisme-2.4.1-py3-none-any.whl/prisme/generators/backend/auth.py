"""Authentication generator for Prism.

Generates cookie-based JWT authentication infrastructure including:
- Token service (JWT creation and verification via cookies)
- Password service (bcrypt hashing and validation)
- Authentication middleware (FastAPI dependencies)
- Authentication routes (signup, login, email verification, password reset, MFA, OAuth)
- Authentication schemas (Pydantic models)
- Email service (Resend API)
- TOTP service (MFA)
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.case_conversion import to_snake_case
from prisme.utils.template_engine import TemplateRenderer


class AuthGenerator(GeneratorBase):
    """Generates cookie-based JWT authentication system for backend."""

    REQUIRED_TEMPLATES = [
        "backend/auth/token_service.py.jinja2",
        "backend/auth/password_service.py.jinja2",
        "backend/auth/middleware_auth.py.jinja2",
        "backend/auth/schemas_auth.py.jinja2",
        "backend/auth/routes_auth.py.jinja2",
        "backend/auth/auth_init.py.jinja2",
        "backend/auth/middleware_init.py.jinja2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Skip generation if auth is not enabled or preset is not JWT
        if not self.auth_config.enabled or self.auth_config.preset != "jwt":
            self.skip_generation = True
            return

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

        # Setup paths for generated auth files
        backend_base = Path(self.generator_config.backend_output)
        package_name = self.get_package_name()
        package_base = backend_base / package_name

        self.auth_base = package_base / "auth"
        self.middleware_path = package_base / "middleware"
        self.models_path = package_base / self.generator_config.models_path
        self.schemas_path = package_base / "schemas"
        self.routes_base = package_base / "api" / "rest"
        self.services_path = package_base / "services"

    def _get_common_context(self) -> dict:
        """Build the common template context from auth config."""
        config = self.auth_config
        project_name = self.get_package_name()
        user_model = config.user_model
        user_model_snake = to_snake_case(user_model)
        username_field = config.username_field
        is_email = username_field == "email"

        return {
            "project_name": project_name,
            "project_title": getattr(self.spec, "title", project_name),
            "user_model": user_model,
            "user_model_snake": user_model_snake,
            "username_field": username_field,
            "username_field_title": username_field.title(),
            "is_email": is_email,
            "default_role": config.default_role,
            "algorithm": config.algorithm,
            "session_max_age_seconds": config.session_max_age_seconds,
            "session_cookie_name": config.session_cookie_name or f"{project_name}_session",
            # Feature flags
            "email_verification": config.email_verification,
            "password_reset": config.password_reset,
            "mfa_enabled": config.mfa_enabled,
            "account_lockout": config.account_lockout,
            "has_email_features": config.has_email_features,
            # Password policy
            "password_min_length": config.password_min_length,
            "min_length": config.password_min_length,
            "require_uppercase": config.password_require_uppercase,
            "require_lowercase": config.password_require_lowercase,
            "require_number": config.password_require_number,
            "require_special": config.password_require_special,
            # Lockout
            "max_failed_attempts": config.max_failed_attempts,
            "lockout_duration_minutes": config.lockout_duration_minutes,
            # Token expiry
            "email_verification_token_hours": config.email_verification_token_hours,
            "password_reset_token_hours": config.password_reset_token_hours,
            # Email
            "email_from": config.email.email_from,
            # OAuth
            "oauth_providers": [p.model_dump() for p in config.oauth_providers],
            # Admin panel
            "admin_panel_enabled": config.admin_panel.enabled,
        }

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all authentication-related files.

        Returns:
            List of generated files with content and strategies
        """
        if getattr(self, "skip_generation", False):
            return []

        files = []
        config = self.auth_config

        # User model
        files.append(self._generate_user_model())

        # Auth config (settings)
        files.append(self._generate_auth_config())

        # Core services
        files.append(self._generate_token_service())
        files.append(self._generate_password_service())

        # Middleware
        files.append(self._generate_jwt_middleware())

        # Routes
        files.append(self._generate_auth_routes())

        # Schemas
        files.append(self._generate_auth_schemas())

        # Init files
        files.append(self._generate_auth_init())
        files.append(self._generate_middleware_init())

        # Conditional: Email service
        if config.has_email_features:
            files.append(self._generate_email_service())

        # Conditional: TOTP service
        if config.mfa_enabled:
            files.append(self._generate_totp_service())

        return files

    def _generate_user_model(self) -> GeneratedFile:
        """Generate the User SQLAlchemy model."""
        ctx = self._get_common_context()
        user_model_snake = ctx["user_model_snake"]
        content = self.renderer.render_file(
            "backend/auth/user_model.py.jinja2",
            context=ctx,
        )

        return GeneratedFile(
            path=self.models_path / f"{user_model_snake}.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="User model for authentication",
        )

    def _generate_auth_config(self) -> GeneratedFile:
        """Generate auth-specific settings module."""
        content = self.renderer.render_file(
            "backend/auth/auth_config.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.auth_base / "config.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth settings",
        )

    def _generate_token_service(self) -> GeneratedFile:
        """Generate JWT token creation and verification service."""
        content = self.renderer.render_file(
            "backend/auth/token_service.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.auth_base / "token_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="JWT token service",
        )

    def _generate_password_service(self) -> GeneratedFile:
        """Generate password hashing and validation service."""
        content = self.renderer.render_file(
            "backend/auth/password_service.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.auth_base / "password_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Password hashing service",
        )

    def _generate_jwt_middleware(self) -> GeneratedFile:
        """Generate FastAPI authentication middleware and dependencies."""
        content = self.renderer.render_file(
            "backend/auth/middleware_auth.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.middleware_path / "auth.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Cookie-based JWT authentication middleware",
        )

    def _generate_auth_schemas(self) -> GeneratedFile:
        """Generate Pydantic schemas for authentication."""
        content = self.renderer.render_file(
            "backend/auth/schemas_auth.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.schemas_path / "auth.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth Pydantic schemas",
        )

    def _generate_auth_routes(self) -> GeneratedFile:
        """Generate FastAPI authentication routes."""
        content = self.renderer.render_file(
            "backend/auth/routes_auth.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.routes_base / "auth.py",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,  # Allow customization
            description="Auth API routes",
        )

    def _generate_auth_init(self) -> GeneratedFile:
        """Generate __init__.py for auth module."""
        content = self.renderer.render_file(
            "backend/auth/auth_init.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.auth_base / "__init__.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth module init",
        )

    def _generate_middleware_init(self) -> GeneratedFile:
        """Generate __init__.py for middleware module."""
        content = self.renderer.render_file(
            "backend/auth/middleware_init.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.middleware_path / "__init__.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Middleware module init",
        )

    def _generate_email_service(self) -> GeneratedFile:
        """Generate Resend email service."""
        content = self.renderer.render_file(
            "backend/auth/email_service.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.services_path / "email_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Email service (Resend)",
        )

    def _generate_totp_service(self) -> GeneratedFile:
        """Generate TOTP service for MFA."""
        content = self.renderer.render_file(
            "backend/auth/totp_service.py.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.auth_base / "totp_service.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="TOTP service (MFA)",
        )

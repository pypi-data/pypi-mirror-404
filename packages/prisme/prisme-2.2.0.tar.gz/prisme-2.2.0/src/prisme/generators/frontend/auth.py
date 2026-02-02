"""Frontend authentication generator for Prism.

Generates React authentication components including:
- AuthContext with useAuth() hook (cookie-based)
- Login and Signup forms (with MFA, OAuth support)
- Protected route wrapper
- Auth API client
- Forgot password, reset password, email verification pages
- TOTP verification component
- OAuth callback page
"""

from __future__ import annotations

from pathlib import Path

from prisme.generators.base import GeneratedFile, GeneratorBase
from prisme.spec.stack import FileStrategy
from prisme.utils.template_engine import TemplateRenderer


class FrontendAuthGenerator(GeneratorBase):
    """Generates React authentication components for frontend."""

    REQUIRED_TEMPLATES = [
        "frontend/auth/AuthContext.tsx.jinja2",
        "frontend/auth/LoginForm.tsx.jinja2",
        "frontend/auth/SignupForm.tsx.jinja2",
        "frontend/auth/ProtectedRoute.tsx.jinja2",
        "frontend/auth/Login.tsx.jinja2",
        "frontend/auth/Signup.tsx.jinja2",
        "frontend/auth/index.ts.jinja2",
        "frontend/auth/authApi.ts.jinja2",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Skip generation if auth is not enabled
        if not self.auth_config.enabled:
            self.skip_generation = True
            return

        # Initialize template renderer
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

        # Setup paths for generated auth files
        frontend_base = Path(self.generator_config.frontend_output)
        self.contexts_path = frontend_base / "contexts"
        self.components_path = frontend_base / "components" / "auth"
        self.pages_path = frontend_base / "pages"
        self.lib_path = frontend_base / "lib"

    def _get_common_context(self) -> dict:
        """Build template context from auth config."""
        config = self.auth_config
        username_field = config.username_field
        is_email = username_field == "email"
        input_type = "email" if is_email else "text"

        return {
            "user_model": config.user_model,
            "username_field": username_field,
            "username_field_title": username_field.title(),
            "username_field_capitalized": username_field[0].upper() + username_field[1:],
            "input_type": input_type,
            "is_email": is_email,
            # Feature flags
            "email_verification": config.email_verification,
            "password_reset": config.password_reset,
            "mfa_enabled": config.mfa_enabled,
            "has_email_features": config.has_email_features,
            # Password policy
            "password_min_length": config.password_min_length,
            "password_require_uppercase": config.password_require_uppercase,
            "password_require_lowercase": config.password_require_lowercase,
            "password_require_number": config.password_require_number,
            "password_require_special": config.password_require_special,
            # OAuth
            "oauth_providers": [p.model_dump() for p in config.oauth_providers],
        }

    def generate_files(self) -> list[GeneratedFile]:
        """Generate all frontend authentication files."""
        if getattr(self, "skip_generation", False):
            return []

        config = self.auth_config
        files = []

        # Auth API client
        files.append(self._generate_auth_api())

        # Auth context and hook
        files.append(self._generate_auth_context())

        # Auth components
        files.append(self._generate_login_form())
        files.append(self._generate_signup_form())
        files.append(self._generate_protected_route())

        # Auth pages
        files.append(self._generate_login_page())
        files.append(self._generate_signup_page())

        # Conditional components and pages
        if config.password_reset:
            files.append(self._generate_forgot_password_form())
            files.append(self._generate_reset_password_page())

        if config.email_verification:
            files.append(self._generate_verify_email_page())
            files.append(self._generate_email_verification_component())

        if config.mfa_enabled:
            files.append(self._generate_totp_verify())

        if config.oauth_providers:
            files.append(self._generate_auth_callback_page())

        # Index files
        files.append(self._generate_components_index())

        return files

    def _generate_auth_api(self) -> GeneratedFile:
        """Generate auth API client."""
        content = self.renderer.render_file(
            "frontend/auth/authApi.ts.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.lib_path / "authApi.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth API client",
        )

    def _generate_auth_context(self) -> GeneratedFile:
        """Generate AuthContext with useAuth() hook."""
        content = self.renderer.render_file(
            "frontend/auth/AuthContext.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.contexts_path / "AuthContext.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth context with useAuth hook",
        )

    def _generate_login_form(self) -> GeneratedFile:
        """Generate LoginForm component."""
        content = self.renderer.render_file(
            "frontend/auth/LoginForm.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "LoginForm.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Login form component",
        )

    def _generate_signup_form(self) -> GeneratedFile:
        """Generate SignupForm component."""
        content = self.renderer.render_file(
            "frontend/auth/SignupForm.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "SignupForm.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Signup form component",
        )

    def _generate_protected_route(self) -> GeneratedFile:
        """Generate ProtectedRoute wrapper component."""
        content = self.renderer.render_file(
            "frontend/auth/ProtectedRoute.tsx.jinja2",
            context={},
        )

        return GeneratedFile(
            path=self.components_path / "ProtectedRoute.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Protected route wrapper",
        )

    def _generate_login_page(self) -> GeneratedFile:
        """Generate Login page component."""
        content = self.renderer.render_file(
            "frontend/auth/Login.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.pages_path / "Login.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Login page",
        )

    def _generate_signup_page(self) -> GeneratedFile:
        """Generate Signup page component."""
        content = self.renderer.render_file(
            "frontend/auth/Signup.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.pages_path / "Signup.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Signup page",
        )

    def _generate_forgot_password_form(self) -> GeneratedFile:
        """Generate ForgotPasswordForm component."""
        content = self.renderer.render_file(
            "frontend/auth/ForgotPasswordForm.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "ForgotPasswordForm.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Forgot password form",
        )

    def _generate_reset_password_page(self) -> GeneratedFile:
        """Generate ResetPassword page."""
        content = self.renderer.render_file(
            "frontend/auth/ResetPassword.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.pages_path / "ResetPassword.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Reset password page",
        )

    def _generate_verify_email_page(self) -> GeneratedFile:
        """Generate VerifyEmail page."""
        content = self.renderer.render_file(
            "frontend/auth/VerifyEmail.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.pages_path / "VerifyEmail.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Email verification page",
        )

    def _generate_email_verification_component(self) -> GeneratedFile:
        """Generate EmailVerification component (pending screen)."""
        content = self.renderer.render_file(
            "frontend/auth/EmailVerification.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "EmailVerification.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Email verification pending screen",
        )

    def _generate_totp_verify(self) -> GeneratedFile:
        """Generate TOTPVerify component."""
        content = self.renderer.render_file(
            "frontend/auth/TOTPVerify.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "TOTPVerify.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="TOTP verification component",
        )

    def _generate_auth_callback_page(self) -> GeneratedFile:
        """Generate OAuth callback page."""
        content = self.renderer.render_file(
            "frontend/auth/AuthCallback.tsx.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.pages_path / "AuthCallback.tsx",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="OAuth callback page",
        )

    def _generate_components_index(self) -> GeneratedFile:
        """Generate index file for auth components."""
        content = self.renderer.render_file(
            "frontend/auth/index.ts.jinja2",
            context=self._get_common_context(),
        )

        return GeneratedFile(
            path=self.components_path / "index.ts",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Auth components index",
        )

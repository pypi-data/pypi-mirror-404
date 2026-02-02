"""Tests for authentication specification models."""

import pytest

from prisme.spec import (
    AdminPanelConfig,
    AuthConfig,
    FieldSpec,
    FieldType,
    ModelSpec,
    Role,
    SignupAccessConfig,
    SignupWhitelist,
    StackSpec,
)
from prisme.spec.project import ProjectSpec
from prisme.spec.validators import validate_auth_config


class TestAuthConfig:
    """Tests for AuthConfig model."""

    def test_default_auth_disabled(self):
        """Auth is disabled by default for backward compatibility."""
        auth = AuthConfig()
        assert auth.enabled is False

    def test_auth_enabled_with_valid_config(self):
        """Can create auth config with enabled=True."""
        auth = AuthConfig(
            enabled=True,
            secret_key="${JWT_SECRET}",
            password_min_length=12,
        )
        assert auth.enabled is True
        assert auth.password_min_length == 12

    def test_password_policy_defaults(self):
        """Password policy has secure defaults."""
        auth = AuthConfig()
        assert auth.password_min_length == 8
        assert auth.password_require_uppercase is True
        assert auth.password_require_lowercase is True
        assert auth.password_require_number is True
        assert auth.password_require_special is False

    def test_session_and_token_expiration_defaults(self):
        """Session and token expiration have reasonable defaults."""
        auth = AuthConfig()
        assert auth.session_max_age_seconds == 86400 * 7  # 7 days
        assert auth.email_verification_token_hours == 24
        assert auth.password_reset_token_hours == 1

    def test_username_field_validation(self):
        """Username field must be email or username."""
        # Valid values
        auth1 = AuthConfig(username_field="email")
        auth2 = AuthConfig(username_field="username")
        assert auth1.username_field == "email"
        assert auth2.username_field == "username"

        # Invalid value
        with pytest.raises(ValueError, match="must be 'email' or 'username'"):
            AuthConfig(username_field="invalid")

    def test_roles_configuration(self):
        """Can configure roles for RBAC."""
        auth = AuthConfig(
            enabled=True,
            roles=[
                Role(name="admin", permissions=["*"]),
                Role(name="editor", permissions=["posts.create", "posts.update"]),
                Role(name="viewer", permissions=["posts.read"]),
            ],
            default_role="viewer",
        )
        assert len(auth.roles) == 3
        assert auth.default_role == "viewer"
        assert auth.roles[0].name == "admin"
        assert auth.roles[0].permissions == ["*"]


class TestRole:
    """Tests for Role model."""

    def test_role_creation(self):
        """Can create a role with name and permissions."""
        role = Role(
            name="editor",
            permissions=["posts.create", "posts.update", "posts.delete"],
            description="Can manage posts",
        )
        assert role.name == "editor"
        assert len(role.permissions) == 3
        assert role.description == "Can manage posts"

    def test_role_with_wildcard_permission(self):
        """Can use wildcard permission for admin."""
        role = Role(name="admin", permissions=["*"])
        assert role.permissions == ["*"]


class TestAuthValidation:
    """Tests for auth configuration validation."""

    def test_validation_passes_when_auth_disabled(self):
        """No validation errors when auth is disabled."""
        stack = StackSpec(
            name="test-app",
            models=[],
        )
        project = ProjectSpec(name="test-app")
        errors = validate_auth_config(stack, project)
        assert errors == []

    def test_validation_fails_when_user_model_missing(self):
        """Validation fails if auth enabled but user model doesn't exist."""
        stack = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="Post",
                    fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(enabled=True, user_model="User"),
        )
        errors = validate_auth_config(stack, project)
        assert len(errors) == 1
        assert "user model" in errors[0].lower()
        assert "user" in errors[0].lower()

    def test_validation_passes_with_valid_user_model(self):
        """Validation passes when user model has all required fields."""
        stack = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="User",
                    fields=[
                        FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                        FieldSpec(
                            name="password_hash",
                            type=FieldType.STRING,
                            required=True,
                            hidden=True,
                        ),
                        FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                        FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                    ],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(enabled=True, user_model="User"),
        )
        errors = validate_auth_config(stack, project)
        assert errors == []

    def test_validation_fails_when_required_fields_missing(self):
        """Validation fails if user model missing required auth fields."""
        stack = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="User",
                    fields=[
                        FieldSpec(name="email", type=FieldType.STRING, required=True),
                        # Missing: password_hash, is_active, roles
                    ],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(enabled=True, user_model="User"),
        )
        errors = validate_auth_config(stack, project)
        assert len(errors) == 1
        assert "missing required fields" in errors[0]
        assert "password_hash" in errors[0]
        assert "is_active" in errors[0]
        assert "roles" in errors[0]

    def test_validation_fails_when_password_hash_not_hidden(self):
        """Validation fails if password_hash not hidden from API."""
        stack = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="User",
                    fields=[
                        FieldSpec(name="email", type=FieldType.STRING, required=True),
                        FieldSpec(
                            name="password_hash",
                            type=FieldType.STRING,
                            required=True,
                            hidden=False,  # Security issue!
                        ),
                        FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                        FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                    ],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(enabled=True, user_model="User"),
        )
        errors = validate_auth_config(stack, project)
        assert len(errors) == 1
        assert "password_hash" in errors[0]
        assert "hidden=True" in errors[0]
        assert "security" in errors[0].lower()

    def test_validation_fails_when_default_role_not_in_roles(self):
        """Validation fails if default role not defined in roles list."""
        stack = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="User",
                    fields=[
                        FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                        FieldSpec(
                            name="password_hash",
                            type=FieldType.STRING,
                            required=True,
                            hidden=True,
                        ),
                        FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                        FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                    ],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(
                enabled=True,
                user_model="User",
                roles=[
                    Role(name="admin", permissions=["*"]),
                    Role(name="editor", permissions=["posts.write"]),
                ],
                default_role="viewer",  # Not in roles list!
            ),
        )
        errors = validate_auth_config(stack, project)
        assert len(errors) == 1
        assert "default role 'viewer'" in errors[0].lower()
        assert "not defined" in errors[0]


class TestAdminPanelConfig:
    """Tests for AdminPanelConfig model."""

    def test_defaults(self):
        config = AdminPanelConfig()
        assert config.enabled is False
        assert config.path == "/admin"

    def test_custom_path(self):
        config = AdminPanelConfig(enabled=True, path="/management")
        assert config.enabled is True
        assert config.path == "/management"


class TestSignupAccessConfig:
    """Tests for SignupAccessConfig model."""

    def test_defaults(self):
        config = SignupAccessConfig()
        assert config.mode == "open"
        assert config.whitelist.emails == []
        assert config.whitelist.domains == []
        assert config.whitelist.patterns == []

    def test_whitelist_mode(self):
        config = SignupAccessConfig(
            mode="whitelist",
            whitelist=SignupWhitelist(
                emails=["admin@example.com"],
                domains=["example.com"],
            ),
        )
        assert config.mode == "whitelist"
        assert config.whitelist.emails == ["admin@example.com"]

    def test_invite_only_mode(self):
        config = SignupAccessConfig(mode="invite_only")
        assert config.mode == "invite_only"


class TestSignupWhitelist:
    """Tests for SignupWhitelist model."""

    def test_valid_regex_patterns(self):
        wl = SignupWhitelist(patterns=[r".*@example\.com$", r"admin\+.*@test\.org"])
        assert len(wl.patterns) == 2

    def test_invalid_regex_pattern_raises(self):
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SignupWhitelist(patterns=["[invalid"])

    def test_empty_defaults(self):
        wl = SignupWhitelist()
        assert wl.emails == []
        assert wl.domains == []
        assert wl.patterns == []


class TestAuthConfigWithAdminPanel:
    """Tests for AuthConfig with admin panel fields."""

    def test_admin_panel_defaults(self):
        auth = AuthConfig()
        assert auth.admin_panel.enabled is False
        assert auth.signup_access.mode == "open"

    def test_admin_panel_enabled(self):
        auth = AuthConfig(
            enabled=True,
            admin_panel=AdminPanelConfig(enabled=True),
            signup_access=SignupAccessConfig(mode="whitelist"),
        )
        assert auth.admin_panel.enabled is True
        assert auth.signup_access.mode == "whitelist"

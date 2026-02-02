"""Tests for authentication code generator."""

from pathlib import Path

import pytest

from prisme.generators import AuthGenerator, GeneratorContext
from prisme.spec import AuthConfig, FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.project import ProjectSpec


@pytest.fixture
def auth_enabled_spec() -> StackSpec:
    """Stack spec with authentication enabled."""
    return StackSpec(
        name="test-auth-app",
        models=[
            ModelSpec(
                name="User",
                fields=[
                    FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                    FieldSpec(
                        name="password_hash", type=FieldType.STRING, required=True, hidden=True
                    ),
                    FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                    FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                ],
            )
        ],
    )


@pytest.fixture
def auth_enabled_project() -> ProjectSpec:
    """Project spec with authentication enabled."""
    return ProjectSpec(
        name="test-auth-app",
        auth=AuthConfig(
            enabled=True,
            secret_key="${JWT_SECRET}",
            user_model="User",
            username_field="email",
        ),
    )


@pytest.fixture
def auth_disabled_spec() -> StackSpec:
    """Stack spec with authentication disabled (default)."""
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Post",
                fields=[
                    FieldSpec(name="title", type=FieldType.STRING, required=True),
                ],
            )
        ],
    )


@pytest.fixture
def generator_context_with_auth(
    auth_enabled_spec: StackSpec, auth_enabled_project: ProjectSpec, tmp_path: Path
) -> GeneratorContext:
    """Generator context with auth enabled."""
    return GeneratorContext(
        domain_spec=auth_enabled_spec,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=auth_enabled_project,
    )


@pytest.fixture
def generator_context_without_auth(
    auth_disabled_spec: StackSpec, tmp_path: Path
) -> GeneratorContext:
    """Generator context with auth disabled."""
    return GeneratorContext(
        domain_spec=auth_disabled_spec,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-app"),
    )


class TestAuthGenerator:
    """Tests for AuthGenerator."""

    def test_generator_skips_when_auth_disabled(
        self, generator_context_without_auth: GeneratorContext
    ):
        """Generator returns empty list when auth is disabled."""
        generator = AuthGenerator(generator_context_without_auth)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generator_creates_files_when_auth_enabled(
        self, generator_context_with_auth: GeneratorContext
    ):
        """Generator creates auth files when auth is enabled."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        # Should generate multiple files
        assert len(files) > 0
        # user_model, config, token_service, password_service, middleware, routes,
        # schemas, email_service (has_email_features=True by default), 2x __init__
        assert len(files) == 10

        # Check skip_generation is not set
        assert not hasattr(generator, "skip_generation") or not generator.skip_generation

    def test_generator_creates_token_service(self, generator_context_with_auth: GeneratorContext):
        """Generator creates token service file."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        file_paths = [str(f.path) for f in files]
        assert any("token_service.py" in p for p in file_paths)

        # Check content — now function-based, not class-based
        token_service_file = next(f for f in files if "token_service.py" in str(f.path))
        assert "create_session_jwt" in token_service_file.content
        assert "decode_session_jwt" in token_service_file.content
        assert "PyJWT" in token_service_file.description or "JWT" in token_service_file.description

    def test_generator_creates_password_service(
        self, generator_context_with_auth: GeneratorContext
    ):
        """Generator creates password service file."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        file_paths = [str(f.path) for f in files]
        assert any("password_service.py" in p for p in file_paths)

        # Check content — now function-based
        password_service_file = next(f for f in files if "password_service.py" in str(f.path))
        assert "hash_password" in password_service_file.content
        assert "verify_password" in password_service_file.content
        assert "validate_password_strength" in password_service_file.content
        assert "bcrypt" in password_service_file.content

    def test_generator_creates_middleware(self, generator_context_with_auth: GeneratorContext):
        """Generator creates JWT middleware file."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        # Find middleware file
        middleware_files = [
            f for f in files if "middleware" in str(f.path) and "auth.py" in str(f.path)
        ]
        assert len(middleware_files) == 1

        middleware_file = middleware_files[0]
        assert "get_current_user" in middleware_file.content
        assert "get_current_active_user" in middleware_file.content
        assert "require_roles" in middleware_file.content
        assert "CurrentUser" in middleware_file.content
        assert "CurrentActiveUser" in middleware_file.content

    def test_generator_creates_auth_routes(self, generator_context_with_auth: GeneratorContext):
        """Generator creates auth routes file."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        # Find auth routes file
        route_files = [f for f in files if "rest" in str(f.path) and "auth.py" in str(f.path)]
        assert len(route_files) == 1

        route_file = route_files[0]
        content = route_file.content

        # Check router prefix
        assert 'prefix="/auth"' in content

        # Check key route decorators exist
        assert '"/signup"' in content
        assert '"/login"' in content
        assert '"/logout"' in content
        assert '"/me"' in content

        # Check route functions
        assert "async def signup" in content
        assert "async def login" in content
        assert "async def logout" in content

    def test_generator_creates_auth_schemas(self, generator_context_with_auth: GeneratorContext):
        """Generator creates auth schemas file."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        # Find schemas file
        schema_files = [f for f in files if "schemas" in str(f.path) and "auth.py" in str(f.path)]
        assert len(schema_files) == 1

        schema_file = schema_files[0]
        content = schema_file.content

        # Check key schemas exist
        assert "class LoginRequest" in content
        assert "class SignupRequest" in content
        assert "class UserResponse" in content

    def test_generator_uses_project_name_in_imports(
        self, generator_context_with_auth: GeneratorContext
    ):
        """Generator uses correct project name in imports."""
        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        project_name = "test_auth_app"  # snake_case of "test-auth-app"

        # Check imports in multiple files — now imports from auth.config
        for file in files:
            if "middleware" in str(file.path) and "auth.py" in str(file.path):
                assert f"from {project_name}.auth.token_service" in file.content
                assert f"from {project_name}.database" in file.content
            elif "rest" in str(file.path) and "auth.py" in str(file.path):
                assert f"from {project_name}.auth." in file.content

    def test_generator_uses_correct_username_field(self):
        """Generator uses configured username field (email vs username)."""
        # Test with email
        spec_email = StackSpec(
            name="test-app",
            models=[
                ModelSpec(
                    name="User",
                    fields=[
                        FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                        FieldSpec(
                            name="password_hash", type=FieldType.STRING, required=True, hidden=True
                        ),
                        FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                        FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                    ],
                )
            ],
        )
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(enabled=True, username_field="email", user_model="User"),
        )

        context = GeneratorContext(
            domain_spec=spec_email, output_dir=Path("/tmp"), dry_run=True, project_spec=project
        )
        generator = AuthGenerator(context)
        files = generator.generate_files()

        # Find routes file
        route_file = next(f for f in files if "rest" in str(f.path) and "auth.py" in str(f.path))
        assert ".email" in route_file.content

    def test_generator_includes_password_policy_in_service(
        self, generator_context_with_auth: GeneratorContext
    ):
        """Generator includes configured password policy in password service."""
        # Modify auth config on project_spec
        generator_context_with_auth.project_spec.auth.password_min_length = 12
        generator_context_with_auth.project_spec.auth.password_require_special = True

        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        password_service_file = next(f for f in files if "password_service.py" in str(f.path))
        content = password_service_file.content

        # Now uses inline values, not self.min_length
        assert "12" in content  # min length rendered in template
        assert "special" in content.lower()  # special char validation present

    def test_generator_file_strategies(self, generator_context_with_auth: GeneratorContext):
        """Generator uses appropriate file strategies."""
        from prisme.spec.stack import FileStrategy

        generator = AuthGenerator(generator_context_with_auth)
        files = generator.generate_files()

        # Services should be ALWAYS_OVERWRITE (pure generated)
        token_service = next(f for f in files if "token_service.py" in str(f.path))
        assert token_service.strategy == FileStrategy.ALWAYS_OVERWRITE

        password_service = next(f for f in files if "password_service.py" in str(f.path))
        assert password_service.strategy == FileStrategy.ALWAYS_OVERWRITE

        # Routes should be GENERATE_ONCE (allow customization)
        auth_routes = next(f for f in files if "rest" in str(f.path) and "auth.py" in str(f.path))
        assert auth_routes.strategy == FileStrategy.GENERATE_ONCE

        # Middleware should be ALWAYS_OVERWRITE
        middleware = next(
            f for f in files if "middleware" in str(f.path) and "auth.py" in str(f.path)
        )
        assert middleware.strategy == FileStrategy.ALWAYS_OVERWRITE

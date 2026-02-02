"""Tests for admin panel backend generator."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.backend.admin import AdminGenerator
from prisme.spec import (
    AdminPanelConfig,
    AuthConfig,
    FieldSpec,
    FieldType,
    ModelSpec,
    SignupAccessConfig,
    StackSpec,
)
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy


@pytest.fixture
def admin_enabled_spec() -> StackSpec:
    """Stack spec with admin panel enabled."""
    return StackSpec(
        name="test-admin-app",
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
def admin_enabled_project() -> ProjectSpec:
    """Project spec with admin panel enabled."""
    return ProjectSpec(
        name="test-admin-app",
        auth=AuthConfig(
            enabled=True,
            secret_key="${JWT_SECRET}",
            user_model="User",
            username_field="email",
            admin_panel=AdminPanelConfig(enabled=True),
            signup_access=SignupAccessConfig(mode="whitelist"),
        ),
    )


@pytest.fixture
def admin_disabled_spec() -> StackSpec:
    """Stack spec with admin panel disabled."""
    return StackSpec(
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


@pytest.fixture
def admin_disabled_project() -> ProjectSpec:
    """Project spec with admin panel disabled."""
    return ProjectSpec(
        name="test-app",
        auth=AuthConfig(enabled=True, secret_key="${JWT_SECRET}"),
    )


@pytest.fixture
def auth_disabled_spec() -> StackSpec:
    """Stack spec with auth disabled entirely."""
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Post",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
            )
        ],
    )


class TestAdminGenerator:
    """Tests for AdminGenerator."""

    def test_skips_when_admin_panel_disabled(
        self, admin_disabled_spec, admin_disabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_disabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_disabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_skips_when_auth_disabled(self, auth_disabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=auth_disabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generates_correct_file_count(
        self, admin_enabled_spec, admin_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()
        # admin_service, bootstrap_service, whitelist_model, schemas, routes, __init__
        assert len(files) == 6

    def test_generates_correct_paths(self, admin_enabled_spec, admin_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()
        file_paths = [str(f.path) for f in files]

        assert any("admin_service.py" in p for p in file_paths)
        assert any("bootstrap_service.py" in p for p in file_paths)
        assert any("whitelist_model.py" in p for p in file_paths)
        assert any("schemas" in p and "admin.py" in p for p in file_paths)
        assert any("rest" in p and "admin.py" in p for p in file_paths)
        assert any("__init__.py" in p for p in file_paths)

    def test_admin_routes_contain_expected_endpoints(
        self, admin_enabled_spec, admin_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()

        route_file = next(f for f in files if "rest" in str(f.path) and "admin.py" in str(f.path))
        content = route_file.content

        assert 'prefix="/admin"' in content
        assert "admin_list_users" in content
        assert "admin_get_user" in content
        assert "admin_update_user" in content
        assert "admin_delete_user" in content
        assert "admin_promote_user" in content
        assert "admin_demote_user" in content
        assert "admin_list_whitelist" in content
        assert "admin_add_whitelist_rule" in content
        assert "admin_delete_whitelist_rule" in content
        assert "bootstrap_admin" in content

    def test_whitelist_model_has_correct_columns(
        self, admin_enabled_spec, admin_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()

        model_file = next(f for f in files if "whitelist_model.py" in str(f.path))
        content = model_file.content

        assert "rule_type" in content
        assert "value" in content
        assert "created_by" in content
        assert "created_at" in content
        assert "signup_whitelist" in content  # table name

    def test_bootstrap_service_has_token_functions(
        self, admin_enabled_spec, admin_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()

        bootstrap_file = next(f for f in files if "bootstrap_service.py" in str(f.path))
        content = bootstrap_file.content

        assert "generate_bootstrap_token" in content
        assert "hash_bootstrap_token" in content
        assert "is_token_expired" in content

    def test_file_strategies(self, admin_enabled_spec, admin_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()

        # Routes should be GENERATE_ONCE
        route_file = next(f for f in files if "rest" in str(f.path) and "admin.py" in str(f.path))
        assert route_file.strategy == FileStrategy.GENERATE_ONCE

        # Services should be ALWAYS_OVERWRITE
        service_file = next(f for f in files if "admin_service.py" in str(f.path))
        assert service_file.strategy == FileStrategy.ALWAYS_OVERWRITE

        bootstrap_file = next(f for f in files if "bootstrap_service.py" in str(f.path))
        assert bootstrap_file.strategy == FileStrategy.ALWAYS_OVERWRITE

    def test_uses_correct_project_name(self, admin_enabled_spec, admin_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = AdminGenerator(context)
        files = generator.generate_files()

        route_file = next(f for f in files if "rest" in str(f.path) and "admin.py" in str(f.path))
        assert "from test_admin_app." in route_file.content

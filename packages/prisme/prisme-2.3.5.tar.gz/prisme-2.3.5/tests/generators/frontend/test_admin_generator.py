"""Tests for frontend admin panel generator."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.admin import FrontendAdminGenerator
from prisme.spec import (
    AdminPanelConfig,
    AuthConfig,
    FieldSpec,
    FieldType,
    ModelSpec,
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
        ),
    )


@pytest.fixture
def admin_disabled_spec() -> StackSpec:
    """Stack spec with admin panel disabled."""
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Post",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
            )
        ],
    )


class TestFrontendAdminGenerator:
    """Tests for FrontendAdminGenerator."""

    def test_skips_when_disabled(self, admin_disabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_disabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = FrontendAdminGenerator(context)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generates_correct_page_files(
        self, admin_enabled_spec, admin_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = FrontendAdminGenerator(context)
        files = generator.generate_files()

        # adminApi, AdminLayout, AdminDashboard, AdminUsers, AdminUserDetail,
        # AdminWhitelist, BootstrapPage, AdminRoles, AdminPermissions, AdminActivityLog
        assert len(files) == 10

        file_paths = [str(f.path) for f in files]
        assert any("adminApi.ts" in p for p in file_paths)
        assert any("AdminLayout.tsx" in p for p in file_paths)
        assert any("AdminDashboard.tsx" in p for p in file_paths)
        assert any("AdminUsers.tsx" in p for p in file_paths)
        assert any("AdminUserDetail.tsx" in p for p in file_paths)
        assert any("AdminWhitelist.tsx" in p for p in file_paths)
        assert any("BootstrapPage.tsx" in p for p in file_paths)
        assert any("AdminRoles.tsx" in p for p in file_paths)
        assert any("AdminPermissions.tsx" in p for p in file_paths)
        assert any("AdminActivityLog.tsx" in p for p in file_paths)

    def test_admin_api_client_generated(self, admin_enabled_spec, admin_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = FrontendAdminGenerator(context)
        files = generator.generate_files()

        api_file = next(f for f in files if "adminApi.ts" in str(f.path))
        content = api_file.content

        assert "adminApi" in content
        assert "listUsers" in content
        assert "bootstrap" in content
        assert "listWhitelist" in content

    def test_file_strategies(self, admin_enabled_spec, admin_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=admin_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=admin_enabled_project,
        )
        generator = FrontendAdminGenerator(context)
        files = generator.generate_files()

        api_file = next(f for f in files if "adminApi.ts" in str(f.path))
        assert api_file.strategy == FileStrategy.ALWAYS_OVERWRITE

        layout_file = next(f for f in files if "AdminLayout.tsx" in str(f.path))
        assert layout_file.strategy == FileStrategy.ALWAYS_OVERWRITE

        dashboard_file = next(f for f in files if "AdminDashboard.tsx" in str(f.path))
        assert dashboard_file.strategy == FileStrategy.GENERATE_ONCE

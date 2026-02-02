"""Tests for profile pages generator."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.profile import ProfilePagesGenerator
from prisme.spec import AuthConfig, FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy


@pytest.fixture
def auth_enabled_spec() -> StackSpec:
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
                ],
            )
        ],
    )


@pytest.fixture
def auth_enabled_project() -> ProjectSpec:
    return ProjectSpec(
        name="test-app",
        auth=AuthConfig(
            enabled=True,
            secret_key="${JWT_SECRET}",
            user_model="User",
            username_field="email",
        ),
    )


class TestProfilePagesGenerator:
    def test_skips_when_auth_disabled(self, auth_enabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=auth_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = ProfilePagesGenerator(context)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generates_profile_and_settings(
        self, auth_enabled_spec, auth_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=auth_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=auth_enabled_project,
        )
        generator = ProfilePagesGenerator(context)
        files = generator.generate_files()

        assert len(files) == 2
        file_paths = [str(f.path) for f in files]
        assert any("ProfilePage.tsx" in p for p in file_paths)
        assert any("SettingsPage.tsx" in p for p in file_paths)

    def test_all_generate_once(self, auth_enabled_spec, auth_enabled_project, tmp_path):
        context = GeneratorContext(
            domain_spec=auth_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=auth_enabled_project,
        )
        generator = ProfilePagesGenerator(context)
        files = generator.generate_files()

        for f in files:
            assert f.strategy == FileStrategy.GENERATE_ONCE

    def test_settings_includes_password_section(
        self, auth_enabled_spec, auth_enabled_project, tmp_path
    ):
        context = GeneratorContext(
            domain_spec=auth_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=auth_enabled_project,
        )
        generator = ProfilePagesGenerator(context)
        files = generator.generate_files()

        settings = next(f for f in files if "SettingsPage" in str(f.path))
        assert "Change Password" in settings.content

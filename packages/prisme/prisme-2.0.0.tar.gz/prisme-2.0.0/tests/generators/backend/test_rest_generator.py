"""Tests for REST API generator."""

from pathlib import Path

import pytest

from prisme.generators.backend.rest import RESTGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec import AuthConfig, FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.project import ProjectSpec


@pytest.fixture
def basic_spec() -> StackSpec:
    """Stack spec without auth."""
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
def jwt_auth_spec() -> StackSpec:
    """Stack spec with JWT auth enabled."""
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="User",
                fields=[
                    FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                ],
            ),
            ModelSpec(
                name="Post",
                fields=[
                    FieldSpec(name="title", type=FieldType.STRING, required=True),
                ],
            ),
        ],
    )


class TestRESTGeneratorAuthRouter:
    """Tests for auth router inclusion in main router."""

    def test_main_router_excludes_auth_when_disabled(self, basic_spec: StackSpec, tmp_path: Path):
        """Main router should not include auth router when auth is disabled."""
        project = ProjectSpec(name="test-app")
        ctx = GeneratorContext(
            domain_spec=basic_spec, output_dir=tmp_path, dry_run=True, project_spec=project
        )
        generator = RESTGenerator(ctx)
        files = generator.generate_index_files()

        router_file = next(f for f in files if f.path.name == "router.py")
        assert "auth_router" not in router_file.content

    def test_main_router_includes_auth_when_jwt_enabled(
        self, jwt_auth_spec: StackSpec, tmp_path: Path
    ):
        """Main router should include auth router when JWT auth is enabled."""
        project = ProjectSpec(
            name="test-app",
            auth=AuthConfig(
                enabled=True,
                preset="jwt",
                user_model="User",
                username_field="email",
            ),
        )
        ctx = GeneratorContext(
            domain_spec=jwt_auth_spec, output_dir=tmp_path, dry_run=True, project_spec=project
        )
        generator = RESTGenerator(ctx)
        files = generator.generate_index_files()

        router_file = next(f for f in files if f.path.name == "router.py")
        assert "from .auth import router as auth_router" in router_file.content
        assert "router.include_router(auth_router)" in router_file.content

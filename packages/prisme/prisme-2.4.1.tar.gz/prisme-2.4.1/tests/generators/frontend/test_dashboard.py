"""Tests for dashboard generator."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.dashboard import DashboardGenerator
from prisme.spec import FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy


@pytest.fixture
def basic_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Post",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
            ),
            ModelSpec(
                name="User",
                fields=[FieldSpec(name="email", type=FieldType.STRING, required=True)],
            ),
        ],
    )


class TestDashboardGenerator:
    def test_generates_dashboard(self, basic_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=basic_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = DashboardGenerator(context)
        files = generator.generate_files()

        assert len(files) == 1
        assert "DashboardPage.tsx" in str(files[0].path)
        assert files[0].strategy == FileStrategy.GENERATE_ONCE

    def test_dashboard_references_models(self, basic_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=basic_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = DashboardGenerator(context)
        files = generator.generate_files()

        content = files[0].content
        assert "Posts" in content
        assert "Users" in content

    def test_skips_when_no_models(self, tmp_path):
        spec = StackSpec(name="empty-app", models=[])
        context = GeneratorContext(
            domain_spec=spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="empty-app"),
        )
        generator = DashboardGenerator(context)
        files = generator.generate_files()
        assert files == []

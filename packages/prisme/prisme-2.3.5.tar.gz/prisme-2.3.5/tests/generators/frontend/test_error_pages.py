"""Tests for error pages generator."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.error_pages import ErrorPagesGenerator
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
            )
        ],
    )


class TestErrorPagesGenerator:
    def test_generates_three_error_pages(self, basic_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=basic_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = ErrorPagesGenerator(context)
        files = generator.generate_files()

        assert len(files) == 3
        file_paths = [str(f.path) for f in files]
        assert any("NotFoundPage.tsx" in p for p in file_paths)
        assert any("ForbiddenPage.tsx" in p for p in file_paths)
        assert any("ServerErrorPage.tsx" in p for p in file_paths)

    def test_all_generate_once(self, basic_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=basic_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = ErrorPagesGenerator(context)
        files = generator.generate_files()

        for f in files:
            assert f.strategy == FileStrategy.GENERATE_ONCE

    def test_content_has_correct_elements(self, basic_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=basic_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = ErrorPagesGenerator(context)
        files = generator.generate_files()

        not_found = next(f for f in files if "NotFoundPage" in str(f.path))
        assert "404" in not_found.content
        assert "Page not found" in not_found.content

        forbidden = next(f for f in files if "ForbiddenPage" in str(f.path))
        assert "403" in forbidden.content

        server_error = next(f for f in files if "ServerErrorPage" in str(f.path))
        assert "500" in server_error.content

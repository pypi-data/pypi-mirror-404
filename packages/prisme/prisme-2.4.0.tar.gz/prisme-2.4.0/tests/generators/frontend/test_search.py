"""Tests for search page generator and inline filtering."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.search import SearchPageGenerator
from prisme.spec import FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy


@pytest.fixture
def multi_model_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Post",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
            ),
            ModelSpec(
                name="Comment",
                fields=[FieldSpec(name="body", type=FieldType.TEXT, required=True)],
            ),
        ],
    )


class TestSearchPageGenerator:
    def test_generates_search_page(self, multi_model_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=multi_model_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = SearchPageGenerator(context)
        files = generator.generate_files()

        assert len(files) == 1
        assert "SearchPage.tsx" in str(files[0].path)
        assert files[0].strategy == FileStrategy.GENERATE_ONCE

    def test_search_page_references_all_models(self, multi_model_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=multi_model_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = SearchPageGenerator(context)
        files = generator.generate_files()

        content = files[0].content
        assert "usePostList" in content
        assert "useCommentList" in content

    def test_skips_when_no_models(self, tmp_path):
        spec = StackSpec(name="empty-app", models=[])
        context = GeneratorContext(
            domain_spec=spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="empty-app"),
        )
        generator = SearchPageGenerator(context)
        files = generator.generate_files()
        assert files == []

"""Tests for bulk operations UI on list pages."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.pages import PagesGenerator
from prisme.spec import FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.overrides import FrontendOverrides
from prisme.spec.project import ProjectSpec


@pytest.fixture
def bulk_enabled_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Task",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
                frontend_overrides=FrontendOverrides(enable_bulk_actions=True),
            ),
        ],
    )


@pytest.fixture
def bulk_disabled_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Task",
                fields=[FieldSpec(name="title", type=FieldType.STRING, required=True)],
            ),
        ],
    )


class TestBulkOperations:
    def test_bulk_actions_in_list_page_when_enabled(self, bulk_enabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=bulk_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = PagesGenerator(context)
        files = generator.generate_files()

        list_file = next(f for f in files if "index.tsx" in str(f.path))
        assert "selectedIds" in list_file.content
        assert "toggleSelection" in list_file.content

    def test_no_bulk_actions_when_disabled(self, bulk_disabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=bulk_disabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = PagesGenerator(context)
        files = generator.generate_files()

        list_file = next(f for f in files if "index.tsx" in str(f.path))
        assert "selectedIds" not in list_file.content

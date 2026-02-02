"""Tests for import page generation."""

import pytest

from prisme.generators import GeneratorContext
from prisme.generators.frontend.pages import PagesGenerator
from prisme.spec import FieldSpec, FieldType, ModelSpec, StackSpec
from prisme.spec.overrides import FrontendOverrides
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy


@pytest.fixture
def import_enabled_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Product",
                fields=[FieldSpec(name="name", type=FieldType.STRING, required=True)],
                frontend_overrides=FrontendOverrides(enable_import=True),
            ),
        ],
    )


@pytest.fixture
def import_disabled_spec() -> StackSpec:
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="Product",
                fields=[FieldSpec(name="name", type=FieldType.STRING, required=True)],
            ),
        ],
    )


class TestImportPage:
    def test_generates_import_page_when_enabled(self, import_enabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=import_enabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = PagesGenerator(context)
        files = generator.generate_files()

        import_files = [f for f in files if "import.tsx" in str(f.path)]
        assert len(import_files) == 1
        assert import_files[0].strategy == FileStrategy.GENERATE_ONCE
        assert "Import" in import_files[0].content

    def test_no_import_page_when_disabled(self, import_disabled_spec, tmp_path):
        context = GeneratorContext(
            domain_spec=import_disabled_spec,
            output_dir=tmp_path,
            dry_run=True,
            project_spec=ProjectSpec(name="test-app"),
        )
        generator = PagesGenerator(context)
        files = generator.generate_files()

        import_files = [f for f in files if "import.tsx" in str(f.path)]
        assert len(import_files) == 0

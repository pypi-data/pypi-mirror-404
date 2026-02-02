"""Tests for the headless UI generator.

Tests for:
- Composable hook generation (usePagination, useSelection, etc.)
- UI state hook generation (useModal, useToast, etc.)
- Utility generation (transform, export)
- Index file generation
- File strategies
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.headless import HeadlessGenerator
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import FileStrategy, StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def basic_model() -> ModelSpec:
    """Create a basic model for testing."""
    return ModelSpec(
        name="Customer",
        description="Customer entity",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="email", type=FieldType.STRING, required=True),
            FieldSpec(name="age", type=FieldType.INTEGER, required=False),
        ],
    )


@pytest.fixture
def stack_spec(basic_model: ModelSpec) -> StackSpec:
    """Create a stack spec with a model."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project",
        models=[basic_model],
    )


@pytest.fixture
def generator_context(stack_spec: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create a generator context."""
    return GeneratorContext(
        domain_spec=stack_spec,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-project"),
    )


@pytest.fixture
def headless_generator(generator_context: GeneratorContext) -> HeadlessGenerator:
    """Create a headless generator."""
    return HeadlessGenerator(generator_context)


class TestHeadlessGeneratorComposables:
    """Tests for composable hook generation."""

    def test_generates_use_pagination(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces usePagination.ts file."""
        files = headless_generator.generate_files()
        pagination_file = next((f for f in files if "usePagination.ts" in str(f.path)), None)

        assert pagination_file is not None
        assert pagination_file.path.name == "usePagination.ts"
        assert "composables" in str(pagination_file.path)

    def test_generates_use_selection(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useSelection.ts file."""
        files = headless_generator.generate_files()
        selection_file = next((f for f in files if "useSelection.ts" in str(f.path)), None)

        assert selection_file is not None
        assert selection_file.path.name == "useSelection.ts"
        assert "composables" in str(selection_file.path)

    def test_generates_use_sorting(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useSorting.ts file."""
        files = headless_generator.generate_files()
        sorting_file = next((f for f in files if "useSorting.ts" in str(f.path)), None)

        assert sorting_file is not None
        assert sorting_file.path.name == "useSorting.ts"
        assert "composables" in str(sorting_file.path)

    def test_generates_use_filtering(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useFiltering.ts file."""
        files = headless_generator.generate_files()
        filtering_file = next((f for f in files if "useFiltering.ts" in str(f.path)), None)

        assert filtering_file is not None
        assert filtering_file.path.name == "useFiltering.ts"
        assert "composables" in str(filtering_file.path)

    def test_generates_use_search(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useSearch.ts file."""
        files = headless_generator.generate_files()
        search_file = next((f for f in files if "useSearch.ts" in str(f.path)), None)

        assert search_file is not None
        assert search_file.path.name == "useSearch.ts"
        assert "composables" in str(search_file.path)

    def test_generates_composables_index(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces composables/index.ts file."""
        files = headless_generator.generate_files()
        index_file = next(
            (f for f in files if "composables" in str(f.path) and f.path.name == "index.ts"),
            None,
        )

        assert index_file is not None
        assert "composables" in str(index_file.path)


class TestHeadlessGeneratorUIState:
    """Tests for UI state hook generation."""

    def test_generates_use_modal(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useModal.ts file."""
        files = headless_generator.generate_files()
        modal_file = next((f for f in files if "useModal.ts" in str(f.path)), None)

        assert modal_file is not None
        assert modal_file.path.name == "useModal.ts"
        assert "/ui/" in str(modal_file.path)

    def test_generates_use_confirmation(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useConfirmation.tsx file."""
        files = headless_generator.generate_files()
        confirmation_file = next((f for f in files if "useConfirmation.tsx" in str(f.path)), None)

        assert confirmation_file is not None
        assert confirmation_file.path.name == "useConfirmation.tsx"
        assert "/ui/" in str(confirmation_file.path)

    def test_generates_use_toast(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useToast.tsx file."""
        files = headless_generator.generate_files()
        toast_file = next((f for f in files if "useToast.tsx" in str(f.path)), None)

        assert toast_file is not None
        assert toast_file.path.name == "useToast.tsx"
        assert "/ui/" in str(toast_file.path)

    def test_generates_use_drawer(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces useDrawer.ts file."""
        files = headless_generator.generate_files()
        drawer_file = next((f for f in files if "useDrawer.ts" in str(f.path)), None)

        assert drawer_file is not None
        assert drawer_file.path.name == "useDrawer.ts"
        assert "/ui/" in str(drawer_file.path)

    def test_generates_ui_index(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces ui/index.ts file."""
        files = headless_generator.generate_files()
        index_file = next(
            (f for f in files if "/ui/" in str(f.path) and f.path.name == "index.ts"),
            None,
        )

        assert index_file is not None


class TestHeadlessGeneratorUtils:
    """Tests for utility generation."""

    def test_generates_transform(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces transform.ts file."""
        files = headless_generator.generate_files()
        transform_file = next((f for f in files if "transform.ts" in str(f.path)), None)

        assert transform_file is not None
        assert transform_file.path.name == "transform.ts"
        assert "/utils/" in str(transform_file.path)

    def test_generates_export(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces export.ts file."""
        files = headless_generator.generate_files()
        export_file = next(
            (f for f in files if "/utils/" in str(f.path) and "export.ts" in str(f.path)),
            None,
        )

        assert export_file is not None
        assert export_file.path.name == "export.ts"

    def test_generates_utils_index(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces utils/index.ts file."""
        files = headless_generator.generate_files()
        index_file = next(
            (f for f in files if "/utils/" in str(f.path) and f.path.name == "index.ts"),
            None,
        )

        assert index_file is not None


class TestHeadlessGeneratorTypes:
    """Tests for type generation."""

    def test_generates_types(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces types.ts file."""
        files = headless_generator.generate_files()
        types_file = next(
            (f for f in files if f.path.name == "types.ts" and "headless" in str(f.path)),
            None,
        )

        assert types_file is not None
        assert "headless" in str(types_file.path)


class TestHeadlessGeneratorMainIndex:
    """Tests for main index file."""

    def test_generates_main_index(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces main index.ts file."""
        files = headless_generator.generate_files()
        # Main index is directly in headless folder
        index_file = next(
            (
                f
                for f in files
                if f.path.name == "index.ts" and str(f.path).endswith("headless/index.ts")
            ),
            None,
        )

        assert index_file is not None


class TestHeadlessGeneratorContent:
    """Tests for generated file content."""

    def test_pagination_has_state_and_actions(self, headless_generator: HeadlessGenerator) -> None:
        """usePagination.ts exports state and actions."""
        files = headless_generator.generate_files()
        pagination_file = next(f for f in files if "usePagination.ts" in str(f.path))

        assert "usePagination" in pagination_file.content
        assert "setPage" in pagination_file.content
        assert "nextPage" in pagination_file.content
        assert "previousPage" in pagination_file.content
        assert "pageSize" in pagination_file.content

    def test_selection_has_generic_type(self, headless_generator: HeadlessGenerator) -> None:
        """useSelection.ts uses generic type parameter."""
        files = headless_generator.generate_files()
        selection_file = next(f for f in files if "useSelection.ts" in str(f.path))

        assert "useSelection<T>" in selection_file.content
        assert "select" in selection_file.content
        assert "deselect" in selection_file.content
        assert "toggle" in selection_file.content
        assert "selectAll" in selection_file.content

    def test_confirmation_has_provider(self, headless_generator: HeadlessGenerator) -> None:
        """useConfirmation.tsx exports ConfirmationProvider."""
        files = headless_generator.generate_files()
        confirmation_file = next(f for f in files if "useConfirmation.tsx" in str(f.path))

        assert "ConfirmationProvider" in confirmation_file.content
        assert "useConfirmation" in confirmation_file.content
        assert "confirm" in confirmation_file.content

    def test_toast_has_provider(self, headless_generator: HeadlessGenerator) -> None:
        """useToast.tsx exports ToastProvider."""
        files = headless_generator.generate_files()
        toast_file = next(f for f in files if "useToast.tsx" in str(f.path))

        assert "ToastProvider" in toast_file.content
        assert "useToast" in toast_file.content
        assert "success" in toast_file.content
        assert "error" in toast_file.content

    def test_transform_has_filter_sort_search(self, headless_generator: HeadlessGenerator) -> None:
        """transform.ts has filter, sort, and search utilities."""
        files = headless_generator.generate_files()
        transform_file = next(f for f in files if "transform.ts" in str(f.path))

        assert "filterData" in transform_file.content
        assert "sortData" in transform_file.content
        assert "searchData" in transform_file.content
        assert "transformData" in transform_file.content

    def test_export_has_csv_and_json(self, headless_generator: HeadlessGenerator) -> None:
        """export.ts has CSV and JSON export utilities."""
        files = headless_generator.generate_files()
        export_file = next(
            f for f in files if "/utils/" in str(f.path) and "export.ts" in str(f.path)
        )

        assert "exportToCSV" in export_file.content
        assert "exportToJSON" in export_file.content
        assert "exportData" in export_file.content

    def test_types_has_all_interfaces(self, headless_generator: HeadlessGenerator) -> None:
        """types.ts has all required interfaces."""
        files = headless_generator.generate_files()
        types_file = next(
            f for f in files if f.path.name == "types.ts" and "headless" in str(f.path)
        )

        # Pagination types
        assert "PaginationOptions" in types_file.content
        assert "PaginationState" in types_file.content
        assert "PaginationActions" in types_file.content

        # Selection types
        assert "SelectionOptions" in types_file.content
        assert "SelectionState" in types_file.content
        assert "SelectionActions" in types_file.content

        # Sorting types
        assert "SortingOptions" in types_file.content
        assert "SortDirection" in types_file.content

        # Modal types
        assert "ModalOptions" in types_file.content
        assert "ModalState" in types_file.content

        # Toast types
        assert "ToastType" in types_file.content
        assert "ToastEntry" in types_file.content

    def test_main_index_exports_all_hooks(self, headless_generator: HeadlessGenerator) -> None:
        """Main index.ts exports all hooks and types."""
        files = headless_generator.generate_files()
        index_file = next(
            f
            for f in files
            if f.path.name == "index.ts" and str(f.path).endswith("headless/index.ts")
        )

        # Composables
        assert "usePagination" in index_file.content
        assert "useSelection" in index_file.content
        assert "useSorting" in index_file.content
        assert "useFiltering" in index_file.content
        assert "useSearch" in index_file.content

        # UI State
        assert "useModal" in index_file.content
        assert "useConfirmation" in index_file.content
        assert "useToast" in index_file.content
        assert "useDrawer" in index_file.content

        # Providers
        assert "ToastProvider" in index_file.content
        assert "ConfirmationProvider" in index_file.content


class TestHeadlessGeneratorStrategy:
    """Tests for file generation strategy."""

    def test_all_files_use_always_overwrite(self, headless_generator: HeadlessGenerator) -> None:
        """All headless files use ALWAYS_OVERWRITE strategy (generated code)."""
        files = headless_generator.generate_files()

        for file in files:
            assert file.strategy == FileStrategy.ALWAYS_OVERWRITE, (
                f"Expected ALWAYS_OVERWRITE for {file.path}, got {file.strategy}"
            )


class TestHeadlessGeneratorFileCount:
    """Tests for generated file count."""

    def test_generates_expected_file_count(self, headless_generator: HeadlessGenerator) -> None:
        """Generator produces expected number of files."""
        files = headless_generator.generate_files()

        # Expected files:
        # - types.ts (1)
        # - composables: 5 hooks + index (6)
        # - ui: 4 hooks + index (5)
        # - utils: 2 files + index (3)
        # - main index (1)
        # Total: 16
        assert len(files) == 16

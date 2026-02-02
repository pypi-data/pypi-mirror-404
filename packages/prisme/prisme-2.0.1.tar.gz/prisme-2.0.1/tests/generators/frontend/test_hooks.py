"""Tests for the hooks generator.

Tests for:
- Data hook generation (useModel, useModelList, useModelMutations)
- Form state hook generation (useModelFormState)
- Table state hook generation (useModelTableState)
- Index file generation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.hooks import HooksGenerator
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
        timestamps=True,
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="email", type=FieldType.STRING, required=True),
            FieldSpec(name="age", type=FieldType.INTEGER, required=False),
            FieldSpec(name="notes", type=FieldType.TEXT, required=False),
        ],
    )


@pytest.fixture
def model_with_form_and_table(basic_model: ModelSpec) -> ModelSpec:
    """Create a model with form and table enabled."""
    # Frontend exposure is enabled by default with form and table generation
    return basic_model


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
def hooks_generator(generator_context: GeneratorContext) -> HooksGenerator:
    """Create a hooks generator."""
    return HooksGenerator(generator_context)


class TestHooksGeneratorDataHooks:
    """Tests for data hook generation."""

    def test_generates_data_hooks(self, hooks_generator: HooksGenerator) -> None:
        """Generator produces useModel.ts file."""
        files = hooks_generator.generate_files()
        hooks_file = next((f for f in files if f.path.name == "useCustomer.ts"), None)

        assert hooks_file is not None

    def test_data_hooks_have_query_and_mutations(self, hooks_generator: HooksGenerator) -> None:
        """Data hooks export query and mutation functions."""
        files = hooks_generator.generate_files()
        hooks_file = next(f for f in files if f.path.name == "useCustomer.ts")

        assert "useCustomer" in hooks_file.content
        assert "useCustomerList" in hooks_file.content
        assert "useCustomerMutations" in hooks_file.content


class TestHooksGeneratorFormState:
    """Tests for form state hook generation."""

    def test_generates_form_state_hook(self, hooks_generator: HooksGenerator) -> None:
        """Generator produces useModelFormState.ts file."""
        files = hooks_generator.generate_files()
        form_state_file = next((f for f in files if f.path.name == "useCustomerFormState.ts"), None)

        assert form_state_file is not None

    def test_form_state_has_typed_values(self, hooks_generator: HooksGenerator) -> None:
        """Form state hook has typed values."""
        files = hooks_generator.generate_files()
        form_state_file = next(f for f in files if f.path.name == "useCustomerFormState.ts")

        assert "CustomerFormValues" in form_state_file.content
        assert "CustomerFormErrors" in form_state_file.content
        assert "CustomerFormTouched" in form_state_file.content

    def test_form_state_has_actions(self, hooks_generator: HooksGenerator) -> None:
        """Form state hook has form actions."""
        files = hooks_generator.generate_files()
        form_state_file = next(f for f in files if f.path.name == "useCustomerFormState.ts")

        assert "setValue" in form_state_file.content
        assert "setValues" in form_state_file.content
        assert "setTouched" in form_state_file.content
        assert "handleSubmit" in form_state_file.content
        assert "reset" in form_state_file.content

    def test_form_state_has_validation(self, hooks_generator: HooksGenerator) -> None:
        """Form state hook has validation for required fields."""
        files = hooks_generator.generate_files()
        form_state_file = next(f for f in files if f.path.name == "useCustomerFormState.ts")

        # Should have validation for required name field
        assert (
            "name is required" in form_state_file.content.lower()
            or "Name is required" in form_state_file.content
        )

    def test_form_state_uses_always_overwrite(self, hooks_generator: HooksGenerator) -> None:
        """Form state hook uses ALWAYS_OVERWRITE strategy."""
        files = hooks_generator.generate_files()
        form_state_file = next(f for f in files if f.path.name == "useCustomerFormState.ts")

        assert form_state_file.strategy == FileStrategy.ALWAYS_OVERWRITE


class TestHooksGeneratorTableState:
    """Tests for table state hook generation."""

    def test_generates_table_state_hook(self, hooks_generator: HooksGenerator) -> None:
        """Generator produces useModelTableState.ts file."""
        files = hooks_generator.generate_files()
        table_state_file = next(
            (f for f in files if f.path.name == "useCustomerTableState.ts"), None
        )

        assert table_state_file is not None

    def test_table_state_composes_primitives(self, hooks_generator: HooksGenerator) -> None:
        """Table state hook composes headless primitives."""
        files = hooks_generator.generate_files()
        table_state_file = next(f for f in files if f.path.name == "useCustomerTableState.ts")

        assert "usePagination" in table_state_file.content
        assert "useSelection" in table_state_file.content
        assert "useSorting" in table_state_file.content
        assert "useSearch" in table_state_file.content

    def test_table_state_has_data_fetching(self, hooks_generator: HooksGenerator) -> None:
        """Table state hook integrates with data hooks."""
        files = hooks_generator.generate_files()
        table_state_file = next(f for f in files if f.path.name == "useCustomerTableState.ts")

        assert "useCustomerList" in table_state_file.content
        assert "useCustomerMutations" in table_state_file.content

    def test_table_state_has_actions(self, hooks_generator: HooksGenerator) -> None:
        """Table state hook has table actions."""
        files = hooks_generator.generate_files()
        table_state_file = next(f for f in files if f.path.name == "useCustomerTableState.ts")

        assert "refetch" in table_state_file.content
        assert "deleteItem" in table_state_file.content
        assert "deleteSelected" in table_state_file.content

    def test_table_state_has_sort_fields_type(self, hooks_generator: HooksGenerator) -> None:
        """Table state hook has typed sort fields."""
        files = hooks_generator.generate_files()
        table_state_file = next(f for f in files if f.path.name == "useCustomerTableState.ts")

        assert "CustomerSortField" in table_state_file.content

    def test_table_state_uses_always_overwrite(self, hooks_generator: HooksGenerator) -> None:
        """Table state hook uses ALWAYS_OVERWRITE strategy."""
        files = hooks_generator.generate_files()
        table_state_file = next(f for f in files if f.path.name == "useCustomerTableState.ts")

        assert table_state_file.strategy == FileStrategy.ALWAYS_OVERWRITE


class TestHooksGeneratorIndex:
    """Tests for index file generation."""

    def test_generates_index(self, hooks_generator: HooksGenerator) -> None:
        """Generator produces index.ts file."""
        files = hooks_generator.generate_files()
        index_file = next((f for f in files if f.path.name == "index.ts"), None)

        assert index_file is not None

    def test_index_exports_all_hooks(self, hooks_generator: HooksGenerator) -> None:
        """Index file exports all generated hooks."""
        files = hooks_generator.generate_files()
        index_file = next(f for f in files if f.path.name == "index.ts")

        # Data hooks
        assert "useCustomer" in index_file.content

        # Form state hooks
        assert "useCustomerFormState" in index_file.content

        # Table state hooks
        assert "useCustomerTableState" in index_file.content

    def test_index_uses_always_overwrite(self, hooks_generator: HooksGenerator) -> None:
        """Index file uses ALWAYS_OVERWRITE strategy."""
        files = hooks_generator.generate_files()
        index_file = next(f for f in files if f.path.name == "index.ts")

        assert index_file.strategy == FileStrategy.ALWAYS_OVERWRITE


class TestHooksGeneratorHelperMethods:
    """Tests for helper methods."""

    def test_build_form_fields(self, hooks_generator: HooksGenerator) -> None:
        """Helper builds form field specs correctly."""
        model = hooks_generator.spec.models[0]
        fields = hooks_generator._build_form_fields(model)

        # Should have name, email, age, notes (4 fields)
        assert len(fields) == 4

        # Check name field
        name_field = next(f for f in fields if f["name"] == "name")
        assert name_field["camel_name"] == "name"
        assert name_field["type"] == "string"
        assert name_field["required"] is True

        # Check age field (optional)
        age_field = next(f for f in fields if f["name"] == "age")
        assert age_field["required"] is False

    def test_get_sortable_fields(self, hooks_generator: HooksGenerator) -> None:
        """Helper returns sortable fields."""
        model = hooks_generator.spec.models[0]
        sortable = hooks_generator._get_sortable_fields(model)

        # Should include string fields (name, email), integer (age), text (notes)
        # Plus timestamps (createdAt, updatedAt) since model has timestamps=True
        assert "name" in sortable
        assert "email" in sortable
        assert "age" in sortable
        assert "notes" in sortable
        assert "createdAt" in sortable
        assert "updatedAt" in sortable

    def test_get_search_fields(self, hooks_generator: HooksGenerator) -> None:
        """Helper returns searchable fields."""
        model = hooks_generator.spec.models[0]
        searchable = hooks_generator._get_search_fields(model)

        # Should include string fields (name, email) and text field (notes)
        assert "name" in searchable
        assert "email" in searchable
        assert "notes" in searchable

        # Should not include integer fields
        assert "age" not in searchable

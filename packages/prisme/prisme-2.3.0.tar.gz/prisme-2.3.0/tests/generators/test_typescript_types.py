"""Tests for TypeScript type generation correctness.

These tests ensure TypeScript types are generated correctly,
preventing common issues like duplicate identifiers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.base import GeneratorContext
from prisme.generators.frontend.types import TypeScriptGenerator
from prisme.generators.testing.frontend import FrontendTestGenerator
from prisme.spec.fields import FieldSpec, FieldType, FilterOperator
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def model_with_between_filter() -> ModelSpec:
    """Create a model with BETWEEN filter operator."""
    return ModelSpec(
        name="StockPrice",
        timestamps=False,  # No timestamps to test conditional generation
        fields=[
            FieldSpec(name="symbol", type=FieldType.STRING, required=True),
            FieldSpec(
                name="price",
                type=FieldType.FLOAT,
                required=True,
                filterable=True,
                filter_operators=[
                    FilterOperator.EQ,
                    FilterOperator.GT,
                    FilterOperator.LT,
                    FilterOperator.BETWEEN,
                ],
            ),
            FieldSpec(
                name="trade_date",
                type=FieldType.DATE,
                required=True,
                filterable=True,
                filter_operators=[
                    FilterOperator.EQ,
                    FilterOperator.GT,
                    FilterOperator.LT,
                    FilterOperator.BETWEEN,
                ],
            ),
        ],
    )


@pytest.fixture
def model_with_json_fields() -> ModelSpec:
    """Create a model with various JSON field types."""
    return ModelSpec(
        name="Document",
        timestamps=True,
        fields=[
            FieldSpec(name="title", type=FieldType.STRING, required=True),
            FieldSpec(
                name="tags",
                type=FieldType.JSON,
                json_item_type="str",
                description="List of string tags",
            ),
            FieldSpec(
                name="scores",
                type=FieldType.JSON,
                json_item_type="int",
                description="List of integer scores",
            ),
            FieldSpec(
                name="metadata",
                type=FieldType.JSON,
                description="Arbitrary metadata object",
            ),
        ],
    )


@pytest.fixture
def between_filter_context(
    tmp_path: Path,
    model_with_between_filter: ModelSpec,
) -> GeneratorContext:
    """Create generator context for BETWEEN filter tests."""
    spec = StackSpec(
        name="TestProject",
        models=[model_with_between_filter],
    )
    return GeneratorContext(
        domain_spec=spec, output_dir=tmp_path, project_spec=ProjectSpec(name="TestProject")
    )


@pytest.fixture
def json_fields_context(
    tmp_path: Path,
    model_with_json_fields: ModelSpec,
) -> GeneratorContext:
    """Create generator context for JSON field tests."""
    spec = StackSpec(
        name="TestProject",
        models=[model_with_json_fields],
    )
    return GeneratorContext(
        domain_spec=spec, output_dir=tmp_path, project_spec=ProjectSpec(name="TestProject")
    )


class TestBetweenFilterOperator:
    """Tests for BETWEEN filter operator TypeScript generation."""

    def test_between_generates_min_max_fields(
        self, between_filter_context: GeneratorContext
    ) -> None:
        """BETWEEN filter should generate Min/Max fields, not duplicates."""
        generator = TypeScriptGenerator(between_filter_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # Should have Min/Max fields for price
        assert "priceMin?: number;" in content
        assert "priceMax?: number;" in content

        # Should have Min/Max fields for trade_date
        assert "tradeDateMin?: string;" in content
        assert "tradeDateMax?: string;" in content

        # Should NOT have duplicate bare field names in filter interface
        # Count occurrences of "price?:" - should only appear once (for EQ)
        filter_section = content[content.find("StockPriceFilter") :]
        price_eq_count = filter_section.count("price?: number;")
        assert price_eq_count == 1, f"Expected 1 'price?:' but found {price_eq_count}"

    def test_no_duplicate_identifiers(self, between_filter_context: GeneratorContext) -> None:
        """Generated TypeScript should not have duplicate identifiers."""
        generator = TypeScriptGenerator(between_filter_context)
        files = generator.generate_files()

        types_file = next(f for f in files if "generated.ts" in str(f.path))
        content = types_file.content

        # Extract the filter interface
        filter_start = content.find("export interface StockPriceFilter")
        filter_end = content.find("}", filter_start) + 1
        filter_interface = content[filter_start:filter_end]

        # Parse field names from the interface
        lines = filter_interface.split("\n")
        field_names = []
        for line in lines:
            if "?:" in line:
                # Extract field name (before the ?:)
                field_name = line.strip().split("?:")[0].strip()
                field_names.append(field_name)

        # Check for duplicates
        duplicates = [name for name in field_names if field_names.count(name) > 1]
        assert not duplicates, f"Found duplicate identifiers: {set(duplicates)}"


class TestJsonFieldMockValues:
    """Tests for JSON field mock value generation in tests."""

    def test_typed_json_array_mock_values(self, json_fields_context: GeneratorContext) -> None:
        """Typed JSON arrays should generate array mock values."""
        generator = FrontendTestGenerator(json_fields_context)
        files = generator.generate_files()

        component_test = next((f for f in files if "Document.test.tsx" in str(f.path)), None)
        assert component_test is not None

        content = component_test.content

        # String array should generate array mock
        assert "['test']" in content or '["test"]' in content

        # Integer array should generate array mock
        assert "[1, 2, 3]" in content

    def test_untyped_json_object_mock_values(self, json_fields_context: GeneratorContext) -> None:
        """Untyped JSON should generate object mock values."""
        generator = FrontendTestGenerator(json_fields_context)
        files = generator.generate_files()

        component_test = next((f for f in files if "Document.test.tsx" in str(f.path)), None)
        assert component_test is not None

        content = component_test.content

        # Untyped JSON (metadata) should generate object mock
        assert "{ test: 'value' }" in content or '{ "test": "value" }' in content


class TestTimestampsConditional:
    """Tests for conditional timestamp generation."""

    def test_no_timestamps_in_mock_when_disabled(
        self, between_filter_context: GeneratorContext
    ) -> None:
        """Mock data should not include timestamps when model has timestamps=False."""
        generator = FrontendTestGenerator(between_filter_context)
        files = generator.generate_files()

        component_test = next((f for f in files if "StockPrice.test.tsx" in str(f.path)), None)
        assert component_test is not None

        content = component_test.content

        # Should NOT have createdAt/updatedAt in mock data
        # since model has timestamps=False
        mock_section = content[content.find("const mockStockPrice") :]
        mock_end = mock_section.find("};") + 2
        mock_data = mock_section[:mock_end]

        assert "createdAt" not in mock_data
        assert "updatedAt" not in mock_data

    def test_timestamps_in_mock_when_enabled(self, json_fields_context: GeneratorContext) -> None:
        """Mock data should include timestamps when model has timestamps=True."""
        generator = FrontendTestGenerator(json_fields_context)
        files = generator.generate_files()

        component_test = next((f for f in files if "Document.test.tsx" in str(f.path)), None)
        assert component_test is not None

        content = component_test.content

        # Should have createdAt/updatedAt in mock data
        # since model has timestamps=True (default)
        mock_section = content[content.find("const mockDocument") :]
        mock_end = mock_section.find("};") + 2
        mock_data = mock_section[:mock_end]

        assert "createdAt" in mock_data
        assert "updatedAt" in mock_data

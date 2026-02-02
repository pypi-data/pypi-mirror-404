"""Tests for conditional validation feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.schemas import SchemasGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def conditional_model() -> ModelSpec:
    """Create a model with conditional validation."""
    return ModelSpec(
        name="Company",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(
                name="sector",
                type=FieldType.ENUM,
                enum_values=["mining", "tech", "finance"],
                required=True,
            ),
            FieldSpec(
                name="mining_license",
                type=FieldType.STRING,
                required=False,
                conditional_required="sector == mining",
            ),
            FieldSpec(
                name="company_type",
                type=FieldType.STRING,
                required=False,
                conditional_enum={
                    "sector:mining": ["gold_miner", "silver_miner", "diversified"],
                    "sector:tech": ["software", "hardware", "services"],
                },
            ),
        ],
    )


@pytest.fixture
def conditional_stack(conditional_model: ModelSpec) -> StackSpec:
    """Create a stack with conditional model."""
    return StackSpec(
        name="test-conditional",
        version="1.0.0",
        models=[conditional_model],
    )


@pytest.fixture
def conditional_context(conditional_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for conditional tests."""
    return GeneratorContext(
        domain_spec=conditional_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-conditional"),
    )


class TestConditionalFieldSpec:
    """Tests for conditional validation fields in FieldSpec."""

    def test_field_with_conditional_required(self) -> None:
        """FieldSpec accepts conditional_required parameter."""
        field = FieldSpec(
            name="license",
            type=FieldType.STRING,
            conditional_required="type == business",
        )
        assert field.conditional_required == "type == business"

    def test_field_with_conditional_enum(self) -> None:
        """FieldSpec accepts conditional_enum parameter."""
        field = FieldSpec(
            name="subtype",
            type=FieldType.STRING,
            conditional_enum={
                "type:a": ["a1", "a2"],
                "type:b": ["b1", "b2"],
            },
        )
        assert field.conditional_enum == {
            "type:a": ["a1", "a2"],
            "type:b": ["b1", "b2"],
        }

    def test_field_without_conditional(self) -> None:
        """FieldSpec defaults conditional fields to None."""
        field = FieldSpec(
            name="simple",
            type=FieldType.STRING,
        )
        assert field.conditional_required is None
        assert field.conditional_enum is None


class TestConditionalSchemaGeneration:
    """Tests for conditional validation schema generation."""

    def test_generates_validated_schema(self, conditional_context: GeneratorContext) -> None:
        """Generates Validated schema with conditional validators."""
        generator = SchemasGenerator(conditional_context)
        files = generator.generate_files()

        schema = next(f for f in files if "company.py" in str(f.path) and "schemas" in str(f.path))
        content = schema.content

        assert "class CompanyValidated" in content
        assert "model_validator" in content

    def test_conditional_required_validator(self, conditional_context: GeneratorContext) -> None:
        """Generates validator for conditional required fields."""
        generator = SchemasGenerator(conditional_context)
        files = generator.generate_files()

        schema = next(f for f in files if "company.py" in str(f.path) and "schemas" in str(f.path))
        content = schema.content

        assert "validate_conditional_required" in content
        assert "mining_license" in content
        assert "sector" in content
        assert "mining" in content

    def test_conditional_enum_validator(self, conditional_context: GeneratorContext) -> None:
        """Generates validator for conditional enum values."""
        generator = SchemasGenerator(conditional_context)
        files = generator.generate_files()

        schema = next(f for f in files if "company.py" in str(f.path) and "schemas" in str(f.path))
        content = schema.content

        assert "validate_conditional_enums" in content
        assert "company_type" in content
        assert "gold_miner" in content
        assert "software" in content

    def test_imports_include_model_validator(self, conditional_context: GeneratorContext) -> None:
        """Imports include model_validator when conditional validation is used."""
        generator = SchemasGenerator(conditional_context)
        files = generator.generate_files()

        schema = next(f for f in files if "company.py" in str(f.path) and "schemas" in str(f.path))
        content = schema.content

        assert "model_validator" in content
        assert "Self" in content

    def test_no_conditional_no_validated_schema(
        self, conditional_context: GeneratorContext
    ) -> None:
        """Models without conditional validation don't get Validated schema."""
        simple_model = ModelSpec(
            name="Simple",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        )
        stack = StackSpec(
            name="test",
            version="1.0.0",
            models=[simple_model],
        )
        context = GeneratorContext(
            domain_spec=stack,
            output_dir=conditional_context.output_dir,
            dry_run=True,
            project_spec=ProjectSpec(name="test"),
        )

        generator = SchemasGenerator(context)
        files = generator.generate_files()

        schema = next(f for f in files if "simple.py" in str(f.path) and "schemas" in str(f.path))
        content = schema.content

        assert "SimpleValidated" not in content
        assert "model_validator" not in content

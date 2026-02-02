"""Tests for the ModelsGenerator, including DateTime timezone support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.models import ModelsGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def datetime_model() -> ModelSpec:
    """Create a model with a DateTime field."""
    return ModelSpec(
        name="Event",
        fields=[
            FieldSpec(name="name", type=FieldType.STRING, required=True),
            FieldSpec(name="started_at", type=FieldType.DATETIME, required=True),
        ],
    )


@pytest.fixture
def datetime_stack(datetime_model: ModelSpec) -> StackSpec:
    return StackSpec(
        name="test-datetime",
        version="1.0.0",
        models=[datetime_model],
    )


@pytest.fixture
def datetime_context(datetime_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    return GeneratorContext(
        domain_spec=datetime_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-datetime"),
    )


class TestDateTimeTimezone:
    """Issue #56: DateTime columns should include timezone=True."""

    def test_datetime_column_has_timezone(
        self, datetime_context: GeneratorContext, datetime_stack: StackSpec
    ) -> None:
        """DateTime fields should generate DateTime(timezone=True) in mapped_column."""
        generator = ModelsGenerator(datetime_context)
        files = generator.generate_files()

        # Find the Event model file
        event_file = next(f for f in files if "event" in str(f.path))
        assert "DateTime(timezone=True)" in event_file.content

    def test_datetime_column_does_not_use_bare_datetime(
        self, datetime_context: GeneratorContext
    ) -> None:
        """DateTime fields should NOT use bare DateTime without timezone."""
        generator = ModelsGenerator(datetime_context)
        files = generator.generate_files()

        event_file = next(f for f in files if "event" in str(f.path))
        # Should not have bare "DateTime)" without timezone
        # But "DateTime(timezone=True)" is fine
        content = event_file.content
        assert "DateTime(timezone=True)" in content
        # Ensure there's no mapped_column(DateTime) without timezone
        assert "mapped_column(DateTime)" not in content

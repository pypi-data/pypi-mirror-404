"""Tests for temporal/time-series query feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from prisme.generators.backend.services import ServicesGenerator
from prisme.generators.base import GeneratorContext
from prisme.spec.fields import FieldSpec, FieldType
from prisme.spec.model import ModelSpec, TemporalConfig
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def temporal_model() -> ModelSpec:
    """Create a model with temporal configuration."""
    return ModelSpec(
        name="PriceHistory",
        fields=[
            FieldSpec(name="symbol", type=FieldType.STRING, required=True),
            FieldSpec(name="price", type=FieldType.DECIMAL, required=True),
            FieldSpec(name="as_of_date", type=FieldType.DATETIME, required=True),
        ],
        temporal=TemporalConfig(
            timestamp_field="as_of_date",
            group_by_field="symbol",
            generate_latest_query=True,
            generate_history_query=True,
        ),
    )


@pytest.fixture
def simple_temporal_model() -> ModelSpec:
    """Create a model with temporal but no group_by."""
    return ModelSpec(
        name="SystemStatus",
        fields=[
            FieldSpec(name="status", type=FieldType.STRING, required=True),
            FieldSpec(name="recorded_at", type=FieldType.DATETIME, required=True),
        ],
        temporal=TemporalConfig(
            timestamp_field="recorded_at",
            generate_latest_query=True,
            generate_history_query=True,
        ),
    )


@pytest.fixture
def temporal_stack(temporal_model: ModelSpec, simple_temporal_model: ModelSpec) -> StackSpec:
    """Create a stack with temporal models."""
    return StackSpec(
        name="test-temporal",
        version="1.0.0",
        models=[temporal_model, simple_temporal_model],
    )


@pytest.fixture
def temporal_context(temporal_stack: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Create generator context for temporal tests."""
    return GeneratorContext(
        domain_spec=temporal_stack,
        output_dir=tmp_path,
        dry_run=True,
        project_spec=ProjectSpec(name="test-temporal"),
    )


class TestTemporalConfig:
    """Tests for TemporalConfig."""

    def test_temporal_config_creation(self) -> None:
        """TemporalConfig can be created with required fields."""
        config = TemporalConfig(
            timestamp_field="created_at",
        )
        assert config.timestamp_field == "created_at"
        assert config.group_by_field is None
        assert config.generate_latest_query is True
        assert config.generate_history_query is True

    def test_temporal_config_with_group_by(self) -> None:
        """TemporalConfig accepts group_by_field."""
        config = TemporalConfig(
            timestamp_field="as_of_date",
            group_by_field="entity_id",
        )
        assert config.group_by_field == "entity_id"


class TestTemporalModelSpec:
    """Tests for temporal field in ModelSpec."""

    def test_model_with_temporal(self, temporal_model: ModelSpec) -> None:
        """ModelSpec accepts temporal configuration."""
        assert temporal_model.temporal is not None
        assert temporal_model.temporal.timestamp_field == "as_of_date"
        assert temporal_model.temporal.group_by_field == "symbol"

    def test_model_without_temporal(self) -> None:
        """ModelSpec defaults temporal to None."""
        model = ModelSpec(
            name="Simple",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        )
        assert model.temporal is None


class TestTemporalServiceQueries:
    """Tests for temporal query generation in services."""

    def test_generates_get_latest_with_group_by(self, temporal_context: GeneratorContext) -> None:
        """Generates get_latest with group_by logic."""
        generator = ServicesGenerator(temporal_context)
        files = generator.generate_files()

        service = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = service.content

        assert "async def get_latest(" in content
        assert "symbol:" in content  # group_by parameter
        assert "max_ts" in content  # subquery alias
        assert "subquery" in content

    def test_generates_get_latest_without_group_by(
        self, temporal_context: GeneratorContext
    ) -> None:
        """Generates simpler get_latest without group_by."""
        generator = ServicesGenerator(temporal_context)
        files = generator.generate_files()

        service = next(
            f
            for f in files
            if "system_status_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = service.content

        assert "async def get_latest(" in content
        assert "order_by" in content
        assert "desc()" in content
        assert "limit(1)" in content

    def test_generates_get_history(self, temporal_context: GeneratorContext) -> None:
        """Generates get_history query method."""
        generator = ServicesGenerator(temporal_context)
        files = generator.generate_files()

        service = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = service.content

        assert "async def get_history(" in content
        assert "start_date:" in content
        assert "end_date:" in content
        assert "as_of_date" in content

    def test_get_history_has_pagination(self, temporal_context: GeneratorContext) -> None:
        """get_history includes pagination parameters."""
        generator = ServicesGenerator(temporal_context)
        files = generator.generate_files()

        service = next(
            f
            for f in files
            if "price_history_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = service.content

        assert "skip: int = 0" in content
        assert "limit: int = 100" in content

    def test_no_temporal_no_queries(self, temporal_context: GeneratorContext) -> None:
        """Models without temporal don't get temporal queries."""
        # Create a context with a non-temporal model
        non_temporal = ModelSpec(
            name="Regular",
            fields=[
                FieldSpec(name="name", type=FieldType.STRING, required=True),
            ],
        )
        stack = StackSpec(
            name="test",
            version="1.0.0",
            models=[non_temporal],
        )
        context = GeneratorContext(
            domain_spec=stack,
            output_dir=temporal_context.output_dir,
            dry_run=True,
            project_spec=ProjectSpec(name="test"),
        )

        generator = ServicesGenerator(context)
        files = generator.generate_files()

        service = next(
            f for f in files if "regular_base.py" in str(f.path) and "_generated" in str(f.path)
        )
        content = service.content

        assert "get_latest" not in content
        assert "get_history" not in content

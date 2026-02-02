"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from prisme.spec.fields import FieldSpec, FieldType, FilterOperator
from prisme.spec.model import ModelSpec, RelationshipSpec
from prisme.spec.project import ProjectSpec
from prisme.spec.stack import StackSpec


@pytest.fixture
def sample_field_spec() -> FieldSpec:
    """Create a sample FieldSpec for testing."""
    return FieldSpec(
        name="email",
        type=FieldType.STRING,
        required=True,
        unique=True,
        max_length=255,
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
        display_name="Email Address",
        ui_widget="email",
    )


@pytest.fixture
def sample_model_spec(sample_field_spec: FieldSpec) -> ModelSpec:
    """Create a sample ModelSpec for testing."""
    return ModelSpec(
        name="Customer",
        description="Customer entity",
        soft_delete=True,
        timestamps=True,
        fields=[
            FieldSpec(
                name="name",
                type=FieldType.STRING,
                required=True,
                max_length=255,
            ),
            sample_field_spec,
            FieldSpec(
                name="status",
                type=FieldType.ENUM,
                enum_values=["active", "inactive", "prospect"],
                default="prospect",
            ),
        ],
        relationships=[
            RelationshipSpec(
                name="orders",
                target_model="Order",
                type="one_to_many",
                back_populates="customer",
            ),
        ],
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--run-docker",
        action="store_true",
        default=False,
        help="Run tests that require Docker",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip Docker tests if --run-docker not specified."""
    if config.getoption("--run-docker", default=False):
        return

    skip_docker = pytest.mark.skip(reason="Need --run-docker option to run")
    for item in items:
        if "docker" in item.keywords:
            item.add_marker(skip_docker)


@pytest.fixture
def sample_stack_spec(sample_model_spec: ModelSpec) -> StackSpec:
    """Create a sample StackSpec for testing."""
    return StackSpec(
        name="test-project",
        version="1.0.0",
        description="Test project for unit tests",
        models=[sample_model_spec],
    )


@pytest.fixture
def sample_project_spec() -> ProjectSpec:
    """Create a sample ProjectSpec for testing."""
    return ProjectSpec(name="test-project")

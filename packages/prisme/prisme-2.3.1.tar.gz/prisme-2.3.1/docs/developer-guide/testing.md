# Testing Guide

Guidelines for running and writing tests for Prisme.

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov

# With HTML coverage report
uv run pytest --cov --cov-report=html
open htmlcov/index.html

# Verbose output
uv run pytest -v

# Very verbose (see print statements)
uv run pytest -vv -s
```

### Running Specific Tests

```bash
# Specific file
uv run pytest tests/spec/test_models.py

# Specific test class
uv run pytest tests/spec/test_models.py::TestModelSpec

# Specific test function
uv run pytest tests/spec/test_models.py::TestModelSpec::test_valid_model

# Pattern matching
uv run pytest -k "model"
uv run pytest -k "model and not slow"
```

### Test Markers

```bash
# Run slow tests (excluded by default)
uv run pytest -m slow

# Run only async tests
uv run pytest -m asyncio

# Run all tests including slow
uv run pytest -m ""
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py           # Shared fixtures
├── spec/                 # Specification tests
│   ├── test_fields.py
│   ├── test_models.py
│   └── test_exposure.py
├── generators/           # Generator tests
│   ├── backend/
│   │   ├── test_models_generator.py
│   │   └── test_services_generator.py
│   └── frontend/
│       └── test_types_generator.py
├── cli/                  # CLI tests
│   └── test_commands.py
└── integration/          # Integration tests
    └── test_full_generation.py
```

### Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<behavior>`

## Writing Tests

### Basic Test Structure

```python
import pytest
from prism.spec import ModelSpec, FieldSpec, FieldType

class TestModelSpec:
    """Tests for ModelSpec."""

    def test_valid_model(self):
        """Test creating a valid model specification."""
        model = ModelSpec(
            name="Customer",
            fields=[
                FieldSpec(name="email", type=FieldType.STRING),
            ],
        )
        assert model.name == "Customer"
        assert len(model.fields) == 1

    def test_model_requires_name(self):
        """Test that model requires a name."""
        with pytest.raises(ValueError):
            ModelSpec(name="", fields=[])
```

### Async Tests

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_service_creates_record(db_session: AsyncSession):
    """Test service creates a database record."""
    service = CustomerService(db_session)

    customer = await service.create({
        "name": "Test",
        "email": "test@example.com",
    })

    assert customer.id is not None
    assert customer.name == "Test"
```

### Parametrized Tests

```python
import pytest
from prism.spec import FieldType

@pytest.mark.parametrize("field_type,expected_python", [
    (FieldType.STRING, "str"),
    (FieldType.INTEGER, "int"),
    (FieldType.BOOLEAN, "bool"),
    (FieldType.DATETIME, "datetime"),
])
def test_field_type_mapping(field_type, expected_python):
    """Test field types map to correct Python types."""
    assert field_type.python_type == expected_python
```

### Using Fixtures

```python
# tests/conftest.py
import pytest
from prism.spec import StackSpec, ModelSpec, FieldSpec, FieldType

@pytest.fixture
def simple_spec():
    """Create a simple test specification."""
    return StackSpec(
        name="test-app",
        models=[
            ModelSpec(
                name="User",
                fields=[
                    FieldSpec(name="email", type=FieldType.STRING, required=True),
                ],
            ),
        ],
    )

@pytest.fixture
def generator_context(simple_spec, tmp_path):
    """Create a generator context for testing."""
    from prism.generators import GeneratorContext

    return GeneratorContext(
        spec=simple_spec,
        backend_path=tmp_path / "backend",
        frontend_path=tmp_path / "frontend",
        package_name="test_app",
    )
```

Using fixtures in tests:

```python
def test_generates_models(generator_context):
    """Test that models are generated correctly."""
    generator = ModelsGenerator(generator_context)
    result = generator.generate()

    assert len(result.files) > 0
    assert "class User" in result.files[0].content
```

## Testing Generators

### Template Output Tests

```python
def test_model_template_output(generator_context):
    """Test model template generates correct code."""
    generator = ModelsGenerator(generator_context)
    result = generator.generate()

    model_file = result.files[0]

    # Check structure
    assert "from sqlalchemy" in model_file.content
    assert "class User(Base):" in model_file.content
    assert "__tablename__" in model_file.content

    # Check fields
    assert "email = Column(" in model_file.content
```

### Snapshot Testing

For complex outputs, use snapshot testing:

```python
def test_generated_schema_matches_snapshot(generator_context, snapshot):
    """Test schema output matches expected snapshot."""
    generator = SchemasGenerator(generator_context)
    result = generator.generate()

    assert result.files[0].content == snapshot
```

## Testing CLI Commands

```python
from click.testing import CliRunner
from prism.cli import main

def test_create_command():
    """Test prism create command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(main, ["create", "test-project"])

        assert result.exit_code == 0
        assert "Created project" in result.output
        assert Path("test-project").exists()

def test_generate_dry_run():
    """Test prism generate --dry-run."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Setup project
        runner.invoke(main, ["create", "test-project"])

        # Run generate with dry-run
        result = runner.invoke(main, ["generate", "--dry-run"], cwd="test-project")

        assert result.exit_code == 0
        assert "Would generate" in result.output
```

## Test Coverage

### Viewing Coverage

```bash
# Terminal report
uv run pytest --cov --cov-report=term-missing

# HTML report
uv run pytest --cov --cov-report=html
open htmlcov/index.html

# XML for CI
uv run pytest --cov --cov-report=xml
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src/prism"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Best Practices

### Do

- Write tests for all new functionality
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests focused and independent
- Use fixtures for shared setup
- Mark slow tests with `@pytest.mark.slow`

### Don't

- Test implementation details (test behavior)
- Use `sleep()` in tests
- Leave print statements in test code
- Skip tests without a reason

## CI Integration

Tests run automatically on every PR:

1. **Lint Job**: ruff check, mypy
2. **Test Job**: pytest with coverage
3. **Coverage Upload**: Results sent to Codecov

All checks must pass for a PR to be merged.

# Development Setup

Complete guide to setting up a Prisme development environment.

## Prerequisites

### Required

- **Python 3.13+**: Check with `python --version`
- **uv**: Install from [astral.sh/uv](https://docs.astral.sh/uv/)
- **Git**: For version control

### Optional

- **Node.js 22+**: For commit hooks and frontend testing
- **Docker**: For integration testing
- **PostgreSQL**: For database tests

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Lasse-numerous/prisme.git
cd prisme
```

### 2. Install Dependencies

```bash
# Install all dependencies including dev and docs
uv sync --all-extras
```

This installs:
- Core dependencies (pydantic, click, jinja2, etc.)
- Dev dependencies (pytest, ruff, mypy, etc.)
- Docs dependencies (mkdocs, mkdocs-material, etc.)

### 3. Install Git Hooks (Optional)

```bash
npm install
```

This sets up:
- Commit message linting (commitlint)
- Pre-commit hooks

### 4. Verify Installation

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy src

# Build docs
uv run mkdocs build
```

## IDE Setup

### VS Code

Recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml"
  ]
}
```

Settings for the workspace:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.organizeImports": true
}
```

### PyCharm

1. Open the project
2. Configure Python interpreter: `.venv/bin/python`
3. Enable ruff integration (Settings > Tools > Ruff)
4. Enable mypy integration (Settings > Tools > Mypy)

## Project Structure

```
prisme/
├── src/prism/                # Main package source
│   ├── __init__.py           # Package exports
│   ├── cli.py                # CLI commands
│   ├── spec/                 # Specification models
│   │   ├── fields.py         # FieldType, FilterOperator
│   │   ├── exposure.py       # REST/GraphQL/MCP/Frontend
│   │   ├── model.py          # ModelSpec
│   │   └── stack.py          # StackSpec
│   ├── generators/           # Code generators
│   │   ├── base.py           # Base classes
│   │   ├── backend/          # Backend generators
│   │   └── frontend/         # Frontend generators
│   ├── templates/            # Jinja2 templates
│   ├── utils/                # Utilities
│   ├── tracking/             # Change tracking
│   └── docker/               # Docker support
├── tests/                    # Test suite
│   ├── conftest.py           # Fixtures
│   ├── spec/                 # Spec model tests
│   ├── generators/           # Generator tests
│   └── cli/                  # CLI tests
├── docs/                     # Documentation
├── specs/                    # Example specs
├── .github/                  # GitHub Actions
├── pyproject.toml            # Project config
└── mkdocs.yml                # Docs config
```

## Common Tasks

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific file
uv run pytest tests/spec/test_models.py

# Specific test
uv run pytest tests/spec/test_models.py::test_model_spec_validation

# Include slow tests
uv run pytest -m slow

# Verbose output
uv run pytest -v
```

### Linting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Check formatting
uv run ruff format --check .

# Auto-format
uv run ruff format .
```

### Type Checking

```bash
# Check all source
uv run mypy src

# Check specific file
uv run mypy src/prism/cli.py
```

### Documentation

```bash
# Serve with hot reload
uv run mkdocs serve

# Build static site
uv run mkdocs build --strict

# Open in browser
open http://localhost:8000
```

### Running the CLI

```bash
# Run CLI commands during development
uv run prism --help
uv run prism create test-project
uv run prism generate
```

## Environment Variables

For testing and development:

| Variable | Description | Default |
|----------|-------------|---------|
| `PRISM_DEBUG` | Enable debug logging | `false` |
| `PRISM_TEST_DB` | Test database URL | `sqlite:///:memory:` |

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
uv sync --all-extras
```

### Import Errors

Ensure you're using the virtual environment:

```bash
# Check which Python
which python

# Should be: /path/to/prisme/.venv/bin/python
```

### Test Database Issues

```bash
# Run tests with SQLite (no external DB needed)
uv run pytest

# Or set test database explicitly
PRISM_TEST_DB=sqlite:///:memory: uv run pytest
```

### Documentation Build Errors

```bash
# Install docs dependencies explicitly
uv sync --extra docs

# Build with verbose output
uv run mkdocs build -v
```

## Next Steps

- Read the [Contributing Guide](contributing.md)
- Understand the [Architecture](../architecture/index.md)
- Check open [Issues](https://github.com/Lasse-numerous/prisme/issues)

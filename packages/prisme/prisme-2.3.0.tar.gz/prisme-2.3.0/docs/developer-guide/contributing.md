# Contributing to Prisme

Thank you for your interest in contributing to Prisme! This guide will help you get started.

## Ways to Contribute

- **Bug Reports**: Found a bug? [Open an issue](https://github.com/Lasse-numerous/prisme/issues)
- **Feature Requests**: Have an idea? [Start a discussion](https://github.com/Lasse-numerous/prisme/discussions)
- **Code**: Fix bugs, add features, improve documentation
- **Documentation**: Improve or add documentation
- **Testing**: Add tests, report test failures

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Node.js 22+ (for commit hooks)
- Git

### Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/prisme.git
cd prisme

# Add upstream remote
git remote add upstream https://github.com/Lasse-numerous/prisme.git
```

### Install Dependencies

```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Install git hooks
npm install
```

### Verify Setup

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Type check
uv run mypy src
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feat/my-feature
```

### 2. Make Changes

- Follow the [code style guidelines](#code-style)
- Write tests for new functionality
- Update documentation if needed

### 3. Test Locally

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/spec/test_models.py

# Run linting
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src
```

### 4. Commit Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: type(scope): description
git commit -m "feat(generators): add support for custom widgets"
git commit -m "fix(cli): resolve path handling on Windows"
git commit -m "docs: update installation guide"
```

#### Commit Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `perf` | Performance improvement | Patch |
| `docs` | Documentation only | None |
| `style` | Code style (formatting) | None |
| `refactor` | Code change (no bug/feature) | None |
| `test` | Add/modify tests | None |
| `build` | Build system changes | None |
| `ci` | CI configuration | None |
| `chore` | Other changes | None |

#### Breaking Changes

Add `!` after the type for breaking changes:

```bash
git commit -m "feat(spec)!: rename FieldType.TEXT to FieldType.STRING"
```

### 5. Push and Create PR

```bash
git push origin feat/my-feature
```

Then open a Pull Request on GitHub.

## Code Style

### Python

- Follow PEP 8 (enforced by ruff)
- Use type hints for all function signatures
- Write docstrings for public APIs (Google style)
- Keep functions focused and small
- Prefer composition over inheritance

```python
# Good
def create_customer(
    db: AsyncSession,
    data: CustomerCreate,
) -> Customer:
    """Create a new customer.

    Args:
        db: Database session
        data: Customer data

    Returns:
        Created customer

    Raises:
        ValueError: If email already exists
    """
    ...
```

### Formatting

```bash
# Auto-format code
uv run ruff format .

# Auto-fix lint issues
uv run ruff check . --fix
```

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy src`)
- [ ] Commits follow conventional commit format
- [ ] Documentation updated (if needed)

### PR Title

Follow the same format as commit messages:

```
feat(generators): add support for custom widgets
fix(cli): resolve path handling on Windows
docs: update installation guide
```

### PR Description

Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Related issues (if any)

### Review Process

1. Automated checks run (CI)
2. Maintainer reviews code
3. Address feedback
4. Merge when approved

## Testing Guidelines

### Writing Tests

```python
# tests/generators/test_models_generator.py
import pytest
from prism.generators.backend import ModelsGenerator

@pytest.mark.asyncio
async def test_generates_model_with_timestamps():
    """Test that timestamps fields are generated correctly."""
    spec = create_test_spec(timestamps=True)
    generator = ModelsGenerator(context)

    result = generator.generate()

    assert "created_at" in result.files[0].content
    assert "updated_at" in result.files[0].content
```

### Test Organization

- One test file per module
- Group related tests in classes
- Use descriptive test names
- Use fixtures for common setup

### Test Markers

```python
@pytest.mark.slow  # Excluded from default runs
@pytest.mark.asyncio  # Async tests
```

## Documentation

### Building Docs

```bash
# Serve locally with hot reload
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Add links to related pages
- Use admonitions for notes/warnings

```markdown
!!! note
    This is an important note.

!!! warning
    Be careful with this operation.
```

## Release Process

Releases are automated via semantic-release:

1. Commits to `main` trigger release check
2. If releasable commits exist:
   - Version bumped based on commit types
   - CHANGELOG.md updated
   - GitHub release created
   - Package published to PyPI

## Getting Help

- [GitHub Issues](https://github.com/Lasse-numerous/prisme/issues)
- [GitHub Discussions](https://github.com/Lasse-numerous/prisme/discussions)

## Code of Conduct

Please be respectful and inclusive. We're all here to build something great together.

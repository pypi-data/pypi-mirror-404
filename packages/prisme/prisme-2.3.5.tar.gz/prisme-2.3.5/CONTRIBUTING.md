# Contributing to Prism

> See also: [README.md](README.md) (project overview) | [AGENT.md](AGENT.md) (AI agent instructions) | [dev/dev-docs.md](dev/dev-docs.md) (development docs)
>
> CLI: `uv run prism --help` (install: `uv add prisme`) | Docs: [docs/](docs/) | [prisme.readthedocs.io](https://prisme.readthedocs.io/)

**Quick start:** `uv sync --all-extras && uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push`

Thank you for your interest in contributing to Prism! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Lasse-numerous/prisme.git
cd prisme

# Install dependencies (includes dev dependencies)
uv sync --all-extras

# Install all git hooks (pre-commit, commit-msg, pre-push)
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

### Running Tests

Tests run automatically on `git push` via pre-push hooks. You can also run them manually:

```bash
# Run all tests (recommended before pushing)
uv run pytest

# Quick check - stop on first failure
uv run pytest -x

# Run with coverage
uv run pytest --cov --cov-report=html

# Run specific test file
uv run pytest tests/spec/test_models.py

# Run slow tests (excluded by default)
uv run pytest -m slow

# Run end-to-end tests
uv run pytest -m e2e

# Run Docker tests (requires Docker)
uv run pytest -m docker
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Check formatting
uv run ruff format --check .

# Auto-format code
uv run ruff format .

# Type check
uv run mypy src
```

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for our commit messages. This enables automatic semantic versioning and changelog generation.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature (triggers minor version bump) |
| `fix` | A bug fix (triggers patch version bump) |
| `perf` | Performance improvement (triggers patch version bump) |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, whitespace) |
| `refactor` | Code changes that neither fix bugs nor add features |
| `test` | Adding or modifying tests |
| `build` | Changes to build system or dependencies |
| `ci` | Changes to CI configuration |
| `chore` | Other changes that don't modify src or test files |

### Examples

```bash
# Feature
feat(generators): add support for nested model generation

# Bug fix
fix(cli): resolve path resolution on Windows

# Breaking change (add ! after type)
feat(spec)!: rename FieldType.TEXT to FieldType.STRING

# With scope
fix(backend): handle null values in REST serialization

# Without scope
docs: update installation instructions
```

### Commit Linting

Commit messages are automatically validated by the `commit-msg` hook (installed via pre-commit). If your commit message doesn't follow the conventional commits format, the commit will be rejected. No Node.js required - this uses the Python-based [conventional-pre-commit](https://github.com/compilerla/conventional-pre-commit) hook.

## Git Hooks

All hooks are managed by [pre-commit](https://pre-commit.com/). Install them with:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

### Pre-commit (on `git commit`)

Runs automatically on each commit to fix formatting issues:
- **ruff** - Auto-fix linting issues
- **ruff-format** - Auto-format code
- **trailing-whitespace** - Remove trailing whitespace
- **end-of-file-fixer** - Ensure files end with newline
- **check-yaml** - Validate YAML syntax

### Commit-msg (on `git commit`)

Validates commit message format:
- **conventional-pre-commit** - Ensures commit follows [Conventional Commits](https://www.conventionalcommits.org/) format

### Pre-push (on `git push`)

Runs automatically before pushing to catch CI failures early:
- **ruff check** - Lint check (no auto-fix)
- **ruff format --check** - Format check
- **mypy** - Type checking
- **pytest** - Run tests

This mirrors the CI pipeline, so if pre-push passes, CI should pass too.

## CI/CD Pipeline

### Continuous Integration

Every push and pull request triggers the CI workflow which runs:

1. **Linting** - `ruff check .`
2. **Format Check** - `ruff format --check .`
3. **Type Checking** - `mypy src`
4. **Tests** - `pytest --cov`
5. **Coverage Upload** - Results uploaded to Codecov

All checks must pass before a PR can be merged.

### Automated Releases

When changes are merged to `main`:

1. **Semantic Release** analyzes commits since last release
2. If releasable commits exist:
   - Version is bumped based on commit types
   - CHANGELOG.md is updated
   - GitHub release is created
   - Package is published to PyPI

## Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Make changes** following the code style guidelines
3. **Write tests** for new functionality
4. **Commit** using conventional commit format
5. **Push** - pre-push hooks automatically run CI checks (lint, format, type check, tests)
6. **Open a Pull Request** once pre-push checks pass
7. **Address feedback** from code review

> **Note:** If you need to bypass pre-push hooks (not recommended), use `git push --no-verify`

## Code Style

- Follow PEP 8 guidelines (enforced by ruff)
- Use type hints for all function signatures
- Write docstrings for public APIs
- Keep functions focused and small
- Prefer composition over inheritance

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Use fixtures for common test data
- Mark slow tests with `@pytest.mark.slow`

## Development Documentation

Internal development documentation is maintained in the `dev/` folder:

- **[dev/dev-docs.md](dev/dev-docs.md)** - Conventions and file naming guidelines
- **[dev/roadmap.md](dev/roadmap.md)** - Development roadmap and priorities
- **dev/issues/** - Active issue tracking documents
- **dev/plans/** - Implementation plans for features
- **dev/tasks/** - Active task tracking documents

See [dev/dev-docs.md](dev/dev-docs.md) for document templates and naming conventions.

## Questions?

Feel free to open an issue for questions or discussions about contributing.

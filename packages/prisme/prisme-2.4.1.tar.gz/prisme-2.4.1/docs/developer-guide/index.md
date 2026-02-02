# Developer Guide

Documentation for contributing to Prisme development.

## Overview

This section covers everything you need to contribute to the Prisme framework itself.

<div class="grid cards" markdown>

-   :material-git:{ .lg .middle } **Contributing**

    ---

    How to contribute to Prisme

    [:octicons-arrow-right-24: Contributing Guide](contributing.md)

-   :material-laptop:{ .lg .middle } **Development Setup**

    ---

    Setting up your development environment

    [:octicons-arrow-right-24: Development Setup](development-setup.md)

-   :material-test-tube:{ .lg .middle } **Testing**

    ---

    Running and writing tests

    [:octicons-arrow-right-24: Testing Guide](testing.md)

</div>

## Quick Start for Contributors

```bash
# Clone the repository
git clone https://github.com/Lasse-numerous/prisme.git
cd prisme

# Install all dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy src

# Build documentation
uv run mkdocs serve
```

## Project Structure

```
prisme/
├── src/prism/                # Main package
│   ├── cli.py                # CLI entry point
│   ├── spec/                 # Specification models
│   ├── generators/           # Code generators
│   ├── templates/            # Jinja2 templates
│   ├── utils/                # Utilities
│   ├── tracking/             # Change tracking
│   └── docker/               # Docker support
├── tests/                    # Test suite
├── docs/                     # Documentation (you're reading it!)
├── specs/                    # Example specifications
├── .github/workflows/        # CI/CD
├── pyproject.toml            # Project configuration
└── mkdocs.yml                # Documentation config
```

## Development Workflow

1. **Fork** the repository
2. **Create** a feature branch
3. **Make changes** following code style guidelines
4. **Write tests** for new functionality
5. **Run** linting and tests locally
6. **Commit** using conventional commits
7. **Submit** a pull request

## Key Resources

- [GitHub Repository](https://github.com/Lasse-numerous/prisme)
- [Issue Tracker](https://github.com/Lasse-numerous/prisme/issues)
- [CI/CD Pipeline](https://github.com/Lasse-numerous/prisme/actions)

# Getting Started

Welcome to Prisme! This section will help you get up and running quickly.

## Overview

Prisme is a code generation framework that lets you define your data models once and generate a full-stack application including:

- **Backend**: FastAPI REST endpoints, Strawberry GraphQL API, FastMCP tools
- **Frontend**: React + TypeScript components, hooks, and pages
- **Database**: SQLAlchemy models with Alembic migrations
- **Testing**: Comprehensive test suites for backend and frontend

## Quick Links

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Installation**

    ---

    Install Prisme using uv or pip

    [:octicons-arrow-right-24: Installation Guide](installation.md)

-   :material-flash:{ .lg .middle } **Quick Start**

    ---

    Create your first project in 5 minutes

    [:octicons-arrow-right-24: Quick Start](quickstart.md)

-   :material-school:{ .lg .middle } **First Project**

    ---

    Complete walkthrough building a real application

    [:octicons-arrow-right-24: First Project Tutorial](first-project.md)

</div>

## Prerequisites

Before you begin, ensure you have:

- **Python 3.13+** installed
- **Node.js 22+** (for frontend development)
- **uv** (recommended) or pip for package management

### Installing uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## Next Steps

Ready to dive in? Start with the [Installation Guide](installation.md) or jump straight to the [Quick Start](quickstart.md) if you prefer learning by doing.

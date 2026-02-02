"""Project templates for Prism.

This module provides templates for bootstrapping new projects:
- minimal: SQLite, REST only, no frontend
- full: PostgreSQL, REST + GraphQL + MCP, React frontend
- saas: Full + auth, multi-tenancy, billing models
- api-only: Full backend, no frontend
"""

from prisme.templates.base import ProjectTemplate, TemplateFile, TemplateRegistry

__all__ = [
    "ProjectTemplate",
    "TemplateFile",
    "TemplateRegistry",
]

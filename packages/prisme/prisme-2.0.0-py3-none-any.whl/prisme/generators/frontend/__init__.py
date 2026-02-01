"""Frontend code generators for Prism.

This module contains generators for:
- TypeScript types
- GraphQL operations
- Widget system
- Headless UI hooks
- React components
- React hooks
- Page components
- Router configuration
- Authentication components
"""

from prisme.generators.frontend.admin import FrontendAdminGenerator
from prisme.generators.frontend.auth import FrontendAuthGenerator
from prisme.generators.frontend.components import ComponentsGenerator
from prisme.generators.frontend.design import DesignSystemGenerator
from prisme.generators.frontend.graphql_ops import GraphQLOpsGenerator
from prisme.generators.frontend.headless import HeadlessGenerator
from prisme.generators.frontend.hooks import HooksGenerator
from prisme.generators.frontend.pages import PagesGenerator
from prisme.generators.frontend.router import RouterGenerator
from prisme.generators.frontend.types import TypeScriptGenerator
from prisme.generators.frontend.widgets import WidgetSystemGenerator

__all__ = [
    "ComponentsGenerator",
    "DesignSystemGenerator",
    "FrontendAdminGenerator",
    "FrontendAuthGenerator",
    "GraphQLOpsGenerator",
    "HeadlessGenerator",
    "HooksGenerator",
    "PagesGenerator",
    "RouterGenerator",
    "TypeScriptGenerator",
    "WidgetSystemGenerator",
]

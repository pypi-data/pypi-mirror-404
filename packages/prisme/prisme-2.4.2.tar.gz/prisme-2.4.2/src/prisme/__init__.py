"""Prism - Code generation framework for full-stack applications from Pydantic models.

"One spec, full spectrum."
"""

from pathlib import Path

from pydantic import BaseModel, Field

from prisme.spec.auth import (
    APIKeyConfig,
    AuthConfig,
    EmailConfig,
    OAuthProviderConfig,
    SignupAccessConfig,
    SignupWhitelist,
)
from prisme.spec.design import (
    BorderRadius,
    DesignSystemConfig,
    FontFamily,
    IconSet,
    ThemePreset,
)
from prisme.spec.exposure import (
    CRUDOperations,
    FrontendExposure,
    GraphQLExposure,
    MCPExposure,
    PaginationConfig,
    PaginationStyle,
    RESTExposure,
)
from prisme.spec.fields import FieldSpec, FieldType, FilterOperator
from prisme.spec.infrastructure import TraefikConfig
from prisme.spec.model import Model, ModelSpec, Relationship, RelationshipSpec, TemporalConfig
from prisme.spec.overrides import DeliveryOverrides, FrontendOverrides, MCPOverrides
from prisme.spec.project import (
    DatabaseConfig,
    ExtensionConfig,
    GeneratorConfig,
    GraphQLConfig,
    ProjectSpec,
    TestingConfig,
    WidgetConfig,
)
from prisme.spec.stack import (
    FileStrategy,
    StackSpec,
)

__version__ = "0.1.0"


class PrismConfig(BaseModel):
    """Prism project configuration.

    This configuration is stored in `prism.config.py` in the project root
    and defines project-level settings including the spec file location.

    Example:
        >>> config = PrismConfig(
        ...     spec_path="specs/models.py",
        ...     backend_path="packages/backend/src/my_app",
        ...     frontend_path="packages/frontend",
        ...     backend_module_name="my_app",
        ... )
    """

    spec_path: str = Field(
        default="specs/models.py",
        description="Path to the Prism specification file (relative to project root)",
    )
    backend_path: str | None = Field(
        default=None,
        description="Path to backend output directory",
    )
    frontend_path: str | None = Field(
        default=None,
        description="Path to frontend output directory",
    )
    backend_module_name: str | None = Field(
        default=None,
        description="Python module name for backend imports (defaults to snake_case of project name)",
    )
    backend_port: int = Field(
        default=8000,
        description="Backend server port",
    )
    frontend_port: int = Field(
        default=5173,
        description="Frontend dev server port",
    )
    database_url_env: str = Field(
        default="DATABASE_URL",
        description="Environment variable name for database URL",
    )
    enable_mcp: bool = Field(
        default=True,
        description="Enable MCP tool generation",
    )
    enable_graphql: bool = Field(
        default=True,
        description="Enable GraphQL endpoint generation",
    )
    enable_rest: bool = Field(
        default=True,
        description="Enable REST endpoint generation",
    )

    model_config = {"extra": "forbid"}

    @classmethod
    def load_from_file(cls, config_path: Path) -> "PrismConfig":
        """Load PrismConfig from a prism.config.py file.

        Args:
            config_path: Path to the prism.config.py file.

        Returns:
            The loaded PrismConfig instance.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If the config file doesn't contain a valid config.
        """
        import importlib.util

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        spec = importlib.util.spec_from_file_location("prisme_config", config_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load config from: {config_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "config") and isinstance(module.config, cls):
            return module.config

        raise ValueError(
            f"Config file must define a 'config' variable of type PrismConfig: {config_path}"
        )


__all__ = [
    "APIKeyConfig",
    "AuthConfig",
    "BorderRadius",
    "CRUDOperations",
    "DatabaseConfig",
    "DeliveryOverrides",
    "DesignSystemConfig",
    "EmailConfig",
    "ExtensionConfig",
    "FieldSpec",
    "FieldType",
    "FileStrategy",
    "FilterOperator",
    "FontFamily",
    "FrontendExposure",
    "FrontendOverrides",
    "GeneratorConfig",
    "GraphQLConfig",
    "GraphQLExposure",
    "IconSet",
    "MCPExposure",
    "MCPOverrides",
    "Model",
    "ModelSpec",
    "OAuthProviderConfig",
    "PaginationConfig",
    "PaginationStyle",
    "PrismConfig",
    "ProjectSpec",
    "RESTExposure",
    "Relationship",
    "RelationshipSpec",
    "SignupAccessConfig",
    "SignupWhitelist",
    "StackSpec",
    "TemporalConfig",
    "TestingConfig",
    "ThemePreset",
    "TraefikConfig",
    "WidgetConfig",
    "__version__",
]

"""Project specification for Prisme v2.

Defines infrastructure and project-level configuration that is separate
from domain model definitions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from prisme.spec.auth import AuthConfig
from prisme.spec.design import DesignSystemConfig

PRISME_PROJECT_VERSION = 1


class BackendConfig(BaseModel):
    """Backend framework configuration."""

    framework: str = Field(
        default="fastapi",
        description="Backend framework: 'fastapi'",
    )
    module_name: str | None = Field(
        default=None,
        description="Python module name (defaults to snake_case of project name)",
    )
    port: int = Field(
        default=8000,
        description="Backend server port",
    )

    model_config = {"extra": "forbid"}


class FrontendConfig(BaseModel):
    """Frontend framework configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable frontend generation",
    )
    framework: str = Field(
        default="react",
        description="Frontend framework: 'react'",
    )
    port: int = Field(
        default=5173,
        description="Frontend dev server port",
    )

    model_config = {"extra": "forbid"}


class ExposureDefaults(BaseModel):
    """Default exposure settings applied to all models."""

    default_page_size: int = Field(default=20, description="Default items per page")
    max_page_size: int = Field(default=100, description="Maximum items per page")

    model_config = {"extra": "forbid"}


class RESTConfig(BaseModel):
    """REST API configuration."""

    enabled: bool = Field(default=True, description="Enable REST API generation")
    prefix: str = Field(default="/api/v1", description="URL prefix for REST endpoints")

    model_config = {"extra": "forbid"}


class GraphQLConfig(BaseModel):
    """GraphQL API configuration."""

    enabled: bool = Field(default=True, description="Enable GraphQL endpoint")
    path: str = Field(default="/graphql", description="GraphQL endpoint path")
    graphiql: bool = Field(default=True, description="Enable GraphiQL playground")
    subscriptions_enabled: bool = Field(
        default=True,
        description="Enable GraphQL subscriptions",
    )
    query_depth_limit: int = Field(default=10, description="Maximum query depth")
    query_complexity_limit: int = Field(default=100, description="Maximum query complexity")

    model_config = {"extra": "forbid"}


class MCPConfig(BaseModel):
    """MCP tool generation configuration."""

    enabled: bool = Field(default=True, description="Enable MCP tool generation")

    model_config = {"extra": "forbid"}


class FrontendExposureConfig(BaseModel):
    """Frontend exposure defaults."""

    enabled: bool = Field(default=True, description="Enable frontend code generation")
    api_style: str = Field(
        default="graphql",
        description="API style: 'graphql', 'rest', or 'both'",
    )
    graphql_client: str = Field(
        default="urql",
        description="GraphQL client: 'urql' or 'apollo'",
    )

    model_config = {"extra": "forbid"}


class ExposureConfig(BaseModel):
    """Controls which delivery channels are enabled and their defaults."""

    defaults: ExposureDefaults = Field(
        default_factory=ExposureDefaults,
        description="Default exposure settings",
    )
    rest: RESTConfig = Field(
        default_factory=RESTConfig,
        description="REST API configuration",
    )
    graphql: GraphQLConfig = Field(
        default_factory=GraphQLConfig,
        description="GraphQL configuration",
    )
    mcp: MCPConfig = Field(
        default_factory=MCPConfig,
        description="MCP configuration",
    )
    frontend: FrontendExposureConfig = Field(
        default_factory=FrontendExposureConfig,
        description="Frontend exposure configuration",
    )

    model_config = {"extra": "forbid"}


class DatabaseConfig(BaseModel):
    """Database configuration."""

    engine: str = Field(
        default="postgresql",
        description="Database engine: 'postgresql' or 'sqlite'",
    )
    async_driver: bool = Field(
        default=True,
        description="Use async database driver",
    )
    url_env: str = Field(
        default="DATABASE_URL",
        description="Environment variable name for database URL",
    )

    model_config = {"extra": "forbid"}


class WidgetConfig(BaseModel):
    """Frontend widget configuration."""

    type_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by field type",
    )
    ui_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by ui_widget hint",
    )
    field_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by Model.field",
    )

    model_config = {"extra": "forbid"}


# Use the full DesignSystemConfig from spec.design
DesignConfig = DesignSystemConfig


class DeployHetznerConfig(BaseModel):
    """Hetzner-specific deployment settings."""

    location: str = Field(default="fsn1", description="Datacenter location")
    staging_server_type: str = Field(default="cx23", description="Staging server type")
    production_server_type: str = Field(default="cx23", description="Production server type")
    production_floating_ip: bool = Field(
        default=True, description="Enable floating IP for production"
    )

    model_config = {"extra": "forbid"}


class DeployConfig(BaseModel):
    """Deployment infrastructure configuration.

    Replaces CLI flags from ``prisme deploy init``.
    """

    provider: str = Field(default="hetzner", description="Cloud provider")
    domain: str = Field(default="", description="Base domain for deployment")
    ssl_email: str = Field(default="", description="Email for Let's Encrypt certificates")
    use_redis: bool = Field(default=False, description="Include Redis in deployment")
    hetzner: DeployHetznerConfig = Field(
        default_factory=DeployHetznerConfig,
        description="Hetzner-specific settings",
    )

    model_config = {"extra": "forbid"}


class CIConfig(BaseModel):
    """CI/CD pipeline configuration.

    Replaces CLI flags from ``prisme ci init``.
    """

    provider: str = Field(default="github", description="CI provider: 'github' or 'gitlab'")
    include_frontend: bool = Field(default=True, description="Include frontend workflows")
    use_redis: bool = Field(default=False, description="Include Redis in CI")
    enable_codecov: bool = Field(default=True, description="Enable Codecov integration")
    enable_dependabot: bool = Field(default=True, description="Enable Dependabot config")
    enable_semantic_release: bool = Field(default=True, description="Enable semantic-release")
    enable_commitlint: bool = Field(default=True, description="Enable commitlint config")

    model_config = {"extra": "forbid"}


class DockerProductionConfig(BaseModel):
    """Production Docker settings."""

    domain: str = Field(default="", description="Production domain name")
    replicas: int = Field(default=2, description="Number of backend replicas")

    model_config = {"extra": "forbid"}


class DockerConfig(BaseModel):
    """Docker configuration.

    Replaces CLI flags from ``prisme docker init`` and ``docker init-prod``.
    """

    include_redis: bool = Field(default=False, description="Include Redis service")
    include_mcp: bool = Field(default=False, description="Include MCP server service")
    production: DockerProductionConfig = Field(
        default_factory=DockerProductionConfig,
        description="Production Docker settings",
    )

    model_config = {"extra": "forbid"}


class TestingConfig(BaseModel):
    """Testing configuration."""

    generate_unit_tests: bool = Field(default=True, description="Generate unit tests")
    generate_integration_tests: bool = Field(default=True, description="Generate integration tests")
    generate_component_tests: bool = Field(default=True, description="Generate component tests")
    generate_graphql_tests: bool = Field(default=True, description="Generate GraphQL tests")
    generate_hook_tests: bool = Field(default=True, description="Generate hook tests")
    generate_factories: bool = Field(default=True, description="Generate test factories")
    test_database: str = Field(default="sqlite", description="Database for tests")

    model_config = {"extra": "forbid"}


class ExtensionConfig(BaseModel):
    """Extension and customization configuration."""

    services_strategy: str = Field(
        default="generate_base",
        description="Strategy for service files",
    )
    components_strategy: str = Field(
        default="generate_base",
        description="Strategy for component files",
    )
    pages_strategy: str = Field(
        default="generate_once",
        description="Strategy for page files",
    )
    use_protected_regions: bool = Field(
        default=True,
        description="Enable protected region markers",
    )

    model_config = {"extra": "forbid"}


class GeneratorConfig(BaseModel):
    """Code generator configuration.

    Controls output paths and generation options.
    """

    # Output paths
    backend_output: str = Field(
        default="packages/backend/src",
        description="Backend output directory",
    )
    frontend_output: str = Field(
        default="packages/frontend/src",
        description="Frontend output directory",
    )

    # Backend structure
    models_path: str = Field(default="models", description="Models subdirectory")
    schemas_path: str = Field(default="schemas", description="Schemas subdirectory")
    services_path: str = Field(default="services", description="Services subdirectory")
    services_generated_path: str = Field(
        default="services/_generated",
        description="Generated services subdirectory",
    )
    rest_path: str = Field(default="api/rest", description="REST API subdirectory")
    graphql_path: str = Field(default="api/graphql", description="GraphQL subdirectory")
    graphql_generated_path: str = Field(
        default="api/graphql/_generated",
        description="Generated GraphQL subdirectory",
    )
    mcp_path: str = Field(default="mcp_server", description="MCP tools subdirectory")
    tests_path: str = Field(default="tests", description="Tests subdirectory")

    # Frontend structure
    types_path: str = Field(default="types", description="Types subdirectory")
    graphql_operations_path: str = Field(
        default="graphql",
        description="GraphQL operations subdirectory",
    )
    api_client_path: str = Field(default="api", description="API client subdirectory")
    components_path: str = Field(default="components", description="Components subdirectory")
    components_generated_path: str = Field(
        default="components/_generated",
        description="Generated components subdirectory",
    )
    hooks_path: str = Field(default="hooks", description="Hooks subdirectory")
    pages_path: str = Field(default="pages", description="Pages subdirectory")
    prism_path: str = Field(default="prism", description="Prism system subdirectory")
    frontend_tests_path: str = Field(default="__tests__", description="Frontend tests subdirectory")

    # Options
    generate_migrations: bool = Field(
        default=True,
        description="Generate Alembic migrations",
    )
    overwrite_existing: bool = Field(
        default=False,
        description="Overwrite existing files",
    )
    dry_run: bool = Field(
        default=False,
        description="Preview changes without writing",
    )

    model_config = {"extra": "forbid"}


class ProjectSpec(BaseModel):
    """Complete project-level specification.

    Contains all infrastructure and configuration settings that are
    separate from domain model definitions. This is the v2 replacement
    for the infrastructure portions of StackSpec.
    """

    name: str = Field(..., description="Project name (kebab-case)")
    title: str | None = Field(default=None, description="Human-readable project title")
    version: str = Field(default="1.0.0", description="Project version")
    description: str | None = Field(default=None, description="Project description")

    backend: BackendConfig = Field(
        default_factory=BackendConfig,
        description="Backend configuration",
    )
    frontend: FrontendConfig = Field(
        default_factory=FrontendConfig,
        description="Frontend configuration",
    )
    exposure: ExposureConfig = Field(
        default_factory=ExposureConfig,
        description="Exposure/delivery channel configuration",
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description="Authentication configuration",
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database configuration",
    )
    design: DesignSystemConfig = Field(
        default_factory=DesignSystemConfig,
        description="Design system configuration",
    )
    testing: TestingConfig = Field(
        default_factory=TestingConfig,
        description="Testing configuration",
    )
    extensions: ExtensionConfig = Field(
        default_factory=ExtensionConfig,
        description="Extension configuration",
    )
    generator: GeneratorConfig = Field(
        default_factory=GeneratorConfig,
        description="Generator configuration",
    )
    widgets: WidgetConfig = Field(
        default_factory=WidgetConfig,
        description="Widget configuration",
    )
    deploy: DeployConfig | None = Field(
        default=None,
        description="Deployment infrastructure configuration",
    )
    ci: CIConfig | None = Field(
        default=None,
        description="CI/CD pipeline configuration",
    )
    docker: DockerConfig | None = Field(
        default=None,
        description="Docker configuration",
    )

    @property
    def effective_title(self) -> str:
        """Get the effective project title."""
        if self.title:
            return self.title
        return self.name.replace("-", " ").replace("_", " ").title()

    model_config = {"extra": "forbid"}


__all__ = [
    "PRISME_PROJECT_VERSION",
    "AuthConfig",
    "BackendConfig",
    "CIConfig",
    "DatabaseConfig",
    "DeployConfig",
    "DeployHetznerConfig",
    "DesignConfig",
    "DockerConfig",
    "DockerProductionConfig",
    "ExposureConfig",
    "ExposureDefaults",
    "ExtensionConfig",
    "FrontendConfig",
    "FrontendExposureConfig",
    "GeneratorConfig",
    "GraphQLConfig",
    "MCPConfig",
    "ProjectSpec",
    "RESTConfig",
    "TestingConfig",
    "WidgetConfig",
]

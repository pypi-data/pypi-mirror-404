"""Prisme specification models.

This module contains all the Pydantic models for defining Prisme specifications.
"""

from prisme.spec.auth import (
    AdminPanelConfig,
    APIKeyConfig,
    AuthConfig,
    EmailConfig,
    OAuthProviderConfig,
    Role,
    SignupAccessConfig,
    SignupWhitelist,
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
from prisme.spec.model import Model, ModelSpec, Relationship, RelationshipSpec
from prisme.spec.overrides import DeliveryOverrides, FrontendOverrides, MCPOverrides
from prisme.spec.project import (
    BackendConfig,
    DatabaseConfig,
    DesignConfig,
    ExposureConfig,
    ExposureDefaults,
    ExtensionConfig,
    FrontendConfig,
    FrontendExposureConfig,
    GeneratorConfig,
    GraphQLConfig,
    MCPConfig,
    ProjectSpec,
    RESTConfig,
    TestingConfig,
    WidgetConfig,
)
from prisme.spec.stack import (
    FileStrategy,
    StackSpec,
)

# v2 alias: Field = FieldSpec (can't live in fields.py due to pydantic.Field collision)
Field = FieldSpec

__all__ = [
    "APIKeyConfig",
    "AdminPanelConfig",
    "AuthConfig",
    "BackendConfig",
    "CRUDOperations",
    "DatabaseConfig",
    "DeliveryOverrides",
    "DesignConfig",
    "EmailConfig",
    "ExposureConfig",
    "ExposureDefaults",
    "ExtensionConfig",
    "Field",
    "FieldSpec",
    "FieldType",
    "FileStrategy",
    "FilterOperator",
    "FrontendConfig",
    "FrontendExposure",
    "FrontendExposureConfig",
    "FrontendOverrides",
    "GeneratorConfig",
    "GraphQLConfig",
    "GraphQLExposure",
    "MCPConfig",
    "MCPExposure",
    "MCPOverrides",
    "Model",
    "ModelSpec",
    "OAuthProviderConfig",
    "PaginationConfig",
    "PaginationStyle",
    "ProjectSpec",
    "RESTConfig",
    "RESTExposure",
    "Relationship",
    "RelationshipSpec",
    "Role",
    "SignupAccessConfig",
    "SignupWhitelist",
    "StackSpec",
    "TestingConfig",
    "WidgetConfig",
]

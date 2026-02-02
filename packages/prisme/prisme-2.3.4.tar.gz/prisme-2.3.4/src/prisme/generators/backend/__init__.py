"""Backend code generators for Prism.

This module contains generators for:
- SQLAlchemy models
- Pydantic schemas
- Service classes
- JWT authentication
- API key authentication
- FastAPI REST endpoints
- Strawberry GraphQL types, queries, mutations
- FastMCP tools
- Alembic database migrations
"""

from prisme.generators.backend.admin import AdminGenerator
from prisme.generators.backend.alembic import AlembicGenerator
from prisme.generators.backend.api_key_auth import APIKeyAuthGenerator
from prisme.generators.backend.auth import AuthGenerator
from prisme.generators.backend.graphql import GraphQLGenerator
from prisme.generators.backend.mcp import MCPGenerator
from prisme.generators.backend.models import ModelsGenerator
from prisme.generators.backend.rest import RESTGenerator
from prisme.generators.backend.schemas import SchemasGenerator
from prisme.generators.backend.services import ServicesGenerator

__all__ = [
    "APIKeyAuthGenerator",
    "AdminGenerator",
    "AlembicGenerator",
    "AuthGenerator",
    "GraphQLGenerator",
    "MCPGenerator",
    "ModelsGenerator",
    "RESTGenerator",
    "SchemasGenerator",
    "ServicesGenerator",
]

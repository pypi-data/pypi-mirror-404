# Changelog

All notable changes to Prisme are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/) and uses [Conventional Commits](https://www.conventionalcommits.org/) for automated version management.

## [Unreleased]

_No unreleased changes._

## [0.8.0] - 2026-01-26

### Added
- Automatic GraphQL option loading for RelationSelect widget
- Optional FK support for many_to_one relationships

### Fixed
- Prevent infinite re-render loop in RelationSelect widget
- Add table prefix to common enum field names
- Use snake_case for relationship ID fields in Pydantic filters
- Add camelCase to snake_case conversion for GraphQL input
- Resolve forward reference and duplicate filter issues in GraphQL

## [0.7.0] - 2026-01-25

### Added
- Many-to-many (M2M) relationship support across Services, MCP, and REST generators
- Association tables automatically generated for M2M relationships

## [0.6.0] - 2026-01-24

### Added
- MCP server support in Docker development environment
- Traefik configuration for MCP service routing

### Fixed
- JSON fields now support both dict and list types
- Auto-generate ForeignKey columns for many_to_one relationships
- Database port conflicts in Docker
- SSL configuration for asyncpg in Docker

## [0.5.0] - 2026-01-23

### Added
- Relationship filtering to list operations
- Filter by relationship fields in queries

## [0.4.0] - 2026-01-22

### Added
- Relationship ID fields to GraphQL input types
- Relationship parameters to MCP tools
- Relationship fields to frontend types and GraphQL operations
- Alembic configuration auto-generated during `prism generate`

### Fixed
- Combine base imports into single line in generated models
- Association tables for many-to-many relationships

## [0.3.0] - 2026-01-21

### Added
- Vite proxy configuration for local development
- Comprehensive MkDocs documentation site
- ReadTheDocs integration for hosted documentation
- AI agent documentation (`claude/agent.md`)
- Getting started tutorials
- API reference documentation
- Architecture documentation
- Developer contribution guide

### Fixed
- Use relative URLs in GraphQL clients for Vite proxy support
- Frontend Traefik router priority
- GraphQL environment variables for frontend in Docker
- Handle json_item_type in MCP schema generator

### Changed
- Updated `pyproject.toml` with documentation dependencies
- Fixed CLI version option to use correct package name (`prisme`)

## [0.1.0] - 2024-01-15

### Added
- Initial release of Prisme framework
- Specification system with `StackSpec`, `ModelSpec`, `FieldSpec`
- Backend generators:
  - SQLAlchemy models
  - Pydantic schemas
  - Service layer with CRUD operations
  - FastAPI REST endpoints
  - Strawberry GraphQL types and resolvers
  - FastMCP tools for AI integration
- Frontend generators:
  - TypeScript type definitions
  - React components (forms, tables)
  - React hooks for data fetching
  - Page components
- Docker development environment support
- CLI commands:
  - `prism create` - Project scaffolding
  - `prism generate` - Code generation
  - `prism install` - Dependency installation
  - `prism dev` - Development servers
  - `prism test` - Test execution
  - `prism db` - Database management
  - `prism docker` - Docker management
- CI/CD pipeline with GitHub Actions
- Automated releases with semantic-release
- PyPI publishing as `prisme`

### Technical Details
- Python 3.13+ required
- Async-first architecture
- Generate base, extend user pattern
- File generation strategies (ALWAYS_OVERWRITE, GENERATE_ONCE, GENERATE_BASE, MERGE)

---

## Version History

For the complete commit history, see the [GitHub releases](https://github.com/Lasse-numerous/prisme/releases) page.

## Upgrade Guides

When upgrading between major versions, please refer to the specific upgrade guide:

- [0.x to 1.0 Migration Guide](#) (coming soon)

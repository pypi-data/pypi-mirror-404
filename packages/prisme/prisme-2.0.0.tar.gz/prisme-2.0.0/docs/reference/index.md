# Reference

Complete API and specification reference for Prisme.

## Specification Reference

Detailed documentation for all Prisme specification classes:

<div class="grid cards" markdown>

-   :material-layers:{ .lg .middle } **StackSpec**

    ---

    Root configuration for your entire application

    [:octicons-arrow-right-24: StackSpec Reference](specification/stack-spec.md)

-   :material-database:{ .lg .middle } **ModelSpec**

    ---

    Define data models with fields and relationships

    [:octicons-arrow-right-24: ModelSpec Reference](specification/model-spec.md)

-   :material-form-textbox:{ .lg .middle } **FieldSpec**

    ---

    Configure individual fields with types and validation

    [:octicons-arrow-right-24: FieldSpec Reference](specification/field-spec.md)

-   :material-api:{ .lg .middle } **Exposure Config**

    ---

    REST, GraphQL, MCP, and Frontend exposure settings

    [:octicons-arrow-right-24: Exposure Config Reference](specification/exposure-config.md)

</div>

## Quick Reference

### Import Everything

```python
from prism import (
    # Core specs
    StackSpec, ModelSpec, FieldSpec, RelationshipSpec,

    # Field types
    FieldType, FilterOperator,

    # Exposure configs
    RESTExposure, GraphQLExposure, MCPExposure, FrontendExposure,
    CRUDOperations, PaginationConfig, PaginationStyle,

    # Stack configs
    DatabaseConfig, GraphQLConfig, GeneratorConfig,
    TestingConfig, ExtensionConfig, WidgetConfig,

    # Advanced
    TemporalConfig, FileStrategy,
)
```

### Field Types

| Type | Python | Database | Description |
|------|--------|----------|-------------|
| `STRING` | `str` | `VARCHAR` | Short text |
| `TEXT` | `str` | `TEXT` | Long text |
| `INTEGER` | `int` | `INTEGER` | Whole numbers |
| `FLOAT` | `float` | `FLOAT` | Decimal numbers |
| `DECIMAL` | `Decimal` | `NUMERIC` | Precise decimals |
| `BOOLEAN` | `bool` | `BOOLEAN` | True/False |
| `DATETIME` | `datetime` | `TIMESTAMP` | Date and time |
| `DATE` | `date` | `DATE` | Date only |
| `TIME` | `time` | `TIME` | Time only |
| `UUID` | `UUID` | `UUID` | Unique identifier |
| `JSON` | `dict/list` | `JSONB` | JSON data |
| `ENUM` | `str` | `ENUM` | Enumeration |
| `FOREIGN_KEY` | `int` | `INTEGER` | Reference |

### Filter Operators

| Operator | SQL | Description |
|----------|-----|-------------|
| `EQ` | `=` | Equals |
| `NE` | `!=` | Not equals |
| `GT` | `>` | Greater than |
| `GTE` | `>=` | Greater than or equal |
| `LT` | `<` | Less than |
| `LTE` | `<=` | Less than or equal |
| `LIKE` | `LIKE` | Pattern match |
| `ILIKE` | `ILIKE` | Case-insensitive pattern |
| `IN` | `IN` | In list |
| `NOT_IN` | `NOT IN` | Not in list |
| `IS_NULL` | `IS NULL` | Is null |
| `BETWEEN` | `BETWEEN` | Range |
| `CONTAINS` | `LIKE %x%` | Contains substring |
| `STARTS_WITH` | `LIKE x%` | Starts with |
| `ENDS_WITH` | `LIKE %x` | Ends with |

### File Strategies

| Strategy | Behavior |
|----------|----------|
| `ALWAYS_OVERWRITE` | Always regenerated |
| `GENERATE_ONCE` | Created once, never touched |
| `GENERATE_BASE` | Base regenerated, user extends |
| `MERGE` | Smart merge with markers |

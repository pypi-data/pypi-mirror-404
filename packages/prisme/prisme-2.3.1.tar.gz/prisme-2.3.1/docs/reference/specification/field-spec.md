# FieldSpec Reference

Defines a single field within a model with type, validation, and UI settings.

## Basic Usage

```python
from prism import FieldSpec, FieldType

field = FieldSpec(
    name="email",
    type=FieldType.STRING,
    required=True,
    unique=True,
)
```

## Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Field name (snake_case) |
| `type` | `FieldType` | Field type |

### Core Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `required` | `bool` | `False` | Is the field required? |
| `unique` | `bool` | `False` | Must values be unique? |
| `indexed` | `bool` | `False` | Create database index? |
| `default` | `Any` | `None` | Default value |
| `default_factory` | `str` | `None` | Factory function name |

## Field Types

```python
from prism import FieldType

FieldType.STRING      # Short text (varchar)
FieldType.TEXT        # Long text
FieldType.INTEGER     # Integer numbers
FieldType.FLOAT       # Floating point
FieldType.DECIMAL     # Precise decimals
FieldType.BOOLEAN     # True/False
FieldType.DATETIME    # Date and time
FieldType.DATE        # Date only
FieldType.TIME        # Time only
FieldType.UUID        # UUID identifier
FieldType.JSON        # JSON data
FieldType.ENUM        # Enumeration
FieldType.FOREIGN_KEY # Foreign key reference
```

## Type-Specific Options

### String/Text Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_length` | `int` | Minimum length |
| `max_length` | `int` | Maximum length |
| `pattern` | `str` | Regex pattern |

```python
FieldSpec(
    name="username",
    type=FieldType.STRING,
    min_length=3,
    max_length=50,
    pattern=r"^[a-zA-Z0-9_]+$",
)
```

### Numeric Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_value` | `number` | Minimum value |
| `max_value` | `number` | Maximum value |

```python
FieldSpec(
    name="age",
    type=FieldType.INTEGER,
    min_value=0,
    max_value=150,
)
```

### Decimal Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `precision` | `int` | Total digits |
| `scale` | `int` | Decimal places |

```python
FieldSpec(
    name="price",
    type=FieldType.DECIMAL,
    precision=10,
    scale=2,
)
```

### Enum Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `enum_values` | `list[str]` | Allowed values |

```python
FieldSpec(
    name="status",
    type=FieldType.ENUM,
    enum_values=["active", "inactive", "pending"],
    default="pending",
)
```

### Foreign Key Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `references` | `str` | Referenced model name |
| `on_delete` | `str` | Delete behavior |

```python
FieldSpec(
    name="customer_id",
    type=FieldType.FOREIGN_KEY,
    references="Customer",
    on_delete="CASCADE",  # CASCADE, SET NULL, RESTRICT
)
```

### JSON Fields

| Parameter | Type | Description |
|-----------|------|-------------|
| `json_item_type` | `str` | Type for array items |

```python
# Generic JSON
FieldSpec(name="metadata", type=FieldType.JSON)

# Typed array - generates list[str]
FieldSpec(
    name="tags",
    type=FieldType.JSON,
    json_item_type="str",  # "str", "int", "float", "bool"
)
```

## Filter and Search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filterable` | `bool` | `False` | Can be used in filters |
| `sortable` | `bool` | `False` | Can be used for sorting |
| `searchable` | `bool` | `False` | Include in full-text search |
| `filter_operators` | `list[FilterOperator]` | `[]` | Available operators |

```python
from prism import FilterOperator

FieldSpec(
    name="name",
    type=FieldType.STRING,
    filterable=True,
    sortable=True,
    searchable=True,
    filter_operators=[
        FilterOperator.EQ,
        FilterOperator.ILIKE,
        FilterOperator.STARTS_WITH,
    ],
)
```

## Display Settings

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str` | Human-readable label |
| `description` | `str` | API documentation |
| `tooltip` | `str` | UI tooltip/help text |
| `hidden` | `bool` | Hide from generated UIs |

```python
FieldSpec(
    name="internal_id",
    type=FieldType.STRING,
    label="Internal ID",
    description="System-generated identifier",
    hidden=True,
)
```

## UI Widget Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `ui_widget` | `str` | Widget type |
| `ui_placeholder` | `str` | Placeholder text |
| `ui_widget_props` | `dict` | Additional props |

```python
FieldSpec(
    name="email",
    type=FieldType.STRING,
    ui_widget="email",
    ui_placeholder="name@example.com",
    ui_widget_props={
        "autocomplete": "email",
        "showValidation": True,
    },
)
```

### Available Widgets

| Widget | Use Case |
|--------|----------|
| `textarea` | Multi-line text |
| `richtext` | Rich text editor |
| `markdown` | Markdown editor |
| `datepicker` | Date selection |
| `datetimepicker` | Date and time |
| `timepicker` | Time only |
| `select` | Single choice |
| `multiselect` | Multiple choices |
| `radio` | Radio buttons |
| `checkbox` | Checkboxes |
| `switch` | Toggle switch |
| `slider` | Numeric slider |
| `rating` | Star rating |
| `color` | Color picker |
| `file` | File upload |
| `image` | Image upload |
| `password` | Password field |
| `email` | Email input |
| `url` | URL input |
| `phone` | Phone input |
| `currency` | Currency input |
| `percentage` | Percentage input |
| `tags` | Tag input |
| `json` | JSON editor |
| `code` | Code editor |

## Conditional Validation

### Conditional Required

```python
FieldSpec(
    name="mining_license",
    type=FieldType.STRING,
    required=False,
    conditional_required="sector == mining",
)
```

### Conditional Enum

```python
FieldSpec(
    name="job_title",
    type=FieldType.ENUM,
    enum_values=["manager", "engineer"],
    conditional_enum={
        "sector:mining": ["gold_miner", "silver_miner"],
        "sector:tech": ["developer", "designer"],
    },
)
```

## GraphQL Settings

| Parameter | Type | Description |
|-----------|------|-------------|
| `graphql_type` | `str` | Override GraphQL type |
| `graphql_deprecation` | `str` | Deprecation reason |

```python
FieldSpec(
    name="old_field",
    type=FieldType.STRING,
    graphql_deprecation="Use new_field instead",
)
```

## Complete Example

```python
from prism import FieldSpec, FieldType, FilterOperator

fields = [
    # Primary key (auto-generated)
    FieldSpec(
        name="id",
        type=FieldType.INTEGER,
        description="Unique identifier",
    ),

    # Required string with validation
    FieldSpec(
        name="email",
        type=FieldType.STRING,
        max_length=255,
        required=True,
        unique=True,
        indexed=True,
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        label="Email Address",
        ui_widget="email",
        filter_operators=[FilterOperator.EQ, FilterOperator.ILIKE],
    ),

    # Enum with default
    FieldSpec(
        name="status",
        type=FieldType.ENUM,
        enum_values=["active", "inactive", "pending"],
        default="pending",
        filter_operators=[FilterOperator.EQ, FilterOperator.IN],
    ),

    # Decimal for currency
    FieldSpec(
        name="balance",
        type=FieldType.DECIMAL,
        precision=12,
        scale=2,
        default=0.0,
        min_value=0,
        ui_widget="currency",
        ui_widget_props={"currency": "USD"},
    ),

    # JSON array
    FieldSpec(
        name="tags",
        type=FieldType.JSON,
        json_item_type="str",
        ui_widget="tags",
    ),

    # Foreign key
    FieldSpec(
        name="organization_id",
        type=FieldType.FOREIGN_KEY,
        references="Organization",
        on_delete="CASCADE",
        required=True,
    ),
]
```

## See Also

- [ModelSpec Reference](model-spec.md)
- [Exposure Config Reference](exposure-config.md)
- [Reference Index](../index.md)

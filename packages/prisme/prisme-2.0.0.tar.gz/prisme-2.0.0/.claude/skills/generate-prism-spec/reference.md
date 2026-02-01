# Prism Spec — Full API Reference

Complete reference for all configurable options in a Prism `StackSpec`.

## StackSpec

```python
StackSpec(
    # Required
    name: str,                              # kebab-case project name
    models: list[ModelSpec],

    # Metadata
    title: str | None = None,               # human-readable (defaults to formatted name)
    version: str = "1.0.0",
    description: str | None = None,

    # Global exposure defaults (applied to models that don't override)
    default_rest_exposure: RESTExposure = RESTExposure(),
    default_graphql_exposure: GraphQLExposure = GraphQLExposure(),
    default_mcp_exposure: MCPExposure = MCPExposure(),
    default_frontend_exposure: FrontendExposure = FrontendExposure(),

    # Configuration objects
    database: DatabaseConfig = DatabaseConfig(),
    graphql: GraphQLConfig = GraphQLConfig(),
    generator: GeneratorConfig = GeneratorConfig(),
    testing: TestingConfig = TestingConfig(),
    extensions: ExtensionConfig = ExtensionConfig(),
    widgets: WidgetConfig = WidgetConfig(),
    auth: AuthConfig = AuthConfig(),
    design: DesignSystemConfig = DesignSystemConfig(),
    traefik: TraefikConfig = TraefikConfig(),
)
```

## DatabaseConfig

```python
DatabaseConfig(
    dialect: str = "postgresql",        # "postgresql" or "sqlite"
    async_driver: bool = True,
    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)
```

## GraphQLConfig

```python
GraphQLConfig(
    enabled: bool = True,
    path: str = "/graphql",
    graphiql: bool = True,
    subscriptions_enabled: bool = True,
    subscription_path: str = "/graphql/ws",
    query_depth_limit: int = 10,
    query_complexity_limit: int = 100,
    enable_tracing: bool = False,
    enable_apollo_federation: bool = False,
    dataloader_cache_per_request: bool = True,
)
```

## GeneratorConfig

```python
GeneratorConfig(
    # Output roots
    backend_output: str = "packages/backend/src",
    frontend_output: str = "packages/frontend/src",

    # Backend paths
    models_path: str = "models",
    schemas_path: str = "schemas",
    services_path: str = "services",
    services_generated_path: str = "services/_generated",
    rest_path: str = "api/rest",
    graphql_path: str = "api/graphql",
    graphql_generated_path: str = "api/graphql/_generated",
    mcp_path: str = "mcp_server",
    tests_path: str = "tests",

    # Frontend paths
    types_path: str = "types",
    graphql_operations_path: str = "graphql",
    api_client_path: str = "api",
    components_path: str = "components",
    components_generated_path: str = "components/_generated",
    hooks_path: str = "hooks",
    pages_path: str = "pages",
    prism_path: str = "prism",
    frontend_tests_path: str = "__tests__",

    # Options
    generate_migrations: bool = True,
    overwrite_existing: bool = False,
    dry_run: bool = False,
)
```

## TestingConfig

```python
TestingConfig(
    generate_unit_tests: bool = True,
    generate_integration_tests: bool = True,
    generate_factories: bool = True,
    test_database: str = "sqlite",
    generate_graphql_tests: bool = True,
    generate_component_tests: bool = True,
    generate_hook_tests: bool = True,
    generate_e2e_tests: bool = False,
)
```

## ExtensionConfig

```python
ExtensionConfig(
    # Backend strategies
    services_strategy: FileStrategy = GENERATE_BASE,
    graphql_types_strategy: FileStrategy = GENERATE_BASE,
    graphql_queries_strategy: FileStrategy = GENERATE_BASE,
    graphql_mutations_strategy: FileStrategy = GENERATE_BASE,
    rest_endpoints_strategy: FileStrategy = GENERATE_BASE,

    # Frontend strategies
    components_strategy: FileStrategy = GENERATE_BASE,
    hooks_strategy: FileStrategy = GENERATE_ONCE,
    pages_strategy: FileStrategy = GENERATE_ONCE,

    # Assembly strategies
    schema_assembly: FileStrategy = MERGE,
    router_assembly: FileStrategy = MERGE,

    # Protected regions
    use_protected_regions: bool = True,
    protected_region_marker: str = "PRISM:PROTECTED",
)
```

FileStrategy values: `ALWAYS_OVERWRITE`, `GENERATE_ONCE`, `GENERATE_BASE`, `MERGE`

## WidgetConfig

```python
WidgetConfig(
    type_widgets: dict[str, str] = {},      # by FieldType
    ui_widgets: dict[str, str] = {},        # by ui_widget hint
    field_widgets: dict[str, str] = {},     # by "Model.field"
)
```

## CRUDOperations

```python
CRUDOperations(
    create: bool = True,
    read: bool = True,
    update: bool = True,
    delete: bool = True,
    list: bool = True,
)
```

## PaginationConfig

```python
PaginationConfig(
    style: PaginationStyle = OFFSET,    # OFFSET, CURSOR, LIMIT_OFFSET
    default_page_size: int = 20,
    max_page_size: int = 100,
)
```

## RESTExposure

```python
RESTExposure(
    enabled: bool = True,
    operations: CRUDOperations = CRUDOperations(),
    prefix: str | None = None,
    tags: list[str] = [],
    pagination: PaginationConfig = PaginationConfig(),
    # Field visibility per operation
    create_fields: list[str] | None = None,     # None = all
    update_fields: list[str] | None = None,
    read_fields: list[str] | None = None,
    list_fields: list[str] | None = None,
    # Security
    auth_required: bool = True,
    permissions: dict[str, list[str]] = {},
    # OpenAPI
    operation_ids: dict[str, str] = {},
)
```

## GraphQLExposure

```python
GraphQLExposure(
    enabled: bool = True,
    operations: CRUDOperations = CRUDOperations(),
    # Type naming
    type_name: str | None = None,
    input_type_name: str | None = None,
    query_name: str | None = None,
    query_list_name: str | None = None,
    # Relay pagination
    use_connection: bool = True,
    connection_name: str | None = None,
    # Mutations
    mutation_prefix: str | None = None,
    # Subscriptions
    enable_subscriptions: bool = False,
    subscription_events: list[str] = ["created", "updated", "deleted"],
    # Field visibility
    query_fields: list[str] | None = None,
    mutation_fields: list[str] | None = None,
    # Performance
    use_dataloader: bool = True,
    max_depth: int | None = None,
    max_complexity: int | None = None,
    # Security
    auth_required: bool = True,
    permissions: dict[str, list[str]] = {},
    # Relationships
    nested_queries: bool = True,
    # Documentation
    type_description: str | None = None,
    field_descriptions: dict[str, str] = {},
)
```

## MCPExposure

```python
MCPExposure(
    enabled: bool = True,
    operations: CRUDOperations = CRUDOperations(),
    tool_prefix: str | None = None,
    tool_descriptions: dict[str, str] = {},
    field_descriptions: dict[str, str] = {},
    expose_as_resource: bool = False,
    resource_uri_template: str | None = None,
)
```

## FrontendExposure

```python
FrontendExposure(
    enabled: bool = True,
    operations: CRUDOperations = CRUDOperations(),
    api_style: str = "graphql",             # "graphql", "rest", or "both"
    graphql_client: str = "urql",           # "urql" or "apollo"
    # Component generation
    generate_form: bool = True,
    generate_table: bool = True,
    generate_detail_view: bool = True,
    # Layout
    form_layout: str = "vertical",          # "vertical", "horizontal", "grid"
    table_columns: list[str] | None = None,
    # Navigation
    include_in_nav: bool = True,
    nav_label: str | None = None,
    nav_icon: str | None = None,            # Lucide icon name
    # Widgets
    widget_overrides: dict[str, str] = {},
)
```

## AuthConfig

```python
AuthConfig(
    enabled: bool = False,
    preset: Literal["jwt", "api_key", "authentik"] = "jwt",
    # API key
    api_key: APIKeyConfig = APIKeyConfig(),
    # Authentik
    authentik: AuthentikConfig = AuthentikConfig(),
    # JWT
    secret_key: str = "${JWT_SECRET}",
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 15,
    refresh_token_expire_days: int = 7,
    # Password policy
    password_min_length: int = 8,
    password_require_uppercase: bool = True,
    password_require_lowercase: bool = True,
    password_require_number: bool = True,
    password_require_special: bool = False,
    # Features
    require_email_verification: bool = False,
    allow_password_reset: bool = True,
    allow_signup: bool = True,
    session_strategy: Literal["jwt", "database"] = "jwt",
    # Rate limiting
    login_rate_limit: str = "5/15minutes",
    signup_rate_limit: str = "3/hour",
    # RBAC
    roles: list[Role] = [],
    default_role: str = "user",
    # User model
    user_model: str = "User",
    username_field: str = "email",          # "email" or "username"
    # Email
    email_backend: Literal["console", "smtp", "none"] = "console",
    smtp_host: str | None = None,
    smtp_port: int = 587,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    from_email: str = "noreply@example.com",
)
```

## APIKeyConfig

```python
APIKeyConfig(
    header: str = "Authorization",
    scheme: str = "Bearer",
    env_var: str = "API_KEY",
    allow_multiple_keys: bool = False,
)
```

## Role

```python
Role(
    name: str,
    permissions: list[str] = [],
    description: str | None = None,
)
```

## AuthentikConfig

```python
AuthentikConfig(
    version: str = "2024.2",
    subdomain: str = "auth",
    mfa: AuthentikMFAConfig = AuthentikMFAConfig(),
    self_signup: bool = True,
    email_verification: bool = True,
    client_id: str = "${AUTHENTIK_CLIENT_ID}",
    client_secret: str = "${AUTHENTIK_CLIENT_SECRET}",
    issuer_url: str = "${AUTHENTIK_ISSUER_URL}",
    webhook_secret: str = "${AUTHENTIK_WEBHOOK_SECRET}",
)
```

## AuthentikMFAConfig

```python
AuthentikMFAConfig(
    enabled: bool = True,
    methods: list[Literal["totp", "email", "webauthn"]] = ["totp", "email"],
)
```

## DesignSystemConfig

```python
DesignSystemConfig(
    theme: ThemePreset = NORDIC,            # NORDIC, MINIMAL, CORPORATE
    primary_color: str | None = None,       # CSS color override
    accent_color: str | None = None,
    dark_mode: bool = True,
    default_theme: str = "system",          # "light", "dark", "system"
    icon_set: IconSet = LUCIDE,             # LUCIDE, HEROICONS
    font_family: FontFamily = INTER,        # INTER, SYSTEM, GEIST
    custom_font_url: str | None = None,
    border_radius: BorderRadius = MD,       # NONE, SM, MD, LG, FULL
    enable_animations: bool = True,
)
```

## TraefikConfig

```python
TraefikConfig(
    enabled: bool = False,
    ssl_provider: Literal["letsencrypt", "manual", "none"] = "letsencrypt",
    ssl_email: str = "${SSL_EMAIL}",
    domain: str = "${DOMAIN}",
    dashboard_enabled: bool = False,
    dashboard_subdomain: str = "traefik",
)
```

## TemporalConfig

```python
TemporalConfig(
    timestamp_field: str,                   # required
    group_by_field: str | None = None,
    generate_latest_query: bool = True,
    generate_history_query: bool = True,
)
```

## FilterOperator values

`EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `LIKE`, `ILIKE`, `IN`, `NOT_IN`, `IS_NULL`, `BETWEEN`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`

## Conditional Validation

Fields support two conditional features:

- `conditional_required: str` — field becomes required when condition is true (e.g., `"sector == mining"`)
- `conditional_enum: dict[str, list[str]]` — allowed enum values change by condition (e.g., `{"sector:mining": ["gold_miner", "silver_miner"]}`)

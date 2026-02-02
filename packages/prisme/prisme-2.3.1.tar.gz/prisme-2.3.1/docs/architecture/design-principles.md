# Design Principles

The philosophy and rationale behind Prisme's architecture.

## Core Philosophy

> **"One spec, full spectrum."**

Define your data models once, get a complete full-stack application.

## Guiding Principles

### 1. Spec as Code

Specifications are written in Python, not configuration files.

**Why:**
- Full IDE support (autocomplete, type checking, navigation)
- Programmable (loops, conditionals, functions)
- Testable (unit test your specs)
- Versionable (diff-friendly, merge-friendly)

**Example:**
```python
# Not this (YAML)
# models:
#   - name: Customer
#     fields:
#       - name: email
#         type: string

# But this (Python)
ModelSpec(
    name="Customer",
    fields=[
        FieldSpec(name="email", type=FieldType.STRING),
    ],
)
```

### 2. Generate Base, Extend User

Generated code is separated from customizations.

**Pattern:**
```
services/
├── _generated/           # Regenerated every time
│   └── customer_service.py
└── customer_service.py   # Your code, never touched
```

**Why:**
- Safe regeneration without losing work
- Clear separation of concerns
- Easy to identify what's generated vs custom
- Inheritance provides clean extension points

### 3. Build-Time Generation

Code is generated at build time, not runtime.

**Why:**
- **Inspectable**: You can read and understand all generated code
- **Debuggable**: Set breakpoints anywhere
- **Optimizable**: Compiler/bundler can optimize
- **No Magic**: No runtime metaprogramming surprises

### 4. Type Safety Everywhere

End-to-end type safety from database to frontend.

**Flow:**
```
Spec → SQLAlchemy Models → Pydantic Schemas → TypeScript Types
```

**Why:**
- Catch errors at compile time
- Better IDE experience
- Self-documenting APIs
- Refactoring confidence

### 5. Selective Exposure

Fine-grained control over what's exposed where.

**Example:**
```python
# Expose to REST and frontend, but not MCP
ModelSpec(
    name="InternalMetrics",
    rest=RESTExposure(enabled=True, auth_required=True),
    graphql=GraphQLExposure(enabled=False),
    mcp=MCPExposure(enabled=False),
    frontend=FrontendExposure(enabled=True),
)
```

**Why:**
- Not everything should be accessible everywhere
- Security by design
- Smaller API surface where appropriate

### 6. Convention Over Configuration

Sensible defaults with opt-in customization.

**Default behaviors:**
- Field names → database column names (snake_case)
- Model names → table names (pluralized, snake_case)
- Endpoints → RESTful patterns
- Pagination → offset-based, 20 items

**Why:**
- Quick start with minimal config
- Consistency across projects
- Less boilerplate
- Still fully customizable

### 7. Async-First

All I/O operations are asynchronous.

**Why:**
- Better resource utilization
- Handle more concurrent requests
- Modern Python best practice
- Consistency throughout codebase

### 8. Extensibility Without Modification

Extend behavior without modifying generated code.

**Extension points:**
- Service class inheritance
- Component composition
- Lifecycle hooks
- Widget system

**Why:**
- Upgrades don't break customizations
- Clean separation of concerns
- Predictable behavior

## Trade-offs

### Code Duplication vs Abstraction

**Choice:** Generate explicit code rather than abstract frameworks.

**Trade-off:**
- More generated files
- Some repetition in patterns
- But: Simpler debugging, easier understanding

### Flexibility vs Simplicity

**Choice:** Opinionated defaults with escape hatches.

**Trade-off:**
- May not fit every use case perfectly
- Some constraints on architecture
- But: Fast start, consistent patterns

### Generation vs Runtime

**Choice:** Build-time generation over runtime magic.

**Trade-off:**
- Regeneration needed for spec changes
- More files in repo
- But: Better performance, debuggability

## Anti-Patterns We Avoid

### 1. Magic Strings

```python
# Bad: Magic strings
permissions=["admin.users.create"]

# Good: Type-safe
permissions={"create": [Role.ADMIN]}
```

### 2. Configuration Hell

```python
# Bad: Deep configuration nesting
config["database"]["connection"]["pool"]["size"]

# Good: Flat, typed configuration
DatabaseConfig(pool_size=10)
```

### 3. Runtime Metaprogramming

```python
# Bad: Dynamic class creation at runtime
type("User", (Base,), {"__tablename__": "users"})

# Good: Generated static code
class User(Base):
    __tablename__ = "users"
```

### 4. Implicit Behavior

```python
# Bad: Hidden side effects
@auto_save  # Saves on every attribute access?
class User: ...

# Good: Explicit operations
await user_service.update(id, data)
```

## Comparison with Alternatives

### vs Traditional Frameworks (Django, Rails)

| Aspect | Traditional | Prisme |
|--------|-------------|--------|
| Models | Runtime ORM | Generated ORM |
| Admin | Generic UI | Generated UI |
| API | Manual or magic | Generated |
| Types | Optional | Required |

### vs API Generators (OpenAPI, GraphQL-first)

| Aspect | API Generators | Prisme |
|--------|----------------|--------|
| Source | API schema | Data models |
| Backend | Stubs only | Full implementation |
| Frontend | Clients only | Full components |
| Database | Manual | Generated |

### vs Low-Code Platforms

| Aspect | Low-Code | Prisme |
|--------|----------|--------|
| Control | Limited | Full |
| Customization | Restricted | Unlimited |
| Code Access | Hidden | Full |
| Deployment | Platform | Anywhere |

## Summary

Prisme's design prioritizes:

1. **Developer experience** through type safety and IDE support
2. **Maintainability** through clear separation of generated and custom code
3. **Transparency** through build-time generation and explicit code
4. **Flexibility** through selective exposure and extension points
5. **Performance** through async-first architecture

These principles guide all development decisions and ensure Prisme remains a productive, understandable, and maintainable tool.

## See Also

- [Architecture Overview](index.md)
- [Generator Architecture](generators.md)
- [Code Generation Guide](../user-guide/code-generation.md)

# V2 Spec/Config Exploration — Wind Pipeline

**Date:** 2026-01-30
**Purpose:** Convert the wind-pipeline v1 spec + config into the v2 PRD format to surface gaps and friction.

---

## What went smoothly

1. **Model/Field/Relationship core** — The v1 `ModelSpec`/`FieldSpec`/`RelationshipSpec` maps cleanly to v2 `Model`/`Field`/`Relationship`. No information loss for the domain-truth parts (fields, types, constraints, relationships).

2. **Operations simplification** — Replacing `CRUDOperations(create=False, update=False, delete=False, list=True, read=True)` with `operations=["read", "list"]` is a clear readability win. Less boilerplate.

3. **Spec → Config extraction** — The following moved out of spec cleanly:
   - `PaginationConfig` (style, default_page_size, max_page_size) → `[exposure.defaults]`
   - `DatabaseConfig` → `[database]`
   - `GraphQLConfig` → `[exposure.graphql]`
   - `GeneratorConfig` → `[generation]`
   - `TestingConfig` → `[generation.testing]`
   - `ExtensionConfig` → `[generation.extensions]`
   - `DesignSystemConfig` → `[design]`
   - `AuthConfig` → `[auth]`
   - `WidgetConfig` (global mappings) → `[design.widgets]` + `[design.field_widgets]`

4. **Config readability** — `prisme.toml` is substantially easier to scan than the Python `PrismConfig` + nested `StackSpec` config. TOML sections map well to the concern categories.

---

## Issues and open questions

### Issue 1: `overrides` is a catch-all bag

The PRD says per-model `overrides` is for "deviations from config defaults (e.g., a specific page_size)". In practice, the wind-pipeline needs overrides for:

- **Delivery**: `page_size`, `rest_tags`, `list_fields`
- **Frontend UI**: `nav_label`, `nav_icon`, `table_columns`
- **MCP**: `mcp_tool_prefix`, `mcp_tool_descriptions`

These are three distinct categories crammed into one `dict`. This will cause:
- No schema validation (it's just `dict[str, Any]`)
- No autocomplete/IDE support
- Unclear which keys are valid
- Easy to typo a key silently

**Recommendation:** Either (a) define typed override categories (`overrides.delivery`, `overrides.frontend`, `overrides.mcp`) or (b) promote the most common ones to named Model fields (`mcp_tool_prefix`, `nav_icon`, etc.) and keep `overrides` only for rare deviations like `page_size`.

### Issue 2: Where do `ui_widget` and `ui_widget_props` live?

The PRD says "UI widget choices" belong in config, not spec. But `ui_widget="slider"` with `ui_widget_props={"min": 10, "max": 200, "step": 5}` is deeply field-specific — it doesn't make sense as a config default.

In the exploration I kept `ui_widget` and `ui_widget_props` on `Field`, which contradicts section 5.2's exclusion list. The PRD's `[design.field_widgets]` handles the mapping case (e.g., "use LatitudeInput for this field") but not the props case.

**Recommendation:** Keep `ui_widget` and `ui_widget_props` on `Field` in spec. They are domain-adjacent (a slider with min/max bounds is describing the field's semantics). Move only the global widget *type registry* to config (`[design.widgets]`). Update PRD section 5.2 to clarify.

### Issue 3: `hidden` field attribute not addressed

The v1 spec uses `hidden=True` on fields like `terrain_data` and `api_key` to exclude them from default list/read views. The PRD mentions `read_fields` / `list_fields` as the visibility mechanism, but `hidden` is more ergonomic for "this field exists but don't show it by default."

**Recommendation:** Keep `hidden` as syntactic sugar. A hidden field is excluded from list_fields and read_fields unless explicitly included. This avoids having to enumerate all visible fields just to exclude one.

### Issue 4: `json_item_type` not in PRD

The v1 spec uses `json_item_type="int"` to hint at JSON array element types (for `color_rgb`). The v2 `Field` definition in the PRD doesn't mention this. Minor, but should be documented.

### Issue 5: `back_populates` and `cascade` on Relationship

The PRD's `Relationship` example is minimal (`target`, `type`). The wind-pipeline uses `back_populates` and `cascade` extensively. These are SQLAlchemy-specific but practically necessary. The PRD should acknowledge them as valid Relationship attributes.

### Issue 6: `timestamps` as separate from `soft_delete`

The PRD example uses `soft_delete=True` but doesn't show `timestamps=True`. The wind-pipeline has models with timestamps but no soft delete (WindSector), and models with neither (WindRoseSector). These should be independent toggles. The PRD should show both.

### Issue 7: Config sections not in PRD

The exploration needed TOML sections not covered in the PRD example:

- `[exposure.graphql]` — GraphQL-specific settings (path, graphiql, subscriptions, query_depth_limit, use_connection, use_dataloader)
- `[exposure.frontend]` — Frontend generation defaults (api_style, generate_form, etc.)
- `[generation.testing]` — Test generation settings
- `[generation.extensions]` — Extension/strategy settings
- `[design]` — Design system settings (theme, dark_mode, icon_set, border_radius)
- `[design.widgets]` / `[design.field_widgets]` — Widget mappings

The PRD's config example is too sparse. These sections should be documented to avoid "where does this go?" confusion — which is exactly the problem v2 is solving.

### Issue 8: `pattern` field validation

The v1 spec uses `pattern=r"^#[0-9A-Fa-f]{6}$"` for regex validation on fields. Not mentioned in PRD's Field definition but clearly domain truth. Should be documented.

### Issue 9: No `label` / `description` / `ui_placeholder` in PRD Field

The PRD's `Field` only shows `(name, type=, required=, default=, unique=)`. The wind-pipeline uses `label`, `description`, and `ui_placeholder` on nearly every field. These are domain metadata (how humans understand the field) and belong in spec. The PRD should list them.

### Issue 10: `on_delete` on foreign key fields

The PRD doesn't mention `on_delete` behavior for foreign key fields. The wind-pipeline uses CASCADE and SET NULL. This is domain-level referential integrity, not infrastructure.

---

## Structural observations

### What got simpler
- Removing `RESTExposure`, `GraphQLExposure`, `MCPExposure`, `FrontendExposure` as separate objects per model. The v2 approach (global config + per-model overrides) reduces boilerplate significantly. The v1 spec repeats `GraphQLExposure(enabled=True, use_connection=True, use_dataloader=True)` on every model — in v2 this is a single config line.

### What got more ambiguous
- The `overrides` dict is doing too much work. Without a schema, it's unclear what's valid.
- The line between "domain truth in spec" and "delivery in config" is blurry for UI hints (nav_icon, table_columns). These describe the model's presentation, not infrastructure, but the PRD's language ("UI widget choices → config") could be read either way.

### Migration complexity
- The v1 → v2 migration for this project would need to:
  1. Parse `StackSpec` constructor args and extract config-level settings → write `prisme.toml`
  2. Parse `prism.config.py` → merge into `prisme.toml`
  3. Rewrite `ModelSpec` → `Model`, `FieldSpec` → `Field`, etc.
  4. Collapse per-model exposure objects into `overrides` dict
  5. Move per-field `filter_operators` defaults to config, keep per-field overrides in spec
- This is doable but non-trivial. The PRD's decision to skip v1 migration tooling (decision #2) is reasonable given no external users, but documenting the manual steps would help.

---

## Summary

The v2 design works well for the core domain model. The main friction is around the **overrides bag** (issue #1) and **UI-related field attributes** (issues #2, #9) that don't fit neatly into the spec-vs-config split. Addressing these before implementation will prevent the same "where does this go?" confusion that v2 is trying to eliminate.

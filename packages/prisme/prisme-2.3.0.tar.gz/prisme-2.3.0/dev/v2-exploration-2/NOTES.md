# V2 Spec/Config Exploration 2 — Wind Pipeline (Post-PRD v2)

**Date:** 2026-01-31
**Purpose:** Re-convert the wind-pipeline spec using the final PRD v2 design: two spec files, typed overrides, slim `prisme.toml`. Compare against exploration-1 to validate that the PRD revisions actually solved the issues raised.

---

## Changes from Exploration 1

The PRD was updated after exploration-1 to address the 10 issues raised. This exploration tests whether those changes work in practice.

| Exploration 1 | Exploration 2 |
|---|---|
| Fat `prisme.toml` (~96 lines) with all project config | Slim `prisme.toml` (~13 lines), generator policy only |
| No `specs/project.py` | `specs/project.py` with `ProjectSpec` Pydantic class |
| Untyped `overrides: dict` on Model | Typed `DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides` |
| Project config in TOML sections | Project config in Python with full IDE support |

---

## Issue-by-issue validation

### Issue 1 (overrides bag) — RESOLVED

The typed sub-models (`DeliveryOverrides`, `FrontendOverrides`, `MCPOverrides`) cleanly separate the three categories that were crammed into one dict. Writing the wind-pipeline spec with them felt natural:

```python
delivery_overrides=DeliveryOverrides(page_size=25, rest_tags=["wind-data"]),
frontend_overrides=FrontendOverrides(nav_label="Wind Data Jobs", nav_icon="wind", ...),
mcp_overrides=MCPOverrides(tool_prefix="windjob", tool_descriptions={...}),
```

Each override category is independently optional. Models that only need MCP customization don't need to touch `DeliveryOverrides` or `FrontendOverrides`. This is a clear improvement over the untyped dict.

**Minor concern:** Three keyword arguments on every model that uses overrides is verbose. For the wind-pipeline (9 models), most models use all three. The verbosity is acceptable because it's explicit and IDE-completable, but it's worth noting.

### Issue 2 (ui_widget placement) — RESOLVED

PRD v2 explicitly keeps `ui_widget` and `ui_widget_props` on `Field` in the domain spec. This was the right call. Writing `Field("radius", ..., ui_widget="slider", ui_widget_props={"min": 100, "max": 5000})` feels correct — the slider bounds are part of what the field *means*.

The global widget type registry (`DesignConfig.widgets.custom_widgets`) now lives in `specs/project.py`, which is the right place for "CoordinatesInput is the widget for the `coordinates` type." The field-level `ui_widget="coordinates"` stays in domain spec.

### Issue 3 (hidden) — RESOLVED

PRD v2 documents `hidden` as syntactic sugar. Used it on `terrain_data`, `buildings_data`, `sectors_data`, `download_path`, `timeseries_file`, `qc_flags`, `api_key`. Works exactly as expected — much more ergonomic than enumerating visible fields.

### Issue 4 (json_item_type) — RESOLVED

PRD v2 now documents `json` field type with `json_item_type`. Used on `LandCoverType.color_rgb` with `json_item_type="int"`.

### Issue 5 (back_populates / cascade) — RESOLVED

PRD v2 documents `back_populates`, `cascade`, `on_delete` on Relationship. The full example in section 5.2 shows them.

### Issue 6 (timestamps independent) — RESOLVED

PRD v2 shows `soft_delete` and `timestamps` as independent toggles with `Model behaviors: soft_delete, timestamps (independent toggles)`. Used both patterns in the wind-pipeline: `WindSector` has `timestamps=True` but no `soft_delete`, `WindRoseSector` has neither.

### Issue 7 (config sections) — RESOLVED (via project spec)

This was the biggest structural change. Instead of adding more TOML sections to `prisme.toml`, the PRD moved all project config to `specs/project.py`. The result:

- `prisme.toml` is now 13 lines — truly boring
- `specs/project.py` is ~100 lines with full Pydantic typing
- GraphQL config, testing config, extensions, design, auth — all in project spec

This is better than the exploration-1 approach. Having `ExposureConfig`, `GraphQLConfig`, `TestingConfig` etc. as typed Pydantic sub-models means IDE autocomplete works, typos are caught, and the file is self-documenting.

### Issues 8-10 (pattern, label/description, on_delete) — RESOLVED

All documented in PRD v2 Field/Relationship definitions.

---

## New observations from this exploration

### Observation 1: Project spec duplicate `graphql` key

The PRD example for `ExposureConfig` has two `graphql` keys:
```python
exposure=ExposureConfig(
    graphql=True,            # enable/disable toggle
    ...
    graphql=GraphQLConfig(   # detailed config
```

This is invalid Python — duplicate keyword argument. Needs resolution. Options:
- (a) `graphql_enabled=True` + `graphql_config=GraphQLConfig(...)` — ugly but unambiguous
- (b) `graphql=GraphQLConfig(enabled=True, ...)` — the boolean becomes a field on the config object
- (c) `graphql=True` enables with defaults, `graphql=GraphQLConfig(...)` enables with overrides (union type)

Option (c) is the most ergonomic but requires Pydantic validator magic. Option (b) is simplest.

### Observation 2: `prisme.toml` is almost too slim

At 13 lines, `prisme.toml` is barely worth existing as a separate file. Its content:
- `prisme_version` — could be inferred from installed package
- `config_version` — meta, needed for migration
- `spec_path` / `project_path` — convention-based defaults would eliminate these
- `generation.mode` — could default to "strict"
- `generation.auto_format` — could default to true
- `tools.python_manager` / `package_manager` — could be detected from lockfiles

**Not a problem** — the file being small is a feature, not a bug. It means the PRD successfully moved project concerns out of config. But consider whether convention-over-configuration could make even this file optional for `prisme create` projects (detect everything, write the file as documentation rather than necessity).

### Observation 3: Two spec files is the right split

Converting the wind-pipeline confirmed the two-file split is correct. While editing `specs/models.py`, I never once needed to think about database engine, auth provider, or frontend framework. While editing `specs/project.py`, I never needed to think about field types or relationships. The concerns are genuinely orthogonal.

The test from the PRD holds: "If I copy `specs/` to a different machine with prisme installed, should the same project come out?" Yes.

### Observation 4: `list_fields` placement is awkward

`list_fields` is currently on `Model` directly (domain spec), but it feels like it belongs in `FrontendOverrides` or `DeliveryOverrides`. The list of fields to show in a list view is a presentation concern, not domain truth. The PRD puts it in domain spec under "per-model field visibility" — but `read_fields`, `create_fields`, `update_fields`, `list_fields` are all about *what the API returns*, which is delivery.

Counter-argument: these control API schema shape, which affects consumers beyond just the frontend. A `hidden=True` field excluded from `read_fields` means the API never returns it — that's a domain-level decision about data exposure.

**Verdict:** Keep in domain spec for now. The "is this domain or delivery?" question is genuinely ambiguous for field visibility. Keeping it close to the field definitions (same file) makes it easy to reason about.

### Observation 5: Missing `include_in_nav` on FrontendOverrides

The v1 spec has `include_in_nav=False` on several models (Site, WindSector, WindRoseSector, LandCoverType) to control sidebar navigation. The PRD's `FrontendOverrides` doesn't list this field. It should — it's the most common frontend override after `nav_label` and `nav_icon`.

Without it, there's no way to say "generate pages for this model but don't put it in the nav." The wind-pipeline needs this for child models accessed via parent detail views.

### Observation 6: No `generate_form` / `generate_table` / `generate_detail_view` per model

The v1 spec has per-model control over which frontend components to generate (e.g., `WindSector` gets `generate_table=True` but `generate_form=False` and `generate_detail_view=False`). The v2 `FrontendOverrides` in the PRD only has `nav_icon`, `nav_label`, `table_columns`, `form_layout`, `list_fields`.

These generation toggles need a home. Options:
- (a) Add to `FrontendOverrides` — `generate_form`, `generate_table`, `generate_detail_view`
- (b) Derive from `operations` — if no `create`/`update`, skip form; if no `read`, skip detail view
- (c) Global default in project spec + per-model override

Option (b) is appealing: if `operations=["read", "list"]`, the generator infers no form is needed. But it's not always true — you might want a read-only detail view without a table, or a table without a detail view. Option (a) is safest.

---

## Summary

The PRD v2 revisions successfully addressed all 10 issues from exploration-1. The two-file spec split and typed overrides are clear improvements. The conversion was smoother this time — less guessing about where things go.

New issues surfaced and resolved (PRD updated):

1. **`graphql` duplicate key** in `ExposureConfig` — **Resolved**: each exposure channel is now a config object with an `enabled` flag. `rest=RESTConfig(enabled=True)`, `graphql=GraphQLConfig(enabled=True, ...)`, `mcp=MCPConfig(enabled=True)`. No more duplicate keywords. Omitting the key or `enabled=False` disables the channel. Added as resolved decision #21.

2. **`include_in_nav`** missing from `FrontendOverrides` — **Resolved**: added to `FrontendOverrides`. Used on Site (`include_in_nav=False`, accessed via project), WindSector, WindRoseSector (accessed via parent detail views), and LandCoverType (reference data). Added as part of resolved decision #22.

3. **Frontend generation toggles** (`generate_form`, `generate_table`, `generate_detail_view`) — **Resolved**: added to `FrontendOverrides`. Defaults are derived from `operations` (no `create`/`update` implies `generate_form=False`) but can be overridden explicitly. WindSector uses `generate_form=False, generate_detail_view=False` to get table-only views. Added as resolved decision #22.

4. **`list_fields` placement** — kept in domain spec. The "is this domain or delivery?" question is genuinely ambiguous for field visibility, and keeping it close to field definitions makes it easy to reason about. Not worth relocating.

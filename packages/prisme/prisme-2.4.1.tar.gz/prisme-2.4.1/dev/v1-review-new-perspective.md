But actually the current version of prisme is not having configuration of it self in spec, but its a spec for generation of a configuration of the target project

Got it — that’s an important distinction, and it *changes* what “Spec vs Config” should mean in Prisme.

Right now your “spec” is effectively:

> **a generation spec that produces the target project’s configuration/code**
> (not the “domain spec” of the target project itself)

So the clean separation becomes:

* **Prisme Config** = how Prisme behaves (generator policy, defaults, targets, safety)
* **Generation Spec** = what to generate (target project shape/config/code)
* **Target Project Config** = runtime config of the generated app (FastAPI settings, DB URLs, auth endpoints, etc.)

Your earlier confusion still applies — it’s just that we should name the layers correctly.

Below is a corrected model that matches your architecture and resolves the confusion without pretending the spec is “domain truth”.

---

## A better 3-layer contract for Prisme (matching reality)

### 1) Prisme CLI

**Execution-time only**

* run generate, plan, apply, test
* choose paths, verbosity, dry-run
* never encode durable intent

### 2) Prisme Config (`prisme.toml`)

**Generator policy + defaults**

* which generators are enabled (REST/GraphQL/MCP/UI)
* what templates/targets are used
* repo layout policy (generated/ vs custom/)
* strict vs lenient mode
* versioning + migration behavior
* formatting policy
* extension hook policy

This is *Prisme’s* configuration.

### 3) Generation Spec (Python DSL)

**Specifies the output target project**

* models/fields/endpoints/UI exposure
* how to generate target-project modules/config
* any “target project configuration” you want generated (e.g., auth provider wiring), expressed as part of the generation spec

This is not “Prisme config”; it’s a **blueprint of the generated project**.

### 4) Target Project Config (generated artifact)

The output:

* `config.py`, `database.py`, etc.
* `.env.example`, helm/terraform, etc.
* runtime config + wiring

This is what your generation spec emits.

So: **the spec generates the app’s config** — and Prisme config controls the generator itself.

---

## Concretely: what should move where (with your architecture)

### Keep in Generation Spec (because it describes the target project)

* which models exist
* CRUD/exposure per model (REST/GraphQL/MCP/UI)
* model-level UI widgets / filter operators (if you want those generated)
* naming conventions / prefixes that are part of the target project surface
* anything that changes the *shape* of the generated app

### Move into Prisme Config (because it’s generator policy/defaults)

* which generators run by default (rest/graphql/mcp/frontend)
* output paths / folder layout policy
* strictness (fail on unknown keys, etc.)
* formatting and canonical ordering
* plan/apply behavior
* “never write outside generated/”
* dependency/tooling choices (poetry/uv/pnpm) if you want them standardized per repo
* versioning + migration policies

### Keep in CLI flags (execution-time only)

* `--spec path`
* `--config path`
* `--dry-run`
* `--diff`
* `--watch`
* `--verbose`
* `--force`
* `--target-env dev|prod`

---

## How to reduce confusion: rename and document the artifacts

Right now “spec” vs “config.py” vs “config” is overloaded.

A very practical fix is to **rename the files and vocabulary**:

* **Prisme Config:** `prisme.toml`
* **Generation Spec:** `prisme.spec.py` (or `project.spec.py`)
* **Generated target runtime config:** `app/config.py` (or `src/app_settings.py`)

And in docs always refer to:

* “Prisme config”
* “Generation spec”
* “Generated project config”

That alone will remove a lot of mental friction.

---

## Versioning in this corrected model

Yes — still do versioning, but now it’s even clearer:

1. **Prisme config schema version**
   `config_version = 1`

2. **Generation spec schema version**
   `PRISME_GENERATION_SPEC_VERSION = 2`

3. (Optional) **Target project config version**
   You might not need this; you can treat it as derived output, tracked via the manifest.

Plus: a **manifest** in generated output that records the versions/hashes used.

---

## The key “contract” sentence (updated)

> The **generation spec** defines *what the generated project looks like*.
> The **Prisme config** defines *how Prisme performs generation safely and consistently*.
> The **CLI** just runs it.

---

If you want, I can update the earlier refactor spec text into a new copy-paste version that uses your correct terminology (Prisme config vs generation spec vs target project config), so it’s aligned with the current implementation philosophy.

Yes please

Perfect — here is a **clean, corrected, copy-pasteable combined refactor spec**, rewritten to **match your actual architecture**:

* the spec is a **generation spec**
* it **produces** the target project’s configuration
* Prisme itself has its **own config**
* terminology is unambiguous

You can paste this as an **ADR / refactor proposal / GitHub issue** as-is.

---

# Prisme Refactor Spec

**Generation Spec vs Prisme Config vs CLI (with Versioning & Safety)**

## Goal

Refactor Prisme to remove conceptual ambiguity by explicitly separating:

1. **Prisme configuration** (how the generator behaves)
2. **Generation specification** (what the target project should look like)
3. **Generated target project configuration** (runtime output)

The refactor must:

* preserve current capabilities
* improve regeneration safety
* enable schema evolution via versioning
* make ownership boundaries explicit
* reduce cognitive load for new users

---

## Core Mental Model (Authoritative)

> **CLI = execution**
> **Prisme config = generator policy**
> **Generation spec = blueprint of the generated project**
> **Generated config = runtime output**

Or, in one sentence:

> The **generation spec** defines *what is generated*.
> The **Prisme config** defines *how Prisme generates it*.
> The **CLI** just runs the process.

---

## Layer Definitions and Responsibilities

### 1. Prisme CLI

**Purpose:** execution-time behavior only.

#### Owns

* command selection (`generate`, `plan`, `apply`, `test`)
* paths to spec/config
* verbosity
* dry-run / diff
* watch mode
* force
* target environment selection (dev/prod)

#### Must NOT own

* durable project intent
* exposure choices
* auth strategy
* database choice
* generator selection

CLI flags must never change the *shape* of generated output.

---

### 2. Prisme Config (`prisme.toml`)

**Purpose:** configure Prisme itself (generator policy & defaults).

This is **not** target-project configuration.

#### Owns

* which generators are enabled by default (REST / GraphQL / MCP / frontend)
* output folder layout policy (`generated/` vs user-owned)
* strict vs lenient mode
* formatting & canonicalization rules
* plan/apply behavior
* dependency/tooling policy (poetry / uv / pnpm)
* versioning & migration behavior
* safety invariants (“never write outside generated/”)

#### Example

```toml
prisme_version = "0.4.0"
config_version = 1

[generation]
mode = "strict"
layout = "generated-first"

[generators]
rest = true
graphql = false
mcp = true
frontend = true

[formatting]
auto_format = true
```

#### Rules

* `prisme.toml` is mandatory (empty is valid)
* CLI flags may only *override execution behavior*, not config meaning
* Config is versioned and migratable

---

### 3. Generation Spec (Python DSL)

**Purpose:** blueprint describing the **target project to be generated**.

This is where you describe:

* models
* fields
* endpoints
* UI surfaces
* auth wiring
* target-project configuration that should be generated

This spec **produces**:

* code
* runtime config files
* infra templates
* UI scaffolding

#### Owns

* domain models
* relationships
* CRUD semantics
* exposure per model (REST / GraphQL / MCP / UI)
* UI widgets & filters *if they are part of the generated surface*
* naming conventions & prefixes that affect the generated API

#### Does NOT own

* how Prisme internally performs generation
* formatting policy
* safety rules
* folder ownership rules

#### Versioning

```python
PRISME_GENERATION_SPEC_VERSION = 2
```

Each generation spec explicitly declares its schema version.

---

### 4. Generated Target Project Config (Output)

**Purpose:** runtime configuration of the generated app.

Examples:

* `config.py`
* `database.py`
* `.env.example`
* auth wiring
* infra templates

#### Rules

* treated as **generated artifacts**
* never edited directly unless explicitly documented as extension points
* overwritten on regeneration

---

## Ownership Boundaries (Hard Rule)

The repo must make ownership obvious:

```
/generated        # fully replaceable
/app              # user-owned code
/prisme.toml      # Prisme config
/project.spec.py  # generation spec
```

Rules:

* generators may only write inside `/generated`
* user code is never touched
* editing generated files is unsupported and detectable

---

## Versioning & Migration

### Versioned Artifacts

* **Prisme config schema version** (`config_version`)
* **Generation spec schema version** (`PRISME_GENERATION_SPEC_VERSION`)
* **Prisme generator version** (`prisme_version`)

These evolve independently.

---

### Migration Command

```
prisme migrate
prisme migrate --dry-run
```

Responsibilities:

* detect outdated schemas
* auto-migrate when safe
* fail loudly with guidance when not
* never silently change behavior

`generate` must refuse unsupported versions.

---

## Deterministic & Safe Generation

Generation must be:

* order-stable
* formatting-stable
* path-stable

Optional but recommended:

* canonical sorting
* automatic formatting
* stable IDs for UI elements

---

## Plan / Apply Workflow

Introduce two-phase generation:

```
prisme plan
prisme apply
```

Plan outputs:

* files to be created/modified
* diff summary
* safety classification

Apply performs writes.

This directly addresses regeneration anxiety.

---

## Manifest / Provenance

Each generation writes:

```
generated/.prisme-manifest.json
```

Containing:

* prisme_version
* config_version
* generation_spec_version
* hashes of spec & config
* enabled generators
* timestamp

Used for debugging, CI, and support.

---

## Extension Points (First-Class)

Customization must happen via explicit hooks, not ad-hoc edits.

Examples:

* backend dependency overrides
* router extension modules
* policy hooks (auth/authorization)
* frontend component overrides
* MCP tool hooks

These hooks are preserved across regeneration.

---

## Doctor Command

```
prisme doctor
```

Checks:

* missing or outdated versions
* broken ownership boundaries
* edited generated files
* mismatched tooling

Usable locally and in CI.

---

## Regeneration Guarantees (Contract)

Golden tests must prove:

* regenerate preserves user-owned code
* spec changes only affect generated artifacts
* Prisme config changes only affect generation behavior
* migrations are explicit and safe

These tests are part of CI and treated as a contract.

---

## Non-Goals

This refactor does NOT aim to:

* redesign the DSL
* remove generators
* enforce frameworks
* add product features

The goal is **clarity, safety, and evolvability**.

---

## Success Criteria

This refactor is successful when:

* users know exactly where a change belongs
* regeneration is boring and safe
* upgrades are explicit and guided
* Prisme feels predictable and trustworthy

---

If you want next, I can:

* convert this into a **formal ADR**
* split it into **phased implementation milestones**
* map this directly onto your **current repo structure** and flag concrete TODOs

This version is now **fully aligned with how Prisme actually works** and removes the last conceptual mismatch.

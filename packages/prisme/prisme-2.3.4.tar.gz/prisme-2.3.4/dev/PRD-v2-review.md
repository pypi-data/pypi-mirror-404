# PRD v2 Review — User Perspective

**Reviewer:** Claude (prompted by Lasse)
**Date:** 2026-01-30

---

## What works well

**The mental model is clear.** The three-layer split (CLI = when/how, Spec = what, Config = where/defaults) with the decision table in section 4 is genuinely useful. A user could tape that table to their monitor and always know where to put things.

**Two-phase generation is the right call.** The `create` vs `generate` separation with `generated/` as the only blast radius directly solves regeneration anxiety. "Run `prisme generate` whenever you want, it only touches `generated/`" is a one-sentence pitch that builds trust.

**The precedence chain is simple.** CLI > Config > Spec defaults — no ambiguity.

---

## Concerns and gaps

### 1. The spec DSL is still complex for "under 2 minutes"

The example spec in section 5.2 has `overrides`, `temporal`, `nested_create`, `before_create`, `after_create`, lifecycle hooks, `filter_operators`, `soft_delete` — all on two models. A new user seeing this will not feel simplicity. The PRD claims success when users understand the mental model in under 2 minutes, but the spec surface area is large. Consider what a minimal spec looks like and lead with that.

### 2. No story for "I need to eject"

What happens when a user outgrows prisme? There's no mention of ejecting from the framework — making `generated/` into normal code the user fully owns. Even if you never build it, acknowledging it reduces lock-in anxiety.

### 3. Extension discovery is hand-wavy

Section 7 says "Generated code auto-discovers and imports them" but doesn't explain how. If I create `app/backend/extensions/routers.py`, how does my `main.py` know about it? This is the most likely source of user confusion — the magic seam between generated and user code.

### 4. `prisme review` appears once with no explanation

Listed in the CLI table as "Override tracking (list, diff, mark-reviewed, restore)" but never defined elsewhere. What are "overrides" in this context? Are these edits to `generated/` files? If so, this contradicts the "editing generated/ is unsupported" rule in section 6.4.

### 5. Config includes adds complexity without demonstrated need

The `prisme.d/*.toml` mechanism is introduced for "large projects" but prisme targets scaffolding CRUD apps. This feels premature. If you ship it, users will use it for small projects too, and now config is scattered.

### 6. No error examples

The PRD says the generator "refuses unknown versions with a clear error" and doctor "checks" things, but never shows what errors look like. Users care deeply about error messages — a single example of a good error would make the PRD more concrete.

### 7. "Clean break" from v1 is fine — say so explicitly

Decision #2 says no v1 migration tooling. Since there are no existing v1 users, this is a non-issue in practice. State that explicitly in the PRD so readers don't wonder about a migration burden that doesn't exist.

### 8. The `app/` directory is invisible to the generator but not to the runtime

This is stated but the implications aren't explored. What happens if a user deletes an extension hook file? Does the app crash? Does it silently skip? The contract between `app/` and `packages/` needs more definition.

### 9. `prisme plan` / `prisme generate` overlap is confusing

Section 10 says `generate` is "shortcut: plan + apply" but section 5.1 lists them as separate commands. For a user, having both `generate` and `plan`+`apply` means deciding which workflow to use — which is the kind of decision paralysis the PRD is trying to eliminate.

---

## Summary

The architectural direction is sound. The main risk is that the PRD optimizes for conceptual clarity at the framework level but doesn't yet show what the simple, happy-path user experience actually feels like. Leading with a "5-minute walkthrough" showing `create` → edit spec → `generate` → customize in `app/` → `generate` again (still safe) would make the promise tangible.

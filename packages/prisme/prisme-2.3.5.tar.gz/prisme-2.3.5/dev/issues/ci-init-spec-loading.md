# Issue: `prism ci init` fails even with valid StackSpec

**Status**: Resolved
**Priority**: Medium
**Created**: 2026-01-26

## Problem

Running `prism ci init` fails with the error "No StackSpec found in file" even when the spec file contains a valid `stack = StackSpec(...)` variable.

```
Error loading spec: No StackSpec found in file. Define a variable named 'spec'
or 'stack', or a function named 'get_spec()' or 'create_spec()'.
```

The spec file at `specs/models.py` has `stack = StackSpec(...)` which matches the documented variable name, but `prism ci init` still fails to find it.

Meanwhile, `prism deploy init` works correctly in the same directory.

## Impact

- Users cannot generate CI workflows for valid Prism projects
- Workaround requires manually creating CI workflows
- Inconsistent behavior between `ci init` and `deploy init` causes confusion

## Root Cause Analysis

The commands have different spec loading requirements:

| Command | Loads Spec | Why |
|---------|-----------|-----|
| `ci init` | YES | Introspects models to detect Redis (background_jobs) and frontend |
| `deploy init` | NO | Takes `--redis` flag and only checks `.prism/` exists |

The `ci init` command at `src/prism/cli.py:3086-3154`:
1. Searches for spec files: `prism.config.py`, `specs/models.py`, `spec.py`
2. Calls `load_spec_from_file()` which validates the entire spec
3. Any spec loading error causes immediate failure

This is problematic because CI workflow generation doesn't truly need the full spec - it only needs:
- Project name (can use directory name)
- Whether to include frontend workflows (can be a CLI flag)
- Whether to include Redis (can be a CLI flag)

## Proposed Solution

Make spec loading optional and add CLI flags for configuration:

1. Add `--frontend` flag to explicitly include frontend workflows
2. Add `--redis` flag to explicitly include Redis in CI (matching `deploy init`)
3. Try to load spec, but fall back gracefully to CLI flags / directory name
4. Show informational message when spec loading fails but flags are provided

This matches the pattern used by `deploy init` which:
- Uses `project_dir.name` for project name
- Takes `--redis` as a CLI flag
- Doesn't require spec loading at all

## Resolution

Fixed in `src/prism/cli.py` by:
1. Adding `--frontend` and `--redis` CLI flags
2. Making spec loading optional with graceful fallback
3. Using directory name as project name fallback
4. Allowing CLI flags to override spec-detected values

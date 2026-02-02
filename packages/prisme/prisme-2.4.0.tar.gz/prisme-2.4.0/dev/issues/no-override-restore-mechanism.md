# Issue: No way to restore generated code after override

**Status**: Resolved
**Priority**: Medium
**Created**: 2026-01-26

## Problem

When the override system preserves user code, there's no easy way to:
1. Restore the generated code (reject the override)
2. Perform a three-way merge between user code and new generated code

Current workaround requires manually using git or copying files to perform merges.

## Impact

Users who want to:
- Accept new generated code over their modifications
- Merge their changes with updated generated code

...must resort to manual git operations, which is error-prone and tedious.

## Proposed Solution

Add new CLI commands:
- `prism review restore <file>` - Replace user code with generated code
- `prism review merge <file>` - Open a merge tool or show three-way diff

Implementation notes:
- Store generated code in a temp location during generation for comparison
- Integrate with common merge tools (VS Code, vimdiff, etc.)
- Support `--all` flag for bulk operations

## Resolution

Implemented `prism review restore <file>` command:

1. Added `_save_generated_content` method to `OverrideLogger` to cache generated content
2. Added `load_generated_content` method to retrieve cached content
3. Added `restore` CLI command that:
   - Loads the cached generated content
   - Replaces the user's file with generated content
   - Removes the override from the log

Usage:
```bash
prism review restore <file>
prism review restore <file> --yes  # Skip confirmation
```

Note: The merge functionality for three-way merging was not implemented as it would require integration with external merge tools. The restore command provides the core functionality to reject an override and restore generated code.

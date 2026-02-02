# Issue: CLI docs mention commands that don't exist

**Status**: Resolved
**Priority**: Medium
**Created**: 2026-01-26

## Problem

The CLI reference documentation mentions `prism review reject` and `prism review approve` commands, but these commands don't exist in the actual CLI.

Actual available commands:
```
prism review --help

Commands:
  clear              Clear reviewed overrides from the log.
  diff               Show diff for a specific overridden file.
  list               List all overridden files.
  mark-all-reviewed  Mark all overrides as reviewed.
  mark-reviewed      Mark an override as reviewed.
  show               Show full override details for a file.
  summary            Show a summary of override status.
```

## Impact

Users following the documentation are confused when they can't find the documented commands. This undermines trust in the documentation.

## Proposed Solution

Either:
1. Implement the `reject`/`approve` commands as documented, or
2. Update the documentation to reflect the actual CLI commands

Recommendation: If the commands were planned but not implemented, either implement them or remove from docs. If the documentation was speculative, remove the references.

## Resolution

Fixed the CLI reference documentation:

1. Removed non-existent `prism review approve` and `prism review reject` commands
2. Added missing commands that exist in the CLI:
   - `prism review diff` - Show diff for a specific overridden file
   - `prism review show` - Show full override details for a file
   - `prism review clear` - Clear reviewed overrides from the log

The documentation now accurately reflects the actual CLI commands.

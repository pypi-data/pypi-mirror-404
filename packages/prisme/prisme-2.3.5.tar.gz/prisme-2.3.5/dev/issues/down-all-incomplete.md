# Issue: prism projects down-all doesn't stop all containers

**Status**: Resolved
**Priority**: Medium
**Created**: 2026-01-26

## Problem

Running `prism projects down-all` stopped some services but left the database container running, causing port conflicts when starting a new project.

## Impact

- Port conflicts prevent new projects from starting
- Users must manually identify and stop orphaned containers
- Inconsistent state between projects

## Proposed Solution

1. Investigate why certain containers are not being stopped:
   - Check if containers are started with different compose project names
   - Verify all compose files are being targeted
   - Check for containers started outside of compose

2. Potential fixes:
   - Use `docker compose down --remove-orphans` flag
   - Scan for containers with Prism labels regardless of project
   - Add `--volumes` flag option to also clean up volumes

3. Add verbose output showing which containers were stopped/skipped

## Resolution

Improved `prism projects down-all` to handle all containers:

1. **Use docker compose down**: Now tries `docker compose down --remove-orphans` first for each project
2. **Fallback to container stops**: If compose fails, falls back to stopping/removing containers individually
3. **Find orphaned containers**: Added `_find_orphaned_containers()` method to detect:
   - Containers with `com.prism.project` label
   - Database containers (`_db_1`, `_postgres_1` patterns) that might not be on proxy network
4. **Added CLI options**:
   - `--volumes/-v`: Also remove volumes when stopping
   - `--quiet/-q`: Suppress detailed output
5. **Verbose output**: Shows which containers are being stopped

This ensures all Prism-related containers are properly stopped, including database containers that might have been orphaned.

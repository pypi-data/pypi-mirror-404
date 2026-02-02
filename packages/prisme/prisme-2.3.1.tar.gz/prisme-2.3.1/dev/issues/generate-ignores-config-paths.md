# Issue: Generate Ignores Config Paths for Backend/Frontend

**Status**: Open
**Priority**: Medium
**Created**: 2026-01-26

## Problem

The `prism generate` command does not respect the custom paths set in the configuration file for backend and frontend directories. When users configure custom paths (e.g., changing the default backend/frontend folder names or locations), the generate command still outputs to the default locations instead of the configured paths.

## Impact

- Users with custom project structures cannot use the generate command effectively
- Generated code ends up in wrong directories, requiring manual intervention
- Configuration appears broken, leading to confusion and support requests

## Proposed Solution

1. Audit the generate command to identify where output paths are determined
2. Ensure all path lookups read from the config file (prism.config.py or similar)
3. Add tests to verify custom paths are respected during generation

## Resolution

(Fill in when resolved)

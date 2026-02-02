# Issue: Database Schema Drift Not Detected

**Status**: Deferred
**Priority**: High
**Type**: Feature Request
**Created**: 2026-01-25

## Problem

The PostgreSQL database had an `instrument_isin` column in `signal_trends` that wasn't in the model or spec. This caused runtime errors when the GraphQL mutation tried to insert records.

**Error:**
```
null value in column "instrument_isin" of relation "signal_trends" violates not-null constraint
```

**Root cause:** Unknown - possibly from a previous spec version that was removed but never migrated.

## Impact

- Silent schema drift can accumulate over time
- Runtime errors only discovered during actual usage
- Difficult to diagnose without direct database inspection
- Can block entire features until manually resolved
- No warning system for developers

## Proposed Solution

Prism should either:

### Option 1: Startup Validation (Development Mode)
Validate that database schema matches models on startup in development mode:
```python
# On app startup in dev mode
schema_diff = compare_db_to_models()
if schema_diff:
    logger.warning(f"Schema drift detected: {schema_diff}")
```

### Option 2: Automatic Migration Generation
Generate migrations automatically when specs change:
- Track spec file hashes
- Generate Alembic migrations when changes detected
- Require explicit `prism migrate` command

### Option 3: Schema Sync Command
Add a CLI command to detect and report drift:
```bash
prism schema:check  # Report differences
prism schema:sync   # Generate migration to fix drift
```

### Option 4: Pre-commit Hook
Add optional pre-commit validation:
```bash
prism validate:schema  # Fails if drift detected
```

## Workaround

Manual investigation and fix:
1. Connect to database via `psql`
2. Inspect actual schema: `\d signal_trends`
3. Compare with model definition
4. Manually drop/alter columns to match:
```sql
ALTER TABLE signal_trends DROP COLUMN instrument_isin;
```

## Resolution

**Deferred**: 2026-01-25

This is a feature request requiring database introspection capabilities. It needs:
- SQLAlchemy inspection of live database schema
- Comparison with model definitions
- CLI commands for schema validation

Prism already has `AlembicGenerator` for migrations. Future work could integrate schema validation into the migration workflow.

# Issue: App.tsx overwrites custom providers on regeneration

**Status**: Resolved
**Priority**: High
**Created**: 2026-01-26

## Problem

App.tsx uses `ALWAYS_OVERWRITE` strategy, which means any custom React context providers added to the app root are lost on regeneration.

Example of custom provider addition:
```tsx
export default function App(): JSX.Element {
  return (
    <AnalysisProvider>
      <RouterProvider router={router} />
    </AnalysisProvider>
  );
}
```

After running `prism generate`, this is overwritten back to:
```tsx
export default function App(): JSX.Element {
  return <RouterProvider router={router} />;
}
```

## Impact

- Custom context providers are lost after every generation
- App crashes with errors like: `useAnalysisContext must be used within an AnalysisProvider`
- Developers must manually restore providers after each generation
- Blocks iterative development workflows

This is related to [Custom routes not preserved](custom-routes-not-preserved.md) - both involve losing custom code in generated files.

## Proposed Solution

Consider one of these approaches:

1. **GENERATE_ONCE strategy for App.tsx**
   - Simple but prevents future App.tsx template improvements

2. **Protected region markers for custom providers**
   - Add `{/* PROTECTED_REGION_START(custom_providers) */}` markers
   - Preserve content within markers during regeneration

3. **Providers config in spec**
   - Support declaring providers in the Prism spec
   - Auto-generate provider wrappers from config
   - Most flexible but requires spec schema changes

Recommendation: Option 2 (protected regions) aligns with the solution proposed for router.tsx custom routes and provides consistency across the codebase.

## Resolution

Implemented Option 2 (protected regions), consistent with router.tsx fix:

1. Changed App.tsx from `ALWAYS_OVERWRITE` to `MERGE` file strategy
2. Added two protected regions in the App.tsx template:
   - `// PRISM:PROTECTED:START - Custom Imports` - for custom context imports
   - `{/* PRISM:PROTECTED:START - Custom Providers */}` - for custom provider wrappers

Custom providers within these regions are now preserved during regeneration.

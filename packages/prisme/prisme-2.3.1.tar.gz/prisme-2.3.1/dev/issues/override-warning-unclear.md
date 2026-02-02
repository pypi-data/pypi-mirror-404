# Issue: Override warning message could be clearer

**Status**: Resolved
**Priority**: Low
**Created**: 2026-01-26

## Problem

The "Code Override Warning" message can be confusing. Users may think their code was overwritten when it was actually preserved.

Current message:
```
4 file(s) were overridden by your custom code
Your modifications were preserved, but the generated code changed.
```

The phrase "overridden by your custom code" is ambiguous - it could mean the generated code overwrote user code, or user code overwrote generated code.

## Impact

Users may be confused about what happened to their code, potentially leading to:
- Unnecessary panic about lost work
- Confusion about the override system's behavior
- Reduced trust in the generation process

## Proposed Solution

Update the warning message to be clearer:

```
4 file(s) have custom modifications that were PRESERVED
The template for these files has changed. Review to ensure compatibility.
```

Alternative wording:
```
4 file(s) kept your custom code (new generated code was skipped)
Run 'prism review list' to see what changed.
```

## Resolution

Updated warning messages to be clearer:

**Before:**
- Title: "🔍 Code Override Warning" (ambiguous)
- Message: "file(s) were overridden by your custom code" (confusing)
- Color: Yellow (concerning)

**After:**
- Title: "🔒 Custom Code Preserved" (reassuring)
- Message: "file(s) with custom code were PRESERVED" (clear)
- Color: Green (positive)
- Added reference to new `prism review restore` command
- Changed "overridden files" to "preserved files" terminology

Also updated the diff panel message from "Generated code was overridden by your custom code" to "Your custom code was preserved - generated code was not applied".

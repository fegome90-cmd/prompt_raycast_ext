# Design: Code Review Fixes for Robust Backend Availability

**Date:** 2026-02-19
**Status:** Approved
**Scope:** Fix critical and important issues from 4-agent code review

## Summary

Fix 6 issues identified in the thorough code review of the robust backend availability implementation:

| Issue | Severity | Fix |
|-------|----------|-----|
| Dead code (line 226) | Critical | Delete commented-out type |
| Hardcoded path in `ecosystem.config.cjs` | Important | Use `__dirname` |
| Hardcoded path in `handlers.tsx` | Important | Generic instruction |
| Duplicate `STAGE_MESSAGES` (3 files) | Important | Create `core/constants.ts` |
| Unused parameter `_t0` | Important | Remove it |
| Duplicate error hint functions | Important | Merge into one |

**Estimated effort:** ~15 minutes

## Design Decisions

### D1: PM2 Config Path Resolution

**Decision:** Use `__dirname` for `cwd` in ecosystem.config.cjs

**Rationale:**
- CommonJS module so `__dirname` is available
- Resolves to the directory containing the config file
- Works for any developer regardless of install location

### D2: Error Handler Path Display

**Decision:** Use generic placeholder `<your-raycast-ext-dir>`

**Rationale:**
- Raycast extensions run in sandboxed environment
- Cannot detect project location at runtime
- Generic instruction is clearer than wrong path

### D3: Shared Constants Location

**Decision:** Create single `core/constants.ts` file

**Rationale:**
- Follows existing pattern (`defaults.ts` for config)
- Keeps related constants together
- Simpler than multiple domain-specific files

## File Changes

### 1. ecosystem.config.cjs

```javascript
// Before
cwd: '/Users/felipe_gonzalez/Developer/raycast_ext',

// After
cwd: __dirname,
```

### 2. dashboard/src/core/errors/handlers.tsx

**Changes:**
1. Replace hardcoded path with generic instruction
2. Remove unused `_t0` parameter

```typescript
// Before
const BACKEND_START_COMMAND = "cd /Users/felipe_gonzalez/Developer/raycast_ext && make dev";
export function handleBackendError(error: unknown, _t0: number) {

// After
const BACKEND_START_COMMAND = "cd <your-raycast-ext-dir> && make dev";
export function handleBackendError(error: unknown) {
```

### 3. dashboard/src/core/constants.ts (NEW)

```typescript
/**
 * Shared constants for Raycast extension
 */

// Loading stage type for progressive status updates
export type LoadingStage =
  | "idle"
  | "validating"
  | "connecting"
  | "analyzing"
  | "improving"
  | "success"
  | "error";

// Stage messages for user-facing status display
export const STAGE_MESSAGES: Record<LoadingStage, string> = {
  idle: "",
  validating: "Validating input...",
  connecting: "Connecting to DSPy...",
  analyzing: "Analyzing prompt structure...",
  improving: "Applying few-shot learning...",
  success: "Complete!",
  error: "Failed",
} as const;
```

### 4. dashboard/src/promptify-quick.tsx

**Changes:**
1. Delete line 226 (commented-out type)
2. Import from `./core/constants`
3. Remove local `LoadingStage` and `STAGE_MESSAGES`
4. Merge `buildErrorHint` and `buildDSPyHint`:

```typescript
// Before: Two separate functions with 70% duplicate code
function buildErrorHint(error: unknown): string | null { ... }
function buildDSPyHint(error: unknown): string | null { ... }

// After: Single function with mode parameter
function buildErrorHint(error: unknown, mode?: "dspy"): string | null {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();
  if (lower.includes("timed out")) return "try increasing timeout (ms)";
  if (lower.includes("connect") || lower.includes("econnrefused") || lower.includes("not reachable")) {
    return mode === "dspy" ? "check the DSPy backend is running" : "check `ollama serve` is running";
  }
  if (lower.includes("model") && lower.includes("not found")) {
    return "Pull the model first: `ollama pull <model>`";
  }
  return null;
}

// Usage
const hint = useBackend ? buildErrorHint(e, "dspy") : buildErrorHint(e);
```

## Testing

No new tests required - all changes are refactoring that preserves behavior:
- Path changes affect only display text
- Constants extraction is pure refactoring
- Function merge maintains same logic

## Rollback

Simple git revert if issues arise - no database migrations or config changes.

## References

- Code review findings from 4-agent review (security, Python/config, refactoring, general)
- Existing patterns in `core/config/defaults.ts`

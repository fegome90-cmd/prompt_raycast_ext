# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 6 code review issues (1 critical, 5 important) from robust backend availability implementation.

**Architecture:** Simple refactoring - PM2 config path fix, error handler cleanup, shared constants extraction, function consolidation.

**Tech Stack:** TypeScript (Raycast), Node.js (PM2), CommonJS

---

## Task 1: Fix PM2 Config Path

**Files:**
- Modify: `ecosystem.config.cjs:5`

**Step 1: Replace hardcoded path with `__dirname`**

```javascript
// ecosystem.config.cjs - line 5
// BEFORE:
cwd: '/Users/felipe_gonzalez/Developer/raycast_ext',

// AFTER:
cwd: __dirname,
```

**Step 2: Verify PM2 restarts correctly**

```bash
pm2 restart raycast-backend-8000 && pm2 status
```

Expected: Status shows "online" with 0 restarts

**Step 3: Commit**

```bash
git add ecosystem.config.cjs
git commit -m "fix: use __dirname for PM2 cwd portability"
```

---

## Task 2: Fix Hardcoded Path in Error Handler

**Files:**
- Modify: `dashboard/src/core/errors/handlers.tsx:6`

**Step 1: Replace hardcoded path with generic instruction**

```typescript
// dashboard/src/core/errors/handlers.tsx - line 6
// BEFORE:
const BACKEND_START_COMMAND = "cd /Users/felipe_gonzalez/Developer/raycast_ext && make dev";

// AFTER:
const BACKEND_START_COMMAND = "cd <your-raycast-ext-dir> && make dev";
```

**Step 2: Update error message markdown (line 39)**

```typescript
// In the markdown string, replace:
cd /Users/felipe_gonzalez/Developer/raycast_ext

// WITH:
cd <your-raycast-ext-dir>
```

**Step 3: Verify lint passes**

```bash
cd dashboard && npm run lint 2>&1 | grep -E "(handlers|error)" || echo "No errors in handlers.tsx"
```

**Step 4: Commit**

```bash
git add dashboard/src/core/errors/handlers.tsx
git commit -m "fix: use generic path in error handler for portability"
```

---

## Task 3: Remove Unused Parameter

**Files:**
- Modify: `dashboard/src/core/errors/handlers.tsx:8`

**Step 1: Remove `_t0` parameter from function signature**

```typescript
// dashboard/src/core/errors/handlers.tsx - line 8
// BEFORE:
export function handleBackendError(error: unknown, _t0: number) {

// AFTER:
export function handleBackendError(error: unknown) {
```

**Step 2: Verify no callers pass second argument**

```bash
grep -r "handleBackendError" dashboard/src/ | grep -v "export function"
```

Expected: Only calls with single argument (error) or usage in error boundaries

**Step 3: Verify lint passes**

```bash
cd dashboard && npm run lint 2>&1 | grep "_t0" || echo "No _t0 warnings"
```

**Step 4: Commit**

```bash
git add dashboard/src/core/errors/handlers.tsx
git commit -m "refactor: remove unused _t0 parameter from handleBackendError"
```

---

## Task 4: Create Shared Constants File

**Files:**
- Create: `dashboard/src/core/constants.ts`

**Step 1: Create the constants file**

```typescript
// dashboard/src/core/constants.ts
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

**Step 2: Verify file compiles**

```bash
cd dashboard && npx tsc --noEmit src/core/constants.ts 2>&1 || echo "Check for errors"
```

**Step 3: Commit**

```bash
git add dashboard/src/core/constants.ts
git commit -m "refactor: extract shared LoadingStage and STAGE_MESSAGES"
```

---

## Task 5: Update promptify-quick.tsx to Use Shared Constants

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Add import at top of file (after line 10)**

```typescript
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";
```

**Step 2: Delete commented-out type (line 226)**

```typescript
// DELETE THIS LINE:
// type LoadingStage = "validating" | "connecting" | "processing" | "finalizing";
```

**Step 3: Remove local `LoadingStage` type (lines 30-31)**

```typescript
// DELETE THESE LINES:
// Loading stage type for progressive status updates
type LoadingStage = "idle" | "validating" | "connecting" | "analyzing" | "improving" | "success" | "error";
```

**Step 4: Remove local `STAGE_MESSAGES` (lines 33-42)**

```typescript
// DELETE THESE LINES:
// Stage messages for user-facing status display
const STAGE_MESSAGES = {
  idle: "",
  validating: "Validating input...",
  connecting: "Connecting to DSPy...",
  analyzing: "Analyzing prompt structure...",
  improving: "Applying few-shot learning...",
  success: "Complete!",
  error: "Failed",
} as const;
```

**Step 5: Verify lint passes**

```bash
cd dashboard && npm run lint 2>&1 | grep "promptify-quick" || echo "No errors"
```

**Step 6: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "refactor: use shared constants from core/constants.ts"
```

---

## Task 6: Merge Duplicate Error Hint Functions

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Replace both functions with single merged function (lines 544-566)**

```typescript
// DELETE buildErrorHint and buildDSPyHint functions

// REPLACE WITH:
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
```

**Step 2: Update call site (line 435)**

```typescript
// BEFORE:
const hint = useBackend ? buildDSPyHint(e) : buildErrorHint(e);

// AFTER:
const hint = buildErrorHint(e, useBackend ? "dspy" : undefined);
```

**Step 3: Verify lint passes**

```bash
cd dashboard && npm run lint 2>&1 | grep -E "(buildErrorHint|buildDSPyHint)" || echo "No errors"
```

**Step 4: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "refactor: merge buildErrorHint and buildDSPyHint into single function"
```

---

## Task 7: Update Other Files Using STAGE_MESSAGES

**Files:**
- Modify: `dashboard/src/promptify-selected.tsx`
- Modify: `dashboard/src/conversation-view.tsx`

**Step 1: Update promptify-selected.tsx**

Add import:
```typescript
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";
```

Remove local STAGE_MESSAGES constant (lines 15-23).

**Step 2: Update conversation-view.tsx**

Add import:
```typescript
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";
```

Remove local STAGE_MESSAGES constant (lines 25-33).

**Step 3: Verify lint passes**

```bash
cd dashboard && npm run lint 2>&1 | grep -E "(STAGE_MESSAGES|promptify-selected|conversation-view)" || echo "No errors"
```

**Step 4: Commit**

```bash
git add dashboard/src/promptify-selected.tsx dashboard/src/conversation-view.tsx
git commit -m "refactor: use shared STAGE_MESSAGES in all components"
```

---

## Task 8: Final Verification

**Step 1: Run full lint**

```bash
cd dashboard && npm run lint
```

Expected: No new errors introduced

**Step 2: Verify PM2 is healthy**

```bash
pm2 status && curl -s http://localhost:8000/health
```

Expected: Status "online", health returns JSON with `"status":"healthy"`

**Step 3: Create summary commit if needed**

```bash
git status
# If any uncommitted changes:
git add -A && git commit -m "chore: finalize code review fixes"
```

---

## Summary

| Task | File | Change |
|------|------|--------|
| 1 | `ecosystem.config.cjs` | Use `__dirname` for cwd |
| 2 | `handlers.tsx` | Generic path instruction |
| 3 | `handlers.tsx` | Remove `_t0` parameter |
| 4 | `constants.ts` | Create shared constants |
| 5 | `promptify-quick.tsx` | Import shared constants |
| 6 | `promptify-quick.tsx` | Merge error hint functions |
| 7 | `promptify-selected.tsx`, `conversation-view.tsx` | Use shared constants |
| 8 | - | Final verification |

**Total: 8 tasks, ~15 minutes**

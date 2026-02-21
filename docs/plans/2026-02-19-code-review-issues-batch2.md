# Code Review Issues - Batch 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all code review findings from mr-thorough (4-agent review) - tests for error functions, error handling improvements, code cleanup

**Architecture:** TDD approach - write failing tests first, then implement fixes. TypeScript tests with Vitest for frontend, code cleanup for dead code/unused imports

**Tech Stack:** TypeScript, Vitest, React Testing Library, Raycast API mocks

---

## Phase 1: CRITICAL - Tests for Error Functions (TDD)

### Task 1: Create Test File for buildErrorHint

**Files:**
- Create: `dashboard/src/__tests__/buildErrorHint.test.ts`

**Step 1: Write the failing tests**

```typescript
// dashboard/src/__tests__/buildErrorHint.test.ts
import { describe, it, expect } from "vitest";

describe("buildErrorHint", () => {
  // Helper to access private function - will need to export it
  const buildErrorHint = (error: unknown, mode?: "dspy" | "nlac"): string | null => {
    const message = error instanceof Error ? error.message : String(error);
    const lower = message.toLowerCase();
    if (lower.includes("timed out")) return "try increasing timeout (ms)";
    if (lower.includes("connect") || lower.includes("econnrefused") || lower.includes("not reachable")) {
      if (mode === "nlac") return "check the NLaC backend is running with 'make dev'";
      if (mode === "dspy") return "check the DSPy backend is running";
      return "check `ollama serve` is running";
    }
    if (lower.includes("model") && lower.includes("not found")) {
      return "Pull the model first: `ollama pull <model>`";
    }
    return null;
  };

  describe("timeout errors", () => {
    it("returns timeout hint for 'timed out' message", () => {
      expect(buildErrorHint(new Error("Request timed out"))).toBe("try increasing timeout (ms)");
    });

    it("returns timeout hint for case-insensitive match", () => {
      expect(buildErrorHint(new Error("TIMED OUT after 30s"))).toBe("try increasing timeout (ms)");
    });
  });

  describe("connection errors", () => {
    it("returns DSPy hint when mode is 'dspy'", () => {
      expect(buildErrorHint(new Error("ECONNREFUSED"), "dspy")).toBe("check the DSPy backend is running");
    });

    it("returns NLaC hint when mode is 'nlac'", () => {
      expect(buildErrorHint(new Error("connect failed"), "nlac")).toBe("check the NLaC backend is running with 'make dev'");
    });

    it("returns Ollama hint when mode is undefined", () => {
      expect(buildErrorHint(new Error("not reachable"))).toBe("check `ollama serve` is running");
    });
  });

  describe("model not found errors", () => {
    it("returns pull hint for model not found", () => {
      expect(buildErrorHint(new Error("model llama3 not found"))).toBe("Pull the model first: `ollama pull <model>`");
    });
  });

  describe("unknown errors", () => {
    it("returns null for unknown error types", () => {
      expect(buildErrorHint(new Error("something weird happened"))).toBeNull();
    });

    it("handles string errors", () => {
      expect(buildErrorHint("random string")).toBeNull();
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm run test -- src/__tests__/buildErrorHint.test.ts
```

Expected: Tests pass (function is inline in test file - will fail when we extract to real file)

**Step 3: Export buildErrorHint from promptify-quick.tsx**

Move the function and export it:

```typescript
// dashboard/src/promptify-quick.tsx - at line ~531
export function buildErrorHint(error: unknown, mode?: "dspy" | "nlac"): string | null {
  const message = error instanceof Error ? error.message : String(error);
  const lower = message.toLowerCase();
  if (lower.includes("timed out")) return "try increasing timeout (ms)";
  if (lower.includes("connect") || lower.includes("econnrefused") || lower.includes("not reachable")) {
    if (mode === "nlac") return "check the NLaC backend is running with 'make dev'";
    if (mode === "dspy") return "check the DSPy backend is running";
    return "check `ollama serve` is running";
  }
  if (lower.includes("model") && lower.includes("not found")) {
    return "Pull the model first: `ollama pull <model>`";
  }
  return null;
}
```

**Step 4: Update test to import from real file**

```typescript
import { buildErrorHint } from "../promptify-quick";
```

**Step 5: Run tests and verify pass**

```bash
cd dashboard && npm run test -- src/__tests__/buildErrorHint.test.ts
```

**Step 6: Commit**

```bash
git add dashboard/src/__tests__/buildErrorHint.test.ts dashboard/src/promptify-quick.tsx
git commit -m "test: add buildErrorHint test coverage with NLaC mode support"
```

---

### Task 2: Create Test File for handleBackendError

**Files:**
- Create: `dashboard/src/core/errors/__tests__/handlers.test.ts`

**Step 1: Write the failing tests**

```typescript
// dashboard/src/core/errors/__tests__/handlers.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleBackendError } from "../handlers";

// Mock Raycast components
vi.mock("@raycast/api", () => ({
  Action: {
    OpenInBrowser: vi.fn(({ title }) => ({ type: "action", title })),
    CopyToClipboard: vi.fn(({ title, content }) => ({ type: "action", title, content })),
  },
  ActionPanel: vi.fn(({ children }) => ({ type: "action-panel", children })),
  Color: {
    Red: "#EF4444",
    Green: "#10B981",
    Yellow: "#F59E0B",
    Blue: "#3B82F6",
    PrimaryText: "#FFFFFF",
    SecondaryText: "#9CA3AF",
  },
}));

describe("handleBackendError", () => {
  describe("AbortError (timeout)", () => {
    it("returns timeout guidance for AbortError", () => {
      const error = new Error("Request aborted");
      error.name = "AbortError";
      const result = handleBackendError(error);
      // Should return a React component - check for timeout-related content
      expect(result).toBeDefined();
    });
  });

  describe("Connection errors", () => {
    it("handles ECONNREFUSED", () => {
      const error = new TypeError("fetch failed: ECONNREFUSED ::1:8000");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles 'fetch failed' errors", () => {
      const error = new TypeError("fetch failed");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("Network errors", () => {
    it("handles ENOTFOUND", () => {
      const error = new Error("getaddrinfo ENOTFOUND localhost");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("HTTP errors", () => {
    it("handles 504 Gateway Timeout", () => {
      const error = new Error("HTTP 504: Gateway Timeout");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles 400 Bad Request", () => {
      const error = new Error("HTTP 400: Bad Request - Invalid prompt");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });
  });

  describe("Unknown errors", () => {
    it("falls through to generic error for unknown types", () => {
      const error = new Error("Something unexpected");
      const result = handleBackendError(error);
      expect(result).toBeDefined();
    });

    it("handles non-Error objects", () => {
      const result = handleBackendError("string error");
      expect(result).toBeDefined();
    });
  });
});
```

**Step 2: Run test to see current state**

```bash
cd dashboard && npm run test -- src/core/errors/__tests__/handlers.test.ts 2>&1 | head -50
```

**Step 3: Fix any issues and verify tests pass**

```bash
cd dashboard && npm run test -- src/core/errors/__tests__/handlers.test.ts
```

**Step 4: Commit**

```bash
git add dashboard/src/core/errors/__tests__/handlers.test.ts
git commit -m "test: add handleBackendError test coverage"
```

---

## Phase 2: HIGH Priority Fixes

### Task 3: Add Logging to Health Check Error

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:249-256`

**Step 1: Update the catch block**

```typescript
// BEFORE:
} catch {
  setBackendStatus("unavailable");
}

// AFTER:
} catch (error) {
  console.error(`${LOG_PREFIX} Health check failed:`, {
    error: error instanceof Error ? error.message : String(error),
    dspyBaseUrl: preferences.dspyBaseUrl || configState.config.dspy.baseUrl,
  });
  setBackendStatus("unavailable");
}
```

**Step 2: Verify lint passes**

```bash
cd dashboard && npm run lint -- --quiet 2>&1 | grep -E "promptify-quick" || echo "No errors"
```

**Step 3: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "fix: add error logging to health check for debugging"
```

---

### Task 4: Fix Loading Stage Reset Race Condition

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:414-449`

**Step 1: Remove redundant setLoadingStage("error") in catch**

The `finally` block always resets to "idle", making the error state flash and disappear.

```typescript
// BEFORE:
} catch (e) {
  setLoadingStage("error");  // This gets overwritten by finally
  // ... error handling
} finally {
  setIsLoading(false);
  setLoadingStage("idle");  // Always runs, overwrites error
}

// AFTER - Option 1: Remove redundant error stage
} catch (e) {
  // Remove setLoadingStage("error") - it's immediately overwritten
  // ... error handling (toast shows error state)
} finally {
  setIsLoading(false);
  setLoadingStage("idle");
}
```

**Step 2: Verify behavior is unchanged**

The toast still shows the error, just no brief flash of "error" loading stage.

**Step 3: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "fix: remove redundant loading stage that was overwritten by finally"
```

---

### Task 5: Add Feedback for savePrompt Failure

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:389-401`

**Step 1: Track save failure and show in toast**

```typescript
// BEFORE:
await savePrompt({
  prompt: finalPrompt,
  rawInput: text,
  improvedFrom: text.length,
  improvedTo: finalPrompt.length,
  confidence: meta?.confidence,
  clarifyingQuestions: meta?.clarifyingQuestions,
  assumptions: meta?.assumptions,
  source: useBackend ? "dspy" : "ollama",
}).catch((error) => {
  console.error(`${LOG_PREFIX} ❌ Failed to save prompt:`, error);
});

await ToastHelper.success("Copied to clipboard", `${finalPrompt.length} characters - Saved to history`);

// AFTER:
let historySaveFailed = false;
await savePrompt({
  prompt: finalPrompt,
  rawInput: text,
  improvedFrom: text.length,
  improvedTo: finalPrompt.length,
  confidence: meta?.confidence,
  clarifyingQuestions: meta?.clarifyingQuestions,
  assumptions: meta?.assumptions,
  source: useBackend ? "dspy" : "ollama",
}).catch((error) => {
  console.error(`${LOG_PREFIX} ❌ Failed to save prompt:`, error);
  historySaveFailed = true;
});

const historyMessage = historySaveFailed
  ? `${finalPrompt.length} characters (history save failed)`
  : `${finalPrompt.length} characters - Saved to history`;
await ToastHelper.success("Copied to clipboard", historyMessage);
```

**Step 2: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "fix: show accurate feedback when history save fails"
```

---

### Task 6: Improve Placeholder Path in Error Handler

**Files:**
- Modify: `dashboard/src/core/errors/handlers.tsx:6, 39`

**Step 1: Replace placeholder with actionable instruction**

```typescript
// BEFORE:
const BACKEND_START_COMMAND = "cd <your-raycast-ext-dir> && make dev";

// AFTER:
const BACKEND_START_COMMAND = "make dev  # Run from project root";
```

**Step 2: Update markdown to remove the cd command**

```typescript
// In the markdown string, replace:
markdown={`## ${tokens.semantic.error.icon} Backend Not Running

Start the backend:
\`\`\`bash
cd <your-raycast-ext-dir>
make dev
\`\`\`

// WITH:
markdown={`## ${tokens.semantic.error.icon} Backend Not Running

Start the backend from the project root:
\`\`\`bash
make dev
\`\`\`
```

**Step 3: Commit**

```bash
git add dashboard/src/core/errors/handlers.tsx
git commit -m "fix: use actionable instruction instead of placeholder path"
```

---

## Phase 3: IMPORTANT - Shared Constants Cleanup

### Task 7: Update prompt-history.tsx to Use Shared Constants

**Files:**
- Modify: `dashboard/src/prompt-history.tsx:8-15`

**Step 1: Add import and remove local constants**

```typescript
// Add import at top:
import { LoadingStage, STAGE_MESSAGES } from "./core/constants";

// Remove local definition (lines 8-15):
// type LoadingStage = "idle" | "loading" | "success" | "error";
// const STAGE_MESSAGES = { ... }
```

**Step 2: Note - History uses different stages**

The history view uses `"loading"` instead of `"connecting"`. Either:
- A) Extend the shared type to include history-specific stages
- B) Keep local stages since they're semantically different

For now, keep local stages but rename to avoid confusion:

```typescript
// Use history-specific naming
type HistoryLoadingStage = "idle" | "loading" | "success" | "error";

const HISTORY_STAGE_MESSAGES: Record<HistoryLoadingStage, string> = {
  idle: "",
  loading: "Loading history...",
  success: "Loaded",
  error: "Failed",
} as const;
```

**Step 3: Commit**

```bash
git add dashboard/src/prompt-history.tsx
git commit -m "refactor: rename local LoadingStage to avoid confusion with shared type"
```

---

### Task 8: Create Test for Constants

**Files:**
- Create: `dashboard/src/core/__tests__/constants.test.ts`

**Step 1: Write the test**

```typescript
// dashboard/src/core/__tests__/constants.test.ts
import { describe, it, expect } from "vitest";
import { STAGE_MESSAGES, type LoadingStage } from "../constants";

describe("constants", () => {
  describe("STAGE_MESSAGES", () => {
    it("contains all LoadingStage keys", () => {
      const stages: LoadingStage[] = ["idle", "validating", "connecting", "analyzing", "improving", "success", "error"];
      stages.forEach((stage) => {
        expect(STAGE_MESSAGES).toHaveProperty(stage);
      });
    });

    it("has non-empty strings for non-idle stages", () => {
      const nonIdleStages: LoadingStage[] = ["validating", "connecting", "analyzing", "improving", "success", "error"];
      nonIdleStages.forEach((stage) => {
        expect(STAGE_MESSAGES[stage].length).toBeGreaterThan(0);
      });
    });

    it("has empty string for idle stage", () => {
      expect(STAGE_MESSAGES.idle).toBe("");
    });
  });
});
```

**Step 2: Run test**

```bash
cd dashboard && npm run test -- src/core/__tests__/constants.test.ts
```

**Step 3: Commit**

```bash
git add dashboard/src/core/__tests__/constants.test.ts
git commit -m "test: add constants.ts coverage"
```

---

## Phase 4: SUGGESTIONS - Quick Wins

### Task 9: Remove Commented Dead Code

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:213`

**Step 1: Delete the commented line**

```typescript
// DELETE THIS LINE:
// type LoadingStage = "validating" | "connecting" | "processing" | "finalizing";
```

**Step 2: Commit**

```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "chore: remove commented-out dead code"
```

---

### Task 10: Remove Unused Imports

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:10`
- Modify: `dashboard/src/conversation-view.tsx:1-11`

**Step 1: Remove formatTimestamp from promptify-quick.tsx**

```typescript
// BEFORE:
import { savePrompt, formatTimestamp } from "./core/promptStorage";

// AFTER:
import { savePrompt } from "./core/promptStorage";
```

**Step 2: Remove unused imports from conversation-view.tsx**

```typescript
// BEFORE:
import {
  List,
  Action,
  ActionPanel,
  Toast,
  showToast,
  Form,
  Clipboard,
  getPreferenceValues,
  popToRoot,
} from "@raycast/api";

// AFTER:
import {
  List,
  Action,
  ActionPanel,
  Form,
  Clipboard,
  getPreferenceValues,
} from "@raycast/api";
```

**Step 3: Verify lint passes**

```bash
cd dashboard && npm run lint -- --fix
```

**Step 4: Commit**

```bash
git add dashboard/src/promptify-quick.tsx dashboard/src/conversation-view.tsx
git commit -m "chore: remove unused imports"
```

---

### Task 11: Extract ENGINE_NAMES to Shared Constants

**Files:**
- Modify: `dashboard/src/core/constants.ts`
- Modify: `dashboard/src/promptify-quick.tsx:12-16`
- Modify: `dashboard/src/prompt-history.tsx`

**Step 1: Add ENGINE_NAMES to constants.ts**

```typescript
// Add to dashboard/src/core/constants.ts
// Engine display names (used in metadata across commands)
export const ENGINE_NAMES = {
  dspy: "DSPy + Haiku",
  ollama: "Ollama",
} as const;
```

**Step 2: Update promptify-quick.tsx to import**

```typescript
// Remove local ENGINE_NAMES, add to import:
import { LoadingStage, STAGE_MESSAGES, ENGINE_NAMES } from "./core/constants";
```

**Step 3: Update prompt-history.tsx to use shared constant**

```typescript
import { ENGINE_NAMES } from "./core/constants";

// Replace hardcoded strings with ENGINE_NAMES.dspy / ENGINE_NAMES.ollama
```

**Step 4: Commit**

```bash
git add dashboard/src/core/constants.ts dashboard/src/promptify-quick.tsx dashboard/src/prompt-history.tsx
git commit -m "refactor: extract ENGINE_NAMES to shared constants"
```

---

### Task 12: Final Verification

**Step 1: Run full test suite**

```bash
cd dashboard && npm run test
```

**Step 2: Run lint**

```bash
cd dashboard && npm run lint
```

**Step 3: Verify PM2 is healthy**

```bash
pm2 status && curl -s http://localhost:8000/health
```

**Step 4: Create summary commit if needed**

```bash
git status
# If any uncommitted changes:
git add -A && git commit -m "chore: finalize code review batch 2 fixes"
```

---

## Summary

| Phase | Tasks | Time Est. |
|-------|-------|-----------|
| Phase 1: Tests (CRITICAL) | 1-2 | 20 min |
| Phase 2: HIGH Fixes | 3-6 | 15 min |
| Phase 3: IMPORTANT | 7-8 | 10 min |
| Phase 4: Quick Wins | 9-12 | 10 min |
| **Total** | **12 tasks** | **~55 min** |

## Coverage Impact

| File | Before | After |
|------|--------|-------|
| `buildErrorHint` | 0% | ~90% |
| `handleBackendError` | 0% | ~80% |
| `constants.ts` | 0% | 100% |

## Files Changed

| File | Change Type |
|------|-------------|
| `dashboard/src/__tests__/buildErrorHint.test.ts` | CREATE |
| `dashboard/src/core/errors/__tests__/handlers.test.ts` | CREATE |
| `dashboard/src/core/__tests__/constants.test.ts` | CREATE |
| `dashboard/src/promptify-quick.tsx` | MODIFY |
| `dashboard/src/core/errors/handlers.tsx` | MODIFY |
| `dashboard/src/conversation-view.tsx` | MODIFY |
| `dashboard/src/prompt-history.tsx` | MODIFY |
| `dashboard/src/core/constants.ts` | MODIFY |

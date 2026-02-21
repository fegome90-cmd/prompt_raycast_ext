# Code Review Fixes - Batch 3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all CRITICAL (4) and HIGH (6) issues from thorough code review

**Architecture:** TDD approach for test gaps, defensive error handling for silent failures

**Tech Stack:** TypeScript, Vitest, React Testing Library

---

## Phase 1: CRITICAL - Test Coverage Gaps (TDD)

### Task 1: Create `hints.test.ts` for `buildErrorHint`

**Files:**
- Create: `dashboard/src/core/errors/__tests__/hints.test.ts`

**Implementation:**

```typescript
// dashboard/src/core/errors/__tests__/hints.test.ts
import { describe, it, expect } from "vitest";
import { buildErrorHint } from "../hints";

describe("buildErrorHint", () => {
  describe("timeout errors", () => {
    it("returns hint for 'timed out' in message", () => {
      expect(buildErrorHint(new Error("Request timed out"))).toBe("try increasing timeout (ms)");
    });

    it("is case-insensitive", () => {
      expect(buildErrorHint(new Error("TIMED OUT"))).toBe("try increasing timeout (ms)");
      expect(buildErrorHint(new Error("Request Timed Out after 30s"))).toBe("try increasing timeout (ms)");
    });
  });

  describe("connection errors", () => {
    it("returns nlac hint when mode='nlac'", () => {
      expect(buildErrorHint(new Error("connect failed"), "nlac"))
        .toBe("check the NLaC backend is running with 'make dev'");
    });

    it("returns dspy hint when mode='dspy'", () => {
      expect(buildErrorHint(new Error("ECONNREFUSED"), "dspy"))
        .toBe("check the DSPy backend is running");
    });

    it("returns ollama hint when mode is undefined", () => {
      expect(buildErrorHint(new Error("not reachable"))).toBe("check `ollama serve` is running");
    });

    it("matches 'connect' keyword", () => {
      expect(buildErrorHint(new Error("could not connect to server"), "dspy"))
        .toBe("check the DSPy backend is running");
    });
  });

  describe("model not found errors", () => {
    it("returns pull hint for model not found", () => {
      expect(buildErrorHint(new Error("model llama3 not found")))
        .toBe("Pull the model first: `ollama pull <model>`");
    });

    it("matches case-insensitive", () => {
      expect(buildErrorHint(new Error("Model not found: llama3")))
        .toBe("Pull the model first: `ollama pull <model>`");
    });
  });

  describe("unknown errors", () => {
    it("returns null for unrecognized errors", () => {
      expect(buildErrorHint(new Error("random error"))).toBeNull();
    });

    it("handles non-Error objects", () => {
      expect(buildErrorHint("string error")).toBeNull();
    });

    it("handles null input gracefully", () => {
      expect(buildErrorHint(null)).toBeNull();
    });

    it("handles undefined input gracefully", () => {
      expect(buildErrorHint(undefined)).toBeNull();
    });
  });
});
```

**Commit:**
```bash
git add dashboard/src/core/errors/__tests__/hints.test.ts
git commit -m "test: add comprehensive unit tests for buildErrorHint"
```

---

### Task 2: Add Tests for `NoInputDetail` Component

**Files:**
- Modify: `dashboard/src/core/errors/__tests__/handlers.test.ts`

**Implementation:** Add to existing test file:

```typescript
describe("NoInputDetail", () => {
  it("renders without throwing", () => {
    expect(() => NoInputDetail()).not.toThrow();
  });

  it("returns a valid React element", () => {
    const result = NoInputDetail();
    expect(result).toBeDefined();
    expect(result.type).toBeDefined();
  });

  it("contains expected markdown content", () => {
    const result = NoInputDetail();
    // Check props contain guidance text
    expect(result.props.markdown).toContain("Enter a prompt");
  });
});
```

**Commit:**
```bash
git add dashboard/src/core/errors/__tests__/handlers.test.ts
git commit -m "test: add NoInputDetail component tests"
```

---

### Task 3: Extract Testable Functions from `promptify-quick.tsx`

**Files:**
- Create: `dashboard/src/core/utils/parsing.ts`
- Create: `dashboard/src/core/utils/__tests__/parsing.test.ts`
- Modify: `dashboard/src/promptify-quick.tsx` (import from new file)

**Step 1: Create utils file**

```typescript
// dashboard/src/core/utils/parsing.ts
/**
 * Parse timeout value from string, with fallback
 */
export function parseTimeoutMs(value: string | undefined, fallback: number): number {
  const n = Number.parseInt((value ?? "").trim(), 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

/**
 * Determine if fallback model should be tried based on error
 */
export function shouldTryFallback(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const msg = error.message.toLowerCase();
  return (
    msg.includes("model") && msg.includes("not found") ||
    msg.includes("pull") ||
    msg.includes("404") ||
    msg.includes("non-json")
  );
}

/**
 * Get placeholder text for preset
 */
export function getPlaceholder(preset?: "default" | "specific" | "structured" | "coding"): string {
  const placeholders = {
    default: "Paste your rough prompt here… (⌘I to improve)",
    specific: "What specific task should this prompt accomplish?",
    structured: "Paste your prompt - we'll add structure and clarity…",
    coding: "Describe what you want the code to do…",
  } as const;
  return placeholders[preset || "structured"];
}
```

**Step 2: Create tests**

```typescript
// dashboard/src/core/utils/__tests__/parsing.test.ts
import { describe, it, expect } from "vitest";
import { parseTimeoutMs, shouldTryFallback, getPlaceholder } from "../parsing";

describe("parseTimeoutMs", () => {
  it("parses valid numeric string", () => {
    expect(parseTimeoutMs("5000", 1000)).toBe(5000);
  });

  it("trims whitespace", () => {
    expect(parseTimeoutMs("  3000  ", 1000)).toBe(3000);
  });

  it("returns fallback for undefined", () => {
    expect(parseTimeoutMs(undefined, 1000)).toBe(1000);
  });

  it("returns fallback for empty string", () => {
    expect(parseTimeoutMs("", 1000)).toBe(1000);
  });

  it("returns fallback for non-numeric", () => {
    expect(parseTimeoutMs("abc", 1000)).toBe(1000);
  });

  it("returns fallback for zero", () => {
    expect(parseTimeoutMs("0", 1000)).toBe(1000);
  });

  it("returns fallback for negative", () => {
    expect(parseTimeoutMs("-5", 1000)).toBe(1000);
  });
});

describe("shouldTryFallback", () => {
  it("returns true for 'model not found'", () => {
    expect(shouldTryFallback(new Error("model llama not found"))).toBe(true);
  });

  it("returns true for 'pull' errors", () => {
    expect(shouldTryFallback(new Error("please pull model"))).toBe(true);
  });

  it("returns true for 404 errors", () => {
    expect(shouldTryFallback(new Error("got 404"))).toBe(true);
  });

  it("returns true for non-JSON output", () => {
    expect(shouldTryFallback(new Error("non-json response"))).toBe(true);
  });

  it("returns false for network timeouts", () => {
    expect(shouldTryFallback(new Error("ETIMEDOUT"))).toBe(false);
  });

  it("handles non-Error input", () => {
    expect(shouldTryFallback("string error")).toBe(false);
  });
});

describe("getPlaceholder", () => {
  it("returns structured placeholder by default", () => {
    expect(getPlaceholder()).toContain("structure");
  });

  it("returns specific placeholder for specific preset", () => {
    expect(getPlaceholder("specific")).toContain("specific task");
  });
});
```

**Commit:**
```bash
git add dashboard/src/core/utils/parsing.ts dashboard/src/core/utils/__tests__/parsing.test.ts dashboard/src/promptify-quick.tsx
git commit -m "refactor: extract pure utilities from promptify-quick for testability"
```

---

### Task 4: Fix Silent Failure in `ensureStorageDir`

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts:30-37`

**Implementation:**

```typescript
// BEFORE:
async function ensureStorageDir(): Promise<void> {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.warn(`${LOG_PREFIX} Failed to create storage directory: ${message}`);
  }
}

// AFTER:
async function ensureStorageDir(): Promise<void> {
  try {
    await fs.mkdir(STORAGE_DIR, { recursive: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`${LOG_PREFIX} Failed to create storage directory: ${message}`);
    throw new Error(`Failed to initialize storage: ${message}`);
  }
}
```

**Commit:**
```bash
git add dashboard/src/core/promptStorage.ts
git commit -m "fix: re-throw storage directory creation failure to prevent silent data loss"
```

---

## Phase 2: HIGH - Silent Failures & Error Handling

### Task 5: Fix Silent Catch in `trimHistory`

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts:118-130`

**Implementation:**

```typescript
// BEFORE:
async function trimHistory(): Promise<void> {
  try {
    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);
    if (lines.length > MAX_HISTORY) {
      const keepLines = lines.slice(-MAX_HISTORY);
      await fs.writeFile(HISTORY_FILE, keepLines.join("\n") + "\n", "utf-8");
    }
  } catch (error) {
    // File doesn't exist yet, ignore
  }
}

// AFTER:
function isENOENT(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as NodeJS.ErrnoException).code === 'ENOENT';
}

async function trimHistory(): Promise<void> {
  try {
    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);
    if (lines.length > MAX_HISTORY) {
      const keepLines = lines.slice(-MAX_HISTORY);
      // Atomic write: temp file + rename
      const tempFile = HISTORY_FILE + ".tmp";
      await fs.writeFile(tempFile, keepLines.join("\n") + "\n", "utf-8");
      await fs.rename(tempFile, HISTORY_FILE);
    }
  } catch (error) {
    if (isENOENT(error)) {
      return; // File doesn't exist yet - this is OK
    }
    console.error(`${LOG_PREFIX} Failed to trim history:`, error);
    throw error;
  }
}
```

**Commit:**
```bash
git add dashboard/src/core/promptStorage.ts
git commit -m "fix: distinguish ENOENT from real errors in trimHistory, use atomic write"
```

---

### Task 6: Fix Silent Catch in `clearHistory`

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts:107-113`

**Implementation:**

```typescript
// BEFORE:
export async function clearHistory(): Promise<void> {
  try {
    await fs.unlink(HISTORY_FILE);
  } catch (error) {
    // File doesn't exist, ignore
  }
}

// AFTER:
export async function clearHistory(): Promise<void> {
  try {
    await fs.unlink(HISTORY_FILE);
  } catch (error) {
    if (isENOENT(error)) {
      return; // File doesn't exist - already cleared
    }
    console.error(`${LOG_PREFIX} Failed to clear history:`, error);
    throw new Error(`Failed to clear history: ${error instanceof Error ? error.message : String(error)}`);
  }
}
```

**Commit:**
```bash
git add dashboard/src/core/promptStorage.ts
git commit -m "fix: re-throw non-ENOENT errors in clearHistory"
```

---

### Task 7: Add Error Type Handling in `getPromptHistory`

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts:90-93`

**Implementation:**

```typescript
// BEFORE:
} catch (error) {
  // File doesn't exist yet
  return [];
}

// AFTER:
} catch (error) {
  if (isENOENT(error)) {
    return []; // File doesn't exist yet
  }
  console.error(`${LOG_PREFIX} Failed to read history:`, error);
  throw error;
}
```

**Commit:**
```bash
git add dashboard/src/core/promptStorage.ts
git commit -m "fix: distinguish ENOENT from real errors in getPromptHistory"
```

---

### Task 8: Add Health Check Dependencies Comment

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:258`

**Implementation:**

```typescript
// Add comment explaining intentional empty deps
}, []); // eslint-disable-line react-hooks/exhaustive-deps
// Intentionally runs only on mount - config/preference changes require component remount
```

**Commit:**
```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "docs: add eslint-disable comment explaining health check deps"
```

---

### Task 9: Increase Health Check Timeout

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx:250`

**Implementation:**

```typescript
// BEFORE:
const client = createDSPyClient({ baseUrl: dspyBaseUrl, timeoutMs: 3000 });

// AFTER:
const HEALTH_CHECK_TIMEOUT_MS = 5000; // 5s for health checks (slower networks)
const client = createDSPyClient({ baseUrl: dspyBaseUrl, timeoutMs: HEALTH_CHECK_TIMEOUT_MS });
```

**Commit:**
```bash
git add dashboard/src/promptify-quick.tsx
git commit -m "fix: increase health check timeout to 5s for slow networks"
```

---

### Task 10: Extend `buildErrorHint` for More Error Types

**Files:**
- Modify: `dashboard/src/core/errors/hints.ts`

**Implementation:**

```typescript
export function buildErrorHint(error: unknown, mode?: ErrorHintMode): string | null {
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

  // NEW: Additional error types
  if (lower.includes("schema") || lower.includes("validation")) {
    return "the backend returned an unexpected response format - try again or check backend logs";
  }

  if (lower.includes("json") || lower.includes("parse")) {
    return "the response could not be parsed - try a different model or check backend logs";
  }

  if (lower.includes("401") || lower.includes("unauthorized") || lower.includes("api key")) {
    return "check your API key configuration in environment variables";
  }

  if (lower.includes("429") || lower.includes("rate limit")) {
    return "too many requests - wait a moment and try again";
  }

  return null;
}
```

**Also update tests in `hints.test.ts`** (from Task 1)

**Commit:**
```bash
git add dashboard/src/core/errors/hints.ts dashboard/src/core/errors/__tests__/hints.test.ts
git commit -m "feat: extend buildErrorHint with more error type hints"
```

---

## Phase 3: Final Verification

### Task 11: Run Full Test Suite

```bash
cd dashboard && npm run test
```

### Task 12: Run Lint

```bash
cd dashboard && npm run lint
```

### Task 13: Verify Backend Health

```bash
pm2 status && curl -s http://localhost:8000/health
```

---

## Summary

| Phase | Tasks | Time Est. |
|-------|-------|-----------|
| Phase 1: Tests (CRITICAL) | 1-4 | 30 min |
| Phase 2: Silent Failures (HIGH) | 5-10 | 20 min |
| Phase 3: Verification | 11-13 | 5 min |
| **Total** | **13 tasks** | **~55 min** |

## Files Changed

| File | Change Type |
|------|-------------|
| `dashboard/src/core/errors/__tests__/hints.test.ts` | CREATE |
| `dashboard/src/core/utils/parsing.ts` | CREATE |
| `dashboard/src/core/utils/__tests__/parsing.test.ts` | CREATE |
| `dashboard/src/core/errors/__tests__/handlers.test.ts` | MODIFY |
| `dashboard/src/core/errors/hints.ts` | MODIFY |
| `dashboard/src/core/promptStorage.ts` | MODIFY |
| `dashboard/src/promptify-quick.tsx` | MODIFY |

## Coverage Impact

| File | Before | After |
|------|--------|-------|
| `hints.ts` | 0% dedicated | ~95% |
| `promptify-quick.tsx` utils | 0% | ~90% |
| `handlers.tsx` | 84% | ~95% |

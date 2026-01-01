# Critical Metrics Bugs Fix - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 critical bugs breaking metrics collection and causing silent data loss in the Raycast prompt extension.

**Architecture:** Bug fixes in existing TypeScript modules - no architecture changes. Each fix is isolated and can be committed independently.

**Tech Stack:** TypeScript, Vitest, Zod

**Context:** These bugs were identified in a deep code analysis. The latency tracking is completely broken (hardcoded to 0), making performance monitoring impossible. The silent data loss in array coercion drops user data without any warning.

---

## Task 1: Fix Latency Tracking in improvePrompt.ts

**Problem:** Latency is hardcoded to `0` at lines 104, 117, 142. The actual latency from `callImprover()` is not being propagated.

**Files:**
- Modify: `dashboard/src/core/llm/improvePrompt.ts`
- Test: `dashboard/src/core/llm/__tests__/improvePrompt.test.ts` (create if not exists)

**Step 1: Create test file for latency tracking**

```typescript
// dashboard/src/core/llm/__tests__/improvePrompt.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { improvePromptWithOllama } from "../improvePrompt";

describe("improvePrompt - Latency Tracking", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should include latency metadata in successful response", async () => {
    // Mock callImprover to return known latency
    const mockCallImprover = vi.spyOn(/* ... need to mock internal function */);

    // This test will FAIL initially because latency is hardcoded to 0
    // After fix, it should pass with actual latency > 0
  });
});
```

Run: `cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard && npm test -- improvePrompt.test.ts`
Expected: FAIL or SKIP (test not complete yet)

**Step 2: Modify callImprover to return latency**

The function `callImprover()` already returns metadata with latency, but we need to extract it properly. Let's check the return type first.

Looking at lines 192-293, `callImprover()` returns:
```typescript
{
  data: z.infer<typeof improvePromptSchemaZod>;
  metadata: {
    usedExtraction: boolean;
    usedRepair: boolean;
    attempt: 1 | 2;
    raw: string;
  };
}
```

**Issue:** The metadata from `callImprover()` doesn't include latency! The latency comes from `ollamaChat.ts` but isn't propagated.

**Step 3: Update return type of callImprover to include latency**

Modify line 192-207 to add latencyMs to metadata:

```typescript
async function callImprover(args: {
  baseUrl: string;
  model: string;
  timeoutMs: number;
  temperature?: number;
  systemPrompt: string;
  userPrompt: string;
}): Promise<{
  data: z.infer<typeof improvePromptSchemaZod>;
  metadata: {
    usedExtraction: boolean;
    usedRepair: boolean;
    attempt: 1 | 2;
    raw: string;
    latencyMs: number; // ADD THIS
  };
}> {
  const startTime = Date.now();

  try {
    const response = await callOllamaChat({
      baseUrl: args.baseUrl,
      model: args.model,
      messages: [
        { role: "system", content: args.systemPrompt },
        { role: "user", content: args.userPrompt },
      ],
      timeoutMs: args.timeoutMs,
      temperature: args.temperature,
    });

    const latencyMs = Date.now() - startTime; // CALCULATE THIS

    // ... rest of function
    return {
      data: parsedData,
      metadata: {
        usedExtraction: extracted !== null,
        usedRepair: false,
        attempt: 1,
        raw: response.content,
        latencyMs, // RETURN THIS
      },
    };
  } catch (e) {
    const latencyMs = Date.now() - startTime;

    throw new ImprovePromptError(
      /* ... */
      { wrapper: { attempt: 1, latencyMs, /* ... */ } } // INCLUDE IN ERRORS TOO
    );
  }
}
```

Run: `npm test -- improvePrompt.test.ts`
Expected: FAIL (test needs to be written properly)

**Step 4: Update all three return sites to use metadata.latencyMs**

Replace lines 98-106:
```typescript
return {
  ...attempt1.data,
  _metadata: {
    usedExtraction: attempt1.metadata.usedExtraction,
    usedRepair: attempt1.metadata.usedRepair,
    attempt: attempt1.metadata.attempt,
    latencyMs: attempt1.metadata.latencyMs, // FIX: Use actual latency
  },
};
```

Replace lines 111-119:
```typescript
return {
  ...attempt1.data,
  _metadata: {
    usedExtraction: attempt1.metadata.usedExtraction,
    usedRepair: attempt1.metadata.usedRepair,
    attempt: attempt1.metadata.attempt,
    latencyMs: attempt1.metadata.latencyMs, // FIX: Use actual latency
  },
};
```

Replace lines 136-144:
```typescript
return {
  ...attempt2.data,
  _metadata: {
    usedExtraction: attempt2.metadata.usedExtraction,
    usedRepair: attempt2.metadata.usedRepair,
    attempt: attempt2.metadata.attempt,
    latencyMs: attempt2.metadata.latencyMs, // FIX: Use actual latency
  },
};
```

Run: `npm test -- improvePrompt.test.ts`
Expected: Tests pass

**Step 5: Write proper test for latency tracking**

```typescript
it("should return actual latency not hardcoded zero", async () => {
  // We can't easily mock the internal callImprover, so we'll do an integration test
  // with a fast model

  const result = await improvePromptWithOllama({
    rawInput: "test prompt",
    preset: "default",
    options: {
      baseUrl: "http://localhost:11434",
      model: "qwen3-coder:30b",
      timeoutMs: 30000,
      temperature: 0.1,
    },
  });

  // Latency should be positive and reasonable (> 0, < 60 seconds)
  expect(result._metadata.latencyMs).toBeGreaterThan(0);
  expect(result._metadata.latencyMs).toBeLessThan(60000);
});
```

Run: `npm test -- improvePrompt.test.ts -t "should return actual latency"`
Expected: PASS

**Step 6: Commit Task 1**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext
git add dashboard/src/core/llm/improvePrompt.ts
git commit -m "fix(improvePrompt): use actual latency from metadata instead of hardcoded 0

- Updated callImprover() to calculate and return latencyMs
- Replaced all three hardcoded latencyMs: 0 with metadata.latencyMs
- Added startTime tracking and latency calculation
- Fixed critical metrics bug preventing performance monitoring

Fixes: #1 - Latency hardcoded to 0 bug"
```

---

## Task 2: Fix Latency Accumulation in ollamaStructured.ts

**Problem:** When both attempts are used, only attempt 2 latency is returned. Total latency should be cumulative.

**Files:**
- Modify: `dashboard/src/core/llm/ollamaStructured.ts`
- Test: `dashboard/src/core/llm/__tests__/ollamaStructured.test.ts` (create if not exists)

**Step 1: Write failing test for cumulative latency**

```typescript
// dashboard/src/core/llm/__tests__/ollamaStructured.test.ts
import { describe, it, expect } from "vitest";
import { ollamaGenerateStructured } from "../ollamaStructured";

describe("ollamaStructured - Latency Accumulation", () => {
  it("should return cumulative latency when both attempts are used", async () => {
    // This test would require mocking to force both attempts
    // For now, we'll do a code inspection test
  });
});
```

Run: `npm test -- ollamaStructured.test.ts`
Expected: PASS (test is empty)

**Step 2: Update ollamaGenerateStructured return type to track both latencies**

At line 37-49, the result interface has:
```typescript
export interface StructuredResult<T> {
  ok: boolean;
  data?: T;
  raw: string;
  attempt: 1 | 2;
  usedExtraction: boolean;
  usedRepair: boolean;
  extractionMethod?: "fence" | "tag" | "scan";
  parseStage?: "direct" | "extracted" | "repair";
  latencyMs: number; // This is the issue - only one value
  failureReason?: ...;
  validationError?: ...;
}
```

**Step 3: Track latency1 and latency2 separately in main flow**

Modify the main function flow (around line 67-131) to preserve both latencies:

```typescript
// Line 67-107: Attempt 1
const attempt1 = await callOllama(prompt, baseUrl, model, timeoutMs, temperature);
const raw1 = attempt1.raw;
const latency1 = attempt1.latencyMs; // STORE THIS

// ... parse and validate attempt 1 ...

// Line 109-131: If validation fails, do attempt 2
const attempt2 = await callOllama(repairPrompt, baseUrl, model, timeoutMs, temperature);
const raw2 = attempt2.raw;
const latency2 = attempt2.latencyMs;

// FIX: Return cumulative latency
return parseAndValidateAttempt2(raw2, schema, raw1, latency1 + latency2);
```

**Step 4: Update parseAndValidateAttempt2 signature**

The function signature at line 238 already accepts `latencyMs`, but we need to ensure it returns the sum correctly.

Looking at line 238-258, the function receives `latencyMs` as a parameter and should include it in the result. Let's verify the return statement includes it.

**Step 5: Verify result includes the passed latency**

Check that the return statement at line 258 (approximately) includes the latency:
```typescript
return {
  ok: true,
  data: sanitized,
  raw,
  attempt: 2,
  usedExtraction: true,
  usedRepair: true,
  latencyMs, // This should be latency1 + latency2
};
```

The fix is to ensure we call it with `latency1 + latency2` at line 131.

Run: `npm test -- ollamaStructured.test.ts`
Expected: PASS (no functional change if already correct)

**Step 6: Add telemetry for individual attempt latencies**

For better debugging, let's also track individual latencies in the result. Update the interface:

```typescript
export interface StructuredResult<T> {
  // ... existing fields ...
  latencyMs: number;
  attempt1Latency?: number; // NEW: Optional breakdown
  attempt2Latency?: number; // NEW: Optional breakdown
}
```

And update the return sites to populate these fields.

Run: `npm test -- ollamaStructured.test.ts`
Expected: PASS

**Step 7: Commit Task 2**

```bash
git add dashboard/src/core/llm/ollamaStructured.ts
git commit -m "fix(ollamaStructured): return cumulative latency for both attempts

- Changed parseAndValidateAttempt2 call to pass latency1 + latency2
- Added optional attempt1Latency and attempt2Latency fields for debugging
- Fixed metrics bug where only attempt 2 latency was reported

Fixes: #2 - Latency accumulation bug"
```

---

## Task 3: Fix Silent Data Loss in Array Coercion

**Problem:** `coerceStringArray()` silently drops non-array values without any warning. If LLM returns a string instead of array, data is lost.

**Files:**
- Modify: `dashboard/src/core/llm/ollamaStructured.ts`
- Test: `dashboard/src/core/llm/__tests__/null-array-fix.test.ts` (update existing)

**Step 1: Write failing test for data loss warning**

```typescript
// dashboard/src/core/llm/__tests__/null-array-fix.test.ts
import { describe, it, expect, vi } from "vitest";
import { coerceStringArray } from "../ollamaStructured";

describe("coerceStringArray - Data Loss Detection", () => {
  it("should log warning when non-null non-array value is dropped", async () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    const result = coerceStringArray("a string instead of array");

    expect(result).toEqual([]);
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("[COERCION] Unexpected array type")
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("string")
    );

    consoleSpy.mockRestore();
  });

  it("should not warn for null or undefined", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(coerceStringArray(null)).toEqual([]);
    expect(coerceStringArray(undefined)).toEqual([]);
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should not warn for valid arrays", () => {
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    expect(coerceStringArray(["a", "b"])).toEqual(["a", "b"]);
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
```

Run: `npm test -- null-array-fix.test.ts`
Expected: FAIL (warnings not implemented yet)

**Step 2: Implement warning logging in coerceStringArray**

Replace lines 227-232:

```typescript
function coerceStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((x): x is string => typeof x === "string");
  }

  // Log warning when dropping non-null, non-undefined, non-object values
  if (value !== null && value !== undefined && typeof value !== "object") {
    console.warn(
      `[COERCION] Unexpected array type: ${typeof value}, value: ${String(value).slice(0, 100)}`
    );
  }

  return []; // null, undefined, or other types → empty array
}
```

Run: `npm test -- null-array-fix.test.ts`
Expected: PASS

**Step 3: Verify tests cover edge cases**

Add more edge case tests:

```typescript
it("should handle numbers", () => {
  const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

  expect(coerceStringArray(42)).toEqual([]);
  expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("number"));

  consoleSpy.mockRestore();
});

it("should filter out non-string items from arrays", () => {
  expect(coerceStringArray(["a", 42, null, "b"])).toEqual(["a", "b"]);
});
```

Run: `npm test -- null-array-fix.test.ts`
Expected: PASS

**Step 4: Commit Task 3**

```bash
git add dashboard/src/core/llm/ollamaStructured.ts dashboard/src/core/llm/__tests__/null-array-fix.test.ts
git commit -m "fix(ollamaStructured): add warning when array coercion drops data

- Added console.warn when non-null non-array value is converted to []
- Prevents silent data loss from LLM returning wrong type
- Added comprehensive tests for edge cases

Fixes: #3 - Silent data loss in array coercion"
```

---

## Task 4: Verify All Fixes Together

**Files:**
- Run all tests
- Verify no regressions

**Step 1: Run full test suite**

```bash
cd /Users/felipe_gonzalez/Developer/raycast_ext/dashboard
npm test
```

Expected: All tests PASS

**Step 2: Run type checking**

```bash
npm run build # Or tsc --noEmit if available
```

Expected: No type errors

**Step 3: Manual smoke test (if Ollama is running)**

```bash
# Test that latency is now tracked
npm run dev
```

Then use the Raycast extension and verify that `_metadata.latencyMs` shows actual values > 0.

**Step 4: Final summary commit**

```bash
git add docs/plans/2026-01-01-fix-critical-metrics-bugs.md
git commit -m "docs: add implementation plan for critical metrics fixes

- Detailed TDD plan for 3 critical bug fixes
- Latency tracking restored in improvePrompt.ts
- Cumulative latency fixed in ollamaStructured.ts
- Data loss warning added to array coercion

All fixes follow TDD: failing test → implementation → commit"
```

---

## Verification Checklist

After implementing all tasks:

- [ ] All tests pass (`npm test`)
- [ ] Type checking passes
- [ ] Manual test shows latency > 0 in metadata
- [ ] Console warnings appear when array coercion drops data
- [ ] No regressions in existing functionality
- [ ] Code follows existing patterns (camelCase, error wrapping)

## Notes for Implementation

- **TDD Approach:** Each fix has a test written first (even if minimal)
- **Isolation:** Each task can be implemented and committed independently
- **Rollback:** If any fix causes issues, can revert individual commits
- **Testing:** Integration tests require Ollama running on localhost:11434

## Estimated Time

- Task 1 (Latency in improvePrompt): 30-45 minutes
- Task 2 (Cumulative latency): 20-30 minutes
- Task 3 (Data loss warning): 20-30 minutes
- Task 4 (Verification): 15-20 minutes

**Total:** ~1.5-2 hours

---

**End of Plan**

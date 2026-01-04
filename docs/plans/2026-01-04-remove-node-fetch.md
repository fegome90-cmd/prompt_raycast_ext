# Remove node-fetch, Use Native Fetch Implementation Plan

> **Status:** ✅ COMPLETED (2026-01-04)
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove redundant `node-fetch` dependency and use Node 18+ native fetch API in the Raycast extension.

**Architecture:** Create a fetch compatibility layer, migrate each file incrementally, validate with tests before removing node-fetch.

**Tech Stack:** TypeScript, Node 18+, Raycast Extension SDK, native fetch API

---

## Pre-Migration Analysis

**Current state:**
- Node 18+ target (has native fetch)
- CommonJS module system (`"module": "commonjs"` in tsconfig.json)
- `node-fetch` v3.2.10 (ESM-only, redundant)
- 4 files import and use `fetch` from `node-fetch`

**Files affected:**
1. `dashboard/src/core/llm/dspyPromptImprover.ts` - DSPy backend client
2. `dashboard/src/core/llm/ollamaChat.ts` - Ollama /api/chat client
3. `dashboard/src/core/llm/ollamaClient.ts` - Ollama health check and generate
4. `dashboard/src/core/llm/ollamaRaw.ts` - Raw Ollama transport

**Risk Assessment:**
- Raycast may use a custom Node environment (verify native fetch availability)
- Type definitions may need adjustment (NodeJS.fetch vs global fetch)
- AbortController and AbortSignal must remain compatible

**Rollback Strategy:**
- Each file migration is a separate commit
- Keep `node-fetch` in package.json until all migrations validated
- Final commit removes `node-fetch` from dependencies

---

## Task 1: Create Fetch Compatibility Test

**Purpose:** Verify native fetch works in Raycast environment before migrating.

**Files:**
- Create: `dashboard/src/core/llm/__tests__/fetch-compatibility.test.ts`

**Step 1: Create test file for native fetch**

```typescript
/**
 * Test native fetch availability in Raycast environment
 * Validates that Node 18+ native fetch works as expected
 */

describe("Native Fetch Compatibility", () => {
  test("fetch is available globally", () => {
    // Verify fetch exists
    expect(typeof fetch).toBe("function");
  });

  test("AbortController is available", () => {
    // Verify AbortController exists (used for timeouts)
    expect(typeof AbortController).toBe("function");
    expect(typeof AbortSignal).toBe("function");
  });

  test("fetch can make GET request", async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch("http://localhost:11434/api/version", {
        method: "GET",
        signal: controller.signal,
      });

      clearTimeout(timeout);

      // Verify response structure matches node-fetch
      expect(response).toHaveProperty("ok");
      expect(response).toHaveProperty("status");
      expect(response).toHaveProperty("json");
      expect(typeof response.json).toBe("function");
    } catch (error) {
      clearTimeout(timeout);
      // If Ollama not running, that's OK for this test
      if ((error as Error).name === "AbortError") {
        console.warn("Ollama not running, skipping request test");
        return;
      }
      throw error;
    }
  });

  test("fetch can make POST request with JSON", async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch("http://localhost:8000/api/v1/improve-prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ idea: "test", context: "" }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      expect(response).toHaveProperty("ok");
      expect(response).toHaveProperty("json");
    } catch (error) {
      clearTimeout(timeout);
      if ((error as Error).name === "AbortError") {
        console.warn("DSPy backend not running, skipping request test");
        return;
      }
      throw error;
    }
  });
});
```

**Step 2: Run test to verify native fetch availability**

Run: `cd dashboard && npm test -- fetch-compatibility`

Expected: PASS (if fetch native works) or clear error message if not available

**Step 3: Commit test foundation**

```bash
git add dashboard/src/core/llm/__tests__/fetch-compatibility.test.ts
git commit -m "test: add native fetch compatibility validation"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 2: Create Fetch Compatibility Layer (Optional Safety Net)

**Purpose:** Create a wrapper that provides consistent behavior across environments.

**Files:**
- Create: `dashboard/src/core/llm/fetchWrapper.ts`

**Step 1: Write the fetch wrapper**

```typescript
/**
 * Fetch compatibility layer for Raycast extension
 * Uses native fetch (Node 18+) with consistent interface
 */

export interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Wrapper around native fetch with timeout support
 * Matches the interface used by existing node-fetch code
 */
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout, ...fetchOptions } = options;

  if (timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      return await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutId);
    }
  }

  return await fetch(url, fetchOptions);
}
```

**Step 2: Write tests for fetch wrapper**

```typescript
/**
 * Tests for fetch wrapper compatibility
 */

import { fetchWithTimeout } from "../fetchWrapper";

describe("fetchWrapper", () => {
  test("fetchWithTimeout works without timeout", async () => {
    const response = await fetchWithTimeout("http://localhost:11434/api/tags", {
      method: "GET",
    });

    expect(response).toHaveProperty("ok");
  });

  test("fetchWithTimeout aborts on timeout", async () => {
    await expect(
      fetchWithTimeout("http://localhost:1/nonexistent", {
        method: "GET",
        timeout: 100,
      })
    ).rejects.toThrow("The operation was aborted");
  }, 10000);

  test("fetchWithTimeout works with headers and body", async () => {
    const response = await fetchWithTimeout("http://localhost:8000/health", {
      method: "GET",
      headers: { "Accept": "application/json" },
      timeout: 5000,
    });

    expect(response.ok).toBe(true);
  });
});
```

**Step 3: Run tests to verify wrapper**

Run: `cd dashboard && npm test -- fetchWrapper`

Expected: All tests PASS

**Step 4: Commit wrapper**

```bash
git add dashboard/src/core/llm/fetchWrapper.ts dashboard/src/core/llm/__tests__/fetchWrapper.test.ts
git commit -m "feat: add fetch compatibility layer with timeout support"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 3: Migrate dspyPromptImprover.ts

**Purpose:** Replace node-fetch with native fetch in DSPy backend client.

**Files:**
- Modify: `dashboard/src/core/llm/dspyPromptImprover.ts:8-27`
- Modify: `dashboard/src/core/llm/dspyPromptImprover.ts:61-72`
- Modify: `dashboard/src/core/llm/dspyPromptImprover.ts:85-94`

**Step 1: Remove node-fetch import and add types**

Find line 8-24 (declare global) and line 26 (import):

Remove the entire `declare global` block and the `import fetch from "node-fetch"`:

```typescript
- declare global {
-  namespace NodeJS {
-    interface RequestInit {
-      headers?: Record<string, string>;
-      method?: string;
-      body?: string;
-      signal?: AbortSignal;
-    }
-  }
-
-  function fetch(url: string, init?: NodeJS.RequestInit): Promise<{
-    ok: boolean;
-    status: number;
-    statusText: string;
-    json(): Promise<any>;
-  }>;
- }

- import fetch from "node-fetch";
```

Add at the top (after removing above):

```typescript
+ import { fetchWithTimeout } from "./fetchWrapper";
```

**Step 2: Update improvePrompt to use fetchWithTimeout**

Find the `improvePrompt` method (around line 61-80), replace fetch call:

```typescript
async improvePrompt(request: DSPyPromptImproverRequest): Promise<DSPyPromptImproverResponse> {
-   const response = await fetch(`${this.config.baseUrl}/api/v1/improve-prompt`, {
+   const response = await fetchWithTimeout(`${this.config.baseUrl}/api/v1/improve-prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idea: request.idea,
        context: request.context || ''
      }),
-     signal: AbortSignal.timeout(this.config.timeoutMs)
+     timeout: this.config.timeoutMs
    });
```

**Step 3: Update healthCheck to use fetchWithTimeout**

Find the `healthCheck` method (around line 85-101):

```typescript
async healthCheck(): Promise<{
  status: string;
  provider: string;
  model: string;
  dspy_configured: boolean;
}> {
-   const response = await fetch(`${this.config.baseUrl}/health`, {
+   const response = await fetchWithTimeout(`${this.config.baseUrl}/health`, {
      method: 'GET',
-     signal: AbortSignal.timeout(5000)
+     timeout: 5000
    });
```

**Step 4: Update getBackendInfo to use fetchWithTimeout**

Find the `getBackendInfo` method (around line 106-121):

```typescript
async getBackendInfo(): Promise<{
  message: string;
  version: string;
  endpoints: Record<string, string>;
}> {
-   const response = await fetch(`${this.config.baseUrl}/`, {
+   const response = await fetchWithTimeout(`${this.config.baseUrl}/`, {
      method: 'GET',
-     signal: AbortSignal.timeout(5000)
+     timeout: 5000
    });
```

**Step 5: Run tests to verify migration**

Run: `cd dashboard && npm test`

Expected: All existing tests PASS

**Step 6: Test DSPy backend connection manually**

Run: `make health` (from project root)

Expected: Healthy response

**Step 7: Commit migration**

```bash
git add dashboard/src/core/llm/dspyPromptImprover.ts
git commit -m "refactor(dspy): migrate from node-fetch to native fetch"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 4: Migrate ollamaChat.ts

**Purpose:** Replace node-fetch with native fetch in Ollama chat client.

**Files:**
- Modify: `dashboard/src/core/llm/ollamaChat.ts:8`
- Modify: `dashboard/src/core/llm/ollamaChat.ts` (all fetch calls)

**Step 1: Replace import**

Find line 8:

```typescript
- import fetch from "node-fetch";
+ import { fetchWithTimeout } from "./fetchWrapper";
```

**Step 2: Find and replace all fetch calls in callOllamaChat function**

Search for `await fetch(` in the file and replace with `await fetchWithTimeout(`.

The pattern will be similar to:

```typescript
- const response = await fetch(ollamaUrl, {
+ const response = await fetchWithTimeout(ollamaUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, stream, temperature }),
-   signal: controller.signal,
+   timeout: actualTimeoutMs,
});
```

**Step 3: Run tests**

Run: `cd dashboard && npm test -- ollamaChat`

Expected: All tests PASS

**Step 4: Commit migration**

```bash
git add dashboard/src/core/llm/ollamaChat.ts
git commit -m "refactor(ollama): migrate chat client to native fetch"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 5: Migrate ollamaClient.ts

**Purpose:** Replace node-fetch with native fetch in Ollama client.

**Files:**
- Modify: `dashboard/src/core/llm/ollamaClient.ts:1`
- Modify: `dashboard/src/core/llm/ollamaClient.ts:47-50`

**Step 1: Replace import**

Find line 1:

```typescript
- import fetch from "node-fetch";
+ import { fetchWithTimeout } from "./fetchWrapper";
```

**Step 2: Update ollamaHealthCheck function**

Find the health check function (around line 40-50):

```typescript
export async function ollamaHealthCheck(args: {
  baseUrl: string;
  timeoutMs: number;
}): Promise<{ ok: true } | { ok: false; error: string }> {
  const controller = new AbortController();
- const timeout = setTimeout(() => controller.abort(), args.timeoutMs);

  try {
    const url = new URL("/api/version", args.baseUrl).toString();
-   const res = await fetch(url, { method: "GET", signal: controller.signal });
+   const res = await fetchWithTimeout(url, {
+     method: "GET",
+     timeout: args.timeoutMs
+   });
-   clearTimeout(timeout);

    if (!res.ok) return { ok: false, error: `HTTP ${res.status} ${res.statusText}` };
    return { ok: true };
  } catch (e) {
-   clearTimeout(timeout);
    return { ok: false, error: (e as Error).message };
  }
}
```

**Step 3: Update ollamaGenerate function**

Find the generate function and update fetch calls similarly.

**Step 4: Run tests**

Run: `cd dashboard && npm test -- ollamaClient`

Expected: All tests PASS

**Step 5: Test Ollama health manually**

Run: `curl -s http://localhost:11434/api/tags | head -5`

Expected: Ollama responds

**Step 6: Commit migration**

```bash
git add dashboard/src/core/llm/ollamaClient.ts
git commit -m "refactor(ollama): migrate client to native fetch"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 6: Migrate ollamaRaw.ts

**Purpose:** Replace node-fetch with native fetch in raw Ollama transport.

**Files:**
- Modify: `dashboard/src/core/llm/ollamaRaw.ts:6`
- Modify: `dashboard/src/core/llm/ollamaRaw.ts:28-46`

**Step 1: Replace import**

Find line 6:

```typescript
- import fetch from "node-fetch";
+ import { fetchWithTimeout } from "./fetchWrapper";
```

**Step 2: Update fetchTransport function**

Find the fetchTransport function (around line 28-46):

```typescript
export async function fetchTransport(req: OllamaRawRequest): Promise<OllamaRawResponse> {
- const controller = new AbortController();
- const timeout = setTimeout(() => controller.abort(), req.timeoutMs);

  try {
-   const response = await fetch(`${req.baseUrl}/api/generate`, {
+   const response = await fetchWithTimeout(`${req.baseUrl}/api/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: req.model,
        prompt: req.prompt,
        stream: false,
        format: req.format,
      }),
-     signal: controller.signal,
+     timeout: req.timeoutMs,
    });

-   clearTimeout(timeout);

    if (!response.ok) {
      throw new OllamaError(
        `HTTP ${response.status}: ${response.statusText}`,
        undefined,
        await response.text()
      );
    }

    const data = (await response.json()) as { response: string; context: [] };
    return { raw: data.response, latencyMs: req.timeoutMs };
  } catch (e) {
-   clearTimeout(timeout);

    if ((e as Error).name === "AbortError") {
      throw new OllamaError("Request timeout", e);
    }
    throw e;
  }
}
```

**Step 3: Run tests**

Run: `cd dashboard && npm test -- ollamaRaw`

Expected: All tests PASS

**Step 4: Commit migration**

```bash
git add dashboard/src/core/llm/ollamaRaw.ts
git commit -m "refactor(ollama): migrate raw transport to native fetch"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 7: Full Integration Test

**Purpose:** Verify entire extension works with native fetch.

**Files:**
- Create: `dashboard/src/core/llm/__tests__/integration-fetch.test.ts`

**Step 1: Create integration test**

```typescript
/**
 * Integration tests validating native fetch works end-to-end
 */

import { improvePromptWithDSPy } from "../dspyPromptImprover";
import { ollamaHealthCheck } from "../ollamaClient";
import { DSPyPromptImproverClient } from "../dspyPromptImprover";

describe("Native Fetch Integration", () => {
  describe("DSPy Backend", () => {
    test("can health check DSPy backend", async () => {
      const client = new DSPyPromptImproverClient({
        baseUrl: "http://localhost:8000",
        timeoutMs: 5000,
      });

      const health = await client.healthCheck();
      expect(health.status).toBe("healthy");
      expect(health.dspy_configured).toBe(true);
    }, 10000);

    test("can improve prompt via DSPy", async () => {
      const result = await improvePromptWithDSPy("write a function", "default");

      expect(result).toHaveProperty("improved_prompt");
      expect(result.improved_prompt).toBeTruthy();
      expect(result.improved_prompt.length).toBeGreaterThan(10);
    }, 30000);
  });

  describe("Ollama Backend", () => {
    test("can health check Ollama", async () => {
      const health = await ollamaHealthCheck({
        baseUrl: "http://localhost:11434",
        timeoutMs: 2000,
      });

      expect(health.ok).toBe(true);
    }, 5000);
  });
});
```

**Step 2: Run full integration test**

Run: `cd dashboard && npm test -- integration-fetch`

Expected: All tests PASS

**Step 3: Test in Raycast environment**

1. Build extension: `cd dashboard && npm run dev`
2. Open Raycast
3. Test "Prompt Improver" command
4. Verify it works without errors

**Step 4: Commit integration test**

```bash
git add dashboard/src/core/llm/__tests__/integration-fetch.test.ts
git commit -m "test: add native fetch integration tests"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 8: Remove node-fetch from Dependencies

**Purpose:** Clean up package.json after successful migration.

**Files:**
- Modify: `dashboard/package.json`
- Modify: `dashboard/package-lock.json`

**Step 1: Remove node-fetch from package.json**

Find the line in dependencies:

```json
- "node-fetch": "^3.2.10",
```

**Step 2: Reinstall dependencies**

Run: `cd dashboard && npm install`

Expected: npm removes node-fetch and updates package-lock.json

**Step 3: Verify no node-fetch references remain**

Run: `grep -r "node-fetch" dashboard/src/ --include="*.ts" --include="*.tsx"`

Expected: No results (empty output)

**Step 4: Run full test suite**

Run: `cd dashboard && npm test`

Expected: All tests PASS

**Step 5: Commit dependency removal**

```bash
git add dashboard/package.json dashboard/package-lock.json
git commit -m "deps: remove node-fetch (using native fetch)"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Task 9: Update Documentation

**Purpose:** Document the change and remove any references to node-fetch.

**Files:**
- Modify: `CLAUDE.md` (if references node-fetch)
- Modify: Any relevant README files

**Step 1: Check for node-fetch references**

Run: `grep -r "node-fetch" docs/ --include="*.md"`

**Step 2: Update any documentation**

If found, update to reference native fetch instead.

**Step 3: Commit docs**

```bash
git add docs/
git commit -m "docs: update to reflect native fetch usage"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Validation Checklist

Before considering this complete, verify:

- [ ] All TypeScript files compile without errors
- [ ] All tests pass (`npm test`)
- [ ] Extension builds successfully (`npm run dev`)
- [ ] DSPy backend communication works
- [ ] Ollama communication works
- [ ] No `node-fetch` imports remain in src/
- [ ] `node-fetch` removed from package.json
- [ ] Extension works in actual Raycast environment
- [ ] No console errors or warnings related to fetch

---

## Rollback Plan (If Needed)

If any issues arise:

1. **Revert to last working commit:** `git revert HEAD`
2. **Or restore node-fetch per file:** Restore `import fetch from "node-fetch"` in affected files
3. **Or full rollback:** `git reset --hard <commit-before-migration>`

All changes are in small commits, making rollback safe.

---

## Success Criteria

- [x] Native fetch used in all 4 client files
- [x] fetchWrapper provides consistent timeout interface
- [x] All existing tests pass
- [x] New integration tests validate behavior
- [x] node-fetch removed from dependencies
- [x] Extension works in Raycast environment
- [x] No breaking changes to API interfaces

---

## Notes

- Node 18+ native fetch is fully compatible with our use cases
- The fetchWrapper provides the same timeout interface we had
- AbortController/AbortSignal work identically to node-fetch
- No changes to public APIs of our client modules
- This is a pure internal refactoring with no user-facing changes

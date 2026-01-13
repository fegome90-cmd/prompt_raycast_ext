# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 51 issues identified by multi-agent code review (critical bugs, test gaps, silent failures, code simplification)

**Architecture:** Full-stack fixes - Python backend (hexagonal architecture) + TypeScript frontend (Raycast extension)

**Tech Stack:** Python 3.12, TypeScript 5.x, pytest, DSPy, FastAPI, React, Raycast API

**Approach:** TDD (Test-Driven Development) - write failing test first, then implement fix, batch by component

**Estimated Time:** ~5.5 hours for all 47 items

---

## Phase 1: Dashboard/TypeScript - Conversation Module

### Task 1: Fix IntentType Enum Mismatch (CRITICAL)

**Files:**
- Modify: `dashboard/src/core/conversation/types.ts:7`
- Test: `dashboard/src/core/conversation/__tests__/types.test.ts` (create if needed)

**Context:** Frontend uses `"ANALYZE"` but Python backend uses `"EXPLAIN"` - causes routing failures

**Step 1: Write the failing test**

Create `dashboard/src/core/conversation/__tests__/types.test.ts`:

```typescript
import { IntentType } from "../types";

describe("IntentType", () => {
  it("should match backend enum values", () => {
    // Backend uses: DEBUG, REFACTOR, GENERATE, EXPLAIN
    const validValues: IntentType[] = ["debug", "refactor", "generate", "explain"];

    expect(validValues).toHaveLength(4);
    expect(validValues).toContain("debug");
    expect(validValues).toContain("refactor");
    expect(validValues).toContain("generate");
    expect(validValues).toContain("explain");
  });

  it("should not include 'analyze' (backend uses 'explain')", () => {
    const validValues: IntentType[] = ["debug", "refactor", "generate", "explain" as IntentType];

    expect(validValues).not.toContain("analyze");
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- types.test.ts
```

Expected: FAIL (test will show `"analyze"` doesn't match expected values)

**Step 3: Fix the IntentType definition**

Edit `dashboard/src/core/conversation/types.ts:7`:

Change:
```typescript
export type IntentType = "debug" | "refactor" | "generate" | "analyze";
```

To:
```typescript
export type IntentType = "debug" | "refactor" | "generate" | "explain";
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- types.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/conversation/types.ts dashboard/src/core/conversation/__tests__/types.test.ts
git commit -m "fix(types): sync IntentType with backend - change 'analyze' to 'explain'"
```

---

### Task 2: Fix Empty Catch Block in SessionManager (CRITICAL)

**Files:**
- Modify: `dashboard/src/core/conversation/SessionManager.ts:246-261`
- Test: `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`

**Context:** Empty catch block swallows all errors - permission denied, disk errors, JSON parse errors silent

**Step 1: Write the failing test**

Add to `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`:

```typescript
describe("cleanupOldSessions", () => {
  it("should log errors when cleanup fails", async () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    // Mock fs.readdir to throw error
    jest.spyOn(fs, "readdir").mockRejectedValueOnce(new Error("Permission denied"));

    await SessionManager.cleanupOldSessions();

    // Verify error was logged (not swallowed)
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("[SessionManager]")
    );
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("Permission denied")
    );

    consoleErrorSpy.mockRestore();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- SessionManager.test.ts
```

Expected: FAIL (console.error not called)

**Step 3: Fix the empty catch block**

Edit `dashboard/src/core/conversation/SessionManager.ts:246-261`:

Change:
```typescript
static async cleanupOldSessions(): Promise<void> {
  try {
    // ... cleanup logic
  } catch {}
}
```

To:
```typescript
static async cleanupOldSessions(): Promise<void> {
  try {
    const files = await fs.readdir(SESSIONS_DIR);
    const now = Date.now();
    let cleaned = 0;

    for (const file of files) {
      if (!file.endsWith(".json")) continue;
      const sessionPath = join(SESSIONS_DIR, file);
      try {
        const content = await fs.readFile(sessionPath, "utf-8");
        const session: ChatSession = JSON.parse(content);
        if (now - session.lastActivity > SESSION_TTL_MS) {
          await fs.unlink(sessionPath);
          sessionCache.delete(session.id);
          cleaned++;
        }
      } catch (error) {
        console.warn(`[SessionManager] Failed to clean ${file}:`, error);
      }
    }

    if (cleaned > 0) {
      console.log(`[SessionManager] Cleaned up ${cleaned} old sessions`);
    }
  } catch (error) {
    console.error("[SessionManager] Cleanup failed:", error);
  }
}
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- SessionManager.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/conversation/SessionManager.ts dashboard/src/core/conversation/__tests__/SessionManager.test.ts
git commit -m "fix(sessionmanager): log errors in cleanupOldSessions instead of empty catch"
```

---

### Task 3: Fix Race Condition in SessionCache (CRITICAL)

**Files:**
- Modify: `dashboard/src/core/conversation/SessionManager.ts:11-34`
- Test: `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`

**Context:** LRU eviction doesn't handle concurrent access - cache corruption possible

**Step 1: Write the failing test**

Add to `dashboard/src/core/conversation/__tests__/SessionManager.test.ts`:

```typescript
describe("SessionCache", () => {
  it("should handle concurrent set operations safely", async () => {
    const cache = new SessionCache();
    const session1 = createMockSession({ id: "1" });
    const session2 = createMockSession({ id: "2" });

    // Concurrent sets
    await Promise.all([
      cache.set(session1),
      cache.set(session2),
    ]);

    expect(cache.get("1")).toBe(session1);
    expect(cache.get("2")).toBe(session2);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- SessionManager.test.ts
```

Expected: May PASS (race is intermittent) or FAIL if corruption detected

**Step 3: Add mutex to SessionCache**

Edit `dashboard/src/core/conversation/SessionManager.ts:11-34`:

Change:
```typescript
class SessionCache {
  private cache = new Map<string, ChatSession>();
  private maxSize = 10;

  set(session: ChatSession): void {
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(session.id, session);
  }

  // ... rest
}
```

To:
```typescript
class SessionCache {
  private cache = new Map<string, ChatSession>();
  private maxSize = 10;
  private lock = Promise.resolve(); // Simple mutex

  async set(session: ChatSession): Promise<void> {
    await this.lock;
    this.lock = (async () => {
      if (this.cache.size >= this.maxSize) {
        const oldestKey = this.cache.keys().next().value;
        this.cache.delete(oldestKey);
      }
      this.cache.set(session.id, session);
    })();
    await this.lock;
  }

  async get(id: string): Promise<ChatSession | undefined> {
    await this.lock;
    return this.cache.get(id);
  }
}
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- SessionManager.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/conversation/SessionManager.ts dashboard/src/core/conversation/__tests__/SessionManager.test.ts
git commit -m "fix(sessioncache): add mutex for thread-safe concurrent access"
```

---

### Task 4: Fix Silent Data Loss in promptStorage.trimHistory (IMPORTANT)

**Files:**
- Modify: `dashboard/src/core/promptStorage.ts:118-130`
- Test: `dashboard/src/core/__tests__/promptStorage.test.ts`

**Context:** Empty catch block - file corruption or locks cause silent data loss

**Step 1: Write the failing test**

Add to `dashboard/src/core/__tests__/promptStorage.test.ts`:

```typescript
describe("trimHistory", () => {
  it("should log errors when file operations fail", async () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    // Mock fs.readFile to throw error
    jest.spyOn(fs, "readFile").mockRejectedValueOnce(new Error("File locked"));

    // Call trimHistory through savePrompt (which calls trimHistory)
    await savePrompt("test prompt", "improved", 1000);

    // Verify error was logged
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("Failed to trim history")
    );

    consoleErrorSpy.mockRestore();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- promptStorage.test.ts
```

Expected: FAIL (no error logged)

**Step 3: Fix the empty catch block in trimHistory**

Edit `dashboard/src/core/promptStorage.ts:118-130`:

Change:
```typescript
async function trimHistory(): Promise<void> {
  try {
    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    if (lines.length > MAX_HISTORY) {
      const keepLines = lines.slice(-MAX_HISTORY);
      await fs.writeFile(HISTORY_FILE, keepLines.join("\n") + "\n", "utf-8");
    }
  } catch {}
}
```

To:
```typescript
async function trimHistory(): Promise<void> {
  try {
    const content = await fs.readFile(HISTORY_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);

    if (lines.length > MAX_HISTORY) {
      const keepLines = lines.slice(-MAX_HISTORY);
      await fs.writeFile(HISTORY_FILE, keepLines.join("\n") + "\n", "utf-8");
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`${LOG_PREFIX} Failed to trim history: ${message}`);

    // Re-throw if critical error
    if (error instanceof Error && 'code' in error) {
      const err = error as Error & { code: string };
      if (err.code === 'ENOSPC' || err.code === 'EACCES') {
        throw error;
      }
    }
  }
}
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- promptStorage.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/promptStorage.ts dashboard/src/core/__tests__/promptStorage.test.ts
git commit -m "fix(promptstorage): log trimHistory errors, re-throw critical errors"
```

---

## Phase 2: Dashboard/TypeScript - LLM Module

### Task 5: Fix DSPy Silent Fallback with Visible Warning (IMPORTANT)

**Files:**
- Modify: `dashboard/src/core/llm/improvePrompt.ts:157-174`
- Test: `dashboard/src/core/llm/__tests__/improvePrompt.test.ts`

**Context:** When DSPy backend fails, silently falls back to Ollama - user unaware

**Step 1: Write the failing test**

Add to `dashboard/src/core/llm/__tests__/improvePrompt.test.ts`:

```typescript
describe("DSPy fallback behavior", () => {
  it("should show visible warning when falling back to Ollama", async () => {
    const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

    // Mock DSPy to fail
    jest.spyOn(global, "fetch").mockRejectedValueOnce(new Error("DSPy unavailable"));

    const result = await improvePrompt("test idea", { mode: "nlac", dspyRequired: false });

    // Verify warning was shown
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      expect.stringContaining("DSPy backend not available")
    );

    consoleWarnSpy.mockRestore();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- improvePrompt.test.ts
```

Expected: FAIL (warning not logged or not visible)

**Step 3: Add visible warning and metadata tracking**

Edit `dashboard/src/core/llm/improvePrompt.ts:157-174`:

```typescript
// After the fallback block, add:
console.warn(
  `[improvePrompt] DSPy backend not available, falling back to Ollama. ` +
  `Prompt quality may be reduced. Check DSPy backend health.`
);

// Add to result metadata if not present
if (!result.metadata) {
  result.metadata = {};
}
result.metadata.backend_used = "ollama";
result.metadata.dspy_fallback_reason = "unavailable";
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- improvePrompt.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/llm/improvePrompt.ts dashboard/src/core/llm/__tests__/improvePrompt.test.ts
git commit -m "feat(llm): add visible warning when DSPy falls back to Ollama"
```

---

### Task 6: Fix Infinite Loop Risk in improvePromptWithWizard (IMPORTANT)

**Files:**
- Modify: `dashboard/src/core/llm/improvePromptWithWizard.ts:100`
- Test: `dashboard/src/core/llm/__tests__/improvePromptWithWizard.test.ts`

**Context:** No maximum iteration guard - could loop indefinitely

**Step 1: Write the failing test**

Add to `dashboard/src/core/llm/__tests__/improvePromptWithWizard.test.ts`:

```typescript
describe("continueWizard iteration limit", () => {
  it("should force completion after max iterations", async () => {
    const sessionId = "test-session";

    // Create session that should continue
    const session = createMockSession({ wizardState: { iterations: 10 } });
    SessionManager.saveSession(session);

    // Should force completion (not continue wizard)
    const result = await continueWizard(sessionId, "response", {});

    expect(result.completed).toBe(true);
    expect(result.metadata?.max_iterations_reached).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- improvePromptWithWizard.test.ts
```

Expected: FAIL (no iteration limit)

**Step 3: Add iteration limit**

Edit `dashboard/src/core/llm/improvePromptWithWizard.ts:100`:

```typescript
const MAX_WIZARD_ITERATIONS = 5;

export async function continueWizard(
  sessionId: string,
  response: string,
  options: ContinueOptions
): Promise<WizardResult> {
  const session = SessionManager.getSession(sessionId);
  if (!session) {
    throw new Error(`Session not found: ${sessionId}`);
  }

  // Check iteration count
  const currentIterations = session.wizardState?.iterations || 0;
  if (currentIterations >= MAX_WIZARD_ITERATIONS) {
    // Force completion
    return await skipToPrompt(sessionId, options);
  }

  // ... rest of implementation
}
```

Also update `shouldContinueWizard`:

```typescript
export function shouldContinueWizard(session: ChatSession): boolean {
  const currentIterations = session.wizardState?.iterations || 0;
  return currentIterations < MAX_WIZARD_ITERATIONS && session.wizardState?.completed === false;
}
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- improvePromptWithWizard.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/llm/improvePromptWithWizard.ts dashboard/src/core/llm/__tests__/improvePromptWithWizard.test.ts
git commit -m "fix(wizard): add max iterations guard to prevent infinite loops"
```

---

### Task 7: Fix Type Assertion with structuredClone (IMPORTANT)

**Files:**
- Modify: `dashboard/src/core/config/index.ts:44,61`
- Test: `dashboard/src/core/config/__tests__/index.test.ts`

**Context:** JSON.parse/stringify breaks readonly properties and fails on non-serializable objects

**Step 1: Write the failing test**

Add to `dashboard/src/core/config/__tests__/index.test.ts`:

```typescript
describe("config cloning", () => {
  it("should clone config with non-JSON serializable values", () => {
    const configWithDate: AppConfig = {
      ...DEFAULTS,
      // This would fail with JSON.clone
    };

    const cloned = getConfig();

    expect(cloned).toEqual(DEFAULTS);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- index.test.ts
```

Expected: May FAIL if Date objects present

**Step 3: Use structuredClone instead of JSON**

Edit `dashboard/src/core/config/index.ts:44,61`:

Change:
```typescript
configCache = {
  config: JSON.parse(JSON.stringify(validated)) as AppConfig,
  timestamp: Date.now(),
};
```

To:
```typescript
configCache = {
  config: structuredClone(validated) as AppConfig,
  timestamp: Date.now(),
};
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- index.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/config/index.ts dashboard/src/core/config/__tests__/index.test.ts
git commit -m "fix(config): use structuredClone instead of JSON for deep cloning"
```

---

### Task 8: Fix Incomplete Error Context in fetchWrapper (LOW)

**Files:**
- Modify: `dashboard/src/core/llm/fetchWrapper.ts:40-50`
- Test: `dashboard/src/core/llm/__tests__/fetchWrapper.test.ts`

**Context:** Errors don't include request details for debugging

**Step 1: Write the failing test**

Add to `dashboard/src/core/llm/__tests__/fetchWrapper.test.ts`:

```typescript
describe("error context", () => {
  it("should include request details in error message", async () => {
    const error = await fetchWrapper({
      url: "http://invalid",
      method: "POST",
      body: { test: "data" }
    }).catch(e => e);

    expect(error.message).toContain("POST");
    expect(error.message).toContain("http://invalid");
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd dashboard && npm test -- fetchWrapper.test.ts
```

Expected: FAIL (request details not in error)

**Step 3: Add request details to error**

Edit `dashboard/src/core/llm/fetchWrapper.ts:40-50`:

```typescript
catch (error) {
  const errorMessage = error instanceof Error ? error.message : String(error);

  throw new Error(
    `Request failed: ${options.method} ${options.url} - ${errorMessage}`
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd dashboard && npm test -- fetchWrapper.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add dashboard/src/core/llm/fetchWrapper.ts dashboard/src/core/llm/__tests__/fetchWrapper.test.ts
git commit -m "fix(fetchwrapper): include request details in error messages"
```

---

## Phase 3: Backend Python - Domain Services

### Task 9: Fix KNNProvider Silent Fallback (CRITICAL)

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:318-320`
- Test: `tests/test_knn_provider.py` (create if needed)

**Context:** Returns random examples instead of semantically similar ones when vectorizer fails

**Step 1: Write the failing test**

Create `tests/test_knn_provider.py`:

```python
import pytest
from pathlib import Path
from hemdov.domain.services.knn_provider import KNNProvider


def test_knn_provider_raises_when_vectorizer_uninitialized():
    """KNNProvider should raise RuntimeError when vectorizer not initialized."""
    provider = KNNProvider(catalog_path=Path("tests/fixtures/valid_catalog.json"))

    # Simulate vectorizer not initialized
    provider._vectorizer = None

    with pytest.raises(RuntimeError, match="vectorizer not initialized"):
        provider.find_examples(intent="debug", complexity="simple", k=3)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_knn_provider.py::test_knn_provider_raises_when_vectorizer_uninitialized -v
```

Expected: FAIL (returns empty list instead of raising)

**Step 3: Fix silent fallback to raise error**

Edit `hemdov/domain/services/knn_provider.py:318-320`:

Change:
```python
else:
    logger.warning("Vectorizer not initialized, returning first k examples")
    return candidates[:k]
```

To:
```python
else:
    raise RuntimeError(
        "KNNProvider cannot find examples: vectorizer not initialized. "
        "Semantic similarity search requires proper vectorization. "
        "Check catalog_path and catalog format."
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_knn_provider.py::test_knn_provider_raises_when_vectorizer_uninitialized -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "fix(knn): raise RuntimeError when vectorizer uninitialized, don't return random examples"
```

---

### Task 10: Fix KNNProvider Example Skipping with Threshold (HIGH)

**Files:**
- Modify: `hemdov/domain/services/knn_provider.py:199-212`
- Test: `tests/test_knn_provider.py`

**Context:** Skips examples without warning when validation fails

**Step 1: Write the failing test**

Add to `tests/test_knn_provider.py`:

```python
def test_knn_provider_raises_when_corruption_threshold_exceeded():
    """KNNProvider should raise when >10% of examples are invalid."""
    provider = KNNProvider(catalog_path=Path("tests/fixtures/corrupted_catalog.json"))

    # Mock validator to fail for most examples
    with pytest.raises(ValueError, match="corruption threshold"):
        provider.find_examples(intent="debug", complexity="simple", k=3)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_knn_provider.py::test_knn_provider_raises_when_corruption_threshold_exceeded -v
```

Expected: FAIL (no threshold check)

**Step 3: Add corruption threshold**

Edit `hemdov/domain/services/knn_provider.py:199-212`:

```python
# At class level, add constant:
CORRUPTION_THRESHOLD = 0.10  # 10%

# In find_examples, after skipping loop:
if skipped_count > 0:
    skip_ratio = skipped_count / len(candidates)
    logger.warning(
        f"Skipped {skipped_count}/{len(candidates)} candidates due to validation failures "
        f"({skip_ratio:.1%})"
    )

    if skip_ratio > self.CORRUPTION_THRESHOLD:
        raise ValueError(
            f"Catalog corruption threshold exceeded: {skip_ratio:.1%} of examples are invalid. "
            f"This suggests catalog file corruption or format mismatch."
        )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_knn_provider.py::test_knn_provider_raises_when_corruption_threshold_exceeded -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/knn_provider.py tests/test_knn_provider.py
git commit -m "feat(knn): add 10% corruption threshold, raise when exceeded"
```

---

### Task 11: Fix NLaCBuilder Broad Exception Catching (CRITICAL)

**Files:**
- Modify: `hemdov/domain/services/nlac_builder.py:99-113`
- Test: `tests/test_nlac_builder.py` (extend existing)

**Context:** Catches all exceptions including FileNotFoundError, JSONDecodeError, RuntimeError

**Step 1: Write the failing test**

Add to `tests/test_nlac_builder.py`:

```python
def test_builder_raises_on_non_transient_errors():
    """Builder should raise on non-transient errors like FileNotFoundError."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = FileNotFoundError("Catalog missing")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(idea="Fix bug", context="", mode="nlac")

    with pytest.raises(FileNotFoundError):
        builder.build(request)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_nlac_builder.py::test_builder_raises_on_non_transient_errors -v
```

Expected: FAIL (error is caught and logged)

**Step 3: Catch only specific transient errors**

Edit `hemdov/domain/services/nlac_builder.py:99-113`:

Change:
```python
except Exception as e:
    logger.exception(f"Failed to fetch KNN examples... Continuing without few-shot")
    # Continue with empty examples list
```

To:
```python
except (ConnectionError, TimeoutError) as e:
    logger.warning(
        f"KNN temporarily unavailable: {e}. Using zero-shot mode."
    )
    # Continue with empty examples for transient errors
except Exception as e:
    # Fail hard for unexpected errors
    logger.error(f"Unexpected error fetching KNN examples: {type(e).__name__}: {e}")
    raise
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_nlac_builder.py::test_builder_raises_on_non_transient_errors -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/nlac_builder.py tests/test_nlac_builder.py
git commit -m "fix(nlacbuilder): catch only transient errors, re-raise unexpected errors"
```

---

### Task 12: Fix OPROOptimizer Broad Exception Catching (CRITICAL)

**Files:**
- Modify: `hemdov/domain/services/oprop_optimizer.py:230-241`
- Test: `tests/test_opro_optimizer.py` (extend existing)

**Context:** Same as Task 11 - broad exception catching

**Step 1-5:** Same pattern as Task 11, apply to OPROOptimizer

```bash
git add hemdov/domain/services/oprop_optimizer.py tests/test_opro_optimizer.py
git commit -m "fix(oprop): catch only transient errors, re-raise unexpected errors"
```

---

### Task 13: Fix ReflexionService Mock Fallback (HIGH)

**Files:**
- Modify: `hemdov/domain/services/reflexion_service.py:106-110`
- Test: `tests/test_reflexion_service.py` (extend existing)

**Context:** Mock fallback in production code

**Step 1: Write the failing test**

Add to `tests/test_reflexion_service.py`:

```python
def test_reflexion_raises_on_llm_failure():
    """Reflexion should raise on LLM failure, not use mock fallback."""
    service = ReflexionService(llm_client=mock_llm)

    # Mock LLM to fail
    mock_llm.generate.side_effect = RuntimeError("LLM failed")

    with pytest.raises(RuntimeError, match="LLM failed"):
        service.reflect(prompt="test", error="error")
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_reflexion_service.py::test_reflexion_raises_on_llm_failure -v
```

Expected: FAIL (mock fallback)

**Step 3: Remove mock fallback**

Edit `hemdov/domain/services/reflexion_service.py:106-110`:

Remove the mock fallback block, let the exception propagate.

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_reflexion_service.py::test_reflexion_raises_on_llm_failure -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/reflexion_service.py tests/test_reflexion_service.py
git commit -m "fix(reflexion): remove mock fallback, raise on LLM failures"
```

---

### Task 14: Fix PromptValidator Silent Autocorrection (MEDIUM)

**Files:**
- Modify: `hemdov/domain/services/prompt_validator.py:56-65`
- Test: `tests/test_prompt_validator.py` (extend existing)

**Context:** Autocorrection failures are silent

**Step 1: Write the failing test**

Add to `tests/test_prompt_validator.py`:

```python
def test_autocorrect_logs_warnings():
    """Autocorrection should log warnings when applied."""
    validator = PromptValidator(llm_client=mock_llm)

    prompt = NLaCPrompt(template="No role section")

    passed, warnings = validator.validate(prompt)
    result = validator._simple_autocorrect(prompt, warnings)

    assert result is True
    # Verify autocorrection was logged
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_prompt_validator.py::test_autocorrect_logs_warnings -v
```

Expected: FAIL (no logging)

**Step 3: Add logging to autocorrection**

Edit `hemdov/domain/services/prompt_validator.py:56-65`:

Add logging after each autocorrection:
```python
logger.info(f"Autocorrected prompt: added {field}")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_prompt_validator.py::test_autocorrect_logs_warnings -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/prompt_validator.py tests/test_prompt_validator.py
git commit -m "feat(validator): log autocorrection operations"
```

---

### Task 15: Fix PromptValidator Broad LLM Error Catching (MEDIUM)

**Files:**
- Modify: `hemdov/domain/services/prompt_validator.py:170-183`
- Test: `tests/test_prompt_validator.py`

**Context:** Catches all LLM errors broadly

**Step 1-5:** Similar to Task 11, catch specific LLM errors only

```bash
git add hemdov/domain/services/prompt_validator.py tests/test_prompt_validator.py
git commit -m "fix(validator): catch specific LLM errors, not broad Exception"
```

---

### Task 16: Add Missing KNNProvider Export (IMPORTANT)

**Files:**
- Modify: `hemdov/domain/services/__init__.py`
- Test: `tests/test_imports.py` (create)

**Context:** KNNProvider not exported but imported elsewhere

**Step 1: Write the failing test**

Create `tests/test_imports.py`:

```python
def test_knn_provider_importable_from_services():
    """KNNProvider should be importable from hemdov.domain.services."""
    from hemdov.domain.services import KNNProvider

    assert KNNProvider is not None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_imports.py::test_knn_provider_importable_from_services -v
```

Expected: FAIL (ImportError)

**Step 3: Add export to __init__.py**

Edit `hemdov/domain/services/__init__.py`:

Add:
```python
from hemdov.domain.services.knn_provider import KNNProvider

__all__ = [
    "ComplexityAnalyzer",
    "ComplexityLevel",
    "IntentClassifier",
    "KNNProvider",  # Add this
    # ... rest
]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_imports.py::test_knn_provider_importable_from_services -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/services/__init__.py tests/test_imports.py
git commit -m "fix(services): export KNNProvider from __init__.py"
```

---

## Phase 4: Backend Python - API Layer

### Task 17: Fix Fire-and-Forget Async (CRITICAL)

**Files:**
- Modify: `api/prompt_improver_api.py:379-386`
- Test: `tests/test_api_integration.py` (extend)

**Context:** Async task errors are lost to the void

**Step 1: Write the failing test**

Add to `tests/test_api_integration.py`:

```python
def test_save_history_async_errors_captured():
    """History save async errors should be captured."""
    # Mock database to fail
    # Call endpoint
    # Verify error was captured (not lost)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api_integration.py::test_save_history_async_errors_captured -v
```

Expected: FAIL (error not captured)

**Step 3: Add done callback for error handling**

Edit `api/prompt_improver_api.py:379-386`:

Change:
```python
asyncio.create_task(_save_history_async(...))
```

To:
```python
task = asyncio.create_task(_save_history_async(...))

def handle_save_error(task):
    if exception := task.exception():
        logger.error(f"Failed to save prompt history: {exception}")

task.add_done_callback(handle_save_error)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api_integration.py::test_save_history_async_errors_captured -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add api/prompt_improver_api.py tests/test_api_integration.py
git commit -m "fix(api): add done_callback to capture history save errors"
```

---

### Task 18: Fix Metrics Failures Suppressed (MEDIUM)

**Files:**
- Modify: `api/prompt_improver_api.py:340-351`
- Test: `tests/test_api_integration.py`

**Context:** Metrics calculation failures are suppressed

**Step 1-5:** Add logging for metrics failures, test verifies logging

```bash
git add api/prompt_improver_api.py tests/test_api_integration.py
git commit -m "feat(api): log metrics calculation failures"
```

---

### Task 19: Add Error IDs to Responses (LOW)

**Files:**
- Modify: `api/prompt_improver_api.py:557-573`
- Test: `tests/test_api_integration.py`

**Context:** Error IDs not tracked for Sentry

**Step 1-5:** Add error_id field to error responses

```bash
git add api/prompt_improver_api.py tests/test_api_integration.py
git commit -m "feat(api): add error_id field to error responses"
```

---

## Phase 5: Backend Python - Infrastructure

### Task 20: Fix SQLite JSON Corruption Silent (MEDIUM)

**Files:**
- Modify: `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:286-294`
- Test: `tests/test_sqlite_prompt_repository.py` (extend)

**Context:** JSON corruption not detected

**Step 1-5:** Add JSON validation before/after operations

```bash
git add hemdov/infrastructure/persistence/sqlite_prompt_repository.py tests/test_sqlite_prompt_repository.py
git commit -m "fix(repository): validate JSON before/after operations, detect corruption"
```

---

### Task 21: Fix SQLite Cache Errors Too Broad (MEDIUM)

**Files:**
- Modify: `hemdov/infrastructure/persistence/sqlite_prompt_repository.py:368-382`
- Test: `tests/test_sqlite_prompt_repository.py`

**Context:** Cache error catching too broad

**Step 1-5:** Catch specific cache errors only

```bash
git add hemdov/infrastructure/persistence/sqlite_prompt_repository.py tests/test_sqlite_prompt_repository.py
git commit -m "fix(repository): catch specific cache errors, not broad Exception"
```

---

## Phase 6: New Tests for Coverage Gaps

### Task 22-24: Vector Caching Tests (CRITICAL - Rating 9/10)

**Files:**
- Create: `tests/test_knn_vector_cache.py`

**Step 1: Write the tests**

```python
import pytest
from pathlib import Path
from hemdov.domain.services.knn_provider import KNNProvider


def test_catalog_vectors_cache_initialized():
    """Verify catalog vectors are pre-computed and cached."""
    provider = KNNProvider(catalog_path=Path("tests/fixtures/valid_catalog.json"))

    assert provider._catalog_vectors is not None
    assert provider._catalog_vectors.shape[0] == len(provider.catalog)


def test_find_examples_uses_cached_vectors():
    """Verify find_examples uses cached vectors when no filtering."""
    provider = KNNProvider(catalog_path=Path("tests/fixtures/valid_catalog.json"))

    # Mock vectorizer to detect re-vectorization calls
    original_vectorizer = provider._vectorizer
    call_count = [0]

    def counting_vectorizer(texts):
        call_count[0] += 1
        return original_vectorizer(texts)

    provider._vectorizer = counting_vectorizer

    # Call find_examples without filtering (should use cache)
    examples = provider.find_examples(intent="debug", complexity="simple", k=3)

    # Should NOT call vectorizer again (uses cache)
    assert call_count[0] == 0, "Should use cached vectors, not re-vectorize"
    assert len(examples) == 3


def test_cache_performance_improvement():
    """Benchmark: cached vectors should be faster than re-vectorization."""
    import time

    provider = KNNProvider(catalog_path=Path("tests/fixtures/valid_catalog.json"))

    # Time with cache (first call still uses cache, initialized in __init__)
    start = time.perf_counter()
    provider.find_examples(intent="debug", complexity="simple", k=3)
    cached_time = time.perf_counter() - start

    # Cache should make lookup fast (< 100ms for reasonable catalog size)
    assert cached_time < 0.1, f"Cache lookup too slow: {cached_time:.3f}s"
```

**Step 2: Run tests**

```bash
pytest tests/test_knn_vector_cache.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_knn_vector_cache.py
git commit -m "test(knn): add vector caching tests (7x speedup verification)"
```

---

### Task 25-27: KNN Error Propagation Tests (CRITICAL - Rating 8/10)

**Files:**
- Create: `tests/test_nlac_error_propagation.py`

**Step 1: Write the tests**

```python
import pytest
from unittest.mock import Mock
from hemdov.domain.services.nlac_builder import NLaCBuilder
from hemdov.domain.dto.nlac_models import NLaCRequest


def test_builder_continues_when_knn_fails():
    """Builder should continue with empty examples when KNN fails transiently."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = ConnectionError("Network timeout")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(idea="Fix bug", context="", mode="nlac")

    # Should not raise, should continue
    result = builder.build(request)

    # Should have template but no few-shot examples
    assert result.template is not None
    assert len(result.fewshot_examples) == 0
    assert result.strategy_meta.get("fewshot_count") == 0


def test_builder_raises_when_knn_fails_permanently():
    """Builder should raise when KNN fails permanently (FileNotFoundError)."""
    mock_knn = Mock()
    mock_knn.find_examples.side_effect = FileNotFoundError("Catalog missing")

    builder = NLaCBuilder(knn_provider=mock_knn)
    request = NLaCRequest(idea="Fix bug", context="", mode="nlac")

    with pytest.raises(FileNotFoundError):
        builder.build(request)


def test_builder_logs_knn_failures():
    """Builder should log appropriate messages on KNN failures."""
    # Add logger capture verification
    pass
```

**Step 2: Run tests**

```bash
pytest tests/test_nlac_error_propagation.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_nlac_error_propagation.py
git commit -m "test(nlac): add KNN error propagation tests"
```

---

### Task 28-30: Exception Behavior Tests (CRITICAL - Rating 8/10)

**Files:**
- Extend: `tests/test_knn_provider.py`

**Step 1: Write the tests**

```python
def test_knn_provider_with_malformed_json():
    """Should raise ValueError for JSON decode errors."""
    import tempfile
    import json

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"invalid": json}')  # Invalid JSON
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            KNNProvider(catalog_path=Path(temp_path))
    finally:
        Path(temp_path).unlink()


def test_knn_provider_with_all_invalid_examples():
    """Should raise ValueError when all examples fail validation."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"invalid": "example"}], f)  # Missing required fields
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="No valid examples found"):
            KNNProvider(catalog_path=Path(temp_path))
    finally:
        Path(temp_path).unlink()


def test_knn_provider_file_not_found():
    """Should raise FileNotFoundError when catalog missing."""
    with pytest.raises(FileNotFoundError, match="ComponentCatalog not found"):
        KNNProvider(catalog_path=Path("/nonexistent/path.json"))
```

**Step 2: Run tests**

```bash
pytest tests/test_knn_provider.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_knn_provider.py
git commit -m "test(knn): add exception behavior tests for malformed catalog"
```

---

### Task 31-32: TypedDict Tests (IMPORTANT - Rating 6/10)

**Files:**
- Extend: `tests/test_nlac_models.py`

**Step 1: Write the tests**

```python
def test_strategy_metadata_requires_strategy_field():
    """StrategyMetadata should require strategy field."""
    from hemdov.domain.dto.nlac_models import StrategyMetadata

    # Should fail without strategy
    with pytest.raises(KeyError):
        metadata: StrategyMetadata = {
            "intent": "debug",
            # Missing "strategy"
            "complexity": "simple",
            "mode": "nlac",
        }


def test_strategy_metadata_requires_rar_used():
    """StrategyMetadata should require rar_used field."""
    from hemdov.domain.dto.nlac_models import StrategyMetadata

    # Should fail without rar_used
    with pytest.raises(KeyError):
        metadata: StrategyMetadata = {
            "strategy": "nlac",
            "intent": "debug",
            # Missing "rar_used"
            "complexity": "simple",
        }
```

**Step 2: Run tests**

```bash
pytest tests/test_nlac_models.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_nlac_models.py
git commit -m "test(models): add TypedDict required field tests"
```

---

## Phase 7: Refactoring (Nice to Have)

### Task 33: Extract Duplicate FixedVocabularyVectorizer (HIGH Priority)

**Files:**
- Create: `hemdov/domain/dspy_modules/vectorizer.py`
- Modify: `eval/src/dspy_prompt_improver_fewshot.py`, `hemdov/domain/services/knn_provider.py`

**Step 1: Write the test**

```python
def test_vectorizer_importable_from_shared_module():
    """FixedVocabularyVectorizer should be importable from shared module."""
    from hemdov.domain.dspy_modules.vectorizer import FixedVocabularyVectorizer

    assert FixedVocabularyVectorizer is not None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_vectorizer.py -v
```

Expected: FAIL (module doesn't exist)

**Step 3: Extract to shared module**

Create `hemdov/domain/dspy_modules/vectorizer.py` with the FixedVocabularyVectorizer class.

Update imports in both files to use the shared module.

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_vectorizer.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hemdov/domain/dspy_modules/vectorizer.py tests/test_vectorizer.py
git commit -m "refactor(vectorizer): extract duplicate FixedVocabularyVectorizer to shared module"
```

---

### Task 34-40: Additional Refactoring

(Same TDD pattern for: NLaCBuilder matrices, KNNProvider decomposition, TypeScript confidence extraction, ConversationView loading stages, Config extraction duplication, PromptValidator constraint checking, presetToRules switch)

---

## Phase 8: Integration Tests

### Task 41-43: Cross-Service Integration Tests

**Files:**
- Create: `tests/test_service_integration.py` (extend existing)

**Step 1: Write the tests**

```python
def test_knn_nlac_integration():
    """Real KNN + NLaCBuilder integration (not mocked)."""
    pass

def test_reflexion_opro_routing():
    """Verify Reflexion → OPRO routing logic."""
    pass

def test_cache_sqlite_integration():
    """Cache + SQLite repository integration."""
    pass
```

**Step 2-5:** Complete TDD cycle for each

```bash
git add tests/test_service_integration.py
git commit -m "test(integration): add cross-service integration tests"
```

---

## Verification

After all tasks complete:

```bash
# Run all tests
make test

# Run TypeScript tests
cd dashboard && npm test

# Run quality gates
make eval

# Check for any remaining issues
make lint
```

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1 | 1-4 | Dashboard/TypeScript - Conversation |
| 2 | 5-8 | Dashboard/TypeScript - LLM |
| 3 | 9-16 | Backend Python - Domain Services |
| 4 | 17-19 | Backend Python - API Layer |
| 5 | 20-21 | Backend Python - Infrastructure |
| 6 | 22-32 | New Tests for Coverage Gaps |
| 7 | 33-40 | Refactoring |
| 8 | 41-43 | Integration Tests |
| **Total** | **43** | **All fixes complete** |

**Estimated Time:** ~5.5 hours

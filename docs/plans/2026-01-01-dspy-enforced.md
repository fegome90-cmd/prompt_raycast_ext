# DSPy-Only Raycast Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Raycast use DSPy as a mandatory backend (no automatic Ollama fallback) when DSPy is enabled.

**Architecture:** Keep DSPy backend as the primary pipeline, but treat failures as blocking errors. Allow explicit opt-out by disabling DSPy in preferences; only then use Ollama directly. Add tests to ensure no fallback occurs when DSPy is required.

**Tech Stack:** TypeScript, Raycast API, Vitest.

### Task 1: Enforce DSPy-only behavior in core pipeline

**Files:**
- Modify: `dashboard/src/core/llm/improvePrompt.ts`
- Test: `dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts`

**Step 1: Write the failing test**

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { improvePromptWithHybrid, ImprovePromptError } from "../improvePrompt";
import * as ollamaChatModule from "../ollamaChat";

vi.mock("../ollamaChat", () => ({ callOllamaChat: vi.fn() }));
const mockCallOllamaChat = ollamaChatModule.callOllamaChat as unknown as ReturnType<typeof vi.fn>;

describe("dspy enforced", () => {
  beforeEach(() => {
    mockCallOllamaChat.mockReset();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("throws when DSPy fails and fallback disabled", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce({ ok: false, status: 503, statusText: "down", json: async () => ({}) });

    await expect(
      improvePromptWithHybrid({
        rawInput: "x",
        preset: "default",
        options: {
          baseUrl: "http://localhost:11434",
          model: "x",
          timeoutMs: 30000,
          dspyBaseUrl: "http://localhost:8000",
        },
        enableDSPyFallback: false,
      }),
    ).rejects.toBeInstanceOf(ImprovePromptError);

    expect(mockCallOllamaChat).not.toHaveBeenCalled();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: FAIL (fallback still happens)

**Step 3: Write minimal implementation**

```ts
// In improvePromptWithHybrid, when enableDSPyFallback === false
// - Do NOT fall through to improvePromptWithOllama
// - Re-throw as ImprovePromptError (or the original error) with metadata
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: PASS

**Step 5: Commit**

```fish
git add dashboard/src/core/llm/improvePrompt.ts dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts
git commit -m "feat: enforce dspy-only mode"
```

### Task 2: Enforce DSPy-only in Raycast UI command

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Write the failing test**

N/A (UI behavior). We will verify by reading code and manual smoke test.

**Step 2: Implement**

```ts
// If dspyEnabled === true, call improvePromptWithHybrid with enableDSPyFallback: false
// On error, show toast "DSPy backend not available" + hint
// Remove/skip ollamaHealthCheck when DSPy is enabled
```

**Step 3: Manual smoke test**

Run: `cd dashboard && ray develop`  
Expected: When DSPy is down, Raycast shows error; when DSPy is up, prompt is improved by DSPy.

**Step 4: Commit**

```fish
git add dashboard/src/promptify-quick.tsx
git commit -m "feat: require dspy in promptify command"
```

### Task 3: Update docs to reflect DSPy-only behavior

**Files:**
- Modify: `docs/backend/README.md`
- Modify: `docs/backend/quickstart.md`
- Modify: `docs/backend/status.md`
- Modify: `docs/backend/implementation-summary.md`
- Modify: `docs/research/wizard/00-EXECUTIVE-SUMMARY.md`

**Step 1: Update docs**

Add a clear statement: “DSPy is mandatory when enabled; no automatic fallback to Ollama.”

**Step 2: Commit**

```fish
git add docs/backend/README.md docs/backend/quickstart.md docs/backend/status.md docs/backend/implementation-summary.md docs/research/wizard/00-EXECUTIVE-SUMMARY.md
git commit -m "docs: document dspy-only mode"
```

---

**Plan complete and saved to** `docs/plans/2026-01-01-dspy-enforced.md`. Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration  
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

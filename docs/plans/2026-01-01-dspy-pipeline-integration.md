# DSPy Pipeline Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan.

**Goal:** Route the Raycast prompt pipeline through DSPy first, with safe fallback to Ollama, and configurable DSPy backend URL.

**Architecture:** Add a DSPy backend config to the app defaults and preferences, update the DSPy client to accept override base URL/timeout, and switch the UI command to call DSPy first before falling back to the existing Ollama path (including fallback model). Keep HemDov adapter untouched.

**Tech Stack:** Raycast extension (TypeScript/React), Vitest, Zod config schemas.

---

### Task 1: Add DSPy config defaults + schema

**Files:**
- Modify: `dashboard/src/core/config/defaults.ts`
- Modify: `dashboard/src/core/config/schema.ts`

**Step 1: Write the failing test**

Create `dashboard/src/core/config/__tests__/dspyConfig.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { validateConfigOnly } from "../index";
import { DEFAULTS } from "../defaults";

describe("DSPy config defaults", () => {
  it("validates defaults with dspy config", () => {
    const result = validateConfigOnly(DEFAULTS);
    expect(result.valid).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- dspyConfig.test.ts`
Expected: FAIL (because `dspy` is missing from schema).

**Step 3: Write minimal implementation**

Add a `dspy` block to defaults:
```ts
dspy: {
  baseUrl: "http://localhost:8000",
  timeoutMs: 30_000,
  enabled: true,
},
```

Add `DSPyConfigSchema` and include it in `AppConfigSchema` and `validatePartialConfig`:
```ts
export const DSPyConfigSchema = z.object({
  baseUrl: z.string().url(),
  timeoutMs: z.number().int().positive().min(1000).max(120_000),
  enabled: z.boolean(),
}).strict();
```

**Step 4: Run test to verify it passes**

Run: `npm test -- dspyConfig.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add dashboard/src/core/config/defaults.ts dashboard/src/core/config/schema.ts dashboard/src/core/config/__tests__/dspyConfig.test.ts
git commit -m "feat: add DSPy config defaults and schema"
```

---

### Task 2: Add Raycast preferences for DSPy backend

**Files:**
- Modify: `dashboard/package.json`
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Write the failing test**

Create `dashboard/src/core/llm/__tests__/dspyClientConfig.test.ts`:
```ts
import { describe, expect, it, vi } from "vitest";
import { createDSPyClient } from "../dspyPromptImprover";

describe("DSPy client config", () => {
  it("uses override baseUrl and timeout", () => {
    const client = createDSPyClient({ baseUrl: "http://localhost:8001", timeoutMs: 1234 });
    // @ts-expect-error - access private config for test
    expect(client.config.baseUrl).toBe("http://localhost:8001");
    // @ts-expect-error - access private config for test
    expect(client.config.timeoutMs).toBe(1234);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- dspyClientConfig.test.ts`
Expected: FAIL (config is private or not set as expected).

**Step 3: Write minimal implementation**

- In `dashboard/package.json` add preferences:
  - `dspyBaseUrl` (default `http://localhost:8000`)
  - `dspyTimeoutMs` (default `30000`)
  - `dspyEnabled` (checkbox default `true`)

- In `dashboard/src/promptify-quick.tsx`, extend `Preferences` type and read new prefs.

- In `dashboard/src/core/llm/dspyPromptImprover.ts`, allow `createDSPyClient` to accept override config (already supported) and expose a test helper or adjust test to avoid private access.

**Step 4: Run test to verify it passes**

Run: `npm test -- dspyClientConfig.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add dashboard/package.json dashboard/src/promptify-quick.tsx dashboard/src/core/llm/__tests__/dspyClientConfig.test.ts
git commit -m "feat: add DSPy preferences and client config test"
```

---

### Task 3: Route prompt pipeline through DSPy first

**Files:**
- Modify: `dashboard/src/core/llm/dspyPromptImprover.ts`
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Write the failing test**

Create `dashboard/src/core/llm/__tests__/dspyPipeline.test.ts`:
```ts
import { describe, expect, it, vi } from "vitest";
import { improvePromptWithDSPy } from "../dspyPromptImprover";

const fetchMock = vi.fn();
global.fetch = fetchMock as any;

describe("DSPy pipeline", () => {
  it("uses configured DSPy baseUrl when provided", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ status: "healthy", dspy_configured: true }) });
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ improved_prompt: "ok", role: "r", directive: "d", framework: "f", guardrails: [] }) });

    const result = await improvePromptWithDSPy("idea", "default", "ctx", {
      baseUrl: "http://localhost:8001",
      timeoutMs: 1000,
    });

    expect(fetchMock.mock.calls[0][0]).toContain("http://localhost:8001/health");
    expect(result.improved_prompt).toBe("ok");
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- dspyPipeline.test.ts`
Expected: FAIL (function signature does not accept config).

**Step 3: Write minimal implementation**

- Update `improvePromptWithDSPy` signature to accept optional config:
  ```ts
  export async function improvePromptWithDSPy(rawInput: string, preset = "default", context?: string, config?: Partial<DSPyBackendConfig>)
  ```
  Use `createDSPyClient(config)` when provided.

- In `promptify-quick.tsx`, replace the Ollama-first path:
  - Try DSPy if `dspyEnabled` is true.
  - If DSPy fails, fall back to `runWithModelFallback` (Ollama).
  - Update toasts to reflect DSPy attempt.

**Step 4: Run test to verify it passes**

Run: `npm test -- dspyPipeline.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add dashboard/src/core/llm/dspyPromptImprover.ts dashboard/src/promptify-quick.tsx dashboard/src/core/llm/__tests__/dspyPipeline.test.ts
git commit -m "feat: route prompt pipeline through DSPy with fallback"
```

---

### Task 4: Update UI copy + error messaging

**Files:**
- Modify: `dashboard/src/promptify-quick.tsx`

**Step 1: Write the failing test**

Create `dashboard/src/core/llm/__tests__/dspyCopy.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import Command from "../../promptify-quick";

describe("DSPy copy", () => {
  it("renders DSPy label in action", () => {
    const { getByText } = render(<Command />);
    expect(getByText(/Improve Prompt/i)).toBeTruthy();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- dspyCopy.test.ts`
Expected: FAIL if label does not match expected.

**Step 3: Write minimal implementation**

Update action label to “Improve Prompt (DSPy + Ollama)” and toast message to “Generating with DSPy…”.

**Step 4: Run test to verify it passes**

Run: `npm test -- dspyCopy.test.ts`
Expected: PASS.

**Step 5: Commit**

```bash
git add dashboard/src/promptify-quick.tsx dashboard/src/core/llm/__tests__/dspyCopy.test.ts
git commit -m "chore: update DSPy copy in UI"
```

---

### Task 5: Full test run

**Files:**
- None

**Step 1: Run full unit tests**

Run: `npm test`
Expected: PASS (no new failures).

**Step 2: Commit (if needed)**

If any fixes required, commit with a descriptive message.

---

Plan complete and saved to `docs/plans/2026-01-01-dspy-pipeline-integration.md`. Two execution options:

1. Subagent-Driven (this session) — I dispatch a fresh subagent per task, review between tasks.
2. Parallel Session (separate) — Open a new session with executing-plans, batch execution with checkpoints.

Which approach?*** End Patch"}}

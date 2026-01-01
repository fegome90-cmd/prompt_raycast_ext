# DSPy + Ollama Pipeline for Raycast Extension Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Raycast extension use the DSPy backend first (HF model via Ollama) with explicit config and safe fallback to Ollama chat.

**Architecture:** Add a dedicated DSPy config block (base URL, timeout, enable flag) to config defaults + schema, wire Raycast preferences to those values, and route `promptify-quick` through `improvePromptWithHybrid` so DSPy is the primary path with Ollama fallback. Add focused tests to validate DSPy path and fallback behavior.

**Tech Stack:** TypeScript, Raycast API, Vitest, DSPy backend (FastAPI), Ollama.

### Task 1: Add DSPy config to app config

**Files:**
- Create: `dashboard/src/core/config/__tests__/dspy-config.test.ts`
- Modify: `dashboard/src/core/config/schema.ts`
- Modify: `dashboard/src/core/config/defaults.ts`
- Modify: `dashboard/src/core/config/index.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";
import { validateConfig } from "../schema";

describe("dspy config", () => {
  it("requires dspy baseUrl, timeoutMs, enabled", () => {
    expect(() =>
      validateConfig({
        ollama: {
          baseUrl: "http://localhost:11434",
          model: "test",
          fallbackModel: "test2",
          timeoutMs: 30000,
          temperature: 0.1,
          healthCheckTimeoutMs: 2000,
        },
        pipeline: { maxQuestions: 3, maxAssumptions: 5, enableAutoRepair: true },
        quality: { minConfidence: 0.7, bannedSnippets: ["x"], metaLineStarters: ["task:"] },
        features: {
          safeMode: false,
          patternsEnabled: true,
          personalityEnabled: true,
          evalEnabled: false,
          autoUpdateKnowledge: false,
        },
        presets: { default: "default", available: ["default"] },
        patterns: { maxScanChars: 1000, severityPolicy: "warn" },
        eval: { gates: { jsonValidPass1: 0.9, copyableRate: 0.9, reviewRateMax: 0.2, latencyP95Max: 60000, patternsDetectedMin: 0 }, dataset: { path: "x", baseline: "y" } },
        dspy: { baseUrl: "http://localhost:8000", timeoutMs: 30000, enabled: true },
      })
    ).not.toThrow();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- src/core/config/__tests__/dspy-config.test.ts`  
Expected: FAIL (schema missing `dspy`)

**Step 3: Write minimal implementation**

```ts
// dashboard/src/core/config/schema.ts
export const DspyConfigSchema = z
  .object({
    baseUrl: z.string().url("dspy.baseUrl must be a valid URL (e.g., http://localhost:8000)"),
    timeoutMs: z
      .number()
      .int()
      .positive("dspy.timeoutMs must be positive")
      .min(1_000, "dspy.timeoutMs must be at least 1s (1000ms)")
      .max(120_000, "dspy.timeoutMs must not exceed 2 minutes (120000ms)"),
    enabled: z.boolean(),
  })
  .strict();

export const AppConfigSchema = z
  .object({
    ollama: OllamaConfigSchema,
    dspy: DspyConfigSchema,
    pipeline: PipelineConfigSchema,
    quality: QualityConfigSchema,
    features: FeaturesConfigSchema,
    presets: PresetsConfigSchema,
    patterns: PatternsConfigSchema,
    eval: EvalConfigSchema,
  })
  .strict();

export type DspyConfig = z.infer<typeof DspyConfigSchema>;

// validatePartialConfig: add a branch
if (configObj.dspy) {
  partialConfig.dspy = DspyConfigSchema.parse(configObj.dspy);
}
```

```ts
// dashboard/src/core/config/defaults.ts
dspy: {
  baseUrl: "http://localhost:8000",
  timeoutMs: 30_000,
  enabled: true,
},
```

```ts
// dashboard/src/core/config/index.ts
// No logic change needed; ensure mergeWithDefaults handles `dspy` by defaults
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- src/core/config/__tests__/dspy-config.test.ts`  
Expected: PASS

**Step 5: Commit**

```fish
git add dashboard/src/core/config/schema.ts dashboard/src/core/config/defaults.ts dashboard/src/core/config/index.ts dashboard/src/core/config/__tests__/dspy-config.test.ts
git commit -m "feat: add dspy config defaults and schema"
```

### Task 2: Add Raycast preferences and wire DSPy in the UI

**Files:**
- Modify: `dashboard/package.json`
- Modify: `dashboard/src/promptify-quick.tsx`
- Modify: `dashboard/src/core/llm/improvePrompt.ts`

**Step 1: Write the failing test**

```ts
import { describe, expect, it, vi } from "vitest";
import { improvePromptWithHybrid } from "../improvePrompt";
import * as ollamaChatModule from "../ollamaChat";

vi.mock("../ollamaChat", () => ({ callOllamaChat: vi.fn() }));
const mockCallOllamaChat = ollamaChatModule.callOllamaChat as unknown as ReturnType<typeof vi.fn>;

describe("dspy hybrid config", () => {
  it("uses dspyBaseUrl when provided", async () => {
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: "healthy", provider: "ollama", model: "x", dspy_configured: true }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ improved_prompt: "ok", role: "r", directive: "d", framework: "f", guardrails: [] }) });

    const result = await improvePromptWithHybrid({
      rawInput: "x",
      preset: "default",
      options: { baseUrl: "http://localhost:11434", model: "x", timeoutMs: 30000, dspyBaseUrl: "http://localhost:8000" },
    });

    expect(result._metadata?.backend).toBe("dspy");
    expect(mockCallOllamaChat).not.toHaveBeenCalled();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: FAIL (missing `dspyBaseUrl` in options + implementation)

**Step 3: Write minimal implementation**

```ts
// dashboard/src/core/llm/improvePrompt.ts
export type ImprovePromptOptions = {
  baseUrl: string;
  model: string;
  timeoutMs: number;
  temperature?: number;
  systemPattern?: string;
  dspyBaseUrl?: string;
  dspyTimeoutMs?: number;
};

// Use dspyBaseUrl/dspyTimeoutMs if present
const dspyClient = createDSPyClient({
  baseUrl: args.options.dspyBaseUrl ?? "http://localhost:8000",
  timeoutMs: args.options.dspyTimeoutMs ?? args.options.timeoutMs,
});
```

```json
// dashboard/package.json (new preferences in command)
{
  "name": "dspyBaseUrl",
  "description": "Base URL for DSPy backend",
  "type": "text",
  "required": false,
  "default": "http://localhost:8000",
  "title": "DSPy Base URL"
},
{
  "name": "dspyEnabled",
  "description": "Enable DSPy backend (fallbacks to Ollama if off)",
  "type": "checkbox",
  "required": false,
  "default": true,
  "title": "DSPy Enabled"
}
```

```ts
// dashboard/src/promptify-quick.tsx
import { improvePromptWithHybrid } from "./core/llm/improvePrompt";

type Preferences = {
  ollamaBaseUrl?: string;
  model?: string;
  fallbackModel?: string;
  preset?: "default" | "specific" | "structured" | "coding";
  timeoutMs?: string;
  dspyBaseUrl?: string;
  dspyEnabled?: boolean;
};

const dspyBaseUrl = preferences.dspyBaseUrl?.trim() || config.dspy.baseUrl;
const dspyEnabled = preferences.dspyEnabled ?? config.dspy.enabled;

const result = await improvePromptWithHybrid({
  rawInput: text,
  preset,
  options: {
    baseUrl,
    model,
    timeoutMs,
    temperature,
    systemPattern: getCustomPatternSync(),
    dspyBaseUrl,
    dspyTimeoutMs: config.dspy.timeoutMs,
  },
  enableDSPyFallback: dspyEnabled,
});
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: PASS

**Step 5: Commit**

```fish
git add dashboard/package.json dashboard/src/promptify-quick.tsx dashboard/src/core/llm/improvePrompt.ts dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts
git commit -m "feat: wire dspy config and preferences into promptify"
```

### Task 3: Verify fallback behavior (DSPy → Ollama)

**Files:**
- Modify: `dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts`

**Step 1: Write the failing test**

```ts
it("falls back to Ollama when DSPy health check fails", async () => {
  globalThis.fetch = vi.fn().mockResolvedValueOnce({ ok: false, status: 503, statusText: "down", json: async () => ({}) });
  mockCallOllamaChat.mockResolvedValueOnce(
    JSON.stringify({
      improved_prompt: "fallback",
      clarifying_questions: [],
      assumptions: [],
      confidence: 0.7,
    })
  );

  const result = await improvePromptWithHybrid({
    rawInput: "x",
    preset: "default",
    options: { baseUrl: "http://localhost:11434", model: "x", timeoutMs: 30000, dspyBaseUrl: "http://localhost:8000" },
  });

  expect(result._metadata?.backend).toBe("ollama");
  expect(mockCallOllamaChat).toHaveBeenCalledTimes(1);
});
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: FAIL (fallback path not asserted)

**Step 3: Write minimal implementation**

Adjust `improvePromptWithHybrid` error handling to ensure fallback occurs on health check failure without throwing.

**Step 4: Run test to verify it passes**

Run: `cd dashboard && npm test -- src/core/llm/__tests__/improvePrompt.dspy.test.ts`  
Expected: PASS

**Step 5: Commit**

```fish
git add dashboard/src/core/llm/__tests__/improvePrompt.dspy.test.ts dashboard/src/core/llm/improvePrompt.ts
git commit -m "test: cover dspy fallback to ollama"
```

### Task 4: Update Raycast pipeline docs

**Files:**
- Modify: `docs/backend/README.md`
- Modify: `docs/research/wizard/00-EXECUTIVE-SUMMARY.md`

**Step 1: Write the failing test**

N/A (docs only).

**Step 2: Update documentation**

```md
## Raycast Pipeline (DSPy First)

1. DSPy backend is queried at `dspy.baseUrl` (default `http://localhost:8000`)
2. If healthy, DSPy response is used
3. If not healthy, fallback to Ollama chat
```

Also update summary checklist to mark pipeline as “operational” and list the HF model in the config snippet.

**Step 3: Commit**

```fish
git add docs/backend/README.md docs/research/wizard/00-EXECUTIVE-SUMMARY.md
git commit -m "docs: describe dspy-first raycast pipeline"
```

---

**Plan complete and saved to** `docs/plans/2026-01-01-dspy-ollama-pipeline.md`. Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration  
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
